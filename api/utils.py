# api/utils.py
import os
import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from io import BytesIO
import tempfile
import pytesseract

# Configure tesseract path (adjust if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------------------------------------------------------------------
# 🧠 OCR + Preprocessing Utilities
# ---------------------------------------------------------------------
def preprocess_image(image_bgr: np.ndarray) -> np.ndarray:
    """
    Clean up and enhance image before OCR.
    Helps on scanned PDFs and slightly blurry uploads.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)  # smooth but preserve edges
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY, 31, 10)
    processed = cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)
    return processed


def extract_text_data(image_bgr: np.ndarray) -> dict:
    """
    Run OCR on the image and return detailed word-level data.
    Returns pytesseract image_to_data dictionary.
    """
    processed = preprocess_image(image_bgr)
    tess_config = r"--oem 3 --psm 6"  # LSTM mode, assume a block of text
    data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT, config=tess_config)
    return data


def extract_text_raw(image_bgr: np.ndarray) -> str:
    """Return plain text OCR output (no bounding boxes)."""
    processed = preprocess_image(image_bgr)
    text = pytesseract.image_to_string(processed, config="--oem 3 --psm 6")
    return text.strip()


# ---------------------------------------------------------------------
# 📄 PDF ↔ Image Helpers
# ---------------------------------------------------------------------
def pdf_to_images(pdf_bytes: bytes, dpi: int = 150) -> list[np.ndarray]:
    """
    Convert PDF bytes into a list of OpenCV BGR images.
    Each page becomes one numpy array.
    """
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in pdf_doc:
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pages.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
    return pages


def images_to_pdf(images_rgb: list[np.ndarray]) -> BytesIO:
    """
    Combine a list of RGB numpy arrays into a single in-memory PDF.
    """
    pdf_bytes = BytesIO()
    pil_images = [Image.fromarray(img) for img in images_rgb]
    pil_images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=pil_images[1:])
    pdf_bytes.seek(0)
    return pdf_bytes


# ---------------------------------------------------------------------
# 🧾 File Helpers
# ---------------------------------------------------------------------
def save_temp_file(data: bytes, suffix: str) -> str:
    """
    Save raw bytes as a temporary file (auto-deleted after restart).
    Returns the file path.
    """
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, f"temp_{os.getpid()}{suffix}")
    with open(path, "wb") as f:
        f.write(data)
    return path


def save_image_temp(image_rgb: np.ndarray, suffix: str = ".png") -> str:
    """
    Save numpy RGB image as temporary file and return path.
    """
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, f"anon_{os.getpid()}{suffix}")
    Image.fromarray(image_rgb).save(path)
    return path


# ---------------------------------------------------------------------
# 🧩 Debug / Logging Helper (Optional)
# ---------------------------------------------------------------------
def debug_log(*args):
    """Simple console logger (useful for API debugging)."""
    print("🧩 [DEBUG]", *args)
