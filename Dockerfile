# Base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Prevents Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download smaller spaCy model
RUN python -m spacy download en_core_web_sm

# Copy app files
COPY . .

# Clean up pip and temp files to save memory
RUN rm -rf /root/.cache/pip /tmp/*

# Expose the port used by Streamlit or FastAPI
EXPOSE 8501

# Start Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
