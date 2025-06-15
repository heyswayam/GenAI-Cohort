from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import json 
load_dotenv()

client = OpenAI()


class State(BaseModel):
    query: str
    llm_result: str | None
    isCoding: bool | None

class ClassifyMessageFormat(BaseModel):
    isCoding:bool

graph_builder = StateGraph(State)


def classifyMessage(data: State):
    print("classifying messages | model = gpt-4.1-mini")
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are an helpful AI assistant. Your job is to classify the following message from user as a coding question or a general question. Answer in boolean and stick to the text_format"},
            {
                "role": "user",
                "content": data.query,
            },
        ],
        text_format=ClassifyMessageFormat,
    )
    data.isCoding = response.output_parsed.isCoding
    return data

def routing(data: State):
    print("routing....")

    if data.isCoding:
        return "codingQuestion"
    return "generalQuestion"

def codingQuestion(data: State):
    print("solving coding question | model = gpt-4.1-mini")
    response = client.responses.create(
    model="gpt-4.1-mini",
    input=[
        {"role": "system", "content": "You are an helpful AI coding assistant."},
        {
            "role": "user",
            "content": data.query,
        },
    ],
    )
    data.llm_result = response.output_text
    return data
tools = [{
    "type": "function",
    "name": "get_weather",
    "description": "Get current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and country e.g. Bogotá, Colombia"
            }
        },
        "required": [
            "location"
        ],
        "additionalProperties": False
    }
}]
import requests

def get_weather(latitude, longitude):
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    return data['current']['temperature_2m']

def generalQuestion(data: State):
    print("solving general question | model = gpt-4.1-nano")

    response = client.responses.create(
    model="gpt-4.1-nano",
    input=[
        {
            "role": "user",
            "content": data.query,
        },
    ],
    tools=tools
    )
    data.llm_result = response.output_text
    # print(json.dumps(response.model_dump()))
    return data

graph_builder.add_node("classifyMessage", classifyMessage)
graph_builder.add_node("generalQuestion", generalQuestion)
graph_builder.add_node("codingQuestion", codingQuestion)
graph_builder.add_node("routing", routing)

graph_builder.add_edge(START, "classifyMessage")
graph_builder.add_conditional_edges("classifyMessage",routing,)
graph_builder.add_edge("generalQuestion", END)
graph_builder.add_edge("codingQuestion", END)

graph = graph_builder.compile()


def main():
    user = input("< ")
    state = State(
        query=user,
        llm_result=None,
        isCoding=None
    )
    graph_result = graph.invoke(state)
    print(graph_result)


if __name__ == "__main__":
    main()

# Known issues, will take only a single chat,