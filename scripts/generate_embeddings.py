
import json
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "software_engineering"
    / "chunks.jsonl"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "software_engineering"
)

EMBEDDINGS_FILE = OUTPUT_DIR / "embeddings.npy"
METADATA_FILE = OUTPUT_DIR / "embedding_metadata.jsonl"

# Lightweight embedding model
MODEL_NAME = "BAAI/bge-small-en-v1.5"


def main():
    print("Loading text chunks...")

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        chunks = [json.loads(line) for line in file if line.strip()]

    if not chunks:
        raise ValueError("No chunks found in the input file.")

    texts = [chunk["text"] for chunk in chunks]

    print(f"Total chunks: {len(chunks)}")
    print(f"Loading embedding model: {MODEL_NAME}")

    model = TextEmbedding(model_name=MODEL_NAME)

    print("Generating embeddings...")

    embeddings = np.array(
        list(model.embed(texts, batch_size=4)),
        dtype=np.float32
    )

    if len(embeddings) != len(chunks):
        raise ValueError("Embedding count does not match chunk count.")

    # Save numerical vectors
    np.save(EMBEDDINGS_FILE, embeddings)

    # Save metadata in the same order as the vectors
    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        for chunk in chunks:
            metadata = {
                "chunk_id": chunk["chunk_id"],
                "subject": chunk["subject"],
                "source": chunk["source"],
                "page": chunk["page"]
            }
            file.write(json.dumps(metadata) + "\n")

    print("\nEmbedding generation completed!")
    print(f"Total embeddings: {len(embeddings)}")
    print(f"Embedding dimensions: {embeddings.shape[1]}")
    print(f"Embeddings saved: {EMBEDDINGS_FILE}")
    print(f"Metadata saved: {METADATA_FILE}")


if __name__ == "__main__":
    main()
