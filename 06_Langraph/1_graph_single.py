from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()


class State(BaseModel):
    query: str
    llm_result: str | None


graph_builder = StateGraph(State)


def chatbot(data: State):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{'role': 'user', 'content': data.query}]
    )
    data.llm_result = json.loads(response.choices[0].message.content)
    return data


graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()


def main():
    user = input("< ")
    state = State(
        query=user,
        llm_result=None
    )
    graph_result = graph.invoke(state)
    print(graph_result)


if __name__ == "__main__":
    main()

# Known issues, will take only a single chat,