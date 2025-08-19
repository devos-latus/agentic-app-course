"""
End-to-end test for the complete CSV analytics workflow.

Tests the full integration from CSV loading through agent interaction,
ensuring the system works as a complete solution.
"""

import pytest
import os
import tempfile
import sys
import warnings
from pathlib import Path

# Add the solution directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "week_1" / "solution"))

# Suppress Pydantic deprecation warnings from agents library
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from agents import Runner, SQLiteSession
from csv_agents import communication_agent
import tools


class TestCompleteWorkflow:
    """Test the complete CSV analytics workflow."""

    def setup_method(self):
        """Set up test environment with sample data."""
        self.temp_dir = tempfile.mkdtemp()

        # Create realistic test CSV files
        self.sales_csv = os.path.join(self.temp_dir, "sales.csv")
        with open(self.sales_csv, "w") as f:
            f.write("""date,product,price,quantity,customer_state
2024-01-15,Laptop,999.99,2,CA
2024-01-16,Mouse,29.99,5,NY
2024-01-17,Keyboard,79.99,1,TX
2024-01-18,Monitor,299.99,3,FL""")

        self.employees_csv = os.path.join(self.temp_dir, "employees.csv")
        with open(self.employees_csv, "w") as f:
            f.write("""name,department,salary,hire_date
Alice Johnson,Engineering,85000,2022-03-15
Bob Smith,Marketing,65000,2021-07-20
Carol Davis,Engineering,92000,2020-01-10""")

        # Create session for testing
        self.session = SQLiteSession(session_id=999)

    def test_data_loading_workflow(self):
        """Test that CSV files are discovered and loaded correctly."""
        # Load the test data
        result = tools._discover_and_load_csv_files(self.temp_dir)

        # Verify successful loading
        assert result["success"] is True
        assert result["successfully_loaded"] == 2
        assert result["failed_to_load"] == 0

        # Verify specific files were loaded
        loaded_files = {f["table_name"]: f for f in result["loaded_files"]}
        assert "sales" in loaded_files
        assert "employees" in loaded_files

        # Verify data integrity
        assert loaded_files["sales"]["row_count"] == 4
        assert loaded_files["employees"]["row_count"] == 3

    @pytest.mark.asyncio
    async def test_agent_data_discovery(self):
        """Test that the reception agent can discover and explain loaded data."""
        # First load test data
        tools._discover_and_load_csv_files(self.temp_dir)

        # Test agent interaction
        result = await Runner.run(
            starting_agent=communication_agent,
            input="What data is available for analysis?",
            session=self.session,
        )

        # Verify the agent responded
        assert result.final_output is not None
        assert len(result.final_output) > 0

        # The response should mention the loaded tables
        response = result.final_output.lower()
        assert "sales" in response or "employees" in response

    @pytest.mark.asyncio
    async def test_agent_schema_explanation(self):
        """Test that the agent can explain table schemas."""
        # Load test data
        tools._discover_and_load_csv_files(self.temp_dir)

        # Ask about specific table schema
        result = await Runner.run(
            starting_agent=communication_agent,
            input="Tell me about the sales table structure",
            session=self.session,
        )

        # Verify response contains schema information
        response = result.final_output.lower()
        assert "sales" in response
        # Should mention some columns from the sales data
        assert any(col in response for col in ["date", "product", "price", "quantity"])

    @pytest.mark.asyncio
    async def test_conversational_memory(self):
        """Test that the agent maintains conversation context."""
        # Load test data
        tools._discover_and_load_csv_files(self.temp_dir)

        # First interaction
        result1 = await Runner.run(
            starting_agent=communication_agent,
            input="What datasets do you have?",
            session=self.session,
        )

        # Follow-up interaction (should remember context)
        result2 = await Runner.run(
            starting_agent=communication_agent,
            input="Tell me more about the first one",
            session=self.session,
        )

        # Both should have responses
        assert result1.final_output is not None
        assert result2.final_output is not None
        assert len(result1.final_output) > 0
        assert len(result2.final_output) > 0


class TestErrorHandling:
    """Test error handling in the complete workflow."""

    @pytest.mark.asyncio
    async def test_no_data_scenario(self):
        """Test agent behavior when no data is loaded."""
        session = SQLiteSession(session_id=998)

        # Try to interact without loading any data
        result = await Runner.run(
            starting_agent=communication_agent,
            input="What data is available?",
            session=session,
        )

        # Agent should handle gracefully
        assert result.final_output is not None
        # Should indicate no data or ask user to load data
        response = result.final_output.lower()
        assert any(
            phrase in response
            for phrase in ["no data", "no datasets", "upload", "load", "available"]
        )

    def test_invalid_directory_handling(self):
        """Test handling of invalid data directories."""
        result = tools._discover_and_load_csv_files("nonexistent_directory")

        assert result["success"] is False
        assert "does not exist" in result["error"]
