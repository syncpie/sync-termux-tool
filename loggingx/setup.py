import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("event", "duration_ms", "details"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level=logging.INFO):
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    formatter = JsonFormatter()
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "termuxpulse.jsonl", maxBytes=2 * 1024 * 1024,
        backupCount=5, encoding="utf-8"
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(formatter)

    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.jsonl", maxBytes=1024 * 1024,
        backupCount=3, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    root.addHandler(app_handler)
    root.addHandler(error_handler)
    root.addHandler(console)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.getLogger("termuxpulse.crash").critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback),
            extra={"event": "uncaught_exception"}
        )

    sys.excepthook = handle_exception
    logging.getLogger("termuxpulse").info(
        "Logging initialized", extra={"event": "logging_started"}
    )
    return logging.getLogger("termuxpulse")
