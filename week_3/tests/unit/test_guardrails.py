"""
Unit Tests for Analytics Guardrails

This module tests the input and output guardrails to ensure they properly
allow analytics-related content and block off-topic content.

Key concepts:
- Input guardrail testing: Verifies analytics questions are allowed, others blocked
- Output guardrail testing: Ensures responses stay on analytics topics
- Guardrail behavior validation: Confirms proper tripwire triggering
- Analytics scope enforcement: Tests boundary conditions
"""

import asyncio
import os
import pytest
import sys
import warnings
from pathlib import Path

# Add the week_3/src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Disable OpenAI agents internal tracing for clean test output
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

# Suppress Pydantic deprecation warnings from agents library
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from agents import Runner, InputGuardrailTripwireTriggered
from agents_.csv_agents import (
    input_guardrail_agent,
    output_guardrail_agent,
    communication_agent,
)


class TestAnalyticsInputGuardrail:
    """Test cases for the analytics input guardrail."""

    @pytest.mark.asyncio
    async def test_allows_data_analysis_questions(self):
        """Test that data analysis questions are allowed through the guardrail."""
        allowed_inputs = [
            "What is the average salary in the employee data?",
            "Show me the temperature trends by city",
            "How many rows are in the sales dataset?",
            "Calculate the sum of quantities in sample_sales",
            "What columns are available in weather_data?",
        ]

        for user_input in allowed_inputs:
            # Test the guardrail agent directly
            result = await Runner.run(input_guardrail_agent, input=user_input)

            # Should recognize as analytics-related
            assert (
                result.final_output.is_analytics_related
            ), f"Analytics question not recognized: '{user_input}'"

    @pytest.mark.asyncio
    async def test_blocks_off_topic_questions(self):
        """Test that non-analytics questions are blocked by the guardrail."""
        blocked_inputs = [
            "My mom died, what should I do?",
            "What's the weather like today?",
            "How do I cook pasta?",
            "Tell me about politics",
            "Help me with relationship advice",
        ]

        for user_input in blocked_inputs:
            # Test the guardrail agent directly
            result = await Runner.run(input_guardrail_agent, input=user_input)

            # Should be marked as not analytics-related
            assert (
                not result.final_output.is_analytics_related
            ), f"Off-topic question incorrectly classified: '{user_input}'"
            # Should have reasoning
            assert (
                len(result.final_output.reasoning) > 0
            ), f"No reasoning provided for: '{user_input}'"


class TestAnalyticsOutputGuardrail:
    """Test cases for the analytics output guardrail."""

    @pytest.mark.asyncio
    async def test_allows_analytics_responses(self):
        """Test that analytics-focused responses are allowed."""
        allowed_responses = [
            "The average salary is $75,000 based on the employee data.",
            "Your weather dataset contains 20 rows with temperature data for 5 cities.",
            "The sales data shows Product A had the highest quantity sold.",
        ]

        for response in allowed_responses:
            # Test the output guardrail agent directly
            result = await Runner.run(
                output_guardrail_agent, input=f"Agent response: {response}"
            )

            # Should recognize as on-topic
            assert (
                result.final_output.is_on_topic
            ), f"Analytics response not recognized: '{response}'"

    @pytest.mark.asyncio
    async def test_blocks_off_topic_responses(self):
        """Test that non-analytics responses are blocked and redirected."""
        blocked_responses = [
            "I'm sorry for your loss. Here's advice about grieving...",
            "The weather today is sunny and warm.",
            "Here's a recipe for pasta with tomato sauce.",
        ]

        for response in blocked_responses:
            # Test the output guardrail agent directly
            result = await Runner.run(
                output_guardrail_agent, input=f"Agent response: {response}"
            )

            # Should be marked as off-topic
            assert (
                not result.final_output.is_on_topic
            ), f"Off-topic response incorrectly classified: '{response}'"
            # Should have reasoning
            assert (
                len(result.final_output.reasoning) > 0
            ), f"No reasoning provided for: '{response}'"


class TestEndToEndGuardrailBehavior:
    """Test complete guardrail integration with the communication agent."""

    @pytest.mark.asyncio
    async def test_communication_agent_blocks_off_topic_input(self):
        """Test that the communication agent properly blocks off-topic questions."""
        off_topic_input = "My mom died, what should I do?"

        # This should raise InputGuardrailTripwireTriggered
        with pytest.raises(InputGuardrailTripwireTriggered):
            await Runner.run(starting_agent=communication_agent, input=off_topic_input)

    @pytest.mark.asyncio
    async def test_communication_agent_allows_analytics_input(self):
        """Test that the communication agent processes analytics questions normally."""
        analytics_input = "What datasets are available?"

        # This should work without raising exceptions
        try:
            result = await Runner.run(
                starting_agent=communication_agent, input=analytics_input
            )
            # Should get a response about the datasets
            assert result.final_output is not None
            assert len(result.final_output) > 0
        except InputGuardrailTripwireTriggered:
            pytest.fail("Analytics question was incorrectly blocked by guardrail")


if __name__ == "__main__":
    # Run basic tests manually
    async def run_manual_tests():
        print("🧪 Running manual guardrail tests...\n")

        # Test input guardrail with analytics question
        print("Testing input guardrail...")
        result = await Runner.run(
            input_guardrail_agent, input="What is the average temperature?"
        )
        print(
            f"✅ Analytics question recognized: {result.final_output.is_analytics_related}"
        )
        print(f"   Reasoning: {result.final_output.reasoning}")

        # Test input guardrail with off-topic question
        result = await Runner.run(
            input_guardrail_agent, input="My mom died, what should I do?"
        )
        print(
            f"✅ Off-topic question blocked: {not result.final_output.is_analytics_related}"
        )
        print(f"   Reasoning: {result.final_output.reasoning}")

        # Test end-to-end with communication agent
        print("\nTesting end-to-end guardrail behavior...")
        try:
            await Runner.run(
                communication_agent, input="My mom died, what should I do?"
            )
            print("❌ Off-topic question was not blocked!")
        except InputGuardrailTripwireTriggered:
            print("✅ Off-topic question properly blocked by communication agent")

        print("\n🎉 Manual tests completed!")

    asyncio.run(run_manual_tests())
