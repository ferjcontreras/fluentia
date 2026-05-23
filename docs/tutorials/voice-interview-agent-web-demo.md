# Voice Interview Agent Web Demo

This tutorial describes how to run the voice interview agent via a web browser. The web UI supports two voice providers:

- **Google Gemini**: Uses Google ADK with native audio models
- **AWS Bedrock**: Uses Amazon Nova Sonic

For deploying with Docker instead of running directly, see [docker-local-deployment.md](docker-local-deployment.md).

## Prerequisites

1. Install Python 3.13+ and [uv](https://docs.astral.sh/uv/)
2. Clone the repository and run `uv sync --group dev`

You also need:
- A microphone (the browser will request permission)
- Speakers or headphones
- A modern web browser (Chrome, Firefox, Edge)

## Setup

### 1. Obtain API Keys

#### Google Gemini

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create or select a project
3. Generate an API key

#### AWS Bedrock

Go to [https://aws-global.example.com/](https://aws-global.example.com/) and copy the AWS access keys. The page provides environment variable exports.

### 2. Configure Terminal Session

Export the credentials for the provider you want to use:

```bash
# Google Gemini
export GOOGLE_API_KEY="your-google-api-key"

# AWS Bedrock
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
```

Verify the credentials are set:

```bash
echo $GOOGLE_API_KEY
echo $AWS_ACCESS_KEY_ID
```

### 3. Start the Web Server

From the repository root:

```bash
uv run uvicorn fluentia.app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Alternatively, use the CLI entry point:

```bash
uv run python -m fluentia.main
```

### 4. Open the Web UI

Navigate to [http://localhost:8000](http://localhost:8000) in your browser.

## Using the Web Demo

### Select Provider

Use the **Provider** dropdown in the header to choose between Google Gemini and AWS Bedrock.

Changing the provider reconnects the WebSocket with the selected provider.

### Configure the Interview

Before starting audio, you can customize the interview settings in the form panel:

- **Agent Name**: The name the agent introduces itself as (default: Taylor)
- **Company Name**: The company mentioned during the interview
- **Questions**: Interview questions, one per line
- **Guidelines**: Additional instructions for the agent's behavior

These values are sent to the server as a `prompt_config` message when the WebSocket connects.

### Start Audio Mode

1. Click **Start Audio** to enable microphone input
2. Your browser will request microphone permission - allow it
3. Speak to begin the interview

The agent will:
1. Greet you and introduce itself
2. Ask each interview question in order
3. Listen to your responses and ask follow-up questions when appropriate
4. Thank you and end the interview after all questions are answered

### Text Mode

You can also type messages in the text input field and click **Send**.

### Event Console

The right panel shows a real-time event console:

- Upstream events (audio/text sent to the agent)
- Downstream events (agent responses, transcriptions, tool calls)
- Connection status changes

Click any event to expand and view the full JSON payload. Use the **Show audio** checkbox to include audio chunk events (disabled by default due to volume).

## Provider-Specific Options

### Google Gemini

The header includes checkboxes for native audio model features:

- **Proactivity**: Enables the model to respond without an explicit prompt
- **Affective Dialog**: Enables detection and adaptation to emotional cues

These options are sent as WebSocket query parameters and only work with native audio models (model name containing "native-audio").

### AWS Bedrock

No additional UI options. Uses Amazon Nova Sonic with the default voice and sample rate configured in `BedrockProviderConfig`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe (returns version and uptime) |
| `/ready` | GET | Readiness probe (shows provider availability) |
| `/api/agents` | GET | Lists available agents with their config fields |
| `/ws/{provider}/{user_id}/{session_id}` | WebSocket | Voice session endpoint |

For details on the WebSocket protocol, see the [WebSocket Protocol Reference](../reference/websocket-protocol.md).

## Architecture

The web demo consists of:

- **Frontend**: Static HTML/CSS/JS in `src/fluentia/static/`
- **Backend**: FastAPI application factory in `src/fluentia/app.py`
- **Session Manager**: WebSocket orchestration in `src/fluentia/session/manager.py`
- **Providers**: `src/fluentia/providers/google.py` and `src/fluentia/providers/bedrock/`

The frontend communicates with a single WebSocket endpoint. The URL path determines which provider handles the session:

```
/ws/google/{user_id}/{session_id}  -> GoogleProvider
/ws/bedrock/{user_id}/{session_id} -> BedrockProvider
```

## Troubleshooting

### WebSocket Connection Failed

If you see connection errors in the event console:

1. Check that the server is running in the terminal
2. Verify your API keys are set correctly
3. Check the server terminal for error messages

### No Audio Output

1. Check your browser's audio permissions
2. Ensure your speakers/headphones are working
3. Check the event console for audio events

### Google API Key Invalid

1. Verify `GOOGLE_API_KEY` is set: `echo $GOOGLE_API_KEY`
2. Ensure the API key has access to Gemini models
3. Restart the server after setting the environment variable

### AWS Credential Expiration

AWS session credentials expire after a few hours. If Bedrock connections fail:

1. Obtain fresh credentials from [https://aws-global.example.com/](https://aws-global.example.com/)
2. Export the new credentials in your terminal
3. Restart the server

### Browser Microphone Permission

If the browser does not prompt for microphone access:

1. Check browser settings for site permissions
2. Ensure you are accessing via `localhost` (not an IP address)
3. Try a different browser
