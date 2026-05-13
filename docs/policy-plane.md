# RepoGraph Policy Plane

RepoGraph semantics are not policy. Policy != semantics. Policy is the layer
that constrains how the graph may be used without redefining the graph
language itself.

## What belongs here

- allowed visibility transitions
- restricted edge categories
- deployment restrictions
- organization-level governance constraints

## What does not belong here

- ontology enums
- topology enums
- projection/redaction semantics
- boundary artifact schema
- private graph truth

## Operating rule

Policy must stay adjacent to RepoGraph semantics, not buried inside random
configuration. If a rule changes graph language, it belongs in RepoGraph
schema/version governance instead of policy.

## Current posture

RepoGraph keeps policy explicit and separate, but the semantic source of truth
remains the schema, topology, projection, and boundary layers.
