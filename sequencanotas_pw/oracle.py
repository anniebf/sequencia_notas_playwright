from __future__ import annotations

import os

import oracledb

from .config import Config


def retorno_cnpjs(config: Config) -> list[str]:
    if not all((config.username_bd, config.password_bd, config.dsn)):
        raise RuntimeError("Defina usernameBd, passwordBd e dsn no arquivo .env.")
    query = """
        SELECT M0_CGC
        FROM PROTHEUS11.sigaemp
        WHERE LENGTH(TRIM(M0_CGC)) >= 12
          AND (m0_insc NOT IN ('ISENTO', ' ') OR m0_insc IS NULL)
    """
    with oracledb.connect(
        user=config.username_bd,
        password=config.password_bd,
        dsn=config.dsn,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return [str(row[0]).strip() for row in cursor.fetchall() if row[0]]
