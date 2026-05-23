"""Authentication configuration for the smithy-based Bedrock SDK.

The default ``EnvironmentCredentialsResolver`` only reads AWS credentials from
environment variables and caches them forever. This module replaces it with a
``ChainedIdentityResolver`` that tries environment variables first and falls back
to the EC2 Instance Metadata Service (IMDS), enabling automatic credential rotation
on EC2 without a wrapper script.

Note on bearer token auth:
    The Bedrock bidirectional streaming API (used by Nova Sonic) requires SigV4 event
    signing for every event sent over the HTTP/2 stream. Bearer token auth (RFC 6750)
    only authenticates the initial HTTP request and provides no event signer, so the
    stream fails immediately when the server receives unsigned events. For this reason,
    bearer tokens are not supported for bidirectional streaming operations in the
    smithy-based SDK.
"""

import logging
from typing import Any

from aws_sdk_bedrock_runtime.config import Config
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
from smithy_aws_core.identity.imds import IMDSCredentialsResolver
from smithy_core.aio.identity import ChainedIdentityResolver
from smithy_http.aio.aiohttp import AIOHTTPClient

logger: logging.Logger = logging.getLogger(__name__)


def _create_sigv4_credentials_resolver() -> ChainedIdentityResolver[Any, Any]:
    """Create a chained credentials resolver for SigV4 authentication.

    Tries environment variables first (``AWS_ACCESS_KEY_ID``,
    ``AWS_SECRET_ACCESS_KEY``, ``AWS_SESSION_TOKEN``), then falls back to the
    EC2 Instance Metadata Service (IMDS) for automatic credential rotation.

    Returns:
        A ChainedIdentityResolver that checks env vars then IMDS.
    """
    env_resolver: EnvironmentCredentialsResolver = EnvironmentCredentialsResolver()
    http_client: AIOHTTPClient = AIOHTTPClient()
    imds_resolver: IMDSCredentialsResolver = IMDSCredentialsResolver(http_client)
    return ChainedIdentityResolver([env_resolver, imds_resolver])


def create_bedrock_config(region: str) -> Config:
    """Create a Bedrock runtime Config with SigV4 auth and chained credential resolver.

    Uses a ``ChainedIdentityResolver`` that tries environment variables first and
    falls back to the EC2 Instance Metadata Service (IMDS). This supports:

    - **Local development**: Set ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``,
      and optionally ``AWS_SESSION_TOKEN`` as environment variables.
    - **EC2 deployment**: Attach an IAM Instance Profile and credentials are
      resolved automatically via IMDS with transparent rotation.

    Args:
        region: AWS region for the Bedrock endpoint.

    Returns:
        A configured Config instance for BedrockRuntimeClient.
    """
    endpoint_uri: str = f"https://bedrock-runtime.{region}.amazonaws.com"
    credentials_resolver: ChainedIdentityResolver[Any, Any] = _create_sigv4_credentials_resolver()

    logger.info("Using SigV4 authentication with chained credential resolver for Bedrock")
    return Config(
        endpoint_uri=endpoint_uri,
        region=region,
        aws_credentials_identity_resolver=credentials_resolver,
    )
