import json
from pathlib import Path
from datetime import datetime
from config import REPORTS_PATH

def export_report(snapshot, history):
    folder = Path(REPORTS_PATH)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"termuxpulse-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    payload = {"generated_at": datetime.now().isoformat(), "snapshot": snapshot, "history": history}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return str(path)
