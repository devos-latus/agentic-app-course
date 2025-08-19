"""
CSV Analytics Agents

This module defines AI agents for CSV data analysis and user interaction.
The agents work together to provide natural language access to CSV data through
SQLite queries and intelligent responses.

Key concepts:
- Multi-Agent Architecture: Specialized agents with handoff relationships
- Structured Output: Pydantic models for consistent agent responses
- Function Tools Integration: Agents use tools to access and analyze data
- Agent Instructions: Clear behavioral guidelines for consistent responses
- Natural Language Interface: Users can ask questions about data in plain English

Use cases:
- Data discovery and explanation for new users
- Statistical analysis and calculations
- Complex SQL query planning and execution
- Error handling and user guidance
- Friendly interface to technical data analysis capabilities
"""

import os
from pydantic import BaseModel
from typing import List, Optional

# Disable OpenAI agents internal tracing
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

from agents import (
    Agent,
    Runner,
    input_guardrail,
    output_guardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
)
from agentic_app_quickstart.examples.helpers import get_model
from tools import (
    get_all_tables,
    get_table_schema,
    get_column_names,
    calculate_column_average,
    count_rows_with_value,
    execute_sql_query,
    execute_sql_analysis,
    load_csv_file,
    discover_and_load_csv_files,
)
from visualization_tools import (
    analyze_data_for_visualization,
    create_bar_chart,
    create_line_plot,
    create_histogram,
    create_pie_chart,
    create_scatter_plot,
    create_box_plot,
    create_heatmap,
)


# Pydantic models for guardrails
class AnalyticsTopicCheck(BaseModel):
    """
    Output structure for analytics topic guardrail.

    Ensures user questions are related to data analysis, CSV data, or statistics.
    """

    is_analytics_related: bool  # True if question is about analytics/data analysis
    reasoning: str  # Explanation of the decision


class ResponseTopicCheck(BaseModel):
    """
    Output structure for response topic guardrail.

    Ensures agent responses stay focused on analytics and data analysis.
    """

    is_on_topic: bool  # True if response is about analytics/data
    reasoning: str  # Explanation of the decision


# Pydantic models for structured agent outputs
class AnalysisResult(BaseModel):
    """
    Structured output for analysis operations.

    This model ensures consistent formatting of analysis results
    across different types of calculations and operations.
    """

    success: bool
    result_type: str  # "average", "count", "schema", "error"
    value: Optional[float] = None
    message: str
    suggestions: Optional[List[str]] = None


class QueryPlan(BaseModel):
    """
    Structured output for SQL query planning.

    This model defines the structure for query planning decisions
    and requirements for SQL generation.
    """

    query_type: str  # "simple", "aggregation", "grouping", "filtering"
    tables_needed: List[str]
    columns_needed: List[str]
    operations: List[str]  # "SELECT", "WHERE", "GROUP BY", "ORDER BY", etc.
    complexity: str  # "simple", "medium", "complex"
    explanation: str


class QueryEvaluation(BaseModel):
    """
    Structured output for query result evaluation.

    This model defines the structure for evaluating whether
    query results properly answer the user's question.
    """

    answers_question: bool
    confidence_level: str  # "high", "medium", "low"
    result_summary: str
    data_quality_notes: Optional[str] = None
    next_action: str  # "return_result", "retry_query", "need_clarification"


# Guardrail Agents
input_guardrail_agent = Agent(
    name="AnalyticsInputGuardrail",
    instructions="""You are a guardrail for a CSV analytics system. 

ALLOW questions about:
- Data analysis, statistics, calculations (even if the specific request might be invalid)
- CSV files, datasets, tables, columns
- Data exploration, trends, patterns
- Loading or querying data
- Charts, graphs, visualizations from data
- Downloading or exporting charts
- Questions about generated visualizations

IMPORTANT: Allow data analysis questions even if they might have technical issues (like averaging text columns).
The Analytics Agent will handle specific errors and provide helpful guidance.

ONLY BLOCK questions that are clearly unrelated to data analysis:
- General conversation, personal questions
- Non-data topics (weather, sports, politics)
- Technical support unrelated to CSV analysis
- Programming help not related to data analysis

Return is_analytics_related=true for data analysis questions, even if they contain errors.
Return false only for completely unrelated topics.""",
    model=get_model(),
    output_type=AnalyticsTopicCheck,
)


output_guardrail_agent = Agent(
    name="AnalyticsOutputGuardrail",
    instructions="""You are a guardrail for CSV analytics responses.

ALLOW responses about:
- Data analysis results and statistics  
- Dataset information and structure
- Analytics guidance and insights
- Data calculations and trends
- Chart and visualization information
- File paths for generated charts
- Visualization metadata and download instructions
- Error messages and troubleshooting for data analysis
- Helpful guidance when data operations fail
- Suggestions for fixing data analysis problems

IMPORTANT: Allow error messages and guidance that help users with data analysis issues.
These are still within the analytics domain and provide value to users.

ONLY BLOCK responses that are completely unrelated to data analysis:
- General conversation, personal topics
- Non-data subjects (weather, sports, politics)
- Technical support unrelated to CSV/data analysis

Return is_on_topic=true for analytics responses AND helpful error guidance.
Return false only for completely unrelated topics.""",
    model=get_model(),
    output_type=ResponseTopicCheck,
)


# Guardrail Functions
@input_guardrail
async def analytics_input_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
):
    """
    Input guardrail that ensures user questions are analytics-related.

    Blocks off-topic questions and guides users back to data analysis topics.
    """
    result = await Runner.run(input_guardrail_agent, input=input, context=ctx)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_analytics_related,
    )


@output_guardrail
async def analytics_output_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, output: str
):
    """
    Output guardrail that ensures agent responses stay on analytics topics.

    Redirects off-topic responses back to data analysis focus.
    """
    result = await Runner.run(
        output_guardrail_agent, input=f"Agent response: {output}", context=ctx
    )

    if not result.final_output.is_on_topic:
        return GuardrailFunctionOutput(
            output_info=result.final_output, tripwire_triggered=True
        )

    return GuardrailFunctionOutput(
        output_info=result.final_output, tripwire_triggered=False
    )


# Communication Agent - Formats responses in user-friendly language
communication_agent = Agent(
    name="CommunicationAgent",
    instructions="""You are the main CSV Analytics assistant that orchestrates specialist agents and presents final results.

CORE RESPONSIBILITIES:
- Welcome users and show available datasets
- Route analysis questions to Analytics Agent
- Route data loading to Data Loader Agent  
- Format specialist results into user-friendly responses
- Maintain conversation context for follow-ups

MEMORY-FIRST APPROACH:
- Check conversation memory before using tools
- Use stored dataset metadata when available
- Only call tools if information is missing from memory

ORCHESTRATION FLOW:
1. Analysis questions → Transfer to Analytics Agent → Format their results
2. Data loading → Transfer to Data Loader Agent → Confirm results
3. Always be the final presenter to users

ERROR HANDLING:
- State problems clearly: "Table 'X' does not exist"
- Show available alternatives immediately
- Don't ask permission - provide helpful options

WELCOME FORMAT:
- Brief greeting
- List datasets (name, rows, key columns)
- 3 example questions""",
    model=get_model(),
    tools=[get_all_tables, get_column_names, get_table_schema],
    input_guardrails=[analytics_input_guardrail],
    output_guardrails=[analytics_output_guardrail],
)


# Analytics Agent - Performs calculations and statistical analysis
analytics_agent = Agent(
    name="AnalyticsAgent",
    instructions="""You are a data analytics specialist that performs calculations and decides when to create visualizations.

TOOL SELECTION:
- Simple stats (average, count): calculate_column_average(), count_rows_with_value()
- Complex stats (median, max, min): execute_sql_analysis()
- Schema info: get_table_schema() (sparingly)
- Raw data for visualization: execute_sql_query()

CONTEXT HANDLING:
- Check conversation memory for table/column context
- For follow-ups like "What about the median?" - infer from recent conversation

VISUALIZATION DECISION WORKFLOW:
You are the ONLY agent that can decide to create visualizations:
1. When users request charts/graphs OR when results would benefit from visualization
2. Use execute_sql_query() to get the raw data needed for the chart
3. If successful, handoff to Visualization Agent with: "Create [chart_type] using this data: [query_results_json]"
4. The Visualization Agent will handle chart creation and return to Communication Agent

REGULAR ANALYTICS WORKFLOW:
1. Identify analysis type and required table/column from context
2. Choose appropriate tool and execute
3. Decide: Should this result be visualized?
4. If yes → handoff to Visualization Agent with data
5. If no → transfer results back to Communication Agent

VISUALIZATION CRITERIA:
Consider visualization when:
- User explicitly requests charts/graphs
- Results contain categorical comparisons (good for bar charts)
- Results show trends or time series (good for line plots)
- Results show distributions (good for histograms)

AVAILABLE VISUALIZATION TYPES ONLY:
- Bar Charts, Line Plots, Histograms, Pie Charts, Scatter Plots, Box Plots, Heatmaps
- If users request unsupported chart types (area charts, bubble charts, treemaps, etc.), 
  explain that only the above types are available and suggest the best alternative

ERROR HANDLING:
- State problem clearly: "Table 'X' does not exist"
- Show available alternatives from error messages immediately""",
    model=get_model(),
    tools=[
        calculate_column_average,
        count_rows_with_value,
        get_column_names,
        execute_sql_analysis,
        get_table_schema,
        get_all_tables,
        execute_sql_query,
    ],
)


# Query Planner Agent - Plans SQL queries for complex analysis
query_planner_agent = Agent(
    name="QueryPlannerAgent",
    instructions="""You analyze data questions and create structured SQL query plans.

CORE FUNCTION:
- Analyze complex data questions requiring SQL
- Create structured QueryPlan with: query_type, tables_needed, columns_needed, operations, complexity, explanation
- Use memory for table schemas when available

WORKFLOW:
1. Identify required tables/columns
2. Determine SQL operations (GROUP BY, WHERE, etc.)
3. Classify complexity (simple/medium/complex)
4. Output complete QueryPlan structure""",
    model=get_model(),
    tools=[get_all_tables, get_column_names, get_table_schema],
    output_type=QueryPlan,
)


# SQL Writer Agent - Writes and executes SQL queries
sql_writer_agent = Agent(
    name="SQLWriterAgent",
    instructions="""You write and execute SQL queries based on query plans.

CORE FUNCTION:
- Convert QueryPlan specifications to SQL
- Execute queries using execute_sql_query tool
- Use proper SQLite syntax with NULL handling

WORKFLOW:
1. Receive query plan specifications
2. Write appropriate SELECT query
3. Execute and return results""",
    model=get_model(),
    tools=[execute_sql_query, get_column_names, get_table_schema],
)


# Query Evaluator Agent - Evaluates results and performs sanity checks
query_evaluator_agent = Agent(
    name="QueryEvaluatorAgent",
    instructions="""You evaluate SQL results and determine if they answer the user's question.

CORE FUNCTION:
- Compare query results with original question
- Perform sanity checks when needed
- Output structured QueryEvaluation: answers_question, confidence_level, result_summary, data_quality_notes, next_action

EVALUATION CRITERIA:
- If the query executed successfully and returned relevant data that answers the user's question, set answers_question=True and next_action="return_result"
- Only set answers_question=False if the results are genuinely incorrect, empty when they shouldn't be, or don't address the question
- Don't be overly critical - if the query worked and provided a reasonable answer, mark it as successful

SANITY CHECKS:
- Verify totals, ranges, and data integrity
- Run additional queries only if results seem suspicious or incomplete

WORKFLOW:
1. Evaluate if results answer the question (be generous with successful queries)
2. Check data quality and completeness
3. Determine confidence level and next action (prefer "return_result" for working queries)""",
    model=get_model(),
    tools=[execute_sql_query, get_column_names, get_table_schema],
    output_type=QueryEvaluation,
)


# Data Loader Agent - Handles CSV file operations and data preparation
data_loader_agent = Agent(
    name="DataLoaderAgent",
    instructions="""You are a data loading specialist that handles CSV file operations and data preparation.

Your role:
- Load individual CSV files into the analytics system with proper validation
- Discover and batch load multiple CSV files from directories  
- Handle file validation and provide clear error reporting
- Guide users on proper CSV format requirements and troubleshooting
- Provide detailed feedback about successful/failed loads with metadata
- Provide comprehensive feedback after loading operations

IMPORTANT - File Operations:
- Use load_csv_file() for single file uploads from users
- Use discover_and_load_csv_files() for batch loading from directories
- Always validate file paths and provide helpful error messages
- Show table names, row counts, and column info for successful loads

Available tools:
- load_csv_file(file_path, table_name): Load a single CSV file with custom table name
- discover_and_load_csv_files(directory_path): Batch load all CSV files from a directory
- get_all_tables(): Show currently loaded datasets for verification

How to handle requests:
1. For single file uploads: "Load [file_path] as [table_name]"
2. For directory scanning: "Load all CSV files from [directory]"
3. For status checks: "What data is currently loaded?"
4. Always provide clear success/failure feedback with details

Response format:
- Confirm what operation you're performing
- Execute the appropriate loading tool
- Report results clearly (successes, failures, metadata)
- Provide guidance on next steps or error resolution
- Always provide clear and complete responses

ERROR HANDLING - When file operations fail:
- IMMEDIATELY state what went wrong: "File not found" or "Invalid CSV format"
- Provide specific suggestions for fixing the issue
- Show available alternatives when relevant (existing tables, valid paths)
- Guide users on proper file format requirements""",
    model=get_model(),
    tools=[
        load_csv_file,
        discover_and_load_csv_files,
        get_all_tables,
        get_table_schema,
    ],
)


# Visualization Agent - Creates charts and visualizations from data
visualization_agent = Agent(
    name="VisualizationAgent",
    instructions="""You are a data visualization specialist that creates charts from query results.

CORE RESPONSIBILITIES:
- Receive query results data from Analytics Agent
- Analyze data to recommend the best chart type
- Generate bar charts, line plots, and histograms
- Save charts as downloadable PNG files
- Provide chart file paths and metadata to users

EXPECTED INPUT FORMAT:
You will receive messages with data to visualize. This could be:
- "Create bar chart using this data: {JSON_query_results}"
- Raw JSON data that needs to be visualized
- Data arrays that should be converted to charts

WORKFLOW:
1. If you receive JSON data or data arrays, IMMEDIATELY create a chart
2. Analyze the data structure to determine the best chart type
3. Use the appropriate visualization tool to create the chart
4. Return the chart file path and details for download
5. DO NOT just echo back the data - always create an actual chart file

CHART TYPE SELECTION:
- Bar Charts: Categorical data comparisons (sales by product, counts by department)
- Line Plots: Trends over time or sequential data
- Histograms: Distribution of numeric values with statistics
- Pie Charts: Proportions and percentages (market share, budget allocation)
- Scatter Plots: Relationships between two numeric variables with correlation
- Box Plots: Data distribution, quartiles, and outliers (can be grouped)
- Heatmaps: Correlation matrices for multiple numeric variables

TOOLS AVAILABLE:
- analyze_data_for_visualization(): Analyze data and suggest chart types
- create_bar_chart(): Generate bar charts for categorical comparisons
- create_line_plot(): Generate line plots for trends and relationships  
- create_histogram(): Generate histograms for numeric distributions
- create_pie_chart(): Generate pie charts for proportions and percentages
- create_scatter_plot(): Generate scatter plots with correlation analysis
- create_box_plot(): Generate box plots for distribution analysis
- create_heatmap(): Generate correlation heatmaps for multiple variables

RESPONSE FORMAT:
- ALWAYS create an actual chart file - never just display data
- Confirm what chart type you're creating and why
- Execute the appropriate visualization tool (create_bar_chart, create_pie_chart, etc.)
- Report the exact chart file location for download
- Provide chart metadata (data points, columns used, etc.)
- Say something like: "Bar chart created successfully! Chart saved to: [full_file_path]"
- Include the complete file path so users can access the chart

ERROR HANDLING:
- If no data is provided, ask Analytics Agent to provide query results
- State visualization problems clearly
- Suggest alternative chart types if data doesn't fit
- Provide guidance on data format requirements

UNSUPPORTED CHART TYPES:
If users request chart types not in the available list, respond with:
"I can only create these chart types: Bar Charts, Line Plots, Histograms, Pie Charts, Scatter Plots, Box Plots, and Heatmaps. 
[Explain which of these would work best for their data instead]"

AVAILABLE CHART TYPES ONLY:
- Bar Charts, Line Plots, Histograms, Pie Charts, Scatter Plots, Box Plots, Heatmaps
- NO other chart types are supported (no area charts, bubble charts, treemaps, etc.)
- Always suggest the best available alternative""",
    model=get_model(),
    tools=[
        analyze_data_for_visualization,
        create_bar_chart,
        create_line_plot,
        create_histogram,
        create_pie_chart,
        create_scatter_plot,
        create_box_plot,
        create_heatmap,
    ],
)

# Set up agent handoffs (following 05_handoffs.py pattern)
# IMPORTANT: Only Analytics Agent can handoff to Visualization Agent
# This keeps visualization separate from the deterministic SQL execution chain
communication_agent.handoffs = [analytics_agent, data_loader_agent]
analytics_agent.handoffs = [
    communication_agent,
    query_planner_agent,
    visualization_agent,
]
query_planner_agent.handoffs = [sql_writer_agent]
sql_writer_agent.handoffs = [query_evaluator_agent]
query_evaluator_agent.handoffs = [
    communication_agent,
    query_planner_agent,
    sql_writer_agent,
]  # NO visualization_agent
data_loader_agent.handoffs = [communication_agent]
visualization_agent.handoffs = [communication_agent]  # Only back to communication

# Agent registry for easy lookup
agents = {
    "communication": communication_agent,
    "analytics": analytics_agent,
    "query_planner": query_planner_agent,
    "sql_writer": sql_writer_agent,
    "query_evaluator": query_evaluator_agent,
    "data_loader": data_loader_agent,
    "visualization": visualization_agent,
}
