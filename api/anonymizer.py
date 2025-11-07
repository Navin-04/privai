import cv2
import pytesseract
import numpy as np
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine

nlp_engine = SpacyNlpEngine(models=[{"lang_code": "en", "model_name": "en_core_web_lg"}])


registry = RecognizerRegistry()
registry.load_predefined_recognizers()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
anonymizer = AnonymizerEngine()

# 📍 Path to local Tesseract installation
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🧩 Core anonymization for text
def anonymize_text(text: str) -> str:
    """
    Detects and replaces PII (names, emails, Aadhaar numbers, etc.) in text.
    """
    results = analyzer.analyze(text=text, language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text


# 🧩 Core anonymization for image
def anonymize_image(image: np.ndarray) -> np.ndarray:
    """
    Detects and blurs PII text and faces in an image.
    """

    # Extract text regions using OCR
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    for i, word in enumerate(data["text"]):
        word = word.strip()
        if not word:
            continue

        # Run Presidio on each OCR-detected word
        results = analyzer.analyze(text=word, language="en")

        # If sensitive info found → blur that region
        if results:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            roi = image[y:y+h, x:x+w]
            image[y:y+h, x:x+w] = cv2.GaussianBlur(roi, (25, 25), 30)

    # 🧠 Face detection + blurring
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    for (x, y, w, h) in faces:
        face_roi = image[y:y+h, x:x+w]
        image[y:y+h, x:x+w] = cv2.GaussianBlur(face_roi, (99, 99), 30)

    return image


# 🧩 Utility: Anonymize text inside image and return the text result
def extract_and_anonymize_text_from_image(image: np.ndarray) -> str:
    """
    Extracts text from an image using Tesseract OCR, then anonymizes it.
    Returns anonymized text for logging or verification.
    """
    text = pytesseract.image_to_string(image)
    return anonymize_text(text)
