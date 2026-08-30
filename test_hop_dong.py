# -*- coding: utf-8 -*-
"""Tests for the immutable SEEKER -> Quantlab artifact contract.

Run from the repository root:
    python -m unittest lab.test_hop_dong

Every database assertion uses a temporary SQLite file, never lab/nao.db.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import so
from nhan.hop_dong import (
    CandidateArtifact,
    CodeArtifact,
    ContractError,
    DocumentArtifact,
    TradeHistoryArtifact,
    artifact_from_json,
)


NOW = "2026-08-16T16:00:00Z"
LATER = "2026-08-16T16:05:00Z"


def make_document(retrieved_at: str = NOW) -> DocumentArtifact:
    return DocumentArtifact(
        source_id="arxiv",
        source_url="https://arxiv.org/abs/2608.00001",
        title="A reproducible market microstructure result",
        retrieved_at=retrieved_at,
        content="Observed spread predicts short-horizon execution cost.",
        media_type="text/plain",
        published_at="2026-08-15T09:00:00+00:00",
        author="Researcher A",
        language="en",
        license="CC-BY-4.0",
        metadata={"http": {"status": 200}, "source_rank": "B"},
    )


def make_candidate(source_fingerprint: str, created_at: str = NOW,
                   title: str = "Spread may predict execution cost") -> CandidateArtifact:
    return CandidateArtifact(
        candidate_kind="empirical_result",
        title=title,
        summary="The source reports a measurable relation worth independent testing.",
        source_artifact_fingerprints=[source_fingerprint],
        evidence=[{
            "artifact_fingerprint": source_fingerprint,
            "quote": "Observed spread predicts short-horizon execution cost.",
            "locator": "body",
        }],
        created_at=created_at,
        tags=["execution", "spread"],
        extractor="seeker-triage",
        extractor_version="1.0.0",
        confidence=0.82,
    )


class ContractTests(unittest.TestCase):
    def test_document_round_trip_and_retry_fingerprint(self) -> None:
        first = make_document(NOW)
        retry = make_document(LATER)

        self.assertEqual(first.fingerprint, retry.fingerprint)
        self.assertEqual(len(first.fingerprint), 64)
        decoded = artifact_from_json(first.to_json())
        self.assertIsInstance(decoded, DocumentArtifact)
        self.assertEqual(decoded, first)
        first.validate()

    def test_tampered_payload_is_rejected(self) -> None:
        envelope = make_document().to_dict()
        envelope["payload"]["title"] = "Tampered title"

        with self.assertRaisesRegex(ContractError, "fingerprint"):
            DocumentArtifact.from_dict(envelope)

        envelope = make_document().to_dict()
        envelope["payload"]["content_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "content_sha256"):
            DocumentArtifact.from_dict(envelope)

    def test_code_and_trade_history_are_normalized(self) -> None:
        code = CodeArtifact(
            source_id="github",
            repository_url="https://github.com/example/research",
            revision="6a81c58",
            path=r"src\signal.py",
            retrieved_at=NOW,
            content="def signal(x):\n    return x > 0\n",
            language="python",
            license="MIT",
        )
        self.assertEqual(code.path, "src/signal.py")
        self.assertIsInstance(CodeArtifact.from_json(code.to_json()), CodeArtifact)

        history = TradeHistoryArtifact(
            source_id="darwinex",
            source_url="https://www.darwinex.com/account/public-123",
            provider="Darwinex",
            account_ref="sha256:pseudonymous-account",
            retrieved_at=NOW,
            records=[
                {"record_id": "2", "record_type": "equity",
                 "occurred_at": "2026-08-16T11:00:00+07:00", "value": 10010.0},
                {"record_id": "1", "record_type": "fill",
                 "occurred_at": "2026-08-16T10:00:00+07:00", "symbol": "EURUSD",
                 "side": "long", "quantity": 0.1},
            ],
            base_currency="usd",
        )
        self.assertEqual(history.base_currency, "USD")
        self.assertEqual(history.records[0]["record_id"], "1")
        self.assertEqual(history.period_start, "2026-08-16T03:00:00Z")
        self.assertIsInstance(TradeHistoryArtifact.from_json(history.to_json()), TradeHistoryArtifact)

    def test_validation_rejects_unsafe_or_ambiguous_input(self) -> None:
        with self.assertRaisesRegex(ContractError, "timezone"):
            DocumentArtifact(
                source_id="web",
                source_url="https://example.com/paper",
                title="Paper",
                retrieved_at="2026-08-16 16:00:00",
                content="content",
            )
        with self.assertRaisesRegex(ContractError, "relative repository"):
            CodeArtifact(
                source_id="github",
                repository_url="https://github.com/example/research",
                revision="main",
                path="../secret.txt",
                retrieved_at=NOW,
                content="secret",
            )
        document = make_document()
        with self.assertRaisesRegex(ContractError, "undeclared source"):
            CandidateArtifact(
                candidate_kind="method",
                title="Candidate",
                summary="Summary",
                source_artifact_fingerprints=[document.fingerprint],
                evidence=[{
                    "artifact_fingerprint": "0" * 64,
                    "quote": "unsupported",
                }],
                created_at=NOW,
            )


class LedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="brain_contract_test_")
        self.original_db = so.DB
        so.DB = Path(self.temp_dir.name) / "nao.db"
        so.khoi_tao()
        so.khoi_tao()  # Migration is safe to run repeatedly on an existing DB.

    def tearDown(self) -> None:
        so.DB = self.original_db
        self.temp_dir.cleanup()

    def test_artifact_and_candidate_queue_are_idempotent_and_append_only(self) -> None:
        document = make_document()
        candidate = make_candidate(document.fingerprint)

        with self.assertRaisesRegex(ContractError, "missing source artifacts"):
            so.xep_candidate(candidate, priority=2)

        artifact_id, artifact_created = so.them_artifact(document)
        retry_id, retry_created = so.them_artifact(make_document(LATER))
        self.assertTrue(artifact_created)
        self.assertFalse(retry_created)
        self.assertEqual(retry_id, artifact_id)

        queue_id, queue_created = so.xep_candidate(candidate, priority=2)
        retry_queue_id, retry_queue_created = so.xep_candidate(
            make_candidate(document.fingerprint, LATER), priority=2
        )
        self.assertTrue(queue_created)
        self.assertFalse(retry_queue_created)
        self.assertEqual(retry_queue_id, queue_id)

        second_candidate = make_candidate(
            document.fingerprint, title="A second independently testable result"
        )
        second_queue_id, _ = so.xep_candidate(second_candidate, priority=1)

        first_page = so.doc_candidate_queue(limit=1)
        second_page = so.doc_candidate_queue(after_id=first_page[-1]["id"], limit=1)
        self.assertEqual(first_page[0]["id"], queue_id)
        self.assertEqual(first_page[0]["priority"], 2)
        self.assertEqual(second_page[0]["id"], second_queue_id)
        self.assertEqual(second_page[0]["priority"], 1)
        self.assertIsInstance(first_page[0]["candidate"], CandidateArtifact)

        with so.ket_noi() as connection:
            counts = {
                "artifact": connection.execute("SELECT COUNT(*) FROM artifact").fetchone()[0],
                "candidate_queue": connection.execute(
                    "SELECT COUNT(*) FROM candidate_queue"
                ).fetchone()[0],
            }
            self.assertEqual(counts, {"artifact": 3, "candidate_queue": 2})
            with self.assertRaises(sqlite3.DatabaseError):
                connection.execute("UPDATE artifact SET artifact_type='other' WHERE id=?", (artifact_id,))
            with self.assertRaises(sqlite3.DatabaseError):
                connection.execute("DELETE FROM candidate_queue WHERE id=?", (queue_id,))
            with self.assertRaises(sqlite3.DatabaseError):
                connection.execute(
                    "INSERT INTO candidate_queue("
                    "candidate_fingerprint,artifact_id,priority,route,enqueued_at) "
                    "VALUES(?,?,?,?,?)",
                    (document.fingerprint, artifact_id, 5, "QUANTLAB", NOW),
                )


if __name__ == "__main__":
    unittest.main()
