
import pymupdf
from pathlib import Path

pdf_path = Path(
    r"C:\Users\user\Downloads\MP\Placements\CBIT-Placement-Policy.pdf"
)

with pymupdf.open(pdf_path) as pdf:
    print("Total pages:", len(pdf))

    for i, page in enumerate(pdf, start=1):
        text = page.get_text("text").strip()

        print(f"\nPage {i}: {len(text)} characters")

        if text:
            print(text[:300])
        else:
            print("No selectable text found on this page.")


