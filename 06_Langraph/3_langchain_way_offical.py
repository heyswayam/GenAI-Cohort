from typing import Annotated
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage

#note : check these link out https://langchain-ai.github.io/langgraph/tutorials/workflows/?h=systemm#routing
#                            https://python.langchain.com/docs/concepts/messages/#langchain-messages



class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

# Initialize the chat model
llm = init_chat_model("openai:gpt-4.1-mini")  # Or your preferred model
## note : 
# When invoking a chat model with a string as input, LangChain will automatically convert the string into a HumanMessage object. This is mostly useful for quick testing.
# print(llm.invoke("Hello, how are you?"))


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# Add nodes and edges
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph
graph = graph_builder.compile()


def main():
    user_input = input("You: ")

    # Initialize with system message
    initial_state = {
        "messages": [
            SystemMessage(content="You are a helpful AI assistant. Respond in JSON format."),
            HumanMessage(content=user_input)
        ]
    }

    # Invoke the graph with the initial state
    result = graph.invoke(initial_state)

    # Print the response
    print("Assistant:", result["messages"][-1].content)


if __name__ == "__main__":
    main()
