import os
import uuid

from fastapi import UploadFile
from pypdf import PdfReader

from core.config import settings


class ResumeValidationError(Exception):
    pass


def validate_resume_file(file: UploadFile) -> None:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise ResumeValidationError(f"Unsupported file type: {ext}")


async def save_uploaded_file(file: UploadFile) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    contents = await file.read()

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise ResumeValidationError(
            f"File too large: {size_mb:.2f}MB (max {settings.MAX_UPLOAD_SIZE_MB}MB)"
        )

    with open(file_path, "wb") as f:
        f.write(contents)

    return file_path


def extract_text_from_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise ResumeValidationError(f"Failed to extract text from PDF: {e}")