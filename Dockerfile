# Base image
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BACKEND_URL=http://127.0.0.1:8080 \
    API_PORT=8080 \
    STREAMLIT_PORT=8501 \
    SPACY_MODEL=en_core_web_sm \
    TESSERACT_CMD=/usr/bin/tesseract \
    CORS_ALLOW_ORIGINS=http://localhost:8501,http://127.0.0.1:8501

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download ${SPACY_MODEL}

COPY . .

EXPOSE 8080 8501

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=5)"]

CMD ["python", "start_services.py"]
