"""
CSV Analytics Main Application (Enhanced for Week 2)

This is the main entry point that uses either the original ChatService or
the enhanced version with comprehensive Phoenix tracing for Week 2.

Key concepts:
- ChatService integration for clean architecture
- Enhanced Phoenix tracing with conversation flow grouping
- Comprehensive error handling (guardrails, UI interrupts, system errors)
- Robust startup and conversation flow
- Interface-agnostic business logic
- Session memory persistence
- Optional Week 2 observability enhancements

Use cases:
- Terminal-based data analysis interface
- Development and debugging with full error handling
- Production monitoring with Phoenix tracing
- Performance analysis and cost tracking
- Consistent behavior across interfaces
"""

import asyncio
import sys
from pathlib import Path
from chat_service import ChatService

# Check if Week 2 enhancements are available
week2_path = Path(__file__).parent.parent.parent / "week_2" / "solution"
WEEK2_AVAILABLE = (week2_path / "monitoring" / "enhanced_chat_service.py").exists()

if WEEK2_AVAILABLE:
    sys.path.insert(0, str(week2_path))
    try:
        from monitoring.enhanced_chat_service import EnhancedChatService

        ENHANCED_TRACING_AVAILABLE = True
    except ImportError:
        ENHANCED_TRACING_AVAILABLE = False
        print("⚠️  Week 2 enhancements found but could not be imported")
else:
    ENHANCED_TRACING_AVAILABLE = False


async def main():
    """
    Main application function with optional Week 2 enhanced tracing.

    This function demonstrates the complete workflow:
    1. Initialize ChatService (enhanced if Week 2 available)
    2. Present welcome message and system status
    3. Handle conversation loop with robust error handling
    4. Optional Phoenix tracing enhancements for observability
    5. Graceful exit handling for various termination scenarios

    Week 2 enhancements add:
    - Conversation-level trace grouping
    - Business logic insights
    - Performance monitoring
    - Message type classification
    """

    # Determine which service to use
    if ENHANCED_TRACING_AVAILABLE:
        print("🚀 Starting CSV Analytics System with Enhanced Phoenix Tracing...")
        print("🔍 Week 2 observability enhancements active!")
        print(
            "📊 Check Phoenix dashboard: https://app.phoenix.arize.com (project: analytics_system)"
        )
        chat_service = EnhancedChatService()  # Week 2 enhanced version
    else:
        print("🔄 Starting CSV Analytics System...")
        print("💡 Run from week_2/solution for enhanced tracing!")
        chat_service = ChatService()  # Original Week 1 version

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

    if ENHANCED_TRACING_AVAILABLE:
        print(
            "🔍 Enhanced tracing active - check Phoenix dashboard for detailed traces!"
        )
        print("Type 'trace' to see session analytics.")

    print("Type 'quit', 'exit', 'bye', or 'q' to end the conversation.\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ")

            # Check for exit commands
            if user_input.lower().strip() in ["quit", "exit", "bye", "q"]:
                if ENHANCED_TRACING_AVAILABLE and hasattr(
                    chat_service, "get_session_analytics"
                ):
                    analytics = chat_service.get_session_analytics()
                    print("\n📊 Session Summary:")
                    print(f"  Messages processed: {analytics['conversation_count']}")
                    print(
                        f"  Most common query type: {analytics['most_common_message_type']}"
                    )
                    print(f"  Session ID: {analytics['session_id']}")
                    print(
                        "  🔍 Check Phoenix dashboard for complete conversation traces!"
                    )

                print("\n👋 Thank you for using CSV Analytics! Goodbye!")
                break

            # Handle Week 2 trace command
            if ENHANCED_TRACING_AVAILABLE and user_input.lower().strip() == "trace":
                if hasattr(chat_service, "get_session_analytics"):
                    analytics = chat_service.get_session_analytics()
                    print("\n📊 Session Analytics:")
                    print(f"  Session ID: {analytics['session_id']}")
                    print(f"  Messages processed: {analytics['conversation_count']}")
                    print(f"  Message types: {analytics['message_types']}")
                    print(
                        f"  Data loaded: {'✅' if analytics['data_loaded'] else '❌'}"
                    )
                    print("  Phoenix project: analytics_system")
                    print("  🔍 Check Phoenix dashboard for detailed traces")
                continue

            # Handle empty input
            if not user_input.strip():
                print(
                    "Please ask a question about your data, or type 'quit' to exit.\n"
                )
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
            print("\n\n👋 Thank you for using CSV Analytics! Goodbye!")
            break

        except EOFError:
            # Handle EOF (when input stream ends)
            print(
                "\n\n👋 Input stream ended. Thank you for using CSV Analytics! Goodbye!"
            )
            break

        except Exception as e:
            # Handle any other unexpected errors
            print(f"\n❌ Unexpected error: {str(e)}")
            print(
                "Please try asking your question differently, or type 'quit' to exit.\n"
            )

    # Clean up session resources when conversation ends
    print("\n🧹 Cleaning up session resources...")
    try:
        chat_service.close_session()
    except Exception:
        pass  # Ignore cleanup errors


if __name__ == "__main__":
    asyncio.run(main())
