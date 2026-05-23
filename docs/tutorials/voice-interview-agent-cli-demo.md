# Voice Interview Agent CLI Demo (Legacy)

> **Note**: This tutorial references the legacy CLI script in `scripts/voice_interview_agent_demo.py`, which is part of the original proof-of-concept. The current production system uses a web-based interface. See [voice-interview-agent-web-demo.md](voice-interview-agent-web-demo.md) for the recommended approach, or [docker-local-deployment.md](docker-local-deployment.md) for Docker deployment.

This tutorial describes how to run the voice interview agent demo via the command-line script. The demo conducts candidate interviews using Amazon Nova Sonic for real-time speech processing.

## Prerequisites

Complete the installation steps in the [README.md](../../README.md):

1. Install Python 3.13+ and [uv](https://docs.astral.sh/uv/)
2. Install PortAudio system dependency (required for the CLI script's microphone access)
3. Clone the repository and run `uv sync --group dev`

You also need:
- A microphone and speakers (or headphones)
- AWS credentials with access to Amazon Bedrock in `us-east-1`

## Setup

### 1. Obtain AWS Credentials

Go to [https://aws-global.example.com/](https://aws-global.example.com/) and copy the AWS access keys. The page provides environment variable exports in this format:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
```

### 2. Configure Terminal Session

Open a new terminal session and paste the exported environment variables. These credentials are session-specific and will expire after a few hours.

Verify the credentials are set:

```bash
echo $AWS_ACCESS_KEY_ID
```

### 3. Create Questions File

Create a text file containing interview questions, one per line. Empty lines are ignored.

Example file `interview_questions.txt`:

```text
Tell us about the size of team you have previously supported.
How would you rate your proficiency with Microsoft Excel - for example, beginner, intermediate, or advanced? Can you tell us about the type of reports you have managed or created and how this supported your wider team and/or business?
Can you describe a challenging situation you faced in a previous role and how you handled it?
```

Requirements:
- UTF-8 encoding
- One question per line
- At least one non-empty line

## Running the Demo

Execute the script with the path to your questions file:

```bash
uv run python scripts/voice_interview_agent_demo.py --questions interview_questions.txt
```

With a company name:

```bash
uv run python scripts/voice_interview_agent_demo.py \
    --questions interview_questions.txt \
    --company "Mercadona"
```

**Important**: The agent waits for you to speak first. Say "Hello" or introduce yourself to start the interview.

Once you speak, the agent (named Taylor) will:
1. Greet you and introduce itself
2. Ask each question in order
3. Listen to your responses and ask follow-up questions when appropriate
4. Thank you and end the interview after all questions are answered

Press **Enter** to stop the session at any time.

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--questions` | (required) | Path to text file with interview questions |
| `--company` | "the company" | Company name used in the introduction |
| `--language` | auto-detect | Language code for input audio (e.g., `en-US`, `es-ES`) |
| `--voice` | `matthew` | Voice for speech synthesis (`matthew`, `ruth`, `amy`, `gregory`) |
| `--region` | `us-east-1` | AWS region for Bedrock |
| `--debug` | disabled | Enable verbose logging |

## Troubleshooting

### Language Detection Issues

If the agent responds in the wrong language, specify the input language explicitly:

```bash
uv run python scripts/voice_interview_agent_demo.py \
    --questions interview_questions.txt \
    --language en-US
```

### ALSA Warnings on Linux

Messages like `ALSA lib pcm.c:2664:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.front` are harmless warnings about audio hardware configurations. They do not affect functionality.

### Credential Expiration

AWS session credentials expire after a few hours. If you see authentication errors, obtain fresh credentials from [https://aws-global.example.com/](https://aws-global.example.com/).

## Example Session

```
$ uv run python scripts/voice_interview_agent_demo.py \
    --questions interview_questions.txt \
    --company "Mercadona"

2024-01-28 21:30:00 - __main__ - INFO - Loading questions from: interview_questions.txt
2024-01-28 21:30:00 - __main__ - INFO - Loaded 3 interview questions
2024-01-28 21:30:00 - __main__ - INFO - Interview agent ready! The interviewer will greet you shortly...
2024-01-28 21:30:00 - __main__ - INFO - Press Enter to end the interview.
[ALSA warnings...]
2024-01-28 21:30:01 - __main__ - INFO - ASSISTANT: Hello! I'm Taylor, and I'll be conducting your interview today for Mercadona...
```
