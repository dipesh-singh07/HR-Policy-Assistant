"""
HR Policy Assistant - Offline Ground Truth & PDF Validation Test
================================================================
Validates the deterministic ingestion, chunking, and document evidence
without requiring external network calls or active API keys.
Used for offline viva demonstrations and structural validation.
"""

import unittest
from pathlib import Path
from pypdf import PdfReader
from ingest import extract_section_headers
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TestHRManualGroundTruth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdf_path = "data/hr_manual.pdf" if Path("data/hr_manual.pdf").exists() else "hr_manual.pdf"
        cls.reader = PdfReader(cls.pdf_path)

    def test_page_count(self):
        """Verify that the manual contains exactly 79 pages as specified."""
        self.assertEqual(len(self.reader.pages), 79)

    def test_q1_privilege_leave(self):
        """Verify Privilege Leave entitlement on Page 60."""
        page_60_text = self.reader.pages[59].extract_text()
        self.assertIn("Privilege Leave (PL) – 12 days", page_60_text)
        self.assertIn("12 days PL is al", page_60_text)

    def test_q2_probation_period(self):
        """Verify Probation period for employees up to Sr. Manager on Page 42."""
        page_42_text = self.reader.pages[41].extract_text()
        self.assertIn("All employees up to Sr. Manager would be placed in Probation for a period of 3 months", page_42_text)

    def test_q3_health_insurance_absent(self):
        """Verify health insurance premium amount is NOT in the manual."""
        for page in self.reader.pages:
            text = page.extract_text()
            self.assertNotIn("health insurance premium", text.lower())
            self.assertNotIn("mediclaim premium", text.lower())

    def test_q4_gst_absent(self):
        """Verify GST rate is NOT in the manual."""
        for page in self.reader.pages:
            text = page.extract_text()
            self.assertNotIn("gst rate", text.lower())
            self.assertNotIn("goods and services tax", text.lower())

    def test_q5_maternity_leave(self):
        """Verify Maternity Leave entitlement on Page 62."""
        page_62_text = self.reader.pages[61].extract_text()
        normalized_text = " ".join(page_62_text.split())
        self.assertIn("12 weeks", normalized_text)
        self.assertIn("90days", normalized_text)
        self.assertIn("ML with pay", normalized_text)

    def test_section_header_extraction(self):
        """Verify section and policy header extraction across pages."""
        pages_text = [p.extract_text() for p in self.reader.pages]
        headers = extract_section_headers(pages_text)
        self.assertEqual(len(headers), 79)
        self.assertIn("Probation Policy", headers[41])
        self.assertIn("Leave Policy", headers[59])
        self.assertIn("Leave Policy", headers[61])

    def test_chunking_integrity(self):
        """Verify text chunking preserves content and metadata."""
        loader = PyPDFLoader(self.pdf_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        self.assertGreater(len(chunks), 100)
        self.assertTrue(all("page" in c.metadata for c in chunks))


if __name__ == "__main__":
    unittest.main()
