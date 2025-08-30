"""
OpenAI Model Configuration Helper

Self-contained helper for configuring OpenAI models and Phoenix tracing.
This is a combined version from agentic_app_quickstart.examples.helpers
that works independently in the Week 3 container.
"""

from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
import os
from dotenv import load_dotenv
from phoenix.otel import register

load_dotenv()


def get_client():
    """Get configured OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_ENDPOINT")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please create a .env file with your API key. "
            "See .env.example for reference."
        )

    if not base_url:
        print("Warning: OPENAI_API_ENDPOINT not set, using default OpenAI endpoint")

    return AsyncOpenAI(api_key=api_key, base_url=base_url)


def get_model():
    """Get configured OpenAI model."""
    model = OpenAIChatCompletionsModel(
        model="gpt-5",
        openai_client=get_client(),
    )

    return model


def get_tracing_provider(project_name: str = "analytics_system"):
    """
    Initialize Phoenix tracing provider with proper configuration.

    Args:
        project_name: The Phoenix project name for organizing traces

    Returns:
        The configured tracer provider
    """
    phoenix_endpoint = os.getenv("PHOENIX_ENDPOINT")
    phoenix_api_key = os.getenv("PHOENIX_API_KEY")

    # Clean up any quotes from environment variables
    if phoenix_endpoint:
        phoenix_endpoint = phoenix_endpoint.strip('"\'')
    if phoenix_api_key:
        phoenix_api_key = phoenix_api_key.strip('"\'')

    print(f"🔭 Phoenix endpoint: {phoenix_endpoint}")
    print(f"🔑 Phoenix API key: {'***' if phoenix_api_key else 'None'}")

    tracing_provider = register(
        endpoint=phoenix_endpoint,
        project_name=project_name,
        protocol="http/protobuf",
        auto_instrument=True,
    )

    return tracing_provider
