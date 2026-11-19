
import pymupdf as fitz
import json
from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "dbms"
    / "Fundamentals_of_Database_Systems (7th edition)DBMS TB.pdf"
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "dbms"
)

OUTPUT_FILE = OUTPUT_DIR / "pages.jsonl"


def extract_text():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    print("Opening DBMS textbook...")

    pdf = fitz.open(PDF_PATH)

    total_pages = len(pdf)
    extracted_pages = 0
    empty_pages = 0

    print(f"Total PDF pages: {total_pages}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:

        for page_index, page in enumerate(pdf):

            page_number = page_index + 1

            text = page.get_text("text", sort=True).strip()

            if not text:
                empty_pages += 1
                continue

            record = {
                "subject": "DBMS",
                "source": "Fundamentals of Database Systems, 7th Edition",
                "page": page_number,
                "text": text
            }

            output.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

            extracted_pages += 1

            if page_number % 50 == 0:
                print(f"Processed {page_number}/{total_pages} pages")

    pdf.close()

    print("\nDBMS extraction completed!")
    print(f"Total pages: {total_pages}")
    print(f"Pages with extracted text: {extracted_pages}")
    print(f"Empty pages: {empty_pages}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    extract_text()
