"""
LLM-as-Judge Test Evaluation Framework

This module provides semantic evaluation of agent responses using LLM judgment
instead of brittle string matching. It evaluates whether responses meet
qualitative requirements like helpfulness, clarity, and user-friendliness.

Key concepts:
- Semantic evaluation over exact string matching
- Flexible criteria-based assessment
- Robust testing that survives message changes
- Qualitative response evaluation

Use cases:
- Evaluating error message quality
- Testing conversational agent responses
- Assessing user experience factors
- Validating agent behavior semantically
"""

from typing import Dict, List, Optional
from pydantic import BaseModel

# Import the model helper for consistency
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "week_1" / "solution"))
from agentic_app_quickstart.examples.helpers import get_model
from agents import Agent, Runner, set_tracing_disabled

# Disable tracing for cleaner test output
set_tracing_disabled(True)


class EvaluationCriteria(BaseModel):
    """Criteria for evaluating agent responses."""

    helpfulness: str  # Does it explain what went wrong clearly?
    actionability: str  # Does it suggest how to fix the issue?
    user_friendliness: str  # Is it conversational, not technical?
    accuracy: str  # Does it correctly identify the problem?


class EvaluationResult(BaseModel):
    """Result of LLM evaluation."""

    passes: bool  # Overall pass/fail
    helpfulness_score: int  # 1-5 scale
    actionability_score: int  # 1-5 scale
    user_friendliness_score: int  # 1-5 scale
    accuracy_score: int  # 1-5 scale
    overall_score: float  # Average score
    reasoning: str  # Explanation of the evaluation
    suggestions: Optional[str] = None  # Suggestions for improvement


# Create the LLM judge agent
llm_judge = Agent(
    name="TestEvaluationJudge",
    instructions="""You are an expert evaluator of conversational AI responses, specifically for data analysis assistants.

Your job is to evaluate agent responses against specific criteria and determine if they meet quality standards.

EVALUATION CRITERIA (Rate each 1-5, where 5 is excellent):

1. HELPFULNESS (1-5): Does the response clearly explain what went wrong? 
   - 5: Crystal clear explanation of the specific issue
   - 3: Adequate explanation but could be clearer  
   - 1: Vague or confusing explanation

2. ACTIONABILITY (1-5): Does it suggest concrete steps to fix the issue?
   - 5: Provides specific, actionable next steps
   - 3: Some guidance but not very specific
   - 1: No actionable suggestions

3. USER-FRIENDLINESS (1-5): Is it conversational and accessible, not technical?
   - 5: Natural, conversational tone; avoids jargon
   - 3: Somewhat conversational but has technical terms
   - 1: Technical, cold, or hard to understand

4. ACCURACY (1-5): Does it correctly identify and describe the problem?
   - 5: Perfectly accurate diagnosis of the issue
   - 3: Mostly accurate with minor issues
   - 1: Inaccurate or misleading

RESPONSE FORMAT:
- Provide scores for each criterion (1-5)
- Calculate overall score (average of all criteria)
- Determine PASSES (true/false): Overall score >= 3.5 AND no individual score < 2
- Give reasoning explaining your evaluation
- Suggest improvements if score < 4.0

Be thorough but concise. Focus on the user experience.""",
    model=get_model(),
    output_type=EvaluationResult,
)


async def evaluate_error_response(
    response: str, scenario: str, expected_behavior: str, context: Optional[str] = None
) -> EvaluationResult:
    """
    Evaluate an agent's error response using LLM judgment.

    Args:
        response: The agent's response to evaluate
        scenario: Description of the error scenario
        expected_behavior: What the response should accomplish
        context: Optional additional context about the test

    Returns:
        EvaluationResult with scores and pass/fail determination
    """

    evaluation_prompt = f"""
SCENARIO: {scenario}

EXPECTED BEHAVIOR: {expected_behavior}

AGENT RESPONSE TO EVALUATE:
"{response}"

{f"ADDITIONAL CONTEXT: {context}" if context else ""}

Please evaluate this response against the four criteria (Helpfulness, Actionability, User-Friendliness, Accuracy) and provide your assessment.
"""

    try:
        result = await Runner.run(starting_agent=llm_judge, input=evaluation_prompt)

        return result.final_output

    except Exception as e:
        # Fallback evaluation if LLM fails
        return EvaluationResult(
            passes=False,
            helpfulness_score=1,
            actionability_score=1,
            user_friendliness_score=1,
            accuracy_score=1,
            overall_score=1.0,
            reasoning=f"LLM evaluation failed: {str(e)}",
            suggestions="Could not evaluate due to technical error",
        )


async def assert_error_response_quality(
    response: str,
    scenario: str,
    expected_behavior: str,
    context: Optional[str] = None,
    min_score: float = 3.5,
) -> None:
    """
    Assert that an error response meets quality standards using LLM evaluation.

    Args:
        response: The agent's response to evaluate
        scenario: Description of the error scenario
        expected_behavior: What the response should accomplish
        context: Optional additional context
        min_score: Minimum acceptable overall score (default 3.5)

    Raises:
        AssertionError: If the response doesn't meet quality standards
    """

    # Run the evaluation (now properly async)
    evaluation = await evaluate_error_response(
        response, scenario, expected_behavior, context
    )

    # Create detailed assertion message
    failure_msg = f"""
Response quality evaluation FAILED:

Scenario: {scenario}
Expected: {expected_behavior}

Agent Response: "{response}"

Evaluation Results:
- Overall Score: {evaluation.overall_score}/5.0 (minimum: {min_score})
- Helpfulness: {evaluation.helpfulness_score}/5
- Actionability: {evaluation.actionability_score}/5  
- User-Friendliness: {evaluation.user_friendliness_score}/5
- Accuracy: {evaluation.accuracy_score}/5

Reasoning: {evaluation.reasoning}

{f"Suggestions: {evaluation.suggestions}" if evaluation.suggestions else ""}
"""

    # Assert the response passes quality standards
    assert evaluation.passes and evaluation.overall_score >= min_score, failure_msg


async def evaluate_conversation_quality(
    conversation_history: List[Dict[str, str]], scenario: str, success_criteria: str
) -> EvaluationResult:
    """
    Evaluate the quality of a multi-turn conversation.

    Args:
        conversation_history: List of {"user": "...", "agent": "..."} exchanges
        scenario: Description of the conversation scenario
        success_criteria: What makes this conversation successful

    Returns:
        EvaluationResult for the overall conversation
    """

    conversation_text = "\n".join(
        [
            f"User: {turn['user']}\nAgent: {turn['agent']}\n"
            for turn in conversation_history
        ]
    )

    evaluation_prompt = f"""
CONVERSATION SCENARIO: {scenario}

SUCCESS CRITERIA: {success_criteria}

CONVERSATION TO EVALUATE:
{conversation_text}

Please evaluate this entire conversation flow against the four criteria, considering how well the agent handled the interaction from start to finish.
"""

    try:
        result = await Runner.run(starting_agent=llm_judge, input=evaluation_prompt)

        return result.final_output

    except Exception as e:
        return EvaluationResult(
            passes=False,
            helpfulness_score=1,
            actionability_score=1,
            user_friendliness_score=1,
            accuracy_score=1,
            overall_score=1.0,
            reasoning=f"Conversation evaluation failed: {str(e)}",
        )


# Convenience functions for common test scenarios
async def assert_helpful_error_message(response: str, error_type: str) -> None:
    """Assert that an error message is helpful and user-friendly."""
    await assert_error_response_quality(
        response=response,
        scenario=f"User encountered a {error_type} error",
        expected_behavior="Explain the error clearly and suggest how to fix it",
        context=f"This is a {error_type} error that should be handled gracefully",
    )


async def assert_recovery_suggestions(response: str, error_scenario: str) -> None:
    """Assert that response provides actionable recovery suggestions."""
    await assert_error_response_quality(
        response=response,
        scenario=error_scenario,
        expected_behavior="Provide specific, actionable suggestions for resolving the issue",
        context="User needs guidance on how to proceed after this error",
    )


async def assert_user_friendly_explanation(response: str, technical_issue: str) -> None:
    """Assert that technical issues are explained in user-friendly terms."""
    await assert_error_response_quality(
        response=response,
        scenario=f"Technical issue occurred: {technical_issue}",
        expected_behavior="Explain the technical issue in simple, non-technical language",
        context="Response should be accessible to non-technical users",
    )
