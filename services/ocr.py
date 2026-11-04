import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

LANGS = "eng+hin+mar"   # needs the hin and mar traineddata packs installed
MAX_PDF_PAGES = 15

def _ocr_image(img):
    try:
        return pytesseract.image_to_string(img, lang=LANGS)
    except pytesseract.TesseractError:
        return pytesseract.image_to_string(img, lang="eng")

def extract_text(path):
    """Text layer first for PDFs, OCR for scans and photos."""
    if path.lower().endswith(".pdf"):
        parts = []
        with fitz.open(path) as doc:
            for i, page in enumerate(doc):
                if i >= MAX_PDF_PAGES:
                    break
                text = page.get_text().strip()
                if len(text) < 30:
                    pix = page.get_pixmap(dpi=200)
                    text = _ocr_image(Image.open(io.BytesIO(pix.tobytes("png"))))
                parts.append(text)
        return "\n\n".join(parts).strip()
    return _ocr_image(Image.open(path)).strip()
