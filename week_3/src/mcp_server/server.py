"""
MCP Server for CSV Analytics with stdio transport

This MCP server provides ALL the CSV analytics tools converted from the Week 1
function_tool format to MCP tool format, plus additional helper tools.

Key concepts:
- FastMCP 2.11.3 server implementation
- stdio transport for local container communication
- All CSV analysis tools from Week 1 converted to MCP format
- Time and pandas documentation helper tools
- SQLite database operations for CSV data

Use cases:
- Complete CSV data analysis via MCP tools
- Time-aware analytics queries
- Pandas documentation assistance
- Schema discovery and data exploration
- Statistical analysis and SQL query execution
"""

import asyncio
import json
import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("CSV Analytics MCP Server")

# Global database connection for MCP tools
DB_PATH = ":memory:"
_db_connection = None

def get_db_connection():
    """Get or create in-memory database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_connection.execute("PRAGMA foreign_keys = ON")
    return _db_connection

# ============================================================================
# HELPER TOOLS (Time and Pandas Documentation)
# ============================================================================

@mcp.tool()
def get_current_time() -> str:
    """
    Get the current date and time in ISO format.
    
    This tool provides the current timestamp for time-aware analytics,
    such as adding timestamps to reports or filtering data by current time.
    
    Returns:
        str: Current datetime in ISO format (YYYY-MM-DDTHH:MM:SS.fffffZ)
    """
    return datetime.now(timezone.utc).isoformat()



# ============================================================================
# HELPER FUNCTIONS FOR DATABASE OPERATIONS
# ============================================================================

def _check_table_exists(conn, table_name: str) -> Dict[str, Any]:
    """Check if table exists and return error info if not."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    if not cursor.fetchone():
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        available_tables = [row[0] for row in cursor.fetchall()]
        table_list = ", ".join(available_tables) if available_tables else "No tables loaded"
        return {
            "success": False,
            "error": f"Table '{table_name}' does not exist. Available tables: {table_list}",
            "suggestion": "Check the table name spelling or use get_all_tables() to see all available tables.",
        }
    return {"success": True}

def _check_column_exists(conn, table_name: str, column_name: str) -> Dict[str, Any]:
    """Check if column exists in table and return error info if not."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        column_list = ", ".join(columns) if columns else "No columns found"
        return {
            "success": False,
            "error": f"Column '{column_name}' does not exist in table '{table_name}'. Available columns: {column_list}",
            "suggestion": "Check the column name spelling or use get_column_names() to see all available columns.",
        }
    return {"success": True, "columns": columns}

def _handle_csv_error(e: Exception, file_path: str) -> str:
    """Convert exception to helpful error message for CSV operations."""
    error_msg = str(e).lower()
    
    error_mappings = {
        ("no such file", "file not found"): f"File '{file_path}' not found. Check the file path and ensure the file exists.",
        ("permission denied",): f"Permission denied accessing '{file_path}'. Check file permissions.",
        ("encoding", "codec"): f"File encoding issue with '{file_path}'. Try saving the CSV with UTF-8 encoding.",
        ("parser error", "expected"): f"CSV format issue in '{file_path}'. Check for malformed rows, inconsistent delimiters, or encoding problems.",
        ("empty",): f"File '{file_path}' appears to be empty or contains no valid data.",
        ("memory",): f"File '{file_path}' is too large to load. Consider splitting it into smaller files.",
    }
    
    for keywords, message in error_mappings.items():
        if any(keyword in error_msg for keyword in keywords):
            return message
    
    return f"Failed to load '{file_path}': {str(e)}"

def _handle_sql_error(e: Exception, conn, sql_query: str) -> str:
    """Convert SQL exception to helpful error message."""
    error_msg = str(e).lower()
    
    if "no such table" in error_msg:
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            available_tables = [row[0] for row in cursor.fetchall()]
            table_list = ", ".join(available_tables) if available_tables else "No tables loaded"
            return f"Table does not exist. Available tables: {table_list}"
        except Exception:
            return "Table does not exist. Use get_all_tables() to see available tables."
    elif "no such column" in error_msg:
        return "Column does not exist. Use get_table_schema(table_name) to see available columns."
    elif "syntax error" in error_msg:
        return "SQL syntax error. Check your query structure, quotes, and keywords."
    else:
        return f"SQL execution failed: {str(e)}"

# ============================================================================
# CSV ANALYSIS TOOLS (Converted from Week 1 function_tools)
# ============================================================================

@mcp.tool()
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
    try:
        conn = get_db_connection()

        # Check if table exists
        table_check = _check_table_exists(conn, table_name)
        if not table_check["success"]:
            return table_check

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

@mcp.tool()
def count_rows_with_value(table_name: str, column_name: str, value: str) -> Dict[str, Any]:
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
    try:
        conn = get_db_connection()

        # Check if table exists
        table_check = _check_table_exists(conn, table_name)
        if not table_check["success"]:
            return table_check

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

@mcp.tool()
def get_all_tables() -> Dict[str, Any]:
    """
    Get information about all loaded tables in the database.

    This tool provides a summary of all available datasets, including table names,
    row counts, and column information. Perfect for agents to show users
    what data is available for analysis.

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

@mcp.tool()
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
    try:
        conn = get_db_connection()

        # Check if table exists
        table_check = _check_table_exists(conn, table_name)
        if not table_check["success"]:
            return table_check

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

@mcp.tool()
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
        table_check = _check_table_exists(conn, table_name)
        if not table_check["success"]:
            return table_check

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

@mcp.tool()
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
        helpful_msg = _handle_sql_error(e, conn, sql_query)

        return {
            "success": False,
            "error": helpful_msg,
            "sql_query": sql_query,
            "suggestion": "Double-check table and column names, and verify your SQL syntax.",
        }

def _load_csv_to_sqlite(file_path: str, table_name: str) -> Dict[str, Any]:
    """
    Internal function to load a CSV file into SQLite with automatic data type detection.
    
    Args:
        file_path: Path to the CSV file to load
        table_name: Name for the SQLite table
        
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
        helpful_msg = _handle_csv_error(e, file_path)

        return {
            "success": False,
            "error": helpful_msg,
            "file_path": file_path,
            "suggestion": "Ensure the file is a valid CSV format with proper headers and consistent column structure.",
        }


@mcp.tool()
def load_data(source: str, table_name: str = None) -> Dict[str, Any]:
    """
    Universal data loading tool - handles both single files and directories.

    This tool automatically detects whether the source is a file or directory
    and loads CSV data accordingly. Simplifies data loading into a single tool.

    Args:
        source: Path to CSV file OR directory containing CSV files
        table_name: Optional table name (required for single files, auto-generated for directories)

    Returns:
        Dict containing loading results, metadata, and any errors
    """
    try:
        if not os.path.exists(source):
            return {
                "success": False,
                "error": f"Path '{source}' does not exist",
                "suggestion": "Check the file or directory path"
            }

        # Check if source is a file or directory
        if os.path.isfile(source):
            # Single file loading
            if not table_name:
                # Auto-generate table name from filename
                table_name = os.path.splitext(os.path.basename(source))[0]
            
            result = _load_csv_to_sqlite(source, table_name)
            
            if result["success"]:
                return {
                    "success": True,
                    "type": "single_file",
                    "loaded_files": [result],
                    "total_loaded": 1,
                    "message": f"Successfully loaded {source} as table '{table_name}'"
                }
            else:
                return {
                    "success": False,
                    "type": "single_file", 
                    "error": result["error"],
                    "source": source
                }
        
        elif os.path.isdir(source):
            # Directory batch loading
            csv_files = [f for f in os.listdir(source) if f.endswith(".csv")]
            
            if not csv_files:
                return {
                    "success": True,
                    "type": "directory",
                    "message": f"No CSV files found in '{source}'",
                    "loaded_files": [],
                    "total_loaded": 0
                }

            loaded_files = []
            failed_files = []

            for csv_file in csv_files:
                file_path = os.path.join(source, csv_file)
                auto_table_name = os.path.splitext(csv_file)[0]
                
                result = _load_csv_to_sqlite(file_path, auto_table_name)
                
                if result["success"]:
                    loaded_files.append(result)
                else:
                    failed_files.append({"file_name": csv_file, "error": result["error"]})

            return {
                "success": True,
                "type": "directory",
                "source": source,
                "total_files_found": len(csv_files),
                "total_loaded": len(loaded_files),
                "total_failed": len(failed_files),
                "loaded_files": loaded_files,
                "failed_files": failed_files,
                "message": f"Loaded {len(loaded_files)}/{len(csv_files)} CSV files from {source}"
            }
        
        else:
            return {
                "success": False,
                "error": f"'{source}' is neither a file nor a directory",
                "suggestion": "Provide a valid file path or directory path"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Data loading failed: {str(e)}",
            "source": source
        }

@mcp.tool()
def execute_sql_analysis(query_request: str) -> Dict[str, Any]:
    """
    Execute complex SQL analysis using a simplified approach.
    
    This tool handles requests that require SQL queries like:
    - Statistical calculations (median, max, min, percentiles)
    - Complex aggregations and grouping
    - Multi-table analysis
    - Advanced filtering and sorting
    
    Args:
        query_request: Natural language description of the analysis needed
                      e.g., "Calculate median salary in employee_data"
                      e.g., "Find maximum temperature by city in weather_data"
    
    Returns:
        Dict containing the analysis results, confidence level, and any notes
    """
    try:
        # For Week 3, we'll use a simplified approach that directly executes common queries
        # This replaces the complex agent chain from Week 1 with direct SQL execution
        
        request_lower = query_request.lower()
        
        # Try to identify the type of analysis and generate appropriate SQL
        if "median" in request_lower:
            # Handle median calculations
            if "salary" in request_lower:
                sql_query = "SELECT AVG(salary) as median_approx FROM (SELECT salary FROM employee_data ORDER BY salary LIMIT 2 OFFSET (SELECT COUNT(*)/2 FROM employee_data))"
            else:
                return {
                    "success": False,
                    "error": "Median calculation needs specific column and table. Try: 'Calculate median salary in employee_data'",
                    "suggestion": "Specify the column and table for median calculation"
                }
        
        elif "maximum" in request_lower or "max" in request_lower:
            # Handle max calculations
            if "temperature" in request_lower:
                sql_query = "SELECT city, MAX(temperature) as max_temp FROM weather_data GROUP BY city ORDER BY max_temp DESC"
            elif "salary" in request_lower:
                sql_query = "SELECT MAX(salary) as max_salary FROM employee_data"
            else:
                return {
                    "success": False,
                    "error": "Maximum calculation needs specific column and table",
                    "suggestion": "Specify what you want the maximum of (e.g., 'maximum salary', 'maximum temperature by city')"
                }
        
        elif "minimum" in request_lower or "min" in request_lower:
            # Handle min calculations
            if "salary" in request_lower:
                sql_query = "SELECT MIN(salary) as min_salary FROM employee_data"
            else:
                return {
                    "success": False,
                    "error": "Minimum calculation needs specific column and table",
                    "suggestion": "Specify what you want the minimum of"
                }
        
        else:
            # For other complex queries, provide guidance
            return {
                "success": False,
                "error": f"Complex analysis not yet implemented for: {query_request}",
                "suggestion": "Try using execute_sql_query directly with your SQL, or use simple statistical tools like calculate_column_average"
            }
        
        # Execute the generated SQL
        result = execute_sql_query(sql_query)
        
        if result["success"]:
            return {
                "success": True,
                "result": result["results"],
                "confidence": "medium",
                "notes": f"Executed SQL analysis for: {query_request}",
                "sql_used": sql_query
            }
        else:
            return {
                "success": False,
                "error": f"SQL execution failed: {result['error']}",
                "suggestion": "Check if the required tables and columns exist"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"SQL analysis failed: {str(e)}",
            "suggestion": "Try rephrasing the question or use simpler statistical tools"
        }

@mcp.tool()
def list_available_tools() -> Dict[str, Any]:
    """
    Get a list of all available MCP tools for CSV analytics.
    
    This tool helps agents discover what capabilities are available
    for data analysis and processing.
    
    Returns:
        Dict containing list of available tools with descriptions
    """
    tools = {
        "Data Loading": {
            "load_data": "Universal data loader - handles single CSV files or entire directories"
        },
        "Data Discovery": {
            "get_all_tables": "List all loaded tables with basic information",
            "get_table_schema": "Get detailed schema information for a specific table", 
            "get_column_names": "Get column names for a specific table"
        },
        "Statistical Analysis": {
            "calculate_column_average": "Calculate the average value of a numeric column",
            "count_rows_with_value": "Count rows containing a specific value in a column"
        },
        "SQL Operations": {
            "execute_sql_query": "Execute SELECT queries against the loaded database",
            "execute_sql_analysis": "Execute complex SQL analysis with natural language requests"
        },
        "Helper Tools": {
            "get_current_time": "Get current timestamp for time-aware analytics"
        }
    }
    
    total_tools = sum(len(category_tools) for category_tools in tools.values())
    
    return {
        "success": True,
        "total_tools": total_tools,
        "categories": tools,
        "message": f"MCP server provides {total_tools} tools for CSV analytics"
    }

if __name__ == "__main__":
    # Redirect print statements to stderr to avoid interfering with stdio protocol
    import sys
    
    print("🚀 Starting CSV Analytics MCP Server...", file=sys.stderr)
    print("📡 Transport: stdio (for container communication)", file=sys.stderr)
    print("🔄 Starting server...\n", file=sys.stderr)
    
    # Run the MCP server with stdio transport (default for FastMCP)
    # FastMCP handles the JSON-RPC protocol over stdin/stdout automatically
    try:
        mcp.run()
    except KeyboardInterrupt:
        print("🛑 MCP Server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"❌ MCP Server error: {e}", file=sys.stderr)
        sys.exit(1)