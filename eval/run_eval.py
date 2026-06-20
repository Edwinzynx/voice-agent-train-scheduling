import os
import sys
import json
import time
import uuid
import sqlite3
from pathlib import Path

# Add backend directory to sys.path so we can import app modules directly
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from app.brain.fsm import FSMCoordinator
from app.config import config_manager

EVAL_DIR = Path(__file__).resolve().parent
DATASET_FILE = EVAL_DIR / "dataset.json"
BASELINE_FILE = EVAL_DIR / "baselines" / "baseline_v1.json"
DB_FILE = Path(__file__).resolve().parent.parent / "backend" / "voice_agent.db"

def run_eval(mode=None):
    print("==================================================")
    print("Starting LocoVoice Automated Evaluation Simulator ")
    print("==================================================")
    
    # 1. Load dataset
    if not DATASET_FILE.exists():
        print(f"Error: Dataset file not found at {DATASET_FILE}")
        return
        
    with open(DATASET_FILE, "r") as f:
        dataset = json.load(f)
        
    # 2. Load baseline
    baseline = {}
    if BASELINE_FILE.exists():
        with open(BASELINE_FILE, "r") as f:
            baseline = json.load(f)
        print(f"Loaded baseline snapshot v{baseline.get('dataset_version', '1.0')}")
    else:
        print("Warning: No baseline file found. Skipping regression checks.")

    # Force mock/real mode based on CLI argument or API keys
    if mode == "mock":
        print("Forcing Mock/Offline mode via CLI.")
        config_manager.settings.use_mock_llm = True
    elif mode == "real":
        print("Forcing Real/LLM mode via CLI.")
        config_manager.settings.use_mock_llm = False
    else:
        if not config_manager.settings.groq_api_key:
            print("No GROQ_API_KEY detected. Defaulting evaluation to Mock/Offline mode.")
            config_manager.settings.use_mock_llm = True
        else:
            print("GROQ_API_KEY detected. Defaulting evaluation to Real/LLM mode.")
            config_manager.settings.use_mock_llm = False
        
    results = []
    total_cases = len(dataset)
    successes = 0
    slot_accuracies = []
    all_latencies = []
    
    print(f"Running {total_cases} test cases...\n")
    
    for case in dataset:
        print(f" -> Running Case: {case['id']} - {case['description']}")
        
        # Fresh FSM coordinator for each scenario to isolate sessions
        coordinator = FSMCoordinator()
        case_id = f"eval-cli-{uuid.uuid4().hex[:6]}"
        
        # Start FSM GREET state
        coordinator.process_turn(case_id, "GREET")
        
        case_latencies = []
        
        for turn in case["turns"]:
            start_time = time.time()
            coordinator.process_turn(case_id, turn)
            elapsed_ms = (time.time() - start_time) * 1000
            case_latencies.append(elapsed_ms)
            all_latencies.append(elapsed_ms)
            # Sleep to respect Groq's 6000 TPM limit in real mode
            if not config_manager.settings.use_mock_llm:
                time.sleep(8.0)
        final_session = coordinator.sessions[case_id]
        
        # Evaluate intent
        intent_matched = final_session.intent == case["expected_intent"]
        
        # Evaluate slot accuracy
        slot_matches = 0
        expected_slots = case["expected_slots"]
        total_expected_slots = len(expected_slots)
        
        for slot_key, expected_val in expected_slots.items():
            actual_val = final_session.slots.get(slot_key)
            if actual_val and expected_val.lower() in str(actual_val).lower():
                slot_matches += 1
                
        slot_acc = (slot_matches / total_expected_slots) if total_expected_slots > 0 else 1.0
        slot_accuracies.append(slot_acc)
        
        # Task success condition
        case_success = (final_session.state == "END") and intent_matched and (slot_acc >= 0.8)
        if case_success:
            successes += 1
            
        avg_lat = sum(case_latencies)/len(case_latencies) if case_latencies else 0.0
        print(f"    State reached: {final_session.state}")
        print(f"    Intent Match : {intent_matched} (Expected: {case['expected_intent']}, Got: {final_session.intent})")
        print(f"    Slot Accuracy: {slot_acc*100:.1f}%")
        print(f"    Avg Latency  : {avg_lat:.1f}ms")
        print(f"    Slots        : {final_session.slots}")
        print(f"    Success      : {'PASS' if case_success else 'FAIL'}\n")
        
        results.append({
            "case_id": case["id"],
            "success": case_success,
            "intent_matched": intent_matched,
            "slot_accuracy": slot_acc,
            "latencies": case_latencies
        })

    # Calculate final scores
    success_rate = (successes / total_cases) * 100.0 if total_cases > 0 else 0.0
    avg_slot_acc = (sum(slot_accuracies) / total_cases) * 100.0 if total_cases > 0 else 0.0
    
    sorted_lat = sorted(all_latencies) if all_latencies else [0.0]
    n_lat = len(sorted_lat)
    p50 = sorted_lat[int(n_lat * 0.5)]
    p90 = sorted_lat[int(n_lat * 0.9)] if n_lat > 1 else sorted_lat[-1]
    p99 = sorted_lat[int(n_lat * 0.99)] if n_lat > 1 else sorted_lat[-1]
    
    print("==================================================")
    print("                EVALUATION SUMMARY                ")
    print("==================================================")
    print(f"Total Test Cases   : {total_cases}")
    print(f"Task Success Rate  : {success_rate:.2f}%")
    print(f"Avg Slot Accuracy  : {avg_slot_acc:.2f}%")
    print(f"p50 Latency        : {p50:.2f}ms")
    print(f"p90 Latency        : {p90:.2f}ms")
    print(f"p99 Latency        : {p99:.2f}ms")
    print("--------------------------------------------------")

    # Regression Checks
    if baseline:
        regression_found = False
        print("REGRESSION CHECK AGAINST BASELINE:")
        
        # 1. Success rate check
        b_success = baseline.get("overall_success_rate", 100.0)
        if success_rate < b_success:
            print(f" [!] REGRESSION: Success rate dropped to {success_rate:.1f}% (Baseline: {b_success:.1f}%)")
            regression_found = True
            
        # 2. Slot accuracy check
        b_slot = baseline.get("avg_slot_accuracy", 100.0)
        if avg_slot_acc < b_slot:
            print(f" [!] REGRESSION: Slot accuracy dropped to {avg_slot_acc:.1f}% (Baseline: {b_slot:.1f}%)")
            regression_found = True
            
        # 3. Latency check (allow 50ms buffer)
        b_p50 = baseline.get("p50_latency_ms", 50.0)
        if config_manager.settings.use_mock_llm:
            if p50 > b_p50 + 50.0:
                print(f" [!] SLOWDOWN: p50 latency increased to {p50:.1f}ms (Baseline: {b_p50:.1f}ms)")
                regression_found = True
        else:
            print(" [INFO] Skipping latency regression check since evaluation is running in Real/LLM mode.")
            
        if not regression_found:
            print(" [OK] All metrics pass. No regressions detected compared to baseline!")
        print("--------------------------------------------------")

    # 3. Write results to SQLite eval_runs table
    if DB_FILE.exists():
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eval_runs (
                    id TEXT PRIMARY KEY,
                    run_time DATETIME,
                    dataset_version TEXT,
                    total_cases INTEGER,
                    completed_cases INTEGER,
                    overall_success_rate REAL,
                    avg_slot_accuracy REAL,
                    p50_latency REAL,
                    p90_latency REAL,
                    p99_latency REAL,
                    raw_results TEXT
                )
            """)
            
            run_id = f"eval-cli-{uuid.uuid4().hex[:8]}"
            cursor.execute(
                "INSERT INTO eval_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    "1.0",
                    total_cases,
                    total_cases,
                    round(success_rate, 2),
                    round(avg_slot_acc, 2),
                    round(p50, 2),
                    round(p90, 2),
                    round(p99, 2),
                    json.dumps(results)
                )
            )
            conn.commit()
            conn.close()
            print("Successfully saved evaluation run scores to SQLite DB.")
        except Exception as e:
            print(f"Could not save evaluation to DB: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LocoVoice Automated Evaluation Simulator")
    parser.add_argument("--mode", choices=["mock", "real"], default=None, help="Force mock or real LLM/STT/TTS mode")
    args = parser.parse_args()
    
    run_eval(args.mode)
