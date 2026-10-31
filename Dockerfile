# Lightweight container for Whisper + Flask
FROM python:3.11-slim

# Install system dependencies for audio decoding (ffmpeg, libsndfile)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch CPU-only first to keep image small (<1GB instead of >4GB with CUDA)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Whisper model during build so startup is instant
ARG WHISPER_MODEL=tiny
ENV WHISPER_MODEL=${WHISPER_MODEL}
RUN python -c "import whisper; whisper.load_model('${WHISPER_MODEL}')"

# Copy app files
COPY . .

# Default port
ENV PORT=5000
EXPOSE 5000

# Run with Gunicorn (1 worker is recommended for CPU-bound Whisper inference)
CMD ["sh", "-c", "gunicorn -w 1 -b 0.0.0.0:$PORT --timeout 300 app:app"]

