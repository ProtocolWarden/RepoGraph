# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Shared RepoGraph exceptions."""


class RepoGraphConfigError(ValueError):
    """Raised when RepoGraph data is invalid."""


class AmbiguousAnchorError(RepoGraphConfigError):
    """Raised when anchor inference matches more than one registered manifest."""
