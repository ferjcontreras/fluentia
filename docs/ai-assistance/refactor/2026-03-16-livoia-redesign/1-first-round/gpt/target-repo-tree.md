# Proposed Target Repository Tree

The new production repository should keep the current documentation shape, preserve AI-assistance content, and organize runtime code around the stage 1 web product.

```text
english-teacher-assistant/
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── Dockerfile
├── README.md
├── pyproject.toml
├── tox.ini
├── uv.lock
├── check_code.sh
├── docker/
│   ├── entrypoint.sh
│   └── healthcheck.sh
├── docs/
│   ├── ai-assistance/                  # Recursively preserved from current repo
│   │   ├── HELP.md
│   │   ├── analysis/
│   │   ├── code-review/
│   │   ├── debug/
│   │   ├── design/
│   │   ├── feature/
│   │   └── refactor/
│   ├── discussions/
│   ├── guides/
│   │   ├── about-avature.md            # Carry over
│   │   ├── technical-writing-style-guide.md  # Carry over
│   │   ├── code-style-guide.md         # Re-version for new repo
│   │   ├── test-development-guide.md   # Re-version for new repo
│   │   └── commit-message-guide.md     # Re-version for new repo
│   ├── reference/
│   │   ├── architecture-overview.md
│   │   ├── configuration-reference.md
│   │   └── websocket-event-protocol.md
│   └── tutorials/
│       ├── local-development.md
│       ├── run-web-demo.md
│       └── provider-setup.md
├── resources/
│   └── prompts/
│       └── interview_agent.txt
├── src/
│   └── livoia_prod/
│       ├── __init__.py
│       ├── app/
│       │   ├── create_app.py
│       │   ├── routes_http.py
│       │   └── routes_ws.py
│       ├── domain/
│       │   ├── session_models.py
│       │   ├── prompt_config.py
│       │   └── events.py
│       ├── services/
│       │   ├── realtime_session_service.py
│       │   ├── prompt_rendering_service.py
│       │   └── provider_selection_service.py
│       ├── providers/
│       │   ├── base.py
│       │   ├── google_bidi_adapter.py
│       │   └── bedrock_bidi_adapter.py
│       ├── web/
│       │   ├── static/
│       │   │   ├── index.html
│       │   │   ├── css/
│       │   │   └── js/
│       │   └── protocol/
│       │       ├── client_messages.py
│       │       └── server_events.py
│       ├── observability/
│       │   ├── logging.py
│       │   └── metrics.py
│       └── config/
│           ├── settings.py
│           └── env_schema.py
└── tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    └── fixtures/
```

## Notes

- `docs/reference/` remains singular to match current repository structure.
- Provider SDK-facing code is isolated under `src/livoia_prod/providers/`.
- Stage 1 tree excludes camera/image modules by design.
