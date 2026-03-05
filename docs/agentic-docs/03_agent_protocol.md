# Coding Agent Protocol

## Purpose
Standardize how coding agents execute feature work from design docs to reduce drift and scope creep.

## Agent Inputs (Per Iteration)
- `docs/phase1.md` (or applicable phase doc)
- `docs//docs/features/parsers//00_playbook.md`
- feature-local `01_rfc.md`, `02_user_stories.md`, `03_design.md`
- active PR task slice from feature `04_workplan.md`

## Agent Execution Rules
- Implement only in-scope PR tasks.
- Keep changes small and focused.
- Add/update tests for changed behavior.
- If design decisions change, update `03_design.md` and `04_workplan.md` in the same iteration.
- Do not bypass contracts in RFC.

## Agent Outputs (Per Iteration)
- code/docs limited to PR scope
- tests and results summary
- updated checkboxes/status in workplan
- explicit assumptions recorded when needed

## Review Rubric
- Contract compliance: does implementation match RFC?
- Behavior coverage: do tests prove acceptance criteria?
- Determinism: is stable output behavior preserved?
- Diff discipline: is scope bounded to planned slice?

## Escalation Conditions
Escalate to humans when:
- contract ambiguity blocks implementation
- invariants conflict across docs
- deterministic behavior cannot be guaranteed with existing interfaces
