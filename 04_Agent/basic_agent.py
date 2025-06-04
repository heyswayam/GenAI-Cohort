from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
import os

load_dotenv()

client = OpenAI()

SYSTEM_PROMPT = """
You are a AI helper, help the user by answering queries

You work on plan, action , observe and output mode

RULE:
- Follow the strict JSON output as per schema.
- Always perform one step at a time and wait for next step

Output Format:
{
"step":"string",
"content":"string",
"function":"name of the function to be called",
"input":"input parameter for the function"
}
Available Tools:
-"get_weather": Takes city name as input argument and returns the temperature of the city
-"run_command": Takes Linux command as a string input, executes it and returns the output

Example:
User:"whats the weather of Tokyo?"
Output:{"step":"plan", "content":"Looks like the user is intrested in finding the temperatue of the city Japan"}
Output:{"step":"plan", "content":"From the available tools, I think I need to call the "get_weather" tool}
Output:{"step":"action", "function":"get_weather","input":"tokyo"}
Output:{"step":"observe","content":"the temperature of Tokyo was found to be 2deg as per the function"}
Output:{"step":"output","content":"the temperature of Tokyo is 2 deg}
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

available_tools = {
    "get_weather": get_weather,
    "run_command": run_comand
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
        model="gpt-4.1-nano",
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
            messages.append({"role": "user", "content":json.dumps({"step": "observe", "content": result})})
            #message can be a dictionary but the message[index].content should be string or array of objects
            #thus you cant keep type numbers or dictionary inside content

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



