import logging
import sys
from pathlib import Path
from app.core.config import settings

log_dir = Path(settings.LOG_DIR)


def setup_logging():
    handlers = [logging.StreamHandler(sys.stdout)]

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / 'app.log')
        handlers.insert(0, file_handler)
    except OSError as exc:
        logging.getLogger(__name__).warning('File logging disabled: %s', exc)

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
    )

    for logger_name in [
        'uvicorn',
        'fastapi',
        'app',
        'celery',
        'motor',
    ]:
        logging.getLogger(logger_name).setLevel(getattr(logging, settings.LOG_LEVEL.upper()))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
