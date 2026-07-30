FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app

RUN mkdir -p /app/data/processed /app/data/embeddings

COPY ./init_ollama.py /app/init_ollama.py
COPY ./ingest_sample_data.py /app/ingest_sample_data.py

EXPOSE 8000

CMD ["sh", "-c", "python /app/init_ollama.py & uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
