# Topography

Topography is reserved for environment-specific placement definitions such as
local paths, ports, compose overlays, and machine-specific runtime bindings.

`RepoGraph` does not implement a heavy shared topography model yet. This module
exists so deployment consumers can converge on shared definitions later without
mixing deployment state into ontology, topology, or projection semantics.
