"""
Integration Tests for Error Handling

This module tests agent interactions and multi-agent error handling workflows
using LLM-based evaluation for response quality assessment.

Key concepts:
- Agent interaction error handling
- Multi-agent error propagation
- Response quality evaluation using LLM-as-judge
- Agent decision-making under error conditions

Use cases:
- Testing agent response quality to various errors
- Validating multi-agent error handling workflows
- Ensuring agents provide helpful recovery suggestions
- Testing agent-to-agent error communication
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

from agents import Runner, SQLiteSession
from csv_agents import analytics_agent, communication_agent
import tools
from helpers.llm_judge import (
    assert_helpful_error_message,
    assert_recovery_suggestions,
    assert_user_friendly_explanation,
    assert_error_response_quality,
)


class TestAgentErrorResponseQuality:
    """Test agent response quality to errors using LLM evaluation."""

    def setup_method(self):
        """Setup test environment with consistent data."""
        self.session = SQLiteSession(session_id=888)

        # Create test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "products.csv")

        with open(self.test_csv, "w") as f:
            f.write("id,name,price,category,description,in_stock\n")
            f.write("1,Laptop,1200,Electronics,Gaming laptop,true\n")
            f.write("2,Phone,800,Electronics,Smartphone,false\n")
            f.write("3,Desk,300,Furniture,Office desk,true\n")
            f.write("4,Chair,150,Furniture,Ergonomic chair,true\n")

        tools._load_csv_to_sqlite(self.test_csv, "products")

    @pytest.mark.asyncio
    async def test_analytics_agent_missing_table_response(self):
        """Test analytics agent response quality for missing table errors."""
        result = await Runner.run(
            starting_agent=analytics_agent,
            input="What's the average price in the inventory_table?",
            session=self.session,
        )

        # Use LLM evaluation for response quality
        await assert_helpful_error_message(
            response=result.final_output, error_type="missing table"
        )

        await assert_recovery_suggestions(
            response=result.final_output,
            error_scenario="User requested data from a table that doesn't exist",
        )

    @pytest.mark.asyncio
    async def test_analytics_agent_missing_column_response(self):
        """Test analytics agent response quality for missing column errors."""
        result = await Runner.run(
            starting_agent=analytics_agent,
            input="Calculate the average weight of products",
            session=self.session,
        )

        await assert_helpful_error_message(
            response=result.final_output, error_type="missing column"
        )

        await assert_recovery_suggestions(
            response=result.final_output,
            error_scenario="User requested analysis of a column that doesn't exist",
        )

    @pytest.mark.asyncio
    async def test_analytics_agent_text_column_analysis(self):
        """Test analytics agent handles text column analysis requests."""
        result = await Runner.run(
            starting_agent=analytics_agent,
            input="What's the average description of products?",
            session=self.session,
        )

        await assert_error_response_quality(
            response=result.final_output,
            scenario="User tried to calculate average of a text column",
            expected_behavior="Explain that text columns can't be averaged and suggest numeric alternatives",
            context="Description column contains text like 'Gaming laptop', 'Smartphone'",
        )

    @pytest.mark.asyncio
    async def test_analytics_agent_empty_search_results(self):
        """Test analytics agent handles queries with no results."""
        result = await Runner.run(
            starting_agent=analytics_agent,
            input="Count products where category equals 'NonexistentCategory'",
            session=self.session,
        )

        await assert_error_response_quality(
            response=result.final_output,
            scenario="Query returned zero results for a search",
            expected_behavior="Clearly state no matches found and explain what was searched",
            context="User searched for 'NonexistentCategory' which doesn't exist in the data",
        )

    @pytest.mark.asyncio
    async def test_communication_agent_error_explanation(self):
        """Test communication agent makes technical errors user-friendly."""
        result = await Runner.run(
            starting_agent=communication_agent,
            input="Show me data from the customer_database table",
            session=self.session,
        )

        await assert_user_friendly_explanation(
            response=result.final_output, technical_issue="Database table not found"
        )

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestMultiAgentErrorHandling:
    """Test error handling in multi-agent workflows."""

    def setup_method(self):
        """Setup test environment."""
        self.session = SQLiteSession(session_id=777)

        # Create minimal test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "sales.csv")

        with open(self.test_csv, "w") as f:
            f.write("date,product,amount,customer\n")
            f.write("2024-01-01,Laptop,1200,Alice\n")
            f.write("2024-01-02,Phone,800,Bob\n")

        tools._load_csv_to_sqlite(self.test_csv, "sales")

    @pytest.mark.asyncio
    async def test_communication_to_analytics_error_flow(self):
        """Test error handling from communication agent to analytics agent."""
        result = await Runner.run(
            starting_agent=communication_agent,
            input="What's the total revenue from the missing_sales_table?",
            session=self.session,
        )

        # The communication agent should handle the error gracefully
        # and provide a user-friendly response
        assert len(result.final_output) > 50  # Substantive response

        # Should be helpful and informative
        response_lower = result.final_output.lower()
        assert any(
            indicator in response_lower
            for indicator in [
                "does not exist",
                "not found",
                "available",
                "tables",
                "help",
            ]
        )

    @pytest.mark.asyncio
    async def test_analytics_agent_error_recovery_suggestions(self):
        """Test analytics agent provides actionable recovery suggestions."""
        result = await Runner.run(
            starting_agent=analytics_agent,
            input="Calculate the average invalid_column for each product",
            session=self.session,
        )

        await assert_recovery_suggestions(
            response=result.final_output,
            error_scenario="User requested analysis of a column that doesn't exist",
        )

        # Should suggest ways to see what's available
        response_lower = result.final_output.lower()
        assert any(
            suggestion in response_lower
            for suggestion in ["schema", "columns", "available", "try", "instead"]
        )

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestErrorHandlingWorkflows:
    """Test complete error handling workflows and patterns."""

    def setup_method(self):
        """Setup test environment."""
        self.session = SQLiteSession(session_id=666)

    @pytest.mark.asyncio
    async def test_no_data_loaded_scenario(self):
        """Test agent behavior when no data is loaded."""
        # Don't load any data - test empty database scenario
        result = await Runner.run(
            starting_agent=communication_agent,
            input="What data is available for analysis?",
            session=self.session,
        )

        # Agent should handle gracefully and guide user
        assert result.final_output is not None
        assert len(result.final_output) > 30  # Substantive response

        # Should indicate no data or guide user to load data
        response_lower = result.final_output.lower()
        assert any(
            phrase in response_lower
            for phrase in [
                "no data",
                "no datasets",
                "load",
                "upload",
                "available",
                "csv",
            ]
        )

    @pytest.mark.asyncio
    async def test_multiple_error_types_in_sequence(self):
        """Test system handles multiple different errors gracefully."""
        # Create minimal data for testing
        temp_dir = tempfile.mkdtemp()
        test_csv = os.path.join(temp_dir, "test.csv")

        with open(test_csv, "w") as f:
            f.write("id,value\n")
            f.write("1,100\n")

        tools._load_csv_to_sqlite(test_csv, "test")

        try:
            # Test sequence of different error types
            error_scenarios = [
                "What's the average missing_column?",  # Missing column
                "Show data from missing_table",  # Missing table
                "Calculate average id",  # Should work - numeric
            ]

            responses = []
            for scenario in error_scenarios:
                result = await Runner.run(
                    starting_agent=analytics_agent, input=scenario, session=self.session
                )
                responses.append((scenario, result.final_output))

            # All responses should be substantive (not empty or error messages)
            for scenario, response in responses:
                assert response is not None
                assert len(response) > 20  # Substantive response
                # Should not contain system error traces
                assert "traceback" not in response.lower()
                assert "exception" not in response.lower()

        finally:
            import shutil

            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("✅ Integration error handling tests ready to run")
    print("Run with: pytest tests/integration/test_error_handling_integration.py -v")
