# Improve Conversation Tab

## Problem Statement

The current Conversation tab divides the screen into two panels:
- **Left (~67%)**: Chat-style transcription log with message bubbles.
- **Right (~33%)**: Dark-themed "Event Console" showing raw protocol events.

This layout serves developers debugging the WebSocket protocol, but it overwhelms end users. During a voice conversation, the primary feedback a user needs is: "the conversation is happening and the agent is listening/speaking." The transcription log and event console are secondary.

## Objectives

1. **Simplify the default experience.** Replace the two-panel layout with a single, centered view that communicates conversation state through visual feedback (animation).
2. **Make advanced panels opt-in.** Both the transcription log and the event console should be toggleable overlays or collapsible sections, not permanent fixtures.
3. **Preserve the "You should speak first" prompt.** Keep this message visible until the user produces their first speech input.
4. **Zero backend changes.** All modifications are confined to `static/index.html`, `static/css/styles.css`, and `static/js/app.js`.

## Requirements

### Functional

| ID | Requirement |
|----|-------------|
| F1 | The default Conversation tab shows a centered conversation state indicator (animated when active, static when idle). |
| F2 | The "You should speak first" message appears after clicking "Start Conversation" and disappears on the first `input_transcription` or `audio` event from the user's turn. |
| F3 | A toggle control allows the user to show/hide the transcription log. When hidden, transcription events are still received but not rendered. |
| F4 | A toggle control allows the user to show/hide the event console. When hidden, events are still captured in memory so toggling it on mid-session shows prior events. |
| F5 | The "Start Conversation" / "New Conversation" button and the text input remain always visible at the bottom. |
| F6 | The existing transcription and event console functionality is preserved without regressions when toggled on. |

### Non-Functional

| ID | Requirement |
|----|-------------|
| N1 | No new JavaScript dependencies. CSS animations only. |
| N2 | Responsive on mobile (single column, no horizontal scroll). |
| N3 | Smooth transitions when toggling panels (no layout jumps). |

## Scope

### In Scope

- Conversation tab layout restructuring.
- Conversation state animation (idle, listening, agent speaking).
- Toggle controls for transcription and event console.
- CSS and JS changes in `static/`.

### Out of Scope

- Settings tab changes.
- Backend or WebSocket protocol changes.
- New event types.
- Provider-specific behavior.

## Feasibility Assessment

**Difficulty: Low-Medium.** All changes are frontend-only (HTML, CSS, vanilla JS). The existing codebase already has:

- State variables tracking conversation phase (`conversationActive`, `isAudio`, `currentOutputTranscriptionElement`).
- A `removeSpeakFirstBanner()` mechanism triggered on first agent response.
- Modular DOM helpers (`createMessageBubble`, `addConsoleEntry`) that can be conditionally skipped.
- CSS animations infrastructure (`@keyframes slideIn`, `@keyframes bannerPulse`, `@keyframes ellipsis`).

The main work items:
1. **New CSS**: Conversation state indicator with 3 visual states (~40 lines of CSS).
2. **Layout restructuring**: Replace fixed two-panel `main-layout` with a centered single-column default (~20 lines of CSS).
3. **Toggle logic**: Two boolean flags in JS controlling `display` of transcription and console panels (~30 lines of JS).
4. **State-driven animation**: Map existing WebSocket events to animation states (~20 lines of JS).

Estimated total: ~110 lines of new/modified code across 3 files.

## Related Documents

- [Summary](summary.md): Design intuition, visual states, key decisions.
- [Detailed Design](detailed-design.md): Component specs, HTML structure, CSS, JS changes.
