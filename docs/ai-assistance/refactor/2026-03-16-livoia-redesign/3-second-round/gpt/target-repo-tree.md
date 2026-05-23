# Proposed Target Repository Tree

The new repository should preserve documentation conventions while organizing runtime code for stage 1 delivery and future multi-agent growth.

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
│   │   ├── about-avature.md
│   │   ├── technical-writing-style-guide.md
│   │   ├── code-style-guide.md
│   │   ├── test-development-guide.md
│   │   └── commit-message-guide.md
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
│       ├── interviewer.md
│       ├── scheduler.md                 # Future profile prompt seed
│       └── avature-assistant.md         # Future profile prompt seed
├── src/
│   └── livoia/
│       ├── __init__.py
│       ├── app/
│       │   ├── __init__.py
│       │   ├── create_app.py
│       │   ├── routes_http.py
│       │   └── routes_ws.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── agent_profile.py
│       │   ├── prompt_config.py
│       │   ├── session_models.py
│       │   └── events.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── agent_profile_service.py
│       │   ├── prompt_rendering_service.py
│       │   ├── provider_selection_service.py
│       │   └── realtime_session_service.py
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── google/
│       │   │   ├── __init__.py
│       │   │   └── adapter.py
│       │   └── bedrock/
│       │       ├── __init__.py
│       │       ├── adapter.py
│       │       └── client.py
│       ├── web/
│       │   ├── static/
│       │   │   ├── index.html
│       │   │   ├── css/
│       │   │   └── js/
│       │   └── protocol/
│       │       ├── __init__.py
│       │       ├── client_messages.py
│       │       └── server_events.py
│       ├── observability/
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   └── metrics.py
│       └── py.typed
└── tests/
    ├── conftest.py
    ├── fixtures/
    ├── unit/
    ├── integration/
    └── e2e/
```

## Notes

- Keep package name `livoia` to reduce migration churn.
- `docs/reference/` remains singular to match current conventions.
- Stage 1 implementation enables only Interviewer profile.
- Future profiles (`scheduler`, `avature-assistant`) are represented by contracts and prompt seeds, but disabled.
- Camera/image modules are intentionally absent from stage 1 tree.
