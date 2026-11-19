
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from retrieve import SemanticRetriever


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.5-flash-lite"

MAX_RETRIES = 3
RETRY_DELAYS = [2, 4]


# --------------------------------------------------
# ERROR HANDLING
# --------------------------------------------------

def is_temporary_error(error):

    error_code = getattr(error, "code", None)
    error_status = str(getattr(error, "status", "")).upper()
    error_message = str(error).upper()

    temporary_codes = {429, 500, 502, 503, 504}

    if error_code in temporary_codes:
        return True

    temporary_keywords = [
        "UNAVAILABLE",
        "RESOURCE_EXHAUSTED",
        "TOO MANY REQUESTS",
        "INTERNAL SERVER ERROR",
        "SERVICE UNAVAILABLE",
        "DEADLINE EXCEEDED",
        "HIGH DEMAND"
    ]

    return (
        error_status in {
            "UNAVAILABLE",
            "RESOURCE_EXHAUSTED",
            "INTERNAL",
            "DEADLINE_EXCEEDED"
        }
        or any(keyword in error_message for keyword in temporary_keywords)
    )


# --------------------------------------------------
# GENERATE AI ANSWER
# --------------------------------------------------

def generate_answer(question, retrieved_passages, client):

    # Prepare clean textbook context without retrieval labels
    context = "\n\n".join(
        passage["text"]
        for passage in retrieved_passages
    )

    prompt = f"""
You are Course Notes AI Tutor, an educational assistant.

Answer the student's question using ONLY the textbook content
provided below.

INSTRUCTIONS:

1. Explain concepts clearly in simple, student-friendly language.
2. Organize answers using appropriate headings and bullet points.
3. Provide detailed explanations when the question requires them.
4. Do not include internal retrieval references such as:
   - Passage 1, Passage 2, etc.
   - Page numbers within the explanation.
   - Chunk IDs or retrieval labels.
   - Statements such as "According to Passage 1".
5. Do not mention the source or textbook repeatedly in the answer.
6. Do not invent facts that are not supported by the provided content.
7. If the provided content is insufficient, clearly explain
   what information is missing.
8. Maintain the original technical meaning of the concepts.
9. Make the answer natural, well-structured, and suitable
   for engineering students.

The textbook sources and page references are displayed separately
in the application. Do not reproduce them in your answer.

TEXTBOOK CONTENT:
{context}

STUDENT QUESTION:
{question}

ANSWER:
"""

    # Retry temporary Gemini service errors
    for attempt in range(MAX_RETRIES):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            return (
                response.text
                or "Gemini did not return a text response."
            )

        except Exception as error:

            if not is_temporary_error(error):
                raise

            if attempt < MAX_RETRIES - 1:

                delay = RETRY_DELAYS[attempt]

                print(
                    f"Gemini is temporarily unavailable. "
                    f"Retrying in {delay} seconds "
                    f"({attempt + 2}/{MAX_RETRIES})..."
                )

                time.sleep(delay)

            else:

                raise RuntimeError(
                    "Gemini is temporarily experiencing high demand. "
                    "Please try again in a few minutes."
                ) from error


# --------------------------------------------------
# COMMAND-LINE EXECUTION
# --------------------------------------------------

def main():

    if not API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing. Check your project-root .env file."
        )

    print("Initializing Gemini...")
    client = genai.Client(api_key=API_KEY)

    print("Initializing textbook retriever...")
    retriever = SemanticRetriever()

    question = input(
        "\nAsk your Course Notes AI Tutor: "
    ).strip()

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

    answer = generate_answer(
        question,
        passages,
        client
    )

    print("=" * 65)
    print("COURSE NOTES AI TUTOR")
    print("=" * 65)
    print(answer)
    print("=" * 65)


if __name__ == "__main__":
    main()
