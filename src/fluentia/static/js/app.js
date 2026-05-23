/**
 * app.js: Main application logic for Fluentia Voice Agent.
 *
 * Uses the versioned event protocol (v1) with normalized event types.
 */

import { startAudioPlayerWorklet, startAudioRecorderWorklet, stopMicrophone } from "./audio-worklet.js";

// ---- Tab switching ----

const tabButtons = document.querySelectorAll(".tab-button");
const tabContents = document.querySelectorAll(".tab-content");

tabButtons.forEach(button => {
  button.addEventListener("click", () => {
    const targetTab = button.dataset.tab;
    tabButtons.forEach(b => b.classList.remove("active"));
    tabContents.forEach(c => c.classList.remove("active"));
    button.classList.add("active");
    document.getElementById("tab-" + targetTab).classList.add("active");
  });
});

// ---- Agent metadata and dynamic settings ----

let agentMetadata = [];
let selectedAgentName = null;
let promptPreviewTimer = null;
let googleModels = [];
let selectedModelId = null;

async function loadAgentMetadata() {
  try {
    const response = await fetch("/api/agents");
    agentMetadata = await response.json();
    buildAgentSelector(agentMetadata);
    if (agentMetadata.length > 0) {
      selectAgent(agentMetadata[0].name);
    }
  } catch {
    // Graceful degradation
  }
}

async function loadGoogleModels() {
  try {
    const response = await fetch("/api/google/models");
    googleModels = await response.json();
    buildModelSelector(googleModels);
  } catch (err) {
    console.warn("Failed to load Google models:", err);
  }
}

function buildModelSelector(models) {
  const defaultModel = models.find(m => m.is_default) || models[0];
  if (defaultModel) selectedModelId = defaultModel.model_id;
}

function getSelectedModelSpec() {
  return googleModels.find(m => m.model_id === selectedModelId) || null;
}

function buildAgentSelector(agents) {
  const select = document.getElementById("agentSelect");
  select.innerHTML = "";
  for (const agent of agents) {
    const option = document.createElement("option");
    option.value = agent.name;
    option.textContent = agent.display_name;
    select.appendChild(option);
  }
  select.addEventListener("change", () => selectAgent(select.value));
}

function selectAgent(agentName) {
  selectedAgentName = agentName;
  const agent = agentMetadata.find(a => a.name === agentName);
  if (!agent) return;

  document.getElementById("agentSelect").value = agentName;
  document.getElementById("agentDescription").textContent = agent.description;
  buildSettingsForm(agent.fields);
  clearPromptPreview();
}

function buildSettingsForm(fields) {
  const container = document.getElementById("agentFields");
  container.innerHTML = "";

  for (const field of fields) {
    const wrapper = document.createElement("div");
    wrapper.className = "settings-field";

    const label = document.createElement("label");
    label.textContent = field.label;
    wrapper.appendChild(label);

    let input;
    if (field.field_type === "textarea") {
      input = document.createElement("textarea");
      input.rows = field.rows || 6;
      input.placeholder = field.placeholder || "";
      input.value = field.default || "";
    } else if (field.field_type === "select" && field.options) {
      input = document.createElement("select");
      for (const opt of field.options) {
        const optEl = document.createElement("option");
        optEl.value = opt;
        optEl.textContent = opt;
        if (opt === field.default) optEl.selected = true;
        input.appendChild(optEl);
      }
    } else {
      input = document.createElement("input");
      input.type = "text";
      input.placeholder = field.placeholder || "";
      input.value = field.default || "";
    }

    input.setAttribute("data-field-key", field.key);
    wrapper.appendChild(input);

    if (field.description) {
      const desc = document.createElement("span");
      desc.className = "field-description";
      desc.textContent = field.description;
      wrapper.appendChild(desc);
    }

    container.appendChild(wrapper);

    input.addEventListener("input", schedulePromptPreview);
  }
}

function collectFieldValues() {
  const values = {};
  document.querySelectorAll("[data-field-key]").forEach(input => {
    const key = input.dataset.fieldKey;
    const value = input.value;
    if (value.trim()) {
      values[key] = value;
    }
  });
  return values;
}

function sendPromptConfig() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      type: "prompt_config",
      variables: collectFieldValues(),
    }));
  }
}

// ---- Prompt preview ----

function schedulePromptPreview() {
  if (conversationActive) return;
  if (promptPreviewTimer) clearTimeout(promptPreviewTimer);
  promptPreviewTimer = setTimeout(renderPromptPreview, 400);
}

async function renderPromptPreview() {
  if (!selectedAgentName) return;
  const previewEl = document.getElementById("promptPreviewContent");
  const previewPanel = document.getElementById("promptPreview");

  previewPanel.classList.add("loading");
  try {
    const response = await fetch(`/api/agents/${encodeURIComponent(selectedAgentName)}/render-prompt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ variables: collectFieldValues() }),
    });
    if (response.ok) {
      previewEl.innerHTML = await response.text();
    } else {
      previewEl.textContent = "Could not render prompt";
    }
  } catch {
    previewEl.textContent = "Could not render prompt";
  } finally {
    previewPanel.classList.remove("loading");
  }
}

function clearPromptPreview() {
  document.getElementById("promptPreviewContent").textContent = "";
  schedulePromptPreview();
}

// ---- Session lock/unlock for settings ----

function setSettingsLocked(locked) {
  const agentSelect = document.getElementById("agentSelect");
  if (agentSelect) agentSelect.disabled = locked;

  document.querySelectorAll("#agentFields input, #agentFields textarea, #agentFields select").forEach(el => {
    el.disabled = locked;
  });
}

// ---- WebSocket handling ----

const userId = "demo-user";
let sessionId = generateSessionId();
let websocket = null;
let isAudio = false;
let conversationActive = false;
let intentionalClose = false;

function generateSessionId() {
  return "session-" + Math.random().toString(36).substring(7);
}

function getWebSocketUrl() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const baseUrl = proto + "//" + window.location.host + "/ws/google/" + userId + "/" + sessionId;
  const params = new URLSearchParams();
  if (selectedAgentName) params.append("agent", selectedAgentName);
  if (selectedModelId) params.append("model", selectedModelId);
  const queryString = params.toString();
  return queryString ? baseUrl + "?" + queryString : baseUrl;
}

// ---- DOM elements ----

const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("message");
const statusIndicator = document.getElementById("statusIndicator");
const statusText = document.getElementById("statusText");
const consoleContent = document.getElementById("consoleContent");
const clearConsoleBtn = document.getElementById("clearConsole");
const showAudioEventsCheckbox = document.getElementById("showAudioEvents");

// ---- Panel toggles ----

const toggleConsoleBtn = document.getElementById("toggleConsole");
const consolePanel = document.getElementById("consolePanel");

let consoleVisible = false;
let subtitlesEnabled = false;

const toggleSubtitlesBtn = document.getElementById("toggleSubtitles");
const subtitleBar = document.getElementById("subtitleBar");
const subtitleText = document.getElementById("subtitleText");
let subtitleFadeTimer = null;

function setSubtitlesEnabled(enabled) {
  subtitlesEnabled = enabled;
  toggleSubtitlesBtn.classList.toggle("active", enabled);
  if (!enabled) {
    subtitleBar.classList.add("hidden");
  }
}

function updateSubtitle(text) {
  if (!subtitlesEnabled) return;
  if (subtitleFadeTimer) {
    clearTimeout(subtitleFadeTimer);
    subtitleFadeTimer = null;
    subtitleBar.classList.remove("fading");
  }
  subtitleText.textContent = text;
  subtitleBar.classList.remove("hidden");
}

function clearSubtitle(fade = true) {
  if (!subtitlesEnabled) return;
  if (fade) {
    subtitleBar.classList.add("fading");
    subtitleFadeTimer = setTimeout(() => {
      subtitleBar.classList.add("hidden");
      subtitleBar.classList.remove("fading");
      subtitleText.textContent = "";
      subtitleFadeTimer = null;
    }, 400);
  } else {
    subtitleBar.classList.add("hidden");
    subtitleText.textContent = "";
  }
}

toggleConsoleBtn.addEventListener("click", () => setConsoleVisible(!consoleVisible));
toggleSubtitlesBtn.addEventListener("click", () => setSubtitlesEnabled(!subtitlesEnabled));

document.getElementById("closeConsole").addEventListener("click", () => setConsoleVisible(false));

// ---- Conversation state indicator ----

const stateIndicator = document.getElementById("stateIndicator");
const stateLabel = document.getElementById("stateLabel");
let conversationState = "idle";

function setConversationState(newState) {
  conversationState = newState;
  stateIndicator.className = "state-indicator " + newState;
  switch (newState) {
    case "idle":
      stateLabel.textContent = "";
      break;
    case "waiting":
      stateLabel.textContent = "";
      break;
    case "user-speaking":
      stateLabel.textContent = "Listening...";
      break;
    case "agent-speaking":
      stateLabel.textContent = "Speaking...";
      break;
  }
}

let inputTranscriptionFinished = false;

// ---- Console ----

function formatTimestamp() {
  const now = new Date();
  return now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
}

function addConsoleEntry(type, content, data = null, isAudio = false) {
  if (isAudio && !showAudioEventsCheckbox.checked) return;

  const entry = document.createElement("div");
  entry.className = `console-entry ${type}`;

  const header = document.createElement("div");
  header.className = "console-entry-header";

  const leftSection = document.createElement("div");
  leftSection.className = "console-entry-left";

  const expandIcon = document.createElement("span");
  expandIcon.className = "console-expand-icon";
  expandIcon.textContent = data ? ">" : "";

  const typeLabel = document.createElement("span");
  typeLabel.className = "console-entry-type";
  typeLabel.textContent = type === 'outgoing' ? 'UP' : type === 'incoming' ? 'DN' : 'ERR';

  leftSection.appendChild(expandIcon);
  leftSection.appendChild(typeLabel);

  const timestamp = document.createElement("span");
  timestamp.className = "console-entry-timestamp";
  timestamp.textContent = formatTimestamp();

  header.appendChild(leftSection);
  header.appendChild(timestamp);

  const contentDiv = document.createElement("div");
  contentDiv.className = "console-entry-content";
  contentDiv.textContent = content;

  entry.appendChild(header);
  entry.appendChild(contentDiv);

  if (data) {
    const jsonDiv = document.createElement("div");
    jsonDiv.className = "console-entry-json collapsed";
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(data, null, 2);
    jsonDiv.appendChild(pre);
    entry.appendChild(jsonDiv);

    entry.classList.add("expandable");
    entry.addEventListener("click", () => {
      const isExpanded = !jsonDiv.classList.contains("collapsed");
      if (isExpanded) {
        jsonDiv.classList.add("collapsed");
        expandIcon.textContent = ">";
      } else {
        jsonDiv.classList.remove("collapsed");
        expandIcon.textContent = "v";
      }
    });
  }

  consoleContent.appendChild(entry);
  consoleContent.scrollTop = consoleContent.scrollHeight;
}

clearConsoleBtn.addEventListener('click', () => { consoleContent.innerHTML = ''; });

// ---- UI helpers ----

function updateConnectionStatus(connected) {
  if (connected) {
    statusIndicator.classList.remove("disconnected");
    statusText.textContent = "Connected";
  } else {
    statusIndicator.classList.add("disconnected");
    statusText.textContent = "Disconnected";
  }
}

function addSpeakFirstBanner() {
  const banner = document.createElement("div");
  banner.className = "speak-first-banner";
  banner.id = "speakFirstBanner";
  banner.innerHTML = '<span class="banner-icon">&#x1f3a4;</span><span class="banner-text">You should speak first</span>';
  // Insert after state label in conversation center
  stateLabel.insertAdjacentElement("afterend", banner);
}

function removeSpeakFirstBanner() {
  const banner = document.getElementById("speakFirstBanner");
  if (banner) banner.remove();
}

// Decode Base64 to ArrayBuffer
function base64ToArrayBuffer(base64) {
  let std = base64.replace(/-/g, '+').replace(/_/g, '/');
  while (std.length % 4) std += '=';
  const bin = window.atob(std);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

// ---- WebSocket connection ----

function connectWebsocket() {
  const wsUrl = getWebSocketUrl();
  websocket = new WebSocket(wsUrl);

  websocket.onopen = function () {
    updateConnectionStatus(true);
    sendPromptConfig();
    addConsoleEntry('incoming', 'WebSocket Connected', { url: wsUrl });
    document.getElementById("sendButton").disabled = false;
    addSubmitHandler();
  };

  websocket.onmessage = function (event) {
    if (typeof event.data !== "string") return;

    const msg = JSON.parse(event.data);
    const type = msg.type;
    const payload = msg.payload || {};

    // Remove speak-first banner on first content
    if (type === "audio" || type === "output_transcription" || type === "text") {
      removeSpeakFirstBanner();
    }

    switch (type) {
      case "audio":
        if (conversationState !== "agent-speaking") {
          setConversationState("agent-speaking");
        }
        if (audioPlayerNode) {
          audioPlayerNode.port.postMessage(base64ToArrayBuffer(payload.data));
        }
        addConsoleEntry('incoming', `Audio: ${payload.sample_rate}Hz`, null, true);
        break;

      case "text":
        addConsoleEntry('incoming', `Text: ${payload.content}`, payload);
        break;

      case "input_transcription": {
        const text = payload.text || "";
        const isPartial = payload.is_partial;
        if (!text) break;

        if (conversationState === "waiting" || conversationState === "agent-speaking") {
          setConversationState("user-speaking");
          removeSpeakFirstBanner();
        }

        if (!isPartial && !inputTranscriptionFinished) {
          inputTranscriptionFinished = true;
        }
        addConsoleEntry('incoming', `Input: "${text}"`, payload);
        break;
      }

      case "output_transcription": {
        const text = payload.text || "";
        const isPartial = payload.is_partial;
        if (!text) break;

        if (conversationState !== "agent-speaking") {
          setConversationState("agent-speaking");
        }
        inputTranscriptionFinished = true;

        if (isPartial) {
          updateSubtitle(subtitleText.textContent + text);
        } else {
          updateSubtitle(text);
        }
        addConsoleEntry('incoming', `Output: "${text}"`, payload);
        break;
      }

      case "turn_complete":
        if (conversationActive) {
          setConversationState("user-speaking");
        }
        inputTranscriptionFinished = false;
        clearSubtitle(true);
        addConsoleEntry('incoming', 'Turn Complete', payload);
        break;

      case "interrupted":
        if (conversationActive) {
          setConversationState("user-speaking");
        }
        if (audioPlayerNode) {
          audioPlayerNode.port.postMessage({ command: "endOfAudio" });
        }
        inputTranscriptionFinished = false;
        clearSubtitle(false);
        addConsoleEntry('incoming', 'Interrupted', payload);
        break;

      case "session_start":
        addConsoleEntry('incoming', 'Session Started', payload);
        break;

      case "session_end":
        addConsoleEntry('incoming', 'Session Ended', payload);
        break;

      case "tool_started":
      case "tool_progress":
      case "tool_completed":
      case "tool_failed":
        addConsoleEntry('incoming', `Tool: ${type} - ${payload.tool_name || ''}`, payload);
        break;

      case "error":
        addConsoleEntry('error', `Error: ${payload.message}`, payload);
        break;

      default:
        // Ignore unknown types (forward compatibility)
        break;
    }
  };

  websocket.onclose = function () {
    updateConnectionStatus(false);
    document.getElementById("sendButton").disabled = true;

    if (intentionalClose) {
      intentionalClose = false;
      return;
    }

    addConsoleEntry('error', 'WebSocket Disconnected');

    setTimeout(function () {
      connectWebsocket();
    }, 5000);
  };

  websocket.onerror = function () {
    updateConnectionStatus(false);
    addConsoleEntry('error', 'WebSocket Error');
  };
}

// Load agents then connect
async function init() {
  await Promise.all([loadAgentMetadata(), loadGoogleModels()]);
  connectWebsocket();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// ---- Text message submission ----

function addSubmitHandler() {
  messageForm.onsubmit = function (e) {
    e.preventDefault();
    const msg = messageInput.value.trim();
    if (msg) {
      messageInput.value = "";
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: "text", text: msg }));
        addConsoleEntry('outgoing', 'User: ' + msg);
      }
    }
    return false;
  };
}

// ---- Audio handling ----

let audioPlayerNode;
let audioPlayerContext;
let audioRecorderNode;
let audioRecorderContext;
let micStream;

function startAudio() {
  startAudioPlayerWorklet().then(([node, ctx]) => {
    audioPlayerNode = node;
    audioPlayerContext = ctx;
  });
  startAudioRecorderWorklet(audioRecorderHandler).then(([node, ctx, stream]) => {
    audioRecorderNode = node;
    audioRecorderContext = ctx;
    micStream = stream;
  });
}

function stopAudio() {
  if (micStream) {
    stopMicrophone(micStream);
    micStream = null;
  }
  if (audioRecorderContext) {
    audioRecorderContext.close();
    audioRecorderContext = null;
    audioRecorderNode = null;
  }
  if (audioPlayerNode) {
    audioPlayerNode.port.postMessage({ command: "endOfAudio" });
  }
  if (audioPlayerContext) {
    audioPlayerContext.close();
    audioPlayerContext = null;
    audioPlayerNode = null;
  }
}

function resetConversationState() {
  inputTranscriptionFinished = false;
  clearSubtitle(false);
}

const startAudioButton = document.getElementById("startAudioButton");
startAudioButton.addEventListener("click", () => {
  if (!conversationActive) {
    // Reconnect with the current settings before starting the session
    sessionId = generateSessionId();
    intentionalClose = true;
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.close();
    }
    connectWebsocket();
    startAudio();
    isAudio = true;
    conversationActive = true;
    startAudioButton.textContent = "New Conversation";
    startAudioButton.classList.add("active");
    setConversationState("waiting");
    setSettingsLocked(true);
    addSpeakFirstBanner();
    addConsoleEntry('outgoing', 'Conversation Started');
  } else {
    stopAudio();
    isAudio = false;
    conversationActive = false;
    startAudioButton.textContent = "Start Conversation";
    startAudioButton.classList.remove("active");
    setConversationState("idle");
    setSettingsLocked(false);
    resetConversationState();
    sessionId = generateSessionId();
    intentionalClose = true;
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.close();
    }
    connectWebsocket();
    addConsoleEntry('outgoing', 'Conversation Reset');
  }
});

function audioRecorderHandler(pcmData) {
  if (websocket && websocket.readyState === WebSocket.OPEN && isAudio) {
    websocket.send(pcmData);
  }
}

