"""
Basic Phoenix Trace Monitor

Monitors and analyzes Phoenix tracing logs to extract insights about
agent performance, conversation patterns, and system health.

Key concepts:
- Real-time trace analysis
- Performance monitoring
- Conversation pattern detection
- System health metrics

Use cases:
- Monitor agent performance in production
- Detect conversation patterns and trends
- Track system health and errors
- Generate performance reports
"""

from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


class PhoenixTraceMonitor:
    """
    Monitor for analyzing Phoenix traces and extracting insights.

    This processes trace data to provide:
    - Performance metrics (latency, success rates)
    - Conversation pattern analysis
    - Agent utilization statistics
    - Error detection and categorization
    """

    def __init__(self):
        """Initialize the monitor."""
        self.conversation_patterns = {
            "visualization": [
                "chart",
                "plot",
                "graph",
                "visualize",
                "histogram",
                "scatter",
                "bar",
            ],
            "analysis": [
                "average",
                "mean",
                "median",
                "calculate",
                "statistics",
                "analyze",
            ],
            "data_exploration": [
                "show",
                "display",
                "list",
                "describe",
                "columns",
                "schema",
            ],
            "error_handling": ["error", "failed", "cannot", "unable", "invalid"],
            "data_management": ["load", "upload", "file", "csv", "import"],
        }

    def analyze_trace_data(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze Phoenix trace data to extract key insights.

        Args:
            traces: List of trace spans from Phoenix

        Returns:
            Comprehensive analysis report
        """
        if not traces:
            return {"error": "No trace data provided"}

        # Extract metrics from traces
        performance_metrics = self._analyze_performance(traces)
        conversation_analysis = self._analyze_conversations(traces)
        agent_metrics = self._analyze_agent_usage(traces)
        error_analysis = self._analyze_errors(traces)

        return {
            "summary": {
                "total_traces": len(traces),
                "analysis_timestamp": datetime.now().isoformat(),
                "time_range": self._get_time_range(traces),
            },
            "performance": performance_metrics,
            "conversations": conversation_analysis,
            "agents": agent_metrics,
            "errors": error_analysis,
            "insights": self._generate_insights(
                performance_metrics,
                conversation_analysis,
                agent_metrics,
                error_analysis,
            ),
        }

    def _analyze_performance(self, traces: List[Dict]) -> Dict[str, Any]:
        """Analyze performance metrics from traces."""
        latencies = []
        costs = []
        success_count = 0

        for trace in traces:
            # Extract latency (from Phoenix trace duration)
            if "latency" in trace:
                latencies.append(float(trace["latency"]))
            elif "duration_ms" in trace:
                latencies.append(float(trace["duration_ms"]))

            # Extract cost information
            if "cost" in trace:
                costs.append(float(trace["cost"]))

            # Count successes
            if trace.get("status") == "OK" or trace.get("success", False):
                success_count += 1

        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        total_cost = sum(costs) if costs else 0
        success_rate = success_count / len(traces) if traces else 0

        return {
            "avg_latency_ms": round(avg_latency, 2),
            "max_latency_ms": max(latencies) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
            "total_cost": round(total_cost, 4),
            "success_rate": round(success_rate, 2),
            "total_conversations": len(traces),
        }

    def _analyze_conversations(self, traces: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation patterns from traces."""
        pattern_counts = defaultdict(int)
        response_lengths = []

        for trace in traces:
            # Classify conversation type
            user_input = trace.get("user_input", "") or trace.get("input", "")
            response = trace.get("response", "") or trace.get("output", "")

            pattern = self._classify_conversation_type(user_input, response)
            pattern_counts[pattern] += 1

            if response:
                response_lengths.append(len(response))

        avg_response_length = (
            sum(response_lengths) / len(response_lengths) if response_lengths else 0
        )

        return {
            "pattern_distribution": dict(pattern_counts),
            "most_common_pattern": max(pattern_counts.keys(), key=pattern_counts.get)
            if pattern_counts
            else "unknown",
            "avg_response_length": round(avg_response_length, 1),
            "total_patterns": len(pattern_counts),
        }

    def _analyze_agent_usage(self, traces: List[Dict]) -> Dict[str, Any]:
        """Analyze agent utilization from traces."""
        agent_counts = defaultdict(int)
        agent_latencies = defaultdict(list)

        for trace in traces:
            agent_name = trace.get("agent_name", "unknown")
            agent_counts[agent_name] += 1

            if "latency" in trace:
                agent_latencies[agent_name].append(float(trace["latency"]))

        # Calculate average latency per agent
        agent_avg_latencies = {}
        for agent, latencies in agent_latencies.items():
            agent_avg_latencies[agent] = (
                sum(latencies) / len(latencies) if latencies else 0
            )

        return {
            "agent_usage_counts": dict(agent_counts),
            "most_used_agent": max(agent_counts.keys(), key=agent_counts.get)
            if agent_counts
            else "unknown",
            "agent_avg_latencies": {
                k: round(v, 2) for k, v in agent_avg_latencies.items()
            },
            "total_agents": len(agent_counts),
        }

    def _analyze_errors(self, traces: List[Dict]) -> Dict[str, Any]:
        """Analyze error patterns from traces."""
        error_count = 0
        error_types = defaultdict(int)

        for trace in traces:
            if trace.get("status") == "ERROR" or not trace.get("success", True):
                error_count += 1
                error_type = trace.get("error_type", "unknown_error")
                error_types[error_type] += 1

        error_rate = error_count / len(traces) if traces else 0

        return {
            "total_errors": error_count,
            "error_rate": round(error_rate, 3),
            "error_types": dict(error_types),
            "most_common_error": max(error_types.keys(), key=error_types.get)
            if error_types
            else None,
        }

    def _classify_conversation_type(self, user_input: str, response: str) -> str:
        """Classify conversation type based on input and response."""
        combined_text = (user_input + " " + response).lower()

        for pattern_type, keywords in self.conversation_patterns.items():
            if any(keyword in combined_text for keyword in keywords):
                return pattern_type

        return "general_conversation"

    def _get_time_range(self, traces: List[Dict]) -> Dict[str, str]:
        """Get time range of traces."""
        timestamps = []
        for trace in traces:
            if "timestamp" in trace:
                timestamps.append(trace["timestamp"])

        if timestamps:
            return {
                "start": min(timestamps),
                "end": max(timestamps),
                "duration_minutes": "calculated_from_timestamps",
            }

        return {"start": "unknown", "end": "unknown", "duration_minutes": 0}

    def _generate_insights(
        self, performance: Dict, conversations: Dict, agents: Dict, errors: Dict
    ) -> List[str]:
        """Generate actionable insights from the analysis."""
        insights = []

        # Performance insights
        if performance["avg_latency_ms"] > 5000:  # > 5 seconds
            insights.append(
                f"⚠️ High average latency detected: {performance['avg_latency_ms']}ms"
            )

        if performance["success_rate"] < 0.9:  # < 90%
            insights.append(
                f"⚠️ Low success rate: {performance['success_rate']*100:.1f}%"
            )

        # Conversation insights
        most_common = conversations.get("most_common_pattern", "unknown")
        if most_common != "unknown":
            insights.append(f"📊 Most common interaction: {most_common}")

        # Agent insights
        most_used_agent = agents.get("most_used_agent", "unknown")
        if most_used_agent != "unknown":
            insights.append(f"🤖 Most utilized agent: {most_used_agent}")

        # Error insights
        if errors["error_rate"] > 0.1:  # > 10%
            insights.append(f"🚨 High error rate: {errors['error_rate']*100:.1f}%")

        if not insights:
            insights.append("✅ System performing within normal parameters")

        return insights


def create_sample_trace_data() -> List[Dict[str, Any]]:
    """
    Create comprehensive trace data including recent logs from 8/25/2025, 05:21 PM onwards.

    This simulates the trace data structure that would come from Phoenix API,
    including both historical and recent conversation traces.
    """
    return [
        # Original traces from Phoenix dashboard
        {
            "trace_id": "conversation_feb95f3b_1",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 6130,  # 6.13s in ms
            "cost": 0.008,
            "user_input": "What's the average salary in the employee data?",
            "response": "The average salary is $75,420 based on 150 employees in the dataset.",
            "agent_name": "AnalyticsAgent",
            "success": True,
            "timestamp": "2025-08-25T17:21:00Z",
            "child_spans": [
                {"name": "ChatCompletion", "duration_ms": 534},
                {"name": "ChatCompletion", "duration_ms": 700},
                {"name": "ChatCompletion", "duration_ms": 1152},
                {"name": "ChatCompletion", "duration_ms": 501},
            ],
        },
        {
            "trace_id": "conversation_feb95f3b_2",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 3200,
            "cost": 0.005,
            "user_input": "Show me a chart of sales by month",
            "response": "I've created a bar chart showing monthly sales trends. The chart shows steady growth from January to December.",
            "agent_name": "VisualizationAgent",
            "success": True,
            "timestamp": "2025-08-25T17:22:30Z",
        },
        # Recent traces from 8/25/2025, 05:21 PM onwards
        {
            "trace_id": "conversation_abc123_3",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 4500,
            "cost": 0.007,
            "user_input": "Load the employee data and show me the first 5 rows",
            "response": "I've loaded the employee data successfully. Here are the first 5 rows showing employee ID, name, department, salary, and hire date.",
            "agent_name": "DataLoaderAgent",
            "success": True,
            "timestamp": "2025-08-25T17:23:15Z",
        },
        {
            "trace_id": "conversation_def456_4",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 2800,
            "cost": 0.004,
            "user_input": "What columns are available in the dataset?",
            "response": "The dataset contains the following columns: employee_id, name, department, salary, hire_date, manager_id, and performance_rating.",
            "agent_name": "CommunicationAgent",
            "success": True,
            "timestamp": "2025-08-25T17:24:45Z",
        },
        {
            "trace_id": "conversation_ghi789_5",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 5200,
            "cost": 0.009,
            "user_input": "Calculate the average salary by department",
            "response": "Here are the average salaries by department: Engineering: $85,200, Sales: $68,500, Marketing: $72,300, HR: $65,800, Finance: $78,900.",
            "agent_name": "AnalyticsAgent",
            "success": True,
            "timestamp": "2025-08-25T17:26:10Z",
        },
        {
            "trace_id": "conversation_jkl012_6",
            "span_name": "conversation_flow",
            "status": "ERROR",
            "latency": 1500,
            "cost": 0.002,
            "user_input": "Show me data for employee ID 99999",
            "response": "Error: Employee ID 99999 not found in the dataset. Please check the ID and try again.",
            "agent_name": "QueryEvaluatorAgent",
            "success": False,
            "timestamp": "2025-08-25T17:27:30Z",
            "error_type": "data_not_found",
        },
        {
            "trace_id": "conversation_mno345_7",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 3800,
            "cost": 0.006,
            "user_input": "Create a histogram of salary distribution",
            "response": "I've created a histogram showing salary distribution across all employees. The chart shows most employees earn between $60K-$80K with a normal distribution.",
            "agent_name": "VisualizationAgent",
            "success": True,
            "timestamp": "2025-08-25T17:28:45Z",
        },
        {
            "trace_id": "conversation_pqr678_8",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 4200,
            "cost": 0.007,
            "user_input": "Which department has the highest performance ratings?",
            "response": "Engineering department has the highest average performance rating at 4.2/5.0, followed by Finance at 3.9/5.0 and Marketing at 3.7/5.0.",
            "agent_name": "AnalyticsAgent",
            "success": True,
            "timestamp": "2025-08-25T17:30:20Z",
        },
        {
            "trace_id": "conversation_stu901_9",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 2200,
            "cost": 0.003,
            "user_input": "analytics",
            "response": "Session Analytics: Session ID: session_123, Messages processed: 8, Data loaded: ✅, Enhanced tracing: ✅, Phoenix project: analytics_system",
            "agent_name": "EnhancedChatService",
            "success": True,
            "timestamp": "2025-08-25T17:31:15Z",
        },
        {
            "trace_id": "conversation_vwx234_10",
            "span_name": "conversation_flow",
            "status": "OK",
            "latency": 6800,
            "cost": 0.011,
            "user_input": "Generate a comprehensive report on employee performance trends over the last year",
            "response": "I've analyzed the performance data and generated a comprehensive report. Key findings: 15% improvement in overall ratings, Engineering leads in performance, 23% of employees received promotions based on high ratings.",
            "agent_name": "AnalyticsAgent",
            "success": True,
            "timestamp": "2025-08-25T17:32:45Z",
        },
    ]


def example_monitoring():
    """
    Example of monitoring Phoenix traces.

    In production, this would connect to Phoenix API to fetch real trace data.
    """
    monitor = PhoenixTraceMonitor()

    # Use sample data (in production, fetch from Phoenix API)
    sample_traces = create_sample_trace_data()

    # Analyze the traces
    analysis = monitor.analyze_trace_data(sample_traces)

    print("🔍 Phoenix Trace Analysis Report")
    print("=" * 50)

    # Print summary
    print("\n📊 SUMMARY:")
    for key, value in analysis["summary"].items():
        print(f"  {key}: {value}")

    # Print performance metrics
    print("\n⚡ PERFORMANCE:")
    for key, value in analysis["performance"].items():
        print(f"  {key}: {value}")

    # Print conversation analysis
    print("\n💬 CONVERSATIONS:")
    for key, value in analysis["conversations"].items():
        print(f"  {key}: {value}")

    # Print agent metrics
    print("\n🤖 AGENTS:")
    for key, value in analysis["agents"].items():
        print(f"  {key}: {value}")

    # Print error analysis
    print("\n🚨 ERRORS:")
    for key, value in analysis["errors"].items():
        print(f"  {key}: {value}")

    # Print insights
    print("\n💡 INSIGHTS:")
    for insight in analysis["insights"]:
        print(f"  • {insight}")


if __name__ == "__main__":
    example_monitoring()
