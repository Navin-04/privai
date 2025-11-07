import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
import tempfile

# 🌐 Backend URL
BACKEND_URL = "http://127.0.0.1:8080"

# 🎨 Streamlit setup
st.set_page_config(page_title="PrivAI – Smart PII Anonymizer", layout="wide")
st.title("🕶️ PrivAI – Smart PII Anonymizer")
st.caption("Upload any file (PDF, image, or text). PrivAI detects and removes personal data using AI-powered anonymization.")

uploaded_file = st.file_uploader("📎 Upload a file (PDF, Image, or Text file)", type=["pdf", "png", "jpg", "jpeg", "txt"])
text_input = st.text_area("✍️ Or directly enter text", height=150)

# 🧠 Process Button
if st.button("🧠 Anonymize"):
    if uploaded_file:
        file_type = uploaded_file.type
        with st.spinner("Analyzing and anonymizing..."):
            try:
                if "pdf" in file_type:
                    # Save uploaded PDF temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        pdf_path = tmp.name

                    # Convert first page to image for preview
                    doc = fitz.open(pdf_path)
                    page = doc.load_page(0)
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    doc.close()

                    # Send PDF to backend
                    files = {"file": uploaded_file.getvalue()}
                    response = requests.post(f"{BACKEND_URL}/anonymize/pdf", files=files)

                    if response.status_code == 200:
                        # Create temp PDF for after preview
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
                            tmp_out.write(response.content)
                            anon_pdf_path = tmp_out.name

                        # Extract first page of anonymized PDF
                        anon_doc = fitz.open(anon_pdf_path)
                        anon_page = anon_doc.load_page(0)
                        anon_pix = anon_page.get_pixmap(dpi=150)
                        anon_img = Image.frombytes("RGB", [anon_pix.width, anon_pix.height], anon_pix.samples)
                        anon_doc.close()

                        # Display preview
                        st.subheader("📄 Preview (First Page)")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(img, caption="🔹 Original PDF (Page 1)", width='stretch')
                        with col2:
                            st.image(anon_img, caption="🔒 Anonymized PDF (Page 1)", width='stretch')

                        st.success("✅ PDF Anonymized Successfully!")
                        st.download_button(
                            "💾 Download Anonymized PDF",
                            data=response.content,
                            file_name="anonymized_output.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("⚠️ Failed to process the PDF.")

                elif "image" in file_type:
                    # Image anonymization
                    files = {"file": uploaded_file.getvalue()}
                    response = requests.post(f"{BACKEND_URL}/anonymize/image", files=files)
                    if response.status_code == 200:
                        st.subheader("🖼️ Before and After")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(uploaded_file, caption="🔹 Original Image", width='stretch')
                        with col2:
                            st.image(response.content, caption="🔒 Anonymized Image", width='stretch')
                        st.download_button(
                            "💾 Download Anonymized Image",
                            data=response.content,
                            file_name="anonymized_image.png",
                            mime="image/png"
                        )
                    else:
                        st.error("⚠️ Could not process image.")

                elif "text" in file_type or uploaded_file.name.endswith(".txt"):
                    # Text file anonymization
                    content = uploaded_file.read().decode("utf-8")
                    response = requests.post(f"{BACKEND_URL}/anonymize/text", data={"text": content})
                    if response.status_code == 200:
                        result = response.json()
                        st.subheader("📜 Before and After")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.code(result["original_text"], language="text")
                        with col2:
                            st.code(result["anonymized_text"], language="text")
                    else:
                        st.error("⚠️ Failed to process text file.")
                else:
                    st.error("Unsupported file type.")

            except Exception as e:
                st.error(f"Error: {e}")

    elif text_input.strip():
        # Raw text anonymization
        with st.spinner("Processing text..."):
            response = requests.post(f"{BACKEND_URL}/anonymize/text", data={"text": text_input})
        if response.status_code == 200:
            result = response.json()
            st.subheader("📜 Before and After")
            col1, col2 = st.columns(2)
            with col1:
                st.code(result["original_text"], language="text")
            with col2:
                st.code(result["anonymized_text"], language="text")
        else:
            st.error("⚠️ Could not process entered text.")
    else:
        st.warning("Please upload a file or enter text to proceed.")
