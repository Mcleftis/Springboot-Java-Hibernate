FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY rag_worker.py .
EXPOSE 8002
CMD ["python", "rag_worker.py"]
