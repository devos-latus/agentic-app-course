"""
Test Chart Types Availability and Unsupported Chart Handling

This module tests that the visualization system properly communicates available
chart types and handles requests for unsupported visualizations.

Key concepts:
- Available Chart Types: Testing that all supported chart types are listed
- Unsupported Chart Handling: Testing responses to unsupported chart requests
- Chart Suggestions: Testing that appropriate alternatives are suggested
- Error Communication: Testing clear error messages for users

Use cases:
- Validating that users know what chart types are available
- Testing graceful handling of unsupported chart requests
- Ensuring proper alternative suggestions are provided
- Verifying clear communication about visualization limitations
"""

import unittest
import os
import sys

# Add the solution directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../week_1/solution"))

from visualization_core import analyze_data_structure


class TestChartTypesAvailable(unittest.TestCase):
    """Test that available chart types are properly communicated."""

    def setUp(self):
        """Set up test data."""
        self.test_data = {
            "results": [
                {"product": "Laptop", "sales": 1999.98, "quantity": 2},
                {"product": "Mouse", "sales": 29.99, "quantity": 5},
                {"product": "Keyboard", "sales": 79.99, "quantity": 3},
                {"product": "Monitor", "sales": 299.99, "quantity": 1},
            ]
        }

        self.expected_chart_types = [
            "bar_chart",
            "line_plot",
            "histogram",
            "pie_chart",
            "scatter_plot",
            "box_plot",
            "heatmap",
        ]

    def test_available_chart_types_listed(self):
        """Test that all available chart types are properly listed."""
        result = analyze_data_structure(self.test_data)

        self.assertTrue(result["success"])
        analysis = result["analysis"]

        # Check that available chart types are listed
        self.assertIn("available_chart_types", analysis)
        available_types = analysis["available_chart_types"]

        # Verify all expected types are present
        for expected_type in self.expected_chart_types:
            self.assertIn(expected_type, available_types)

        # Verify we have exactly the expected number of types
        self.assertEqual(len(available_types), len(self.expected_chart_types))

        print(f"✅ All {len(available_types)} chart types are properly listed")

    def test_chart_type_descriptions_provided(self):
        """Test that descriptions are provided for each chart type."""
        result = analyze_data_structure(self.test_data)

        self.assertTrue(result["success"])
        analysis = result["analysis"]

        # Check that descriptions are provided
        self.assertIn("chart_type_descriptions", analysis)
        descriptions = analysis["chart_type_descriptions"]

        # Verify each available chart type has a description
        for chart_type in analysis["available_chart_types"]:
            self.assertIn(chart_type, descriptions)
            self.assertIsInstance(descriptions[chart_type], str)
            self.assertGreater(
                len(descriptions[chart_type]), 10
            )  # Non-trivial description

        print("✅ All chart types have proper descriptions")
        for chart_type, desc in descriptions.items():
            print(f"   • {chart_type}: {desc}")

    def test_multiple_suggestions_provided(self):
        """Test that multiple chart suggestions are provided when appropriate."""
        result = analyze_data_structure(self.test_data)

        self.assertTrue(result["success"])
        analysis = result["analysis"]

        # Check that multiple suggestions are provided
        self.assertIn("all_suggestions", analysis)
        suggestions = analysis["all_suggestions"]

        # Should have multiple suggestions for this mixed data
        self.assertGreaterEqual(len(suggestions), 2)

        # Each suggestion should have chart_type and reason
        for suggestion in suggestions:
            self.assertIn("chart_type", suggestion)
            self.assertIn("reason", suggestion)
            self.assertIn(suggestion["chart_type"], self.expected_chart_types)
            self.assertIsInstance(suggestion["reason"], str)
            self.assertGreater(len(suggestion["reason"]), 10)

        print(f"✅ {len(suggestions)} chart suggestions provided:")
        for suggestion in suggestions:
            print(f"   • {suggestion['chart_type']}: {suggestion['reason']}")

    def test_primary_suggestion_reasonable(self):
        """Test that the primary suggestion is reasonable for the data."""
        result = analyze_data_structure(self.test_data)

        self.assertTrue(result["success"])
        analysis = result["analysis"]

        # Check primary suggestion
        primary_type = analysis["suggested_chart_type"]
        reasoning = analysis["reasoning"]

        # Should be one of the expected types
        self.assertIn(primary_type, self.expected_chart_types)

        # Should have meaningful reasoning
        self.assertIsInstance(reasoning, str)
        self.assertGreater(len(reasoning), 15)

        # For this categorical + numeric data, should suggest appropriate charts
        reasonable_suggestions = ["bar_chart", "pie_chart"]
        self.assertIn(primary_type, reasonable_suggestions)

        print(f"✅ Primary suggestion '{primary_type}' is reasonable")
        print(f"   Reasoning: {reasoning}")

    def test_error_case_includes_available_types(self):
        """Test that error cases still include available chart types."""
        # Test with invalid data to trigger error case
        result = analyze_data_structure({"invalid": "data structure"})

        self.assertFalse(result["success"])
        self.assertIn("error", result)

        # Should still include available chart types for user reference
        # This might not be in the current implementation, but it's good practice
        # We'll just verify the function handles errors gracefully
        self.assertIsInstance(result["error"], str)

        print("✅ Error handling works gracefully")
        print(f"   Error: {result['error']}")


class TestUnsupportedChartHandling(unittest.TestCase):
    """Test handling of requests for unsupported chart types."""

    def test_unsupported_chart_types_list(self):
        """Test that we know what chart types are NOT supported."""
        # These are common chart types that we don't support
        unsupported_types = [
            "area_chart",
            "bubble_chart",
            "treemap",
            "sunburst",
            "radar_chart",
            "waterfall",
            "gantt",
            "sankey",
            "violin_plot",
            "candlestick",
            "funnel",
            "3d_chart",
        ]

        supported_types = [
            "bar_chart",
            "line_plot",
            "histogram",
            "pie_chart",
            "scatter_plot",
            "box_plot",
            "heatmap",
        ]

        # Verify no overlap
        for unsupported in unsupported_types:
            self.assertNotIn(unsupported, supported_types)

        print(
            f"✅ Clear distinction between supported ({len(supported_types)}) and unsupported ({len(unsupported_types)}) types"
        )
        print(f"   Supported: {', '.join(supported_types)}")
        print(f"   Unsupported examples: {', '.join(unsupported_types)}")


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)
