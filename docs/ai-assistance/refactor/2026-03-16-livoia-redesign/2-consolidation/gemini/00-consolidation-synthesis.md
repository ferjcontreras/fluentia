# Redesign Consolidation & Synthesis

This document analyzes the three redesign variants proposed for the `english-teacher-assistant` to production migration. It breaks down each variant, highlights its pros and cons, and proposes a consolidated synthesis architecture that combines their best qualities.

## 1. Analysis of the Variants

### Variant 1: Claude (`2026-03-16-prod-redesign-claude`)

**Core Concept:** A pragmatic, flattened architecture (`src/livoia/`) that consolidates the fragmented PoC packages into a single namespace. It introduces a `BaseProvider` ABC that entirely encapsulates a WebSocket session.

*   **Pros:**
    *   **Simplicity:** Highly pragmatic and eliminates deep module nesting.
    *   **Unified Endpoint:** The `/ws/{provider}/{user_id}/{session_id}` pattern is elegant.
    *   **Extensive Tooling Thought:** Maintains the existing `BaseTool` design while addressing future orchestrator needs directly.
*   **Cons:**
    *   **Coupling:** Making the Provider responsible for the *entire* WebSocket lifecycle tightly couples transport (WebSockets) with business logic (LLM integration).
    *   **Scalability of App:** Putting too much orchestration logic inside `app.py` and the provider could lead to bloated classes.

### Variant 2: Gemini (`2026-03-16-prod-redesign-gemini`)

**Core Concept:** A Domain-Driven structure (`app/`, `core/`, `providers/`) heavily focused on enterprise non-functional requirements like Kubernetes scalability and the "Asynchronous Orchestrator Challenge."

*   **Pros:**
    *   **Enterprise Infrastructure:** Best-in-class CI/CD and multi-stage Docker strategy.
    *   **Strict Statelessness:** Explicitly designs for Kubernetes deployments and removes `.env` file reliance in favor of strict Pydantic runtime injection.
    *   **Complex Feature Handling:** Deeply thinks through the problem of non-blocking audio while long-running external orchestrator tools execute.
*   **Cons:**
    *   **Scope Creep:** Over-indexes on future requirements (like Orchestrator integration) risking complexity during the initial "Stage 1" migration.
    *   **Abstract:** The architecture is a bit high-level without explicit component contracts.

### Variant 3: GPT (`2026-03-16-prod-redesign-gpt`)

**Core Concept:** A strict "Modular Monolith" with deeply segregated bounded contexts (`app/`, `domain/`, `services/`, `providers/`, `web/`, `config/`). Emphasizes strict "Stage 1" non-goals.

*   **Pros:**
    *   **Excellent Separation of Concerns:** Strongly decouples the WebSocket Transport (`app/`) from the Session Orchestration (`services/`), which in turn is decoupled from Provider Network Logic (`providers/`).
    *   **Scope Discipline:** Explicitly defines what is *not* in Stage 1 to maintain focus.
    *   **Protocol Neutrality:** Emphasizes a unified, versionable JSON event protocol over the WebSocket.
*   **Cons:**
    *   **Boilerplate Risk:** A 6-layer architecture might introduce unnecessary mapping overhead for a system whose primary job is bridging an audio stream to an SDK.

---

## 2. Proposed Synthesis

The ideal architecture takes the **Decoupled Orchestration** of GPT, the **Pragmatic Tooling and Endpoints** of Claude, and the **Enterprise Infrastructure** of Gemini.

### Consolidated Architecture Model

A "Pragmatic Domain" layout. It avoids GPT's excessive layering but fixes Claude's transport coupling.

```text
src/livoia/
├── app/                  # Transport Layer (from GPT)
│   ├── main.py           # FastAPI initialization
│   ├── api.py            # HTTP & WS Endpoints (Unified WS pattern from Claude)
│   └── dependencies.py   # DI and state setup
├── core/                 # Business & Orchestration Layer (from Gemini/GPT)
│   ├── session.py        # Manages WebSocket lifecycle & event normalization
│   ├── prompt.py         # Prompt rendering engine
│   └── tools.py          # Tool registry & execution (from Claude)
├── providers/            # External Integrations Layer
│   ├── base.py           # Provider Adapters (Network logic only, no WS handling)
│   ├── google/
│   └── bedrock/
└── config/               # Settings & Validation
```

### Key Synthesized Decisions

#### 1. Transport vs. Provider Protocol
**Decision:** Keep WebSockets out of the Providers.
The `core.session.SessionOrchestrator` will own the WebSocket. It will read audio and text from the client, and independently pass it to a `ProviderAdapter`. The `ProviderAdapter` only knows about the LLM SDK (Google or Bedrock) and yields normalized system events (`TextOutput`, `AudioOutput`, `ToolInvocation`). The Orchestrator forwards these to the WebSocket.
*Why?* Combines GPT's decoupling with Claude's unified endpoint.

#### 2. The Tool Framework & Async Challenges
**Decision:** Adopt Claude's `BaseTool` approach but implement Gemini's detached execution.
Tools will remain localized in `core/tools.py`. However, to support future long-running tools, the `SessionOrchestrator` will handle tool execution asynchronously. It will emit `ToolStarted` and `ToolProgress` events back down the WebSocket (or SSE) for the UI transparency tab, natively solving Gemini's Orchestrator challenge without over-engineering Stage 1.

#### 3. Infrastructure & Configuration
**Decision:** Go all-in on Gemini's infrastructure approach.
*   **Docker:** 2-stage builder using `uv` to ensure a minimal, highly secure production image.
*   **Config:** `pydantic-settings` strictly enforcing environment variables. No `.env` reading in production. AWS credentials handled transparently via K8s Service Accounts.

#### 4. Project Scope
**Decision:** Enforce GPT's Stage 1 Non-Goals.
We will build the codebase to *accommodate* UI tool toggles, the Prompt Tab, and Orchestrator integration, but we will **not** build them in the initial migration. The first milestone must achieve feature parity with the existing Web Demo, just cleanly arranged in the new structure.

## Summary

This synthesis provides a highly maintainable, testable, and production-ready foundation. It sidesteps the boilerplate trap of a pure modular monolith while preventing the spaghetti code that arises when network transport (FastAPI WebSockets) becomes entangled with third-party SDKs (Google/AWS Bedrock).
