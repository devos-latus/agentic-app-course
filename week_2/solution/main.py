"""
CSV Analytics Main Application (Week 2 Enhanced)

This is the Week 2 version that uses the EnhancedChatService with comprehensive
Phoenix tracing while maintaining the same user experience as Week 1.

Key concepts:
- ChatService integration for clean architecture (same as Week 1)
- Enhanced Phoenix tracing with conversation flow grouping (Week 2 addition)
- Comprehensive error handling (same as Week 1)
- Robust startup and conversation flow (same as Week 1)
- Session memory persistence (same as Week 1)
- Real-time logging with offline analysis (Week 2 addition)

Use cases:
- Terminal-based data analysis interface (same as Week 1)
- Development and debugging with enhanced observability (Week 2 addition)
- Production monitoring with Phoenix tracing (Week 2 addition)
- Consistent behavior with Week 1 interface
"""

import asyncio
import sys
from pathlib import Path

# Add Week 1 solution to path for base functionality
week1_path = Path(__file__).parent.parent.parent / "week_1" / "solution"
sys.path.insert(0, str(week1_path))

# Import enhanced tracing from our solution module
from enhanced_chat_service import EnhancedChatService


async def main():
    """
    Main application function using EnhancedChatService with comprehensive tracing.

    This function demonstrates the complete workflow (same as Week 1):
    1. Initialize EnhancedChatService and load data
    2. Present welcome message and system status
    3. Handle conversation loop with robust error handling
    4. Graceful exit handling for various termination scenarios

    Week 2 enhancements:
    - Uses EnhancedChatService instead of ChatService
    - Comprehensive Phoenix tracing with conversation flow grouping
    - Real-time logging with offline analysis capabilities
    - Enhanced session analytics
    """
    print("🔄 Starting CSV Analytics System...")

    # Initialize the enhanced chat service (Week 2 enhancement)
    chat_service = EnhancedChatService()  # Week 2: Enhanced version with tracing

    # Load initial data
    print("📁 Loading data...")

    try:
        init_result = await chat_service.initialize_data()

        if init_result.get("table_count", 0) > 0:
            print(f"✅ Loaded {init_result['table_count']} datasets!")
        else:
            print("⚠️  No datasets loaded. You can still interact with the system.")
            print(
                "The system will start, but no datasets will be available for analysis."
            )

    except Exception as e:
        print(f"⚠️  Warning during data loading: {str(e)}")
        print("The system will still start, but some features may be limited.")

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
    print("Type 'quit', 'exit', 'bye', or 'q' to end the conversation.\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ")

            # Check for exit commands (same as Week 1)
            if user_input.lower().strip() in ["quit", "exit", "bye", "q"]:
                print("\n👋 Thank you for using CSV Analytics! Goodbye!")
                break

            # Handle Week 2 analytics command
            if user_input.lower().strip() == "analytics":
                analytics = chat_service.get_session_analytics()
                print("\n📊 Session Analytics:")
                print(f"  Session ID: {analytics['session_id']}")
                print(f"  Messages processed: {analytics['conversation_count']}")
                print(f"  Data loaded: {'✅' if analytics['data_loaded'] else '❌'}")
                print(
                    f"  Enhanced tracing: {'✅' if analytics['enhanced_tracing_enabled'] else '❌'}"
                )
                print(f"  Phoenix project: {analytics['phoenix_project']}")
                print("  🔍 Complete traces available in Phoenix dashboard")
                continue

            # Handle Week 2 trace command
            if user_input.lower().strip() == "trace":
                analytics = chat_service.get_session_analytics()
                print("\n🔍 Trace Context:")
                print(f"  Session ID: {analytics['session_id']}")
                print(f"  Messages: {analytics['conversation_count']}")
                print(
                    f"  Enhanced tracing: {'✅' if analytics['enhanced_tracing_enabled'] else '❌'}"
                )
                print("📊 Check Phoenix dashboard for detailed traces!")
                continue

            # Handle empty input (same as Week 1)
            if not user_input.strip():
                print(
                    "Please ask a question about your data, or type 'quit' to exit.\n"
                )
                continue

            # Send message to chat service (same as Week 1)
            response = await chat_service.send_message(user_input)

            if response["success"]:
                print(f"\nAgent: {response['response']}\n")
            else:
                # Handle different error types appropriately (same as Week 1)
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
            # Handle Ctrl+C gracefully (same as Week 1)
            print("\n\n👋 Thank you for using CSV Analytics! Goodbye!")
            break

        except EOFError:
            # Handle EOF (when input stream ends) (same as Week 1)
            print(
                "\n\n👋 Input stream ended. Thank you for using CSV Analytics! Goodbye!"
            )
            break

        except Exception as e:
            # Handle any other unexpected errors (same as Week 1)
            print(f"\n❌ Unexpected error: {str(e)}")
            print(
                "Please try asking your question differently, or type 'quit' to exit.\n"
            )

    # Clean up session resources when conversation ends (same as Week 1)
    print("\n🧹 Cleaning up session resources...")
    try:
        chat_service.close_session()
    except Exception:
        pass  # Ignore cleanup errors


if __name__ == "__main__":
    asyncio.run(main())
