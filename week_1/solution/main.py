"""
CSV Analytics Main Application (Unified)

This is the unified main entry point that uses the ChatService for consistent behavior
while maintaining all the robust features from the original implementation.

Key concepts:
- ChatService integration for clean architecture
- Comprehensive error handling (guardrails, UI interrupts, system errors)
- Robust startup and conversation flow
- Interface-agnostic business logic
- Session memory persistence

Use cases:
- Terminal-based data analysis interface
- Development and debugging with full error handling
- Consistent behavior with future web interfaces
- Production-ready terminal application
"""

import asyncio
from chat_service import ChatService


async def main():
    """
    Main application function using the ChatService with comprehensive error handling.

    This function demonstrates the complete workflow:
    1. Initialize ChatService and load data
    2. Present welcome message and system status
    3. Handle conversation loop with robust error handling
    4. Graceful exit handling for various termination scenarios

    The function maintains the same user experience as the original while
    using the clean ChatService architecture.
    """
    print("🔄 Starting CSV Analytics System...")

    # Initialize the chat service with dynamic session ID
    chat_service = ChatService()  # Generates unique UUID automatically

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

            # Check for exit commands (more comprehensive than refactored version)
            if user_input.lower().strip() in ["quit", "exit", "bye", "q"]:
                print("\n👋 Thank you for using CSV Analytics! Goodbye!")
                break

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
