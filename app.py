import os

import fitz  # PyMuPDF
import streamlit as st
import requests
from PIL import Image

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080").rstrip("/")
REQUEST_TIMEOUT = (10, 180)


def create_upload_payload(uploaded_file) -> dict[str, tuple[str, bytes, str]]:
    return {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }


def render_pdf_preview(pdf_bytes: bytes) -> Image.Image:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        if document.page_count == 0:
            raise ValueError("The uploaded PDF has no pages.")

        page = document.load_page(0)
        pixmap = page.get_pixmap(dpi=150)
        return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)


def backend_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    return payload.get("error") or payload.get("detail") or response.text or "Unknown backend error."


def call_backend(path: str, *, files=None, data=None) -> requests.Response:
    response = requests.post(
        f"{BACKEND_URL}{path}",
        files=files,
        data=data,
        timeout=REQUEST_TIMEOUT,
    )
    return response


def backend_is_available() -> bool:
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.ok
    except requests.RequestException:
        return False

# 🎨 Streamlit setup
st.set_page_config(page_title="PrivAI – Smart PII Anonymizer", layout="wide")
st.title("🕶️ PrivAI – Smart PII Anonymizer")
st.caption("Upload any file (PDF, image, or text). PrivAI detects and removes personal data using AI-powered anonymization.")

if not backend_is_available():
    st.warning(
        f"Backend is not reachable at `{BACKEND_URL}`. "
        "Start the API service before processing files."
    )

uploaded_file = st.file_uploader("📎 Upload a file (PDF, Image, or Text file)", type=["pdf", "png", "jpg", "jpeg", "txt"])
text_input = st.text_area("✍️ Or directly enter text", height=150)

# 🧠 Process Button
if st.button("🧠 Anonymize"):
    if uploaded_file:
        file_type = uploaded_file.type
        with st.spinner("Analyzing and anonymizing..."):
            try:
                if "pdf" in file_type:
                    original_pdf = uploaded_file.getvalue()
                    img = render_pdf_preview(original_pdf)

                    # Send PDF to backend
                    response = call_backend("/anonymize/pdf", files=create_upload_payload(uploaded_file))

                    if response.status_code == 200:
                        anon_img = render_pdf_preview(response.content)

                        # Display preview
                        st.subheader("📄 Preview (First Page)")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(img, caption="🔹 Original PDF (Page 1)", use_container_width=True)
                        with col2:
                            st.image(anon_img, caption="🔒 Anonymized PDF (Page 1)", use_container_width=True)

                        st.success("✅ PDF Anonymized Successfully!")
                        st.download_button(
                            "💾 Download Anonymized PDF",
                            data=response.content,
                            file_name="anonymized_output.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error(f"⚠️ Failed to process the PDF. {backend_error_message(response)}")

                elif "image" in file_type:
                    # Image anonymization
                    response = call_backend("/anonymize/image", files=create_upload_payload(uploaded_file))
                    if response.status_code == 200:
                        st.subheader("🖼️ Before and After")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(uploaded_file, caption="🔹 Original Image", use_container_width=True)
                        with col2:
                            st.image(response.content, caption="🔒 Anonymized Image", use_container_width=True)
                        st.download_button(
                            "💾 Download Anonymized Image",
                            data=response.content,
                            file_name="anonymized_image.png",
                            mime="image/png"
                        )
                    else:
                        st.error(f"⚠️ Could not process image. {backend_error_message(response)}")

                elif "text" in file_type or uploaded_file.name.endswith(".txt"):
                    # Text file anonymization
                    content = uploaded_file.getvalue().decode("utf-8", errors="replace")
                    response = call_backend("/anonymize/text", data={"text": content})
                    if response.status_code == 200:
                        result = response.json()
                        st.subheader("📜 Before and After")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.code(result["original_text"], language="text")
                        with col2:
                            st.code(result["anonymized_text"], language="text")
                    else:
                        st.error(f"⚠️ Failed to process text file. {backend_error_message(response)}")
                else:
                    st.error("Unsupported file type.")

            except requests.RequestException as e:
                st.error(f"Backend request failed: {e}")
            except Exception as e:
                st.error(f"Error: {e}")

    elif text_input.strip():
        # Raw text anonymization
        try:
            with st.spinner("Processing text..."):
                response = call_backend("/anonymize/text", data={"text": text_input})
            if response.status_code == 200:
                result = response.json()
                st.subheader("📜 Before and After")
                col1, col2 = st.columns(2)
                with col1:
                    st.code(result["original_text"], language="text")
                with col2:
                    st.code(result["anonymized_text"], language="text")
            else:
                st.error(f"⚠️ Could not process entered text. {backend_error_message(response)}")
        except requests.RequestException as e:
            st.error(f"Backend request failed: {e}")
    else:
        st.warning("Please upload a file or enter text to proceed.")
