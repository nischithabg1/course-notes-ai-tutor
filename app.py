
import os
import sys
from pathlib import Path

# Limit numerical library threads to avoid memory issues on Windows
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import streamlit as st
from dotenv import load_dotenv
from google import genai

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.retrieve import SemanticRetriever
from scripts.ask_tutor import generate_answer
from scripts.process_subject import process_subject

from app.storage import ChatStorage
from app.subject_manager import SubjectManager

load_dotenv(PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_API_KEY")

# --------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Course Notes AI Tutor",
    page_icon="📚",
    layout="wide"
)

# --------------------------------------------------
# INITIALIZE RESOURCES
# --------------------------------------------------

@st.cache_resource
def load_retriever():
    return SemanticRetriever()


@st.cache_resource
def load_gemini():
    if not API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing in your .env file."
        )

    return genai.Client(api_key=API_KEY)


@st.cache_resource
def load_storage():
    return ChatStorage()


@st.cache_resource
def load_subject_manager():
    return SubjectManager()


storage = load_storage()
subject_manager = load_subject_manager()

# --------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------

if "subject_selector" not in st.session_state:
    st.session_state.subject_selector = "Software Engineering"

if "active_subject" not in st.session_state:
    st.session_state.active_subject = st.session_state.subject_selector

if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "subject_notice" not in st.session_state:
    st.session_state.subject_notice = None

# Apply a newly processed subject selection before
# creating the subject selectbox widget.
if "subject_to_select" in st.session_state:
    st.session_state.subject_selector = (
        st.session_state.subject_to_select
    )
    del st.session_state.subject_to_select

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def create_waterfall_diagram():

    waterfall_diagram = """
    digraph Waterfall {
        graph [
            rankdir=TB,
            bgcolor="transparent",
            nodesep=0.35,
            ranksep=0.4
        ];

        node [
            shape=box,
            style="rounded,filled",
            fillcolor="#DBEAFE",
            color="#2563EB",
            fontname="Arial",
            fontsize=12,
            margin="0.25,0.15"
        ];

        edge [
            color="#64748B",
            penwidth=1.5,
            arrowsize=0.8
        ];

        A [label="1. Requirements Definition"];
        B [label="2. System and Software Design"];
        C [label="3. Implementation and Unit Testing"];
        D [label="4. Integration and System Testing"];
        E [label="5. Operation and Maintenance"];

        A -> B -> C -> D -> E;
    }
    """

    st.graphviz_chart(
        waterfall_diagram,
        use_container_width=True
    )

    st.caption(
        "Reconstructed from the textbook's description "
        "of Waterfall Model, Figure 2.1, page 48. "
        "This is not the original textbook illustration."
    )


def display_sources(sources):

    if sources:

        with st.expander("📖 View textbook sources"):

            for source in sources:

                st.markdown(
                    f"**Page {source.get('page', 'N/A')}** · "
                    f"`{source.get('chunk_id', 'N/A')}`"
                )

                st.write(source.get("text", ""))


def display_message(message):

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message.get("diagram") == "waterfall":

            st.subheader("📊 Waterfall Model – Figure 2.1")

            create_waterfall_diagram()

        display_sources(message.get("sources", []))


def load_conversation(conversation_id):

    conversation = storage.get_conversation(conversation_id)

    if conversation is None:
        st.warning("This conversation could not be found.")
        return

    st.session_state.current_conversation_id = conversation_id

    st.session_state.messages = storage.get_messages(
        conversation_id
    )


def start_new_chat():

    st.session_state.current_conversation_id = None
    st.session_state.messages = []


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("📚 Course Notes AI Tutor")
    st.caption("Your personal AI learning assistant")

    st.divider()

    # ----------------------------------------------
    # DYNAMIC SUBJECT SELECTION
    # ----------------------------------------------

    st.subheader("Choose Subject")

    all_subjects = subject_manager.get_subjects()

    ready_subjects = [
        item["name"]
        for item in all_subjects
        if item["status"] == "ready"
    ]

    pending_subjects = [
        item
        for item in all_subjects
        if item["status"] == "pending"
    ]

    if ready_subjects:

        if st.session_state.subject_selector not in ready_subjects:
            st.session_state.subject_selector = ready_subjects[0]

        subject = st.selectbox(
            "Select a subject",
            ready_subjects,
            key="subject_selector",
            label_visibility="collapsed"
        )

        if st.session_state.active_subject != subject:
            st.session_state.active_subject = subject
            start_new_chat()

        st.info(
            f"{len(ready_subjects)} processed subject(s) available."
        )

    else:
        subject = None
        st.warning("No processed subjects are available yet.")

    st.divider()

    # ----------------------------------------------
    # MANAGE SUBJECTS
    # ----------------------------------------------

    with st.expander("➕ Manage Subjects", expanded=True):

        st.markdown("**1. Register a new subject**")

        with st.form("add_subject_form", clear_on_submit=True):

            new_subject_name = st.text_input(
                "Subject name",
                placeholder="e.g. Operating Systems"
            )

            add_subject_button = st.form_submit_button(
                "Add Subject",
                use_container_width=True
            )

            if add_subject_button:

                try:
                    result = subject_manager.add_subject(
                        new_subject_name
                    )

                    st.session_state.subject_notice = (
                        f"Subject '{result['name']}' added successfully. "
                        "Now upload its textbook below."
                    )

                    st.rerun()

                except (ValueError, Exception) as error:
                    st.error(str(error))

        # Refresh subject information after registration
        all_subjects = subject_manager.get_subjects()

        pending_subjects = [
            item
            for item in all_subjects
            if item["status"] == "pending"
        ]

        st.divider()

        # ------------------------------------------
        # PDF UPLOAD AND PROCESSING
        # ------------------------------------------

        st.markdown("**2. Upload and process textbook**")

        if pending_subjects:

            pending_names = [
                item["name"]
                for item in pending_subjects
            ]

            selected_pending_name = st.selectbox(
                "Choose a pending subject",
                pending_names,
                key="pending_subject_selector"
            )

            selected_pending = next(
                item
                for item in pending_subjects
                if item["name"] == selected_pending_name
            )

            uploaded_pdf = st.file_uploader(
                "Upload textbook PDF",
                type=["pdf"],
                key=f"pdf_upload_{selected_pending['slug']}"
            )

            if uploaded_pdf is not None:

                st.caption(
                    f"Selected file: {uploaded_pdf.name}"
                )

                if st.button(
                    "🚀 Process Textbook",
                    use_container_width=True,
                    type="primary"
                ):

                    subject_slug = selected_pending["slug"]

                    raw_folder = (
                        PROJECT_ROOT
                        / "data"
                        / "raw"
                        / subject_slug
                    )

                    raw_folder.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    pdf_path = raw_folder / "textbook.pdf"

                    try:

                        with open(pdf_path, "wb") as file:
                            file.write(uploaded_pdf.getvalue())

                        with st.spinner(
                            "Processing textbook. This may take "
                            "a few minutes..."
                        ):

                            process_subject(
                                subject_slug,
                                pdf_path
                            )

                        # Clear cached retriever so the new
                        # subject data can be loaded.
                        load_retriever.clear()

                        st.session_state.subject_to_select = (
                            selected_pending["name"]
                        )

                        st.session_state.subject_notice = (
                            f"{selected_pending['name']} has been "
                            "processed successfully and is now ready!"
                        )

                        st.success(
                            "Textbook processing completed successfully!"
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Textbook processing failed: {error}"
                        )

                        st.info(
                            "The subject remains pending. "
                            "You can correct the issue and try again."
                        )

        else:

            st.success("All registered subjects are processed.")

        # ------------------------------------------
        # PENDING SUBJECT LIST
        # ------------------------------------------

        if pending_subjects:

            st.divider()
            st.markdown("**Pending subjects**")

            for item in pending_subjects:

                st.markdown(f"⏳ **{item['name']}**")
                st.caption("Awaiting textbook processing.")

    if st.session_state.subject_notice:

        st.success(st.session_state.subject_notice)
        st.session_state.subject_notice = None

    st.divider()

    # ----------------------------------------------
    # CHAT HISTORY
    # ----------------------------------------------

    st.subheader("💬 Chat History")

    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        start_new_chat()
        st.rerun()

    if subject:

        all_conversations = storage.get_conversations()

        subject_conversations = [
            conversation
            for conversation in all_conversations
            if conversation["subject"] == subject
        ]

        if not subject_conversations:

            st.caption("No previous conversations yet.")

        else:

            st.caption("Your previous conversations")

            for conversation in subject_conversations:

                conversation_id = conversation["conversation_id"]
                conversation_title = conversation["title"]

                col1, col2 = st.columns([0.78, 0.22])

                with col1:

                    if st.button(
                        f"💬 {conversation_title}",
                        key=f"open_{conversation_id}",
                        use_container_width=True
                    ):

                        load_conversation(conversation_id)
                        st.rerun()

                with col2:

                    if st.button(
                        "🗑️",
                        key=f"delete_{conversation_id}",
                        help="Delete this conversation",
                        use_container_width=True
                    ):

                        storage.delete_conversation(conversation_id)

                        if (
                            st.session_state.current_conversation_id
                            == conversation_id
                        ):
                            start_new_chat()

                        st.rerun()

    st.divider()

    st.caption("Powered by FastEmbed and Google Gemini")

# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------

st.markdown(
    '<div style="font-size:2.3rem;font-weight:750;'
    'color:#2563EB;">Course Notes AI Tutor 📖</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div style="color:#64748b;font-size:1rem;">'
    'Ask questions and learn directly from your course materials.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

if not subject:

    st.info(
        "Register a subject and upload its textbook from "
        "Manage Subjects to get started."
    )

else:

    st.subheader(f"💬 Ask your {subject} questions")

    # ----------------------------------------------
    # DISPLAY EXISTING CHAT MESSAGES
    # ----------------------------------------------

    for message in st.session_state.messages:
        display_message(message)

    # ----------------------------------------------
    # CHAT INPUT
    # ----------------------------------------------

    question = st.chat_input(
        "Ask something about your course notes..."
    )

    if question:

        try:

            # CREATE CONVERSATION IF IT DOES NOT EXIST

            if st.session_state.current_conversation_id is None:

                conversation_title = question.strip()

                if len(conversation_title) > 45:
                    conversation_title = (
                        conversation_title[:45] + "..."
                    )

                conversation_id = storage.create_conversation(
                    subject=subject,
                    title=conversation_title
                )

                st.session_state.current_conversation_id = (
                    conversation_id
                )

            else:

                conversation_id = (
                    st.session_state.current_conversation_id
                )

            # SAVE USER QUESTION

            user_message = {
                "role": "user",
                "content": question,
                "sources": [],
                "diagram": None
            }

            storage.add_message(
                conversation_id=conversation_id,
                role="user",
                content=question
            )

            st.session_state.messages.append(user_message)

            with st.chat_message("user"):
                st.markdown(question)

            # GENERATE AI RESPONSE

            with st.chat_message("assistant"):

                with st.spinner(
                    "Searching your textbook and generating an answer..."
                ):

                    retriever = load_retriever()
                    client = load_gemini()

                    passages = retriever.search(
                        question,
                        subject=subject,
                        top_k=5
                    )

                    if not passages:

                        answer = (
                            "I couldn't find relevant information "
                            "in the selected subject's materials."
                        )

                    else:

                        answer = generate_answer(
                            question,
                            passages,
                            client
                        )

                st.markdown(answer)

                # WATERFALL MODEL DIAGRAM SUPPORT

                show_waterfall = (
                    "waterfall" in question.lower()
                    and bool(passages)
                )

                if show_waterfall:

                    st.subheader(
                        "📊 Waterfall Model – Figure 2.1"
                    )

                    create_waterfall_diagram()

                # DISPLAY TEXTBOOK SOURCES

                display_sources(passages)

                # SAVE ASSISTANT RESPONSE

                assistant_message = {
                    "role": "assistant",
                    "content": answer,
                    "sources": passages,
                    "diagram": (
                        "waterfall" if show_waterfall else None
                    )
                }

                storage.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=answer,
                    sources=passages,
                    diagram=assistant_message["diagram"]
                )

                st.session_state.messages.append(
                    assistant_message
                )

            st.rerun()

        except Exception as error:

            st.error(
                f"Something went wrong: {error}"
            )

            st.info(
                "Check your API connection and project configuration."
            )
