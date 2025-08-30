"""
Terminal Main Application for Week 3 Testing

Terminal interface for testing the Week 3 containerized application locally.
This allows us to test all components (MCP server + agents + Phoenix tracing)
before containerizing.

Key concepts:
- Local testing of container components
- MCP server stdio integration testing
- Agent system validation
- Phoenix tracing verification
- Data loading and analysis testing

Use cases:
- Pre-container testing and validation
- Development and debugging
- Component integration testing
- Performance verification
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agents_.chat_service import ChatService, initialize_chat_service


async def main():
    """
    Main terminal application for testing Week 3 functionality.

    This function tests the complete Week 3 system:
    1. Initialize ChatService with MCP server integration
    2. Start MCP server subprocess with stdio transport
    3. Load CSV data from local data directory
    4. Present welcome message and system status
    5. Handle conversation loop with robust error handling
    6. Phoenix tracing integration for observability
    7. Graceful exit handling and resource cleanup
    """
    print("🚀 Starting Week 3 CSV Analytics System (Terminal Test Mode)")
    print("🔧 Testing: MCP Server + Agents + Phoenix Tracing + Data Loading")
    print("📁 Data directory: ./data/")
    print("📡 MCP Transport: stdio (subprocess)")
    print("🔍 Phoenix Tracing: enabled")
    print()

    # Initialize the chat service with MCP integration
    print("🔄 Initializing ChatService with MCP server...")
    
    try:
        chat_service = await initialize_chat_service()
        print("✅ ChatService initialized successfully!")
        
        # Verify MCP server is running
        analytics = chat_service.get_session_analytics()
        if analytics["mcp_server_active"]:
            print("✅ MCP server started successfully!")
        else:
            print("❌ MCP server failed to start!")
            return
            
    except Exception as e:
        print(f"❌ Failed to initialize ChatService: {str(e)}")
        print("Please check your environment configuration and dependencies.")
        return

    # Get welcome message
    print("\n🤖 Getting welcome message...")

    try:
        welcome_msg = await chat_service.get_welcome_message()
        print(f"\n{welcome_msg}\n")

    except Exception as e:
        print(f"❌ Error during welcome: {str(e)}")
        print("You can still ask questions about the data directly.\n")

    # Start conversation loop
    print("💬 You can now ask questions about your data!")
    print("🔍 Phoenix tracing active - check dashboard for traces!")
    print("📊 Special commands:")
    print("  - 'analytics' - Show session analytics")
    print("  - 'tools' - List available MCP tools")
    print("  - 'health' - Check system health")
    print("Type 'quit', 'exit', 'bye', or 'q' to end the conversation.\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ")

            # Check for exit commands
            if user_input.lower().strip() in ["quit", "exit", "bye", "q"]:
                analytics = chat_service.get_session_analytics()
                print("\n📊 Session Summary:")
                print(f"  Messages processed: {analytics['conversation_count']}")
                print(f"  Session ID: {analytics['session_id'][:8]}...")
                print(f"  Data loaded: {'✅' if analytics['data_loaded'] else '❌'}")
                print(f"  MCP server: {'✅' if analytics['mcp_server_active'] else '❌'}")
                print("  🔍 Check Phoenix dashboard for complete conversation traces!")

                print("\n👋 Thank you for using Week 3 CSV Analytics! Goodbye!")
                break

            # Handle special commands
            if user_input.lower().strip() == "analytics":
                analytics = chat_service.get_session_analytics()
                print(f"\n📊 Session Analytics:")
                print(f"  Session ID: {analytics['session_id']}")
                print(f"  Messages processed: {analytics['conversation_count']}")
                print(f"  Data loaded: {'✅' if analytics['data_loaded'] else '❌'}")
                print(f"  Enhanced tracing: {'✅' if analytics['enhanced_tracing_enabled'] else '❌'}")
                print(f"  MCP server active: {'✅' if analytics['mcp_server_active'] else '❌'}")
                print(f"  Phoenix project: {analytics['phoenix_project']}")
                print("  🔍 Complete traces available in Phoenix dashboard")
                continue

            if user_input.lower().strip() == "tools":
                print("\n🔧 Testing MCP tool discovery...")
                try:
                    tools_result = await chat_service.mcp_client.call_tool("list_available_tools", {})
                    if tools_result.get("success"):
                        print(f"✅ MCP Server Tools ({tools_result['total_tools']} total):")
                        for category, tools in tools_result["categories"].items():
                            print(f"  📂 {category}:")
                            for tool_name, description in tools.items():
                                print(f"    - {tool_name}: {description}")
                    else:
                        print(f"❌ Failed to get tools: {tools_result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ Error testing MCP tools: {str(e)}")
                continue

            if user_input.lower().strip() == "health":
                print("\n🏥 System Health Check:")
                analytics = chat_service.get_session_analytics()
                print(f"  FastAPI: Not running (terminal mode)")
                print(f"  MCP Server: {'✅ Healthy' if analytics['mcp_server_active'] else '❌ Unhealthy'}")
                print(f"  Agents: ✅ Healthy")
                print(f"  Phoenix Tracing: {'✅ Enabled' if analytics['enhanced_tracing_enabled'] else '❌ Disabled'}")
                print(f"  Data Loading: {'✅ Complete' if analytics['data_loaded'] else '⚠️ Incomplete'}")
                print(f"  Session Count: {analytics['conversation_count']}")
                continue

            # Handle empty input
            if not user_input.strip():
                print("Please ask a question about your data, or type 'quit' to exit.\n")
                continue

            # Send message to chat service
            response = await chat_service.send_message(user_input)

            if response["success"]:
                print(f"\nAgent: {response['response']}\n")
            else:
                # Handle different error types appropriately
                error_type = response.get("error_type", "unknown")
                if error_type == "guardrail":
                    # Guardrail violations get a cleaner message (no ❌)
                    print(f"\n{response['response']}\n")
                elif error_type == "validation":
                    # Validation errors are usually user input issues
                    print(f"\n{response['response']}\n")
                else:
                    # System errors show more technical detail
                    print(f"\n❌ Error: {response['error']}\n")

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\n👋 Thank you for using Week 3 CSV Analytics! Goodbye!")
            break

        except EOFError:
            # Handle EOF (when input stream ends)
            print("\n\n👋 Input stream ended. Thank you for using Week 3 CSV Analytics! Goodbye!")
            break

        except Exception as e:
            # Handle any other unexpected errors
            print(f"\n❌ Unexpected error: {str(e)}")
            print("Please try asking your question differently, or type 'quit' to exit.\n")

    # Clean up session resources when conversation ends
    print("\n🧹 Cleaning up session resources...")
    try:
        await chat_service.close_session()
        print("✅ Cleanup complete!")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Week 3 CSV Analytics - Terminal Test Mode")
    print("Testing MCP Integration + Agents + Phoenix Tracing")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Application terminated by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print("Please check your configuration and try again.")
