"""
Pydantic Models for Agent System

Self-contained Pydantic models extracted from Week 1 csv_agents.py
for use in the Week 3 containerized application.
"""

from pydantic import BaseModel
from typing import List, Optional


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
