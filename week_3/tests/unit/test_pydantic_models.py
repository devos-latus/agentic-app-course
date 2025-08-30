"""
Unit tests for Pydantic models in CSV Analytics Agents.

Tests the validation, serialization, and data structure enforcement
of the Pydantic models used for structured agent outputs.

Key concepts:
- Pydantic model validation and type checking
- Required vs optional field handling
- Data structure consistency enforcement
- Error handling for invalid inputs

Use cases:
- Testing AnalysisResult model for analysis operations
- Testing QueryPlan model for SQL query planning
- Testing QueryEvaluation model for result evaluation
- Validating error handling for malformed data
"""

import pytest
import sys
from pathlib import Path
from pydantic import ValidationError

# Add the week_3/src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents_.pydantic_models import AnalysisResult, QueryPlan, QueryEvaluation


class TestAnalysisResult:
    """Test the AnalysisResult Pydantic model."""

    def test_analysis_result_valid_minimal(self):
        """Test AnalysisResult with minimal required fields."""
        result = AnalysisResult(
            success=True,
            result_type="average",
            message="Calculation completed successfully",
        )

        assert result.success is True
        assert result.result_type == "average"
        assert result.message == "Calculation completed successfully"
        assert result.value is None  # Optional field
        assert result.suggestions is None  # Optional field

    def test_analysis_result_valid_complete(self):
        """Test AnalysisResult with all fields populated."""
        result = AnalysisResult(
            success=True,
            result_type="count",
            value=42.5,
            message="Found 42.5 average value",
            suggestions=["Check for outliers", "Consider filtering data"],
        )

        assert result.success is True
        assert result.result_type == "count"
        assert result.value == 42.5
        assert result.message == "Found 42.5 average value"
        assert result.suggestions == ["Check for outliers", "Consider filtering data"]

    def test_analysis_result_error_case(self):
        """Test AnalysisResult for error scenarios."""
        result = AnalysisResult(
            success=False,
            result_type="error",
            message="Table 'nonexistent' does not exist",
            suggestions=["Check available tables", "Verify table name spelling"],
        )

        assert result.success is False
        assert result.result_type == "error"
        assert result.message == "Table 'nonexistent' does not exist"
        assert result.value is None
        assert len(result.suggestions) == 2

    def test_analysis_result_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisResult(success=True)  # Missing result_type and message

        error = exc_info.value
        assert "Field required" in str(error)
        assert "result_type" in str(error)
        assert "message" in str(error)

    def test_analysis_result_invalid_types(self):
        """Test that invalid field types raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisResult(
                success="not_a_boolean",  # Should be bool but can't be coerced
                result_type=123,  # Should be str
                message=["not", "a", "string"],  # Should be str
            )

        error = exc_info.value
        # Check for any of the expected validation errors
        error_str = str(error)
        assert (
            "Input should be a valid string" in error_str
            or "Input should be a valid boolean" in error_str
        )


class TestQueryPlan:
    """Test the QueryPlan Pydantic model."""

    def test_query_plan_valid_simple(self):
        """Test QueryPlan with valid simple query data."""
        plan = QueryPlan(
            query_type="simple",
            tables_needed=["employees"],
            columns_needed=["name", "salary"],
            operations=["SELECT"],
            complexity="simple",
            explanation="Basic employee salary lookup",
        )

        assert plan.query_type == "simple"
        assert plan.tables_needed == ["employees"]
        assert plan.columns_needed == ["name", "salary"]
        assert plan.operations == ["SELECT"]
        assert plan.complexity == "simple"
        assert plan.explanation == "Basic employee salary lookup"

    def test_query_plan_valid_complex(self):
        """Test QueryPlan with complex query requirements."""
        plan = QueryPlan(
            query_type="aggregation",
            tables_needed=["sales", "products"],
            columns_needed=["product_id", "revenue", "category"],
            operations=["SELECT", "JOIN", "GROUP BY", "ORDER BY"],
            complexity="complex",
            explanation="Revenue analysis by product category with ranking",
        )

        assert plan.query_type == "aggregation"
        assert len(plan.tables_needed) == 2
        assert len(plan.columns_needed) == 3
        assert len(plan.operations) == 4
        assert plan.complexity == "complex"
        assert "ranking" in plan.explanation

    def test_query_plan_empty_lists(self):
        """Test QueryPlan with empty lists (edge case)."""
        plan = QueryPlan(
            query_type="filtering",
            tables_needed=[],
            columns_needed=[],
            operations=["SELECT", "WHERE"],
            complexity="medium",
            explanation="Filter operation with no specific tables identified yet",
        )

        assert plan.tables_needed == []
        assert plan.columns_needed == []
        assert len(plan.operations) == 2

    def test_query_plan_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            QueryPlan(
                query_type="simple",
                tables_needed=["test"],
                # Missing other required fields
            )

        error = exc_info.value
        assert "Field required" in str(error)

    def test_query_plan_invalid_list_types(self):
        """Test that invalid list field types raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            QueryPlan(
                query_type="simple",
                tables_needed="not_a_list",  # Should be List[str]
                columns_needed=["valid"],
                operations=["SELECT"],
                complexity="simple",
                explanation="Test",
            )

        error = exc_info.value
        assert "Input should be a valid list" in str(error)


class TestQueryEvaluation:
    """Test the QueryEvaluation Pydantic model."""

    def test_query_evaluation_valid_success(self):
        """Test QueryEvaluation for successful query results."""
        evaluation = QueryEvaluation(
            answers_question=True,
            confidence_level="high",
            result_summary="Found 156 employees with average salary of $75,000",
            next_action="return_result",
        )

        assert evaluation.answers_question is True
        assert evaluation.confidence_level == "high"
        assert (
            evaluation.result_summary
            == "Found 156 employees with average salary of $75,000"
        )
        assert evaluation.data_quality_notes is None  # Optional field
        assert evaluation.next_action == "return_result"

    def test_query_evaluation_valid_with_notes(self):
        """Test QueryEvaluation with data quality notes."""
        evaluation = QueryEvaluation(
            answers_question=True,
            confidence_level="medium",
            result_summary="Revenue trends show 15% growth",
            data_quality_notes="Some missing data for Q1 2023",
            next_action="return_result",
        )

        assert evaluation.answers_question is True
        assert evaluation.confidence_level == "medium"
        assert evaluation.data_quality_notes == "Some missing data for Q1 2023"
        assert evaluation.next_action == "return_result"

    def test_query_evaluation_needs_retry(self):
        """Test QueryEvaluation when query needs to be retried."""
        evaluation = QueryEvaluation(
            answers_question=False,
            confidence_level="low",
            result_summary="Query returned empty results",
            data_quality_notes="Filter conditions may be too restrictive",
            next_action="retry_query",
        )

        assert evaluation.answers_question is False
        assert evaluation.confidence_level == "low"
        assert evaluation.next_action == "retry_query"
        assert "restrictive" in evaluation.data_quality_notes

    def test_query_evaluation_needs_clarification(self):
        """Test QueryEvaluation when user clarification is needed."""
        evaluation = QueryEvaluation(
            answers_question=False,
            confidence_level="low",
            result_summary="Ambiguous query results",
            next_action="need_clarification",
        )

        assert evaluation.answers_question is False
        assert evaluation.next_action == "need_clarification"

    def test_query_evaluation_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            QueryEvaluation(
                answers_question=True,
                confidence_level="high",
                # Missing result_summary and next_action
            )

        error = exc_info.value
        assert "Field required" in str(error)

    def test_query_evaluation_invalid_boolean(self):
        """Test that invalid boolean values raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            QueryEvaluation(
                answers_question="maybe",  # Should be bool
                confidence_level="high",
                result_summary="Test results",
                next_action="return_result",
            )

        error = exc_info.value
        assert "Input should be a valid boolean" in str(error)


class TestModelSerialization:
    """Test serialization and deserialization of models."""

    def test_analysis_result_to_dict(self):
        """Test AnalysisResult serialization to dictionary."""
        result = AnalysisResult(
            success=True,
            result_type="average",
            value=42.5,
            message="Test message",
            suggestions=["suggestion1", "suggestion2"],
        )

        data = result.model_dump()

        assert data["success"] is True
        assert data["result_type"] == "average"
        assert data["value"] == 42.5
        assert data["message"] == "Test message"
        assert data["suggestions"] == ["suggestion1", "suggestion2"]

    def test_query_plan_from_dict(self):
        """Test QueryPlan creation from dictionary."""
        data = {
            "query_type": "aggregation",
            "tables_needed": ["sales"],
            "columns_needed": ["revenue"],
            "operations": ["SELECT", "SUM"],
            "complexity": "medium",
            "explanation": "Sum revenue calculation",
        }

        plan = QueryPlan(**data)

        assert plan.query_type == "aggregation"
        assert plan.tables_needed == ["sales"]
        assert plan.operations == ["SELECT", "SUM"]

    def test_query_evaluation_json_serialization(self):
        """Test QueryEvaluation JSON serialization."""
        evaluation = QueryEvaluation(
            answers_question=True,
            confidence_level="high",
            result_summary="All good",
            next_action="return_result",
        )

        json_str = evaluation.model_dump_json()

        assert '"answers_question":true' in json_str
        assert '"confidence_level":"high"' in json_str
        assert '"result_summary":"All good"' in json_str
        assert '"next_action":"return_result"' in json_str


class TestModelValidation:
    """Test comprehensive model validation scenarios."""

    def test_analysis_result_none_values(self):
        """Test AnalysisResult handles None values correctly for optional fields."""
        result = AnalysisResult(
            success=False,
            result_type="error",
            message="Error occurred",
            value=None,
            suggestions=None,
        )

        assert result.value is None
        assert result.suggestions is None

    def test_query_plan_type_consistency(self):
        """Test QueryPlan maintains type consistency."""
        plan = QueryPlan(
            query_type="simple",
            tables_needed=["table1", "table2"],
            columns_needed=["col1", "col2", "col3"],
            operations=["SELECT", "WHERE"],
            complexity="simple",
            explanation="Test query",
        )

        # Verify all list elements are strings
        assert all(isinstance(table, str) for table in plan.tables_needed)
        assert all(isinstance(col, str) for col in plan.columns_needed)
        assert all(isinstance(op, str) for op in plan.operations)

    def test_query_evaluation_optional_field_behavior(self):
        """Test QueryEvaluation optional field default behavior."""
        evaluation = QueryEvaluation(
            answers_question=True,
            confidence_level="medium",
            result_summary="Test summary",
            next_action="return_result",
            # data_quality_notes not provided
        )

        assert evaluation.data_quality_notes is None

        # Test with explicit None
        evaluation2 = QueryEvaluation(
            answers_question=True,
            confidence_level="medium",
            result_summary="Test summary",
            data_quality_notes=None,
            next_action="return_result",
        )

        assert evaluation2.data_quality_notes is None
