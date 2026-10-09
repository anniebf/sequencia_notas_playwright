from datetime import datetime, timedelta


def gerar_intervalo_datas() -> tuple[str, str]:
    hoje = datetime.now()
    if hoje.day < 16:
        ultimo_dia = datetime(hoje.year, hoje.month, 1) - timedelta(days=1)
        primeiro_dia = ultimo_dia.replace(day=1)
    else:
        primeiro_dia = hoje.replace(day=1)
        if hoje.month == 12:
            proximo_mes = datetime(hoje.year + 1, 1, 1)
        else:
            proximo_mes = datetime(hoje.year, hoje.month + 1, 1)
        ultimo_dia = proximo_mes - timedelta(days=1)
    return primeiro_dia.strftime("%d%m%Y"), ultimo_dia.strftime("%d%m%Y")
