import atexit
import json
import requests
from pathlib import Path
import shutil
import subprocess
import time
import os
from typing import Optional, Dict, Any

# Global dictionary to track running processes (simplified)
running_processes = {}

# Global variable to track current project context
current_project_context = {
    "project_path": None,
    "project_type": None,
    "server_running": False,
    "server_name": None,
    "project_files": []
}


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
    global running_processes, current_project_context
    original_dir = os.getcwd()

    try:
        directory = params.get('directory', '.')
        command = params.get('command', 'npm start')
        server_name = params.get('name', f"server_{len(running_processes) + 1}")

        # Kill all existing node processes first to prevent conflicts
        try:
            subprocess.run('pkill -f node', shell=True, capture_output=True)
            print("Killed all existing node processes")
        except Exception:
            pass  # Continue even if pkill fails

        # Change to the specified directory
        if directory != '.':
            if not os.path.exists(directory):
                return f"Error: Directory {directory} does not exist"
            os.chdir(directory)

        # Check if package.json exists
        if not os.path.exists('package.json'):
            return f"Error: No package.json found in {directory}"

        # Better process handling - redirect all outputs to prevent hanging
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )

            # Store the process information
            running_processes[server_name] = {
                'process': process,
                'command': command,
                'directory': os.path.abspath(directory),
                'start_time': time.time()
            }

            # Update project context
            current_project_context.update({
                "server_running": True,
                "server_name": server_name
            })

            # Change back to original directory
            os.chdir(original_dir)

            # Give the server time to start
            if 'npm run dev' in command or 'yarn dev' in command:
                time.sleep(4)  # Vite needs more time to start
            else:
                time.sleep(3)

            # Check if process is still running
            if process.poll() is None:
                # Always return localhost:5173 for development servers
                return f"Development server '{server_name}' started successfully! PID: {process.pid}. Check http://localhost:5173"
            else:
                return f"Server failed to start. Process exited with code: {process.returncode}"

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

        # Update project context with new file
        if current_project_context["project_path"] and file_path.startswith(current_project_context["project_path"]):
            if file_path not in current_project_context["project_files"]:
                current_project_context["project_files"].append(file_path)

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
            # Remove from project context
            if file_path in current_project_context["project_files"]:
                current_project_context["project_files"].remove(file_path)
            return f"Successfully deleted file: {file_path}"
        elif path.is_dir():
            shutil.rmtree(file_path)
            return f"Successfully deleted directory: {file_path}"
        else:
            return f"Error: {file_path} does not exist"
    except Exception as e:
        return f"Error deleting {file_path}: {str(e)}"


def update_project_context(params: Dict[str, str]) -> str:
    """Update the current project context"""
    global current_project_context

    try:
        if 'project_path' in params:
            current_project_context['project_path'] = params['project_path']
        if 'project_type' in params:
            current_project_context['project_type'] = params['project_type']
        if 'server_info' in params:
            current_project_context['server_info'] = params['server_info']

        return f"Project context updated: {current_project_context}"
    except Exception as e:
        return f"Error updating project context: {str(e)}"


def cleanup_processes():
    """Clean up all running processes on exit"""
    try:
        subprocess.run('pkill -f node', shell=True, capture_output=True)
        print("Cleaned up all node processes")
    except Exception:
        pass


# Register cleanup function
atexit.register(cleanup_processes)


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
