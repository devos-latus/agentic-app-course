"""
Visualization Core Module for CSV Analytics System

This module provides comprehensive chart generation and data visualization capabilities
for the CSV analytics system. It integrates with the agent framework to enable
automatic chart creation from SQL query results.

Key concepts:
- Chart Generation: Create bar charts, line plots, and histograms from data
- Data Analysis: Analyze data structure to suggest appropriate chart types
- File Management: Handle chart storage and retrieval with organized naming
- Agent Integration: Function tools that agents can use for visualization
- Error Handling: Graceful error handling with helpful user messages

Use cases:
- Generate charts from SQL query results automatically
- Analyze data to suggest the best visualization type
- Create downloadable chart files for users
- Integrate with web interfaces for chart display
- Support various chart types for different data patterns
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Any
import uuid
from agents import function_tool

# Configure matplotlib for headless operation
plt.switch_backend("Agg")
plt.style.use("default")

# Chart storage configuration
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "charts")
DEFAULT_CHART_WIDTH = 12
DEFAULT_CHART_HEIGHT = 8
DEFAULT_DPI = 150


def ensure_charts_directory() -> str:
    """
    Ensure the charts directory exists for storing generated charts.

    Returns:
        str: Path to the charts directory
    """
    if not os.path.exists(CHARTS_DIR):
        os.makedirs(CHARTS_DIR)
    return CHARTS_DIR


def generate_chart_filename(chart_type: str, title: str = "") -> str:
    """
    Generate a unique filename for a chart.

    Args:
        chart_type: Type of chart (bar_chart, line_plot, histogram)
        title: Optional title to include in filename

    Returns:
        str: Full path to the chart file
    """
    ensure_charts_directory()

    # Create safe filename from title
    safe_title = "".join(
        c for c in title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    safe_title = safe_title.replace(" ", "_")[:30]  # Limit length

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]

    if safe_title:
        filename = f"{chart_type}_{safe_title}_{timestamp}_{unique_id}.png"
    else:
        filename = f"{chart_type}_{timestamp}_{unique_id}.png"

    return os.path.join(CHARTS_DIR, filename)


def prepare_data_for_plotting(query_results: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert query results to a pandas DataFrame for plotting.

    Args:
        query_results: Dictionary containing 'results' key with list of records

    Returns:
        pd.DataFrame: Prepared data for plotting
    """
    if "results" not in query_results:
        raise ValueError("Query results must contain 'results' key")

    results = query_results["results"]
    if not results:
        raise ValueError("No data available for plotting")

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Handle numeric conversion
    for col in df.columns:
        if df[col].dtype == "object":
            # Try to convert to numeric
            try:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass  # Keep as non-numeric
            except Exception:
                pass

    return df


def analyze_data_structure(query_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze data structure to suggest the most appropriate chart type.

    Args:
        query_results: Dictionary containing query results

    Returns:
        Dict containing analysis results and chart type suggestion
    """
    try:
        df = prepare_data_for_plotting(query_results)

        row_count = len(df)
        column_count = len(df.columns)

        # Analyze column types
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

        # Available chart types
        available_charts = [
            "bar_chart",
            "line_plot",
            "histogram",
            "pie_chart",
            "scatter_plot",
            "box_plot",
            "heatmap",
        ]

        # Determine best chart type with multiple suggestions
        suggestions = []

        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            if row_count <= 10:
                suggestions.append(
                    (
                        "pie_chart",
                        "Small categorical dataset - pie chart shows proportions clearly",
                    )
                )
                suggestions.append(
                    (
                        "bar_chart",
                        "Categorical comparisons - bar chart shows values clearly",
                    )
                )
            else:
                suggestions.append(
                    (
                        "bar_chart",
                        "Categorical data with numeric values - bar chart shows comparisons clearly",
                    )
                )
                suggestions.append(
                    ("line_plot", "Sequential data - line plot shows trends")
                )

        if len(numeric_cols) >= 2:
            suggestions.append(
                (
                    "scatter_plot",
                    "Two numeric columns - scatter plot shows relationships and correlation",
                )
            )
            suggestions.append(
                (
                    "heatmap",
                    "Multiple numeric columns - heatmap shows correlation matrix",
                )
            )

        if len(numeric_cols) >= 1:
            suggestions.append(
                ("histogram", "Numeric data - histogram shows distribution")
            )
            suggestions.append(
                ("box_plot", "Numeric data - box plot shows distribution and outliers")
            )

        # Select primary suggestion
        primary_suggestion = (
            suggestions[0]
            if suggestions
            else ("bar_chart", "Default choice for mixed data types")
        )

        return {
            "success": True,
            "analysis": {
                "row_count": row_count,
                "column_count": column_count,
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
                "suggested_chart_type": primary_suggestion[0],
                "reasoning": primary_suggestion[1],
                "all_suggestions": [
                    {"chart_type": chart, "reason": reason}
                    for chart, reason in suggestions
                ],
                "available_chart_types": available_charts,
                "chart_type_descriptions": {
                    "bar_chart": "Categorical comparisons (sales by product, counts by department)",
                    "line_plot": "Trends over time or sequential data",
                    "histogram": "Distribution of numeric values with statistics",
                    "pie_chart": "Proportions and percentages (market share, budget allocation)",
                    "scatter_plot": "Relationships between two numeric variables with correlation",
                    "box_plot": "Data distribution, quartiles, and outliers (can be grouped)",
                    "heatmap": "Correlation matrices for multiple numeric variables",
                },
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Data analysis failed: {str(e)}",
            "analysis": None,
            "available_chart_types": [
                "bar_chart",
                "line_plot",
                "histogram",
                "pie_chart",
                "scatter_plot",
                "box_plot",
                "heatmap",
            ],
        }


def create_bar_chart_core(
    query_results: Dict[str, Any], title: str = "Bar Chart"
) -> Dict[str, Any]:
    """
    Create a bar chart from query results.

    Args:
        query_results: Dictionary containing query results
        title: Chart title

    Returns:
        Dict containing chart creation results and file path
    """
    try:
        df = prepare_data_for_plotting(query_results)

        # Find best columns for x and y axis
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if not categorical_cols and not numeric_cols:
            raise ValueError("No suitable columns found for bar chart")

        # Determine x and y columns
        if categorical_cols and numeric_cols:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
        elif len(df.columns) >= 2:
            x_col = df.columns[0]
            y_col = df.columns[1]
        else:
            # Single column - create count chart
            x_col = df.columns[0]
            df_counts = df[x_col].value_counts().reset_index()
            df_counts.columns = [x_col, "count"]
            df = df_counts
            y_col = "count"

        # Create the chart
        plt.figure(figsize=(DEFAULT_CHART_WIDTH, DEFAULT_CHART_HEIGHT), dpi=DEFAULT_DPI)

        # Sort by y values for better visualization
        df_sorted = df.sort_values(y_col, ascending=False)

        bars = plt.bar(
            df_sorted[x_col],
            df_sorted[y_col],
            color="steelblue",
            alpha=0.8,
            edgecolor="navy",
            linewidth=0.5,
        )

        plt.title(title, fontsize=16, fontweight="bold", pad=20)
        plt.xlabel(x_col.replace("_", " ").title(), fontsize=12, fontweight="bold")
        plt.ylabel(y_col.replace("_", " ").title(), fontsize=12, fontweight="bold")

        # Rotate x-axis labels if they're long
        if any(len(str(x)) > 8 for x in df_sorted[x_col]):
            plt.xticks(rotation=45, ha="right")

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:,.0f}" if height >= 1 else f"{height:.2f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()

        # Save chart
        chart_path = generate_chart_filename("bar_chart", title)
        plt.savefig(
            chart_path,
            dpi=DEFAULT_DPI,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()

        return {
            "success": True,
            "chart_type": "bar_chart",
            "title": title,
            "image_path": chart_path,
            "data_points": len(df),
            "x_column": x_col,
            "y_column": y_col,
            "message": f"Bar chart created successfully with {len(df)} data points",
        }

    except Exception as e:
        plt.close()  # Ensure plot is closed on error
        return {
            "success": False,
            "error": f"Bar chart creation failed: {str(e)}",
            "chart_type": "bar_chart",
            "title": title,
        }


def create_line_plot_core(
    query_results: Dict[str, Any], title: str = "Line Plot"
) -> Dict[str, Any]:
    """
    Create a line plot from query results.

    Args:
        query_results: Dictionary containing query results
        title: Chart title

    Returns:
        Dict containing chart creation results and file path
    """
    try:
        df = prepare_data_for_plotting(query_results)

        if len(df.columns) < 2:
            raise ValueError("Line plot requires at least 2 columns")

        x_col = df.columns[0]
        y_col = df.columns[1]

        # Sort by x column
        df_sorted = df.sort_values(x_col)

        # Create the chart
        plt.figure(figsize=(DEFAULT_CHART_WIDTH, DEFAULT_CHART_HEIGHT), dpi=DEFAULT_DPI)

        plt.plot(
            df_sorted[x_col],
            df_sorted[y_col],
            marker="o",
            linewidth=2.5,
            markersize=6,
            color="steelblue",
            markerfacecolor="navy",
            markeredgecolor="white",
            markeredgewidth=1,
        )

        plt.title(title, fontsize=16, fontweight="bold", pad=20)
        plt.xlabel(x_col.replace("_", " ").title(), fontsize=12, fontweight="bold")
        plt.ylabel(y_col.replace("_", " ").title(), fontsize=12, fontweight="bold")

        # Rotate x-axis labels if they're long
        if any(len(str(x)) > 8 for x in df_sorted[x_col]):
            plt.xticks(rotation=45, ha="right")

        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save chart
        chart_path = generate_chart_filename("line_plot", title)
        plt.savefig(
            chart_path,
            dpi=DEFAULT_DPI,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()

        return {
            "success": True,
            "chart_type": "line_plot",
            "title": title,
            "image_path": chart_path,
            "data_points": len(df),
            "x_column": x_col,
            "y_column": y_col,
            "message": f"Line plot created successfully with {len(df)} data points",
        }

    except Exception as e:
        plt.close()  # Ensure plot is closed on error
        return {
            "success": False,
            "error": f"Line plot creation failed: {str(e)}",
            "chart_type": "line_plot",
            "title": title,
        }


def create_histogram_core(
    query_results: Dict[str, Any], column_name: str, title: str = "Histogram"
) -> Dict[str, Any]:
    """
    Create a histogram from query results.

    Args:
        query_results: Dictionary containing query results
        column_name: Name of the column to create histogram for
        title: Chart title

    Returns:
        Dict containing chart creation results and file path
    """
    try:
        df = prepare_data_for_plotting(query_results)

        if column_name not in df.columns:
            available_cols = ", ".join(df.columns)
            raise ValueError(
                f"Column '{column_name}' not found. Available columns: {available_cols}"
            )

        # Ensure column is numeric
        if not pd.api.types.is_numeric_dtype(df[column_name]):
            try:
                df[column_name] = pd.to_numeric(df[column_name])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Column '{column_name}' is not numeric and cannot be converted"
                )

        # Remove null values
        data = df[column_name].dropna()

        if len(data) == 0:
            raise ValueError(f"No valid numeric data in column '{column_name}'")

        # Calculate statistics
        stats = {
            "mean": float(data.mean()),
            "median": float(data.median()),
            "std": float(data.std()),
            "min": float(data.min()),
            "max": float(data.max()),
            "count": len(data),
        }

        # Create the chart
        plt.figure(figsize=(DEFAULT_CHART_WIDTH, DEFAULT_CHART_HEIGHT), dpi=DEFAULT_DPI)

        # Calculate optimal number of bins
        bins = min(30, max(10, len(data) // 10))

        n, bins_edges, patches = plt.hist(
            data,
            bins=bins,
            alpha=0.7,
            color="steelblue",
            edgecolor="navy",
            linewidth=0.5,
        )

        # Add mean and median lines
        plt.axvline(
            stats["mean"],
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {stats['mean']:.2f}",
        )
        plt.axvline(
            stats["median"],
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Median: {stats['median']:.2f}",
        )

        plt.title(title, fontsize=16, fontweight="bold", pad=20)
        plt.xlabel(
            column_name.replace("_", " ").title(), fontsize=12, fontweight="bold"
        )
        plt.ylabel("Frequency", fontsize=12, fontweight="bold")
        plt.legend()
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()

        # Save chart
        chart_path = generate_chart_filename("histogram", title)
        plt.savefig(
            chart_path,
            dpi=DEFAULT_DPI,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()

        return {
            "success": True,
            "chart_type": "histogram",
            "title": title,
            "image_path": chart_path,
            "data_points": len(data),
            "column": column_name,
            "statistics": stats,
            "message": f"Histogram created successfully for {len(data)} data points",
        }

    except Exception as e:
        plt.close()  # Ensure plot is closed on error
        return {
            "success": False,
            "error": f"Histogram creation failed: {str(e)}",
            "chart_type": "histogram",
            "title": title,
        }


def create_pie_chart_core(
    query_results: Dict[str, Any], title: str = "Pie Chart"
) -> Dict[str, Any]:
    """
    Create a pie chart from query results.

    Args:
        query_results: Dictionary containing query results
        title: Chart title

    Returns:
        Dict containing chart creation results and file path
    """
    try:
        df = prepare_data_for_plotting(query_results)

        # Find best columns for labels and values
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if not categorical_cols or not numeric_cols:
            raise ValueError(
                "Pie chart requires one categorical and one numeric column"
            )

        label_col = categorical_cols[0]
        value_col = numeric_cols[0]

        # Aggregate data if needed
        df_grouped = df.groupby(label_col)[value_col].sum().reset_index()

        # Create the chart
        plt.figure(figsize=(DEFAULT_CHART_WIDTH, DEFAULT_CHART_HEIGHT), dpi=DEFAULT_DPI)

        # Create pie chart with better styling
        wedges, texts, autotexts = plt.pie(
            df_grouped[value_col],
            labels=df_grouped[label_col],
            autopct="%1.1f%%",
            startangle=90,
            colors=plt.cm.Set3.colors,
        )

        # Enhance text styling
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")

        plt.title(title, fontsize=16, fontweight="bold", pad=20)
        plt.axis("equal")  # Equal aspect ratio ensures circular pie

        # Save chart
        chart_path = generate_chart_filename("pie_chart", title)
        plt.savefig(
            chart_path,
            dpi=DEFAULT_DPI,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()

        return {
            "success": True,
            "chart_type": "pie_chart",
            "title": title,
            "image_path": chart_path,
            "data_points": len(df_grouped),
            "label_column": label_col,
            "value_column": value_col,
            "message": f"Pie chart created successfully with {len(df_grouped)} segments",
        }

    except Exception as e:
        plt.close()
        return {
            "success": False,
            "error": f"Pie chart creation failed: {str(e)}",
            "chart_type": "pie_chart",
            "title": title,
        }


def create_scatter_plot_core(
    query_results: Dict[str, Any],
    x_column: str,
    y_column: str,
    title: str = "Scatter Plot",
) -> Dict[str, Any]:
    """
    Create a scatter plot from query results.

    Args:
        query_results: Dictionary containing query results
        x_column: Name of the column for x-axis
        y_column: Name of the column for y-axis
        title: Chart title

    Returns:
        Dict containing chart creation results and file path
    """
    try:
        df = prepare_data_for_plotting(query_results)

        if x_column not in df.columns:
            raise ValueError(
                f"Column '{x_column}' not found. Available columns: {', '.join(df.columns)}"
            )
        if y_column not in df.columns:
            raise ValueError(
                f"Column '{y_column}' not found. Available columns: {', '.join(df.columns)}"
            )

        # Ensure columns are numeric
        for col in [x_column, y_column]:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Column '{col}' is not numeric and cannot be converted"
                    )

        # Remove null values
        df_clean = df[[x_column, y_column]].dropna()

        if len(df_clean) == 0:
            raise ValueError("No valid data after removing nulls")

        # Create the chart
        plt.figure(figsize=(DEFAULT_CHART_WIDTH, DEFAULT_CHART_HEIGHT), dpi=DEFAULT_DPI)

        plt.scatter(
            df_clean[x_column],
            df_clean[y_column],
            alpha=0.6,
            s=60,
            c="steelblue",
            edgecolors="navy",
            linewidth=0.5,
        )

        plt.title(title, fontsize=16, fontweight="bold", pad=20)
        plt.xlabel(x_column.replace("_", " ").title(), fontsize=12, fontweight="bold")
        plt.ylabel(y_column.replace("_", " ").title(), fontsize=12, fontweight="bold")
        plt.grid(True, alpha=0.3)

        # Add correlation coefficient
        correlation = df_clean[x_column].corr(df_clean[y_column])
        plt.text(
            0.05,
            0.95,
            f"Correlation: {correlation:.3f}",
            transform=plt.gca().transAxes,
            fontsize=12,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        plt.tight_layout()

        # Save chart
        chart_path = generate_chart_filename("scatter_plot", title)
        plt.savefig(
            chart_path,
            dpi=DEFAULT_DPI,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()

        return {
            "success": True,
            "chart_type": "scatter_plot",
            "title": title,
            "image_path": chart_path,
            "data_points": len(df_clean),
            "x_column": x_column,
            "y_column": y_column,
            "correlation": correlation,
            "message": f"Scatter plot created successfully with {len(df_clean)} data points",
        }

    except Exception as e:
        plt.close()
        return {
            "success": False,
            "error": f"Scatter plot creation failed: {str(e)}",
            "chart_type": "scatter_plot",
            "title": title,
        }


def create_box_plot_core(
    query_results: Dict[str, Any],
    column_name: str,
    group_column: str = None,
    title: str = "Box Plot",
) -> Dict[str, Any]:
    """
    Create a box plot from query results.

    Args:
        query_results: Dictionary containing query results
        column_name: Name of the numeric column to analyze
        group_column: Optional column to group by
        title: Chart title

    Returns:
        Dict containing chart creation results and file path
    """
    try:
        df = prepare_data_for_plotting(query_results)

        if column_name not in df.columns:
            raise ValueError(
                f"Column '{column_name}' not found. Available columns: {', '.join(df.columns)}"
            )

        # Ensure main column is numeric
        if not pd.api.types.is_numeric_dtype(df[column_name]):
            try:
                df[column_name] = pd.to_numeric(df[column_name])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Column '{column_name}' is not numeric and cannot be converted"
                )

        # Create the chart
        plt.figure(figsize=(DEFAULT_CHART_WIDTH, DEFAULT_CHART_HEIGHT), dpi=DEFAULT_DPI)

        if group_column and group_column in df.columns:
            # Grouped box plot
            groups = df[group_column].unique()
            data_by_group = [
                df[df[group_column] == group][column_name].dropna() for group in groups
            ]

            box_plot = plt.boxplot(data_by_group, labels=groups, patch_artist=True)

            # Color the boxes
            colors = plt.cm.Set3.colors[: len(groups)]
            for patch, color in zip(box_plot["boxes"], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            plt.xlabel(
                group_column.replace("_", " ").title(), fontsize=12, fontweight="bold"
            )
        else:
            # Single box plot
            data = df[column_name].dropna()
            box_plot = plt.boxplot(data, patch_artist=True)
            box_plot["boxes"][0].set_facecolor("steelblue")
            box_plot["boxes"][0].set_alpha(0.7)

        plt.title(title, fontsize=16, fontweight="bold", pad=20)
        plt.ylabel(
            column_name.replace("_", " ").title(), fontsize=12, fontweight="bold"
        )
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()

        # Save chart
        chart_path = generate_chart_filename("box_plot", title)
        plt.savefig(
            chart_path,
            dpi=DEFAULT_DPI,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()

        return {
            "success": True,
            "chart_type": "box_plot",
            "title": title,
            "image_path": chart_path,
            "data_points": len(df),
            "column": column_name,
            "group_column": group_column,
            "message": f"Box plot created successfully for {column_name}"
            + (f" grouped by {group_column}" if group_column else ""),
        }

    except Exception as e:
        plt.close()
        return {
            "success": False,
            "error": f"Box plot creation failed: {str(e)}",
            "chart_type": "box_plot",
            "title": title,
        }


def create_heatmap_core(
    query_results: Dict[str, Any], title: str = "Heatmap"
) -> Dict[str, Any]:
    """
    Create a correlation heatmap from query results.

    Args:
        query_results: Dictionary containing query results
        title: Chart title

    Returns:
        Dict containing chart creation results and file path
    """
    try:
        df = prepare_data_for_plotting(query_results)

        # Select only numeric columns
        numeric_df = df.select_dtypes(include=["number"])

        if len(numeric_df.columns) < 2:
            raise ValueError("Heatmap requires at least 2 numeric columns")

        # Calculate correlation matrix
        correlation_matrix = numeric_df.corr()

        # Create the chart
        plt.figure(figsize=(DEFAULT_CHART_WIDTH, DEFAULT_CHART_HEIGHT), dpi=DEFAULT_DPI)

        # Create heatmap

        # mask = np.triu(
        #     np.ones_like(correlation_matrix, dtype=bool)
        # )  # Mask upper triangle - commented out as not used

        im = plt.imshow(
            correlation_matrix, cmap="RdYlBu_r", aspect="auto", vmin=-1, vmax=1
        )

        # Add colorbar
        cbar = plt.colorbar(im)
        cbar.set_label("Correlation Coefficient", fontsize=12, fontweight="bold")

        # Set ticks and labels
        plt.xticks(
            range(len(correlation_matrix.columns)),
            [col.replace("_", " ").title() for col in correlation_matrix.columns],
            rotation=45,
            ha="right",
        )
        plt.yticks(
            range(len(correlation_matrix.columns)),
            [col.replace("_", " ").title() for col in correlation_matrix.columns],
        )

        # Add correlation values as text
        for i in range(len(correlation_matrix.columns)):
            for j in range(len(correlation_matrix.columns)):
                if i != j:  # Don't show 1.0 on diagonal
                    plt.text(
                        j,
                        i,
                        f"{correlation_matrix.iloc[i, j]:.2f}",
                        ha="center",
                        va="center",
                        color="black",
                        fontweight="bold",
                    )

        plt.title(title, fontsize=16, fontweight="bold", pad=20)
        plt.tight_layout()

        # Save chart
        chart_path = generate_chart_filename("heatmap", title)
        plt.savefig(
            chart_path,
            dpi=DEFAULT_DPI,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close()

        return {
            "success": True,
            "chart_type": "heatmap",
            "title": title,
            "image_path": chart_path,
            "data_points": len(df),
            "columns": list(numeric_df.columns),
            "message": f"Correlation heatmap created successfully for {len(numeric_df.columns)} numeric columns",
        }

    except Exception as e:
        plt.close()
        return {
            "success": False,
            "error": f"Heatmap creation failed: {str(e)}",
            "chart_type": "heatmap",
            "title": title,
        }


# Function tools for agent use
@function_tool
def analyze_data_for_visualization(query_results: str) -> Dict[str, Any]:
    """
    Analyze query results to determine the best visualization approach.

    This tool helps agents understand what type of chart would work best
    for a given dataset by analyzing the structure, data types, and size.

    Args:
        query_results: JSON string containing query results with 'results' key

    Returns:
        Dict containing analysis results and chart type recommendations
    """
    try:
        import json

        data = json.loads(query_results)
        return analyze_data_structure(data)
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON format in query results"}
    except Exception as e:
        return {"success": False, "error": f"Analysis failed: {str(e)}"}


@function_tool
def create_bar_chart(query_results: str, title: str = "Bar Chart") -> Dict[str, Any]:
    """
    Create a bar chart from SQL query results.

    This tool generates bar charts that are perfect for comparing categories,
    showing sales by product, counts by department, or any categorical comparisons.
    The chart file is saved and the path is returned for display or download.

    Args:
        query_results: JSON string containing query results with 'results' key
        title: Title for the chart

    Returns:
        Dict containing success status, file path, and chart metadata
    """
    try:
        import json

        data = json.loads(query_results)
        return create_bar_chart_core(data, title)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON format in query results",
            "chart_type": "bar_chart",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Bar chart creation failed: {str(e)}",
            "chart_type": "bar_chart",
        }


@function_tool
def create_line_plot(query_results: str, title: str = "Line Plot") -> Dict[str, Any]:
    """
    Create a line plot from SQL query results.

    This tool generates line plots that are ideal for showing trends over time,
    relationships between variables, or sequential data patterns.

    Args:
        query_results: JSON string containing query results with 'results' key
        title: Title for the chart

    Returns:
        Dict containing success status, file path, and chart metadata
    """
    try:
        import json

        data = json.loads(query_results)
        return create_line_plot_core(data, title)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON format in query results",
            "chart_type": "line_plot",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Line plot creation failed: {str(e)}",
            "chart_type": "line_plot",
        }


@function_tool
def create_histogram(
    query_results: str, column_name: str, title: str = "Histogram"
) -> Dict[str, Any]:
    """
    Create a histogram from SQL query results.

    This tool generates histograms that show the distribution of numeric data,
    including statistics like mean, median, and standard deviation.

    Args:
        query_results: JSON string containing query results with 'results' key
        column_name: Name of the numeric column to create histogram for
        title: Title for the chart

    Returns:
        Dict containing success status, file path, chart metadata, and statistics
    """
    try:
        import json

        data = json.loads(query_results)
        return create_histogram_core(data, column_name, title)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON format in query results",
            "chart_type": "histogram",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Histogram creation failed: {str(e)}",
            "chart_type": "histogram",
        }


@function_tool
def create_pie_chart(query_results: str, title: str = "Pie Chart") -> Dict[str, Any]:
    """
    Create a pie chart from SQL query results.

    This tool generates pie charts that are perfect for showing proportions
    and percentages of categorical data, like market share or budget allocation.

    Args:
        query_results: JSON string containing query results with 'results' key
        title: Title for the chart

    Returns:
        Dict containing success status, file path, and chart metadata
    """
    try:
        import json

        data = json.loads(query_results)
        return create_pie_chart_core(data, title)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON format in query results",
            "chart_type": "pie_chart",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Pie chart creation failed: {str(e)}",
            "chart_type": "pie_chart",
        }


@function_tool
def create_scatter_plot(
    query_results: str, x_column: str, y_column: str, title: str = "Scatter Plot"
) -> Dict[str, Any]:
    """
    Create a scatter plot from SQL query results.

    This tool generates scatter plots that show relationships between two numeric
    variables, including correlation coefficients to measure the strength of relationships.

    Args:
        query_results: JSON string containing query results with 'results' key
        x_column: Name of the column for x-axis
        y_column: Name of the column for y-axis
        title: Title for the chart

    Returns:
        Dict containing success status, file path, correlation, and chart metadata
    """
    try:
        import json

        data = json.loads(query_results)
        return create_scatter_plot_core(data, x_column, y_column, title)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON format in query results",
            "chart_type": "scatter_plot",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Scatter plot creation failed: {str(e)}",
            "chart_type": "scatter_plot",
        }


@function_tool
def create_box_plot(
    query_results: str,
    column_name: str,
    group_column: str = None,
    title: str = "Box Plot",
) -> Dict[str, Any]:
    """
    Create a box plot from SQL query results.

    This tool generates box plots that show data distribution, quartiles, and outliers.
    Can create grouped box plots to compare distributions across categories.

    Args:
        query_results: JSON string containing query results with 'results' key
        column_name: Name of the numeric column to analyze
        group_column: Optional column to group by for comparative box plots
        title: Title for the chart

    Returns:
        Dict containing success status, file path, and chart metadata
    """
    try:
        import json

        data = json.loads(query_results)
        return create_box_plot_core(data, column_name, group_column, title)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON format in query results",
            "chart_type": "box_plot",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Box plot creation failed: {str(e)}",
            "chart_type": "box_plot",
        }


@function_tool
def create_heatmap(
    query_results: str, title: str = "Correlation Heatmap"
) -> Dict[str, Any]:
    """
    Create a correlation heatmap from SQL query results.

    This tool generates correlation heatmaps that show relationships between
    multiple numeric variables in a matrix format with color coding.

    Args:
        query_results: JSON string containing query results with 'results' key
        title: Title for the chart

    Returns:
        Dict containing success status, file path, and chart metadata
    """
    try:
        import json

        data = json.loads(query_results)
        return create_heatmap_core(data, title)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON format in query results",
            "chart_type": "heatmap",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Heatmap creation failed: {str(e)}",
            "chart_type": "heatmap",
        }
