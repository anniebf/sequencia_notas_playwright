FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DIRETORIO_PADRAO=/app \
    CONFIG_DIR=/config

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY sequencanotas_pw ./sequencanotas_pw

RUN mkdir -p /app/data/download /app/data/csv /app/data/captcha /app/data/log

ENTRYPOINT ["python", "-m", "sequencanotas_pw.main"]