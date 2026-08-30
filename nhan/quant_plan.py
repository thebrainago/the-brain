# -*- coding: utf-8 -*-
"""Immutable preregistration contract for the two Quantlab research lanes.

``QuantPlan`` is deliberately narrower than a generic research note.  It pins
the strategy implementation and parameters, the exact applicability scope,
the search budget, the data/cost evidence, and the decision rule before a
confirmation window is evaluated.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias


SCHEMA_VERSION = 1
LANES = frozenset({"candidate_validation", "autonomous_discovery"})
CONFIRMATION_STATUSES = frozenset({"exposed_legacy", "forward_only", "clean_unseen"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

JsonValue: TypeAlias = (
    None | bool | int | float | str | tuple["JsonValue", ...] | Mapping[str, "JsonValue"]
)


class QuantPlanError(ValueError):
    """The preregistration plan is incomplete, ambiguous, or has been altered."""


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QuantPlanError(f"{name} must be a non-empty string")
    return value.strip()


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise QuantPlanError(f"{name} must be a positive integer")
    return value


def _finite(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QuantPlanError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise QuantPlanError(f"{name} must be a finite number")
    return number


def _sha256_text(name: str, value: Any) -> str:
    value = _text(name, value).lower()
    if not _SHA256_RE.fullmatch(value):
        raise QuantPlanError(f"{name} must be a SHA-256 hex digest")
    return value


def _freeze(value: Any, path: str) -> JsonValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise QuantPlanError(f"{path} contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise QuantPlanError(f"{path} keys must be strings")
        return MappingProxyType(
            {key: _freeze(value[key], f"{path}.{key}") for key in sorted(value)}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, f"{path}[]") for item in value)
    raise QuantPlanError(f"{path} contains unsupported type {type(value).__name__}")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            _thaw(value), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise QuantPlanError(f"value is not canonical JSON: {exc}") from exc


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _strict_object(name: str, value: Any, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise QuantPlanError(f"{name} must be an object")
    unknown = set(value) - fields
    missing = fields - set(value)
    if missing or unknown:
        raise QuantPlanError(
            f"{name} fields invalid; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    return dict(value)


def _string_list(name: str, value: Any) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, (list, tuple)) or not value:
        raise QuantPlanError(f"{name} must be a non-empty list of strings")
    result = tuple(sorted({_text(f"{name}[]", item).upper() for item in value}))
    if not result:
        raise QuantPlanError(f"{name} must not be empty")
    return result


def _window(name: str, value: Any) -> Mapping[str, JsonValue]:
    raw = _strict_object(name, value, {"start", "end"})
    start = _text(f"{name}.start", raw["start"])
    end = _text(f"{name}.end", raw["end"])
    if start > end:
        raise QuantPlanError(f"{name}.start must not be after end")
    return MappingProxyType({"end": end, "start": start})


@dataclass(frozen=True, slots=True)
class QuantPlan:
    """A content-addressed, strict, immutable research plan."""

    lane: str
    origin: Mapping[str, JsonValue]
    strategy: Mapping[str, JsonValue]
    scope: Mapping[str, JsonValue]
    search: Mapping[str, JsonValue]
    evidence: Mapping[str, JsonValue]
    decision_rule: Mapping[str, JsonValue]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise QuantPlanError(
                f"unsupported schema_version={self.schema_version}; expected {SCHEMA_VERSION}"
            )

        lane = _text("lane", self.lane).lower()
        if lane not in LANES:
            raise QuantPlanError(f"lane must be one of {sorted(LANES)}")

        origin = _strict_object("origin", self.origin, {"kind", "reference", "producer"})
        origin = MappingProxyType({
            "kind": _text("origin.kind", origin["kind"]),
            "producer": _text("origin.producer", origin["producer"]),
            "reference": _text("origin.reference", origin["reference"]),
        })

        strategy = _strict_object(
            "strategy", self.strategy,
            {"template", "template_hash", "parameters", "parameters_hash", "strategy_hash"},
        )
        parameters = _freeze(strategy["parameters"], "strategy.parameters")
        if not isinstance(parameters, Mapping):
            raise QuantPlanError("strategy.parameters must be an object")
        template = _text("strategy.template", strategy["template"])
        template_hash = _sha256_text("strategy.template_hash", strategy["template_hash"])
        parameters_hash = _sha256_text("strategy.parameters_hash", strategy["parameters_hash"])
        if parameters_hash != sha256_json(parameters):
            raise QuantPlanError("strategy.parameters_hash does not match frozen parameters")
        expected_strategy_hash = sha256_json({
            "parameters_hash": parameters_hash,
            "template": template,
            "template_hash": template_hash,
        })
        strategy_hash = _sha256_text("strategy.strategy_hash", strategy["strategy_hash"])
        if strategy_hash != expected_strategy_hash:
            raise QuantPlanError("strategy.strategy_hash does not match template and parameters")
        strategy = MappingProxyType({
            "parameters": parameters,
            "parameters_hash": parameters_hash,
            "strategy_hash": strategy_hash,
            "template": template,
            "template_hash": template_hash,
        })

        scope = _strict_object("scope", self.scope, {"assets", "timeframes", "applicability"})
        assets = _string_list("scope.assets", scope["assets"])
        timeframes = _string_list("scope.timeframes", scope["timeframes"])
        applicability = _freeze(scope["applicability"], "scope.applicability")
        if not isinstance(applicability, Mapping):
            raise QuantPlanError("scope.applicability must be an object")
        scope = MappingProxyType({
            "applicability": applicability,
            "assets": assets,
            "timeframes": timeframes,
        })

        search = _strict_object("search", self.search, {"batch_id", "family", "max_trials"})
        max_trials = _positive_int("search.max_trials", search["max_trials"])
        if len(assets) * len(timeframes) > max_trials:
            raise QuantPlanError("scope cross-product exceeds search.max_trials")
        search = MappingProxyType({
            "batch_id": _text("search.batch_id", search["batch_id"]),
            "family": _text("search.family", search["family"]),
            "max_trials": max_trials,
        })

        evidence = _strict_object(
            "evidence", self.evidence,
            {"data_release_id", "train_window", "confirmation_window",
             "cost_model_generation", "cost_snapshot_id", "confirmation_status"},
        )
        confirmation_status = _text(
            "evidence.confirmation_status", evidence["confirmation_status"]
        ).lower()
        if confirmation_status not in CONFIRMATION_STATUSES:
            raise QuantPlanError(
                "evidence.confirmation_status must be one of "
                f"{sorted(CONFIRMATION_STATUSES)}"
            )
        train_window = _window("evidence.train_window", evidence["train_window"])
        confirmation_window = _window(
            "evidence.confirmation_window", evidence["confirmation_window"]
        )
        if str(train_window["end"]) >= str(confirmation_window["start"]):
            raise QuantPlanError("train and confirmation windows must not overlap")
        evidence = MappingProxyType({
            "confirmation_status": confirmation_status,
            "confirmation_window": confirmation_window,
            "cost_model_generation": _positive_int(
                "evidence.cost_model_generation", evidence["cost_model_generation"]
            ),
            "cost_snapshot_id": _sha256_text(
                "evidence.cost_snapshot_id", evidence["cost_snapshot_id"]
            ),
            "data_release_id": _sha256_text(
                "evidence.data_release_id", evidence["data_release_id"]
            ),
            "train_window": train_window,
        })

        decision = _strict_object(
            "decision_rule", self.decision_rule,
            {"generation", "primary_p", "primary_effect", "min_trades"},
        )
        primary_p = _strict_object(
            "decision_rule.primary_p", decision["primary_p"], {"metric", "maximum"}
        )
        p_max = _finite("decision_rule.primary_p.maximum", primary_p["maximum"])
        if not 0.0 < p_max <= 1.0:
            raise QuantPlanError("decision_rule.primary_p.maximum must be in (0, 1]")
        primary_effect = _strict_object(
            "decision_rule.primary_effect", decision["primary_effect"],
            {"metric", "minimum", "unit"},
        )
        decision = MappingProxyType({
            "generation": _positive_int("decision_rule.generation", decision["generation"]),
            "min_trades": _positive_int("decision_rule.min_trades", decision["min_trades"]),
            "primary_effect": MappingProxyType({
                "metric": _text(
                    "decision_rule.primary_effect.metric", primary_effect["metric"]
                ),
                "minimum": _finite(
                    "decision_rule.primary_effect.minimum", primary_effect["minimum"]
                ),
                "unit": _text("decision_rule.primary_effect.unit", primary_effect["unit"]),
            }),
            "primary_p": MappingProxyType({
                "maximum": p_max,
                "metric": _text("decision_rule.primary_p.metric", primary_p["metric"]),
            }),
        })

        object.__setattr__(self, "lane", lane)
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "strategy", strategy)
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "search", search)
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "decision_rule", decision)

    @property
    def plan_hash(self) -> str:
        return sha256_json(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        value = {
            "schema_version": self.schema_version,
            "lane": self.lane,
            "origin": _thaw(self.origin),
            "strategy": _thaw(self.strategy),
            "scope": _thaw(self.scope),
            "search": _thaw(self.search),
            "evidence": _thaw(self.evidence),
            "decision_rule": _thaw(self.decision_rule),
        }
        if include_hash:
            value["plan_hash"] = self.plan_hash
        return value

    def to_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "QuantPlan":
        if not isinstance(value, Mapping):
            raise QuantPlanError("QuantPlan must be an object")
        expected = {
            "schema_version", "lane", "origin", "strategy", "scope",
            "search", "evidence", "decision_rule", "plan_hash",
        }
        if set(value) != expected:
            raise QuantPlanError(
                f"QuantPlan fields invalid; missing={sorted(expected - set(value))}, "
                f"unknown={sorted(set(value) - expected)}"
            )
        plan = cls(
            schema_version=value["schema_version"], lane=value["lane"],
            origin=value["origin"], strategy=value["strategy"], scope=value["scope"],
            search=value["search"], evidence=value["evidence"],
            decision_rule=value["decision_rule"],
        )
        claimed = _sha256_text("plan_hash", value["plan_hash"])
        if claimed != plan.plan_hash:
            raise QuantPlanError("plan_hash does not match plan contents")
        return plan

    @classmethod
    def from_json(cls, value: str) -> "QuantPlan":
        if not isinstance(value, str):
            raise QuantPlanError("QuantPlan JSON must be a string")
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise QuantPlanError(f"invalid QuantPlan JSON: {exc}") from exc
        return cls.from_dict(decoded)


def strategy_spec(template: str, template_hash: str,
                  parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Build the self-checking strategy section from frozen inputs."""
    template = _text("strategy.template", template)
    template_hash = _sha256_text("strategy.template_hash", template_hash)
    parameters = _freeze(parameters, "strategy.parameters")
    if not isinstance(parameters, Mapping):
        raise QuantPlanError("strategy.parameters must be an object")
    parameters_hash = sha256_json(parameters)
    return {
        "template": template,
        "template_hash": template_hash,
        "parameters": _thaw(parameters),
        "parameters_hash": parameters_hash,
        "strategy_hash": sha256_json({
            "parameters_hash": parameters_hash,
            "template": template,
            "template_hash": template_hash,
        }),
    }


__all__ = [
    "SCHEMA_VERSION", "LANES", "CONFIRMATION_STATUSES", "QuantPlanError",
    "QuantPlan", "canonical_json", "sha256_json", "strategy_spec",
]
