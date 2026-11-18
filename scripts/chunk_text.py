
import json
import re
from pathlib import Path

# Project directory
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Input and output files
INPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "software_engineering"
    / "pages.jsonl"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "software_engineering"
    / "chunks.jsonl"
)

# Chunk configuration
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def clean_text(text):
    """Remove unnecessary whitespace and normalize text."""

    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_into_chunks(text):
    """Split text into overlapping chunks."""

    chunks = []
    start = 0

    while start < len(text):

        end = min(start + CHUNK_SIZE, len(text))

        # Try to end at a sentence boundary
        if end < len(text):
            search_start = start + int(CHUNK_SIZE * 0.5)

            boundaries = [
                text.rfind(". ", search_start, end),
                text.rfind("? ", search_start, end),
                text.rfind("! ", search_start, end),
            ]

            boundary = max(boundaries)

            if boundary != -1:
                end = boundary + 1
            else:
                # Fall back to a word boundary
                space = text.rfind(" ", search_start, end)

                if space != -1:
                    end = space

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # Move forward while retaining overlap
        next_start = max(start + 1, end - CHUNK_OVERLAP)

        while next_start < end and text[next_start].isspace():
            next_start += 1

        start = next_start

    return chunks


def process_textbook():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    print("Reading extracted textbook data...")

    records = []

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            records.append(json.loads(line))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    total_characters = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:

        for record in records:

            page_number = record["page"]

            text = clean_text(record["text"])

            page_chunks = split_into_chunks(text)

            for index, chunk in enumerate(page_chunks, start=1):

                chunk_record = {
                    "chunk_id": f"SE-P{page_number}-C{index}",
                    "subject": record["subject"],
                    "source": record["source"],
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
                    f"Processed {page_number}/{len(records)} pages"
                )

    print("\nChunking completed!")
    print(f"Pages processed: {len(records)}")
    print(f"Total chunks generated: {total_chunks}")
    print(f"Total characters: {total_characters}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    process_textbook()
