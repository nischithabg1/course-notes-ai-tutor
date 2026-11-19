
import argparse
import json
import sys
from pathlib import Path

import pymupdf as fitz

# --------------------------------------------------
# PROJECT PATH CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Add project root to Python import path
sys.path.insert(0, str(PROJECT_ROOT))

from app.subject_manager import SubjectManager


# --------------------------------------------------
# PDF EXTRACTION
# --------------------------------------------------

def extract_text(subject_slug, pdf_path):

    manager = SubjectManager()
    subject = manager.get_subject(subject_slug)

    if subject is None:
        raise ValueError(
            f"Subject '{subject_slug}' is not registered."
        )

    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    output_dir = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / subject_slug
    )

    output_file = output_dir / "pages.jsonl"

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Subject: {subject['name']}")
    print(f"PDF: {pdf_path.name}")
    print("Opening textbook...")

    pdf = fitz.open(pdf_path)

    total_pages = len(pdf)
    extracted_pages = 0
    empty_pages = 0

    print(f"Total PDF pages: {total_pages}")

    try:

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as output:

            for page_index, page in enumerate(pdf):

                page_number = page_index + 1

                text = page.get_text(
                    "text",
                    sort=True
                ).strip()

                if not text:
                    empty_pages += 1
                    continue

                record = {
                    "subject": subject["name"],
                    "subject_id": subject_slug,
                    "source": pdf_path.name,
                    "page": page_number,
                    "text": text
                }

                output.write(
                    json.dumps(
                        record,
                        ensure_ascii=False
                    ) + "\n"
                )

                extracted_pages += 1

                if page_number % 50 == 0:
                    print(
                        f"Processed {page_number}/{total_pages} pages"
                    )

    finally:
        pdf.close()

    if extracted_pages == 0:
        output_file.unlink(missing_ok=True)

        raise ValueError(
            "No extractable text was found in the PDF. "
            "The document may be scanned and require OCR."
        )

    print("\nExtraction completed!")
    print(f"Subject: {subject['name']}")
    print(f"Total pages: {total_pages}")
    print(f"Pages with extracted text: {extracted_pages}")
    print(f"Empty pages: {empty_pages}")
    print(f"Output saved to: {output_file}")

    return {
        "total_pages": total_pages,
        "extracted_pages": extracted_pages,
        "empty_pages": empty_pages,
        "output_file": str(output_file)
    }


# --------------------------------------------------
# COMMAND LINE INTERFACE
# --------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Extract text from a subject textbook PDF."
    )

    parser.add_argument(
        "--subject",
        required=True,
        help="Registered subject ID, e.g. operating_systems"
    )

    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to the textbook PDF"
    )

    args = parser.parse_args()

    extract_text(
        subject_slug=args.subject,
        pdf_path=args.pdf
    )
