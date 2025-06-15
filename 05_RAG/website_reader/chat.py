from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

vector_store = QdrantVectorStore.from_existing_collection(
    collection_name="chai_docs_youtube",
    url="http://localhost:6333",
    embedding=embedding_model
)
# Display welcome message
print("="*50)
print("🌟 Welcome to the Chai Docs Assistant! 🌟")
print("This tool helps you get answers about Chai docs using AI.")
print("Ask any question about Chai documentation and get accurate answers")
print("with references to the source materials.")
print("Currently the documentation contains: HTML, Git, C++, Django, SQL, DevOps")
print("="*50)
print("Enter your question below:")
query = input("> ")
results = vector_store.similarity_search(
    query
)
# print(results)
context = "\n\n".join([
    f"{idx+1}\nPage Title: {res.metadata['title']}\nPage Content: {res.page_content}\nSource Link: {res.metadata['link']}\n\n"
    for idx, res in enumerate(results)
])

# print(context)

SYSTEM_PROMPT = f"""
You are an AI website assistant using Retrieval-Augmented Generation (RAG) to answer user queries about technical documentation.

Instructions:
- Use the provided context as your primary and authoritative source of information.
- Answer questions directly from the context whenever possible.
- You may lightly supplement with relevant technical knowledge only when necessary to clarify concepts.
- When referencing information, always cite the source using "Source: [Page Title] ([Source Link])"
- If the question cannot be answered from the context, acknowledge this clearly.
- Be concise and specific in your answers.
- Format code snippets with proper syntax highlighting.

Context:
{context}
"""

def gpt_mini():
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{'role':"system",'content':SYSTEM_PROMPT},
                  {'role':"user",'content':query}]
    )
    return response.choices[0].message.content


print(f"☕️ {gpt_mini()}")
