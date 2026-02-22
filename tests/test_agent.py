"""
Tests for the Research Digest Agent

Covers:
1. Empty/unreachable source handling
2. Deduplication of duplicate content
3. Preservation of conflicting claims
"""

import pytest
import os
import tempfile
from app.ingestion import ingest
from app.extractor import extract_claims
from app.deduplicator import group_claims, deduplicate_exact

THRESHOLD = 0.78


class TestIngestion:
    def test_empty_source_handling(self):
        docs = ingest(["nonexistent_file.txt"])
        assert docs == []

    def test_url_fetch_failure(self):
        docs = ingest(["https://invalid-domain-xyz-123.com"])
        assert docs == []

    def test_valid_file_ingestion(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a valid test document with enough meaningful content to pass filtering requirements.")
            temp_path = f.name

        try:
            docs = ingest([temp_path])
            assert len(docs) == 1
            assert docs[0]["length"] > 0
            assert "test document" in docs[0]["text"].lower()
        finally:
            os.unlink(temp_path)

    def test_short_content_ignored(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Too short.")
            temp_path = f.name

        try:
            docs = ingest([temp_path])
            assert len(docs) == 0
        finally:
            os.unlink(temp_path)


class TestExtraction:
    def test_claim_extraction(self):
        doc = {
            "source": "test.txt",
            "title": "Test",
            "text": "Artificial intelligence is transforming industries across multiple sectors and improving efficiency significantly worldwide.",
            "length": 200
        }

        claims = extract_claims(doc)
        assert len(claims) >= 1

        for claim in claims:
            assert "claim" in claim
            assert "evidence" in claim
            assert "source" in claim

    def test_empty_document(self):
        doc = {"source": "empty.txt", "title": "Empty", "text": "", "length": 0}
        claims = extract_claims(doc)
        assert claims == []


class TestDeduplication:
    def test_exact_deduplication(self):
        claims = [
            {"claim": "AI is growing fast", "source": "A"},
            {"claim": "AI is growing fast", "source": "A"},
            {"claim": "Artificial intelligence is growing fast", "source": "B"}
        ]

        unique_claims = deduplicate_exact(claims)
        assert len(unique_claims) == 2

    def test_semantic_grouping(self):
        claims = [
            {"claim": "AI is growing fast", "source": "A"},
            {"claim": "Artificial intelligence is growing fast", "source": "B"},
            {"claim": "Weather patterns are changing globally due to climate shifts", "source": "C"}
        ]

        groups = group_claims(claims, threshold=THRESHOLD)

        assert len(groups) <= 3
        total = sum(len(g) for g in groups)
        assert total == 3


class TestGrouping:
    def test_conflicting_claims_preserved(self):
        claims = [
            {"claim": "Remote work increases productivity significantly for employees", "source": "A"},
            {"claim": "Remote work decreases productivity due to collaboration challenges", "source": "B"}
        ]

        groups = group_claims(claims, threshold=THRESHOLD)

        total = sum(len(g) for g in groups)
        assert total == 2  # both claims preserved

    def test_empty_input(self):
        groups = group_claims([])
        assert groups == []

    def test_multiple_sources_grouping(self):
        claims = [
            {"claim": "AI transforms healthcare systems and patient outcomes globally", "source": "1"},
            {"claim": "AI transforms finance through automation and data analysis", "source": "2"},
            {"claim": "AI transforms manufacturing with smart automation techniques", "source": "3"}
        ]

        groups = group_claims(claims, threshold=THRESHOLD)

        total = sum(len(g) for g in groups)
        assert total == 3


class TestPipeline:
    def test_complete_pipeline(self):
        from app.pipeline import run_pipeline

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
            f1.write("Artificial intelligence is transforming industries and improving decision making processes significantly across sectors.")
            p1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
            f2.write("Remote work increases flexibility but also introduces communication challenges in distributed teams.")
            p2 = f2.name

        try:
            docs, claims, groups = run_pipeline([p1, p2], threshold=THRESHOLD)

            assert len(docs) == 2
            assert len(claims) > 0
            assert len(groups) > 0

        finally:
            os.unlink(p1)
            os.unlink(p2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])