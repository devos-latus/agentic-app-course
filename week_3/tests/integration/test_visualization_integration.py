"""
Visualization Agent Integration Tests

Simple integration tests that focus on testing the visualization system
with actual agents and real workflows.

Key concepts:
- Agent Integration: Testing that visualization agent works with other agents
- Tool Integration: Testing that visualization tools work within agents
- Memory Integration: Testing conversation memory across visualization workflows
- Error Handling: Testing graceful error handling in agent workflows

Use cases:
- Validating that agents can import and use visualization tools
- Testing basic agent handoff workflows
- Ensuring visualization system integrates with existing CSV analytics
- Testing error handling in multi-agent scenarios
"""

import unittest
import asyncio
import os
import sys

# Add the solution directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../week_1/solution"))

from agents import Runner, SQLiteSession, set_tracing_disabled
from visualization_tools import create_bar_chart_core, analyze_data_structure

# Disable tracing for clean test output
set_tracing_disabled(True)


class TestVisualizationAgentIntegration(unittest.TestCase):
    """Test basic integration of visualization agents."""

    def test_agent_imports(self):
        """Test that all agents can be imported successfully."""
        try:
            from csv_agents import (
                communication_agent,
                analytics_agent,
                visualization_agent,
                agents,
            )

            # All agents should exist
            self.assertIsNotNone(communication_agent)
            self.assertIsNotNone(analytics_agent)
            self.assertIsNotNone(visualization_agent)
            self.assertIsNotNone(agents)

            # Visualization agent should have tools
            self.assertGreater(len(visualization_agent.tools), 0)

            # Check expected tools are present
            tool_names = [tool.name for tool in visualization_agent.tools]
            expected_tools = [
                "analyze_data_for_visualization",
                "create_bar_chart",
                "create_line_plot",
                "create_histogram",
            ]

            for tool_name in expected_tools:
                self.assertIn(tool_name, tool_names, f"Missing tool: {tool_name}")

            print("✅ All agents imported successfully")
            print(f"✅ Visualization agent has {len(visualization_agent.tools)} tools")

        except ImportError as e:
            self.fail(f"Failed to import agents: {e}")

    def test_agent_handoffs(self):
        """Test that agent handoffs are properly configured."""
        try:
            from csv_agents import (
                analytics_agent,
                visualization_agent,
            )

            # Analytics agent should be able to handoff to visualization agent
            analytics_handoffs = [agent.name for agent in analytics_agent.handoffs]
            self.assertIn("VisualizationAgent", analytics_handoffs)

            # Visualization agent should be able to handoff back
            viz_handoffs = [agent.name for agent in visualization_agent.handoffs]
            self.assertIn("CommunicationAgent", viz_handoffs)

            print("✅ Agent handoffs properly configured")
            print(f"   Analytics can handoff to: {analytics_handoffs}")
            print(f"   Visualization can handoff to: {viz_handoffs}")

        except ImportError as e:
            self.fail(f"Failed to import agents for handoff testing: {e}")

    def test_visualization_tools_work(self):
        """Test that visualization tools work correctly."""
        # Test core visualization functions
        test_data = {
            "results": [
                {"department": "Engineering", "count": 15},
                {"department": "Sales", "count": 12},
                {"department": "Marketing", "count": 8},
            ]
        }

        # Test data analysis
        analysis_result = analyze_data_structure(test_data)
        self.assertTrue(analysis_result["success"])
        # Our improved logic now suggests pie_chart for small categorical datasets
        self.assertEqual(
            analysis_result["analysis"]["suggested_chart_type"], "pie_chart"
        )

        # Test chart creation
        chart_result = create_bar_chart_core(test_data, "Test Integration Chart")
        self.assertTrue(chart_result["success"])
        self.assertEqual(chart_result["chart_type"], "bar_chart")
        self.assertIn("image_path", chart_result)

        # Verify file was created
        self.assertTrue(os.path.exists(chart_result["image_path"]))

        print("✅ Visualization tools working correctly")
        print(
            f"   Data analysis: {analysis_result['analysis']['suggested_chart_type']}"
        )
        print(f"   Chart created: {chart_result['image_path']}")

    def test_simple_agent_workflow(self):
        """Test a simple workflow with visualization agent."""

        async def run_test():
            try:
                from csv_agents import visualization_agent

                # Create a session
                session = SQLiteSession(session_id=12345)

                # Simple request to visualization agent
                test_request = "I have data about departments with counts. Can you help me visualize it?"

                result = await Runner.run(
                    starting_agent=visualization_agent,
                    input=test_request,
                    session=session,
                )

                # Should get some response
                self.assertIsNotNone(result.final_output)
                self.assertIsInstance(result.final_output, str)
                self.assertGreater(
                    len(result.final_output), 10
                )  # Should be a substantial response

                print("✅ Simple agent workflow completed")
                print(f"   Response length: {len(result.final_output)} characters")

                return True

            except Exception as e:
                print(f"❌ Agent workflow failed: {e}")
                return False

        # Run the async test
        success = asyncio.run(run_test())
        self.assertTrue(success, "Agent workflow should complete successfully")


class TestVisualizationSystemIntegration(unittest.TestCase):
    """Test integration of the complete visualization system."""

    def test_system_components(self):
        """Test that all system components are properly integrated."""

        # Test 1: Core functions exist and work
        self.assertTrue(callable(create_bar_chart_core))
        self.assertTrue(callable(analyze_data_structure))

        # Test 2: Agents can be imported
        try:
            from csv_agents import visualization_agent

            self.assertIsNotNone(visualization_agent)
        except ImportError:
            self.fail("Cannot import visualization agent")

        # Test 3: Tools are properly configured
        tool_names = [tool.name for tool in visualization_agent.tools]
        self.assertGreater(len(tool_names), 0)

        # Test 4: Chart directory can be created
        charts_dir = "/tmp/charts"
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir)
        self.assertTrue(os.path.exists(charts_dir))

        print("✅ All system components properly integrated")
        print("   Core functions: Available")
        print(f"   Visualization agent: Available with {len(tool_names)} tools")
        print(f"   Chart directory: {charts_dir}")

    def tearDown(self):
        """Clean up test files."""
        charts_dir = "/tmp/charts"
        if os.path.exists(charts_dir):
            for file in os.listdir(charts_dir):
                if any(
                    file.startswith(prefix)
                    for prefix in ["bar_chart_", "line_plot_", "histogram_"]
                ):
                    try:
                        os.remove(os.path.join(charts_dir, file))
                    except OSError:
                        pass  # Ignore cleanup errors


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)

    print(f"\n{'='*60}")
    print("VISUALIZATION AGENT INTEGRATION TESTS COMPLETE")
    print(f"{'='*60}")
    print("\n💡 What was tested:")
    print("   ✓ Agent imports and configuration")
    print("   ✓ Agent handoff relationships")
    print("   ✓ Visualization tools functionality")
    print("   ✓ Basic agent workflow execution")
    print("   ✓ System component integration")
    print("\n🚀 Integration tests validate that the visualization system")
    print("   works properly with the multi-agent architecture!")
