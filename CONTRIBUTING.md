# Contributing to RepoGraph

RepoGraph is the shared graph-semantics library for the platform. Changes here
affect ontology, topology, projection/redaction, boundary artifacts, and
shared topography definitions.

## Before You Start

- Check open issues to avoid duplicate work
- For semantic changes, open an issue first to discuss the model impact
- All contributions must pass the test suite before merging

## Development Setup

```bash
git clone https://github.com/ProtocolWarden/RepoGraph.git
cd RepoGraph
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Running Tests

```bash
python -m pytest
```

## Project Structure

```text
src/repograph/
  ontology/     # identity, visibility, disclosure, and validation models
  topology/     # edge vocabulary, graph instance, and validation models
  projection/   # redaction rules, boundary artifacts, and validation
  topography/   # shared topography definitions
```

## Architectural Constraints

RepoGraph is a **library**. It holds shared semantics and validation. It must
not:

- define private graph data
- publish public graph instances
- orchestrate execution or scheduling
- own deployment overlays
- own consumer-specific policies

## Pull Requests

- Keep PRs focused
- Add tests for ontology, topology, projection, or boundary changes
- Update `README.md` if the public model or verification flow changes

## Code of Conduct

This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).
