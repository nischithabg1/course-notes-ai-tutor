
import json
import sys
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))

from app.subject_manager import SubjectManager

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EXPECTED_DIMENSIONS = 384


# --------------------------------------------------
# SEMANTIC RETRIEVER
# --------------------------------------------------

class SemanticRetriever:

    def __init__(self):

        print("Loading embedding model...")

        self.model = TextEmbedding(
            model_name=MODEL_NAME
        )

        self.subject_manager = SubjectManager()

        # Cache data separately for each subject
        self.subject_data = {}

        print("Semantic retriever initialized.")

    # --------------------------------------------------
    # RESOLVE SUBJECT
    # --------------------------------------------------

    def _resolve_subject(self, subject):

        if not subject or not str(subject).strip():
            raise ValueError("Subject cannot be empty.")

        subjects = self.subject_manager.get_subjects()

        subject_key = str(subject).strip().casefold()

        for item in subjects:

            if (
                item["slug"].casefold() == subject_key
                or item["name"].casefold() == subject_key
            ):

                return item

        available = ", ".join(
            item["name"] for item in subjects
        )

        raise ValueError(
            f"Unsupported subject: {subject}. "
            f"Registered subjects: {available}"
        )

    # --------------------------------------------------
    # LOAD SUBJECT DATA
    # --------------------------------------------------

    def _load_subject_data(self, subject):

        subject_info = self._resolve_subject(subject)

        folder_name = subject_info["slug"]

        # Only processed subjects can be searched
        if subject_info["status"] != "ready":

            raise ValueError(
                f"{subject_info['name']} is not ready yet. "
                "Upload and process its textbook first."
            )

        # Return cached data if already loaded
        if folder_name in self.subject_data:

            return self.subject_data[folder_name]

        data_dir = (
            PROJECT_ROOT
            / "data"
            / "processed"
            / folder_name
        )

        embeddings_file = data_dir / "embeddings.npy"
        metadata_file = data_dir / "embedding_metadata.jsonl"
        chunks_file = data_dir / "chunks.jsonl"

        required_files = [
            embeddings_file,
            metadata_file,
            chunks_file
        ]

        for file_path in required_files:

            if not file_path.exists():

                raise FileNotFoundError(
                    f"Required processed file not found: {file_path}"
                )

        print(
            f"Loading data for: {subject_info['name']}"
        )

        # Load numerical embeddings
        embeddings = np.load(
            embeddings_file,
            allow_pickle=False
        )

        # Load metadata
        with open(
            metadata_file,
            "r",
            encoding="utf-8"
        ) as file:

            metadata = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        # Load chunk text
        with open(
            chunks_file,
            "r",
            encoding="utf-8"
        ) as file:

            chunks = {
                chunk["chunk_id"]: chunk["text"]
                for line in file
                if line.strip()
                for chunk in [json.loads(line)]
            }

        # --------------------------------------------------
        # DATA VALIDATION
        # --------------------------------------------------

        if embeddings.ndim != 2:

            raise ValueError(
                "Embeddings must be a 2D array."
            )

        if embeddings.shape[1] != EXPECTED_DIMENSIONS:

            raise ValueError(
                f"Expected {EXPECTED_DIMENSIONS} dimensions, "
                f"received {embeddings.shape[1]}."
            )

        if len(embeddings) == 0:

            raise ValueError(
                "No embeddings found for this subject."
            )

        if not np.isfinite(embeddings).all():

            raise ValueError(
                "Embeddings contain invalid numerical values."
            )

        if len(embeddings) != len(metadata):

            raise ValueError(
                "Embedding and metadata counts do not match."
            )

        if len(chunks) != len(metadata):

            raise ValueError(
                "Chunk and metadata counts do not match."
            )

        # Ensure metadata and chunk IDs correspond
        for item in metadata:

            if item["chunk_id"] not in chunks:

                raise ValueError(
                    f"Missing chunk text: {item['chunk_id']}"
                )

        # Verify metadata belongs to selected subject
        for item in metadata:

            metadata_subject = item.get(
                "subject_id",
                folder_name
            )

            if metadata_subject != folder_name:

                raise ValueError(
                    "Metadata contains a different subject ID."
                )

        # Cache the loaded subject data
        self.subject_data[folder_name] = {
            "embeddings": embeddings,
            "metadata": metadata,
            "chunks": chunks
        }

        print(
            f"Loaded {len(metadata)} chunks "
            f"for {subject_info['name']}."
        )

        return self.subject_data[folder_name]

    # --------------------------------------------------
    # SEMANTIC SEARCH
    # --------------------------------------------------

    def search(
        self,
        question,
        subject="Software Engineering",
        top_k=5
    ):

        if not question or not question.strip():

            raise ValueError(
                "Question cannot be empty."
            )

        if top_k < 1:

            raise ValueError(
                "top_k must be at least 1."
            )

        # Resolve and load selected subject
        subject_info = self._resolve_subject(subject)

        data = self._load_subject_data(
            subject_info["slug"]
        )

        embeddings = data["embeddings"]
        metadata = data["metadata"]
        chunks = data["chunks"]

        # Convert question into an embedding
        query_vector = np.array(
            list(
                self.model.embed([question])
            ),
            dtype=np.float32
        )[0]

        query_norm = np.linalg.norm(query_vector)

        if query_norm == 0:

            raise ValueError(
                "Question embedding has zero magnitude."
            )

        # Calculate cosine similarity
        embedding_norms = np.linalg.norm(
            embeddings,
            axis=1
        )

        similarities = (
            embeddings @ query_vector
        ) / (
            embedding_norms * query_norm + 1e-10
        )

        # Select top matching chunks
        result_count = min(
            top_k,
            len(similarities)
        )

        top_positions = np.argsort(
            similarities
        )[::-1][:result_count]

        results = []

        for position in top_positions:

            item = metadata[position]

            results.append({
                **item,
                "similarity": float(
                    similarities[position]
                ),
                "text": chunks[item["chunk_id"]]
            })

        return results


# --------------------------------------------------
# COMMAND LINE INTERFACE
# --------------------------------------------------

if __name__ == "__main__":

    manager = SubjectManager()

    retriever = SemanticRetriever()

    subjects = [
        item
        for item in manager.get_subjects()
        if item["status"] == "ready"
    ]

    print("\nAvailable processed subjects:")

    for index, item in enumerate(subjects, start=1):

        print(f"{index}. {item['name']}")

    if not subjects:

        raise ValueError(
            "No processed subjects are available."
        )

    choice = input(
        "\nSelect subject number: "
    ).strip()

    if not choice.isdigit():

        raise ValueError(
            "Please enter a valid subject number."
        )

    choice_number = int(choice)

    if not 1 <= choice_number <= len(subjects):

        raise ValueError(
            "Invalid subject selection."
        )

    selected_subject = subjects[
        choice_number - 1
    ]

    question = input(
        "\nEnter your question: "
    )

    results = retriever.search(
        question,
        subject=selected_subject["slug"],
        top_k=5
    )

    print(
        f"\nMost relevant {selected_subject['name']} passages:\n"
    )

    for rank, result in enumerate(results, start=1):

        print(f"\n--- Result {rank} ---")
        print(f"Subject: {result['subject']}")
        print(f"Page: {result['page']}")
        print(
            f"Similarity: {result['similarity']:.4f}"
        )
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Text:\n{result['text']}")
