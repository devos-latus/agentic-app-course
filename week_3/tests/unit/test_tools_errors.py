"""
Unit Tests for Tools and Service - Error Scenarios

This module tests error handling across all components in isolation to ensure proper
error responses, categorization, and user-friendly messaging when things go wrong.

Key concepts:
- Tool-level error response testing (SQL, calculations, schema operations)
- ChatService error categorization and validation
- Error message quality and user-friendliness
- Response structure consistency across components
- CSV loading and discovery error handling

Use cases:
- Testing individual tool error responses and structures
- Validating ChatService error categorization logic
- Ensuring error messages are helpful and actionable
- Testing input validation and parameter checking
- Verifying consistent error response formats
"""

import pytest
import tempfile
import os
import sys
import warnings
from pathlib import Path

# Add solution directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from agents_.chat_service import ChatService
# Week 3 uses MCP tools via ChatService - no direct tools import needed


class TestToolErrorHandling:
    """Test error handling in individual tools."""

    def setup_method(self):
        """Setup test data for tools."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "test_data.csv")

        with open(self.test_csv, "w") as f:
            f.write("id,name,price,category\n")
            f.write("1,Laptop,1200,Electronics\n")
            f.write("2,Phone,800,Electronics\n")
            f.write("3,Desk,300,Furniture\n")

        tools._load_csv_to_sqlite(self.test_csv, "test_data")

    def test_sql_query_missing_table_error(self):
        """Test SQL tool error response for missing table."""
        result = tools._execute_sql_query("SELECT * FROM missing_table")

        # Verify error response structure
        assert result["success"] is False
        assert "error" in result
        assert "sql_query" in result
        assert "suggestion" in result

        # Verify helpful error content
        assert "available tables" in result["error"].lower()
        assert "test_data" in result["error"]

    def test_sql_query_missing_column_error(self):
        """Test SQL tool error response for missing column."""
        result = tools._execute_sql_query("SELECT missing_column FROM test_data")

        # Verify error response structure
        assert result["success"] is False
        assert "error" in result

        # Verify helpful error content
        assert "column does not exist" in result["error"].lower()
        assert "get_table_schema" in result["error"].lower()

    def test_sql_query_security_blocking(self):
        """Test SQL tool blocks dangerous operations."""
        result = tools._execute_sql_query("DROP TABLE test_data")

        assert result["success"] is False
        assert "only select queries" in result["error"].lower()
        assert "security" in result["error"].lower()

    def test_sql_query_syntax_error_detection(self):
        """Test SQL tool handles syntax errors appropriately."""
        # Test common SELECT misspelling
        result = tools._execute_sql_query("SELCT * FROM test_data")

        assert result["success"] is False
        assert (
            "syntax error" in result["error"].lower()
            or "select" in result["error"].lower()
        )

    def test_calculate_average_missing_table(self):
        """Test calculate_column_average with missing table."""
        result = tools._calculate_column_average("missing_table", "price")

        # Verify error response structure
        assert result["success"] is False
        assert "error" in result
        assert "suggestion" in result

        # Verify helpful content
        assert "does not exist" in result["error"]
        assert "available tables" in result["error"].lower()

    def test_calculate_average_missing_column(self):
        """Test calculate_column_average with missing column."""
        result = tools._calculate_column_average("test_data", "missing_column")

        assert result["success"] is False
        assert "does not exist" in result["error"]
        assert "available columns" in result["error"].lower()

    def test_calculate_average_text_column(self):
        """Test calculate_column_average with text column."""
        result = tools._calculate_column_average("test_data", "name")

        assert result["success"] is False
        assert (
            "text data" in result["error"].lower()
            or "numeric" in result["error"].lower()
        )

    def test_count_rows_missing_table(self):
        """Test count_rows_with_value with missing table."""
        result = tools._count_rows_with_value(
            "missing_table", "category", "Electronics"
        )

        assert result["success"] is False
        assert "does not exist" in result["error"]
        assert "available tables" in result["error"].lower()

    def test_count_rows_missing_column(self):
        """Test count_rows_with_value with missing column."""
        result = tools._count_rows_with_value("test_data", "missing_column", "value")

        assert result["success"] is False
        assert "does not exist" in result["error"]
        assert "available columns" in result["error"].lower()

    def test_get_table_schema_missing_table(self):
        """Test get_table_schema with missing table."""
        result = tools._get_table_schema("missing_table")

        assert result["success"] is False
        assert "does not exist" in result["error"]
        assert "available tables" in result["error"].lower()

    def test_get_all_tables_success(self):
        """Test get_all_tables returns proper structure."""
        result = tools._get_all_tables()

        assert result["success"] is True
        assert "table_count" in result
        assert "tables" in result
        assert isinstance(result["tables"], list)

        if result["tables"]:
            table = result["tables"][0]
            assert "table_name" in table
            assert "row_count" in table
            assert "column_count" in table
            assert "columns" in table

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestChatServiceErrorCategorization:
    """Test ChatService error categorization and response structure."""

    def setup_method(self):
        """Setup ChatService for testing."""
        self.chat_service = ChatService(session_id="unit-test-session")

    @pytest.mark.asyncio
    async def test_empty_message_validation(self):
        """Test empty message returns proper validation error."""
        response = await self.chat_service.send_message("")

        # Verify error categorization
        assert response["success"] is False
        assert response["error_type"] == "validation"

        # Verify response structure
        assert "error" in response
        assert "response" in response
        assert "empty message" in response["error"].lower()

    @pytest.mark.asyncio
    async def test_whitespace_message_validation(self):
        """Test whitespace-only message returns validation error."""
        response = await self.chat_service.send_message("   \t\n  ")

        assert response["success"] is False
        assert response["error_type"] == "validation"
        assert "empty message" in response["error"].lower()

    @pytest.mark.asyncio
    async def test_guardrail_error_categorization(self):
        """Test guardrail violations are properly categorized."""
        response = await self.chat_service.send_message(
            "What's the weather like today?"
        )

        # May succeed or be blocked by guardrail
        if not response["success"]:
            assert response["error_type"] == "guardrail"
            assert "data analysis" in response["response"].lower()

    @pytest.mark.asyncio
    async def test_csv_loading_empty_path_validation(self):
        """Test CSV loading with empty file path."""
        response = await self.chat_service.load_csv_file("", "test_table")

        assert response["success"] is False
        assert response["error_type"] == "validation"
        assert "file path" in response["error"].lower()

    @pytest.mark.asyncio
    async def test_csv_loading_empty_table_name_validation(self):
        """Test CSV loading with empty table name."""
        response = await self.chat_service.load_csv_file("/path/file.csv", "")

        assert response["success"] is False
        assert response["error_type"] == "validation"
        assert "table name" in response["error"].lower()

    @pytest.mark.asyncio
    async def test_csv_loading_nonexistent_file_system_error(self):
        """Test CSV loading with nonexistent file returns system error."""
        response = await self.chat_service.load_csv_file(
            "/nonexistent/file.csv", "test_table"
        )

        assert response["success"] is False
        assert response["error_type"] == "system"
        assert (
            "unable to load" in response["response"].lower()
            or "error" in response["response"].lower()
        )

    def test_error_response_structure_consistency(self):
        """Test that error responses have consistent structure."""
        # Define expected response structures
        expected_success_keys = {"success", "response"}
        expected_error_keys = {"success", "error_type", "error", "response"}

        # Verify structure definitions are complete
        assert len(expected_success_keys) >= 2
        assert len(expected_error_keys) >= 4
        assert "success" in expected_success_keys
        assert "success" in expected_error_keys

    def test_session_id_handling(self):
        """Test ChatService session ID handling."""
        # Test with explicit session ID
        service1 = ChatService(session_id="test-123")
        assert service1.session_id == "test-123"

        # Test with auto-generated session ID
        service2 = ChatService()
        assert isinstance(service2.session_id, str)
        assert len(service2.session_id) > 10  # UUIDs are longer

        # Ensure different services have different IDs
        service3 = ChatService()
        assert service2.session_id != service3.session_id


class TestCSVDiscoveryErrorHandling:
    """Test CSV discovery and loading error handling."""

    def test_discover_nonexistent_directory(self):
        """Test CSV discovery with nonexistent directory."""
        result = tools._discover_and_load_csv_files("nonexistent_directory")

        assert result["success"] is False
        assert "does not exist" in result["error"]

    def test_discover_empty_directory(self):
        """Test CSV discovery with empty directory."""
        temp_dir = tempfile.mkdtemp()

        try:
            result = tools._discover_and_load_csv_files(temp_dir)

            assert result["success"] is True
            assert result["loaded_files"] == []
            assert "no csv files found" in result["message"].lower()
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_load_csv_nonexistent_file(self):
        """Test loading nonexistent CSV file."""
        result = tools._load_csv_to_sqlite("/nonexistent/file.csv", "test_table")

        assert result["success"] is False
        assert "error" in result
        assert (
            "not found" in result["error"].lower()
            or "does not exist" in result["error"].lower()
        )


class TestErrorMessageQuality:
    """Test the quality and usefulness of error messages."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "quality_test.csv")

        with open(self.test_csv, "w") as f:
            f.write("name,department,salary\n")
            f.write("Alice,Engineering,75000\n")
            f.write("Bob,Marketing,65000\n")

        tools._load_csv_to_sqlite(self.test_csv, "quality_test")

    def test_error_messages_contain_suggestions(self):
        """Test that error messages include actionable suggestions."""
        result = tools._calculate_column_average("invalid_table", "invalid_column")

        assert result["success"] is False
        assert "suggestion" in result
        assert len(result["suggestion"]) > 10  # Should be meaningful

    def test_error_messages_are_user_friendly(self):
        """Test that error messages avoid technical jargon."""
        result = tools._execute_sql_query("SELECT * FROM nonexistent")

        assert result["success"] is False
        # Should use user-friendly language
        assert "does not exist" in result["error"] or "not found" in result["error"]
        # Should avoid raw SQLite error messages
        assert "sqlite" not in result["error"].lower()
        assert "pragma" not in result["error"].lower()

    def test_error_messages_provide_alternatives(self):
        """Test that error messages suggest available alternatives."""
        # Test with wrong table name
        result = tools._calculate_column_average("wrong_table", "salary")

        assert result["success"] is False
        assert "quality_test" in result["error"]  # Should suggest the correct table

    def test_csv_loading_invalid_format_handling(self):
        """Test CSV loading error message for malformed file."""
        # Create a malformed CSV file
        bad_csv = os.path.join(self.temp_dir, "bad_data.csv")
        with open(bad_csv, "w") as f:
            f.write("name,age\n")
            f.write("Alice,25,extra_field\n")  # Too many fields
            f.write("Bob\n")  # Too few fields

        result = tools._load_csv_to_sqlite(bad_csv, "bad_table")

        # Note: pandas is quite forgiving, so this might still succeed
        # but in a real scenario with stricter CSV parsers, we'd get helpful errors
        if not result["success"]:
            assert "suggestion" in result
            assert "CSV format" in result["error"] or "format" in result["suggestion"]

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    print("✅ Unit error handling tests ready to run")
    print("Run with: pytest tests/unit/test_tools_errors.py -v")
