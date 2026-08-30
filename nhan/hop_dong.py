# -*- coding: utf-8 -*-
"""Versioned hand-off contract from SEEKER to downstream consumers.

SEEKER owns acquisition, normalization, and provenance.  These artifacts carry
evidence across that boundary; they deliberately do not contain executable
strategy logic, backtest plans, or acceptance decisions.

The wire format is a strict JSON envelope::

    {
      "schema_version": 1,
      "artifact_type": "document",
      "fingerprint": "<sha256>",
      "payload": {...}
    }

Fingerprints include every semantic payload field but omit retrieval/creation
timestamps.  Retrying the same hand-off is therefore idempotent, while changed
content or provenance creates a new immutable artifact.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, Sequence, TypeAlias
from urllib.parse import urlsplit


SCHEMA_VERSION = 1
ARTIFACT_TYPES = frozenset({"document", "code", "trade_history", "candidate"})
CANDIDATE_KINDS = frozenset(
    {"method", "empirical_result", "code", "track_record", "dataset", "other"}
)
TRADE_RECORD_TYPES = frozenset(
    {"order", "fill", "position", "balance", "equity", "cashflow", "snapshot"}
)

JsonValue: TypeAlias = (
    None | bool | int | float | str | tuple["JsonValue", ...] | Mapping[str, "JsonValue"]
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """The object does not satisfy the SEEKER hand-off contract."""


def _text(name: str, value: Any, *, preserve: bool = False) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{name} must be a string")
    normalised = value if preserve else value.strip()
    if not normalised:
        raise ContractError(f"{name} must not be empty")
    return normalised


def _optional_text(name: str, value: Any) -> str | None:
    if value is None:
        return None
    return _text(name, value)


def _uri(name: str, value: Any) -> str:
    uri = _text(name, value)
    parsed = urlsplit(uri)
    if not parsed.scheme:
        raise ContractError(f"{name} must be an absolute URI")
    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        raise ContractError(f"{name} must include a host")
    return uri


def _timestamp(name: str, value: Any, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    raw = _text(name, value)
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError as exc:
        raise ContractError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractError(f"{name} must include a timezone")
    parsed = parsed.astimezone(timezone.utc)
    timespec = "microseconds" if parsed.microsecond else "seconds"
    return parsed.isoformat(timespec=timespec).replace("+00:00", "Z")


def _freeze_json(value: Any, path: str = "metadata") -> JsonValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractError(f"{path} contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, JsonValue] = {}
        keys = list(value)
        if any(not isinstance(key, str) for key in keys):
            raise ContractError(f"{path} keys must be strings")
        for key in sorted(keys):
            frozen[key] = _freeze_json(value[key], f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, f"{path}[]") for item in value)
    raise ContractError(f"{path} contains unsupported type {type(value).__name__}")


def _thaw_json(value: JsonValue | Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            _thaw_json(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContractError(f"value is not canonical JSON: {exc}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _fingerprint(value: Any, name: str = "fingerprint") -> str:
    fingerprint = _text(name, value).lower()
    if not _SHA256_RE.fullmatch(fingerprint):
        raise ContractError(f"{name} must be a 64-character SHA-256 hex string")
    return fingerprint


def _metadata(value: Any) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ContractError("metadata must be a JSON object")
    frozen = _freeze_json(value)
    assert isinstance(frozen, Mapping)
    return frozen


class _ArtifactMixin:
    schema_version: ClassVar[int] = SCHEMA_VERSION
    artifact_type: ClassVar[str]

    def _payload(self) -> dict[str, Any]:
        raise NotImplementedError

    def _identity_payload(self) -> dict[str, Any]:
        payload = self._payload()
        payload.pop("retrieved_at", None)
        payload.pop("created_at", None)
        return payload

    @property
    def fingerprint(self) -> str:
        identity = {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "payload": self._identity_payload(),
        }
        return _sha256(identity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "fingerprint": self.fingerprint,
            "payload": _thaw_json(self._payload()),
        }

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    def validate(self) -> None:
        artifact_from_dict(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]):
        artifact = artifact_from_dict(value)
        if not isinstance(artifact, cls):
            raise ContractError(
                f"expected artifact_type={cls.artifact_type}, got {artifact.artifact_type}"
            )
        return artifact

    @classmethod
    def from_json(cls, value: str):
        artifact = artifact_from_json(value)
        if not isinstance(artifact, cls):
            raise ContractError(
                f"expected artifact_type={cls.artifact_type}, got {artifact.artifact_type}"
            )
        return artifact


@dataclass(frozen=True, slots=True)
class DocumentArtifact(_ArtifactMixin):
    """An immutable document snapshot with source-level provenance."""

    artifact_type: ClassVar[str] = "document"

    source_id: str
    source_url: str
    title: str
    retrieved_at: str
    content: str
    media_type: str = "text/plain"
    published_at: str | None = None
    author: str | None = None
    language: str | None = None
    license: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _text("source_id", self.source_id))
        object.__setattr__(self, "source_url", _uri("source_url", self.source_url))
        object.__setattr__(self, "title", _text("title", self.title))
        object.__setattr__(self, "retrieved_at", _timestamp("retrieved_at", self.retrieved_at))
        object.__setattr__(self, "content", _text("content", self.content, preserve=True))
        object.__setattr__(self, "media_type", _text("media_type", self.media_type).lower())
        object.__setattr__(
            self, "published_at", _timestamp("published_at", self.published_at, optional=True)
        )
        object.__setattr__(self, "author", _optional_text("author", self.author))
        object.__setattr__(self, "language", _optional_text("language", self.language))
        object.__setattr__(self, "license", _optional_text("license", self.license))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def _payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_url": self.source_url,
            "title": self.title,
            "retrieved_at": self.retrieved_at,
            "content": self.content,
            "content_sha256": self.content_sha256,
            "media_type": self.media_type,
            "published_at": self.published_at,
            "author": self.author,
            "language": self.language,
            "license": self.license,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class CodeArtifact(_ArtifactMixin):
    """Source code pinned to a repository revision and relative path."""

    artifact_type: ClassVar[str] = "code"

    source_id: str
    repository_url: str
    revision: str
    path: str
    retrieved_at: str
    content: str
    language: str | None = None
    license: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        path = _text("path", self.path).replace("\\", "/")
        parsed_path = PurePosixPath(path)
        if parsed_path.is_absolute() or ".." in parsed_path.parts or path.endswith("/"):
            raise ContractError("path must be a relative repository file path")
        normalised_path = str(parsed_path)
        if normalised_path in {"", "."}:
            raise ContractError("path must name a repository file")

        object.__setattr__(self, "source_id", _text("source_id", self.source_id))
        object.__setattr__(self, "repository_url", _uri("repository_url", self.repository_url))
        object.__setattr__(self, "revision", _text("revision", self.revision))
        object.__setattr__(self, "path", normalised_path)
        object.__setattr__(self, "retrieved_at", _timestamp("retrieved_at", self.retrieved_at))
        object.__setattr__(self, "content", _text("content", self.content, preserve=True))
        object.__setattr__(self, "language", _optional_text("language", self.language))
        object.__setattr__(self, "license", _optional_text("license", self.license))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def _payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "repository_url": self.repository_url,
            "revision": self.revision,
            "path": self.path,
            "retrieved_at": self.retrieved_at,
            "content": self.content,
            "content_sha256": self.content_sha256,
            "language": self.language,
            "license": self.license,
            "metadata": self.metadata,
        }


def _trade_records(value: Any) -> tuple[Mapping[str, JsonValue], ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ContractError("records must be a non-empty list")
    records: list[Mapping[str, JsonValue]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping):
            raise ContractError(f"records[{index}] must be a JSON object")
        record = dict(raw)
        record_id = _text(f"records[{index}].record_id", record.get("record_id"))
        if record_id in seen:
            raise ContractError(f"duplicate trade record_id: {record_id}")
        seen.add(record_id)
        record_type = _text(
            f"records[{index}].record_type", record.get("record_type")
        ).lower()
        if record_type not in TRADE_RECORD_TYPES:
            raise ContractError(
                f"records[{index}].record_type must be one of {sorted(TRADE_RECORD_TYPES)}"
            )
        occurred_at = _timestamp(
            f"records[{index}].occurred_at", record.get("occurred_at")
        )
        record["record_id"] = record_id
        record["record_type"] = record_type
        record["occurred_at"] = occurred_at
        frozen = _freeze_json(record, f"records[{index}]")
        assert isinstance(frozen, Mapping)
        records.append(frozen)
    records.sort(key=lambda item: (str(item["occurred_at"]), str(item["record_type"]), str(item["record_id"])))
    return tuple(records)


@dataclass(frozen=True, slots=True)
class TradeHistoryArtifact(_ArtifactMixin):
    """Normalized observed account events; no strategy inference is included."""

    artifact_type: ClassVar[str] = "trade_history"

    source_id: str
    source_url: str
    provider: str
    account_ref: str
    retrieved_at: str
    records: Sequence[Mapping[str, Any]]
    base_currency: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        records = _trade_records(self.records)
        start = _timestamp("period_start", self.period_start, optional=True)
        end = _timestamp("period_end", self.period_end, optional=True)
        record_times = [str(record["occurred_at"]) for record in records]
        start = start or min(record_times)
        end = end or max(record_times)
        if start > end:
            raise ContractError("period_start must not be after period_end")
        if min(record_times) < start or max(record_times) > end:
            raise ContractError("trade records must fall inside the declared period")

        currency = _optional_text("base_currency", self.base_currency)
        if currency is not None:
            currency = currency.upper()
            if not (3 <= len(currency) <= 12 and currency.isalnum()):
                raise ContractError("base_currency must be a 3-12 character code")

        object.__setattr__(self, "source_id", _text("source_id", self.source_id))
        object.__setattr__(self, "source_url", _uri("source_url", self.source_url))
        object.__setattr__(self, "provider", _text("provider", self.provider))
        object.__setattr__(self, "account_ref", _text("account_ref", self.account_ref))
        object.__setattr__(self, "retrieved_at", _timestamp("retrieved_at", self.retrieved_at))
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "base_currency", currency)
        object.__setattr__(self, "period_start", start)
        object.__setattr__(self, "period_end", end)
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    @property
    def records_sha256(self) -> str:
        return _sha256(self.records)

    def _payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_url": self.source_url,
            "provider": self.provider,
            "account_ref": self.account_ref,
            "retrieved_at": self.retrieved_at,
            "records": self.records,
            "records_sha256": self.records_sha256,
            "base_currency": self.base_currency,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "metadata": self.metadata,
        }


def _source_fingerprints(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ContractError("source_artifact_fingerprints must be a non-empty list")
    return tuple(sorted({_fingerprint(item, "source artifact fingerprint") for item in value}))


def _evidence(
    value: Any, source_fingerprints: tuple[str, ...]
) -> tuple[Mapping[str, JsonValue], ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ContractError("evidence must be a non-empty list")
    allowed = {"artifact_fingerprint", "quote", "locator", "note"}
    items: list[Mapping[str, JsonValue]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping):
            raise ContractError(f"evidence[{index}] must be a JSON object")
        unknown = set(raw) - allowed
        if unknown:
            raise ContractError(f"evidence[{index}] has unknown fields: {sorted(unknown)}")
        reference = _fingerprint(
            raw.get("artifact_fingerprint"), f"evidence[{index}].artifact_fingerprint"
        )
        if reference not in source_fingerprints:
            raise ContractError(f"evidence[{index}] references an undeclared source artifact")
        item: dict[str, JsonValue] = {
            "artifact_fingerprint": reference,
            "quote": _text(f"evidence[{index}].quote", raw.get("quote")),
        }
        if raw.get("locator") is not None:
            item["locator"] = _text(f"evidence[{index}].locator", raw["locator"])
        if raw.get("note") is not None:
            item["note"] = _text(f"evidence[{index}].note", raw["note"])
        items.append(MappingProxyType(item))
    items.sort(
        key=lambda item: (
            str(item["artifact_fingerprint"]),
            str(item.get("locator", "")),
            str(item["quote"]),
        )
    )
    return tuple(items)


@dataclass(frozen=True, slots=True)
class CandidateArtifact(_ArtifactMixin):
    """A sourced research candidate for Quantlab, not an executable strategy."""

    artifact_type: ClassVar[str] = "candidate"

    candidate_kind: str
    title: str
    summary: str
    source_artifact_fingerprints: Sequence[str]
    evidence: Sequence[Mapping[str, Any]]
    created_at: str
    tags: Sequence[str] = ()
    extractor: str = "deterministic"
    extractor_version: str = "1"
    confidence: float | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = _text("candidate_kind", self.candidate_kind).lower()
        if kind not in CANDIDATE_KINDS:
            raise ContractError(f"candidate_kind must be one of {sorted(CANDIDATE_KINDS)}")
        sources = _source_fingerprints(self.source_artifact_fingerprints)
        evidence = _evidence(self.evidence, sources)
        if isinstance(self.tags, str) or not isinstance(self.tags, (list, tuple)):
            raise ContractError("tags must be a list of strings")
        tags = tuple(sorted({_text("tag", tag) for tag in self.tags}))

        confidence = self.confidence
        if confidence is not None:
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
                raise ContractError("confidence must be a number between 0 and 1")
            confidence = float(confidence)
            if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
                raise ContractError("confidence must be a number between 0 and 1")

        object.__setattr__(self, "candidate_kind", kind)
        object.__setattr__(self, "title", _text("title", self.title))
        object.__setattr__(self, "summary", _text("summary", self.summary))
        object.__setattr__(self, "source_artifact_fingerprints", sources)
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "created_at", _timestamp("created_at", self.created_at))
        object.__setattr__(self, "tags", tags)
        object.__setattr__(self, "extractor", _text("extractor", self.extractor))
        object.__setattr__(
            self, "extractor_version", _text("extractor_version", self.extractor_version)
        )
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def _payload(self) -> dict[str, Any]:
        return {
            "candidate_kind": self.candidate_kind,
            "title": self.title,
            "summary": self.summary,
            "source_artifact_fingerprints": self.source_artifact_fingerprints,
            "evidence": self.evidence,
            "created_at": self.created_at,
            "tags": self.tags,
            "extractor": self.extractor,
            "extractor_version": self.extractor_version,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


Artifact: TypeAlias = DocumentArtifact | CodeArtifact | TradeHistoryArtifact | CandidateArtifact

_ARTIFACT_CLASSES: dict[str, type[Artifact]] = {
    DocumentArtifact.artifact_type: DocumentArtifact,
    CodeArtifact.artifact_type: CodeArtifact,
    TradeHistoryArtifact.artifact_type: TradeHistoryArtifact,
    CandidateArtifact.artifact_type: CandidateArtifact,
}


def artifact_from_dict(value: Mapping[str, Any]) -> Artifact:
    """Validate a strict wire envelope and return its typed artifact."""
    if not isinstance(value, Mapping):
        raise ContractError("artifact envelope must be a JSON object")
    expected_fields = {"schema_version", "artifact_type", "fingerprint", "payload"}
    if set(value) != expected_fields:
        missing = sorted(expected_fields - set(value))
        unknown = sorted(set(value) - expected_fields)
        raise ContractError(f"invalid envelope fields; missing={missing}, unknown={unknown}")
    if value["schema_version"] != SCHEMA_VERSION:
        raise ContractError(
            f"unsupported schema_version={value['schema_version']!r}; expected {SCHEMA_VERSION}"
        )
    artifact_type = _text("artifact_type", value["artifact_type"]).lower()
    artifact_class = _ARTIFACT_CLASSES.get(artifact_type)
    if artifact_class is None:
        raise ContractError(f"unknown artifact_type={artifact_type!r}")
    payload = value["payload"]
    if not isinstance(payload, Mapping):
        raise ContractError("payload must be a JSON object")
    payload = dict(payload)
    claimed_content_hash = payload.pop("content_sha256", None)
    claimed_records_hash = payload.pop("records_sha256", None)
    try:
        artifact = artifact_class(**payload)
    except TypeError as exc:
        raise ContractError(f"invalid {artifact_type} payload: {exc}") from exc
    if isinstance(artifact, (DocumentArtifact, CodeArtifact)):
        if claimed_content_hash is None:
            raise ContractError(f"{artifact_type} payload is missing content_sha256")
        if _fingerprint(claimed_content_hash, "content_sha256") != artifact.content_sha256:
            raise ContractError("content_sha256 does not match content")
    elif claimed_content_hash is not None:
        raise ContractError(f"{artifact_type} payload must not contain content_sha256")
    if isinstance(artifact, TradeHistoryArtifact):
        if claimed_records_hash is None:
            raise ContractError("trade_history payload is missing records_sha256")
        if _fingerprint(claimed_records_hash, "records_sha256") != artifact.records_sha256:
            raise ContractError("records_sha256 does not match records")
    elif claimed_records_hash is not None:
        raise ContractError(f"{artifact_type} payload must not contain records_sha256")
    claimed = _fingerprint(value["fingerprint"])
    if claimed != artifact.fingerprint:
        raise ContractError("artifact fingerprint does not match its payload")
    return artifact


def artifact_from_json(value: str) -> Artifact:
    """Parse and validate an artifact JSON envelope."""
    if not isinstance(value, str):
        raise ContractError("artifact JSON must be a string")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid artifact JSON: {exc}") from exc
    return artifact_from_dict(decoded)


def validate_artifact(value: Artifact | Mapping[str, Any] | str) -> Artifact:
    """Return a validated typed artifact from an object, envelope, or JSON string."""
    if isinstance(value, _ArtifactMixin):
        value.validate()
        return value
    if isinstance(value, str):
        return artifact_from_json(value)
    return artifact_from_dict(value)


__all__ = [
    "SCHEMA_VERSION",
    "ARTIFACT_TYPES",
    "CANDIDATE_KINDS",
    "TRADE_RECORD_TYPES",
    "ContractError",
    "DocumentArtifact",
    "CodeArtifact",
    "TradeHistoryArtifact",
    "CandidateArtifact",
    "Artifact",
    "artifact_from_dict",
    "artifact_from_json",
    "validate_artifact",
]
