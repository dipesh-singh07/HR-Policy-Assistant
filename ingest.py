"""
HR Policy Assistant - Document Ingestion Script
==============================================
Loads the Enso Group HR Policy Manual PDF, extracts text while tracking
policy sections and page numbers, chunks the text into overlapping segments,
generates vector embeddings, and persists them into ChromaDB.

Usage:
    python ingest.py [path_to_pdf] [--local]
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from chromadb.utils import embedding_functions

load_dotenv()


class LocalChromaEmbeddings:
    """Wrapper around Chroma's local ONNX all-MiniLM-L6-v2 embeddings for LangChain."""
    def __init__(self):
        self.fn = embedding_functions.DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.fn(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.fn([text])[0]


def extract_section_headers(pages_text: list[str]) -> list[str]:
    page_sections = []
    current_section = "General Introduction"
    current_policy = ""

    for page_num, text in enumerate(pages_text, start=1):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:8]:
            sec_match = re.search(r"(SECTION\s*-\s*[IVX]+(?:\s*:\s*[A-Z\s]+)?)", line, re.IGNORECASE)
            if sec_match:
                current_section = sec_match.group(1).strip()
            pol_match = re.search(r"(\[[A-Z]\]\s*[^0-9\n\r]+(?:Policy|Code|Procedure)?)", line, re.IGNORECASE)
            if pol_match:
                current_policy = pol_match.group(1).strip()
            ann_match = re.search(r"(Annexure\s+[IVX]+[^\n\r]*)", line, re.IGNORECASE)
            if ann_match:
                current_policy = ann_match.group(1).strip()

        if current_policy:
            combined = f"{current_section} - {current_policy}"
        else:
            combined = current_section
        page_sections.append(combined)

    return page_sections


def get_embeddings(force_local: bool = False):
    """Initializes embeddings: tries Gemini if key configured, otherwise local ONNX."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    use_local = force_local or (os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() == "true")

    if not use_local and api_key and api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            emb_model = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
            print(f"[3/4] Trying Google Gemini embeddings ({emb_model})...")
            gemini_emb = GoogleGenerativeAIEmbeddings(model=emb_model, google_api_key=api_key)
            # Test one query with short timeout to ensure network is reachable
            import urllib.request
            test_url = f"https://generativelanguage.googleapis.com/v1beta/{emb_model}:embedContent?key={api_key}"
            req = urllib.request.Request(test_url, data=b'{"model":"' + emb_model.encode() + b'","content":{"parts":[{"text":"test"}]}}', headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as _:
                pass
            print(f"      Connected successfully to Google Gemini embeddings ({emb_model}).")
            return gemini_emb
        except Exception as e:
            print(f"      [Notice] Google Gemini embeddings endpoint unreachable/timed out ({e}).")
            print("      Falling back to local ONNX (all-MiniLM-L6-v2) embedding engine...")

    print("[3/4] Using local ONNX embeddings (all-MiniLM-L6-v2)...")
    return LocalChromaEmbeddings()


def ingest_document(pdf_path: str = None, persist_dir: str = "db", force_local: bool = False) -> Chroma:
    if not pdf_path:
        if os.path.exists("data/hr_manual.pdf"):
            pdf_path = "data/hr_manual.pdf"
        elif os.path.exists("hr_manual.pdf"):
            pdf_path = "hr_manual.pdf"
        else:
            raise FileNotFoundError("Could not locate 'hr_manual.pdf'.")

    print(f"[1/4] Loading document: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    raw_documents = loader.load()
    print(f"      Loaded {len(raw_documents)} pages.")

    raw_texts = [doc.page_content for doc in raw_documents]
    sections = extract_section_headers(raw_texts)

    for i, doc in enumerate(raw_documents):
        doc.metadata["page_label"] = i + 1
        doc.metadata["section"] = sections[i]
        doc.metadata["source"] = Path(pdf_path).name

    print("[2/4] Splitting text into overlapping chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(raw_documents)
    print(f"      Created {len(chunks)} chunks.")

    embeddings = get_embeddings(force_local=force_local)

    print(f"[4/4] Ingesting and persisting to './{persist_dir}'...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    print(f"SUCCESS: ChromaDB index successfully saved to ./{persist_dir} ({len(chunks)} chunks).")
    return vector_store


if __name__ == "__main__":
    force_local = "--local" in sys.argv
    target_pdf = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            target_pdf = arg
            break
    ingest_document(pdf_path=target_pdf, force_local=force_local)
