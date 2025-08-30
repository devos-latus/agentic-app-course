"""
LLM-as-Judge Tests for System Robustness

This module uses an LLM to evaluate if our system properly handles:
1. Missing columns gracefully
2. Non-numeric data appropriately
3. Helpful error messages to users

Key concepts:
- LLM-based evaluation of user experience quality
- Robustness testing across error scenarios
- Qualitative assessment of error handling
- User-friendly communication evaluation

Use cases:
- Testing error message helpfulness from user perspective
- Evaluating graceful degradation under error conditions
- Assessing system robustness and recovery capabilities
- Validating user experience quality metrics
"""

import pytest
import tempfile
import os
import sys
import warnings
from pathlib import Path

# Add the solution directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "week_1" / "solution"))

# Suppress Pydantic deprecation warnings from agents library
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from agents import Runner, SQLiteSession, Agent
from agentic_app_quickstart.examples.helpers import get_model
from csv_agents import analytics_agent
import tools


class TestRobustnessWithLLMJudge:
    """Test system robustness using LLM as a judge for quality evaluation."""

    def setup_method(self):
        """Setup test environment with sample data."""
        self.session = SQLiteSession(session_id=900)

        # Create test data with various data types
        self.temp_dir = tempfile.mkdtemp()

        # Products table with mixed data types
        self.products_csv = os.path.join(self.temp_dir, "products.csv")
        with open(self.products_csv, "w") as f:
            f.write("id,name,price,category,description,in_stock\n")
            f.write("1,Laptop,1200.50,Electronics,High-performance laptop,true\n")
            f.write("2,Chair,299.99,Furniture,Comfortable office chair,false\n")
            f.write("3,Book,15.99,Education,Programming guide,true\n")
            f.write("4,Invalid Price,not_a_number,Electronics,Broken data,maybe\n")

        # Load test data
        tools._load_csv_to_sqlite(self.products_csv, "products")

        # Create LLM judge agent
        self.judge_agent = Agent(
            name="RobustnessJudge",
            instructions="""You are an expert evaluator of user experience and system robustness.

Evaluate system responses based on these criteria:

1. MISSING COLUMNS HANDLING:
   - Does the system clearly state which column is missing?
   - Does it immediately show available alternatives?
   - Is the error message helpful for recovery?
   - Score: 1-10 (10 = excellent graceful handling)

2. NON-NUMERIC DATA HANDLING:
   - Does the system detect non-numeric data appropriately?
   - Does it explain why the operation can't be performed?
   - Does it suggest appropriate alternatives?
   - Score: 1-10 (10 = excellent data type handling)

3. ERROR MESSAGE HELPFULNESS:
   - Are error messages clear and specific?
   - Do they provide actionable guidance?
   - Are they user-friendly (not technical jargon)?
   - Do they help users succeed on retry?
   - Score: 1-10 (10 = extremely helpful messages)

For each test, provide:
- Individual scores (1-10) for each criteria that applies
- Brief reasoning for each score
- Overall assessment of robustness
- Suggestions for improvement (if any)

Be strict but fair in your evaluation. A score of 8+ indicates excellent handling.""",
            model=get_model(),
        )

    @pytest.mark.asyncio
    async def test_missing_column_graceful_handling(self):
        """Test graceful handling of missing columns with LLM judge evaluation."""

        # Test scenario: User tries to access non-existent column
        user_input = "What is the average salary in the products table?"

        result = await Runner.run(
            starting_agent=analytics_agent, input=user_input, session=self.session
        )

        system_response = result.final_output

        # LLM Judge evaluation
        judge_prompt = f"""
        SCENARIO: Missing Column Handling Test
        
        User asked: "{user_input}"
        System responded: "{system_response}"
        
        Available columns in products table: id, name, price, category, description, in_stock
        Note: 'salary' column does not exist in this table.
        
        Evaluate this response for MISSING COLUMNS HANDLING and ERROR MESSAGE HELPFULNESS.
        
        Rate each criterion (1-10) and explain your reasoning.
        """

        judge_result = await Runner.run(
            starting_agent=self.judge_agent,
            input=judge_prompt,
            session=SQLiteSession(session_id=901),
        )

        print("\n=== MISSING COLUMN TEST ===")
        print(f"User Input: {user_input}")
        print(f"System Response: {system_response}")
        print(f"LLM Judge Evaluation: {judge_result.final_output}")

        # Basic assertions to ensure the test framework works
        assert result.final_output is not None
        assert len(result.final_output) > 0
        assert (
            "salary" in result.final_output.lower()
        )  # Should mention the missing column

    @pytest.mark.asyncio
    async def test_non_numeric_data_handling(self):
        """Test appropriate handling of non-numeric data with LLM judge evaluation."""

        # Test scenario 1: Try to calculate average of text column
        user_input = "Calculate the average name in the products table"

        result = await Runner.run(
            starting_agent=analytics_agent, input=user_input, session=self.session
        )

        system_response = result.final_output

        # LLM Judge evaluation
        judge_prompt = f"""
        SCENARIO: Non-Numeric Data Handling Test
        
        User asked: "{user_input}"
        System responded: "{system_response}"
        
        Context: The 'name' column contains text values like 'Laptop', 'Chair', 'Book' - clearly not numeric.
        Available numeric columns: id, price
        
        Evaluate this response for NON-NUMERIC DATA HANDLING and ERROR MESSAGE HELPFULNESS.
        
        Rate each criterion (1-10) and explain your reasoning.
        """

        judge_result = await Runner.run(
            starting_agent=self.judge_agent,
            input=judge_prompt,
            session=SQLiteSession(session_id=902),
        )

        print("\n=== NON-NUMERIC DATA TEST ===")
        print(f"User Input: {user_input}")
        print(f"System Response: {system_response}")
        print(f"LLM Judge Evaluation: {judge_result.final_output}")

        # Basic assertions
        assert result.final_output is not None
        assert "name" in result.final_output.lower()

    @pytest.mark.asyncio
    async def test_mixed_data_type_handling(self):
        """Test handling of columns with mixed data types."""

        # Test scenario: Try to use column that has some invalid numeric data
        user_input = "What is the average price in products? Include all rows."

        result = await Runner.run(
            starting_agent=analytics_agent, input=user_input, session=self.session
        )

        system_response = result.final_output

        # LLM Judge evaluation
        judge_prompt = f"""
        SCENARIO: Mixed Data Type Handling Test
        
        User asked: "{user_input}"
        System responded: "{system_response}"
        
        Context: The 'price' column contains mostly numbers (1200.50, 299.99, 15.99) but one invalid entry ('not_a_number').
        
        Evaluate this response for NON-NUMERIC DATA HANDLING and ERROR MESSAGE HELPFULNESS.
        Did the system handle the mixed data appropriately? Did it provide warnings or explanations?
        
        Rate each criterion (1-10) and explain your reasoning.
        """

        judge_result = await Runner.run(
            starting_agent=self.judge_agent,
            input=judge_prompt,
            session=SQLiteSession(session_id=903),
        )

        print("\n=== MIXED DATA TYPE TEST ===")
        print(f"User Input: {user_input}")
        print(f"System Response: {system_response}")
        print(f"LLM Judge Evaluation: {judge_result.final_output}")

        # Basic assertions
        assert result.final_output is not None

    @pytest.mark.asyncio
    async def test_helpful_error_messages_quality(self):
        """Test overall quality and helpfulness of error messages."""

        # Test multiple error scenarios in sequence
        error_scenarios = [
            "Count rows where nonexistent_column equals Electronics",
            "What is the average description in products",  # Text column
            "Show me data from missing_table",  # Missing table
        ]

        responses = []
        for scenario in error_scenarios:
            result = await Runner.run(
                starting_agent=analytics_agent, input=scenario, session=self.session
            )
            responses.append((scenario, result.final_output))

        # Combine all responses for comprehensive evaluation
        all_responses = "\n\n".join([f"User: {q}\nSystem: {r}" for q, r in responses])

        # LLM Judge evaluation
        judge_prompt = f"""
        SCENARIO: Comprehensive Error Message Quality Test
        
        Multiple error scenarios tested:
        
        {all_responses}
        
        Context: 
        - 'nonexistent_column' does not exist (available: id, name, price, category, description, in_stock)
        - 'description' is a text column, not numeric
        - 'missing_table' does not exist (available: products)
        
        Evaluate ALL responses for ERROR MESSAGE HELPFULNESS overall.
        
        Consider:
        1. Are the messages consistently helpful across different error types?
        2. Do they provide specific, actionable guidance?
        3. Are they user-friendly and not overly technical?
        4. Do they help users understand what went wrong and how to fix it?
        5. Is the information presented clearly and immediately useful?
        
        Provide an overall robustness score (1-10) and detailed feedback.
        """

        judge_result = await Runner.run(
            starting_agent=self.judge_agent,
            input=judge_prompt,
            session=SQLiteSession(session_id=904),
        )

        print("\n=== COMPREHENSIVE ERROR MESSAGE QUALITY TEST ===")
        for scenario, response in responses:
            print(f"User: {scenario}")
            print(f"System: {response}")
            print()
        print(f"LLM Judge Evaluation: {judge_result.final_output}")

        # Basic assertions
        assert all(response for _, response in responses)

    @pytest.mark.asyncio
    async def test_recovery_and_learning_flow(self):
        """Test if users can successfully recover after errors."""

        # Simulate a user making an error and then correcting it
        error_input = "What is the average cost in products?"  # Wrong column name

        error_result = await Runner.run(
            starting_agent=analytics_agent, input=error_input, session=self.session
        )

        # User corrects based on error message
        corrected_input = (
            "What is the average price in products?"  # Correct column name
        )

        success_result = await Runner.run(
            starting_agent=analytics_agent, input=corrected_input, session=self.session
        )

        # LLM Judge evaluation of the recovery flow
        judge_prompt = f"""
        SCENARIO: Error Recovery and Learning Flow Test
        
        Step 1 - User made error:
        User: "{error_input}"
        System: "{error_result.final_output}"
        
        Step 2 - User corrected based on error message:
        User: "{corrected_input}"
        System: "{success_result.final_output}"
        
        Evaluate this complete flow for:
        1. ERROR MESSAGE HELPFULNESS - Did the error message enable successful recovery?
        2. MISSING COLUMNS HANDLING - Was the guidance clear enough for user to fix the issue?
        3. Overall user experience - Can users learn from errors and succeed?
        
        Rate the complete recovery flow (1-10) and explain how well the system supports user learning.
        """

        judge_result = await Runner.run(
            starting_agent=self.judge_agent,
            input=judge_prompt,
            session=SQLiteSession(session_id=905),
        )

        print("\n=== RECOVERY AND LEARNING FLOW TEST ===")
        print(f"Error: {error_input}")
        print(f"System: {error_result.final_output}")
        print(f"Corrected: {corrected_input}")
        print(f"System: {success_result.final_output}")
        print(f"LLM Judge Evaluation: {judge_result.final_output}")

        # Basic assertions
        assert error_result.final_output is not None
        assert success_result.final_output is not None
        # Success result should contain actual data/numbers
        assert any(char.isdigit() for char in success_result.final_output)

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestRobustnessMetrics:
    """Additional metrics-based tests for robustness validation."""

    def test_error_message_completeness(self):
        """Test that error messages contain all required information."""

        # Test missing table error
        result = tools._calculate_column_average("nonexistent_table", "price")

        # Check error message contains required elements
        assert not result["success"]
        assert "does not exist" in result["error"]
        assert (
            "Available tables:" in result["error"]
            or "Available tables" in result["error"]
        )
        assert "suggestion" in result

        # Test missing column error
        result = tools._calculate_column_average("products", "nonexistent_column")

        assert not result["success"]
        assert "does not exist" in result["error"]
        assert (
            "Available columns:" in result["error"]
            or "Available columns" in result["error"]
        )
        assert "suggestion" in result

    def test_non_numeric_data_detection(self):
        """Test detection and handling of non-numeric data."""

        # Create test data with text column
        temp_dir = tempfile.mkdtemp()
        text_csv = os.path.join(temp_dir, "text_data.csv")
        with open(text_csv, "w") as f:
            f.write("name,description\n")
            f.write("Product A,High quality item\n")
            f.write("Product B,Budget option\n")

        tools._load_csv_to_sqlite(text_csv, "text_products")

        # Try to calculate average of text column
        result = tools._calculate_column_average("text_products", "description")

        assert not result["success"]
        assert "text" in result["error"].lower() or "numeric" in result["error"].lower()
        assert "suggestion" in result

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)

    def test_sql_error_handling_robustness(self):
        """Test SQL execution error handling."""

        # Test various SQL error scenarios
        sql_tests = [
            "SELECT nonexistent_column FROM products",  # Missing column
            "SELECT * FROM nonexistent_table",  # Missing table
            "SELECT * FROM products WHERE",  # Syntax error
        ]

        for sql_query in sql_tests:
            result = tools._execute_sql_query(sql_query)

            # Each should fail gracefully with helpful messages
            assert not result["success"]
            assert "error" in result
            assert "suggestion" in result
            assert len(result["error"]) > 10  # Should be descriptive
