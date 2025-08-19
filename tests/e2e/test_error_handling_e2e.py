"""
End-to-End Error Handling Tests

This module tests complete user journey error handling scenarios, focusing on
realistic user workflows and the overall user experience during error conditions.

Key concepts:
- Complete user journey testing
- Realistic error scenarios
- User experience validation
- System resilience under error conditions
- Recovery workflow testing

Use cases:
- Testing complete user error scenarios from start to finish
- Validating system behavior under realistic error conditions
- Ensuring users can recover from errors effectively
- Testing system resilience and graceful degradation
"""

import pytest
import tempfile
import os
import sys
import warnings
from pathlib import Path

# Add solution directory and test helpers to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "week_1" / "solution"))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from chat_service import ChatService
import tools
from helpers.llm_judge import (
    assert_error_response_quality,
    evaluate_conversation_quality,
)


class TestUserJourneyErrorScenarios:
    """Test complete user journey error scenarios."""

    def setup_method(self):
        """Setup realistic user environment."""
        self.chat_service = ChatService(session_id="e2e-user-session")

        # Create realistic business data
        self.temp_dir = tempfile.mkdtemp()

        # Sales data
        self.sales_csv = os.path.join(self.temp_dir, "sales_data.csv")
        with open(self.sales_csv, "w") as f:
            f.write("date,product,revenue,quantity,customer_segment\n")
            f.write("2024-01-01,Laptop,1200,1,Enterprise\n")
            f.write("2024-01-02,Phone,800,2,Consumer\n")
            f.write("2024-01-03,Tablet,600,1,Consumer\n")
            f.write("2024-01-04,Monitor,300,3,Enterprise\n")

        # Employee data
        self.employee_csv = os.path.join(self.temp_dir, "employee_data.csv")
        with open(self.employee_csv, "w") as f:
            f.write("id,name,department,salary,hire_date\n")
            f.write("1,Alice,Engineering,85000,2022-01-15\n")
            f.write("2,Bob,Sales,65000,2021-06-20\n")
            f.write("3,Carol,Marketing,70000,2023-03-10\n")

        # Load data
        tools._load_csv_to_sqlite(self.sales_csv, "sales_data")
        tools._load_csv_to_sqlite(self.employee_csv, "employee_data")

    @pytest.mark.asyncio
    async def test_new_user_data_exploration_with_errors(self):
        """Test new user exploring data and encountering various errors."""
        conversation_history = []

        # User starts by exploring what's available
        response1 = await self.chat_service.send_message(
            "What data do I have available?"
        )
        conversation_history.append(
            {"user": "What data do I have available?", "agent": response1["response"]}
        )

        # User tries to analyze non-existent data
        response2 = await self.chat_service.send_message(
            "Show me the customer satisfaction scores"
        )
        conversation_history.append(
            {
                "user": "Show me the customer satisfaction scores",
                "agent": response2["response"],
            }
        )

        # User tries to analyze existing data but wrong column
        response3 = await self.chat_service.send_message(
            "What's the average profit margin?"
        )
        conversation_history.append(
            {
                "user": "What's the average profit margin?",
                "agent": response3["response"],
            }
        )

        # User finally asks for something that exists
        response4 = await self.chat_service.send_message(
            "What's the average revenue in sales_data?"
        )
        conversation_history.append(
            {
                "user": "What's the average revenue in sales_data?",
                "agent": response4["response"],
            }
        )

        # Evaluate the entire conversation flow
        evaluation = await evaluate_conversation_quality(
            conversation_history=conversation_history,
            scenario="New user exploring data and encountering various errors",
            success_criteria="System should guide user from errors to successful analysis",
        )

        # The conversation should overall be helpful and lead to success
        assert evaluation.passes
        assert evaluation.overall_score >= 3.5

    @pytest.mark.asyncio
    async def test_business_analyst_workflow_with_recovery(self):
        """Test business analyst workflow with error recovery."""
        conversation_history = []

        # Analyst wants to do comparative analysis
        response1 = await self.chat_service.send_message(
            "Compare revenue by product category"
        )
        conversation_history.append(
            {
                "user": "Compare revenue by product category",
                "agent": response1["response"],
            }
        )

        # Realizes they need to use correct column name
        response2 = await self.chat_service.send_message(
            "Actually, compare revenue by product in sales_data"
        )
        conversation_history.append(
            {
                "user": "Actually, compare revenue by product in sales_data",
                "agent": response2["response"],
            }
        )

        # Follow up with related question
        response3 = await self.chat_service.send_message(
            "Which product generated the most revenue?"
        )
        conversation_history.append(
            {
                "user": "Which product generated the most revenue?",
                "agent": response3["response"],
            }
        )

        # Evaluate business analyst workflow
        evaluation = await evaluate_conversation_quality(
            conversation_history=conversation_history,
            scenario="Business analyst performing comparative analysis with error recovery",
            success_criteria="System should help analyst recover from errors and complete analysis",
        )

        assert evaluation.passes
        assert evaluation.overall_score >= 3.0

    @pytest.mark.asyncio
    async def test_data_loading_error_recovery_journey(self):
        """Test complete data loading error and recovery journey."""
        # Start fresh service without pre-loaded data
        fresh_service = ChatService(session_id="data-loading-test")

        conversation_history = []

        # User tries to load non-existent file
        response1 = await fresh_service.load_csv_file(
            "/path/to/missing/file.csv", "my_data"
        )
        conversation_history.append(
            {
                "user": "Load /path/to/missing/file.csv as my_data",
                "agent": response1["response"],
            }
        )

        # User asks what went wrong
        response2 = await fresh_service.send_message("What data is available?")
        conversation_history.append(
            {"user": "What data is available?", "agent": response2["response"]}
        )

        # User tries to analyze without data
        response3 = await fresh_service.send_message("Show me sales trends")
        conversation_history.append(
            {"user": "Show me sales trends", "agent": response3["response"]}
        )

        # Verify the journey provides helpful guidance
        for response in [response1, response2, response3]:
            if not response["success"]:
                assert len(response["response"]) > 30  # Substantive error message
                # Should not be cryptic technical errors
                assert "traceback" not in response["response"].lower()
                assert "exception" not in response["response"].lower()

    @pytest.mark.asyncio
    async def test_system_resilience_under_multiple_errors(self):
        """Test system remains stable under multiple error conditions."""
        error_queries = [
            "Calculate average missing_column",
            "Show data from missing_table",
            "What's the median description",  # Text column
            "Count rows where invalid_column = 'value'",
            "DELETE FROM sales_data",  # Security violation
            "",  # Empty query
            "   ",  # Whitespace query
        ]

        stable_responses = 0
        for query in error_queries:
            try:
                if query.strip():  # Non-empty queries
                    response = await self.chat_service.send_message(query)
                else:  # Empty queries
                    response = await self.chat_service.send_message(query)

                # System should remain stable (not crash)
                assert response is not None
                assert "response" in response
                stable_responses += 1

            except Exception as e:
                # System should not throw unhandled exceptions
                pytest.fail(
                    f"System threw unhandled exception for query '{query}': {str(e)}"
                )

        # All queries should get stable responses
        assert stable_responses == len(error_queries)

    @pytest.mark.asyncio
    async def test_user_experience_consistency_across_errors(self):
        """Test that user experience is consistent across different error types."""
        error_scenarios = [
            ("missing table", "Analyze data from inventory_table"),
            ("missing column", "What's the average profit?"),
            ("text analysis", "Calculate average name in employee_data"),
            (
                "empty results",
                "Count products where department equals 'NonexistentDept'",
            ),
        ]

        responses = []
        for error_type, query in error_scenarios:
            response = await self.chat_service.send_message(query)
            responses.append((error_type, query, response["response"]))

        # All responses should maintain consistent quality
        for error_type, query, response_text in responses:
            await assert_error_response_quality(
                response=response_text,
                scenario=f"User encountered {error_type} error",
                expected_behavior="Provide helpful, consistent error guidance",
                context=f"Query: '{query}'",
            )

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestErrorRecoveryWorkflows:
    """Test error recovery and user guidance workflows."""

    def setup_method(self):
        """Setup test environment."""
        self.chat_service = ChatService(session_id="recovery-test")

        # Create simple test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "orders.csv")

        with open(self.test_csv, "w") as f:
            f.write("order_id,customer,amount,status\n")
            f.write("1,Alice,150,completed\n")
            f.write("2,Bob,200,pending\n")
            f.write("3,Carol,75,completed\n")

        tools._load_csv_to_sqlite(self.test_csv, "orders")

    @pytest.mark.asyncio
    async def test_guided_error_recovery_workflow(self):
        """Test that system guides users through error recovery."""
        # User makes an error
        response1 = await self.chat_service.send_message("What's the average price?")

        # System should guide toward correct column
        if not response1["success"] or "price" not in response1["response"].lower():
            # Follow the guidance to use correct column
            response2 = await self.chat_service.send_message(
                "What's the average amount?"
            )
            assert response2["success"] is True

    @pytest.mark.asyncio
    async def test_progressive_error_refinement(self):
        """Test progressive refinement from error to success."""
        # Start with vague request
        await self.chat_service.send_message("Show me sales performance")

        # Refine to specific table
        await self.chat_service.send_message("Show me performance data from orders")

        # Refine to specific question
        response3 = await self.chat_service.send_message(
            "What's the total amount from orders?"
        )

        # The progression should lead to better responses
        # At minimum, responses should be getting more specific/helpful
        assert len(response3["response"]) > 20  # Substantive final response

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    print("✅ E2E error handling tests ready to run")
    print("Run with: pytest tests/e2e/test_error_handling_e2e.py -v")
