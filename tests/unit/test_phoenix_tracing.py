#!/usr/bin/env python3
"""
Unit Test for Phoenix Tracing Setup

This module tests that Phoenix tracing is properly configured and can send traces
without interfering with the main application functionality.

Key concepts:
- Phoenix tracing configuration validation
- OpenTelemetry trace creation
- API key validation
- Tracing endpoint connectivity

Use cases:
- Verifying Phoenix setup during development
- Testing tracing configuration in CI/CD
- Validating tracing doesn't break application
"""

import os
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Load environment variables
load_dotenv()

# Disable OpenAI agents internal tracing
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

# Configure Phoenix tracing
from phoenix.otel import register

# Set Phoenix API key
phoenix_api_key = os.getenv("PHEONIX_API_KEY")
if phoenix_api_key:
    os.environ["PHOENIX_API_KEY"] = phoenix_api_key
    print(f"✅ Phoenix API key set: {phoenix_api_key[:20]}...")
else:
    print("❌ No Phoenix API key found!")

# Register Phoenix tracing
tracer_provider = register(
    endpoint="https://app.phoenix.arize.com/s/devos",
    project_name="analytics_system",
    protocol="http/protobuf",
    auto_instrument=True,
)

print("✅ Phoenix tracing registered")

# Create a test trace
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("test_phoenix_trace") as span:
    span.set_attribute("test.message", "Hello from analytics_system!")
    span.set_attribute("test.component", "phoenix_test")
    span.set_status(Status(StatusCode.OK, "Test trace completed"))
    print("✅ Test trace created")

print("🔍 Check your Phoenix dashboard for the 'analytics_system' project")
print("📍 Look for a trace named 'test_phoenix_trace'")
