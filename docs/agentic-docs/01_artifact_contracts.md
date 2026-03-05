# Artifact Contracts

## Contract Authority
For each feature folder, `01_rfc.md` is the single normative source of truth for:
- input/output contracts
- required fields
- invariants
- deterministic ordering rules
- identity/anchor strategy

Other artifacts must reference RFC sections instead of redefining contracts.

## `00_context.md` Contract
Must include:
- pipeline/module placement
- upstream/downstream ownership boundaries
- invariant summary (high-level only)
- one compact golden example
- verification map (contract area -> test family)

Must not include full schema duplication.

## `01_rfc.md` Contract
Must include:
- problem and scope
- normative input/output schemas
- required fields
- invariants and deterministic ordering
- success criteria thresholds
- non-goals
- open decisions
- change-control policy

## `02_user_stories.md` Contract
Must include:
- personas and outcomes
- Given/When/Then acceptance criteria
- explicit edge/failure scenarios
- traceability matrix: AC/ES -> RFC section -> test category
- measurable quality gates

Must not include implementation-library decisions.

## `03_design.md` Contract
Must include:
- implementation goals linked to RFC
- deterministic data flow
- algorithm decomposition and tie-breakers
- edge-case handling policy
- observability events and payload fields
- complexity/limitations and deferred items

Must not redefine normative schema contracts.

## `04_workplan.md` Contract
Must include:
- milestone mapping
- dependency order
- PR-by-PR tasks with:
  - scope
  - touched modules
  - acceptance checks
  - required tests
  - rollback/mitigation notes
  - exit criteria
- command checklist and done criteria

## Optional Contracts
### `05_test_plan.md`
- test pyramid
- fixture and snapshot policy
- CI gates and thresholds
- report/metrics format

### `06_rollout.md`
- rollout stages
- success metrics
- abort/rollback triggers
- ownership and communication plan
