# Lightweight image — no PyTorch, no local Whisper model
FROM python:3.11-slim

# Only libsndfile needed now (for soundfile audio header reads)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
EXPOSE 5000

# 2 workers OK now — no heavy in-memory model shared across workers
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app"]
