ARG SERVICE_DIR=gateway
ARG PORT=8080

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common ./common
ARG SERVICE_DIR
ARG PORT
COPY ${SERVICE_DIR}/main.py ./main.py
ENV PYTHONPATH=/app
ENV PORT=${PORT}
EXPOSE ${PORT}
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
