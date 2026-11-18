
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from retrieve import SemanticRetriever


# Load environment variables from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.5-flash-lite"


def generate_answer(question, retrieved_passages, client):
    # Prepare textbook context
    context = ""

    for index, passage in enumerate(retrieved_passages, start=1):
        context += (
            f"\nPassage {index}\n"
            f"Subject: {passage['subject']}\n"
            f"Source: {passage['source']}\n"
            f"Page: {passage['page']}\n"
            f"Content: {passage['text']}\n"
        )

    prompt = f"""
You are Course Notes AI Tutor, an educational assistant.

Answer the student's question using ONLY the textbook passages
provided below.

Instructions:
1. Explain the answer clearly in student-friendly language.
2. Organize the answer using headings or bullet points when useful.
3. Do not invent facts that are not supported by the passages.
4. Mention the textbook page number when using information.
5. If the passages do not contain enough information, clearly
   say that the provided textbook material is insufficient.
6. Do not pretend that you have information from other sources.

TEXTBOOK PASSAGES:
{context}

STUDENT QUESTION:
{question}

ANSWER:
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text or "Gemini did not return a text response."


def main():
    if not API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing. Check your project-root .env file."
        )

    print("Initializing Gemini...")
    client = genai.Client(api_key=API_KEY)

    print("Initializing textbook retriever...")
    retriever = SemanticRetriever()

    question = input("\nAsk your Course Notes AI Tutor: ").strip()

    if not question:
        print("Please enter a question.")
        return

    print("\nSearching textbook passages...")

    passages = retriever.search(
        question,
        subject="Software Engineering",
        top_k=5
    )

    if not passages:
        print("No relevant textbook passages found.")
        return

    print("Generating AI answer...\n")

    answer = generate_answer(question, passages, client)

    print("=" * 65)
    print("COURSE NOTES AI TUTOR")
    print("=" * 65)
    print(answer)
    print("=" * 65)


if __name__ == "__main__":
    main()
