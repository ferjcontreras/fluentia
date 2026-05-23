# Gemini Model Comparison for Live API

**Date**: 2026-04-07
**Source**: https://ai.google.dev/gemini-api/docs/live-api and related documentation

---

## Available Models for Live API

| Model ID | Display Name | Context Window | Native Audio | Proactivity | Affective Dialog | Async Function Calling |
|----------|-------------|----------------|-------------|-------------|-----------------|----------------------|
| `gemini-3.1-flash-live-preview` | Gemini 3.1 Flash Live | 128k tokens | Yes | No | No | No (sequential only) |
| `gemini-2.5-flash-native-audio-preview-12-2025` | Gemini 2.5 Flash Native Audio | 128k tokens | Yes | Yes (v1alpha) | Yes (v1alpha) | Yes (NON_BLOCKING) |
| `gemini-2.5-flash-live-preview` | Gemini 2.5 Flash Live | 32k tokens | No | No | No | Yes (NON_BLOCKING) |

---

## Gemini 3.1 Flash Live Details

- **Model ID**: `gemini-3.1-flash-live-preview`
- **Thinking**: Uses `thinkingLevel` (minimal, low, medium, high) instead of `thinkingBudget`
- **Thinking output**: `thinking_config.include_thoughts` for thought summaries
- **Text input**: `send_client_content` for initial context only; use `send_realtime_input` during session
- **Turn coverage**: Defaults to `TURN_INCLUDES_AUDIO_ACTIVITY_AND_ALL_VIDEO`
- **Config option**: `initial_history_in_client_content` (3.1 only)
- **Unsupported features**: Proactive audio, affective dialog, async function calling

---

## Gemini 2.5 Flash Native Audio Details

- **Model ID**: `gemini-2.5-flash-native-audio-preview-12-2025`
- **Previous version**: `gemini-2.5-flash-native-audio-preview-09-2025`
- **Proactivity**: Requires `v1alpha` API version. Config: `proactivity={'proactive_audio': True}`
- **Affective dialog**: Requires `v1alpha`. Config: `enable_affective_dialog=True`
- **Async function calling**: `behavior: NON_BLOCKING`, scheduling options: `INTERRUPT`, `WHEN_IDLE`, `SILENT`

---

## Audio Specifications (All Models)

| Parameter | Value |
|-----------|-------|
| Input format | Raw 16-bit PCM, little-endian |
| Input sample rate | 16 kHz |
| Input MIME type | `audio/pcm;rate=16000` |
| Output format | Raw 16-bit PCM |
| Output sample rate | 24 kHz |
| Recommended chunk size | 20-40ms |
| Max buffering | 100ms |
| Audio token rate | ~25 tokens/second |

---

## Session Limits

| Parameter | Value |
|-----------|-------|
| Connection lifetime | ~10 minutes (server sends GoAway) |
| Audio-only session (no compression) | ~15 minutes |
| Audio+video session (no compression) | ~2 minutes |
| Resumption token validity | 2 hours |
| Supported languages | 97 |

---

## SDK Information

- **Python package**: `google-genai` (import: `from google import genai`)
- **ADK package**: `google-adk` (import: `from google.adk.agents import Agent`)
- **JavaScript package**: `@google/genai`
