# Design Summary: Conversation Tab Redesign

## Core Idea

Replace the developer-oriented two-panel layout with a conversation-first experience. The default view shows a single centered visual indicator that communicates "what's happening right now" through animation. Advanced panels (transcription log, event console) slide in on demand.

## Visual States

The conversation indicator has four states:

### 1. Idle (pre-conversation)

The user has not started a conversation yet. The indicator is a static circle with the Fluentia gradient, rendered at moderate size (80-100px). No animation. The "Start Conversation" button is prominent below.

```
        +-----------------------+
        |                       |
        |                       |
        |       ( circle )      |
        |                       |
        |  "Start Conversation" |
        +-----------------------+
```

### 2. Waiting for User (conversation started, user has not spoken)

The user clicked "Start Conversation" but has not spoken yet. The circle pulses gently (scale 1.0 to 1.05, opacity 0.8 to 1.0). The "You should speak first" message appears below the circle.

```
        +-----------------------+
        |                       |
        |    ( pulsing circle ) |
        |  "You should speak    |
        |         first"        |
        |  "New Conversation"   |
        +-----------------------+
```

### 3. User Speaking (input audio detected)

The user is speaking. The circle shows a rhythmic "breathing" animation: concentric rings expand outward from the circle (ripple effect), colored in the user's blue (`#4285f4`). This state is entered when the client is actively sending audio chunks and an `input_transcription` partial event arrives.

```
        +-----------------------+
        |                       |
        |  (( (( circle )) ))   |  <- blue ripples
        |                       |
        |  "New Conversation"   |
        +-----------------------+
```

### 4. Agent Speaking (audio output received)

The agent is responding. The circle shows an oscillating waveform animation around its perimeter, colored in the agent's green (`#34a853`). This state is entered on `audio` events and cleared on `turn_complete` or `interrupted`.

```
        +-----------------------+
        |                       |
        |  ~~( circle )~~       |  <- green waveform
        |                       |
        |  "New Conversation"   |
        +-----------------------+
```

## State Transitions

```
[Page Load] --> Idle
Idle -- "Start Conversation" click --> WaitingForUser
WaitingForUser -- first input_transcription --> UserSpeaking
UserSpeaking -- output_transcription / audio --> AgentSpeaking
AgentSpeaking -- turn_complete / interrupted --> UserSpeaking
UserSpeaking -- (silence, no events) --> WaitingForUser (optional, deferred)
Any -- "New Conversation" click --> Idle
```

Note: The transition from UserSpeaking back to WaitingForUser on silence is a nice-to-have. The initial implementation can stay in UserSpeaking until the agent responds, since the model processes audio continuously.

## Toggle Panels

Two icon buttons in a toolbar below the tab bar (or in the conversation area header):

| Button | Default | Behavior |
|--------|---------|----------|
| Transcript icon | Off | Slides in a panel on the left showing the existing chat-bubble transcription log. |
| Console icon | Off | Slides in the dark event console panel on the right. |

When both are off, the conversation indicator occupies the full width, centered. When one is on, the indicator shifts or shrinks. When both are on, the layout resembles the current two-panel view with the indicator between them or above.

Recommended approach: **overlay panels**. The indicator always stays centered. Panels slide in from the edges as overlays with slight transparency, so the user retains the sense of "being in a conversation" even while inspecting details.

## Key Decisions

### Why animation instead of text status?

Voice conversations are real-time and continuous. A text label ("Agent is speaking...") adds cognitive load and feels disconnected from the audio experience. A visual animation provides ambient awareness without requiring the user to read.

### Why default to panels hidden?

The transcription is a by-product of ASR and is often inaccurate (as discussed in the audio understanding analysis). Showing it by default sets a false expectation that the text is the "real" conversation. The audio is the real conversation. The event console is a debugging tool. Neither should be the primary experience.

### Why keep the text input always visible?

Some users may prefer to type. The text input also serves as a visual anchor at the bottom of the screen, consistent across states.

### Why CSS-only animations?

No dependency on animation libraries. The existing codebase already uses `@keyframes` for the typing indicator and banner pulse. Adding 3-4 more keyframe definitions is consistent with the current approach and keeps the bundle size at zero.

## Open Questions

1. **Indicator size**: Should the circle be larger on desktop (120px) and smaller on mobile (80px)? Or fixed?
2. **Sound wave visualization**: Should the agent-speaking state use a real-time visualization of the audio output amplitude, or a pre-designed animation? Real-time requires reading PCM data in JS; pre-designed is simpler.
3. **Panel memory**: Should the toggle state persist across page reloads (localStorage)?
