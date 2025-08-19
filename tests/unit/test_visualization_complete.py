"""
Complete Visualization System Tests

This module contains comprehensive tests for the entire visualization system,
including core functions, function tools, and agent integration.

Key concepts:
- Core Function Testing: Testing the underlying visualization logic
- Function Tool Testing: Testing agent-compatible tool interfaces
- Agent Integration Testing: Testing visualization agent functionality
- End-to-End Testing: Testing complete workflows from data to charts
- Error Handling Testing: Testing graceful error handling throughout

Use cases:
- Validating complete visualization system functionality
- Testing both core functions and agent tools
- Ensuring chart generation works in all scenarios
- Verifying proper error handling and edge cases
"""

import unittest
import os
import pandas as pd
import json
import sys

# Add the solution directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../week_1/solution"))

from visualization_tools import (
    # Core functions
    analyze_data_structure,
    create_bar_chart_core,
    create_line_plot_core,
    create_histogram_core,
    prepare_data_for_plotting,
    ensure_charts_directory,
    generate_chart_filename,
    # Function tools (these are FunctionTool objects)
    analyze_data_for_visualization,
    create_bar_chart,
    create_line_plot,
    create_histogram,
)


class TestCoreFunctions(unittest.TestCase):
    """Test the core visualization functions (without function_tool decorators)."""

    def setUp(self):
        """Set up test data."""
        self.test_data = {
            "results": [
                {"department": "Engineering", "count": 15},
                {"department": "Sales", "count": 12},
                {"department": "Marketing", "count": 8},
                {"department": "HR", "count": 5},
            ]
        }

        self.numeric_data = {
            "results": [
                {"salary": 50000},
                {"salary": 55000},
                {"salary": 60000},
                {"salary": 65000},
                {"salary": 70000},
            ]
        }

    def test_data_preparation(self):
        """Test data preparation for plotting."""
        df = prepare_data_for_plotting(self.test_data)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 4)
        self.assertListEqual(list(df.columns), ["department", "count"])
        self.assertEqual(df.iloc[0]["department"], "Engineering")
        self.assertEqual(df.iloc[0]["count"], 15)

    def test_data_analysis(self):
        """Test data structure analysis."""
        result = analyze_data_structure(self.test_data)

        self.assertTrue(result["success"])
        analysis = result["analysis"]
        self.assertEqual(analysis["row_count"], 4)
        self.assertEqual(analysis["column_count"], 2)
        # Our improved logic now suggests pie_chart for small categorical datasets
        self.assertEqual(analysis["suggested_chart_type"], "pie_chart")
        self.assertIn("categorical", analysis["reasoning"])

    def test_bar_chart_creation(self):
        """Test bar chart creation."""
        result = create_bar_chart_core(self.test_data, "Test Bar Chart")

        self.assertTrue(result["success"])
        self.assertEqual(result["chart_type"], "bar_chart")
        self.assertEqual(result["title"], "Test Bar Chart")
        self.assertEqual(result["data_points"], 4)
        self.assertIn("image_path", result)

        # Verify file was created
        self.assertTrue(os.path.exists(result["image_path"]))

    def test_line_plot_creation(self):
        """Test line plot creation."""
        time_data = {
            "results": [
                {"month": "Jan", "sales": 1000},
                {"month": "Feb", "sales": 1200},
                {"month": "Mar", "sales": 1500},
            ]
        }

        result = create_line_plot_core(time_data, "Sales Trend")

        self.assertTrue(result["success"])
        self.assertEqual(result["chart_type"], "line_plot")
        self.assertEqual(result["title"], "Sales Trend")
        self.assertEqual(result["data_points"], 3)

        # Verify file was created
        self.assertTrue(os.path.exists(result["image_path"]))

    def test_histogram_creation(self):
        """Test histogram creation."""
        result = create_histogram_core(
            self.numeric_data, "salary", "Salary Distribution"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["chart_type"], "histogram")
        self.assertEqual(result["title"], "Salary Distribution")
        self.assertIn("statistics", result)
        self.assertIn("mean", result["statistics"])

        # Verify file was created
        self.assertTrue(os.path.exists(result["image_path"]))

    def test_utility_functions(self):
        """Test utility functions."""
        # Test filename generation
        filepath = generate_chart_filename("test_chart")
        filename = os.path.basename(filepath)
        self.assertTrue(filename.startswith("test_chart_"))
        self.assertTrue(filename.endswith(".png"))

        # Test directory creation
        ensure_charts_directory()
        self.assertTrue(os.path.exists("/tmp/charts"))


class TestFunctionTools(unittest.TestCase):
    """Test the function tools that agents use."""

    def setUp(self):
        """Set up test data."""
        self.test_data = {
            "results": [
                {"department": "Engineering", "count": 15},
                {"department": "Sales", "count": 12},
                {"department": "Marketing", "count": 8},
            ]
        }
        self.test_data_json = json.dumps(self.test_data)

    def test_function_tool_properties(self):
        """Test that function tools have correct properties."""
        # These are FunctionTool objects, not callable functions
        self.assertTrue(hasattr(analyze_data_for_visualization, "name"))
        self.assertTrue(hasattr(create_bar_chart, "name"))
        self.assertTrue(hasattr(create_line_plot, "name"))
        self.assertTrue(hasattr(create_histogram, "name"))

        # Check tool names
        self.assertEqual(
            analyze_data_for_visualization.name, "analyze_data_for_visualization"
        )
        self.assertEqual(create_bar_chart.name, "create_bar_chart")
        self.assertEqual(create_line_plot.name, "create_line_plot")
        self.assertEqual(create_histogram.name, "create_histogram")

    def test_function_tool_schemas(self):
        """Test that function tools are properly configured."""
        # The important thing is that they are FunctionTool objects that agents can use
        tools = [
            analyze_data_for_visualization,
            create_bar_chart,
            create_line_plot,
            create_histogram,
        ]

        for tool in tools:
            # Each should be a FunctionTool object with a name
            self.assertTrue(hasattr(tool, "name"))
            self.assertIsInstance(tool.name, str)
            # The exact internal structure may vary, but having a name means it's properly configured


class TestAgentIntegration(unittest.TestCase):
    """Test agent integration with visualization tools."""

    def test_agent_import(self):
        """Test that agents can import visualization tools."""
        try:
            from csv_agents import visualization_agent

            # Agent should exist
            self.assertIsNotNone(visualization_agent)
            self.assertEqual(visualization_agent.name, "VisualizationAgent")

            # Agent should have visualization tools
            self.assertGreater(len(visualization_agent.tools), 0)

            # Check tool names
            tool_names = [tool.name for tool in visualization_agent.tools]
            self.assertIn("analyze_data_for_visualization", tool_names)
            self.assertIn("create_bar_chart", tool_names)
            self.assertIn("create_line_plot", tool_names)
            self.assertIn("create_histogram", tool_names)

        except ImportError as e:
            self.fail(f"Failed to import visualization agent: {e}")

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

        except ImportError as e:
            self.fail(f"Failed to import agents for handoff testing: {e}")


class TestErrorHandling(unittest.TestCase):
    """Test error handling throughout the visualization system."""

    def test_invalid_data_handling(self):
        """Test handling of invalid data."""
        # Empty data
        result = analyze_data_structure({"results": []})
        self.assertFalse(result["success"])
        self.assertIn("error", result)

        # Invalid data structure
        result = create_bar_chart_core({"invalid": "data"}, "Test Chart")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_insufficient_data_handling(self):
        """Test handling of insufficient data for charts."""
        # Empty data for bar chart
        empty_data = {"results": []}
        result = create_bar_chart_core(empty_data, "Test Chart")
        self.assertFalse(result["success"])
        self.assertIn("No data available", result["error"])

        # Non-numeric data for histogram
        text_data = {"results": [{"text": "hello"}, {"text": "world"}]}
        result = create_histogram_core(text_data, "text", "Test Histogram")
        self.assertFalse(result["success"])
        self.assertIn("not numeric", result["error"])

    def test_missing_column_handling(self):
        """Test handling of missing columns."""
        test_data = {"results": [{"col1": 1, "col2": 2}]}
        result = create_histogram_core(test_data, "nonexistent_col", "Test")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_single_data_point(self):
        """Test handling of single data point."""
        single_point = {"results": [{"category": "A", "value": 100}]}

        # Should still work for bar chart
        result = create_bar_chart_core(single_point, "Single Point Chart")
        self.assertTrue(result["success"])
        self.assertEqual(result["data_points"], 1)

    def test_large_dataset(self):
        """Test handling of larger datasets."""
        # Create data with many categories
        large_data = {
            "results": [
                {"category": f"Cat_{i}", "value": i * 10}
                for i in range(25)  # More than 20 categories
            ]
        }

        result = create_bar_chart_core(large_data, "Large Dataset Chart")
        self.assertTrue(result["success"])
        self.assertEqual(result["data_points"], 25)

    def test_mixed_data_types(self):
        """Test handling of mixed data types."""
        mixed_data = {
            "results": [
                {"name": "John", "age": 25, "salary": 50000},
                {"name": "Jane", "age": 30, "salary": 60000},
            ]
        }

        # Analysis should work
        result = analyze_data_structure(mixed_data)
        self.assertTrue(result["success"])

        # Should identify mixed types
        analysis = result["analysis"]
        self.assertGreater(len(analysis["categorical_columns"]), 0)
        self.assertGreater(len(analysis["numeric_columns"]), 0)


class TestCleanup(unittest.TestCase):
    """Test cleanup and file management."""

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
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestCoreFunctions,
        TestFunctionTools,
        TestAgentIntegration,
        TestErrorHandling,
        TestEdgeCases,
        TestCleanup,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*60}")
    print("COMPLETE VISUALIZATION SYSTEM TESTS SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.testsRun > 0:
        success_rate = (
            (result.testsRun - len(result.failures) - len(result.errors))
            / result.testsRun
            * 100
        )
        print(f"Success rate: {success_rate:.1f}%")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.splitlines()[-1] if traceback else 'No details'}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
            print(f"  {traceback.splitlines()[-1] if traceback else 'No details'}")

    # Overall assessment
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("\n🎉 All visualization system tests passed!")
        print("✅ Core functions working")
        print("✅ Function tools properly configured")
        print("✅ Agent integration successful")
        print("✅ Error handling robust")
        print("✅ Edge cases handled")
        print("\n🚀 Visualization system is ready for production use!")
    else:
        print("\n⚠️  Some tests failed. Review issues before proceeding.")

    print("\n💡 Next steps:")
    print("   1. Run integration tests with real agents")
    print("   2. Test Gradio interface with visualization features")
    print("   3. Create demo workflows for end users")
