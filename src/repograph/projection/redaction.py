# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Redaction helpers."""

from __future__ import annotations


def public_name(*, canonical_name: str, public_alias: str | None) -> str:
    return public_alias or canonical_name
