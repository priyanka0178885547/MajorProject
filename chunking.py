
import os
import json
import fitz
import pytesseract

from PIL import Image
from docx import Document
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "chunks.json")

FOLDERS = [
    "Academics",
    "Admissions",
    "departments",
    "Placements",
    "Scholarship",
    "transport"
]

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Update this path if Tesseract is installed elsewhere.
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_pdf(file_path):
    extracted_pages = []

    with fitz.open(file_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            method = "text"

            # Use OCR if the page has no selectable text.
            if not text:
                try:
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(2, 2),
                        alpha=False
                    )
                    image = Image.open(
                        BytesIO(pix.tobytes("png"))
                    )
                    text = pytesseract.image_to_string(
                        image,
                        lang="eng"
                    ).strip()
                    method = "ocr"
                except Exception as error:
                    print(
                        f"OCR failed: {file_path}, "
                        f"page {page_number}: {error}"
                    )
                    text = ""

            if text:
                extracted_pages.append({
                    "page": page_number,
                    "text": text,
                    "method": method
                })
            else:
                print(
                    f"No text extracted: {file_path}, "
                    f"page {page_number}"
                )

    return extracted_pages


def extract_docx(file_path):
    document = Document(file_path)
    text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )
    return text


def split_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def process_file(file_path, folder_name):
    records = []
    relative_path = os.path.relpath(file_path, BASE_DIR)

    try:
        if file_path.lower().endswith(".pdf"):
            pages = extract_pdf(file_path)

            for page in pages:
                for chunk_id, chunk in enumerate(
                    split_text(page["text"])
                ):
                    records.append({
                        "department": folder_name,
                        "source": relative_path,
                        "page": page["page"],
                        "extraction_method": page["method"],
                        "chunk_id": chunk_id,
                        "text": chunk
                    })

        elif file_path.lower().endswith(".docx"):
            text = extract_docx(file_path)

            for chunk_id, chunk in enumerate(split_text(text)):
                records.append({
                    "department": folder_name,
                    "source": relative_path,
                    "page": None,
                    "extraction_method": "docx",
                    "chunk_id": chunk_id,
                    "text": chunk
                })

    except Exception as error:
        print(f"Failed to process {relative_path}: {error}")

    return records


def main():
    all_chunks = []

    for folder_name in FOLDERS:
        folder_path = os.path.join(BASE_DIR, folder_name)

        if not os.path.isdir(folder_path):
            print(f"Folder not found: {folder_name}")
            continue

        print(f"\nProcessing folder: {folder_name}")

        for root, _, files in os.walk(folder_path):
            for filename in files:
                if filename.lower().endswith((".pdf", ".docx")):
                    file_path = os.path.join(root, filename)
                    records = process_file(file_path, folder_name)
                    all_chunks.extend(records)

                    print(
                        f"Processed: {os.path.relpath(file_path, BASE_DIR)}"
                        f" | Chunks: {len(records)}"
                    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
        json.dump(all_chunks, output, ensure_ascii=False, indent=2)

    print("\n========== COMPLETE ==========")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

