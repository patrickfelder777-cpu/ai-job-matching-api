
import fitz


MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract readable text from a PDF resume.

    Args:
        pdf_bytes: Raw PDF file contents.

    Returns:
        Extracted text as a string.

    Raises:
        ValueError: If the PDF is empty, too large,
                    invalid, or contains no extractable text.
    """
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise ValueError("PDF file exceeds the 10 MB limit.")

    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a valid PDF.")

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            pages = []

            for page in document:
                text = page.get_text("text")

                if text.strip():
                    pages.append(text.strip())

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "Unable to read the uploaded PDF."
        ) from exc

    extracted_text = "\n\n".join(pages).strip()

    if not extracted_text:
        raise ValueError(
            "No readable text found in the PDF. "
            "Scanned documents may require OCR."
        )

    return extracted_text
