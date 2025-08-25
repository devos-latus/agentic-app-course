"""
Enhanced ChatService for Week 2 Phoenix Tracing

This module provides enhanced tracing capabilities that extend the existing
Week 1 ChatService without modifying its core functionality.

Key concepts:
- Extends existing ChatService with custom Phoenix spans
- Follows Phoenix best practices for observability
- Adds conversation-level trace grouping
- Business logic insights beyond auto-instrumentation

Use cases:
- Production monitoring of agentic systems
- Performance analysis and debugging
- Business intelligence on conversation patterns
- Cost and usage tracking
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add Week 1 solution to path
week1_path = Path(__file__).parent.parent.parent.parent / "week_1" / "solution"
sys.path.insert(0, str(week1_path))

from chat_service import ChatService

# Import Week 2 enhanced tracing (separated concerns)
from monitoring.enhanced_tracing import (
    trace_user_conversation,
    add_conversation_result,
    setup_enhanced_tracing,
)

# Setup tracing for this module
setup_enhanced_tracing("analytics_system")


class EnhancedChatService(ChatService):
    """
    Enhanced ChatService that adds custom Phoenix spans to Week 1 implementation.

    This follows Phoenix best practices by:
    - Leveraging existing auto-instrumentation as foundation
    - Adding custom spans for business logic insights
    - Maintaining trace context consistency
    - Preserving all original functionality
    """

    def __init__(self, session_id=None):
        """Initialize with enhanced tracing capabilities."""
        super().__init__(session_id)
        self.conversation_count = 0

        print(f"🔍 Enhanced Phoenix tracing enabled for session: {self.session_id}")

    async def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a message to the agent system with enhanced tracing.

        Args:
            message: User's message

        Returns:
            Dict with response and metadata (same as Week 1)
        """
        self.conversation_count += 1

        # Use enhanced hierarchical tracing
        async with trace_user_conversation(
            self.session_id, self.conversation_count, message
        ) as span:
            # Call original implementation (which has auto-instrumentation)
            # The auto-instrumented spans will now be children of our conversation span
            result = await super().send_message(message)

            # Add response info to span with enhanced metadata
            if span:
                add_conversation_result(
                    span,
                    result.get("success", False),
                    result.get("response", ""),
                    result.get("agent_name", "unknown"),
                    metadata={
                        "conversation_count": self.conversation_count,
                        "session_type": "enhanced_chat",
                        "data_loaded": self._data_loaded,
                    },
                )

            return result

    # All other methods inherit from ChatService with auto-instrumentation

    def get_session_analytics(self) -> dict:
        """
        Get basic session analytics (Week 2 enhancement).

        Returns:
            Dict with basic session statistics
        """
        return {
            "session_id": self.session_id,
            "conversation_count": self.conversation_count,
            "data_loaded": self._data_loaded,
            "enhanced_tracing_enabled": True,
            "phoenix_project": "analytics_system",
        }


# Convenience functions for backward compatibility
async def initialize_enhanced_chat_service(
    session_id: Optional[str] = None,
) -> "EnhancedChatService":
    """
    Initialize and return an EnhancedChatService instance with data loaded.

    Args:
        session_id: Optional session ID. If None, generates unique UUID.

    Returns:
        Initialized EnhancedChatService instance
    """
    service = EnhancedChatService(session_id)
    await service.initialize_data()
    return service
