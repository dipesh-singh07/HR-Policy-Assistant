"""
HR Policy Assistant - Streamlit Web Application
==============================================
Provides an interactive, clear web UI for querying the Enso Group HR Policy Manual.

Features:
- Natural-language Q&A interface
- One-click testing for all 5 exam questions
- Grounded answer display with clean 'Not found' indicator
- Transparent source citations with PDF page numbers, sections, and excerpts
- Real-time diagnostic sidebar and error handling
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="HR Policy Assistant - Enso Group",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App Title & Header
st.title("📋 HR Policy Assistant")
st.subheader("Grounded Question & Answer over Enso Group HR Policy Manual")
st.caption("Retrieval-Augmented Generation (RAG) powered by LangChain, ChromaDB, and Google Gemini.")

# Sidebar diagnostics & configuration
with st.sidebar:
    st.header("⚙️ System Status")
    db_exists = os.path.exists("db") and len(os.listdir("db")) > 0
    pdf_exists = os.path.exists("data/hr_manual.pdf") or os.path.exists("hr_manual.pdf")
    api_key_set = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

    st.write("**ChromaDB Index:**", "✅ Ready" if db_exists else "❌ Not Built")
    st.write("**HR Manual PDF:**", "✅ Present (79 pages)" if pdf_exists else "❌ Missing")
    st.write("**Gemini API Key:**", "✅ Configured" if api_key_set else "❌ Missing in .env")

    st.divider()
    st.subheader("Configuration")
    model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    emb_name = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
    top_k = st.slider("Retriever Top-K Chunks", min_value=2, max_value=8, value=4, step=1)

    st.caption(f"**LLM:** `{model_name}`")
    st.caption(f"**Embeddings:** `{emb_name}`")
    st.caption("**PDF Target:** `Enso Group HR Manual (79 pp)`")

# Diagnostic warning banners if prerequisites are unmet
if not api_key_set:
    st.error(
        "⚠️ **Missing API Key**: `GEMINI_API_KEY` is not set in `.env`.\n\n"
        "Please add your Gemini API key to `.env` file to enable RAG generation."
    )
if not db_exists:
    st.warning(
        "⚠️ **Vector Database Not Found**: ChromaDB index `./db` has not been generated yet.\n\n"
        "Run `python ingest.py` in your terminal to ingest and index `hr_manual.pdf`."
    )

# Quick exam test questions
st.markdown("### 🎯 Exam Test Questions (Click to test)")
sample_questions = [
    "How many days of Privilege Leave (PL) does a permanent employee get per year?",
    "What is the probation period for employees up to Senior Manager?",
    "What is the company's health-insurance premium amount?",
    "What is the current GST rate in India?",
    "How many days of maternity leave are given?",
]

# State management for query input
if "query_input" not in st.session_state:
    st.session_state["query_input"] = sample_questions[0]

cols = st.columns(len(sample_questions))
for idx, q_text in enumerate(sample_questions):
    if cols[idx].button(f"Q{idx+1}", help=q_text, use_container_width=True):
        st.session_state["query_input"] = q_text

# Input box for user query
query = st.text_input(
    "Enter an HR policy question:",
    value=st.session_state.get("query_input", ""),
    placeholder="e.g. How many days of Privilege Leave are permitted?"
)

ask_button = st.button("🔍 Search HR Policy", type="primary", use_container_width=True)

# Query Execution
if ask_button or query:
    if not query.strip():
        st.warning("Please enter a question.")
    elif not db_exists or not api_key_set:
        st.error("Cannot query: Please ensure ChromaDB is ingested and GEMINI_API_KEY is configured.")
    else:
        with st.spinner("Retrieving policy evidence and generating grounded response..."):
            try:
                from rag_pipeline import HRPolicyAssistant

                assistant = HRPolicyAssistant(top_k=top_k)
                result = assistant.ask(query)

                st.divider()

                # Display Answer
                if not result["is_found"]:
                    st.error("### Result: Not found")
                    st.info(
                        "ℹ️ **Grounding Rule Applied**: The requested information is not established "
                        "by the Enso Group HR Policy Manual. The assistant strictly refused external speculation."
                    )
                else:
                    st.success("### Answer")
                    st.markdown(result["answer"])

                    # Display Source Citations
                    st.markdown("### 📖 Source Citations & Policy References")
                    for i, src in enumerate(result["sources"], start=1):
                        with st.expander(
                            f"Reference {i}: {src['source']} — Page {src['page']} ({src['section']})",
                            expanded=(i == 1)
                        ):
                            st.markdown(f"**Document:** `{src['source']}`")
                            st.markdown(f"**Page:** `{src['page']}`")
                            st.markdown(f"**Section/Policy:** `{src['section']}`")
                            st.markdown("**Evidence Excerpt:**")
                            st.text(src["snippet"])

            except Exception as ex:
                st.error(f"Error processing query: {ex}")
