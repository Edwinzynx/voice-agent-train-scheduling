import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

# Monkeypatch DB_FILE in run_eval to a non-existent file in a subfolder so it fails the exists() check
import eval.run_eval as run_eval
run_eval.DB_FILE = Path("non_existent_db_file_path_eval.db")

print("Running offline evaluation with database write disabled...")
try:
    run_eval.run_eval(mode="mock")
except Exception as e:
    print("Evaluation encountered an error:", e)
