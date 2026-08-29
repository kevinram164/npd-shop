# Kaniko-safe (venv --copies). Context: services/
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN python -m venv --copies /app/venv \
    && rm -f /app/venv/lib64 \
    && /app/venv/bin/pip install --upgrade pip \
    && /app/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /app/venv/bin/python -c "import uvicorn; print(uvicorn.__file__)" \
    && test -x /app/venv/bin/uvicorn

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/venv/bin:$PATH" \
    VIRTUAL_ENV=/app/venv \
    PORT=8004

WORKDIR /app
COPY --from=builder /app/venv /app/venv
COPY common ./common
COPY payment-worker/main.py ./main.py
RUN chmod -R a+rX /app && test -x /app/venv/bin/uvicorn

EXPOSE 8004
CMD ["/bin/sh", "-c", "echo '[noli-payment] starting on 8004' >&2; exec /app/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8004 --no-access-log"]
