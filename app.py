
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

sys.path.insert(0, str(SCRIPTS_DIR))

from retrieve import SemanticRetriever
from ask_tutor import generate_answer

# Load API key
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


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>
.main-title {
    font-size: 2.3rem;
    font-weight: 750;
    color: #2563EB;
}

.subtitle {
    color: #64748b;
    font-size: 1rem;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("📚 Course Notes AI Tutor")
    st.caption("Your personal AI learning assistant")

    st.divider()

    st.subheader("Choose Subject")

    subject = st.selectbox(
        "Select a subject",
        ["Software Engineering"],
        label_visibility="collapsed"
    )

    st.info(
        "Currently available: Software Engineering. "
        "More subjects can be added through the document manager."
    )

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Powered by FastEmbed and Google Gemini")


# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------

st.markdown(
    '<div class="main-title">Course Notes AI Tutor 📖</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Ask questions and learn directly from your course materials.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

st.subheader(f"💬 Ask your {subject} questions")


# --------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# Display previous messages
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        # Display reconstructed diagram if applicable
        if message.get("diagram") == "waterfall":

            st.subheader("📊 Waterfall Model – Figure 2.1")

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

        # Display textbook sources
        if message.get("sources"):

            with st.expander("📖 View textbook sources"):

                for source in message["sources"]:

                    st.markdown(
                        f"**Page {source['page']}** · "
                        f"`{source['chunk_id']}`"
                    )

                    st.write(source["text"])


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

question = st.chat_input(
    "Ask something about your course notes..."
)


if question:

    # Display user question
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    # Generate assistant response
    with st.chat_message("assistant"):

        try:

            with st.spinner(
                "Searching your textbook and generating an answer..."
            ):

                retriever = load_retriever()
                client = load_gemini()

                # Retrieve relevant textbook passages
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

                    # Generate Gemini answer
                    answer = generate_answer(
                        question,
                        passages,
                        client
                    )

            # Display generated answer
            st.markdown(answer)


            # --------------------------------------------------
            # WATERFALL MODEL DIAGRAM SUPPORT
            # --------------------------------------------------

            show_waterfall = (
                "waterfall" in question.lower()
                and bool(passages)
            )

            if show_waterfall:

                st.subheader(
                    "📊 Waterfall Model – Figure 2.1"
                )

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


            # --------------------------------------------------
            # TEXTBOOK SOURCE REFERENCES
            # --------------------------------------------------

            if passages:

                with st.expander("📖 View textbook sources"):

                    for source in passages:

                        st.markdown(
                            f"**Page {source['page']}** · "
                            f"`{source['chunk_id']}`"
                        )

                        st.write(source["text"])


            # Save assistant response
            st.session_state.messages.append({

                "role": "assistant",

                "content": answer,

                "sources": passages,

                "diagram": (
                    "waterfall" if show_waterfall else None
                )

            })


        except Exception as error:

            st.error(
                f"Something went wrong: {error}"
            )

            st.info(
                "Check your API connection and project configuration."
            )
