# Capability Plane Charter

Status: active · Schema: `capabilities` @ 1.0.0 · Module: `src/repograph/capabilities/`

## What the capability plane is

The capability plane answers one question: **what can the fleet do, who owns it,
what does it need, how risky is it, and where should it run?** A capability is a
named, ownable *action* — `repo_health_audit`, `board_unblock`, `session_gc` —
modelled as a first-class graph **node** with typed **edges**
(`owns` / `targets` / `executes` / `requires` / `validates` / `produces`).

It exists to make an already-running fleet **legible**, not to add a runtime. The
first consumer is an operator or agent reading the registry into context at
session start. RepoGraph owns the *language*; PlatformManifest authors the
*instances*; Custodian checks them against *reality* (CAP1). The graph is the
truth — the flat authoring fields are sugar that compile to nodes and edges.

## What it is NOT — the ownership boundary (the point of this charter)

Capabilities are a **fleet-level** plane. They are deliberately **not** owned by,
and must **not** be migrated into, any single subsystem:

- **Not topology.** A capability is not a `RepoNode` and does not belong to the
  repo-graph. Repos *host* and *own* capabilities (via the `owns` edge); they do
  not contain them. The capability plane sits beside topology, not inside it.
- **Not execution.** A capability is not a TeamExecutor lane, a CoreRunner job, or
  an OperationsCenter task. `executes` / `requires` edges and `preferred_lane`
  *reference* those subsystems; they do not move the capability into them.
  `routing.preferred_lane` is descriptive metadata in v1, not a dispatch hook.
- **Not a behaviour catalogue per repo.** There are no per-behaviour `SKILL.md`
  files and no "harness runtime" repo. The runtime already exists; this plane
  describes it.

Concretely: do not relocate `src/repograph/capabilities/` into OperationsCenter,
SwitchBoard, TeamExecutor, or CoreRunner. Those are **consumers** of the plane
(out of scope for v1), not its home. Centralising the definition is what keeps
"who owns this action?" answerable in one place.

## Load-bearing invariants

1. **Exactly one `owns` edge per capability.** Accountability is singular;
   participation (`executes` / `requires` / `validates`) is plural. This edge is
   the answer to "does this action belong in repo X?".
2. **`invocation.ref` must resolve in the owning repo.** RepoGraph keeps the ref
   opaque (it never imports the fleet); Custodian's **CAP1** detector binds it to
   real code in the owning repo. Read-models rot silently — this check is what
   stops the registry from drifting into fiction.
3. **`target_scope` trichotomy.** `repo` (resolves an id) · `repo_set` (validates
   a selector, does **not** expand membership) · `fleet` (no id/selector).
4. **Risk gates a lane.** Risk ≥ `mutates_fleet` requires an explicit
   `preferred_lane`. Unknown enums fail closed.

## Layer boundary

| Layer | Repo | Responsibility |
|-------|------|----------------|
| Language | RepoGraph | capability nodes/edges, schema, validation, projection — **import-free of the fleet** |
| Instances | PlatformManifest | authored capabilities + read-model CLI |
| Reality check | Custodian | CAP1 — `invocation.ref` resolves in the owning repo |
| Consumers (later) | OC / SwitchBoard / CoreRunner | read the registry; **not** owners — see above |

v1 is a **read-model**: no mutation API, no dispatch. Consumers and any
write-path are explicitly future work.
