FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lstm_worker.py .
EXPOSE 8004
CMD ["python", "lstm_worker.py"]
