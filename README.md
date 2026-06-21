# PrivAI

PrivAI is a Streamlit frontend plus a FastAPI backend for anonymizing text, images, and PDFs using Presidio, spaCy, OCR, and face blurring.

## What was fixed

- The frontend now reads `BACKEND_URL` from environment variables instead of assuming `127.0.0.1:8080`.
- The backend now streams files from memory, which avoids temp-file collisions between simultaneous users.
- Tesseract and the spaCy model are now configurable for Windows, Docker, and Linux hosting.
- The repository now includes `start_services.py` so both backend and frontend can start together with one command.
- Docker now installs the OCR system dependency and starts both services instead of only Streamlit.

## Local Run

### 1. Install prerequisites

- Python `3.11`
- Tesseract OCR
- The packages in [requirements.txt](/D:/privai/requirements.txt)
- The spaCy English model set in `SPACY_MODEL` (default: `en_core_web_sm`)

### 2. Create a virtual environment and install dependencies

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Configure environment

Copy [.env.example](/D:/privai/.env.example) into your environment or set the values manually.

Important:

- On Windows, set `TESSERACT_CMD` to your local Tesseract path.
- On Docker/Linux, `/usr/bin/tesseract` is the default.

### 4. Start the app

```powershell
python start_services.py
```

Then open `http://localhost:8501`.

## Docker Run

```powershell
docker build -t privai .
docker run -p 8501:8501 -p 8080:8080 privai
```

Then open `http://localhost:8501`.

## Recommended Hosting Path

The simplest production path is a single Docker deployment on a VM, Railway, or Render Docker service. This repo now supports that path directly.

Recommended environment variables:

- `BACKEND_URL=http://127.0.0.1:8080`
- `API_PORT=8080`
- `STREAMLIT_PORT=8501`
- `SPACY_MODEL=en_core_web_sm`
- `TESSERACT_CMD=/usr/bin/tesseract`
- `CORS_ALLOW_ORIGINS=https://your-frontend-domain`

## Alternatives

### Option 1. Single container

Best for:

- fastest launch
- demo use
- small traffic

Tradeoffs:

- simplest setup
- weaker scaling separation between UI and API

### Option 2. Split frontend and backend into two services

Best for:

- better scaling
- cleaner operations
- future mobile/API reuse

Tradeoffs:

- more configuration
- must set `BACKEND_URL` to the backend public URL
- must lock `CORS_ALLOW_ORIGINS` to the frontend domain

### Option 3. Replace Streamlit with a standard web frontend later

Best for:

- custom onboarding
- richer multi-user UX
- auth, dashboards, history, usage controls

Tradeoffs:

- higher build effort
- more frontend engineering work

## New-User Readiness Checklist

- Add onboarding text that explains supported file types and expected processing time.
- Add authentication if private files will be uploaded by real users.
- Add file size limits and request timeouts at the hosting layer.
- Add logging and error monitoring.
- Add a queue or background worker if PDF uploads become large.
- Add tests for text, image, and PDF flows before public launch.

## Implementation Plan

### Phase 1. Get it running

1. Install Python 3.11, Tesseract, and Python dependencies.
2. Download the spaCy model.
3. Run `python start_services.py`.
4. Verify `http://localhost:8501` and `http://localhost:8080/health`.

### Phase 2. Deploy

1. Build the Docker image.
2. Deploy the container to a host that supports Python plus system packages.
3. Set production environment variables.
4. Validate text, image, and PDF uploads against the deployed URL.

### Phase 3. Prepare for external users

1. Add authentication or access control.
2. Add upload-size limits and rate limiting.
3. Add structured logging and uptime monitoring.
4. Add regression tests.
5. Add a privacy policy and retention policy if storing any files or logs.
