import atexit
from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
from pathlib import Path
import shutil
import subprocess
import threading
import time
import signal
import os
from typing import Optional, Dict, Any

load_dotenv()

client = OpenAI()

# Global dictionary to track running processes
running_processes = {}


SYSTEM_PROMPT = """
You are a React AI assistant that helps users build web applications in React through systematic planning and execution.

WORKFLOW:
You operate in a structured 4-step cycle: Plan → Action → Observe → Output
- PLAN: Analyze the user's request and determine the next step
- ACTION: Execute a specific function to make progress
- OBSERVE: Evaluate the result of the action
- OUTPUT: Provide the final result when the task is complete

EXISTING PROJECT HANDLING:
When asked to work with existing projects:
1. First check if the directory exists using run_command with "ls" or check directory structure
2. Navigate to the project directory
3. Check if package.json exists and dependencies are installed
4. If dependencies missing, run "npm install" first
5. Start the appropriate development server based on project type:
   - For Vite projects: use "npm run dev" 
   - For Create React App: use "npm start"
6. For project analysis, read key files like package.json, src/App.jsx, etc.

PROJECT TYPE DETECTION:
- Check package.json for "vite" dependency = Vite project
- Check for "react-scripts" dependency = Create React App
- Default port for Vite: 5173
- Default port for CRA: 3000

RULES:
1. Follow the strict JSON output format specified in the schema
2. Execute only ONE action per step - never chain multiple actions
3. Always observe the result before planning the next step
4. Continue the Plan→Action→Observe cycle until the task is complete
5. Provide clear, descriptive content in plan and observe steps
6. Use appropriate error handling and provide helpful error messages
7. If asked formal conversational question, directly jump to output

DEVELOPMENT RULES:

1. **Project Initialization:**
    - Always use: `yes | npm create vite@latest {project_name} -- --template react` for JavaScript projects
    - Use `yes | npm create vite@latest {project_name} -- --template react-ts` for TypeScript projects
    - Alternative: `echo "y" | npm create vite@latest {project_name} -- --template react`
    - Use specific templates when requested (react-swc, react-swc-ts, etc.)
    - The `yes |` or `echo "y" |` prefix automatically answers "yes" to prompts

2. **File Extensions & Imports:**
    - When importing components in React, you must always include file extensions (e.g., import Calculator from './components/Calculator.js')

3. **Error Handling:**
    - Always handle potential errors in code (division by zero, file not found, etc.)
    - Provide user-friendly error messages
    - Include try-catch blocks for operations that might fail

4. **Documentation:**
    - Include brief comments explaining complex logic
    - Provide usage instructions in the final output
    - Mention any dependencies or requirements needed to run the project

OUTPUT SCHEMA:
{
    "step": "plan|action|observe|output",
    "content": "descriptive text explaining the step", // omit during action step
    "function": "function_name", // only during action step
    "input": "function_parameter" // only during action step
}

AVAILABLE TOOLS:
- "get_weather": Get weather information for a city (input: city_name)
- "run_command": Execute system commands (input: command_string)
- "start_server": Start a development server in background (input: {"directory": "path", "command": "npm start"})
- "stop_server": Stop a running server (input: server_name)
- "list_servers": List all running servers (input: null)
- "write_file": Write content to a file (input: {"path": "file_path", "content": "file_content"})
- "read_file": Read file contents (input: file_path)
- "delete_file": Delete a file (input: file_path)
- "create_directory": Create a directory (input: directory_path)

EXAMPLES:

User: "What's the weather in Tokyo?"
{"step": "plan", "content": "User wants to know the weather in Tokyo. I'll use the get_weather function."}
{"step": "action", "function": "get_weather", "input": "Tokyo"}
{"step": "observe", "content": "Successfully retrieved weather data for Tokyo showing 15°C with clear skies"}
{"step": "output", "content": "The weather in Tokyo is 15°C with clear skies."}

User: "Create a simple todo app in React"
{"step": "plan", "content": "User wants to create a simple todo app in React. I'll start by initializing a new React project using Vite."}
{"step": "action", "function": "run_command", "input": "yes | npm create vite@latest todo-app -- --template react"}
{"step": "observe", "content": "React app has been created successfully using Vite template"}
{"step": "plan", "content": "Now I need to navigate to the project directory and install dependencies"}
{"step": "action", "function": "run_command", "input": "cd todo-app && npm install"}
{"step": "observe", "content": "Dependencies installed successfully"}
{"step": "plan", "content": "I'll create a components directory to organize the project structure"}
{"step": "action", "function": "create_directory", "input": "todo-app/src/components"}
{"step": "observe", "content": "Components directory created successfully"}
{"step": "plan", "content": "Now I'll create the main TodoApp component with state management for todos"}
{"step": "action", "function": "write_file", "input": {"path": "todo-app/src/components/TodoApp.jsx", "content": "[TodoApp component code with useState for managing todos, add/delete/toggle functionality]"}}
{"step": "observe", "content": "Successfully created TodoApp component with full todo functionality"}
{"step": "plan", "content": "I'll create individual components for better code organization - TodoItem and TodoForm"}
{"step": "action", "function": "write_file", "input": {"path": "todo-app/src/components/TodoItem.jsx", "content": "[TodoItem component for individual todo rendering and actions]"}}
{"step": "observe", "content": "Successfully created TodoItem component"}
{"step": "plan", "content": "Now creating the TodoForm component for adding new todos"}
{"step": "action", "function": "write_file", "input": {"path": "todo-app/src/components/TodoForm.jsx", "content": "[TodoForm component with controlled input and form submission]"}}
{"step": "observe", "content": "Successfully created TodoForm component"}
{"step": "plan", "content": "I'll add CSS styling to make the app visually appealing"}
{"step": "action", "function": "write_file", "input": {"path": "todo-app/src/components/TodoApp.css", "content": "[Modern CSS styles for the todo app with responsive design]"}}
{"step": "observe", "content": "Successfully created CSS styles for the todo app"}
{"step": "plan", "content": "Now I need to update the main App.jsx file to use the TodoApp component"}
{"step": "action", "function": "write_file", "input": {"path": "todo-app/src/App.jsx", "content": "[Updated App.jsx importing and using TodoApp component]"}}
{"step": "observe", "content": "Successfully updated App.jsx to use the TodoApp component"}
{"step": "plan", "content": "Finally, I'll start the development server to run the application"}
{"step": "action", "function": "start_server", "input": {"directory": "todo-app", "command": "npm run dev"}}
{"step": "observe", "content": "Development server started successfully on localhost:5173 (Vite default port)"}
{"step": "output", "content": "Successfully created a complete todo app in React! The app includes:\n\n**Features:**\n- Add new todos\n- Mark todos as complete/incomplete\n- Delete todos\n- Clean, modern UI\n\n**Project Structure:**\n- TodoApp.jsx (main component)\n- TodoItem.jsx (individual todo component)\n- TodoForm.jsx (add todo form)\n- TodoApp.css (styling)\n\n**Running:** The app is now running on http://localhost:5173\n\n**Commands:**\n- `npm run dev` - Start development server\n- `npm run build` - Build for production\n- `npm run preview` - Preview production build"}

User: "Create a TypeScript React calculator app"
{"step": "plan", "content": "User wants a calculator app in React with TypeScript. I'll initialize using the react-ts template."}
{"step": "action", "function": "run_command", "input": "yes | npm create vite@latest calculator-app -- --template react-ts"}
{"step": "observe", "content": "React TypeScript app created successfully using Vite"}
{"step": "plan", "content": "Now I'll install dependencies and set up the project structure"}
{"step": "action", "function": "run_command", "input": "cd calculator-app && npm install"}
{"step": "observe", "content": "Dependencies installed successfully"}
{"step": "plan", "content": "I'll create the calculator component with TypeScript interfaces"}
{"step": "action", "function": "write_file", "input": {"path": "calculator-app/src/components/Calculator.tsx", "content": "[Calculator component with TypeScript types and interfaces]"}}
{"step": "observe", "content": "Successfully created Calculator component with proper TypeScript typing"}
{"step": "output", "content": "Successfully created a TypeScript React calculator app with proper type safety and modern React patterns!"}
"""


def get_weather(city):
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."

    return "Something went wrong"


def run_command(cmd: str):
    """Execute a command and return the output (for non-server commands)"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=40)
        if result.returncode == 0:
            return f"Command executed successfully. Output: {result.stdout}"
        else:
            return f"Command failed with error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 40 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def start_server(params: Dict[str, str]) -> str:
    """Start a development server in the background"""
    global running_processes
    original_dir = os.getcwd()

    try:
        directory = params.get('directory', '.')
        command = params.get('command', 'npm start')
        server_name = params.get('name', f"server_{len(running_processes) + 1}")

        # Change to the specified directory
        if directory != '.':
            if not os.path.exists(directory):
                return f"Error: Directory {directory} does not exist"
            os.chdir(directory)

        # Check if package.json exists
        if not os.path.exists('package.json'):
            return f"Error: No package.json found in {directory}"

        # Simpler process handling that works reliably on macOS
        try:

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Store the process information
            running_processes[server_name] = {
                'process': process,
                'command': command,
                'directory': os.path.abspath(directory),
                'start_time': time.time()
            }

            # Change back to original directory
            os.chdir(original_dir)

            # Give the server time to start
            if 'npm run dev' in command or 'yarn dev' in command:
                time.sleep(3)  # Vite needs time to start
            else:
                time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                if 'npm run dev' in command or 'yarn dev' in command:
                    return f"Development server '{server_name}' started successfully! PID: {process.pid}. Check http://localhost:5173"
                else:
                    return f"Server '{server_name}' started successfully! PID: {process.pid}"
            else:
                # Process died, get error output
                stdout, stderr = process.communicate()
                error_msg = stderr if stderr else stdout
                return f"Server failed to start. Error: {error_msg}"

        except Exception as subprocess_error:
            return f"Error creating subprocess: {str(subprocess_error)}"

    except Exception as e:
        return f"Error starting server: {str(e)}"
    finally:
        # Ensure we always return to original directory
        try:
            os.chdir(original_dir)
        except:
            pass


def stop_server(server_name: str) -> str:
    """Stop a running server"""
    global running_processes

    if server_name not in running_processes:
        return f"Server '{server_name}' not found"

    try:
        process_info = running_processes[server_name]
        process = process_info['process']

        if process.poll() is not None:
            # Process already terminated
            del running_processes[server_name]
            return f"Server '{server_name}' was already stopped"

        # Terminate the process more gracefully
        try:
            process.terminate()

            # Wait for process to terminate
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                process.kill()
                process.wait(timeout=2)

        except Exception as kill_error:
            return f"Error terminating process: {str(kill_error)}"

        del running_processes[server_name]
        return f"Server '{server_name}' stopped successfully"

    except Exception as e:
        return f"Error stopping server '{server_name}': {str(e)}"


def list_servers() -> str:
    """List all running servers"""
    global running_processes

    if not running_processes:
        return "No servers currently running"

    active_servers = []
    inactive_servers = []

    for name, info in list(running_processes.items()):
        process = info['process']
        if process.poll() is None:
            # Process is still running
            runtime = time.time() - info['start_time']
            active_servers.append(f"- {name}: {info['command']} (PID: {process.pid}, Runtime: {runtime:.1f}s, Dir: {info['directory']})")
        else:
            # Process has died
            inactive_servers.append(name)

    # Clean up dead processes
    for name in inactive_servers:
        del running_processes[name]

    if active_servers:
        result = "Active servers:\n" + "\n".join(active_servers)
        if inactive_servers:
            result += f"\n\nCleaned up {len(inactive_servers)} inactive server(s)"
        return result
    else:
        return "No active servers (cleaned up inactive processes)"


def create_directory(directory_path: str) -> str:
    """Create a directory (including parent directories if needed)."""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return f"Successfully created directory: {directory_path}"
    except Exception as e:
        return f"Error creating directory {directory_path}: {str(e)}"


def write_file(params: Dict[str, str]) -> str:
    """Write content to a file."""
    try:
        file_path = params.get('path')
        content = params.get('content', '')

        if not file_path:
            return "Error: file path is required"

        # Create parent directories if they don't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote content to {file_path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"


def read_file(file_path: str) -> str:
    """Read content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"File content:\n{content}"
    except FileNotFoundError:
        return f"Error: File {file_path} not found"
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"


def delete_file(file_path: str) -> str:
    """Delete a file or directory."""
    try:
        path = Path(file_path)
        if path.is_file():
            path.unlink()
            return f"Successfully deleted file: {file_path}"
        elif path.is_dir():
            shutil.rmtree(file_path)
            return f"Successfully deleted directory: {file_path}"
        else:
            return f"Error: {file_path} does not exist"
    except Exception as e:
        return f"Error deleting {file_path}: {str(e)}"


def cleanup_processes():
    """Clean up all running processes on exit"""
    global running_processes
    for server_name in list(running_processes.keys()):
        stop_server(server_name)


# Register cleanup function
atexit.register(cleanup_processes)


# To handle existing projects

def detect_project_type(directory: str) -> str:
    """Detect the type of React project"""
    try:
        package_json_path = os.path.join(directory, 'package.json')
        if not os.path.exists(package_json_path):
            return "No package.json found"

        with open(package_json_path, 'r') as f:
            package_data = json.load(f)

        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        all_deps = {**dependencies, **dev_dependencies}

        if 'vite' in all_deps:
            return "Vite React Project"
        elif 'react-scripts' in all_deps:
            return "Create React App"
        elif 'react' in dependencies:
            return "Custom React Project"
        else:
            return "Not a React project"

    except Exception as e:
        return f"Error detecting project type: {str(e)}"


def check_project_setup(directory: str) -> str:
    """Check if project is properly set up"""
    try:
        if not os.path.exists(directory):
            return f"Directory {directory} does not exist"

        package_json = os.path.join(directory, 'package.json')
        node_modules = os.path.join(directory, 'node_modules')

        if not os.path.exists(package_json):
            return "No package.json found - not a Node.js project"

        if not os.path.exists(node_modules):
            return "Dependencies not installed - need to run 'npm install'"

        project_type = detect_project_type(directory)
        return f"Project ready: {project_type}"

    except Exception as e:
        return f"Error checking project: {str(e)}"


available_tools = {
    "get_weather": get_weather,
    "run_command": run_command,
    "start_server": start_server,
    "stop_server": stop_server,
    "list_servers": list_servers,
    "create_directory": create_directory,
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file,
    "detect_project_type": detect_project_type,
    "check_project_setup": check_project_setup
}


def main():
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    choice = input("\nEnter existing project path or describe what you want to do: ").strip()

    # If user enters a path, assume they want to start an existing project
    if choice.startswith("./"):
        messages.append({"role": "user", "content": f"Start the development server for the existing project at {choice}"})
    else:
        # Otherwise, treat as a new request
        messages.append({"role": "user", "content": choice})

    try:
        while True:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fixed the model name
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
                print("\n" + "=" * 50)
                follow_up = input("💬 Any follow-up questions or changes needed? (or 'quit' to exit): ").strip()
                messages.append({"role": "user", "content": follow_up})
                
                if not follow_up or follow_up.lower() in ['quit', 'exit', 'no', 'n']:
                    print("👋 Goodbye! Thanks for using the React AI Assistant!")
                    break
                else:
                    continue

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        cleanup_processes()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        cleanup_processes()


if __name__ == "__main__":
    main()
