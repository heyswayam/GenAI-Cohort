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


def main():
    messages = [
        {"role": "system", "content": system_prompt.SYSTEM_PROMPT},
    ]

    print("🚀 Welcome to the Enhanced React AI Assistant!")
    print("💡 I can help you create new React projects or work with existing ones.")
    print("🔄 After completing any task, I'll ask if you want to make changes - we can keep improving your project together!")
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
