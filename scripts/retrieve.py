
import json
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "software_engineering"
)

EMBEDDINGS_FILE = DATA_DIR / "embeddings.npy"
METADATA_FILE = DATA_DIR / "embedding_metadata.jsonl"

MODEL_NAME = "BAAI/bge-small-en-v1.5"


class SemanticRetriever:
    def __init__(self):
        print("Loading stored embeddings...")

        self.embeddings = np.load(EMBEDDINGS_FILE)

        with open(METADATA_FILE, "r", encoding="utf-8") as file:
            self.metadata = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        if len(self.embeddings) != len(self.metadata):
            raise ValueError("Embedding and metadata counts do not match.")

        print("Loading embedding model...")
        self.model = TextEmbedding(model_name=MODEL_NAME)

        print(f"Loaded {len(self.metadata)} textbook chunks.")

    def search(self, question, subject="Software Engineering", top_k=5):
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        # Convert the student's question into a vector
        query_vector = np.array(
            list(self.model.embed([question])),
            dtype=np.float32
        )[0]

        # Filter chunks by the selected subject
        subject_indices = [
            i for i, item in enumerate(self.metadata)
            if item["subject"].casefold() == subject.casefold()
        ]

        if not subject_indices:
            return []

        subject_embeddings = self.embeddings[subject_indices]

        # Calculate cosine similarity
        query_norm = np.linalg.norm(query_vector)
        embedding_norms = np.linalg.norm(
            subject_embeddings, axis=1
        )

        similarities = (
            subject_embeddings @ query_vector
        ) / (embedding_norms * query_norm + 1e-10)

        # Select the most relevant chunks
        top_positions = np.argsort(similarities)[::-1][:top_k]

        results = []

        for position in top_positions:
            original_index = subject_indices[position]

            results.append({
                **self.metadata[original_index],
                "similarity": float(similarities[position]),
                "text": self._get_chunk_text(
                    self.metadata[original_index]["chunk_id"]
                )
            })

        return results

    def _get_chunk_text(self, chunk_id):
        chunks_file = DATA_DIR / "chunks.jsonl"

        with open(chunks_file, "r", encoding="utf-8") as file:
            for line in file:
                chunk = json.loads(line)

                if chunk["chunk_id"] == chunk_id:
                    return chunk["text"]

        return ""


if __name__ == "__main__":
    retriever = SemanticRetriever()

    question = input("\nEnter your question: ")

    results = retriever.search(
        question,
        subject="Software Engineering",
        top_k=5
    )

    print("\nMost relevant textbook passages:\n")

    for rank, result in enumerate(results, start=1):
        print(f"\n--- Result {rank} ---")
        print(f"Page: {result['page']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Text:\n{result['text']}")
