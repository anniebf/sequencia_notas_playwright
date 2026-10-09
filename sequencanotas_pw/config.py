from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    root: Path
    params_file: Path
    contabilista: str
    senha_contabilista: str
    download_dir: Path
    csv_dir: Path
    captcha_dir: Path
    log_dir: Path
    producao_dir: Path | None
    headless: bool
    anti_captcha_token: str | None
    username_bd: str | None
    password_bd: str | None
    dsn: str | None


def load_config() -> Config:
    root = Path(__file__).resolve().parents[1]
    config_dir = Path(os.getenv("CONFIG_DIR", "/config"))
    load_dotenv(config_dir / ".env")
    configured_params = os.getenv("SEQUENCIA_NOTAS_PARAMS")
    mounted_params = config_dir / "params.json"
    local_params = root / "params.json"
    legacy_params = root.parent / "SequenciaNotas" / "parametros_contabilista" / "params.json"
    alternate_legacy_params = root.parent / "SequenciaNotas" / "sequencianotas" / "params.json"
    candidates = (
        (Path(configured_params),) if configured_params else ()
    ) + (mounted_params, local_params, legacy_params, alternate_legacy_params)
    params_file = next((candidate for candidate in candidates if candidate.is_file()), None)
    env_contabilista = os.getenv("CONTABILISTA")
    env_senha_contabilista = os.getenv("SENHA_CONTABILISTA")
    if params_file is None and not (env_contabilista and env_senha_contabilista):
        params_file = local_params
        raise FileNotFoundError(
            f"Arquivo de parametros nao encontrado: {params_file}. "
            "Copie params.example.json para params.json, defina "
            "SEQUENCIA_NOTAS_PARAMS ou informe CONTABILISTA e SENHA_CONTABILISTA."
        )

    params_file = params_file or local_params
    params = (
        json.loads(params_file.read_text(encoding="utf-8"))
        if params_file.is_file()
        else {}
    )
    required = ("contabilista", "senha_contabilista")
    params["contabilista"] = (
        env_contabilista or params.get("contabilista")
    )
    params["senha_contabilista"] = (
        env_senha_contabilista or params.get("senha_contabilista")
    )
    missing = [key for key in required if not params.get(key)]
    if missing:
        raise ValueError(f"Parametros obrigatorios ausentes: {', '.join(missing)}")

    production = os.getenv("SEQUENCIA_NOTAS_PRODUCAO", "").strip()
    return Config(
        root=root,
        params_file=params_file,
        contabilista=str(params["contabilista"]),
        senha_contabilista=str(params["senha_contabilista"]),
        download_dir=root / "data" / "download",
        csv_dir=root / "data" / "csv",
        captcha_dir=root / "data" / "captcha",
        log_dir=root / "data" / "log",
        producao_dir=Path(production) if production else None,
        headless=os.getenv("SEQUENCIA_NOTAS_HEADLESS", "true").lower() not in {"0", "false", "no"},
        anti_captcha_token=os.getenv("ANTI_CAPTCHA_TOKEN") or os.getenv("token"),
        username_bd=os.getenv("usernameBd"),
        password_bd=os.getenv("passwordBd"),
        dsn=os.getenv("dsn"),
    )
