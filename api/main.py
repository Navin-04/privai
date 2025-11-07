from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, cv2, numpy as np, fitz
from PIL import Image
from io import BytesIO

# 🧠 Import your anonymization functions
from api.anonymizer import anonymize_image, anonymize_text

app = FastAPI(title="PrivAI - PII Anonymization API", version="1.0")

# 🔓 Allow connections from frontend (Streamlit or browser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🏠 Root route
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to PrivAI Backend 👁‍🗨", "status": "active"}


# 🧾 Text anonymization endpoint
@app.post("/anonymize/text", tags=["PII Processing"])
async def anonymize_text_api(text: str = Form(...)):
    """
    Accepts raw text input and returns anonymized text.
    """
    anonymized_output = anonymize_text(text)
    return {"original_text": text, "anonymized_text": anonymized_output}


# 🖼️ Image anonymization endpoint
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

        output_path = os.path.join(tempfile.gettempdir(), "anonymized_image.png")
        Image.fromarray(anonymized_rgb).save(output_path)

        return FileResponse(output_path, media_type="image/png", filename="anonymized_image.png")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# 📄 PDF anonymization endpoint
@app.post("/anonymize/pdf", tags=["PII Processing"])
async def anonymize_pdf_api(file: UploadFile = File(...)):
    """
    Accepts a PDF, converts each page to an image, anonymizes it, then returns a combined redacted PDF.
    """
    try:
        contents = await file.read()
        temp_dir = tempfile.mkdtemp()
        input_pdf = os.path.join(temp_dir, file.filename)

        with open(input_pdf, "wb") as f:
            f.write(contents)

        doc = fitz.open(input_pdf)
        output_images = []

        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            img_np.setflags(write=1)
            anon_img = anonymize_image(img_np)
            output_images.append(Image.fromarray(cv2.cvtColor(anon_img, cv2.COLOR_BGR2RGB)))

        output_pdf_path = os.path.join(tempfile.gettempdir(), "anonymized_output.pdf")
        output_images[0].save(output_pdf_path, save_all=True, append_images=output_images[1:])

        return FileResponse(output_pdf_path, media_type="application/pdf", filename="anonymized_output.pdf")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# 🧩 Optional: Favicon handler to clean logs
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return JSONResponse(status_code=204, content={})
