# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Schema validation helpers."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from ..errors import RepoGraphConfigError
from .compatibility import ensure_supported_schema_version
from .kinds import SchemaKind


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_artifact_hash(payload: dict[str, Any]) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def validate_schema_document(
    payload: dict[str, Any],
    *,
    expected_kind: SchemaKind,
) -> None:
    raw_kind = payload.get("schema_kind")
    raw_version = payload.get("schema_version")
    if raw_kind != expected_kind.value:
        raise RepoGraphConfigError(
            f"expected schema_kind={expected_kind.value!r}, got {raw_kind!r}"
        )
    if not isinstance(raw_version, str) or not raw_version.strip():
        raise RepoGraphConfigError("schema_version must be a non-empty string")
    ensure_supported_schema_version(expected_kind, raw_version)


def validate_boundary_artifact_payload(
    payload: dict[str, Any],
    *,
    signature_verifier: Any | None = None,
) -> None:
    validate_schema_document(payload, expected_kind=SchemaKind.BOUNDARY_ARTIFACT)
    if payload.get("artifact_kind") != "boundary_disclosure_artifact":
        raise RepoGraphConfigError(
            "artifact_kind must be 'boundary_disclosure_artifact'"
        )
    required = ("source_graph_id", "generated_at", "forbidden_names")
    missing = [name for name in required if name not in payload or payload[name] in (None, "")]
    if missing:
        raise RepoGraphConfigError(
            f"boundary artifact missing required field(s): {missing}"
        )
    if payload.get("artifact_hash"):
        expected = payload["artifact_hash"]
        material = {
            key: value
            for key, value in payload.items()
            if key not in {"artifact_hash", "signature", "signed_at", "public_projection_redaction_report"}
        }
        observed = compute_artifact_hash(material)
        if expected != observed:
            raise RepoGraphConfigError(
                f"boundary artifact hash mismatch: expected {expected!r}, observed {observed!r}"
            )
    signature = payload.get("signature")
    if signature:
        if signature_verifier is None:
            raise RepoGraphConfigError(
                "boundary artifact signature present but no verifier is available"
            )
        if not signature_verifier(payload):
            raise RepoGraphConfigError("boundary artifact signature verification failed")
