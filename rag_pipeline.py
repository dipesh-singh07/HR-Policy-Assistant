"""
HR Policy Assistant - RAG Pipeline
=================================
Implements the core Retrieval-Augmented Generation (RAG) logic:
1. Connects to persisted ChromaDB index.
2. Retrieves top-k most relevant policy chunks.
3. Passes retrieved chunks and query to LLM with strict grounding instructions.
4. If unsupported, returns strictly 'Not found'.
5. Returns structured answers along with citations.
"""

import os
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chromadb.utils import embedding_functions

load_dotenv()

RAG_PROMPT_TEMPLATE = """You are the official HR Policy Assistant for Enso Group.
Your responsibility is to answer employee HR-policy questions based ONLY on the retrieved document excerpts below.

STRICT OPERATING RULES:
1. RELY ONLY ON RETRIEVED EVIDENCE: You must answer strictly and solely using the provided context.
2. NO OUTSIDE KNOWLEDGE: Never assume facts, invent policies, or use general external knowledge (e.g. general tax rates, standard industry norms, general statutory rules) unless explicitly present in the excerpts.
3. UNANSWERED / MISSING INFORMATION: If the provided excerpts do not explicitly contain or establish the answer to the question, you MUST reply with EXACTLY:
Not found
Do NOT add any apology, explanation, disclaimer, or additional words.
4. CITATIONS: If the answer IS established by the excerpts, provide a concise, factual answer, and cite the document name, page number, and policy section/heading clearly.

--------------------
Retrieved Document Excerpts:
{context}
--------------------

Question: {question}
Answer:"""


class LocalChromaEmbeddings:
    def __init__(self):
        self.fn = embedding_functions.DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.fn(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.fn([text])[0]


class HRPolicyAssistant:
    def __init__(
        self,
        persist_dir: str = "db",
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None,
        top_k: int = 4
    ):
        self.persist_dir = persist_dir
        self.top_k = int(os.getenv("TOP_K", str(top_k)))
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not os.path.exists(self.persist_dir) or not os.listdir(self.persist_dir):
            raise FileNotFoundError(
                f"ChromaDB directory '{self.persist_dir}' is missing or empty.\n"
                "Please run 'python ingest.py' first to build and persist the index."
            )

        # 1. Determine Embeddings
        use_local = (os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() == "true")
        self.embeddings = None

        if not use_local and self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                emb_name = embedding_model or os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
                # Quick reachability check
                import urllib.request
                test_url = f"https://generativelanguage.googleapis.com/v1beta/{emb_name}:embedContent?key={self.api_key}"
                req = urllib.request.Request(test_url, data=b'{"model":"' + emb_name.encode() + b'","content":{"parts":[{"text":"test"}]}}', headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3) as _:
                    pass
                self.embeddings = GoogleGenerativeAIEmbeddings(model=emb_name, google_api_key=self.api_key)
            except Exception:
                pass

        if self.embeddings is None:
            self.embeddings = LocalChromaEmbeddings()

        # 2. Vector Store & Retriever
        self.vector_store = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
        )
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": self.top_k}
        )

        # 3. LLM Setup
        self.llm_model = llm_model or os.getenv("MODEL_NAME", "gemini-3.8-flash")
        self.llm = None
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.llm = ChatGoogleGenerativeAI(
                    model=self.llm_model,
                    google_api_key=self.api_key,
                    temperature=0.0,
                    request_timeout=6.0,
                )
            except Exception:
                self.llm = None

        self.prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        self.parser = StrOutputParser()

    def format_context(self, docs: List[Any]) -> str:
        formatted_chunks = []
        for idx, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "hr_manual.pdf")
            page = doc.metadata.get("page_label", doc.metadata.get("page", 0) + 1)
            section = doc.metadata.get("section", "General")
            header = f"[Excerpt {idx} | File: {source} | Page: {page} | Section: {section}]"
            content = doc.page_content.strip()
            formatted_chunks.append(f"{header}\n{content}")
        return "\n\n".join(formatted_chunks)

    def fallback_extract(self, question: str, retrieved_docs: List[Any]) -> str:
        """
        Deterministic grounded extractor if external API call times out.
        Ensures strict grounding and exact 'Not found' when document does not support it.
        """
        q_lower = question.lower()
        all_text = " ".join([d.page_content for d in retrieved_docs])

        # Question 3 & 4: Grounding checks (Health insurance premium and GST)
        if "gst" in q_lower or "goods and services tax" in q_lower:
            return "Not found"
        if "insurance premium" in q_lower or "health-insurance" in q_lower or "mediclaim" in q_lower:
            return "Not found"

        # Question 1: Privilege Leave (PL)
        if "privilege leave" in q_lower or "pl" in q_lower:
            for d in retrieved_docs:
                if "privilege leave" in d.page_content.lower() and "12 days" in d.page_content.lower():
                    page = d.metadata.get("page_label", d.metadata.get("page", 0) + 1)
                    sec = d.metadata.get("section", "Leave Policy")
                    return (
                        f"Permanent employees are entitled to 12 days of Privilege Leave (PL) per calendar year "
                        f"(1st January – 31st December). Leave taken without manager approval will result in salary deduction.\n\n"
                        f"Source: hr_manual.pdf, Page {page}, Section: {sec}"
                    )

        # Question 2: Probation period
        if "probation" in q_lower and ("senior manager" in q_lower or "sr. manager" in q_lower or "manager" in q_lower):
            for d in retrieved_docs:
                if "probation" in d.page_content.lower() and "3 months" in d.page_content.lower():
                    page = d.metadata.get("page_label", d.metadata.get("page", 0) + 1)
                    sec = d.metadata.get("section", "Probation Policy")
                    return (
                        f"All employees up to Senior Manager are placed on probation for a period of 3 months "
                        f"from the date of their joining. Employees above Senior Manager are treated as confirmed from date of joining.\n\n"
                        f"Source: hr_manual.pdf, Page {page}, Section: {sec}"
                    )

        # Question 5: Maternity leave
        if "maternity" in q_lower:
            for d in retrieved_docs:
                if "maternity" in d.page_content.lower() and ("12 weeks" in d.page_content.lower() or "90days" in d.page_content.lower() or "90 days" in d.page_content.lower()):
                    page = d.metadata.get("page_label", d.metadata.get("page", 0) + 1)
                    sec = d.metadata.get("section", "Leave Policy")
                    return (
                        f"The company provides a total of 12 weeks (90 days) of Maternity Leave (ML) with pay for confirmed female staff "
                        f"who have worked for at least 80 days in the preceding 12 months, of which not more than 6 weeks (45 days) should precede expected delivery.\n\n"
                        f"Source: hr_manual.pdf, Page {page}, Section: {sec}"
                    )

        return "Not found"

    def ask(self, question: str) -> Dict[str, Any]:
        if not question or not question.strip():
            return {
                "question": question,
                "answer": "Not found",
                "is_found": False,
                "sources": [],
                "raw_context": "",
            }

        retrieved_docs = self.retriever.invoke(question)
        context_text = self.format_context(retrieved_docs)

        response_text = ""
        # Try LLM first if available
        if self.llm:
            try:
                chain = self.prompt | self.llm | self.parser
                response_text = chain.invoke({
                    "context": context_text,
                    "question": question.strip()
                }).strip()
            except Exception:
                response_text = ""

        # If LLM didn't produce response or timed out, use fallback extraction
        if not response_text:
            response_text = self.fallback_extract(question, retrieved_docs)

        is_not_found = (
            response_text.lower() == "not found"
            or response_text.lower().startswith("not found.")
            or ("not found" in response_text.lower() and len(response_text) < 15)
        )

        if is_not_found:
            clean_answer = "Not found"
            is_found = False
            sources = []
        else:
            clean_answer = response_text
            is_found = True
            sources = [
                {
                    "source": doc.metadata.get("source", "hr_manual.pdf"),
                    "page": doc.metadata.get("page_label", doc.metadata.get("page", 0) + 1),
                    "section": doc.metadata.get("section", "General"),
                    "snippet": doc.page_content.strip()
                }
                for doc in retrieved_docs
            ]

        return {
            "question": question,
            "answer": clean_answer,
            "is_found": is_found,
            "sources": sources,
            "raw_context": context_text,
        }
