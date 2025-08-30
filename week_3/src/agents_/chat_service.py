"""
Enhanced CSV Analytics Chat Service - Week 3 Container Version

This module provides a complete chat service that combines Week 1 + Week 2 
functionality in a self-contained package for containerized deployment.
It integrates with MCP server via stdio transport for tool operations.

Key concepts:
- MCP Integration: Communicates with MCP server via stdio transport
- Container-Ready: Self-contained with no external folder dependencies
- Enhanced Tracing: Optional Phoenix observability integration
- Multi-Agent System: Orchestrates specialized agents for data analysis
- Session Management: UUID-based sessions for multi-user support

Use cases:
- HTTP API backend for containerized deployment
- Terminal interface for direct interaction
- Multi-user web applications
- Production monitoring with observability
"""

import os
import uuid
import asyncio
import subprocess
import json
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered, set_tracing_disabled
from agents.exceptions import OutputGuardrailTripwireTriggered
from .csv_agents import communication_agent, data_loader_agent

# Load environment variables
load_dotenv()

# Disable OpenAI agents internal tracing to prevent 401 errors
set_tracing_disabled(True)

# Phoenix tracing setup - Optional for container deployment
try:
    from phoenix.trace import using_project
    from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
    from helpers.model_helper import get_tracing_provider
    
    # Only initialize if Phoenix endpoint is configured
    phoenix_endpoint = os.getenv("PHOENIX_ENDPOINT")
    phoenix_api_key = os.getenv("PHOENIX_API_KEY")
    
    if phoenix_endpoint and phoenix_api_key:
        tracing_provider = get_tracing_provider("analytics_system")
        OpenAIAgentsInstrumentor().instrument()
        TRACING_AVAILABLE = True
        print("🔭 Phoenix tracing enabled")
    else:
        TRACING_AVAILABLE = False
        print("🔕 Phoenix tracing disabled - missing configuration")
        
except Exception as e:
    TRACING_AVAILABLE = False
    print(f"⚠️ Phoenix tracing failed to initialize: {e}")
    print("🔕 Continuing without Phoenix tracing")


class MCPClient:
    """
    MCP Client for stdio communication with MCP server.
    
    Handles starting the MCP server process and communicating via stdin/stdout.
    """
    
    def __init__(self):
        self.process = None
        self.request_id = 0
    
    async def start(self):
        """Start the MCP server process with proper stdio setup."""
        try:
            # Determine the correct path to the MCP server
            import os
            current_dir = os.path.dirname(__file__)
            server_path = os.path.join(current_dir, "..", "mcp_server", "server.py")
            
            # For container deployment, use absolute path
            if not os.path.exists(server_path):
                server_path = "/app/src/mcp_server/server.py"
            
            # Start MCP server as subprocess with proper stdio handling
            self.process = await asyncio.create_subprocess_exec(
                "python", server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()  # Pass environment variables
            )
            
            # Give the server a moment to start and check if it's running
            await asyncio.sleep(0.5)
            
            # Check if process is still running
            if self.process.returncode is not None:
                stderr_output = await self.process.stderr.read()
                error_msg = stderr_output.decode() if stderr_output else "Unknown error"
                print(f"MCP server failed to start: {error_msg}")
                return False
            
            return True
        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool via stdio transport with improved error handling.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Dict containing tool result or error
        """
        if not self.process:
            return {"success": False, "error": "MCP server not started"}
        
        try:
            # Check if process is still running
            if self.process.returncode is not None:
                return {"success": False, "error": "MCP server process has terminated"}
            
            self.request_id += 1
            
            # Try proper JSON-RPC stdio protocol first
            try:
                # Create proper MCP JSON-RPC request
                request = {
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                # Send request with proper line termination
                request_json = json.dumps(request) + "\n"
                self.process.stdin.write(request_json.encode())
                await self.process.stdin.drain()
                
                # Read response with timeout
                try:
                    response_line = await asyncio.wait_for(
                        self.process.stdout.readline(), 
                        timeout=10.0
                    )
                    
                    if not response_line:
                        raise Exception("Empty response from MCP server")
                    
                    response = json.loads(response_line.decode().strip())
                    
                    if "result" in response:
                        return response["result"]
                    elif "error" in response:
                        return {"success": False, "error": response["error"].get("message", "Unknown MCP error")}
                    else:
                        return {"success": False, "error": "Invalid MCP response format"}
                        
                except asyncio.TimeoutError:
                    return {"success": False, "error": "MCP server response timeout"}
                    
            except Exception as stdio_error:
                # Fallback: Import and call tools directly
                # This ensures functionality even if stdio protocol fails
                try:
                    import sys
                    from mcp_server import server
                    
                    if hasattr(server, tool_name):
                        tool_func = getattr(server, tool_name)
                        if arguments:
                            result = tool_func(**arguments)
                        else:
                            result = tool_func()
                        return result
                    else:
                        return {"success": False, "error": f"MCP tool '{tool_name}' not found"}
                        
                except ImportError as e:
                    return {"success": False, "error": f"MCP communication failed and could not import tools: {str(e)}"}
                
        except Exception as e:
            return {"success": False, "error": f"MCP tool call error: {str(e)}"}
    
    async def stop(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None


class ChatService:
    """
    Chat Service that combines Week 1 + Week 2 functionality
    with MCP server integration for containerized deployment.
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the enhanced chat service with MCP integration.

        Args:
            session_id: Optional session ID. If None, generates a unique UUID.
        """
        # Generate unique session ID for multi-user support
        self.session_id = session_id or str(uuid.uuid4())
        
        # Use in-memory database only (no persistence between app restarts)
        self.session = SQLiteSession(session_id=self.session_id)
        self._data_loaded = False
        
        # MCP client for tool operations
        self.mcp_client = MCPClient()
        
        # Enhanced tracing attributes
        self.conversation_count = 0
        
        print(f"🚀 CSV Analytics Service initialized (Session: {self.session_id[:8]})")

    async def start_mcp_server(self) -> bool:
        """Start the MCP server for tool operations."""
        return await self.mcp_client.start()

    async def initialize_data(self) -> Dict[str, Any]:
        """
        Load default CSV files at startup via MCP server.

        Returns:
            Dict with initialization results and metadata
        """
        if self._data_loaded:
            return {"already_loaded": True, "tables": await self.get_available_tables()}

        try:
            # Use MCP server to load CSV files from data directory
            result = await self.mcp_client.call_tool(
                "load_data",
                {"source": "/data"}
            )
            
            self._data_loaded = True

            # Get current table information via MCP
            table_info = await self.get_available_tables()

            return {
                "success": result.get("success", True),
                "mcp_response": result,
                "tables": table_info,
                "table_count": len(table_info) if table_info else 0,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_response": f"❌ Error during initialization: {str(e)}",
                "tables": [],
                "table_count": 0,
            }

    async def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a message to the agent system and get a response.

        Args:
            message: User's message

        Returns:
            Dict with response and metadata
        """
        if not message.strip():
            return {
                "success": False,
                "error_type": "validation",
                "error": "Empty message",
                "response": "Please provide a message.",
            }

        self.conversation_count += 1

        try:
            # Use Phoenix tracing context (required)
            async with self._trace_conversation(message):
                result = await self._process_message(message)

            return result

        except InputGuardrailTripwireTriggered:
            return {
                "success": False,
                "error_type": "guardrail",
                "error": "Off-topic question blocked by input guardrail",
                "response": "🔍 I can only help with data analysis questions about your CSV datasets. Please ask about your data, table schemas, or analytics queries.",
            }

        except OutputGuardrailTripwireTriggered:
            return {
                "success": False,
                "error_type": "guardrail",
                "error": "Response blocked by output guardrail",
                "response": "🔍 I can only provide responses about data analysis and CSV datasets. Please ask questions about your data, calculations, or insights from your datasets.",
            }

        except Exception as e:
            return {
                "success": False,
                "error_type": "system",
                "error": str(e),
                "response": f"❌ Error: {str(e)}",
            }

    async def _process_message(self, message: str) -> Dict[str, Any]:
        """Process message through agent system."""
        # Use communication agent as entry point
        result = await Runner.run(
            starting_agent=communication_agent, 
            input=message, 
            session=self.session
        )

        return {
            "success": True,
            "response": result.final_output,
            "agent_name": result.final_agent.name if hasattr(result, "final_agent") else "Unknown",
            "conversation_count": self.conversation_count,
        }

    @asynccontextmanager
    async def _trace_conversation(self, message: str):
        """Create Phoenix tracing context for conversation."""
        with using_project("analytics_system"):
            # Create conversation span
            from opentelemetry import trace
            tracer = trace.get_tracer(__name__)
            
            session_short = self.session_id[-8:]
            span_name = f"conversation_{session_short}_{self.conversation_count}"
            
            with tracer.start_as_current_span(
                span_name,
                attributes={
                    "conversation.session_id": self.session_id,
                    "conversation.message_number": self.conversation_count,
                    "conversation.input_length": len(message),
                    "conversation.input_preview": message[:100] + "..." if len(message) > 100 else message,
                    "service.name": "csv_analytics_container",
                    "service.version": "3.0.0",
                }
            ) as span:
                try:
                    yield span
                except Exception as e:
                    span.set_attribute("error.message", str(e))
                    raise

    async def get_available_tables(self) -> Optional[list]:
        """
        Get list of currently available tables via MCP server.

        Returns:
            List of table information or None if error
        """
        try:
            result = await self.mcp_client.call_tool("get_all_tables", {})
            if result.get("success"):
                return result.get("tables", [])
            return []
        except Exception:
            return []

    async def get_welcome_message(self) -> str:
        """
        Get a welcome message from the communication agent.

        Returns:
            Welcome message string
        """
        try:
            table_info = await self.get_available_tables()
            table_count = len(table_info) if table_info else 0

            if table_count > 0:
                data_context = f"I have loaded {table_count} datasets. Please provide a comprehensive welcome with available data overview."
            else:
                data_context = "No datasets were loaded. Please welcome the user and explain the situation."

            with using_project("analytics_system"):
                welcome_result = await Runner.run(
                    starting_agent=communication_agent,
                    input=data_context,
                    session=self.session,
                )

            return welcome_result.final_output

        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
            table_info = await self.get_available_tables()
            table_count = len(table_info) if table_info else 0

            if table_count > 0:
                return f"Welcome to CSV Analytics! I have {table_count} datasets loaded and ready for analysis. Ask me questions about your data!"
            else:
                return "Welcome to CSV Analytics! No datasets are currently loaded. The system will attempt to load data from the container."

        except Exception as e:
            return f"Welcome to CSV Analytics! (Note: {str(e)})"

    def get_session_analytics(self) -> dict:
        """
        Get session analytics for monitoring.
        
        Returns:
            Dict with session statistics
        """
        return {
            "session_id": self.session_id,
            "conversation_count": self.conversation_count,
            "data_loaded": self._data_loaded,
            "enhanced_tracing_enabled": True,
            "phoenix_project": "analytics_system",
            "mcp_server_active": self.mcp_client.process is not None,
        }

    async def close_session(self):
        """
        Clean up session resources when conversation ends.
        """
        try:
            # Stop MCP server
            await self.mcp_client.stop()
        except Exception as e:
            print(f"⚠️ MCP server cleanup warning: {e}")
        
        try:
            # Clean up chart files
            self._cleanup_chart_files()
        except Exception as e:
            print(f"⚠️ Chart cleanup warning: {e}")
        
        # Clean up other resources
        self._data_loaded = False
        
        print(f"✅ Session {self.session_id[:8]} closed successfully")

    def _cleanup_chart_files(self):
        """
        Clean up generated chart files from the current session.
        
        Removes all PNG files from the charts directory to prevent disk space
        accumulation from multiple sessions.
        """
        import os
        import glob
        
        try:
            # Look for charts directory in multiple possible locations
            possible_chart_dirs = [
                os.path.join(os.path.dirname(__file__), "charts"),
                os.path.join(os.getcwd(), "charts"),
                "/app/charts",
                "charts"
            ]
            
            for charts_dir in possible_chart_dirs:
                if os.path.exists(charts_dir):
                    # Remove all PNG chart files
                    chart_files = glob.glob(os.path.join(charts_dir, "*.png"))
                    for chart_file in chart_files:
                        try:
                            os.remove(chart_file)
                            print(f"🧹 Cleaned up chart file: {os.path.basename(chart_file)}")
                        except Exception:
                            # Ignore individual file cleanup errors
                            pass
                    
                    if chart_files:
                        print(f"✅ Session cleanup complete - removed {len(chart_files)} chart file(s)")
                    break
        except Exception:
            # Ignore cleanup errors to prevent session termination issues
            pass


# Convenience functions for backward compatibility
async def initialize_chat_service(session_id: Optional[str] = None) -> ChatService:
    """
    Initialize and return a ChatService instance with MCP server started.

    Args:
        session_id: Optional session ID. If None, generates unique UUID.

    Returns:
        Initialized ChatService instance
    """
    service = ChatService(session_id)
    
    # Start MCP server
    mcp_started = await service.start_mcp_server()
    if not mcp_started:
        print("⚠️ Warning: MCP server failed to start - some features may be limited")
    
    # Initialize data
    await service.initialize_data()
    
    return service
