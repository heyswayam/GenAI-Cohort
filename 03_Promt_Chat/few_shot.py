from dotenv import load_dotenv
from openai import OpenAI
import json


load_dotenv()
client = OpenAI()

# Few-shot Prompting
# SYSTEM_PROMPT = """
#     You are an AI expert in Coding. You only know Python and nothing else.
#     You help users in solving there python doubts only and nothing else.
#     Only and Only if user tries to ask something else apart from Python you can just roast them.

#     Examples:
#     User: How to make a Tea?
#     Assistant: Do I look like a chef to you, you piece of crap !!

# """

# Chai Of Thought Prompt
SYSTEM_PROMPT = """
You are an AI expert in Python coding. You ONLY understand Python — no exceptions.

Your job is to help users solve Python-related questions step-by-step using chain-of-thought reasoning.

If the user tries to ask anything outside of Python, respond with a roast in the 'result' step, and do not entertain the query.

Rules:
1. Follow the strict JSON output as per schema.
2. Always perform one step at a time and wait for the next input.
3. Follow this exact step sequence: "analyse", "think", "output", "validate", and finally "result".
4. Always carefully analyse the user query before proceeding.
5. In the final "result" step:
   - You MUST include the code content that was shared in the "output" step.
   - Provide a brief explanation of the logic used.
6. If the user tries to ask something else than Python or even greets, respond with step "result".

Output Format:
{ "step": "string", "content": "string" }

Example:
User: How to add 2 and 3?
Assistant:
{ "step": "analyse", "content": "It looks like the user wants to do a simple arithmetic operation in Python." }
{ "step": "think", "content": "To perform this, I will use the addition operator in Python." }
{ "step": "output", "content": "2 + 3 = 5" }
{ "step": "validate", "content": "Yes, adding 2 and 3 correctly gives 5." }
{ "step": "result", "content": "2 + 3 = 5, calculated using the + operator in Python." }

Example:
User: Write me a program to find factorial of a number in python
Assistant:
{ "step": "analyse", "content": "The user wants a Python program to calculate the factorial of a number." }
{ "step": "think", "content": "I'll use a loop to multiply all numbers from 1 to the input number." }
{ "step": "output", "content": "```python\nnum = int(input('Enter a number: '))\n\ndef factorial(n):\n    result = 1\n    for i in range(1, n + 1):\n        result *= i\n    return result\n\nprint('Factorial:', factorial(num))\n```" }
{ "step": "validate", "content": "This code correctly computes the factorial using iteration." }
{ "step": "result", "content": "This program takes a number as input and calculates its factorial using a loop.\n\nFinal Code:\n```python\nnum = int(input('Enter a number: '))\n\ndef factorial(n):\n    result = 1\n    for i in range(1, n + 1):\n        result *= i\n    return result\n\nprint('Factorial:', factorial(num))\n```" }

"""

# response = client.chat.completions.create(
#     model="gpt-4.1-mini",
#     response_format={"type": "json_object"},
#     messages=[
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": "hey there,My name is Swayam"},
#         {"role": "assistant", "content": "Hey Swayam! I’m here to help you with Python coding questions. What do you need assistance with?"},
#         {"role": "user", "content": "Write me a program to find factorial of a number in python"},
#         {"role": "assistant", "content": json.dumps({'step': 'analyse', 'content': 'The user asks for a program to find the factorial of a number, which involves calculating the product of all positive integers up to that number.'})},
#         {"role": "assistant", "content": json.dumps({'step': 'think', 'content': 'To find the factorial of a number, I can implement a function that multiplies all integers from 1 to that number, either iteratively or recursively.'})},
#         {"role": "assistant", "content": json.dumps({'step': 'output', 'content': "Here's a Python program to find the factorial of a number:\n\n```python\nnum = int(input('Enter a number: '))\n\ndef factorial(n):\n    result = 1\n    for i in range(1, n + 1):\n        result *= i\n    return result\n\nprint('Factorial:', factorial(num))\n```"})},
#         {"role": "assistant", "content": json.dumps({'step': 'validate', 'content': 'The program correctly calculates the factorial of a user-input number using an iterative approach.'})}

#         ]
# )
# print(json.loads(response.choices[0].message.content))


messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
    ]

query = input("> ")
messages.append({"role":"user","content":query})

def gpt_mini(msg):
        response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=msg
        )
        return json.loads(response.choices[0].message.content)
def gpt_nano(msg):
        response = client.chat.completions.create(
        model="gpt-4.1-nano",
        response_format={"type": "json_object"},
        messages=msg
        )   
        return json.loads(response.choices[0].message.content)

response_content = gpt_nano(messages)

while True:
    messages.append({"role":"assistant","content":json.dumps(response_content)})

    # print(f"🧠  {response_content['content']}")
    if response_content['step'] == 'output':
        response_content = gpt_mini(messages)
        continue

    elif response_content['step'] == 'result':
        print(f"🤖 {response_content['content']}")
        break
    else:
        response_content = gpt_nano(messages)
        

# messages.append({"role":"assistant","content":response_content})
