"""
End-to-end test for Week 2 Enhanced CSV analytics workflow with Phoenix tracing.

Tests the complete integration using EnhancedChatService to generate comprehensive
Phoenix traces and validate enhanced monitoring capabilities.
"""

import pytest
import os
import tempfile
import sys
import warnings
from pathlib import Path

# Add the Week 2 solution directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "week_2" / "solution"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "week_1" / "solution"))

# Suppress Pydantic deprecation warnings from agents library
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from enhanced_chat_service import EnhancedChatService, initialize_enhanced_chat_service
import tools


class TestWeek2EnhancedWorkflow:
    """Test the Week 2 enhanced CSV analytics workflow with Phoenix tracing."""

    def setup_method(self):
        """Set up test environment with sample data."""
        self.temp_dir = tempfile.mkdtemp()

        # Create comprehensive test CSV files for thorough testing
        self.sales_csv = os.path.join(self.temp_dir, "sales_data.csv")
        with open(self.sales_csv, "w") as f:
            f.write("""date,product,price,quantity,customer_state,sales_rep
2024-01-15,Laptop,999.99,2,CA,Alice Johnson
2024-01-16,Mouse,29.99,5,NY,Bob Smith
2024-01-17,Keyboard,79.99,1,TX,Carol Davis
2024-01-18,Monitor,299.99,3,FL,David Wilson
2024-01-19,Tablet,599.99,1,CA,Alice Johnson
2024-01-20,Headphones,149.99,4,NY,Bob Smith""")

        self.employees_csv = os.path.join(self.temp_dir, "employee_performance.csv")
        with open(self.employees_csv, "w") as f:
            f.write("""name,department,salary,hire_date,performance_score,manager
Alice Johnson,Sales,85000,2022-03-15,4.5,Sarah Connor
Bob Smith,Sales,65000,2021-07-20,4.2,Sarah Connor
Carol Davis,Engineering,92000,2020-01-10,4.8,John Doe
David Wilson,Marketing,75000,2023-01-05,4.1,Jane Smith""")

        self.inventory_csv = os.path.join(self.temp_dir, "inventory_levels.csv")
        with open(self.inventory_csv, "w") as f:
            f.write("""product,category,stock_level,reorder_point,supplier,last_updated
Laptop,Electronics,25,10,TechCorp,2024-01-20
Mouse,Electronics,150,50,TechCorp,2024-01-20
Keyboard,Electronics,75,25,TechCorp,2024-01-19
Monitor,Electronics,40,15,DisplayCorp,2024-01-18
Tablet,Electronics,30,12,TechCorp,2024-01-20""")

    @pytest.mark.asyncio
    async def test_enhanced_service_initialization(self):
        """Test that EnhancedChatService initializes with tracing enabled."""
        service = await initialize_enhanced_chat_service()

        # Verify enhanced service is properly initialized
        assert service is not None
        assert hasattr(service, "conversation_count")
        assert service.conversation_count == 0

        # Check analytics functionality
        analytics = service.get_session_analytics()
        assert analytics["enhanced_tracing_enabled"] is True
        assert analytics["phoenix_project"] == "analytics_system"
        assert analytics["conversation_count"] == 0

    @pytest.mark.asyncio
    async def test_enhanced_data_loading_with_tracing(self):
        """Test data loading with enhanced tracing spans."""
        service = EnhancedChatService()

        # Load test data (this will create Phoenix traces)
        tools._discover_and_load_csv_files(self.temp_dir)

        # Initialize the service
        await service.initialize_data()

        # Verify data loading worked
        analytics = service.get_session_analytics()
        assert analytics["data_loaded"] is True

    @pytest.mark.asyncio
    async def test_enhanced_conversation_flow_tracing(self):
        """Test multiple conversation turns with enhanced tracing."""
        service = EnhancedChatService()

        # Load test data
        tools._discover_and_load_csv_files(self.temp_dir)
        await service.initialize_data()

        # Test multiple conversation turns to generate rich traces
        conversations = [
            "What datasets are available for analysis?",
            "Show me the structure of the sales_data table",
            "What are the total sales by state?",
            "Who are the top performing sales representatives?",
            "Create a visualization of sales by product",
            "What's the average performance score by department?",
            "Show me inventory levels below reorder points",
            "Analyze the relationship between salary and performance",
        ]

        for i, message in enumerate(conversations):
            result = await service.send_message(message)

            # Verify each conversation was processed
            assert result is not None
            assert isinstance(result, dict)

            # Check conversation count increments
            analytics = service.get_session_analytics()
            assert analytics["conversation_count"] == i + 1

    @pytest.mark.asyncio
    async def test_enhanced_error_handling_with_tracing(self):
        """Test error scenarios with enhanced tracing."""
        service = EnhancedChatService()

        # Load test data
        tools._discover_and_load_csv_files(self.temp_dir)
        await service.initialize_data()

        # Test various error scenarios to generate error traces
        error_scenarios = [
            "Show me data from nonexistent_table",
            "Calculate the square root of the color column",
            "Create a pie chart of the weather data",
            "What's the correlation between unicorns and rainbows?",
            "",  # Empty input
        ]

        for message in error_scenarios:
            if message:  # Skip empty message for this test
                result = await service.send_message(message)
                # Should handle errors gracefully
                assert result is not None

    @pytest.mark.asyncio
    async def test_enhanced_analytics_and_session_tracking(self):
        """Test enhanced analytics and session tracking features."""
        service = EnhancedChatService()

        # Load test data
        tools._discover_and_load_csv_files(self.temp_dir)
        await service.initialize_data()

        # Send several messages
        messages = [
            "What data do we have?",
            "Show me sales statistics",
            "Create a chart of employee performance",
        ]

        for message in messages:
            await service.send_message(message)

        # Test analytics functionality
        analytics = service.get_session_analytics()

        # Verify analytics data
        assert analytics["conversation_count"] == len(messages)
        assert analytics["enhanced_tracing_enabled"] is True
        assert analytics["phoenix_project"] == "analytics_system"
        assert analytics["data_loaded"] is True
        assert "session_id" in analytics

    @pytest.mark.asyncio
    async def test_enhanced_memory_persistence_with_tracing(self):
        """Test conversation memory with enhanced tracing."""
        service = EnhancedChatService()

        # Load test data
        tools._discover_and_load_csv_files(self.temp_dir)
        await service.initialize_data()

        # Test memory persistence across multiple interactions
        result1 = await service.send_message("What datasets do we have available?")
        result2 = await service.send_message(
            "Tell me more about the first dataset you mentioned"
        )
        result3 = await service.send_message(
            "Can you show me some statistics from that table?"
        )

        # All interactions should succeed
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

        # Verify conversation count
        analytics = service.get_session_analytics()
        assert analytics["conversation_count"] == 3

    @pytest.mark.asyncio
    async def test_enhanced_visualization_requests_with_tracing(self):
        """Test visualization requests with enhanced tracing."""
        service = EnhancedChatService()

        # Load test data
        tools._discover_and_load_csv_files(self.temp_dir)
        await service.initialize_data()

        # Test various visualization requests
        viz_requests = [
            "Create a bar chart of sales by product",
            "Show me a pie chart of employees by department",
            "Generate a scatter plot of salary vs performance score",
            "Create a line chart of sales over time",
        ]

        for request in viz_requests:
            result = await service.send_message(request)
            assert result is not None

        # Verify all conversations were tracked
        analytics = service.get_session_analytics()
        assert analytics["conversation_count"] == len(viz_requests)


class TestWeek2TracingIntegration:
    """Test Phoenix tracing integration specifically."""

    @pytest.mark.asyncio
    async def test_tracing_span_creation(self):
        """Test that custom spans are created for conversations."""
        service = EnhancedChatService()

        # This should create custom spans in Phoenix
        result = await service.send_message("Hello, what can you help me with?")

        # Verify the message was processed
        assert result is not None

        # Verify conversation count incremented (indicating span was created)
        analytics = service.get_session_analytics()
        assert analytics["conversation_count"] == 1

    @pytest.mark.asyncio
    async def test_session_analytics_accuracy(self):
        """Test that session analytics accurately reflect activity."""
        service = EnhancedChatService()

        initial_analytics = service.get_session_analytics()
        assert initial_analytics["conversation_count"] == 0

        # Send multiple messages
        for i in range(5):
            await service.send_message(f"Test message {i+1}")

            analytics = service.get_session_analytics()
            assert analytics["conversation_count"] == i + 1

    def test_enhanced_service_inheritance(self):
        """Test that EnhancedChatService properly inherits from ChatService."""
        service = EnhancedChatService()

        # Should have all base ChatService methods
        assert hasattr(service, "send_message")
        assert hasattr(service, "initialize_data")
        assert hasattr(service, "get_welcome_message")
        assert hasattr(service, "close_session")

        # Should have enhanced methods
        assert hasattr(service, "get_session_analytics")
        assert hasattr(service, "conversation_count")
