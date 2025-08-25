"""
Phoenix Configuration for Week 2

Simple Phoenix setup that follows the helpers.py pattern.

Key concepts:
- Simple Phoenix tracing setup
- Uses existing helpers.py pattern
- Week 2 project organization

Use cases:
- Week 2 enhanced tracing setup
- Phoenix project configuration
- Connection testing
"""

import os
from dotenv import load_dotenv
from agentic_app_quickstart.examples.helpers import get_tracing_provider

# Load environment variables
load_dotenv()


def setup_week2_tracing(project_name: str = "week2_enhanced_system"):
    """
    Set up Phoenix tracing for Week 2 using the simple helpers pattern.

    Args:
        project_name: Phoenix project name for Week 2

    Returns:
        Configured tracer provider
    """
    phoenix_api_key = os.getenv("PHOENIX_API_KEY")
    phoenix_endpoint = os.getenv("PHOENIX_ENDPOINT")

    if not phoenix_api_key:
        print("⚠️  PHOENIX_API_KEY not set - traces will not be sent to Phoenix")
        print("   Add PHOENIX_API_KEY=your_key to .env file")

    if not phoenix_endpoint:
        print("ℹ️  Using default Phoenix endpoint")

    # Use the existing helpers pattern
    tracing_provider = get_tracing_provider(project_name)

    print(f"✅ Phoenix tracing configured for project: {project_name}")
    return tracing_provider


def test_connection():
    """Test Phoenix connection with simple trace."""
    try:
        from opentelemetry import trace

        # Set up tracing
        setup_week2_tracing("week2_test")

        # Create test trace
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("week2_connection_test") as span:
            span.set_attribute("test.status", "success")
            span.set_attribute("test.project", "week2_enhanced_system")

        print("✅ Test trace sent successfully!")
        print("🔍 Check Phoenix dashboard for 'week2_connection_test' trace")
        return True

    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    """Test Phoenix setup."""
    print("🚀 Week 2 Phoenix Setup")
    print("=" * 30)

    # Check environment
    api_key = os.getenv("PHOENIX_API_KEY")
    endpoint = os.getenv("PHOENIX_ENDPOINT")

    print(f"Phoenix API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"Phoenix Endpoint: {endpoint or 'Default'}")

    # Test connection
    print("\n🧪 Testing connection...")
    success = test_connection()

    if success:
        print("\n🎉 Week 2 Phoenix setup complete!")
    else:
        print("\n📋 Setup needed:")
        print("  1. Add PHOENIX_API_KEY to .env file")
        print("  2. Optionally set PHOENIX_ENDPOINT")
        print("  3. Run: python -m week_2.solution.config.phoenix_config")
