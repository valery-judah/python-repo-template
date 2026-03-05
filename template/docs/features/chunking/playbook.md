# Feature Workflow Playbook (Reusable)  
**Context:** Retrieval-phase features for a RAG assistant (starting with *segmentation*).  
**Goal:** A lightweight, repeatable workflow that (a) preserves design intent, (b) is friendly to a coding agent, and (c) enforces correctness via tests + quality gates.

---

## 0) Principles (the “non-negotiables”)
These are the invariants your feature workflows should preserve across the pipeline:

- **Stable identity:** segments/sections must have stable identifiers across re-runs when inputs and config are unchanged.
- **Anchorability:** every segment must be mappable back to source text deterministically (anchors + offsets).
- **Hierarchical integrity:** strict tree structure (single parent; acyclic), consistent ordering.
- **Determinism:** segmentation output is reproducible given the same inputs + configuration.

> The workflow below is shaped to protect these invariants through explicit contracts + snapshot tests.

---

## 1) Minimal artifact set (not overwhelming)
Keep the “docs/feature-folder” small, but structured enough to rehydrate the main logic months later.

### Required artifacts (5)
Inside `docs/<feature>/`:

1) **`00_context.md`**  
   - Where this feature sits in the pipeline  
   - Inputs/outputs at the boundary (schemas, ownership)  
   - Current behavior + known gaps + dependencies

Treat `00_context.md` as the feature "contract surface"

Make it contain only the information that must remain stable:

- **Pipeline placement**: module path + owner + upstream/downstream dependencies
- **Boundary contract**: input schema(s) and output schema(s)
- **Invariants**: determinism, hierarchy rules, required metadata
- **Golden examples**: small I/O examples that tests can consume
- **Test map**: which tests enforce which invariants

2) **`01_rfc.md`** 
   - Problem, scope/non-scope, success criteria, open decisions, rollout

3) **`02_user_stories.md`**
   - Acceptance criteria written as testable checks  
   - Quality gates (measurable thresholds) and what “pass” means

4) **`03_design.md`** *(most important for agent execution)*  
   - Contract freeze: fields, algorithms, edge-case policies  
   - Determinism rules and tie-breakers  
   - Data model and configuration schema

5) **`04_workplan.md`**  
   - PR-by-PR plan with checkboxes  
   - “Done means tests + docs updated” rule  
   - Explicit file/module targets

### Optional but recommended (2)
6) **`05_test_plan.md`**  
   - Test pyramid + golden corpora definition + CI gating matrix  
   - Snapshot update policy

7) **`06_rollout.md`**  
   - Shadow mode, offline eval, dual-index options, A/B, rollback criteria

> If you want to keep it even leaner: merge `05_test_plan.md` into the end of `03_design.md`, and merge `06_rollout.md` into `01_rfc.md`.

---

## 2) End-to-end workflow (design → implementation → verification)

### Step A — Contract freeze (before writing code)
**Objective:** Produce a stable contract the coding agent must implement against (no re-interpretation).

**Actions**
- Declare the segmentation module boundary:
  - **Inputs:** canonical text + structure tree + anchors (from upstream parsing/distillation)
  - **Outputs:** `SECTION` + `PASSAGE` nodes with required metadata
- Freeze required fields (minimum set):
  - `doc_id`, `doc_version_id`, `segment_id`, `segment_type`
  - `parent_id` (for `PASSAGE`)
  - `anchor` (or anchor-range), plus offsets into canonical text
  - `section_ordinal`, `passage_ordinal`
  - `token_count`, `metadata` (incl. special-type flags)
- Freeze deterministic ordering rules:
  - A single traversal order for sections (e.g., pre-order DFS)
  - Stable tie-breakers (e.g., path, ordinal, offset)
- Freeze ID strategy:
  - Hash stable inputs: doc identifiers + section path + anchor/span signature (+ config hash)
- Record all decisions in `03_design.md` under “Decisions & tie-breakers”.

**Artifact updates**
- `03_design.md`: add a “Frozen Contract” section.
- `02_user_stories.md`: ensure every acceptance criterion maps to a test.

**Exit gate**
- A reviewer can answer “what is the contract?” without reading code.

---

### Step B — Design decomposition into deterministic subroutines
**Objective:** Break policy into small, testable functions.

Recommended subcomponents for segmentation (adaptable to other features):
1) `build_section_tree(structure_tree) -> sections`
2) `collect_blocks(section) -> ordered blocks` (with anchors/ranges)
3) `chunk_blocks_into_passages(blocks, cfg, tokenizer)`
4) `split_special_table(block)` (atomic vs row-group; header repetition)
5) `split_special_code(block)` (atomic vs heuristic splitting)
6) `merge_too_small_passages(passages, cfg)`
7) `apply_overlap(passages, cfg)` (with provenance metadata)
8) `assign_ordinals_offsets(passages)` (deterministic)
9) `make_segment_ids(nodes, cfg_hash)`

**Design emphasis**
- Every step must be **pure** (no hidden state, no randomness).
- Every step must define:
  - inputs/outputs
  - ordering guarantees
  - tie-breakers for ambiguous cases

**Artifact updates**
- `03_design.md`: include “Algorithm Overview” + “Edge-Case Policy”.
- `04_workplan.md`: create one PR task group per subroutine.

---

### Step C — Implementation in small PRs (agent-friendly)
**Objective:** Reduce blast radius; keep reviews + tests aligned.

A practical PR sequence for segmentation:
1) **Scaffolding + schema**  
   Types/data classes, config schema, tokenizer abstraction (no algorithm changes).
2) **Section tree + strict hierarchy checks**  
   Build `SECTION` nodes; enforce strict tree constraints.
3) **Baseline chunker**  
   Paragraph/list boundary chunking; token accounting; max/min token logic.
4) **Anchors + offsets**  
   Compute offsets; ensure anchor-to-text mapping is deterministic.
5) **Tables**  
   Atomic then row-group splitting; header repetition logic.
6) **Code blocks**  
   Atomic then heuristic splitting (line/function boundary heuristics).
7) **Overlap + provenance**  
   Overlap windows; provenance metadata (“overlap_from”, “overlap_to”, etc.).
8) **Determinism snapshot + quality report**  
   Golden corpus snapshot; per-doc quality report output.
9) **Observability**  
   Metrics/events: segment counts, distributions, split reasons, anomalies.

**Agent instruction pattern (per PR)**
- “Implement *only* items from this PR task list; do not broaden scope.”
- “Add/extend tests for each new behavior.”
- “Update design/workplan docs when decisions change.”

---

### Step D — Tests + quality gates (CI is the enforcement layer)
**Objective:** Prevent regressions before embedding/indexing.

#### Test pyramid
1) **Unit tests (fast, many)**
- Boundary selection (paragraph/list/headings)
- Table splitting rules + header repetition
- Code splitting rules
- Overlap + merge-small behavior
- ID generation and ordering determinism

2) **Property tests (structural invariants)**
- No cycles; exactly one parent for `PASSAGE`
- No empty passage text
- Non-negative token counts; monotonic ordinals within section
- Anchor/offset range validity (within canonical text bounds)
- Determinism: same inputs → identical outputs

3) **Golden snapshot tests (high value, fewer)**
- A curated corpus with stable expected output:
  - ordered list of nodes with: `segment_id`, `parent_id`, ordinals, offsets, anchor signature, text hash, token_count, special flags
- Snapshot update rule:
  - Changes must be intentional + documented (include reason, expected impact).

4) **Anchor-resolution tests**
- Sample segments (or all for small docs): ensure anchor/offset extracts the exact segment text.

#### CI gating matrix (recommended minimum)
Fail the build if:
- Any segment has empty text
- Required fields missing
- Hierarchy invalid (cycle, multiple parents, orphan PASSAGE)
- Offsets out of bounds
- Determinism snapshot mismatch (unless explicitly updated)
- Table split output lacks header repetition (when splitting enabled)
- Mid-sentence split rate exceeds threshold (for non-special content)

#### Quality report artifact (per run)
Produce a machine-readable report (JSON or CSV) with:
- token_count histograms (per segment type)
- split-reason counts (paragraph, heading, table, code, max_tokens, merge_small, overlap)
- special segment counts (tables, code)
- anomaly counts (very small segments, high overlap, missing anchors)
- determinism hash (config hash + pipeline version hash)

This report becomes your “regression radar” in PR review.

---

### Step E — Integration and rollout (safe deployment)
**Objective:** Deploy without destabilizing retrieval quality.

Recommended rollout ladder:
1) **Shadow mode**
- Generate segments + metrics, but do not use for retrieval.
2) **Offline evaluation**
- Compare retrieval metrics vs baseline (Recall@k, MRR, nDCG, evidence coverage).
3) **Optional dual-index**
- Index baseline + new segmentation simultaneously for controlled comparison.
4) **A/B rollout**
- Gradually increase traffic; define rollback triggers (e.g., retrieval KPI regressions).

---

## 3) Definition of Done (DoD) checklist
A feature is “done” when:

**Design**
- [ ] Contract freeze documented (I/O + required fields + invariants)
- [ ] Tie-breakers and determinism rules documented
- [ ] Config schema documented, with defaults and compatibility notes
- [ ] Edge-case policy captured (tables, code, too-small segments, overlap)

**Implementation**
- [ ] Subroutines implemented with minimal coupling
- [ ] All PRs scoped and merged in planned order (or plan updated)

**Tests & gates**
- [ ] Unit tests cover each subroutine
- [ ] Property tests enforce invariants
- [ ] Golden snapshot corpus exists and passes
- [ ] Anchor-resolution tests pass
- [ ] CI gates enforce quality thresholds and determinism

**Operational**
- [ ] Quality report produced and reviewed
- [ ] Rollout plan documented with rollback criteria

---

## 4) Coding-agent workflow (repeatable protocol)
Use a predictable “agent contract” so results are consistent across features.

### Inputs to the agent (each iteration)
- `phase1.md` (pipeline overview + invariants)
- `docs/<feature>/01_rfc.md`
- `docs/<feature>/02_user_stories.md`
- `docs/<feature>/03_design.md`
- The current PR task list from `04_workplan.md`

### Required outputs from the agent (each iteration)
- Code changes limited to the PR scope
- Tests added/updated
- Quality report regenerated (if it’s part of the scope)
- `03_design.md` updated if any decision changed
- `04_workplan.md` checkboxes updated

### Review rubric (quick)
- Does code match the frozen contract?
- Do tests cover new behavior and invariants?
- Does snapshot change have a documented reason?
- Do metrics/report show expected distributions and no new anomalies?

---

## 5) Templates (copy/paste)

### `03_design.md` skeleton (short)
```md
# Design: <Feature>

## Frozen Contract
- Inputs:
- Outputs:
- Required fields:
- Invariants:
- Deterministic ordering rules:
- ID strategy:
- Config schema + defaults:

## Algorithm Overview
- Step 1:
- Step 2:
- …

## Edge-case Policy
- Tables:
- Code:
- Too-small segments:
- Overlap:
- Missing anchors / malformed structure:

## Decisions & Tie-breakers
- Decision 1:
- Decision 2:
```

### `04_workplan.md` skeleton (PR-driven)
```md
# Workplan: <Feature>

## PR1: Scaffolding + schema
- [ ] Task …
- [ ] Tests …
- [ ] Docs updates …

## PR2: Section tree + hierarchy checks
- [ ] Task …
- [ ] Tests …

## PR3: Chunker baseline
- [ ] Task …
- [ ] Tests …

## PR4: Anchors + offsets
- [ ] Task …
- [ ] Tests …

## PR5+: Special cases + determinism + reports
- [ ] …
```

### `05_test_plan.md` skeleton (minimal)
```md
# Test Plan: <Feature>

## Golden corpora
- corpus_a:
- corpus_b:

## Unit tests
- …

## Property tests
- …

## Snapshot tests
- fields included:
- snapshot update policy:

## CI gates
- must-pass checks:
- thresholds:
```

---

## 6) Practical notes for segmentation specifically
- Prefer “structure-first”: build `SECTION` nodes from structure tree, then derive `PASSAGE` nodes.
- Make special handling explicit and testable:
  - tables: atomic vs split-by-row-group; repeat header
  - code: atomic vs heuristic splitting by logical boundaries
- Persist enough metadata to debug retrieval results:
  - ordinals, offsets, section path, special-type flags, split reason
- Keep configuration captured and hashed into determinism identity.