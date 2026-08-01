FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common ./common
COPY order-service/main.py ./main.py
ENV PYTHONPATH=/app
ENV PORT=8003
EXPOSE 8003
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
