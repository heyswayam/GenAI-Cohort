from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import subprocess
import requests
from pathlib import Path
import shutil
import time


load_dotenv()

client = OpenAI()

# Original weather function (keeping for backwards compatibility)
def get_weather(city):
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."
    return "Something went wrong"

# Enhanced command runner with working directory support
def run_command(params):
    if isinstance(params, str):
        cmd = params
        working_dir = None
    else:
        cmd = params.get('command', params)
        working_dir = params.get('working_directory', None)
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=working_dir,
            timeout=300  # 5 minute timeout
        )
        if result.returncode == 0:
            return f"Command executed successfully. Output: {result.stdout.strip()}"
        else:
            return f"Command failed with error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 5 minutes"
    except Exception as e:
        return f"Error executing command: {str(e)}"

# File Management Functions
def read_file(params):
    try:
        path = params.get('path', params) if isinstance(params, dict) else params
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"File content of {path}:\n{content}"
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(params):
    try:
        path = params['path']
        content = params['content']
        
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File written successfully: {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def append_file(params):
    try:
        path = params['path']
        content = params['content']
        
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Content appended to file: {path}"
    except Exception as e:
        return f"Error appending to file: {str(e)}"

def list_directory(params):
    try:
        path = params.get('path', params) if isinstance(params, dict) else params
        if not path:
            path = '.'
        
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                items.append(f"📁 {item}/")
            else:
                items.append(f"📄 {item}")
        
        return f"Contents of {path}:\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def create_directory(params):
    try:
        path = params.get('path', params) if isinstance(params, dict) else params
        os.makedirs(path, exist_ok=True)
        return f"Directory created: {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

def delete_file(params):
    try:
        path = params.get('path', params) if isinstance(params, dict) else params
        if os.path.isfile(path):
            os.remove(path)
            return f"File deleted: {path}"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Directory deleted: {path}"
        else:
            return f"Path not found: {path}"
    except Exception as e:
        return f"Error deleting: {str(e)}"

# System Command Functions
def check_command_exists(params):
    try:
        command = params.get('command', params) if isinstance(params, dict) else params
        result = shutil.which(command)
        if result:
            return f"Command '{command}' is available at: {result}"
        else:
            return f"Command '{command}' is not available on this system"
    except Exception as e:
        return f"Error checking command: {str(e)}"

# React-Specific Functions
def init_react_project(params):
    try:
        name = params['name']
        template = params.get('template', 'default')
        
        if template == 'vite':
            cmd = f"npm create vite@latest {name} -- --template react"
        elif template == 'typescript':
            cmd = f"npx create-react-app {name} --template typescript"
        else:
            cmd = f"npx create-react-app {name}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            return f"React project '{name}' created successfully with {template} template"
        else:
            return f"Failed to create React project: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "React project creation timed out. This might take longer on slower connections."
    except Exception as e:
        return f"Error creating React project: {str(e)}"

def install_packages(params):
    try:
        packages = params['packages']
        dev = params.get('dev', False)
        working_dir = params.get('working_directory', None)
        
        if isinstance(packages, str):
            packages = [packages]
        
        package_list = ' '.join(packages)
        dev_flag = '--save-dev' if dev else ''
        cmd = f"npm install {package_list} {dev_flag}".strip()
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=working_dir, timeout=300)
        if result.returncode == 0:
            return f"Packages installed successfully: {package_list}"
        else:
            return f"Failed to install packages: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Package installation timed out"
    except Exception as e:
        return f"Error installing packages: {str(e)}"

def start_dev_server(params):
    try:
        port = params.get('port', 3000) if isinstance(params, dict) else 3000
        working_dir = params.get('working_directory', None) if isinstance(params, dict) else None
        
        # Check if server is already running
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return f"Development server already running on port {port}"
        except:
            pass
        
        # Start the server in background
        cmd = "npm start"
        process = subprocess.Popen(cmd, shell=True, cwd=working_dir)
        time.sleep(3)  # Give it a moment to start
        
        return f"Development server starting on port {port}. Process ID: {process.pid}. Check http://localhost:{port}"
    except Exception as e:
        return f"Error starting dev server: {str(e)}"

def build_project(params):
    try:
        working_dir = params.get('working_directory', None) if isinstance(params, dict) else None
        result = subprocess.run("npm run build", shell=True, capture_output=True, text=True, cwd=working_dir, timeout=300)
        if result.returncode == 0:
            return "Project built successfully for production"
        else:
            return f"Build failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Build process timed out"
    except Exception as e:
        return f"Error building project: {str(e)}"

def run_tests(params):
    try:
        watch = params.get('watch', False) if isinstance(params, dict) else False
        working_dir = params.get('working_directory', None) if isinstance(params, dict) else None
        cmd = "npm test" + (" -- --watchAll" if watch else " -- --watchAll=false --passWithNoTests")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=working_dir, timeout=120)
        return f"Test results:\n{result.stdout}"
    except subprocess.TimeoutExpired:
        return "Tests timed out"
    except Exception as e:
        return f"Error running tests: {str(e)}"

# Code Analysis Functions
def analyze_component(params):
    try:
        path = params.get('path', params) if isinstance(params, dict) else params
        
        if not os.path.exists(path):
            return f"Component file not found: {path}"
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic analysis
        analysis = {
            "file_size": len(content),
            "line_count": len(content.split('\n')),
            "has_useState": "useState" in content,
            "has_useEffect": "useEffect" in content,
            "has_props": "props" in content,
            "is_functional": "function " in content or ("const " in content and "=>" in content),
            "imports": [line.strip() for line in content.split('\n') if line.strip().startswith('import')]
        }
        
        return f"Component analysis for {path}:\n{json.dumps(analysis, indent=2)}"
    except Exception as e:
        return f"Error analyzing component: {str(e)}"

def check_dependencies(params):
    try:
        working_dir = params.get('working_directory', '.') if isinstance(params, dict) else '.'
        package_path = os.path.join(working_dir, 'package.json')
        
        if os.path.exists(package_path):
            with open(package_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            result = {
                "dependencies": dependencies,
                "devDependencies": dev_dependencies,
                "total_deps": len(dependencies) + len(dev_dependencies)
            }
            
            return f"Project dependencies:\n{json.dumps(result, indent=2)}"
        else:
            return f"No package.json found in {working_dir}"
    except Exception as e:
        return f"Error checking dependencies: {str(e)}"

def lint_code(params):
    try:
        fix = params.get('fix', False) if isinstance(params, dict) else False
        working_dir = params.get('working_directory', None) if isinstance(params, dict) else None
        cmd = "npx eslint ." + (" --fix" if fix else "")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=working_dir, timeout=120)
        return f"ESLint results:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "ESLint timed out"
    except Exception as e:
        return f"Error running ESLint: {str(e)}"

# Available tools dictionary
available_tools = {
    # Original tools
    "get_weather": get_weather,
    "run_command": run_command,
    
    # File Management
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "list_directory": list_directory,
    "create_directory": create_directory,
    "delete_file": delete_file,
    
    # System Commands
    "check_command_exists": check_command_exists,
    
    # React-Specific
    "init_react_project": init_react_project,
    "install_packages": install_packages,
    "start_dev_server": start_dev_server,
    "build_project": build_project,
    "run_tests": run_tests,
    
    # Code Analysis
    "analyze_component": analyze_component,
    "check_dependencies": check_dependencies,
    "lint_code": lint_code,
}

# Enhanced system prompt
SYSTEM_PROMPT = """
You are an AI React Development Assistant that helps users build, edit, and manage React projects from scratch.

You work in a structured plan → action → observe → continue/output mode, executing steps in a continuous loop until the task is completed.

## CORE RULES:
- Follow strict JSON output format as per schema
- NEVER stop at a single step - continue working through your plan until completion
- After each 'observe' step, decide whether to 'continue' with more actions or provide final 'output'
- When working with React projects, always verify the current project structure before making changes
- Handle errors gracefully and suggest solutions
- Provide clear explanations for each action taken
- ALWAYS complete the entire task in one conversation session

## EXECUTION FLOW:
1. **plan** → Analyze the request and create a complete step-by-step plan
2. **action** → Execute one action from your plan
3. **observe** → Analyze the result of the action
4. **continue** → Decide next action OR move to output
5. **Repeat 2-4** until task is completely finished
6. **output** → Final result when everything is done

## OUTPUT FORMAT:
{
  "step": "plan|action|observe|continue|output",
  "content": "detailed description of what you're doing/planning",
  "function": "function_name_to_call (only for action steps)",
  "input": "input_parameter_for_function (only for action steps)",
  "reasoning": "why this step is necessary",
  "next_action": "what you plan to do next (for continue steps)",
  "progress": "current progress status (e.g., '2/5 steps completed')",
  "completed": false
}

## STEP DEFINITIONS:

### PLAN Step:
- Analyze the user's request thoroughly
- Break down into specific, actionable steps
- Estimate total number of steps needed
- Set "completed": false

### ACTION Step:
- Execute ONE specific action
- Call appropriate function with correct parameters
- Include reasoning for this specific action
- Set "completed": false

### OBSERVE Step:
- Analyze the result of the previous action
- Determine if the action was successful
- Identify any issues or next requirements
- Set "completed": false

### CONTINUE Step:
- Decide what to do next based on observation
- Either plan another action or move to output
- Update progress status
- Set "completed": false
- Include "next_action" field

### OUTPUT Step:
- Only use when the ENTIRE task is completely finished
- Provide final summary and results
- Set "completed": true
- This ends the execution loop

## AVAILABLE TOOLS:

### File Management:
- "read_file": Read contents of a file. Input: {"path": "file/path"}
- "write_file": Create/overwrite a file. Input: {"path": "file/path", "content": "file_content"}
- "append_file": Add content to existing file. Input: {"path": "file/path", "content": "content_to_add"}
- "list_directory": List files/folders in directory. Input: {"path": "directory/path"}
- "create_directory": Create new directory. Input: {"path": "directory/path"}
- "delete_file": Delete a file. Input: {"path": "file/path"}

### System Commands:
- "run_command": Execute system command. Input: {"command": "command_string", "working_directory": "optional/path"}
- "check_command_exists": Verify if a command/tool is installed. Input: {"command": "command_name"}

### React-Specific Helpers:
- "init_react_project": Initialize new React project. Input: {"name": "project_name", "template": "default|typescript|vite"}
- "install_packages": Install npm packages. Input: {"packages": ["package1", "package2"], "dev": false}
- "start_dev_server": Start React development server. Input: {"port": 3000}
- "build_project": Build React project for production. Input: {}
- "run_tests": Execute React tests. Input: {"watch": false}

### Code Analysis:
- "analyze_component": Analyze React component structure. Input: {"path": "component/path"}
- "check_dependencies": Check package.json dependencies. Input: {}
- "lint_code": Run ESLint on project. Input: {"fix": false}

## EXAMPLE COMPLETE WORKFLOW:

**User**: "Create a simple React todo app with Material-UI"

**Step 1**:
{
  "step": "plan",
  "content": "Creating a React todo app with Material-UI requires: 1) Check Node.js/npm availability, 2) Initialize React project, 3) Install Material-UI, 4) Create todo components, 5) Implement todo functionality, 6) Test the application",
  "reasoning": "Breaking down the complete task into manageable steps",
  "progress": "Planning phase - 0/6 steps completed",
  "completed": false
}

**Step 2**:
{
  "step": "action",
  "content": "Checking if Node.js is available on the system",
  "function": "check_command_exists",
  "input": {"command": "node"},
  "reasoning": "Need to verify development environment before proceeding",
  "progress": "1/6 steps - Environment check",
  "completed": false
}

**Step 3**:
{
  "step": "observe",
  "content": "Node.js is available. System is ready for React development.",
  "reasoning": "Environment check successful, can proceed with project creation",
  "progress": "1/6 steps completed",
  "completed": false
}

**Step 4**:
{
  "step": "continue",
  "content": "Environment is ready. Next, I'll initialize the React project.",
  "next_action": "Create new React project named 'todo-app'",
  "reasoning": "Prerequisites met, proceeding with project initialization",
  "progress": "1/6 steps completed",
  "completed": false
}

**Step 5**:
{
  "step": "action",
  "content": "Creating new React project named 'todo-app'",
  "function": "init_react_project",
  "input": {"name": "todo-app", "template": "default"},
  "reasoning": "Setting up the base React application structure",
  "progress": "2/6 steps - Project initialization",
  "completed": false
}

... (continue until all steps are completed)

**Final Step**:
{
  "step": "output",
  "content": "React todo app with Material-UI has been successfully created! The app includes: 1) Basic React structure, 2) Material-UI components installed, 3) Todo functionality with add/remove/toggle features, 4) Responsive design. The development server is running on localhost:3000.",
  "reasoning": "All planned steps completed successfully",
  "progress": "6/6 steps completed",
  "completed": true
}

## CRITICAL RULES:
1. NEVER stop after just one action - always continue until the task is completely finished
2. Always include progress tracking in your responses
3. Use 'continue' step to decide your next move after each observation
4. Only use 'output' when the ENTIRE task is 100% complete
5. If you encounter errors, handle them and continue with alternative approaches
6. Always verify your work before declaring completion

## ERROR HANDLING:
- If a step fails, analyze the error and try alternative approaches
- Continue working toward the goal even if one approach doesn't work
- Include error recovery in your planning
- Never give up until you've exhausted all reasonable options

Remember: You are in a continuous loop until the task is COMPLETELY finished. Keep working through your plan step by step!
"""

def main():
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    
    query = input("🚀 Enter your React development request: ")
    messages.append({"role": "user", "content": query})
    
    step_count = 0
    max_steps = 50  # Safety limit
    
    print("\n" + "="*60)
    print("🔄 STARTING CONTINUOUS EXECUTION LOOP")
    print("="*60)
    
    while step_count < max_steps:
        try:
            step_count += 1
            print(f"\n--- LOOP ITERATION {step_count} ---")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=messages
            )
            
            parsed_response = json.loads(response.choices[0].message.content)
            messages.append({"role": "assistant", "content": response.choices[0].message.content})
            
            # Extract response fields
            step = parsed_response.get('step', 'unknown')
            content = parsed_response.get('content', '')
            reasoning = parsed_response.get('reasoning', '')
            progress = parsed_response.get('progress', '')
            completed = parsed_response.get('completed', False)
            
            # Display step information with enhanced formatting
            step_emoji = {
                'plan': '🧠',
                'action': '🔧',
                'observe': '👁️',
                'continue': '🔄',
                'output': '🎯'
            }
            
            print(f"{step_emoji.get(step, '❓')} {step.upper()}: {content}")
            
            if reasoning:
                print(f"   💭 Reasoning: {reasoning}")
            
            if progress:
                print(f"   📊 Progress: {progress}")
            
            # Handle different step types
            if step == 'plan':
                print("   📋 Planning phase initiated...")
                continue
                
            elif step == 'action':
                fun_name = parsed_response.get('function')
                inp = parsed_response.get('input')
                
                if fun_name in available_tools:
                    print(f"   🛠️  Executing: {fun_name}")
                    print(f"   📥 Input: {str(inp)[:100]}{'...' if len(str(inp)) > 100 else ''}")
                    
                    result = available_tools[fun_name](inp)
                    messages.append({"role": "user", "content": json.dumps({
                        "step": "observe", 
                        "content": result
                    })})
                    
                    print(f"   ✅ Result: {result[:200]}{'...' if len(result) > 200 else ''}")
                else:
                    error_msg = f"Function '{fun_name}' not available. Available: {list(available_tools.keys())}"
                    messages.append({"role": "user", "content": json.dumps({
                        "step": "observe", 
                        "content": error_msg
                    })})
                    print(f"   ❌ Error: {error_msg}")
                continue
                
            elif step == 'observe':
                print("   🔍 Analyzing results...")
                continue
                
            elif step == 'continue':
                next_action = parsed_response.get('next_action', '')
                if next_action:
                    print(f"   ➡️  Next: {next_action}")
                print("   🔄 Continuing execution...")
                continue
                
            elif step == 'output':
                print(f"\n🎉 TASK COMPLETED SUCCESSFULLY!")
                print(f"📋 Final Result: {content}")
                if completed:
                    print("✅ Task marked as completed")
                break
                
            else:
                print(f"   ❓ Unknown step type: {step}")
                continue
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Raw response: {response.choices[0].message.content}")
            break
            
        except KeyboardInterrupt:
            print("\n⏹️  Execution interrupted by user")
            break
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("🔄 Attempting to continue...")
            continue
    
    if step_count >= max_steps:
        print(f"\n⚠️  Maximum steps ({max_steps}) reached. Execution stopped.")
    
    print("\n" + "="*60)
    print(f"🏁 EXECUTION LOOP COMPLETED - Total Steps: {step_count}")
    print("="*60)
    
    # Optional: Show conversation summary
    show_summary = input("\n📋 Show conversation summary? (y/n): ").lower().strip()
    if show_summary == 'y':
        print("\n--- CONVERSATION SUMMARY ---")
        for i, message in enumerate(messages[1:], 1):  # Skip system message
            role = message['role']
            content = message['content'][:100] + '...' if len(message['content']) > 100 else message['content']
            print(f"{i}. {role.upper()}: {content}")

if __name__ == "__main__":
    # Initialize your OpenAI client here
    # client = openai.OpenAI(api_key="your-api-key")
    
    main()