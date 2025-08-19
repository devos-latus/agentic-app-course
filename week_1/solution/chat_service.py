"""
CSV Analytics Chat Service

This module provides a shared service layer for handling chat interactions
with the CSV Analytics agent system. It can be used by both terminal and web interfaces.

Key concepts:
- Interface-agnostic chat handling
- Session management abstraction
- Shared business logic for both terminal and web UIs
- Clean separation of concerns

Use cases:
- Terminal application chat handling
- Web interface chat handling
- API endpoint chat handling
- Consistent behavior across interfaces
"""

import os
import uuid
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered
from agents.exceptions import OutputGuardrailTripwireTriggered
from csv_agents import communication_agent, data_loader_agent
from phoenix.otel import register
import tools

# Load environment variables first
load_dotenv()

# Disable OpenAI agents internal tracing BEFORE importing agents
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

# Set Phoenix API key
os.environ["PHOENIX_API_KEY"] = os.getenv("PHEONIX_API_KEY")

# Register Phoenix tracing (suppress verbose output)
tracer_provider = register(
    project_name="analytics_system",
    endpoint="https://app.phoenix.arize.com/s/devos/v1/traces",
    protocol="http/protobuf",
    auto_instrument=True,
    verbose=False,
)


class ChatService:
    """
    Service class for handling chat interactions with the CSV Analytics system.

    This class provides a clean interface for chat functionality that can be
    used by both terminal and web interfaces.
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the chat service with dynamic session management.

        Args:
            session_id: Optional session ID. If None, generates a unique UUID.
                       Use this to resume existing conversations.
        """
        # Generate unique session ID for multi-user support
        self.session_id = session_id or str(uuid.uuid4())

        # Use in-memory database only (no persistence between app restarts)
        self.session = SQLiteSession(session_id=self.session_id)
        self._data_loaded = False

    async def initialize_data(self) -> Dict[str, Any]:
        """
        Load default CSV files at startup.

        Returns:
            Dict with initialization results and metadata
        """
        if self._data_loaded:
            return {"already_loaded": True, "tables": await self.get_available_tables()}

        try:
            # Use DataLoaderAgent to load default data
            result = await Runner.run(
                starting_agent=data_loader_agent,
                input="Please scan the 'data' directory and load all CSV files found there.",
                session=self.session,
            )

            self._data_loaded = True

            # Get current table information
            table_info = await self.get_available_tables()

            return {
                "success": True,
                "agent_response": result.final_output,
                "tables": table_info,
                "table_count": len(table_info) if table_info else 0,
            }

        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
            # Guardrails triggered during initialization - this is okay
            # It means there's no data or the agent response was filtered
            self._data_loaded = True

            # Get current table information
            table_info = await self.get_available_tables()

            return {
                "success": True,
                "agent_response": "No data directory found or no CSV files available for loading.",
                "tables": table_info,
                "table_count": len(table_info) if table_info else 0,
                "guardrail_triggered": True,
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
            Dict with response and metadata. Possible response types:
            - success=True: Normal response from agent
            - success=False, error_type="guardrail": Off-topic message blocked
            - success=False, error_type="system": System/technical error
            - success=False, error_type="validation": Input validation error
        """
        if not message.strip():
            return {
                "success": False,
                "error_type": "validation",
                "error": "Empty message",
                "response": "Please provide a message.",
            }

        try:
            # Use communication agent as entry point
            result = await Runner.run(
                starting_agent=communication_agent, input=message, session=self.session
            )

            return {
                "success": True,
                "response": result.final_output,
                "agent_name": result.final_agent.name
                if hasattr(result, "final_agent")
                else "Unknown",
            }

        except InputGuardrailTripwireTriggered:
            # Handle input guardrail violations
            return {
                "success": False,
                "error_type": "guardrail",
                "error": "Off-topic question blocked by input guardrail",
                "response": "🔍 I can only help with data analysis questions about your CSV datasets. Please ask about your data, table schemas, or analytics queries.",
            }

        except OutputGuardrailTripwireTriggered:
            # Handle output guardrail violations
            return {
                "success": False,
                "error_type": "guardrail",
                "error": "Response blocked by output guardrail",
                "response": "🔍 I can only provide responses about data analysis and CSV datasets. Please ask questions about your data, calculations, or insights from your datasets.",
            }

        except Exception as e:
            # Handle all other system errors
            return {
                "success": False,
                "error_type": "system",
                "error": str(e),
                "response": f"❌ Error: {str(e)}",
            }

    async def load_csv_file(self, file_path: str, table_name: str) -> Dict[str, Any]:
        """
        Load a CSV file using the DataLoaderAgent.

        Args:
            file_path: Path to the CSV file
            table_name: Name for the table

        Returns:
            Dict with loading results. Response types:
            - success=True: File loaded successfully
            - success=False, error_type="validation": Invalid parameters
            - success=False, error_type="system": Loading/system error
        """
        if not file_path or not file_path.strip():
            return {
                "success": False,
                "error_type": "validation",
                "error": "File path is required",
                "response": "Please provide a valid file path.",
            }

        if not table_name or not table_name.strip():
            return {
                "success": False,
                "error_type": "validation",
                "error": "Table name is required",
                "response": "Please provide a valid table name.",
            }

        try:
            load_request = f"Please load the CSV file '{file_path}' and name the table '{table_name.strip()}'"

            result = await Runner.run(
                starting_agent=data_loader_agent,
                input=load_request,
                session=self.session,
            )

            # Check if the response indicates failure
            response_text = result.final_output.lower()
            if any(
                error_phrase in response_text
                for error_phrase in [
                    "error:",
                    "not found",
                    "does not exist",
                    "failed to load",
                    "unable to load",
                    "cannot load",
                    "file not found",
                ]
            ):
                return {
                    "success": False,
                    "error_type": "system",
                    "error": f"File loading failed: {result.final_output}",
                    "response": f"❌ Unable to load file '{file_path}'. {result.final_output}",
                }

            return {
                "success": True,
                "response": result.final_output,
                "table_name": table_name.strip(),
            }

        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
            # Guardrails triggered during file loading - usually means file issues
            return {
                "success": False,
                "error_type": "system",
                "error": "File loading blocked by guardrail (file may not exist or be invalid)",
                "response": f"❌ Unable to load file '{file_path}'. Please check that the file exists and is a valid CSV.",
            }

        except Exception as e:
            return {
                "success": False,
                "error_type": "system",
                "error": str(e),
                "response": f"❌ Error loading file: {str(e)}",
            }

    async def get_available_tables(self) -> Optional[list]:
        """
        Get list of currently available tables.

        Returns:
            List of table information or None if error
        """
        try:
            tables_info = tools._get_all_tables()
            if tables_info["success"]:
                return tables_info["tables"]
            return None
        except Exception:
            return None

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
                data_context = f"I have loaded {table_count} datasets. "
                data_context += "Please use your tools to get the details and welcome the user with a comprehensive overview."
            else:
                data_context = "No datasets were loaded. Please welcome the user and explain the situation."

            welcome_result = await Runner.run(
                starting_agent=communication_agent,
                input=data_context,
                session=self.session,
            )

            return welcome_result.final_output

        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
            # Guardrails triggered during welcome - provide fallback
            table_info = await self.get_available_tables()
            table_count = len(table_info) if table_info else 0

            if table_count > 0:
                return f"Welcome to CSV Analytics! I have {table_count} datasets loaded and ready for analysis. Ask me questions about your data!"
            else:
                return "Welcome to CSV Analytics! No datasets are currently loaded. You can upload CSV files and I'll help you analyze them."

        except Exception as e:
            return f"Welcome to CSV Analytics! (Note: {str(e)})"

    def close_session(self):
        """
        Clean up session resources when conversation ends.

        This ensures proper cleanup of in-memory resources and prevents
        memory leaks in multi-user scenarios. Also cleans up generated chart files.
        """
        # Clean up chart files
        self._cleanup_chart_files()

        # SQLiteSession with in-memory database will be garbage collected
        # No explicit cleanup needed for in-memory databases
        self._data_loaded = False

    def _cleanup_chart_files(self):
        """
        Clean up generated chart files from the current session.

        Removes all PNG files from the charts directory to prevent disk space
        accumulation from multiple sessions.
        """
        import os
        import glob

        try:
            charts_dir = os.path.join(os.path.dirname(__file__), "charts")
            if os.path.exists(charts_dir):
                # Remove all PNG chart files
                chart_files = glob.glob(os.path.join(charts_dir, "*.png"))
                for chart_file in chart_files:
                    try:
                        os.remove(chart_file)
                        print(
                            f"🧹 Cleaned up chart file: {os.path.basename(chart_file)}"
                        )
                    except Exception:
                        # Ignore individual file cleanup errors
                        pass

                if chart_files:
                    print(
                        f"✅ Session cleanup complete - removed {len(chart_files)} chart file(s)"
                    )
        except Exception:
            # Ignore cleanup errors to prevent session termination issues
            pass


# Convenience functions for backward compatibility
async def initialize_chat_service(session_id: Optional[str] = None) -> ChatService:
    """
    Initialize and return a ChatService instance with data loaded.

    Args:
        session_id: Optional session ID. If None, generates unique UUID.

    Returns:
        Initialized ChatService instance
    """
    service = ChatService(session_id)
    await service.initialize_data()
    return service
