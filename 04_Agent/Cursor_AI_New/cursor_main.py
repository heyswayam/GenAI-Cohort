from dotenv import load_dotenv
from openai import OpenAI
import json
from pathlib import Path
import time
import os
import functions
import system_prompt
load_dotenv()

client = OpenAI()

# =====================================
# TOKEN OPTIMIZATION CONFIGURATION
# =====================================
MAX_MESSAGES = 15  # Trigger summarization when messages exceed this count
MIN_MESSAGES_AFTER_SUMMARY = 3  # Keep system + summary + current after optimization
SUMMARY_MAX_TOKENS = 500  # Maximum tokens for conversation summary
SHOW_MESSAGE_COUNT = True  # Show message count for debugging

available_tools = {
    "get_weather": functions.get_weather,
    "run_command": functions.run_command,
    "start_server": functions.start_server,
    "stop_server": functions.stop_server,
    "list_servers": functions.list_servers,
    "create_directory": functions.create_directory,
    "read_file": functions.read_file,
    "write_file": functions.write_file,
    "delete_file": functions.delete_file,
    "detect_project_type": functions.detect_project_type,
    "check_project_setup": functions.check_project_setup,
    "update_project_context": functions.update_project_context
}


def estimate_token_count(messages):
    """
    Rough estimation of token count for a list of messages
    This is a simple approximation: ~4 characters per token
    """
    total_chars = 0
    for message in messages:
        content = message.get("content", "")
        total_chars += len(content)

    # Rough estimate: 4 characters per token
    estimated_tokens = total_chars // 4
    return estimated_tokens


def summarize_messages(messages_to_summarize):
    """
    Summarize a list of messages to reduce token usage while preserving context
    """
    try:
        # Create a prompt to summarize the conversation
        summary_prompt = """
        Please summarize the following conversation between a user and an AI assistant that helps build applications.
        Focus on:
        1. What projects were created or worked on
        2. Key features implemented
        3. Important decisions made
        4. Current project state
        5. Any ongoing context that affects future actions
        
        Keep the summary concise but comprehensive enough to maintain context for future interactions.
        
        Conversation to summarize:
        """

        # Format messages for summarization
        conversation_text = ""
        for msg in messages_to_summarize:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Skip system messages in summarization
            if role == "system":
                continue

            # For JSON responses, try to extract meaningful content
            if role == "assistant":
                try:
                    parsed = json.loads(content)
                    if parsed.get("step") == "output":
                        conversation_text += f"Assistant: {parsed.get('content', '')}\n"
                    elif parsed.get("step") == "plan":
                        conversation_text += f"Assistant (planning): {parsed.get('content', '')}\n"
                    elif parsed.get("step") == "action":
                        conversation_text += f"Assistant (action): {parsed.get('function', '')} - {parsed.get('input', '')}\n"
                except json.JSONDecodeError:
                    conversation_text += f"Assistant: {content[:200]}...\n"
            else:
                conversation_text += f"User: {content}\n"

        # Get summary from OpenAI
        summary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise summaries of conversations."},
                {"role": "user", "content": summary_prompt + conversation_text}
            ],
            max_tokens=SUMMARY_MAX_TOKENS  # Use configuration constant
        )

        summary = summary_response.choices[0].message.content
        return summary

    except Exception as e:
        print(f"⚠️  Warning: Failed to summarize messages: {e}")
        # Return a basic summary if API call fails
        return "Previous conversation included project setup and development tasks."


def optimize_messages(messages):
    """
    Optimize message array to reduce token usage by summarizing old messages
    """
    if len(messages) <= MAX_MESSAGES:
        return messages

    # Calculate token usage before optimization
    tokens_before = estimate_token_count(messages)

    print(f"🔧 Token optimization: Summarizing {len(messages) - MIN_MESSAGES_AFTER_SUMMARY} messages...")
    print(f"📊 Estimated tokens before: ~{tokens_before}")

    # Keep system message (index 0) and current message (last one)
    system_message = messages[0]
    current_message = messages[-1]

    # Messages to summarize (everything except system and current)
    messages_to_summarize = messages[1:-1]

    # Create summary
    summary = summarize_messages(messages_to_summarize)

    # Create new optimized message array
    optimized_messages = [
        system_message,
        {"role": "assistant", "content": f"[CONVERSATION SUMMARY]: {summary}"},
        current_message
    ]

    # Calculate token usage after optimization
    tokens_after = estimate_token_count(optimized_messages)
    tokens_saved = tokens_before - tokens_after
    savings_percentage = (tokens_saved / tokens_before) * 100 if tokens_before > 0 else 0

    print(f"✅ Optimization complete: {len(messages)} → {len(optimized_messages)} messages")
    print(f"💰 Token savings: ~{tokens_saved} tokens ({savings_percentage:.1f}% reduction)")
    print(f"📊 Estimated tokens after: ~{tokens_after}")

    return optimized_messages



def main():
    messages = [
        {"role": "system", "content": system_prompt.SYSTEM_PROMPT},
    ]

    print("🚀 Welcome to the Enhanced React AI Assistant!")
    print("💡 I can help you create new React projects or work with existing ones.")
    print("🔄 After completing any task, I'll ask if you want to make changes - we can keep improving your project together!")
    print(f"⚡ Token optimization enabled: Auto-summarize when > {MAX_MESSAGES} messages")
    print("=" * 70)

    choice = input("\nEnter existing project path or describe what you want to do: ").strip()

    # If user enters a path, assume they want to start an existing project
    if choice.startswith("./") or choice.startswith("/") or os.path.exists(choice):
        messages.append({"role": "user", "content": f"Start the development server for the existing project at {choice}"})
    else:
        # Otherwise, treat as a new request
        messages.append({"role": "user", "content": choice})

    try:
        while True:
            # Optimize messages to reduce token usage
            # messages = optimize_messages(messages)

            # Debug: Show current message count if enabled
            if SHOW_MESSAGE_COUNT:
                print(f"📊 Current message count: {len(messages)}")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=messages
            )
            parsed_response = json.loads(response.choices[0].message.content)
            messages.append({"role": "assistant", "content": response.choices[0].message.content})

            if parsed_response['step'] == 'plan' or parsed_response['step'] == 'observe':
                print(f"🧠 {parsed_response.get('step').upper()}: {parsed_response.get('content')}")
                continue

            if parsed_response['step'] == 'action':
                fun_name = parsed_response.get('function')
                inp = parsed_response.get('input')
                print("\n⚡ ACTION")
                print(f"   ├─ Function: {fun_name}")
                print(f"   └─ Input   : {json.dumps(inp, indent=2) if isinstance(inp, dict) else inp}")

                if fun_name in available_tools:
                    result = available_tools[fun_name](inp)
                    messages.append({"role": "user", "content": json.dumps({"step": "observe", "content": result})})
                    print(f"✅ RESULT: {result}")
                else:
                    error_msg = f"Function '{fun_name}' not found in available tools"
                    messages.append({"role": "user", "content": json.dumps({"step": "observe", "content": error_msg})})
                    print(f"❌ ERROR: {error_msg}")
                continue

            if parsed_response['step'] == 'output':
                print(f"🎯 FINAL OUTPUT: {parsed_response.get('content')}")
                print("\n" + "=" * 70)

                # Add a small delay to ensure all output is flushed
                time.sleep(0.5)

                print("💬 Would you like to make any changes or improvements to the project?")
                print("💡 Examples: 'Add dark mode', 'Change colors', 'Add new feature', etc.")

                try:
                    # Flush stdout to ensure prompt appears
                    import sys
                    sys.stdout.flush()

                    # Use a more reliable input method
                    user_input = input("\n👤 Your response (or 'quit'/'exit'/'done' to finish): ").strip()

                except (EOFError, KeyboardInterrupt):
                    print("\n👋 Goodbye! Thanks for using the React AI Assistant!")
                    break
                except Exception as input_error:
                    print(f"⚠️  Input error: {input_error}")
                    print("Please try again...")
                    continue

                if not user_input or user_input.lower() in ['quit', 'exit', 'done', 'no', 'n']:
                    print("✨ Great work! Your project is ready to go!")
                    if functions.current_project_context["server_running"]:
                        print(f"🌐 Don't forget - your development server is still running!")
                        print(f"📂 Project location: {functions.current_project_context.get('project_path', 'Current directory')}")
                    print("👋 Goodbye! Thanks for using the React AI Assistant!")
                    break
                else:
                    # Continue the conversation with the user's new request
                    messages.append({"role": "user", "content": user_input})
                    print("\n" + "=" * 70)
                    print("🔄 Processing your request...")
                    continue

            # Optimize messages for token usage
            # messages = optimize_messages(messages)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
        if functions.current_project_context["server_running"]:
            print("🔌 Stopping development server...")
        functions.cleanup_processes()
        print("👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        functions.cleanup_processes()


if __name__ == "__main__":
    main()
