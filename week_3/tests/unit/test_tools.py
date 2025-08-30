"""
Unit Tests for Tools - Success Scenarios

This module tests successful tool operations to ensure core functionality
works correctly. Error scenarios are tested in test_tools_errors.py.

Key concepts:
- Tool success path validation
- CSV to SQLite conversion verification
- Data type detection testing
- Metadata extraction validation
- Schema inspection functionality

Use cases:
- Verifying tools work correctly with valid inputs
- Testing data loading and conversion success paths
- Validating tool output structure and content
- Ensuring tools return expected results for valid operations
"""

import os
import tempfile
import sys
from pathlib import Path

# Add the week_3/src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# For Week 3, we test MCP tools via the MCP server
import asyncio
from agents_.chat_service import ChatService


class TestCSVLoading:
    """Test CSV file loading and SQLite conversion."""

    def setup_method(self):
        """Create temporary test data."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test CSV content
        self.test_csv_content = """name,age,salary,hire_date
Alice,25,50000,2022-01-15
Bob,30,60000,2021-06-20
Carol,28,55000,2023-03-10"""

        self.test_csv_path = os.path.join(self.temp_dir, "test_employees.csv")
        with open(self.test_csv_path, "w") as f:
            f.write(self.test_csv_content)

    def test_load_csv_to_sqlite_success(self):
        """Test successful CSV loading."""
        result = tools._load_csv_to_sqlite(self.test_csv_path, "test_table")

        assert result["success"] is True
        assert result["table_name"] == "test_table"
        assert result["row_count"] == 3
        assert result["column_count"] == 4
        assert len(result["columns"]) == 4

        # Check column names
        column_names = [col["name"] for col in result["columns"]]
        assert "name" in column_names
        assert "age" in column_names
        assert "salary" in column_names
        assert "hire_date" in column_names

    def test_get_table_schema(self):
        """Test schema extraction."""
        # First load a table
        tools._load_csv_to_sqlite(self.test_csv_path, "schema_test")

        # Then get its schema
        result = tools._get_table_schema("schema_test")

        assert result["success"] is True
        assert result["table_name"] == "schema_test"
        assert result["row_count"] == 3
        assert result["column_count"] == 4
        assert len(result["sample_data"]) <= 3

    def test_get_all_tables(self):
        """Test getting all tables information."""
        # Load test data
        tools._load_csv_to_sqlite(self.test_csv_path, "all_tables_test")

        result = tools._get_all_tables()

        assert result["success"] is True
        assert result["table_count"] >= 1

        # Find our test table
        test_table = None
        for table in result["tables"]:
            if table["table_name"] == "all_tables_test":
                test_table = table
                break

        assert test_table is not None
        assert test_table["row_count"] == 3
        assert test_table["column_count"] == 4


class TestAnalyticsTools:
    """Test the analytics function tools."""

    def setup_method(self):
        """Create test data for analytics testing."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test CSV with numeric and categorical data
        self.test_csv_content = """name,department,salary,age
Alice,Engineering,75000,28
Bob,Marketing,65000,32
Carol,Engineering,85000,30
David,Marketing,60000,25
Eve,Engineering,90000,35"""

        self.test_csv_path = os.path.join(self.temp_dir, "test_analytics.csv")
        with open(self.test_csv_path, "w") as f:
            f.write(self.test_csv_content)

        # Load into database
        tools._load_csv_to_sqlite(self.test_csv_path, "analytics_test")

    def test_calculate_column_average_success(self):
        """Test calculating average of numeric column."""
        result = tools._calculate_column_average("analytics_test", "salary")

        assert result["success"] is True
        assert result["table_name"] == "analytics_test"
        assert result["column_name"] == "salary"
        assert result["average"] == 75000.0  # (75000+65000+85000+60000+90000)/5
        assert result["count"] == 5

    def test_count_rows_with_value_success(self):
        """Test counting rows with specific value."""
        result = tools._count_rows_with_value(
            "analytics_test", "department", "Engineering"
        )

        assert result["success"] is True
        assert result["table_name"] == "analytics_test"
        assert result["column_name"] == "department"
        assert result["search_value"] == "Engineering"
        assert result["count"] == 3  # Alice, Carol, Eve
        assert result["total_rows"] == 5
        assert result["percentage"] == 60.0  # 3/5 * 100

    def test_count_rows_with_value_no_matches(self):
        """Test counting rows when no matches found."""
        result = tools._count_rows_with_value("analytics_test", "department", "Finance")

        assert result["success"] is True
        assert result["count"] == 0
        assert result["percentage"] == 0.0

    def test_execute_sql_query_success(self):
        """Test successful SQL query execution."""
        result = tools._execute_sql_query(
            "SELECT department, AVG(salary) as avg_salary FROM analytics_test GROUP BY department"
        )

        assert result["success"] is True
        assert result["row_count"] == 2  # Engineering and Marketing
        assert "department" in result["column_names"]
        assert "avg_salary" in result["column_names"]
        assert len(result["results"]) == 2


class TestCSVDiscovery:
    """Test CSV file discovery and batch loading."""

    def setup_method(self):
        """Create temporary directory with test CSV files."""
        self.temp_dir = tempfile.mkdtemp()

        # Create multiple test CSV files
        csv_files = {
            "sales.csv": "product,price,quantity\nLaptop,999,2\nMouse,29,5",
            "employees.csv": "name,department,salary\nAlice,IT,70000\nBob,Sales,60000",
            "weather.csv": "date,temperature,humidity\n2024-01-01,22,65\n2024-01-02,25,70",
        }

        for filename, content in csv_files.items():
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, "w") as f:
                f.write(content)

    def test_discover_and_load_csv_files(self):
        """Test automatic discovery and loading of all CSV files."""
        result = tools._discover_and_load_csv_files(self.temp_dir)

        assert result["success"] is True
        assert result["total_files_found"] == 3
        assert result["successfully_loaded"] == 3
        assert result["failed_to_load"] == 0

        # Check loaded files
        loaded_files = result["loaded_files"]
        assert len(loaded_files) == 3

        # Check that each file was processed
        file_names = [f["file_name"] for f in loaded_files]
        assert "sales.csv" in file_names
        assert "employees.csv" in file_names
        assert "weather.csv" in file_names

    def test_discover_empty_directory(self):
        """Test discovery in directory with no CSV files."""
        empty_dir = tempfile.mkdtemp()

        result = tools._discover_and_load_csv_files(empty_dir)

        assert result["success"] is True
        assert result["loaded_files"] == []
        assert "No CSV files found" in result["message"]
