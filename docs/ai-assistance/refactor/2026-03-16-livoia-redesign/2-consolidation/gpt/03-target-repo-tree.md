# Proposed Target Repository Tree

This target tree keeps migration practical, avoids unnecessary renaming churn, and supports the synthesized architecture.

```text
english-teacher-assistant/
├── .gitlab-ci.yml
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
│   ├── ai-assistance/                  # Preserved recursively from current repo
│   ├── discussions/
│   ├── guides/
│   ├── reference/
│   └── tutorials/
├── resources/
│   └── prompts/
│       └── interview_agent.txt         # Optional canonical prompt seed
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
│       │   ├── prompt_config.py
│       │   ├── session_models.py
│       │   └── ws_events.py
│       ├── services/
│       │   ├── __init__.py
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
│       ├── observability/
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   └── metrics.py
│       ├── web/
│       │   ├── static/
│       │   │   ├── index.html
│       │   │   ├── css/
│       │   │   └── js/
│       │   └── protocol/
│       │       ├── __init__.py
│       │       ├── client_messages.py
│       │       └── server_events.py
│       └── py.typed
└── tests/
    ├── conftest.py
    ├── fixtures/
    ├── unit/
    ├── integration/
    └── e2e/
```

## Notes

- Package name remains `livoia` to reduce migration friction and import churn.
- `docs/reference/` remains singular to match current repository conventions.
- Stage 1 tree intentionally excludes camera/image-specific modules.
- Tool runtime modules are deferred until the tool transparency/configurable-tools phase.
