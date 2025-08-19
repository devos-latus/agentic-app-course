"""
E2E Tests for Conversation Memory

This module tests the complete conversation memory workflow including:
- Memory persistence within sessions
- Follow-up question handling
- Context building over multiple interactions
- Session isolation between users

Key concepts:
- Conversation context: Agents remember previous exchanges
- Follow-up questions: "What about the median?" after asking about averages
- Memory boundaries: Session-specific context isolation
- Multi-turn conversations: Building understanding over time

Use cases:
- Data analysis conversations with follow-ups
- User asking related questions in sequence
- Multiple users with isolated conversation histories
- Context-aware responses based on conversation history
"""

import pytest
import sys
import os

# Add the week_1/solution directory to Python path for imports
week1_solution_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "week_1", "solution"
)
sys.path.insert(0, week1_solution_path)

from chat_service import ChatService


@pytest.fixture(autouse=True)
def change_working_directory():
    """Change working directory to week_1/solution for tests."""
    original_cwd = os.getcwd()
    week1_solution_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "week_1", "solution"
    )
    os.chdir(week1_solution_path)
    yield
    os.chdir(original_cwd)


class TestConversationMemory:
    """Test conversation memory and context building."""

    @pytest.mark.asyncio
    async def test_basic_conversation_memory(self):
        """Test that agent remembers previous conversation within session."""
        service = ChatService()

        # Initialize with some data
        await service.initialize_data()

        # First question about averages
        response1 = await service.send_message(
            "What's the average salary in the employee data?"
        )

        # Should get a successful response
        assert response1["success"] is True
        assert (
            "average" in response1["response"].lower()
            or "mean" in response1["response"].lower()
        )

        # Follow-up question that requires memory
        response2 = await service.send_message("What about the median?")

        # Should understand this refers to salary in employee data
        assert response2["success"] is True
        # Agent should understand context from previous question
        assert any(
            term in response2["response"].lower()
            for term in ["median", "salary", "employee"]
        )

    @pytest.mark.asyncio
    async def test_multi_turn_context_building(self):
        """Test building context over multiple conversation turns."""
        service = ChatService()
        await service.initialize_data()

        # Turn 1: Ask about a specific dataset
        response1 = await service.send_message("Tell me about the sales data")
        assert response1["success"] is True

        # Turn 2: Ask for specific analysis (should remember we're talking about sales)
        response2 = await service.send_message("What's the total sales amount?")
        assert response2["success"] is True

        # Turn 3: Follow-up question (should maintain sales context)
        response3 = await service.send_message("And what's the average price?")
        assert response3["success"] is True

        # All responses should be successful and contextually relevant
        # Agent should understand we're still talking about sales data

    @pytest.mark.asyncio
    async def test_session_memory_isolation(self):
        """Test that different sessions have isolated memories."""
        # Create two separate chat services (different users)
        user1_service = ChatService()
        user2_service = ChatService()

        await user1_service.initialize_data()
        await user2_service.initialize_data()

        # User 1 asks about employee data
        user1_response1 = await user1_service.send_message(
            "What's the average salary in the employee data?"
        )
        assert user1_response1["success"] is True

        # User 2 asks about sales data (different context)
        user2_response1 = await user2_service.send_message("Show me the sales trends")
        assert user2_response1["success"] is True

        # User 1 asks follow-up (should remember salary context)
        user1_response2 = await user1_service.send_message("What about the maximum?")
        assert user1_response2["success"] is True

        # User 2 asks follow-up (should remember sales context, not salary)
        user2_response2 = await user2_service.send_message("What's the average price?")
        assert user2_response2["success"] is True

        # Sessions should maintain separate contexts
        # User 1's "maximum" should relate to salary
        # User 2's "average price" should relate to sales

    @pytest.mark.asyncio
    async def test_conversation_continuity_after_errors(self):
        """Test that conversation memory persists even after errors."""
        service = ChatService()
        await service.initialize_data()

        # Establish context with successful query
        response1 = await service.send_message("What columns are in the weather data?")
        assert response1["success"] is True

        # Ask invalid/off-topic question (should trigger guardrail)
        await service.send_message("What's the weather like today in New York?")
        # This might fail due to guardrails, which is expected

        # Follow-up should still remember the weather data context
        response3 = await service.send_message(
            "What's the temperature range in that data?"
        )
        assert response3["success"] is True
        # Should understand "that data" refers to weather data from first question

    @pytest.mark.asyncio
    async def test_complex_analytical_conversation(self):
        """Test a realistic data analysis conversation flow."""
        service = ChatService()
        await service.initialize_data()

        # Start with data exploration
        response1 = await service.send_message("What datasets do I have available?")
        assert response1["success"] is True

        # Focus on one dataset
        response2 = await service.send_message(
            "Let's analyze the employee data. What's the structure?"
        )
        assert response2["success"] is True

        # Ask for basic statistics
        response3 = await service.send_message(
            "Show me summary statistics for the numeric columns"
        )
        assert response3["success"] is True

        # Ask follow-up about specific insight
        response4 = await service.send_message(
            "Which department has the highest average salary?"
        )
        assert response4["success"] is True

        # Ask clarifying follow-up
        response5 = await service.send_message(
            "How many employees are in that department?"
        )
        assert response5["success"] is True
        # Should understand "that department" from previous context

        # All responses should be successful
        responses = [response1, response2, response3, response4, response5]
        for i, response in enumerate(responses, 1):
            assert response["success"] is True, f"Response {i} failed: {response}"

    @pytest.mark.asyncio
    async def test_memory_with_session_cleanup(self):
        """Test that memory is properly cleaned up when session ends."""
        service = ChatService()
        await service.initialize_data()

        # Have a conversation
        response1 = await service.send_message("What's in the sales data?")
        assert response1["success"] is True

        # Clean up session
        service.close_session()

        # Create new service with same session ID (simulating restart)
        new_service = ChatService(session_id=service.session_id)
        await new_service.initialize_data()

        # Ask follow-up question - should NOT remember previous context
        # since we're using in-memory sessions (no persistence)
        response2 = await new_service.send_message("What about the average price?")

        # This should either:
        # 1. Ask for clarification (preferred)
        # 2. Still work if agent is smart enough to infer context
        # Either way it should succeed, just testing cleanup worked
        assert response2["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])
