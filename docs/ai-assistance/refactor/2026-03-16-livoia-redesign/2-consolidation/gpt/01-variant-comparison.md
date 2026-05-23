# Variant Comparison

## Inputs reviewed

- `2026-03-16-prod-redesign-claude` (10 documents)
- `2026-03-16-prod-redesign-gemini` (3 documents)
- `2026-03-16-prod-redesign-gpt` (9 documents)
- Current implementation checkpoints in:
  - `src/livoia_web/app.py`
  - `src/livoia_web/adapters/bedrock_adapter.py`
  - `src/livoia_web/static/js/app.js`
  - `src/livoia/modules/speech_caller.py`
  - `src/livoia/clients/speech/bedrock_sonic.py`

## Executive comparison

| Dimension | Claude variant | Gemini variant | GPT variant |
|---|---|---|---|
| Scope clarity | Strong parity focus, but still references image flow in protocol docs | Broad and future-heavy; stage boundaries not strict | Strongest scope boundary with explicit stage 1 non-goals |
| Architecture precision | Detailed and implementable, mostly concrete | Conceptual; less actionable at file/module level | Concrete module boundaries, provider-neutral contracts |
| Migration practicality | Very strong phased migration plan | Limited migration detail | Strong file-level migration inventory (keep/adapt/drop) |
| Risk of over-building | Medium (keeps many details, some future features mixed in) | High (introduces orchestrator/SSE complexity early) | Low-medium (modular but still introduces new package naming and layers) |
| Fit with current code | High (maps from current files clearly) | Medium-low (assumes broader re-platforming) | High (grounded in current behavior and explicit exclusions) |
| CI/CD alignment | Strong, closest to current operational baseline | Good intent, but includes some mismatches (e.g., portaudio assumptions) | Strong baseline with pragmatic adaptation guidance |
| Documentation completeness | Very high detail | Lower detail | High detail, focused on deliverable artifacts |

## Variant-by-variant strengths and concerns

## 1) Claude variant

### Pros

- Most complete implementation detail across backend, frontend, tools, config, CI/CD, docs, and phased migration.
- Strong direct mapping from current PoC files to target files.
- Good reduction mindset: remove unused `livoia` components not needed for web stage.
- Clear provider abstraction and explicit session flow.

### Cons

- Includes image/camera protocol details in some sections, which conflicts with the desired stage 1 narrowing.
- Introduces a unified provider websocket route (`/ws/{provider}/...`) even though current frontend already supports provider-based routing via a provider segment; this is workable but not required for production parity.
- Some sections are verbose enough that teams may treat design as implementation freeze instead of guardrails.

### Main risk

- Scope drift from strict stage 1 if image/tool-future concerns are not explicitly deferred.

## 2) Gemini variant

### Pros

- Strong forward-looking treatment for asynchronous long-running tools and orchestrator integration.
- Clean high-level decomposition (`app/core/providers`) and event-stream thinking.
- Solid operational instincts (statelessness, Kubernetes secret injection, CI phases).

### Cons

- Too conceptual for direct migration execution (missing file-level inventory and concrete step plan).
- Pulls future complexity (orchestrator, progress channels) too early for stage 1 parity migration.
- Contains assumptions less aligned with current web-demo code reality (e.g., dependency/system package framing around PyAudio for production path).

### Main risk

- Delayed delivery due to architecture expansion before baseline parity is shipped.

## 3) GPT variant

### Pros

- Best explicit scope framing: stage 1 must-haves + explicit non-goals.
- Strong single-architecture recommendation (modular monolith) with bounded contexts.
- Includes two critical execution artifacts:
  - proposed target repo tree
  - file-level migration inventory with keep/adapt/drop decisions
- Good future extensibility posture without forcing immediate complexity.

### Cons

- Uses a new package name (`livoia_prod`) that may increase migration churn and import changes without strong functional benefit.
- Some abstraction layers can be interpreted too rigidly unless accompanied by migration pragmatism.
- Less implementation granularity than Claude in certain runtime details.

### Main risk

- Refactor tax from unnecessary renaming/splitting if adopted literally.

## Consolidation conclusion

The best synthesis is:

1. **Take GPT as the backbone** (scope discipline, single architecture, inventory orientation).
2. **Take Claude as the execution detail source** (migration phases, concrete provider flow, CI/doc specifics).
3. **Use Gemini selectively as future-roadmap input only** (async orchestrator/tool lifecycle concepts), not stage 1 baseline implementation.

This yields a design that is realistic to implement quickly while still leaving clean extension points for prompt/tool transparency and asynchronous tooling later.
