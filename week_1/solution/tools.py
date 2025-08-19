"""
CSV Analytics Tools

This module provides essential function tools for loading and analyzing CSV data with AI agents.
The tools handle automatic data type detection, CSV to SQLite conversion, and metadata extraction
for seamless agent-based data analysis.

Key concepts:
- Function Tools: Python functions decorated with @function_tool for agent use
- Data Type Detection: Automatic inference of appropriate SQLite types from CSV data
- SQLite Integration: Fast, queryable storage for CSV data analysis
- Schema Discovery: Tools for agents to understand data structure and plan queries
- Statistical Analysis: Core statistical functions and SQL execution capabilities

Use cases:
- Automatic CSV file discovery and loading at startup
- Schema inspection for agent query planning and context
- Basic statistical calculations (averages, counts)
- Complex SQL analysis through deterministic agent workflows
- Data exploration and metadata extraction for user guidance
"""

import os
import sqlite3
import pandas as pd
from typing import Dict, Any
from agents import function_tool


# Global database connection - shared across all tools
# Using in-memory database to avoid persistence between runs
DB_PATH = ":memory:"
_db_connection = None


def get_db_connection():
    """Get or create in-memory database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_connection.execute("PRAGMA foreign_keys = ON")
    return _db_connection


def _load_csv_to_sqlite(file_path: str, table_name: str) -> Dict[str, Any]:
    """
    Load a CSV file into SQLite with automatic data type detection and conversion.

    Args:
        file_path: Path to the CSV file to load
        table_name: Name for the SQLite table (usually filename without extension)

    Returns:
        Dict containing success status, row count, columns, and any errors
    """
    try:
        # Read CSV with pandas for automatic type inference
        df = pd.read_csv(file_path)

        # Get database connection
        conn = get_db_connection()

        # Convert DataFrame to SQLite (pandas handles type conversion)
        df.to_sql(table_name, conn, if_exists="replace", index=False)

        # Get column information
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]

        return {
            "success": True,
            "table_name": table_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": columns,
            "file_path": file_path,
        }

    except Exception as e:
        error_msg = str(e).lower()
        if "no such file" in error_msg or "file not found" in error_msg:
            helpful_msg = f"File '{file_path}' not found. Check the file path and ensure the file exists."
        elif "permission denied" in error_msg:
            helpful_msg = (
                f"Permission denied accessing '{file_path}'. Check file permissions."
            )
        elif "encoding" in error_msg or "codec" in error_msg:
            helpful_msg = f"File encoding issue with '{file_path}'. Try saving the CSV with UTF-8 encoding."
        elif "parser error" in error_msg or "expected" in error_msg:
            helpful_msg = f"CSV format issue in '{file_path}'. Check for malformed rows, inconsistent delimiters, or encoding problems."
        elif "empty" in error_msg:
            helpful_msg = (
                f"File '{file_path}' appears to be empty or contains no valid data."
            )
        elif "memory" in error_msg:
            helpful_msg = f"File '{file_path}' is too large to load. Consider splitting it into smaller files."
        else:
            helpful_msg = f"Failed to load '{file_path}': {str(e)}"

        return {
            "success": False,
            "error": helpful_msg,
            "file_path": file_path,
            "suggestion": "Ensure the file is a valid CSV format with proper headers and consistent column structure.",
        }


def _discover_and_load_csv_files(data_directory: str = "data") -> Dict[str, Any]:
    """
    Automatically discover and load all CSV files from a directory.

    Args:
        data_directory: Directory to scan for CSV files (default: "data")

    Returns:
        Dict containing summary of all loaded files and any errors
    """
    try:
        if not os.path.exists(data_directory):
            return {
                "success": False,
                "error": f"Directory '{data_directory}' does not exist",
            }

        # Find all CSV files
        csv_files = [f for f in os.listdir(data_directory) if f.endswith(".csv")]

        if not csv_files:
            return {
                "success": True,
                "message": f"No CSV files found in '{data_directory}'",
                "loaded_files": [],
            }

        loaded_files = []
        failed_files = []

        for csv_file in csv_files:
            file_path = os.path.join(data_directory, csv_file)
            table_name = os.path.splitext(csv_file)[0]  # Remove .csv extension

            result = _load_csv_to_sqlite(file_path, table_name)

            if result["success"]:
                loaded_files.append(
                    {
                        "file_name": csv_file,
                        "table_name": table_name,
                        "row_count": result["row_count"],
                        "columns": [col["name"] for col in result["columns"]],
                    }
                )
            else:
                failed_files.append({"file_name": csv_file, "error": result["error"]})

        return {
            "success": True,
            "data_directory": data_directory,
            "total_files_found": len(csv_files),
            "successfully_loaded": len(loaded_files),
            "failed_to_load": len(failed_files),
            "loaded_files": loaded_files,
            "failed_files": failed_files,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "data_directory": data_directory}


def _calculate_column_average(table_name: str, column_name: str) -> Dict[str, Any]:
    """
    Calculate the average value of a numeric column in a table.

    Args:
        table_name: Name of the table to analyze
        column_name: Name of the numeric column to average

    Returns:
        Dict containing the average value, count of values, and any errors
    """
    try:
        conn = get_db_connection()

        # Check if table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if not cursor.fetchone():
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            available_tables = [row[0] for row in cursor.fetchall()]
            table_list = (
                ", ".join(available_tables) if available_tables else "No tables loaded"
            )
            return {
                "success": False,
                "error": f"Table '{table_name}' does not exist. Available tables: {table_list}",
                "suggestion": "Check the table name spelling or use get_all_tables() to see all available tables.",
            }

        # Check if column exists
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            column_list = ", ".join(columns) if columns else "No columns found"
            return {
                "success": False,
                "error": f"Column '{column_name}' does not exist in table '{table_name}'. Available columns: {column_list}",
                "suggestion": "Check the column name spelling or use get_column_names() to see all available columns.",
            }

        # Check if column contains numeric data by testing a sample
        cursor = conn.execute(
            f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 5"
        )
        sample_values = [row[0] for row in cursor.fetchall()]

        # Test if values are numeric
        numeric_count = 0
        for value in sample_values:
            try:
                float(str(value))
                numeric_count += 1
            except (ValueError, TypeError):
                pass

        # If less than half the sample values are numeric, it's probably a text column
        if len(sample_values) > 0 and numeric_count / len(sample_values) < 0.5:
            return {
                "success": False,
                "error": f"Column '{column_name}' appears to contain mostly text data. Cannot calculate average of text values.",
                "suggestion": f"Try a numeric column instead. Use get_table_schema('{table_name}') to see column types and available numeric columns.",
            }

        # Calculate average of numeric values only
        cursor = conn.execute(f"""
            SELECT AVG(CAST({column_name} AS REAL)), COUNT({column_name}) 
            FROM {table_name} 
            WHERE {column_name} IS NOT NULL 
            AND CAST({column_name} AS REAL) != 0 OR {column_name} = '0'
        """)
        result = cursor.fetchone()

        average, count = result[0], result[1]

        if average is None or count == 0:
            return {
                "success": False,
                "error": f"No valid numeric values found in column '{column_name}'. The column may contain only text or null values.",
                "suggestion": "Check if the column contains numbers. Use get_table_schema() to see column types, or try a different column.",
            }

        return {
            "success": True,
            "table_name": table_name,
            "column_name": column_name,
            "average": round(average, 2),
            "count": count,
            "message": f"Average of {column_name}: {round(average, 2)} (based on {count} values)",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error calculating average: {str(e)}",
            "suggestion": "Verify the table and column names are correct, and that the column contains numeric data.",
        }


@function_tool
def calculate_column_average(table_name: str, column_name: str) -> Dict[str, Any]:
    """
    Calculate the average value of a numeric column in a table.

    This tool computes the mean value for a specified numeric column,
    handling missing values and providing error feedback for non-numeric columns.
    Perfect for statistical analysis and data exploration.

    Args:
        table_name: Name of the table to analyze
        column_name: Name of the numeric column to average

    Returns:
        Dict containing the average value, count of values, and any errors
    """
    return _calculate_column_average(table_name, column_name)


def _count_rows_with_value(
    table_name: str, column_name: str, value: str
) -> Dict[str, Any]:
    """
    Count how many rows contain a specific value in a given column.

    Args:
        table_name: Name of the table to search
        column_name: Name of the column to search in
        value: The value to count (will be treated as string for comparison)

    Returns:
        Dict containing the count, total rows, and percentage
    """
    try:
        conn = get_db_connection()

        # Check if table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if not cursor.fetchone():
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            available_tables = [row[0] for row in cursor.fetchall()]
            table_list = (
                ", ".join(available_tables) if available_tables else "No tables loaded"
            )
            return {
                "success": False,
                "error": f"Table '{table_name}' does not exist. Available tables: {table_list}",
                "suggestion": "Check the table name spelling or use get_all_tables() to see all available tables.",
            }

        # Check if column exists
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            column_list = ", ".join(columns) if columns else "No columns found"
            return {
                "success": False,
                "error": f"Column '{column_name}' does not exist in table '{table_name}'. Available columns: {column_list}",
                "suggestion": "Check the column name spelling or use get_column_names() to see all available columns.",
            }

        # Count rows with the specific value
        cursor = conn.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} = ?", (value,)
        )
        count_with_value = cursor.fetchone()[0]

        # Get total row count
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]

        # Calculate percentage
        percentage = (count_with_value / total_rows * 100) if total_rows > 0 else 0

        return {
            "success": True,
            "table_name": table_name,
            "column_name": column_name,
            "search_value": value,
            "count": count_with_value,
            "total_rows": total_rows,
            "percentage": round(percentage, 1),
            "message": f"Found {count_with_value} rows with '{value}' in {column_name} ({percentage:.1f}% of {total_rows} total rows)",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error counting rows: {str(e)}",
            "suggestion": "Verify the table and column names are correct, and ensure the search value is properly formatted.",
        }


@function_tool
def count_rows_with_value(
    table_name: str, column_name: str, value: str
) -> Dict[str, Any]:
    """
    Count how many rows contain a specific value in a given column.

    This tool searches for exact matches of a value in a column and returns
    the count. Useful for categorical analysis and data distribution exploration.

    Args:
        table_name: Name of the table to search
        column_name: Name of the column to search in
        value: The value to count (will be treated as string for comparison)

    Returns:
        Dict containing the count, total rows, and percentage
    """
    return _count_rows_with_value(table_name, column_name, value)


def _get_all_tables() -> Dict[str, Any]:
    """
    Get information about all loaded tables in the database.

    Returns:
        Dict containing list of all tables with their basic information
    """
    try:
        conn = get_db_connection()

        # Get all table names
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row[0] for row in cursor.fetchall()]

        tables_info = []
        for table_name in table_names:
            try:
                # Get row count
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                # Get column names
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]

                tables_info.append(
                    {
                        "table_name": table_name,
                        "row_count": row_count,
                        "column_count": len(columns),
                        "columns": columns,
                    }
                )
            except Exception:
                # Skip tables that cause errors
                continue

        return {"success": True, "table_count": len(tables_info), "tables": tables_info}

    except Exception as e:
        return {"success": False, "error": str(e)}


@function_tool
def get_all_tables() -> Dict[str, Any]:
    """
    Get information about all loaded tables in the database.

    This tool provides a summary of all available datasets, including table names,
    row counts, and column information. Perfect for agents to show users
    what data is available for analysis.

    Returns:
        Dict containing list of all tables with their basic information
    """
    return _get_all_tables()


def _get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    Get detailed schema information for a loaded table.

    This tool provides comprehensive metadata about a table including column names,
    data types, sample values, and basic statistics. Useful for agents to understand
    what data is available for analysis.

    Args:
        table_name: Name of the SQLite table to inspect

    Returns:
        Dict containing schema details, column info, and sample data
    """
    try:
        conn = get_db_connection()

        # Check if table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if not cursor.fetchone():
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            available_tables = [row[0] for row in cursor.fetchall()]
            table_list = (
                ", ".join(available_tables) if available_tables else "No tables loaded"
            )
            return {
                "success": False,
                "error": f"Table '{table_name}' does not exist. Available tables: {table_list}",
                "suggestion": "Check the table name spelling or use get_all_tables() to see all available tables.",
            }

        # Get table schema
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append(
                {
                    "name": row[1],
                    "type": row[2],
                    "not_null": bool(row[3]),
                    "primary_key": bool(row[5]),
                }
            )

        # Get row count
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        # Get sample data (first 3 rows)
        cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample_rows = cursor.fetchall()

        # Get column names for sample data
        column_names = [col[0] for col in cursor.description]
        sample_data = [dict(zip(column_names, row)) for row in sample_rows]

        return {
            "success": True,
            "table_name": table_name,
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns,
            "sample_data": sample_data,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "table_name": table_name}


@function_tool
def get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    Get detailed schema information for a loaded table.

    This tool provides comprehensive metadata about a table including column names,
    data types, sample values, and basic statistics. Useful for agents to understand
    what data is available for analysis.

    Args:
        table_name: Name of the SQLite table to inspect

    Returns:
        Dict containing schema details, column info, and sample data
    """
    return _get_table_schema(table_name)


@function_tool
def get_column_names(table_name: str) -> Dict[str, Any]:
    """
    Get the column names for a specific table.

    This tool provides a quick way to get just the column names without
    the full schema details. Useful for agents that need to quickly check
    what columns are available for analysis.

    Args:
        table_name: Name of the SQLite table to inspect

    Returns:
        Dict containing list of column names
    """
    try:
        conn = get_db_connection()

        # Check if table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if not cursor.fetchone():
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            available_tables = [row[0] for row in cursor.fetchall()]
            table_list = (
                ", ".join(available_tables) if available_tables else "No tables loaded"
            )
            return {
                "success": False,
                "error": f"Table '{table_name}' does not exist. Available tables: {table_list}",
                "suggestion": "Check the table name spelling or use get_all_tables() to see all available tables.",
            }

        # Get column names
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        column_names = [row[1] for row in cursor.fetchall()]

        return {
            "success": True,
            "table_name": table_name,
            "column_count": len(column_names),
            "columns": column_names,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "table_name": table_name}


def _execute_sql_query(sql_query: str) -> Dict[str, Any]:
    """
    Execute a SQL query against the loaded SQLite database.

    This tool allows agents to run custom SQL queries for complex analysis
    that goes beyond the basic function tools. Includes safety checks and
    result formatting for agent consumption.

    Args:
        sql_query: The SQL query to execute (SELECT statements only)

    Returns:
        Dict containing query results, column names, and execution details
    """
    try:
        conn = get_db_connection()

        # Basic safety check - only allow SELECT statements
        query_upper = sql_query.strip().upper()
        if not query_upper.startswith("SELECT"):
            # Check if it's a syntax error that just looks like a non-SELECT
            if any(
                word in query_upper for word in ["SELCT", "SEECT", "SELET", "SELEC"]
            ):
                return {
                    "success": False,
                    "error": "SQL syntax error. Check your query structure - did you mean 'SELECT'?",
                    "sql_query": sql_query,
                    "suggestion": "Double-check your SQL syntax, especially the SELECT keyword.",
                }
            else:
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed for security reasons",
                }

        # Execute the query
        cursor = conn.execute(sql_query)
        rows = cursor.fetchall()

        # Get column names
        column_names = (
            [description[0] for description in cursor.description]
            if cursor.description
            else []
        )

        # Convert to list of dictionaries for easier consumption
        results = []
        for row in rows:
            results.append(dict(zip(column_names, row)))

        return {
            "success": True,
            "sql_query": sql_query,
            "row_count": len(results),
            "column_names": column_names,
            "results": results,
            "message": f"Query executed successfully, returned {len(results)} rows",
        }

    except Exception as e:
        error_msg = str(e).lower()

        # Provide specific guidance based on error type
        if "no such table" in error_msg:
            try:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                available_tables = [row[0] for row in cursor.fetchall()]
                table_list = (
                    ", ".join(available_tables)
                    if available_tables
                    else "No tables loaded"
                )
                helpful_msg = f"Table does not exist. Available tables: {table_list}"
            except Exception:
                helpful_msg = "Table does not exist. Use get_all_tables() to see available tables."
        elif "no such column" in error_msg:
            helpful_msg = "Column does not exist. Use get_table_schema(table_name) to see available columns."
        elif "syntax error" in error_msg:
            helpful_msg = (
                "SQL syntax error. Check your query structure, quotes, and keywords."
            )
        else:
            helpful_msg = f"SQL execution failed: {str(e)}"

        return {
            "success": False,
            "error": helpful_msg,
            "sql_query": sql_query,
            "suggestion": "Double-check table and column names, and verify your SQL syntax.",
        }


@function_tool
def execute_sql_query(sql_query: str) -> Dict[str, Any]:
    """
    Execute a SQL query against the loaded SQLite database.

    This tool allows agents to run custom SQL queries for complex analysis
    that goes beyond the basic function tools. Includes safety checks and
    result formatting for agent consumption.

    Args:
        sql_query: The SQL query to execute (SELECT statements only)

    Returns:
        Dict containing query results, column names, and execution details
    """
    return _execute_sql_query(sql_query)


async def _execute_sql_analysis(query_request: str) -> Dict[str, Any]:
    """
    Execute a complete SQL analysis flow using the deterministic agent chain.

    This function encapsulates the deterministic flow:
    Query Planner → SQL Writer → Query Evaluator → Final Result
    """
    try:
        # Import agents here to avoid circular dependencies
        from csv_agents import (
            query_planner_agent,
            sql_writer_agent,
            query_evaluator_agent,
        )
        from agents import Runner

        # Step 1: Query Planner analyzes the request
        planner_result = await Runner.run(
            starting_agent=query_planner_agent, input=query_request
        )

        # Step 2: SQL Writer executes based on the plan
        sql_result = await Runner.run(
            starting_agent=sql_writer_agent,
            input=f"Execute this query plan: {planner_result.final_output}",
        )

        # Step 3: Query Evaluator validates and formats results
        eval_result = await Runner.run(
            starting_agent=query_evaluator_agent,
            input=f"Evaluate these SQL results for the original request '{query_request}': {sql_result.final_output}",
        )

        # Return structured result
        if hasattr(eval_result.final_output, "answers_question"):
            # If it's a QueryEvaluation object
            evaluation = eval_result.final_output
            if (
                evaluation.answers_question
                and evaluation.next_action == "return_result"
            ):
                return {
                    "success": True,
                    "result": evaluation.result_summary,
                    "confidence": evaluation.confidence_level,
                    "notes": evaluation.data_quality_notes,
                }
            else:
                return {
                    "success": False,
                    "error": evaluation.result_summary,
                    "suggestion": "Query needs refinement or clarification",
                }
        else:
            # If it's a string response
            return {
                "success": True,
                "result": str(eval_result.final_output),
                "confidence": "high",
                "notes": None,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"SQL analysis failed: {str(e)}",
            "suggestion": "Try rephrasing the question or check data availability",
        }


@function_tool
async def execute_sql_analysis(query_request: str) -> Dict[str, Any]:
    """
    Execute complex SQL analysis using the deterministic agent flow.

    This tool handles requests that require SQL queries like:
    - Statistical calculations (median, max, min, percentiles)
    - Complex aggregations and grouping
    - Multi-table analysis
    - Advanced filtering and sorting

    The tool internally manages the complete flow:
    Query Planner → SQL Writer → Query Evaluator → Results

    Args:
        query_request: Natural language description of the analysis needed
                      e.g., "Calculate median salary in employee_data"
                      e.g., "Find maximum temperature by city in weather_data"

    Returns:
        Dict containing the analysis results, confidence level, and any notes
    """
    return await _execute_sql_analysis(query_request)


# Data loading function tools (for agent use)
def _discover_and_load_csv_files_tool(data_directory: str = "data") -> Dict[str, Any]:
    """
    Automatically discover and load all CSV files from a directory.

    This tool scans a directory for CSV files, loads each one into SQLite,
    and provides a summary of all loaded datasets. Designed for startup
    initialization to make data immediately available to agents.

    Args:
        data_directory: Directory to scan for CSV files (default: "data")

    Returns:
        Dict containing summary of all loaded files and any errors
    """
    return _discover_and_load_csv_files(data_directory)


@function_tool
def discover_and_load_csv_files(data_directory: str = "data") -> Dict[str, Any]:
    """
    Automatically discover and load all CSV files from a directory.

    This tool scans a directory for CSV files, loads each one into SQLite,
    and provides a summary of all loaded datasets. Designed for startup
    initialization to make data immediately available to agents.

    Args:
        data_directory: Directory to scan for CSV files (default: "data")

    Returns:
        Dict containing summary of all loaded files and any errors
    """
    return _discover_and_load_csv_files(data_directory)


@function_tool
def load_csv_file(file_path: str, table_name: str) -> Dict[str, Any]:
    """
    Load a single CSV file into the analytics system.

    This tool loads a CSV file into SQLite with automatic data type detection.
    Use this when users want to load a specific CSV file or when processing
    uploaded files from the UI.

    Args:
        file_path: Path to the CSV file to load
        table_name: Name for the database table (will be used to reference the data)

    Returns:
        Dict with success status, table metadata, row count, and any errors
    """
    return _load_csv_to_sqlite(file_path, table_name)
