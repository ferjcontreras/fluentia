# Decision Rationale: Per-Dimension Justification

This document explains, for each architectural dimension, which variant's approach was chosen, which were rejected, and why.

---

## 1. Package Structure

**Chosen**: Gemini's three-domain layout (`session/`, `providers/`, `tools/`), adapted with Claude's flat-where-possible principle.

**Rejected**:
- GPT's five-layer architecture: Too many layers for the current scope. The `observability/security` layer as a first-class boundary is premature -- observability is a cross-cutting concern, not a layer in the call chain. The `web/protocol/` sub-package adds nesting that doesn't carry its weight.
- Claude's fully flat layout: The missing session orchestration layer means session lifecycle logic would be duplicated across providers. When both Google and Bedrock need to handle reconnections, timeouts, and event relay, that shared logic needs a home.

**Key adaptation**: Gemini's `core/` was renamed to `session/` because "core" is too vague. The session package owns exactly one responsibility: managing the WebSocket session lifecycle, normalizing events, and coordinating with providers. This is more discoverable than "core."

---

## 2. Provider Interface

**Chosen**: Hybrid of Claude's `handle_session()` method and GPT's event normalization.

**Rejected**:
- GPT's fine-grained interface (`connect`, `send_audio`, `send_text`, `receive_events`, `close`): Too prescriptive. Google ADK manages its own connection lifecycle internally -- forcing it into a 5-method interface would require fighting the SDK. Claude correctly identified this constraint.
- Claude's provider-owns-everything approach: Correct about lifecycle ownership, but without event normalization, each provider must independently implement WebSocket message formatting. This duplicates protocol logic and makes protocol changes require touching every provider.
- Gemini's unspecified interface: No concrete interface to evaluate.

**Resolution**: Providers own their session lifecycle (call `handle_session()`) but communicate results via a shared `emit()` callback that accepts normalized `SessionEvent` objects. This gives providers maximum SDK-level freedom while ensuring the session layer sees a uniform event stream.

---

## 3. WebSocket Protocol

**Chosen**: GPT's protocol versioning and event taxonomy.

**Rejected**:
- Claude's unversioned protocol: Works today, but any protocol change requires coordinated client-server deployments. Adding `"v": 1` to every message is nearly zero cost and enables graceful protocol evolution.
- Gemini's dual-channel approach (WebSocket + SSE): Adds client-side complexity (managing two connections) for a benefit (separating audio from tool events) that can be achieved more simply with a `type` field on a single channel.

**Why GPT wins here**: Protocol versioning is a one-time investment with compounding returns. It's the kind of decision that's trivial to make now and painful to retrofit later. GPT was the only variant that recognized this.

---

## 4. Tool Framework

**Chosen**: Claude's concrete implementation as foundation + Gemini's async state machine as the evolution path.

**Rejected**:
- GPT's export-dead-code approach: Exporting `tools/base.py` with no consumers violates the "no dead code" principle. Better to define the right interface and implement it when needed.
- Gemini's purely conceptual design: The vocal narration idea is innovative, but without implementation details (asyncio primitives, cancellation, error handling), it can't be adopted as-is.

**Resolution**: Define `BaseTool`, `ToolProcessor`, `ToolState`, and `ToolResult` types in stage 1. The types are small, tested, and provide the seam for future tool implementations. The async state machine pattern is documented as the intended approach for long-running tools but is not implemented until a tool needs it. This is different from GPT's dead code -- these are types with tests, not unused framework code.

---

## 5. Configuration

**Chosen**: Claude's concrete implementation with GPT's three-layer mental model and Gemini's IRSA awareness.

**Rejected**:
- GPT's future env groups (`TOOLS_*`, `ORCHESTRATOR_*`): Premature. Defining env prefixes before the features they configure exist creates naming commitments that may not survive contact with reality.
- Gemini's minimal 5-variable list: Insufficient for a real deployment.

**Why Claude wins**: Claude provided exact variable names, types, defaults, and Pydantic model code. The other two described configuration philosophically. When a developer needs to implement configuration, Claude's variant is the only one that can be used directly.

**Additions**:
- GPT's secret redaction policy (never log raw keys, redact at startup) is added because it's a production hygiene requirement that Claude overlooked.
- Gemini's IRSA note (AWS credentials optional, provided by IAM Roles for Service Accounts in production) is added because it correctly reflects how Kubernetes workloads authenticate to AWS.

---

## 6. CI/CD Pipeline

**Chosen**: Consensus (all three propose the same four stages), with per-variant refinements merged.

All three variants independently arrived at `quality -> tests -> dependency-analysis -> build`. This convergence validates the pipeline structure.

**Refinements taken from each**:
- **GPT**: Least-privilege credentials, short-lived tokens, immutable image tagging.
- **Claude**: Simplified Dockerfile (removed `portaudio19-dev`, renamed image to `livoia`).
- **Gemini**: Commitizen for structured commits, IRSA for ECR authentication.

**Rejected from Gemini**: `--workers 4` in the Dockerfile CMD. WebSocket connections are stateful; multiple uvicorn workers within a single container cause connection routing issues. Horizontal scaling should happen at the Kubernetes pod level, not the uvicorn worker level.

---

## 7. Frontend

**Chosen**: Claude's pragmatic approach (vanilla JS, no build step, files in package).

**Rejected**:
- GPT's "modularize where possible" with no specifics: Not actionable.
- Gemini's ambitious 4-tab vision with no implementation details: Aspirational but premature.

**Why Claude wins**: The frontend is a thin layer over Web Audio APIs and a WebSocket. It doesn't need a framework, a build step, or an elaborate tab architecture in stage 1. Claude's approach ships a working UI with the least possible complexity.

**Taken from Gemini**: The tab roadmap (Settings -> Prompt -> Tool Use) is adopted as the UI evolution path, just not implemented upfront.

---

## 8. Testing Strategy

**Chosen**: Claude's migration-aware test plan + Gemini's coverage targets and test containers.

**Rejected**:
- GPT's test structure without WebSocket guidance: Defines directories but doesn't address the hardest testing challenge (real-time bidirectional streams).

**Gap filled**: WebSocket testing patterns were missing from all three variants. The synthesis adds:
- Unit tests with mocked `WebSocket` objects, asserting `SessionEvent` sequences.
- Integration tests using FastAPI's `TestClient` WebSocket support.
- The observation that `testcontainers-python` (Gemini) can provide ephemeral mock services.

**Why Claude leads**: Claude's 10-phase plan includes "which tests to port" and "validation step" per phase. This makes the migration testable at every stage, not just at the end.

---

## 9. Migration Plan

**Chosen**: GPT's inventory audit as pre-step + Claude's phased execution (streamlined from 10 to 7 phases).

**Rejected**:
- Gemini's absent migration plan: Knowing the target state without a path to get there is insufficient for execution.
- GPT's less granular six-step order: Lacks the per-phase validation and parallelism opportunities that Claude provides.

**Why this combination**: GPT's `EXPORT_AS_IS / EXPORT_ADAPT / DO_NOT_EXPORT` classification is an excellent pre-migration exercise that forces explicit decisions about every file. Claude's phased plan with parallelizable phases (2a/2b/2c and 3a/3b) provides the actual execution path.

**Streamlining from 10 to 7 phases**: Claude's phases 0-9 were consolidated because some phases (e.g., separate phases for tool framework and prompt management) are small enough to run in parallel rather than sequentially. This reduces the critical path without losing granularity.

---

## 10. Observability

**Chosen**: New synthesis (none of the three were adequate).

**Why all three failed**: This is the most surprising gap in the analysis. All three variants discuss production readiness, but:
- GPT defines metrics hooks with no backend.
- Claude drops Prometheus with no replacement.
- Gemini mentions neither health checks nor logging.

For a real-time voice application, observability is table stakes. Session duration, audio latency, provider errors, and tool execution times are critical operational metrics.

**Synthesis approach**: Ship a metrics *interface* (Protocol class) with a logging-based implementation. This gives structured, queryable metrics from day 1 via log aggregation, with a clear upgrade path to Prometheus when the ops team is ready. The cost is near-zero (a few method calls), and the benefit is immediate operational visibility.

---

## 11. Documentation

**Chosen**: Claude's four-category taxonomy + Gemini's Mermaid diagrams and local-dev tutorial.

**Rejected**:
- GPT's flat docs structure: No clear taxonomy.
- Gemini's focus on rewriting existing docs: Effort-intensive with questionable value -- the existing guides are already good.

**Why this combination**: Claude's `guides/references/tutorials/ai-assistance` taxonomy is intuitive and matches the Diataxis documentation framework. Gemini's Mermaid diagrams add visual architecture communication that's more accessible than prose. The local-dev tutorial with docker-compose lowers the onboarding barrier.

---

## 12. Package Name

**Chosen**: `livoia` (Claude) over `livoia_prod` (GPT).

**Rationale**: "prod" in a package name implies the package is environment-specific. But the same code runs in development, staging, and production -- what changes is the configuration, not the package. `livoia` is cleaner, shorter, and doesn't create confusion about whether there's a corresponding `livoia_dev` or `livoia_staging`.

---

## 13. Dependency Reduction

**Chosen**: Claude's aggressive trimming.

**Rationale**: The current PoC has 48 core dependencies because it's a general-purpose ML infrastructure library. The redesign is a focused voice agent. Dependencies should match the scope. Claude is the only variant that explicitly listed what to drop and why, and the reasoning is sound:
- `langchain-*`: Only used by the ML library features being excluded.
- `openai`: Not used directly by voice providers.
- `numpy`: No numerical processing in a WebSocket relay.
- `redis`: No caching needed for stateless voice sessions.
- `PyAudio`: CLI audio removed; browser uses Web Audio API.

The result is a dramatically smaller dependency tree, faster installs, smaller Docker images, and fewer supply chain risks.

---

## Summary: Variant Contribution Scorecard

| Dimension | GPT | Claude | Gemini | Notes |
|-----------|-----|--------|--------|-------|
| Architecture | Partial | Partial | **Primary** | Gemini's layout, adapted |
| Provider Interface | **Primary** | **Primary** | -- | Hybrid of both |
| WebSocket Protocol | **Primary** | -- | -- | GPT's versioning adopted |
| Tool Framework | -- | **Primary** | Partial | Claude's impl + Gemini's patterns |
| Configuration | Partial | **Primary** | Partial | Claude's code + GPT's policy + Gemini's IRSA |
| CI/CD | Partial | Partial | Partial | Equal contributions |
| Frontend | -- | **Primary** | -- | Claude's pragmatism |
| Testing | -- | **Primary** | Partial | Claude's plan + Gemini's tools |
| Migration | Partial | **Primary** | -- | GPT's inventory + Claude's phases |
| Observability | -- | -- | -- | New synthesis (all three failed) |
| Documentation | -- | **Primary** | Partial | Claude's taxonomy + Gemini's visuals |

**Overall**: Claude provides the strongest foundation (most actionable, most concrete), GPT adds the most production foresight (protocol versioning, secret handling, event normalization), and Gemini contributes the most innovative ideas (async tool narration, DI patterns, test containers). The synthesis draws from all three in proportion to their strengths.
