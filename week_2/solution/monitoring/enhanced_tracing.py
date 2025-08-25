"""
Enhanced Phoenix Tracing for Week 2 - Clean Hierarchical Traces

Creates well-organized, hierarchical traces that group auto-instrumentation
under meaningful business context spans.

Key concepts:
- Hierarchical span organization
- Business context as parent spans
- Auto-instrumentation as child spans
- Clean Phoenix dashboard experience

Use cases:
- Production monitoring with clear trace hierarchy
- Business intelligence on conversation patterns
- Performance analysis with proper context
"""

from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from agentic_app_quickstart.examples.helpers import get_tracing_provider


def setup_enhanced_tracing(project_name: str = "analytics_system"):
    """
    Enhanced Phoenix tracing setup with proper configuration.

    Args:
        project_name: Phoenix project name

    Returns:
        Tracer provider
    """
    return get_tracing_provider(project_name)


@asynccontextmanager
async def trace_user_conversation(
    session_id: str, message_number: int, user_input: str
):
    """
    Create a top-level conversation span that groups all operations.

    This creates a clean hierarchy:
    📱 User Conversation (SERVER)
    ├── 🤖 Agent Processing (INTERNAL)
    │   ├── 🔍 LLM Call (auto-instrumented)
    │   ├── 🛠️ Tool Execution (auto-instrumented)
    │   └── 📊 Data Analysis (auto-instrumented)
    └── ✅ Response Generation (INTERNAL)

    Args:
        session_id: Session identifier
        message_number: Message number in conversation
        user_input: User's input message
    """
    tracer = trace.get_tracer(__name__)

    # Create unique span name with session prefix to avoid duplicates
    session_short = session_id[-8:]  # Last 8 chars of session ID
    span_name = f"conversation_{session_short}_{message_number}"

    with (
        tracer.start_as_current_span(
            span_name,
            kind=SpanKind.SERVER,  # This is the entry point
            attributes={
                "conversation.session_id": session_id,
                "conversation.message_number": message_number,
                "conversation.type": "user_interaction",
                "conversation.input_length": len(user_input),
                "conversation.input_preview": user_input[:100] + "..."
                if len(user_input) > 100
                else user_input,
                "service.name": "csv_analytics_agent",
                "service.version": "2.0.0",
                "span.kind": "conversation",
                "otel.library.name": "enhanced_chat_service",
            },
        ) as conversation_span
    ):
        try:
            yield conversation_span
            conversation_span.set_status(
                Status(StatusCode.OK, "Conversation completed successfully")
            )

        except Exception as e:
            conversation_span.set_status(
                Status(StatusCode.ERROR, f"Conversation failed: {str(e)}")
            )
            conversation_span.set_attribute("error.type", type(e).__name__)
            conversation_span.set_attribute("error.message", str(e))
            raise


@asynccontextmanager
async def trace_agent_processing(parent_span, agent_name: str, operation: str):
    """
    Create a child span for agent processing operations.

    Args:
        parent_span: Parent conversation span
        agent_name: Name of the processing agent
        operation: Type of operation being performed
    """
    tracer = trace.get_tracer(__name__)

    span_name = f"agent_processing_{operation}"

    with tracer.start_as_current_span(
        span_name,
        kind=SpanKind.INTERNAL,
        attributes={
            "agent.name": agent_name,
            "agent.operation": operation,
            "processing.type": "agent_execution",
        },
    ) as processing_span:
        try:
            yield processing_span
            processing_span.set_status(
                Status(StatusCode.OK, f"Agent {agent_name} completed {operation}")
            )

        except Exception as e:
            processing_span.set_status(
                Status(StatusCode.ERROR, f"Agent processing failed: {str(e)}")
            )
            processing_span.set_attribute("error.agent", agent_name)
            processing_span.set_attribute("error.operation", operation)
            raise


def add_conversation_result(
    span,
    success: bool,
    response: str,
    agent_name: str,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Add conversation result information to the span.

    Args:
        span: OpenTelemetry span
        success: Whether the conversation was successful
        response: Agent response text
        agent_name: Name of responding agent
        metadata: Additional metadata to include
    """
    if not span:
        return

    # Core result attributes
    span.set_attribute("conversation.success", success)
    span.set_attribute("conversation.responding_agent", agent_name)
    span.set_attribute("conversation.response_length", len(response))

    # Safe response preview
    response_preview = response[:200] + "..." if len(response) > 200 else response
    span.set_attribute("conversation.response_preview", response_preview)

    # Add metadata if provided
    if metadata:
        for key, value in metadata.items():
            span.set_attribute(f"conversation.{key}", str(value))

    # Business intelligence attributes
    span.set_attribute("business.interaction_type", _classify_interaction(response))
    span.set_attribute("business.response_category", _classify_response(response))


def _classify_interaction(response: str) -> str:
    """Classify the type of interaction based on response content."""
    response_lower = response.lower()

    if any(
        word in response_lower for word in ["chart", "plot", "graph", "visualization"]
    ):
        return "visualization"
    elif any(
        word in response_lower
        for word in ["analysis", "statistics", "calculate", "average"]
    ):
        return "analysis"
    elif any(
        word in response_lower for word in ["error", "cannot", "unable", "failed"]
    ):
        return "error_handling"
    elif any(
        word in response_lower for word in ["table", "columns", "data", "dataset"]
    ):
        return "data_exploration"
    else:
        return "general_conversation"


def _classify_response(response: str) -> str:
    """Classify the response category for business intelligence."""
    response_lower = response.lower()

    if "successfully" in response_lower or "completed" in response_lower:
        return "success"
    elif "error" in response_lower or "failed" in response_lower:
        return "error"
    elif "?" in response or "clarify" in response_lower:
        return "clarification_needed"
    else:
        return "informational"


# Convenience function for backward compatibility
trace_conversation = trace_user_conversation
