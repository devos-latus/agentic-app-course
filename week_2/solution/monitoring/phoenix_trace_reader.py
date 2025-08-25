"""
Phoenix Trace Reader - Real Data from Arize Phoenix

Connects to Arize Phoenix to pull actual trace data for analysis.
Based on the Arize export client pattern for trajectory evaluation.

Key concepts:
- Real Phoenix API integration
- Trace data extraction and filtering
- Tool call sequence analysis
- Conversation flow reconstruction

Use cases:
- Pull real trace data from Phoenix dashboard
- Analyze actual agent conversations
- Extract tool usage patterns
- Generate performance reports from real data
"""

import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from arize.exporter import ArizeExportClient
    from arize.utils.types import Environments
    ARIZE_AVAILABLE = True
except ImportError:
    print("⚠️  Arize client not installed. Install with: pip install arize")
    ARIZE_AVAILABLE = False


class PhoenixTraceReader:
    """
    Reader for extracting real trace data from Arize Phoenix.
    
    This connects to the actual Phoenix API to pull conversation traces,
    tool calls, and performance metrics for analysis.
    """
    
    def __init__(self):
        """Initialize the Phoenix trace reader."""
        self.client = None
        self.space_id = os.getenv("PHOENIX_SPACE_ID")
        self.model_id = os.getenv("PHOENIX_MODEL_ID") or "analytics_system"
        
        if ARIZE_AVAILABLE:
            try:
                # Try to initialize with explicit API key from environment
                phoenix_api_key = os.getenv("PHOENIX_API_KEY")
                if phoenix_api_key:
                    self.client = ArizeExportClient(api_key=phoenix_api_key)
                    print(f"✅ Phoenix client initialized with API key for model: {self.model_id}")
                else:
                    self.client = ArizeExportClient()
                    print(f"✅ Phoenix client initialized for model: {self.model_id}")
            except Exception as e:
                print(f"⚠️  Phoenix client initialization failed: {str(e)}")
        else:
            print("⚠️  Arize client not available")
    
    def pull_all_spans_from_analytics_system(self, hours_back: int = 24) -> pd.DataFrame:
        """
        Pull ALL spans from the analytics_system project in Phoenix.
        
        Args:
            hours_back: How many hours back to pull spans from
            
        Returns:
            DataFrame with all span data from analytics_system
        """
        if not self.client:
            print("⚠️  No Phoenix client available")
            return self._create_empty_dataframe()
        
        try:
            # Set time range for last N hours
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours_back)
            
            print(f"🔍 Pulling ALL spans from analytics_system project")
            print(f"   From: {start_time}")
            print(f"   To: {end_time}")
            print(f"   Project: analytics_system")
            
            # Pull ALL trace data from Phoenix analytics_system project
            df = self.client.export_model_to_df(
                space_id=self.space_id,
                model_id="analytics_system",  # Explicitly use analytics_system
                environment=Environments.TRACING,
                start_time=start_time,
                end_time=end_time
            )
            
            print(f"✅ Retrieved {len(df)} total spans from analytics_system")
            
            # Show span types for debugging
            if not df.empty and 'name' in df.columns:
                span_types = df['name'].value_counts()
                print(f"📊 Span types found:")
                for span_name, count in span_types.head(10).items():
                    print(f"   {span_name}: {count}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error pulling spans from Phoenix: {str(e)}")
            return self._create_empty_dataframe()
    
    def filter_conversation_spans(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter spans relevant for conversation analysis.
        
        Args:
            df: Raw trace DataFrame from Phoenix
            
        Returns:
            Filtered DataFrame with conversation spans
        """
        try:
            # Filter for conversation flow spans (our custom spans)
            conversation_spans = df[
                (df['name'].str.contains('conversation', case=False, na=False)) |
                (df['attributes.conversation.type'] == 'user_interaction')
            ].copy()
            
            print(f"🔍 Found {len(conversation_spans)} conversation spans")
            return conversation_spans
            
        except Exception as e:
            print(f"⚠️  Error filtering conversation spans: {str(e)}")
            return df
    
    def filter_llm_spans(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter spans for LLM calls and tool executions.
        
        Args:
            df: Raw trace DataFrame from Phoenix
            
        Returns:
            Filtered DataFrame with LLM and tool spans
        """
        try:
            # Filter for LLM calls and tool executions
            llm_spans = df[
                (df['attributes.openinference.span.kind'] == 'LLM') |
                (df['name'].str.contains('ChatCompletion', case=False, na=False)) |
                (df['name'].str.contains('tool', case=False, na=False))
            ].copy()
            
            print(f"🤖 Found {len(llm_spans)} LLM/tool spans")
            return llm_spans
            
        except Exception as e:
            print(f"⚠️  Error filtering LLM spans: {str(e)}")
            return df
    
    def extract_conversation_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extract structured conversation data from Phoenix traces.
        
        Args:
            df: Filtered trace DataFrame
            
        Returns:
            List of conversation records
        """
        conversations = []
        
        try:
            for _, row in df.iterrows():
                conversation = {
                    "trace_id": row.get('context.trace_id', 'unknown'),
                    "span_id": row.get('context.span_id', 'unknown'),
                    "span_name": row.get('name', 'unknown'),
                    "status": row.get('status_code', 'unknown'),
                    "latency": self._extract_latency(row),
                    "cost": self._extract_cost(row),
                    "user_input": self._extract_user_input(row),
                    "response": self._extract_response(row),
                    "agent_name": self._extract_agent_name(row),
                    "success": self._extract_success(row),
                    "timestamp": row.get('start_time', datetime.now().isoformat()),
                    "tools_used": self._extract_tools(row),
                    "error_type": self._extract_error_type(row)
                }
                conversations.append(conversation)
            
            print(f"📊 Extracted {len(conversations)} conversation records")
            return conversations
            
        except Exception as e:
            print(f"❌ Error extracting conversation data: {str(e)}")
            return []
    
    def _extract_latency(self, row) -> float:
        """Extract latency from trace row."""
        try:
            if 'end_time' in row and 'start_time' in row:
                start = pd.to_datetime(row['start_time'])
                end = pd.to_datetime(row['end_time'])
                return (end - start).total_seconds() * 1000  # Convert to ms
            return 0.0
        except Exception:
            return 0.0
    
    def _extract_cost(self, row) -> float:
        """Extract cost information from trace row."""
        try:
            # Look for cost in various attribute fields
            cost_fields = [
                'attributes.llm.token_count.total',
                'attributes.conversation.cost',
                'attributes.cost'
            ]
            for field in cost_fields:
                if field in row and pd.notna(row[field]):
                    return float(row[field]) * 0.001  # Estimate cost
            return 0.0
        except Exception:
            return 0.0
    
    def _extract_user_input(self, row) -> str:
        """Extract user input from trace row."""
        try:
            input_fields = [
                'attributes.conversation.user_input',
                'attributes.input.value',
                'attributes.conversation.input_preview'
            ]
            for field in input_fields:
                if field in row and pd.notna(row[field]):
                    return str(row[field])
            return ""
        except Exception:
            return ""
    
    def _extract_response(self, row) -> str:
        """Extract agent response from trace row."""
        try:
            response_fields = [
                'attributes.conversation.response_text',
                'attributes.output.value',
                'attributes.conversation.response_preview'
            ]
            for field in response_fields:
                if field in row and pd.notna(row[field]):
                    return str(row[field])
            return ""
        except Exception:
            return ""
    
    def _extract_agent_name(self, row) -> str:
        """Extract agent name from trace row."""
        try:
            agent_fields = [
                'attributes.conversation.responding_agent',
                'attributes.agent.name',
                'attributes.conversation.agent_name'
            ]
            for field in agent_fields:
                if field in row and pd.notna(row[field]):
                    return str(row[field])
            return "unknown"
        except Exception:
            return "unknown"
    
    def _extract_success(self, row) -> bool:
        """Extract success status from trace row."""
        try:
            if 'status_code' in row:
                return row['status_code'] == 'OK'
            if 'attributes.conversation.success' in row:
                return bool(row['attributes.conversation.success'])
            return True  # Default to success if no error indicators
        except Exception:
            return True
    
    def _extract_tools(self, row) -> List[str]:
        """Extract tool usage from trace row."""
        try:
            tools = []
            tool_fields = [
                'attributes.llm.tools',
                'attributes.tool_calls',
                'name'
            ]
            for field in tool_fields:
                if field in row and pd.notna(row[field]):
                    value = str(row[field])
                    if 'tool' in value.lower() or 'function' in value.lower():
                        tools.append(value)
            return tools
        except Exception:
            return []
    
    def _extract_error_type(self, row) -> Optional[str]:
        """Extract error type from trace row."""
        try:
            if 'status_code' in row and row['status_code'] != 'OK':
                return row.get('status_message', 'unknown_error')
            if 'attributes.error.type' in row:
                return str(row['attributes.error.type'])
            return None
        except Exception:
            return None
    
    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Return empty DataFrame when Phoenix client is not available."""
        print("❌ No Phoenix API credentials configured")
        print("   Set PHOENIX_API_KEY and PHOENIX_SPACE_ID environment variables")
        return pd.DataFrame()


def analyze_all_analytics_system_spans():
    """
    Analyze ALL spans from the analytics_system project in Phoenix.
    
    This pulls all spans from the analytics_system project and provides
    comprehensive analysis of agent behavior, performance, and patterns.
    """
    print("🔍 Analytics System - Complete Span Analysis")
    print("=" * 60)
    
    # Initialize trace reader
    reader = PhoenixTraceReader()
    
    # Pull ALL spans from analytics_system from last 24 hours
    print("\n📡 Pulling ALL spans from analytics_system project...")
    all_spans = reader.pull_all_spans_from_analytics_system(hours_back=24)
    
    if all_spans.empty:
        print("❌ No spans found in analytics_system project")
        return
    
    print(f"\n📊 Total spans retrieved: {len(all_spans)}")
    
    # Show column structure for debugging
    if not all_spans.empty:
        print(f"\n🔍 Available columns: {list(all_spans.columns)[:10]}...")
        
    # Filter for different span types
    print("\n🔍 Analyzing span types...")
    
    # Get conversation spans
    conversation_spans = reader.filter_conversation_spans(all_spans)
    print(f"   Conversation spans: {len(conversation_spans)}")
    
    # Get LLM spans  
    llm_spans = reader.filter_llm_spans(all_spans)
    print(f"   LLM/Tool spans: {len(llm_spans)}")
    
    # Extract conversation data from all relevant spans
    print("\n📊 Extracting conversation data from all spans...")
    
    # Try to extract from conversation spans first, then fall back to all spans
    target_spans = conversation_spans if not conversation_spans.empty else all_spans
    conversations = reader.extract_conversation_data(target_spans)
    
    if not conversations:
        print("❌ No conversation data could be extracted")
        print("🔍 Raw span sample:")
        if not all_spans.empty:
            print(all_spans.head(2).to_dict('records'))
        return
    
    print(f"✅ Extracted {len(conversations)} conversation records")
    
    # Simple inline analysis since phoenix_monitor was deleted
    analysis = {
        "summary": {
            "total_traces": len(conversations),
            "analysis_timestamp": datetime.now().isoformat(),
        },
        "performance": {
            "success_rate": sum(1 for c in conversations if c.get("success", True)) / len(conversations) if conversations else 0,
            "total_conversations": len(conversations),
        },
        "agents": {
            "agent_usage": {},
        },
        "insights": []
    }
    
    # Count agent usage
    for conv in conversations:
        agent = conv.get("agent_name", "unknown")
        analysis["agents"]["agent_usage"][agent] = analysis["agents"]["agent_usage"].get(agent, 0) + 1
    
    # Generate simple insights
    if analysis["performance"]["success_rate"] == 1.0:
        analysis["insights"].append("✅ Perfect success rate (100%)")
    
    most_used_agent = max(analysis["agents"]["agent_usage"].keys(), key=analysis["agents"]["agent_usage"].get) if analysis["agents"]["agent_usage"] else "none"
    if most_used_agent != "none":
        analysis["insights"].append(f"🤖 Most utilized agent: {most_used_agent}")
    
    # Print comprehensive results
    print("\n📈 ANALYTICS SYSTEM SPAN ANALYSIS:")
    print("=" * 60)
    
    for section, data in analysis.items():
        if section == "insights":
            print(f"\n💡 {section.upper()}:")
            for insight in data:
                print(f"  • {insight}")
        elif isinstance(data, dict):
            print(f"\n📊 {section.upper()}:")
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for subkey, subvalue in value.items():
                        print(f"    {subkey}: {subvalue}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"\n{section}: {data}")
    
    # Additional span-level analysis
    print(f"\n🔍 SPAN-LEVEL INSIGHTS:")
    print(f"  Total spans analyzed: {len(all_spans)}")
    print(f"  Conversation spans: {len(conversation_spans)}")
    print(f"  LLM/Tool spans: {len(llm_spans)}")
    print(f"  Extracted conversations: {len(conversations)}")
    
    return analysis


if __name__ == "__main__":
    analyze_all_analytics_system_spans()
