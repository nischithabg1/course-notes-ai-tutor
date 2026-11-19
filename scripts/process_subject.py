import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.subject_manager import SubjectManager
from scripts.extract_pdf import extract_text
from scripts.chunk_text import process_textbook
from scripts.generate_embeddings import generate_embeddings


def process_subject(subject_slug, pdf_path):

    manager = SubjectManager()
    subject = manager.get_subject(subject_slug)

    if subject is None:
        raise ValueError(f"Subject '{subject_slug}' is not registered.")

    if subject["status"] == "ready":
        raise ValueError(
            "This subject is already ready. Processing it again could "
            "overwrite its existing textbook data."
        )

    if subject["status"] == "processing":
        raise ValueError("This subject is already being processed.")

    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    try:
        manager.update_status(subject_slug, "processing")

        print("\nSTEP 1: Extracting PDF text...")
        extract_text(subject_slug, pdf_path)
        print("PDF extraction completed.")

        print("\nSTEP 2: Creating text chunks...")
        process_textbook(subject_slug)
        print("Text chunking completed.")

        print("\nSTEP 3: Generating embeddings...")
        generate_embeddings(subject_slug)
        print("Embedding generation completed.")

        manager.update_status(subject_slug, "ready")

        print("\n" + "=" * 50)
        print(f"SUCCESS: {subject['name']} is now ready!")
        print("=" * 50)

        return True

    except Exception:
        manager.update_status(subject_slug, "pending")
        print(
            "\nProcessing failed. The subject status has been reset "
            "to pending."
        )
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Process a new subject textbook automatically."
    )

    parser.add_argument(
        "--subject",
        required=True,
        help="Registered subject slug, e.g. operating_systems"
    )

    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to the subject textbook PDF"
    )

    args = parser.parse_args()

    process_subject(args.subject, args.pdf)


if __name__ == "__main__":
    main()