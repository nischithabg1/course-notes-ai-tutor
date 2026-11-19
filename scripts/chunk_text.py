
import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))

from app.subject_manager import SubjectManager

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150

# Preserve existing chunk ID prefixes
LEGACY_PREFIXES = {
    "software_engineering": "SE",
    "dbms": "DBMS"
}


# --------------------------------------------------
# TEXT CLEANING
# --------------------------------------------------

def clean_text(text):
    """Remove unnecessary whitespace and normalize text."""

    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# --------------------------------------------------
# TEXT CHUNKING
# --------------------------------------------------

def split_into_chunks(text):
    """Split text into overlapping chunks."""

    chunks = []
    start = 0

    while start < len(text):

        end = min(start + CHUNK_SIZE, len(text))

        if end < len(text):

            search_start = start + int(CHUNK_SIZE * 0.5)

            boundaries = [
                text.rfind(". ", search_start, end),
                text.rfind("? ", search_start, end),
                text.rfind("! ", search_start, end)
            ]

            boundary = max(boundaries)

            if boundary != -1:

                end = boundary + 1

            else:

                space = text.rfind(
                    " ",
                    search_start,
                    end
                )

                if space != -1:
                    end = space

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = max(
            start + 1,
            end - CHUNK_OVERLAP
        )

        while next_start < end and text[next_start].isspace():
            next_start += 1

        start = next_start

    return chunks


# --------------------------------------------------
# SUBJECT CHUNK PROCESSING
# --------------------------------------------------

def process_textbook(subject_slug):

    manager = SubjectManager()

    subject = manager.get_subject(subject_slug)

    if subject is None:
        raise ValueError(
            f"Subject '{subject_slug}' is not registered."
        )

    subject_name = subject["name"]

    # Preserve old chunk IDs for existing subjects
    prefix = LEGACY_PREFIXES.get(
        subject_slug,
        subject_slug.upper()
    )

    subject_dir = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / subject_slug
    )

    input_file = subject_dir / "pages.jsonl"
    output_file = subject_dir / "chunks.jsonl"

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}"
        )

    print(f"Processing subject: {subject_name}")
    print("Reading extracted textbook data...")

    total_chunks = 0
    total_characters = 0
    total_pages = 0

    subject_dir.mkdir(parents=True, exist_ok=True)

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as source:

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as output:

            for line in source:

                if not line.strip():
                    continue

                record = json.loads(line)

                total_pages += 1

                page_number = record["page"]

                text = clean_text(record["text"])

                page_chunks = split_into_chunks(text)

                for index, chunk in enumerate(
                    page_chunks,
                    start=1
                ):

                    chunk_record = {
                        "chunk_id": (
                            f"{prefix}-P{page_number}-C{index}"
                        ),
                        "subject": subject_name,
                        "subject_id": subject_slug,
                        "source": record.get(
                            "source",
                            "Unknown textbook"
                        ),
                        "page": page_number,
                        "text": chunk,
                        "character_count": len(chunk)
                    }

                    output.write(
                        json.dumps(
                            chunk_record,
                            ensure_ascii=False
                        ) + "\n"
                    )

                    total_chunks += 1
                    total_characters += len(chunk)

                if page_number % 100 == 0:
                    print(
                        f"Processed PDF page {page_number}"
                    )

    if total_chunks == 0:
        output_file.unlink(missing_ok=True)

        raise ValueError(
            "No text chunks were generated. "
            "Check the extracted pages file."
        )

    print("\nChunking completed!")
    print(f"Subject: {subject_name}")
    print(f"Pages with extracted text: {total_pages}")
    print(f"Total chunks generated: {total_chunks}")
    print(f"Total characters: {total_characters}")
    print(f"Output saved to: {output_file}")

    return {
        "subject": subject_name,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "total_characters": total_characters,
        "output_file": str(output_file)
    }


# --------------------------------------------------
# COMMAND LINE INTERFACE
# --------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Chunk textbook content dynamically by subject."
    )

    parser.add_argument(
        "--subject",
        required=True,
        help="Registered subject ID, e.g. operating_systems"
    )

    args = parser.parse_args()

    process_textbook(args.subject)
