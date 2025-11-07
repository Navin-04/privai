# =============================
# PrivAI Deployment Dockerfile
# =============================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for Tesseract + OpenCV)
RUN apt-get update && apt-get install -y \
    tesseract-ocr libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_lg

# Copy the entire project
COPY . .

# Expose the Streamlit port
EXPOSE 8501

# Start both FastAPI (backend) and Streamlit (frontend)
CMD uvicorn api.main:app --host 0.0.0.0 --port 8080 & \
    streamlit run app.py --server.port 8501 --server.address 0.0.0.0
