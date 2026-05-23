"""Entry point for running the Fluentia application."""

import uvicorn

from fluentia.app import create_app
from fluentia.config import AppConfig


def main() -> None:
    """Run the Fluentia voice agent server."""
    config: AppConfig = AppConfig()
    app = create_app()
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
