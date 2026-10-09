from __future__ import annotations

import logging
from pathlib import Path
from datetime import datetime


def configure_logging(directory: Path) -> logging.Logger:
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("sequencia_notas_pw")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(directory / f"execucao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.addHandler(logging.StreamHandler())
    return logger
