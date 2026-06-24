FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY quant_worker.py .
EXPOSE 8003
CMD ["python", "quant_worker.py"]
