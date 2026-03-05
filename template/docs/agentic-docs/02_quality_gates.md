# Quality Gates (Reusable)

## Minimum Gate Categories
1. Contract correctness
2. Structural invariants
3. Determinism
4. Edge-case behavior
5. Regression visibility

## Required Checks (Baseline)
- Required contract fields present in produced artifacts.
- Structural constraints hold (e.g., no cycles/orphans where hierarchy applies).
- Deterministic reruns produce identical outputs under fixed inputs/config.
- Anchor/range resolvability checks pass where provenance is required.
- Golden snapshot tests pass or include explicit reviewed update rationale.

## CI Failure Conditions (Recommended)
- Missing required fields.
- Broken hierarchy constraints.
- Invalid ranges/offsets.
- Empty derived artifacts where non-empty is required.
- Snapshot drift without approved update.

## Reporting
Each feature should produce a machine-readable quality report (JSON/CSV) with:
- counts by artifact type
- anomaly counts
- determinism hash/config hash
- quality-threshold pass/fail indicators

## Change Management
If gates change:
- update feature RFC success criteria
- update test plan and workplan references
- document rationale in changelog/PR notes
