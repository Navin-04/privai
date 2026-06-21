import os
from io import BytesIO

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

from api.anonymizer import anonymize_image, anonymize_text
from api.utils import images_to_pdf, pdf_to_images

app = FastAPI(title="PrivAI - PII Anonymization API", version="1.0")


def _allowed_origins() -> list[str]:
    raw_origins = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    )
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["*"]


cors_origins = _allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to PrivAI Backend 👁‍🗨", "status": "active"}


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "ok"}


@app.post("/anonymize/text", tags=["PII Processing"])
async def anonymize_text_api(text: str = Form(...)):
    """
    Accepts raw text input and returns anonymized text.
    """
    anonymized_output = anonymize_text(text)
    return {"original_text": text, "anonymized_text": anonymized_output}


@app.post("/anonymize/image", tags=["PII Processing"])
async def anonymize_image_api(file: UploadFile = File(...)):
    """
    Accepts an image file (PNG/JPG) and returns anonymized version.
    """
    try:
        contents = await file.read()
        image = np.array(Image.open(BytesIO(contents)).convert("RGB"))
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        anonymized = anonymize_image(image_bgr)
        anonymized_rgb = cv2.cvtColor(anonymized, cv2.COLOR_BGR2RGB)

        output = BytesIO()
        Image.fromarray(anonymized_rgb).save(output, format="PNG")
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="image/png",
            headers={
                "Content-Disposition": 'attachment; filename="anonymized_image.png"'
            },
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/anonymize/pdf", tags=["PII Processing"])
async def anonymize_pdf_api(file: UploadFile = File(...)):
    """
    Accepts a PDF, converts each page to an image, anonymizes it, then returns a combined redacted PDF.
    """
    try:
        contents = await file.read()
        pages = pdf_to_images(contents)
        if not pages:
            return JSONResponse(
                status_code=400,
                content={"error": "Uploaded PDF does not contain any pages."},
            )

        output_images = []
        for page in pages:
            page.setflags(write=1)
            anon_img = anonymize_image(page)
            output_images.append(cv2.cvtColor(anon_img, cv2.COLOR_BGR2RGB))

        output_pdf = images_to_pdf(output_images)
        return StreamingResponse(
            output_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="anonymized_output.pdf"'
            },
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# 🧩 Optional: Favicon handler to clean logs
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return JSONResponse(status_code=204, content={})
