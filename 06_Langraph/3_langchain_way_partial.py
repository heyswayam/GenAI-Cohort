from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

## NOTES
#LLM is invoked by messages
#graph is invoked by state
# we can replace add_messages by simplying concating the messages


# Initialize the chat model
llm = init_chat_model(model_provider="openai", model="gpt-4.1")
## note : 
# When invoking a chat model with a string as input, LangChain will automatically convert the string into a HumanMessage object. This is mostly useful for quick testing.
# print(llm.invoke("Hello, how are you?"))


# Define the state with regular fields like in 1_graph_single.py
# but add messages with add_messages annotation
class State(BaseModel):
    query: str
    llm_result: str | None
    messages: list = []

# Create the graph builder
graph_builder = StateGraph(State)

SYSTEM_PROMPT = """You are a helpful AI assistant"""

def chatbot(state: State):
    # Add the system and user messages to the existing messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": state.query}]
    
    # Invoke the LLM with the messages array
    response = llm.invoke(messages)
    
    # Update the state
    state.llm_result = response
    state.messages = messages + [{"role": "assistant", "content": response.content}]

    # or
    # return {"query": state.query, "messages": state.messages, "llm_result": state.llm_result}  
    return state


# Add node and edges as in 1_graph_single.py
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph
graph = graph_builder.compile()

def main():
    user_input = input("You: ")
    state = State(
        query=user_input,
        llm_result=None,
    )
    response = graph.invoke(state)
    print("LLM:", response.get("llm_result"))
    
    # can comment out llm_result from state and extract it this way, since we are already saving the response in messages
    # print("LLM:", response['messages'][-1]['content'])


if __name__ == "__main__":
    main()