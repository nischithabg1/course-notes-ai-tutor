# Course Notes AI Tutor – Multi-Subject RAG Application

An AI-powered educational assistant that helps students understand their course materials by asking questions directly from uploaded textbook PDFs.

The application uses **Retrieval-Augmented Generation (RAG)** to retrieve relevant textbook content and generate contextual answers using Google Gemini.

## 1. Project Overview

Students often spend time searching through lengthy textbooks to find explanations for specific topics. Course Notes AI Tutor simplifies this process by allowing students to upload textbooks, select a subject, and ask questions in natural language.

The system retrieves relevant passages from the selected subject's textbook and uses them as context for generating answers.

## 2. Key Features

- **Multi-Subject Support:** Register and manage multiple academic subjects.
- **PDF Upload:** Upload a textbook PDF for each subject.
- **Text Extraction:** Extract textbook content using PyMuPDF.
- **Text Chunking:** Divide extracted content into smaller overlapping chunks.
- **Semantic Search:** Retrieve relevant textbook passages using vector embeddings.
- **AI-Powered Answers:** Generate student-friendly answers using Google Gemini.
- **Textbook Sources:** Display retrieved source passages separately with page references.
- **Chat History:** Save and revisit previous conversations.
- **Automatic Processing:** Extract, chunk, and generate embeddings automatically after textbook upload.
- **Temporary API Error Handling:** Retry certain temporary Gemini service errors.

## 3. Technologies Used

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| PDF Text Extraction | PyMuPDF |
| Embedding Model | BAAI/bge-small-en-v1.5 |
| Embedding Framework | FastEmbed |
| Vector Operations | NumPy |
| Generative AI | Google Gemini API |
| Database | SQLite |
| Environment Configuration | python-dotenv |
| Testing | pytest |

## 4. System Architecture

The application follows a Retrieval-Augmented Generation architecture.

### Textbook Processing Pipeline

1. Student registers a subject.
2. Student uploads the subject's textbook PDF.
3. PyMuPDF extracts text from the PDF.
4. Extracted text is cleaned and divided into overlapping chunks.
5. FastEmbed generates vector embeddings for each chunk.
6. Embeddings and metadata are stored locally.

### Question Answering Pipeline

1. Student selects a subject and enters a question.
2. The question is converted into an embedding.
3. Semantic similarity search retrieves relevant textbook chunks.
4. Retrieved content is passed to Google Gemini as context.
5. Gemini generates an answer grounded in the retrieved content.
6. The answer and textbook sources are displayed separately.
7. Conversation details are saved in SQLite.

## 5. Project Structure

```text
course-notes-ai-tutor/
│
├── app.py
│
├── app/
│   ├── __init__.py
│   ├── cli.py
│   ├── core.py
│   ├── llm.py
│   ├── storage.py
│   └── subject_manager.py
│
├── scripts/
│   ├── extract_pdf.py
│   ├── extract_dbms.py
│   ├── chunk_text.py
│   ├── generate_embeddings.py
│   ├── retrieve.py
│   ├── ask_tutor.py
│   └── process_subject.py
│
├── tests/
│   ├── test_core.py
│   └── test_smoke.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── subjects.json
│   └── chat_history.db
│
├── .env.example
├── .gitignore
├── requirements.txt
├── pytest.ini
└── README.md
```

Generated textbook data, local databases, virtual environments, and API credentials are stored locally and excluded from Git.

## 6. Installation and Setup

### Prerequisites

- Python 3.11 or later
- Git
- Google Gemini API key

### Step 1: Clone the repository

```bash
git clone https://github.com/nischithabg1/course-notes-ai-tutor.git
cd course-notes-ai-tutor
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Gemini API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Replace the placeholder with your own Gemini API key.

**Important:** Never commit your `.env` file or share your API key publicly.

### Step 5: Run the application

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

## 7. Using the Application

1. Launch the Streamlit application.
2. Open **Manage Subjects**.
3. Register a new academic subject.
4. Select the pending subject.
5. Upload its textbook PDF.
6. Click **Process Textbook**.
7. Wait for extraction, chunking, and embedding generation.
8. Select the processed subject from the subject dropdown.
9. Ask questions related to the textbook.
10. Expand **View textbook sources** to inspect the retrieved passages.

Previously saved conversations can be accessed from the Chat History section.

## 8. Running Tests

Run the automated test suite:

```bash
pytest -v
```

Run Python syntax checks:

```bash
python -m compileall app.py app scripts tests
```

## 9. Important Notes

- The application currently supports PDFs containing selectable text. Scanned image-only PDFs require OCR, which is not included in the current version.
- Gemini responses depend on API availability, quotas, and service limits.
- Answers are grounded in retrieved textbook content. If the retrieved content does not sufficiently support an answer, the assistant is instructed to communicate that limitation.
- Uploaded textbooks, generated embeddings, and chat history are stored locally and are not included in the Git repository.
- A reconstructed Waterfall Model diagram is provided for the relevant Software Engineering question; it is not the original textbook illustration.

## 10. Future Enhancements

- Automatic chapter-wise summaries.
- AI-generated multiple-choice questions.
- Exam-oriented answer generation.
- OCR support for scanned textbooks.
- User authentication and personalized learning progress.

## 11. Conclusion

Course Notes AI Tutor demonstrates how Retrieval-Augmented Generation can be applied to educational materials. By combining semantic search with generative AI, the application enables students to interact with their textbooks through natural-language questions and receive relevant, context-aware explanations.

**Developed as an academic project using Python, Streamlit, FastEmbed, and Google Gemini.**