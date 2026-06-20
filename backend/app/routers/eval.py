import json
import uuid
import time
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import EvalRun
from ..brain.fsm import FSMCoordinator

router = APIRouter(
    prefix="/eval",
    tags=["eval"]
)

from pathlib import Path

# Hardcoded default eval dataset fallback
DEFAULT_EVAL_DATASET = [
    {
        "id": "scenario-1-search",
        "description": "Standard train search from Delhi to Varanasi in English",
        "turns": [
            "Hello, I want to find trains.",
            "From Delhi",
            "To Varanasi",
            "For tomorrow please",
            "Yes, that's correct.",
            "No, thank you."
        ],
        "expected_intent": "FIND_TRAINS",
        "expected_slots": {
            "source": "Delhi",
            "destination": "Varanasi",
            "date": "2026-06-19"
        }
    },
    {
        "id": "scenario-2-book-hinglish",
        "description": "Stateful ticket booking in Hinglish with passenger details",
        "turns": [
            "Bhai ek ticket book karni hai.",
            "Delhi se Bhopal",
            "Kal chalna hai",
            "Sleeper coach chahiye",
            "Yatri ka naam hai Amit",
            "Haan ticket confirm kar do",
            "Nahi, bas, thank you."
        ],
        "expected_intent": "BOOK_TICKET",
        "expected_slots": {
            "source": "Delhi",
            "destination": "Bhopal",
            "date": "2026-06-19",
            "class_code": "SL",
            "passenger_name": "Amit"
        }
    },
    {
        "id": "scenario-3-status",
        "description": "PNR status check for existing booking",
        "turns": [
            "Mujhe PNR status check karna hai",
            "PNR number hai 4829384729",
            "Yes",
            "No, that is all."
        ],
        "expected_intent": "GET_PNR_STATUS",
        "expected_slots": {
            "pnr_number": "4829384729"
        }
    },
    {
        "id": "scenario-4-cancel-hindi",
        "description": "Ticket cancellation in Hindi",
        "turns": [
            "Mera ticket cancel kar do.",
            "Das digit number hai 4829384729",
            "Haan cancel kar dijiye",
            "No, thanks."
        ],
        "expected_intent": "CANCEL_TICKET",
        "expected_slots": {
            "pnr_number": "4829384729"
        }
    }
]

def load_eval_dataset():
    eval_dir = Path(__file__).resolve().parent.parent.parent.parent / "eval"
    dataset_file = eval_dir / "dataset.json"
    if dataset_file.exists():
        try:
            with open(dataset_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading eval dataset from file: {e}")
    return DEFAULT_EVAL_DATASET

async def run_evaluation_task(run_id: str, db_session_creator):
    """
    Simulates conversations turn-by-turn and calculates evaluation metrics.
    Runs in background task.
    """
    db = db_session_creator()
    try:
        eval_run_rec = db.query(EvalRun).filter(EvalRun.id == run_id).first()
        if not eval_run_rec:
            return
            
        dataset = load_eval_dataset()
        results = []
        total_cases = len(dataset)
        completed_cases = 0
        successes = 0
        slot_accuracies = []
        all_latencies = []
        
        for case in dataset:
            coordinator = FSMCoordinator()
            case_id = f"eval-sim-{uuid.uuid4().hex[:6]}"
            session = coordinator.get_or_create_session(case_id)
            
            # Start FSM GREET state
            coordinator.process_turn(case_id, "GREET")
            
            case_latencies = []
            
            # Pipe turns
            for turn in case["turns"]:
                start_time = time.time()
                # Run the turn
                coordinator.process_turn(case_id, turn)
                elapsed_ms = (time.time() - start_time) * 1000
                case_latencies.append(elapsed_ms)
                all_latencies.append(elapsed_ms)
                # Sleep to stay under Groq's 6000 TPM limit
                from ..config import config_manager
                if not config_manager.settings.use_mock_llm:
                    await asyncio.sleep(8.0)
                else:
                    await asyncio.sleep(0.01)
                
            # Verify results
            final_session = coordinator.sessions[case_id]
            
            # 1. Intent accuracy
            intent_ok = final_session.intent == case["expected_intent"]
            
            # 2. Slot accuracy
            slot_matches = 0
            total_expected_slots = len(case["expected_slots"])
            for slot_key, expected_val in case["expected_slots"].items():
                actual_val = final_session.slots.get(slot_key)
                if actual_val and expected_val.lower() in str(actual_val).lower():
                    slot_matches += 1
            
            slot_acc = (slot_matches / total_expected_slots) if total_expected_slots > 0 else 1.0
            slot_accuracies.append(slot_acc)
            
            # 3. Overall success
            # Success means we hit END state, intent matched, and slots are filled
            case_success = (final_session.state == "END") and intent_ok and (slot_acc >= 0.8)
            if case_success:
                successes += 1
                
            results.append({
                "case_id": case["id"],
                "description": case["description"],
                "success": case_success,
                "intent_matched": intent_ok,
                "slot_accuracy": slot_acc,
                "latencies_ms": case_latencies,
                "avg_latency": sum(case_latencies)/len(case_latencies) if case_latencies else 0.0,
                "final_state": final_session.state,
                "slots": final_session.slots
            })
            
            completed_cases += 1
            eval_run_rec.completed_cases = completed_cases
            db.commit()

        # Compute stats
        success_rate = (successes / total_cases) * 100.0 if total_cases > 0 else 0.0
        avg_slot_acc = (sum(slot_accuracies) / total_cases) * 100.0 if total_cases > 0 else 0.0
        
        sorted_lat = sorted(all_latencies) if all_latencies else [0.0]
        n_lat = len(sorted_lat)
        p50 = sorted_lat[int(n_lat * 0.5)]
        p90 = sorted_lat[int(n_lat * 0.9)] if n_lat > 1 else sorted_lat[-1]
        p99 = sorted_lat[int(n_lat * 0.99)] if n_lat > 1 else sorted_lat[-1]
        
        eval_run_rec.overall_success_rate = round(success_rate, 2)
        eval_run_rec.avg_slot_accuracy = round(avg_slot_acc, 2)
        eval_run_rec.p50_latency = round(p50, 2)
        eval_run_rec.p90_latency = round(p90, 2)
        eval_run_rec.p99_latency = round(p99, 2)
        eval_run_rec.raw_results = json.dumps(results)
        
        db.commit()
    except Exception as e:
        logger.error(f"Error executing evaluation suite: {e}")
    finally:
        db.close()

@router.post("/run")
def trigger_eval(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Triggers an async evaluation run and returns a tracking ID.
    """
    run_id = f"eval-run-{uuid.uuid4().hex[:8]}"
    
    # Save skeleton run record
    eval_rec = EvalRun(
        id=run_id,
        run_time=datetime.utcnow(),
        total_cases=len(DEFAULT_EVAL_DATASET),
        completed_cases=0
    )
    db.add(eval_rec)
    db.commit()
    
    # Run simulation in the background
    from ..database import SessionLocal
    background_tasks.add_task(run_evaluation_task, run_id, SessionLocal)
    
    return {
        "success": True,
        "eval_run_id": run_id,
        "message": "Evaluation simulation suite launched."
    }

@router.get("/runs")
def get_eval_runs(db: Session = Depends(get_db)):
    """
    Returns list of all historical evaluation runs.
    """
    runs = db.query(EvalRun).order_by(EvalRun.run_time.desc()).all()
    # Parse JSON list inside raw_results if needed by frontend
    parsed_runs = []
    for run in runs:
        parsed_runs.append({
            "id": run.id,
            "run_time": run.run_time,
            "dataset_version": run.dataset_version,
            "total_cases": run.total_cases,
            "completed_cases": run.completed_cases,
            "overall_success_rate": run.overall_success_rate,
            "avg_slot_accuracy": run.avg_slot_accuracy,
            "p50_latency": run.p50_latency,
            "p90_latency": run.p90_latency,
            "p99_latency": run.p99_latency,
            "results": json.loads(run.raw_results) if run.raw_results else []
        })
    return parsed_runs
