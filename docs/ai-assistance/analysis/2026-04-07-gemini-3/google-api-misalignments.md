# Google Gemini Live API: Misalignments and Improvement Opportunities

**Date**: 2026-04-07
**Context**: Analysis of Fluentia's Google provider implementation vs. current Google documentation for the Gemini Live API.

---

## 1. Model ID Version Drift

**Current**: Default model is `gemini-2.5-flash-native-audio-preview-09-2025`
**Latest in Google docs**: `gemini-2.5-flash-native-audio-preview-12-2025` (December 2025 version)

**Impact**: We may be using an older preview snapshot. Google may deprecate the `-09-2025` variant.
**Action**: Update to `-12-2025` when switching the 2.5 model reference. (Done as part of this task.)

---

## 2. Context Window Compression Not Implemented

**Google recommendation**: Enable `ContextWindowCompressionConfig` with `SlidingWindow()` for sessions expected to last more than a few minutes. Optional `trigger_tokens` parameter.

```python
config = types.LiveConnectConfig(
    context_window_compression=types.ContextWindowCompressionConfig(
        sliding_window=types.SlidingWindow(),
        trigger_tokens=1000,  # optional
    )
)
```

**Current state**: Not implemented. Our sessions can exceed the 32k context window for non-native-audio models (128k for native audio).
**Impact**: Long sessions may silently lose context. Native audio models have 128k tokens which is ~85 minutes of audio at 25 tokens/sec, so this is less urgent for audio-only sessions, but still recommended.
**Action**: Add context window compression support, especially for sessions expected to exceed a few minutes.

---

## 3. GoAway Message Handling Not Implemented

**Google recommendation**: The server sends a `GoAway` message with `timeLeft` before terminating the session (~10 minute connection lifetime). Clients should handle this gracefully by resuming the session.

**Current state**: We do not detect or handle GoAway messages. If the server terminates, the session ends abruptly.
**Impact**: Sessions longer than ~10 minutes will drop without graceful resumption.
**Action**: Implement GoAway detection and automatic session resumption in the Google provider.

---

## 4. Session Resumption Only Partially Implemented

**Google recommendation**: Store the latest `new_handle` from `SessionResumptionUpdate` messages and pass it as `SessionResumptionConfig.handle` on reconnect. Tokens are valid for 2 hours.

**Current state**: We pass `SessionResumptionConfig()` (empty, no handle) in the RunConfig. We never store or use resumption handles.
**Impact**: Reconnections start fresh sessions instead of resuming state.
**Action**: Implement full session resumption: store handles in memory, pass them on reconnect, handle `SessionResumptionUpdate` events.

---

## 5. Audio Chunk Timing Recommendations

**Google recommendation**: Send audio in 20-40ms chunks; never buffer more than 100ms before sending.

**Current state**: Our `AudioWorkletProcessor` sends audio in process() blocks (128 frames at 16kHz = 8ms per block). This is actually within spec but smaller than recommended.
**Impact**: Small chunks may increase WebSocket overhead. The docs recommend 20-40ms (320-640 samples at 16kHz).
**Action**: Consider batching multiple AudioWorklet process() outputs to reach 20-40ms chunks. Low priority since current behavior works.

---

## 6. Proactivity and Affective Dialog Require `v1alpha` API Version

**Google docs**: Proactivity (`proactive_audio`) and affective dialog require the `v1alpha` API version.

**Current state**: We enable these features via ADK RunConfig without explicitly setting the API version. It's unclear whether the ADK handles this automatically.
**Impact**: These features may silently fail or not be enabled if the ADK defaults to v1 instead of v1alpha.
**Action**: Verify that google-adk correctly handles v1alpha routing when proactivity/affective_dialog are enabled. If not, add explicit API version configuration.

---

## 7. Voice Configuration Not Passed

**Google docs**: Voice can be configured via `speech_config.voice_config.prebuilt_voice_config.voice_name` (e.g., "Kore").

**Current state**: We do not pass a voice configuration to the RunConfig. The model uses its default voice.
**Impact**: No ability to customize the agent's voice.
**Action**: Consider adding a `voice_name` field to `GoogleProviderConfig` and passing it in the RunConfig.

---

## 8. Thinking Configuration for Gemini 3.1

**Google docs**: Gemini 3.1 uses `thinkingLevel` (minimal, low, medium, high) instead of `thinkingBudget`. Supports `thinking_config.include_thoughts` for thought summaries.

**Current state**: No thinking configuration is passed.
**Impact**: The model uses its default thinking behavior. For voice interactions, lower thinking levels may improve latency.
**Action**: Consider adding thinking level configuration, especially for Gemini 3.1 where latency matters.

---

## 9. Language Instruction Best Practice

**Google recommendation**: For multilingual scenarios, use explicit language instructions:
`"RESPOND IN {LANG}. YOU MUST RESPOND UNMISTAKABLY IN {LANG}."`

**Current state**: Language is handled via the agent prompt template, not via explicit configuration.
**Impact**: The model might switch languages unexpectedly in multilingual contexts.
**Action**: Low priority, but consider adding language enforcement in system prompts for non-English agents.

---

## 10. Cascaded Model Not Explored

**Google docs**: There is a cascaded model variant `gemini-live-2.5-flash` mentioned in best practices documentation that may have different latency/quality trade-offs.

**Current state**: Not used or mentioned.
**Impact**: May miss latency improvements for certain use cases.
**Action**: Evaluate the cascaded model variant for use cases where latency is more important than quality.

---

## Priority Summary

| # | Issue | Priority | Effort |
|---|-------|----------|--------|
| 1 | Model ID version drift | High | Low |
| 2 | Context window compression | Medium | Medium |
| 3 | GoAway handling | Medium | Medium |
| 4 | Full session resumption | Medium | High |
| 5 | Audio chunk timing | Low | Low |
| 6 | v1alpha API version | Medium | Low |
| 7 | Voice configuration | Low | Low |
| 8 | Thinking config for 3.1 | Low | Low |
| 9 | Language instructions | Low | Low |
| 10 | Cascaded model evaluation | Low | Low |
