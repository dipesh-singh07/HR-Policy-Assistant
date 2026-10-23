# Project 1: HR Policy Assistant — GenAI Exam

A production-grade Retrieval-Augmented Generation (RAG) assistant built over the **Enso Group HR Policy Manual (79 pages)**. The application indexes company policies, retrieves grounded context, cites the exact source page and section, and strictly returns **`Not found`** whenever an answer is not established by the document.

---

## 1. Project Objective

The HR Policy Assistant serves employee queries regarding internal company policies by strictly grounding all answers in the official `hr_manual.pdf`. The core objectives are:
- **Zero Hallucination / Strict Grounding**: Answer only what is explicitly established in the manual.
- **Strict Fallback**: Reply with exactly `Not found` if a topic (e.g. external tax rates or unstated premium amounts) is absent.
- **Transparent Attribution**: Always cite the source PDF filename, page number, and policy section/heading.
- **Index Persistence**: Persist the ChromaDB vector database to disk so it does not re-index on every launch.
- **Interactive Demonstrability**: Provide a Streamlit UI and interactive CLI (`ask.py`) for live viva demonstration.

---

## 2. Technology Stack

- **Language**: Python 3.12+
- **Orchestration**: LangChain (`langchain`, `langchain-core`, `langchain-community`, `langchain-text-splitters`)
- **Document Loading**: PyPDF (`pypdf`, `PyPDFLoader`)
- **Chunking**: `RecursiveCharacterTextSplitter` (700 characters, 100 character overlap)
- **Vector Database**: ChromaDB (`chromadb`, `langchain-chroma`) persisted locally in `./db`
- **Embeddings**: Google Gemini Generative AI Embeddings (`models/text-embedding-004` / `models/embedding-001`) via `langchain-google-genai`
- **LLM**: Google Gemini (`gemini-2.5-flash` / `gemini-1.5-flash`) with deterministic decoding (`temperature=0.0`)
- **User Interface**: Streamlit (`app.py`)
- **Environment Management**: `python-dotenv`

---

## 3. Architecture & RAG Workflow

```
[ hr_manual.pdf (79 pages) ]
             │
             ▼
[ PyPDFLoader + Section Parser ] ──▶ Page-level section metadata extraction
             │
             ▼
[ RecursiveCharacterTextSplitter ] ──▶ 700-char chunks (100 overlap) + metadata
             │
             ▼
[ GoogleGenerativeAIEmbeddings ] ──▶ Vector representations
             │
             ▼
[ ChromaDB (./db directory) ] ──▶ Persistent disk storage
             │
 ┌───────────┴────────────────────────┐
 │ User Query via Streamlit or CLI    │
 └───────────┬────────────────────────┘
             ▼
[ Top-K Vector Retriever ] ──▶ Fetches top 4 relevant chunks
             │
             ▼
[ Grounded Context Formatter ] ──▶ Formats excerpts with Page & Section tags
             │
             ▼
[ Gemini 2.5 Flash LLM ] ──▶ Strict prompt: Answer with citations OR "Not found"
             │
             ▼
[ Structured Output / Display ] ──▶ Verified Answer + Collapsible Source Citations
```

### Key Architectural Decisions:
1. **Hierarchical Metadata Tracking**: `ingest.py` tracks roman numeral sections (`SECTION - I` to `SECTION - IV`) and policy blocks (`[B] Probation Policy`, `[G] Leave Policy`) across consecutive pages.
2. **Page Labeling (1-Indexed)**: PDF 0-indexed page indices are mapped to `page_label = page + 1` so citations match the physical document page numbers printed on the manual (`HR Manual - 42`, `HR Manual - 60`, etc.).
3. **Deterministic Prompt Guardrails**: Temperature is set to `0.0`. The system prompt instructs the model to reply with strictly `Not found` with no extra words if the retrieved context does not establish the answer.

---

## 4. Installation & Setup

### Step 1: Clone or Navigate to the Workspace
```bash
cd /Users/dipeshsingh/Desktop/GENAI
```

### Step 2: Set Up Virtual Environment
Using Python 3.12 (or `uv`):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
*(Or with `uv`)*:
```bash
uv venv .venv --python 3.12
uv pip install --python .venv -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy the template and supply your Gemini API key:
```bash
cp .env.example .env
```
Edit `.env` (or run in terminal):
```bash
printf "Enter GEMINI_API_KEY (typing hidden): " && read -s val && echo && echo "GEMINI_API_KEY=$val" >> .env && echo "Saved."
```

Example `.env` configuration:
```env
GEMINI_API_KEY=AIzaSy...
MODEL_NAME=gemini-2.5-flash
EMBEDDING_MODEL=models/text-embedding-004
TOP_K=4
CHROMA_DB_DIR=db
PDF_PATH=data/hr_manual.pdf
```

---

## 5. Ingestion & Execution Commands

### Ingest the Document
Run the ingestion script to extract, chunk, embed, and persist `hr_manual.pdf` into `./db`:
```bash
.venv/bin/python ingest.py
```
*Output confirmation: `SUCCESS: ChromaDB index successfully saved to ./db`.*

### Run Automated Offline Grounding Tests
Validates document facts, section detection, and page counts without external network calls:
```bash
.venv/bin/python test_offline_grounding.py
```

### Run End-to-End Exam Test Suite
Runs the 5 required exam questions through the RAG pipeline and validates grounding:
```bash
.venv/bin/python test_questions.py
```

### Launch Interactive CLI Tool
```bash
.venv/bin/python ask.py
```
Or for a one-off query:
```bash
.venv/bin/python ask.py "What is the probation period for employees up to Senior Manager?"
```

### Launch Streamlit Web Application
```bash
.venv/bin/streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 6. Required Test Questions & Evidence-Backed Answers

All five required exam questions were evaluated against the official Enso Group HR Policy Manual:

| # | Question | Grounded Answer | Status | Source Page | Policy Section | Evidence Excerpt from Document |
|---|---|---|---|---|---|---|
| **1** | How many days of Privilege Leave (PL) does a permanent employee get per year? | Permanent employees are entitled to **12 days of Privilege Leave (PL)** per calendar year (1st Jan – 31st Dec). | **Found** | **Page 60** | `SECTION - IV - [G] Leave Policy` | *"Privilege Leave (PL) – 12 days... All permanent employees are eligible to avail PL. PL is calculated for a period of one calendar year (1st Jan-31st Dec). 12 days PL is allowed to each employee."* |
| **2** | What is the probation period for employees up to Senior Manager? | The probation period for all employees up to Senior Manager is **3 months** from the date of joining. | **Found** | **Page 42** | `SECTION - IV - [B] Probation Policy` | *"All employees up to Sr. Manager would be placed in Probation for a period of 3 months from the date of their joining."* |
| **3** | What is the company's health-insurance premium amount? | **Not found** | **Not found** | *N/A* | *N/A* | The manual does not state or establish any health-insurance premium amount. The system strictly outputs `Not found`. |
| **4** | What is the current GST rate in India? | **Not found** | **Not found** | *N/A* | *N/A* | External statutory GST rates are not part of the Enso Group HR Policy Manual. The system refuses external knowledge and outputs `Not found`. |
| **5** | How many days of maternity leave are given? | Female employees who have worked for at least 80 days in the preceding 12 months are entitled to **12 weeks (90 days)** of Maternity Leave with pay (not more than 6 weeks / 45 days preceding expected delivery). | **Found** | **Page 62** | `SECTION - IV - [G] Leave Policy` | *"The company will provide a total of 12 weeks(- 90days) as ML with pay, of which not more than 6 weeks(- 45days) should precede the expected date of delivery."* |

---

## 7. Viva Demonstration Guide

When explaining this project to an examiner during a viva:

1. **How does RAG prevent hallucinations?**
   - The model's temperature is set to `0.0`.
   - The prompt instructs the model to only use the context inside `{context}`.
   - For Question 3 (Health Insurance Premium) and Question 4 (GST Rate), the document contains no information. Instead of relying on pre-training data, the model returns exactly `Not found`.

2. **How is persistence achieved?**
   - ChromaDB writes embeddings to the `./db` directory.
   - When `app.py` or `ask.py` runs, it re-opens `Chroma(persist_directory="db", ...)` without calling `ingest.py` again.

3. **How are chunking boundaries chosen?**
   - `RecursiveCharacterTextSplitter` with `chunk_size=700` and `chunk_overlap=100` ensures sentences and policy clauses are not severed at boundaries.

4. **How are page numbers and sections cited?**
   - `PyPDFLoader` attaches the zero-indexed page number to each chunk.
   - Ingestion extracts the active policy heading and enriches each chunk's metadata with `page_label = page + 1` and `section`.

---

## 8. Known Limitations & Potential Improvements

1. **Scanned / Table Layouts**: `pypdf` extracts text sequentially; complex multi-column tables in PDFs can occasionally merge table columns. A layout-aware parser (e.g. `unstructured` or `pdfplumber`) could further improve table structure.
2. **Re-ranking**: Top-4 similarity search works reliably for standard queries. Adding a cross-encoder re-ranker (e.g., FlashRank or Cohere ReRank) could improve retrieval on highly nuanced multi-hop queries.
3. **Conversational Memory**: The current implementation answers each query independently to guarantee strict grounding without cross-turn context contamination. A sliding window buffer could be added for multi-turn chats.
