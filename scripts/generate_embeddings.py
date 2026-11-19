
import os
import sys
import json
import argparse
from pathlib import Path

# --------------------------------------------------
# MEMORY CONFIGURATION
# --------------------------------------------------

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from fastembed import TextEmbedding

from app.subject_manager import SubjectManager


MODEL_NAME = "BAAI/bge-small-en-v1.5"
BATCH_SIZE = 4
EXPECTED_DIMENSIONS = 384


# --------------------------------------------------
# GENERATE EMBEDDINGS
# --------------------------------------------------

def generate_embeddings(subject_slug):

    manager = SubjectManager()

    subject = manager.get_subject(subject_slug)

    if subject is None:
        raise ValueError(
            f"Subject '{subject_slug}' is not registered."
        )

    subject_name = subject["name"]

    subject_dir = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / subject_slug
    )

    input_file = subject_dir / "chunks.jsonl"
    embeddings_file = subject_dir / "embeddings.npy"
    metadata_file = subject_dir / "embedding_metadata.jsonl"

    if not input_file.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {input_file}"
        )

    print(f"Generating embeddings for: {subject_name}")
    print("Loading text chunks...")

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:

        chunks = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

    if not chunks:
        raise ValueError(
            "No chunks found in the input file."
        )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print(f"Total chunks: {len(chunks)}")
    print(f"Loading embedding model: {MODEL_NAME}")

    model = TextEmbedding(
        model_name=MODEL_NAME
    )

    print(
        f"Generating embeddings with batch size {BATCH_SIZE}..."
    )

    embeddings = np.array(
        list(
            model.embed(
                texts,
                batch_size=BATCH_SIZE
            )
        ),
        dtype=np.float32
    )

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    if len(embeddings) != len(chunks):
        raise ValueError(
            "Embedding count does not match chunk count."
        )

    if embeddings.ndim != 2:
        raise ValueError(
            "Embeddings must be a 2D array."
        )

    if embeddings.shape[1] != EXPECTED_DIMENSIONS:
        raise ValueError(
            f"Expected {EXPECTED_DIMENSIONS} dimensions, "
            f"received {embeddings.shape[1]}."
        )

    if not np.isfinite(embeddings).all():
        raise ValueError(
            "Embeddings contain invalid numerical values."
        )

    # --------------------------------------------------
    # SAVE EMBEDDINGS
    # --------------------------------------------------

    subject_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    np.save(
        embeddings_file,
        embeddings
    )

    # --------------------------------------------------
    # SAVE METADATA
    # --------------------------------------------------

    with open(
        metadata_file,
        "w",
        encoding="utf-8"
    ) as file:

        for chunk in chunks:

            metadata = {
                "chunk_id": chunk["chunk_id"],
                "subject": chunk["subject"],
                "subject_id": subject_slug,
                "source": chunk["source"],
                "page": chunk["page"]
            }

            file.write(
                json.dumps(
                    metadata,
                    ensure_ascii=False
                ) + "\n"
            )

    # --------------------------------------------------
    # COMPLETION REPORT
    # --------------------------------------------------

    print("\nEmbedding generation completed!")

    print(f"Subject: {subject_name}")
    print(f"Total embeddings: {len(embeddings)}")
    print(f"Embedding dimensions: {embeddings.shape[1]}")
    print(f"Embeddings saved: {embeddings_file}")
    print(f"Metadata saved: {metadata_file}")

    return {
        "subject": subject_name,
        "total_embeddings": len(embeddings),
        "dimensions": embeddings.shape[1],
        "embeddings_file": str(embeddings_file),
        "metadata_file": str(metadata_file)
    }


# --------------------------------------------------
# COMMAND LINE INTERFACE
# --------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate textbook embeddings dynamically."
    )

    parser.add_argument(
        "--subject",
        required=True,
        help="Registered subject ID, e.g. operating_systems"
    )

    args = parser.parse_args()

    generate_embeddings(args.subject)
