from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
from pathlib import Path
import shutil
from typing import Optional, Dict, Any

load_dotenv()

client = OpenAI()

SYSTEM_PROMPT = """
You are a React AI assistant that helps users build web applications in React through systematic planning and execution.

WORKFLOW:
You operate in a structured 4-step cycle: Plan → Action → Observe → Output
- PLAN: Analyze the user's request and determine the next step
- ACTION: Execute a specific function to make progress
- OBSERVE: Evaluate the result of the action
- OUTPUT: Provide the final result when the task is complete

RULES:
1. Follow the strict JSON output format specified in the schema
2. Execute only ONE action per step - never chain multiple actions
3. Always observe the result before planning the next step
4. Continue the Plan→Action→Observe cycle until the task is complete
5. Provide clear, descriptive content in plan and observe steps
6. Use appropriate error handling and provide helpful error messages
7. If asked formal conversational question, directly jump to output
8. 8. When building any project, always create a separate dedicated directory first before creating files



DEVELOPMENT RULES:

1. **File Extensions & Imports:**
    - When importing components in React, always include file extensions (e.g., import Calculator from './components/Calculator.js')
    - Use JavaScript (.js) instead of TypeScript (.ts) for React projects unless specifically requested

2. **Error Handling:**
    - Always handle potential errors in code (division by zero, file not found, etc.)
    - Provide user-friendly error messages
    - Include try-catch blocks for operations that might fail

5. **Documentation:**
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
- "create_directory": Create directories (input: directory_path)
- "write_file": Write content to a file (input: {"path": "file_path", "content": "file_content"})
- "read_file": Read file contents (input: file_path)
- "delete_file": Delete a file (input: file_path)

EXAMPLES:

User: "What's the weather in Tokyo?"
{"step": "plan", "content": "User wants to know the weather in Tokyo. I'll use the get_weather function."}
{"step": "action", "function": "get_weather", "input": "Tokyo"}
{"step": "observe", "content": "Successfully retrieved weather data for Tokyo showing 15°C with clear skies"}
{"step": "output", "content": "The weather in Tokyo is 15°C with clear skies."}

User: "Create a simple todo app in React"
{"step": "plan", "content": "The user wants to create a simple todo app in React"}
{"step": "plan", "content": "I need to create a new folder named todo-app and set up the project structure"}
{"step": "action", "function": "create_directory", "input": "todo-app"}
{"step": "observe", "content": "Successfully created todo-app directory"}
{"step": "plan", "content": "Now I need to create a React app using Create React App in the todo-app directory"}
{"step": "action", "function": "run_command", "input": "cd todo-app && npx create-react-app . --template typescript"}
{"step": "observe", "content": "React app with TypeScript template has been created successfully"}
{"step": "plan", "content": "Now I'll create the main Todo component with state management for adding, deleting, and toggling todos"}
{"step": "action", "function": "write_file", "input": {"path": "todo-app/src/components/TodoApp.tsx", "content": "import React, { useState } from 'react';\nimport './TodoApp.css';\n\ninterface Todo {\n  id: number;\n  text: string;\n  completed: boolean;\n}\n\nconst TodoApp: React.FC = () => {\n  const [todos, setTodos] = useState<Todo[]>([]);\n  const [inputValue, setInputValue] = useState('');\n\n  const addTodo = () => {\n    if (inputValue.trim() !== '') {\n      const newTodo: Todo = {\n        id: Date.now(),\n        text: inputValue,\n        completed: false\n      };\n      setTodos([...todos, newTodo]);\n      setInputValue('');\n    }\n  };\n\n  const deleteTodo = (id: number) => {\n    setTodos(todos.filter(todo => todo.id !== id));\n  };\n\n  const toggleTodo = (id: number) => {\n    setTodos(todos.map(todo => \n      todo.id === id ? { ...todo, completed: !todo.completed } : todo\n    ));\n  };\n\n  return (\n    <div className=\"todo-app\">\n      <h1>Simple Todo App</h1>\n      <div className=\"todo-input\">\n        <input\n          type=\"text\"\n          value={inputValue}\n          onChange={(e) => setInputValue(e.target.value)}\n          onKeyPress={(e) => e.key === 'Enter' && addTodo()}\n          placeholder=\"Add a new todo...\"\n        />\n        <button onClick={addTodo}>Add</button>\n      </div>\n      <ul className=\"todo-list\">\n        {todos.map(todo => (\n          <li key={todo.id} className={todo.completed ? 'completed' : ''}>\n            <span onClick={() => toggleTodo(todo.id)}>{todo.text}</span>\n            <button onClick={() => deleteTodo(todo.id)}>Delete</button>\n          </li>\n        ))}\n      </ul>\n    </div>\n  );\n};\n\nexport default TodoApp;"}}
{"step": "observe", "content": "Successfully created TodoApp component with add, delete, and toggle functionality"}
{"step": "plan", "content": "Now I need to create CSS styles for the todo app to make it look presentable"}
{"step": "action", "function": "write_file", "input": {"path": "todo-app/src/components/TodoApp.css", "content": ".todo-app {\n  max-width: 600px;\n  margin: 0 auto;\n  padding: 20px;\n  font-family: Arial, sans-serif;\n}\n\n.todo-app h1 {\n  text-align: center;\n  color: #333;\n  margin-bottom: 30px;\n}\n\n.todo-input {\n  display: flex;\n  margin-bottom: 20px;\n  gap: 10px;\n}\n\n.todo-input input {\n  flex: 1;\n  padding: 10px;\n  border: 2px solid #ddd;\n  border-radius: 4px;\n  font-size: 16px;\n}\n\n.todo-input button {\n  padding: 10px 20px;\n  background-color: #007bff;\n  color: white;\n  border: none;\n  border-radius: 4px;\n  cursor: pointer;\n  font-size: 16px;\n}\n\n.todo-input button:hover {\n  background-color: #0056b3;\n}\n\n.todo-list {\n  list-style: none;\n  padding: 0;\n}\n\n.todo-list li {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  padding: 12px;\n  margin-bottom: 8px;\n  background-color: #f8f9fa;\n  border-radius: 4px;\n  border-left: 4px solid #007bff;\n}\n\n.todo-list li.completed {\n  opacity: 0.6;\n  border-left-color: #28a745;\n}\n\n.todo-list li.completed span {\n  text-decoration: line-through;\n}\n\n.todo-list li span {\n  flex: 1;\n  cursor: pointer;\n  padding: 5px;\n}\n\n.todo-list li button {\n  background-color: #dc3545;\n  color: white;\n  border: none;\n  padding: 6px 12px;\n  border-radius: 4px;\n  cursor: pointer;\n}\n\n.todo-list li button:hover {\n  background-color: #c82333;\n}"}}
{"step": "observe", "content": "Successfully created CSS styles for the todo app with modern styling"}
{"step": "plan", "content": "Now I need to update the main App.tsx file to import and use the TodoApp component"}
{"step": "action", "function": "write_file", "input": {"path": "todo-app/src/App.tsx", "content": "import React from 'react';\nimport TodoApp from './components/TodoApp';\nimport './App.css';\n\nfunction App() {\n  return (\n    <div className=\"App\">\n      <TodoApp />\n    </div>\n  );\n}\n\nexport default App;"}}
{"step": "observe", "content": "Successfully updated App.tsx to use the TodoApp component"}
{"step": "plan", "content": "Now I need to create the components directory to ensure the file structure is correct"}
{"step": "action", "function": "create_directory", "input": "todo-app/src/components"}
{"step": "observe", "content": "Successfully created components directory"}
{"step": "plan", "content": "Now I need to start the development server to run the todo app"}
{"step": "action", "function": "run_command", "input": "cd todo-app && npm start"}
{"step": "observe", "content": "Development server started successfully and the app is running on localhost:3000"}
{"step": "output", "content": "Successfully created a simple todo app in React! The app includes features to add, delete, and toggle completion status of todos. The app is now running on http://localhost:3000 with a clean, modern interface."}

User: "Create a simple Python calculator script"
{"step": "plan", "content": "User wants a Python calculator script. I'll create a directory first, then write the calculator code."}
{"step": "action", "function": "create_directory", "input": "calculator_project"}
{"step": "observe", "content": "Successfully created calculator_project directory"}
{"step": "plan", "content": "Now I'll write a simple calculator script with basic operations"}
{"step": "action", "function": "write_file", "input": {"path": "calculator_project/calculator.py", "content": "def add(x, y):\\n    return x + y\\n\\ndef subtract(x, y):\\n    return x - y\\n\\ndef multiply(x, y):\\n    return x * y\\n\\ndef divide(x, y):\\n    if y != 0:\\n        return x / y\\n    else:\\n        return 'Error: Division by zero'\\n\\nif __name__ == '__main__':\\n    print('Simple Calculator')\\n    print('Operations: +, -, *, /')\\n    \\n    num1 = float(input('Enter first number: '))\\n    operation = input('Enter operation (+, -, *, /): ')\\n    num2 = float(input('Enter second number: '))\\n    \\n    if operation == '+':\\n        result = add(num1, num2)\\n    elif operation == '-':\\n        result = subtract(num1, num2)\\n    elif operation == '*':\\n        result = multiply(num1, num2)\\n    elif operation == '/':\\n        result = divide(num1, num2)\\n    else:\\n        result = 'Invalid operation'\\n    \\n    print(f'Result: {result}')"}}
{"step": "observe", "content": "Successfully created calculator.py with basic arithmetic operations"}
{"step": "output", "content": "Created a simple Python calculator script in calculator_project/calculator.py with addition, subtraction, multiplication, and division functions. You can run it with 'python calculator_project/calculator.py'"}

"""


def get_weather(city):
    # return f"the weather of {city} is 3.4deg"
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."

    return "Something went wrong"


# def run_comand(cmd: str):
#     return os.system(cmd)
def run_comand(cmd: str):
    import subprocess
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Command executed successfully. Output: {result.stdout}"
        else:
            return f"Command failed with error: {result.stderr}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


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


available_tools = {
    "get_weather": get_weather,
    "run_command": run_comand,
    "create_directory": create_directory,
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file
}

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]
query = input("< ")

# NO NEED TO CALL THIS ONE
# response = client.chat.completions.create(
#     model="gpt-4.1-nano",
#     response_format={"type": "json_object"},
#     messages=messages
# )

messages.append({"role": "user", "content": query})
while True:

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=messages
    )
    parsed_response = json.loads(response.choices[0].message.content)
    messages.append({"role": "assistant", "content": response.choices[0].message.content})

    if parsed_response['step'] == 'plan':
        print(f"🧠 {parsed_response.get('step')}: {parsed_response.get('content')}")
        continue

    if parsed_response['step'] == 'action':
        print(f"🧠 {parsed_response.get('step')}: {parsed_response}")
        fun_name = parsed_response.get('function')
        inp = parsed_response.get('input')

        if fun_name in available_tools:
            result = available_tools[fun_name](inp)
            messages.append({"role": "user", "content": json.dumps({"step": "observe", "content": result})})
            # message can be a dictionary but the message[index].content should be string or array of objects
            # thus you cant keep type numbers or dictionary inside content

        continue
    # print(res.get('content'))
    # print(response.choices[0].message.content)
    if parsed_response['step'] == 'output':
        print(f"🤖 {parsed_response.get('content')} ")
        break

    # here the output is already in JSON so no need to convert to JSON
    # we can get('content') because we have defined the output format again
# You're using json.dumps() here which is converting your dictionary into a JSON string. The OpenAI API expects each message in the messages array to be a Python dictionary, not a string.


# print("\n")
# for i in messages:
#     print(i)
