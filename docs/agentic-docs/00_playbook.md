# Agentic Feature Playbook

## Purpose
Provide one reusable workflow to design, implement, and validate future pipeline features with deterministic behavior and explicit contracts.

## Non-negotiables
- Stable identity for produced artifacts when inputs/config are unchanged.
- Anchorability/provenance from derived artifacts back to source representation.
- Hierarchical integrity where parent/child structures exist.
- Determinism for identical inputs, code version, and config.

## Standard Feature Workflow
1. Define boundaries in `00_context.md`.
2. Freeze contract and scope in `01_rfc.md`.
3. Define testable acceptance checks in `02_user_stories.md`.
4. Specify deterministic implementation design in `03_design.md`.
5. Plan PR-sequenced execution in `04_workplan.md`.
6. Add optional `05_test_plan.md` and `06_rollout.md` when feature risk warrants.

## Required Artifact Set per Feature
- `00_context.md`
- `01_rfc.md`
- `02_user_stories.md`
- `03_design.md`
- `04_workplan.md`

## Optional Artifacts
- `05_test_plan.md` for high-risk, high-complexity, or high-regression-surface features.
- `06_rollout.md` for staged rollout, shadow mode, or A/B deployment plans.

## Directory Convention
- Shared rules and templates live under `docs//docs/features/parsers//`.
- Feature docs live under `docs//docs/features/parsers/ature-name>/`.
- Existing domain docs (e.g. `docs/parsers/`) may remain as canonical docs during migration.

## Definition of Done (Documentation)
- Feature artifact set exists and is internally consistent.
- `01_rfc.md` is authoritative for contract and invariants.
- Every acceptance criterion maps to tests/workplan.
- Workplan includes explicit exit criteria and required checks.
