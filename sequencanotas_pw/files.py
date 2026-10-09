from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd


def convert_download_to_csv(download: Path, csv_dir: Path, name: str) -> Path:
    csv_dir.mkdir(parents=True, exist_ok=True)
    try:
        frame = pd.read_excel(download).iloc[5:]
    except (OSError, ValueError, ImportError) as exc:
        raise RuntimeError(f"Nao foi possivel ler o Excel exportado para {name}.") from exc

    if frame.empty:
        raise RuntimeError(f"Arquivo exportado para {name} nao possui registros.")

    target = csv_dir / f"{name}.csv"
    frame.to_csv(target, header=False, index=False, sep=";")
    if not target.exists() or target.stat().st_size <= 20:
        raise RuntimeError(f"Arquivo exportado para {name} esta vazio ou corrompido.")
    download.unlink(missing_ok=True)
    return target


def copy_to_production(source: Path, production: Path | None) -> None:
    if production is None:
        return
    production.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, production / source.name)
