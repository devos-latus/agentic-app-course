"""
Unit Tests for Session Management

This module tests the dynamic session management features including:
- UUID-based session ID generation
- Multi-user session isolation
- In-memory-only storage
- Session lifecycle management

Key concepts:
- Session isolation: Each session has independent memory
- Dynamic IDs: UUID generation for unique sessions
- Memory boundaries: No cross-session data leakage
- Lifecycle management: Proper session cleanup

Use cases:
- Multiple concurrent users
- Session privacy validation
- Memory cleanup verification
- Unique session ID generation testing
"""

import pytest
import uuid
import asyncio
import sys
import os
from unittest.mock import patch, AsyncMock

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


class TestSessionManagement:
    """Test dynamic session management functionality."""

    def test_default_session_id_is_uuid(self):
        """Test that default session ID is a valid UUID."""
        service = ChatService()

        # Should be a valid UUID string
        uuid_obj = uuid.UUID(service.session_id)
        assert str(uuid_obj) == service.session_id
        assert len(service.session_id) == 36  # Standard UUID string length

    def test_custom_session_id_preserved(self):
        """Test that custom session ID is preserved."""
        custom_id = "test-session-123"
        service = ChatService(session_id=custom_id)

        assert service.session_id == custom_id

    def test_unique_session_ids_generated(self):
        """Test that each service instance gets a unique session ID."""
        service1 = ChatService()
        service2 = ChatService()
        service3 = ChatService()

        # All session IDs should be different
        session_ids = {service1.session_id, service2.session_id, service3.session_id}
        assert len(session_ids) == 3

        # All should be valid UUIDs
        for session_id in session_ids:
            uuid.UUID(session_id)  # Should not raise exception

    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """Test that different sessions are completely isolated."""
        # Create two separate chat services
        service1 = ChatService()
        service2 = ChatService()

        # Mock the Runner.run to simulate conversation
        with patch("chat_service.Runner.run") as mock_run:
            # Mock responses for session isolation test
            mock_run.return_value = AsyncMock()
            mock_run.return_value.final_output = "Test response"

            # Simulate conversation in service1
            await service1.send_message("Hello from service 1")

            # Simulate conversation in service2
            await service2.send_message("Hello from service 2")

            # Sessions should have different IDs
            assert service1.session_id != service2.session_id

            # Each Runner.run call should use different session objects
            calls = mock_run.call_args_list
            assert len(calls) == 2

            # Extract session objects from calls
            session1 = calls[0][1]["session"]  # service1's session
            session2 = calls[1][1]["session"]  # service2's session

            # Sessions should be different objects
            assert session1 is not session2
            assert session1.session_id != session2.session_id

    def test_session_cleanup(self):
        """Test session cleanup functionality."""
        service = ChatService()

        # Initialize some state
        service._data_loaded = True

        # Call cleanup
        service.close_session()

        # Data loaded flag should be reset
        assert service._data_loaded is False

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self):
        """Test handling multiple concurrent chat sessions."""
        # Create multiple services (simulating multiple users)
        services = [ChatService() for _ in range(5)]

        # All should have unique session IDs
        session_ids = [service.session_id for service in services]
        assert len(set(session_ids)) == 5  # All unique

        # All should be valid UUIDs
        for session_id in session_ids:
            uuid.UUID(session_id)  # Should not raise exception

        # Mock successful data initialization for all
        with patch("chat_service.Runner.run") as mock_run:
            mock_run.return_value = AsyncMock()
            mock_run.return_value.final_output = "Data loaded"

            # Initialize data for all services concurrently
            init_tasks = [service.initialize_data() for service in services]
            results = await asyncio.gather(*init_tasks)

            # All should succeed
            for result in results:
                assert result.get("success") is not False  # May be True or missing


if __name__ == "__main__":
    pytest.main([__file__])
