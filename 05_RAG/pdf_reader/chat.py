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
    collection_name="my_documents",
    url="http://localhost:6333",
    embedding=embedding_model
)

query = input("> ")
results = vector_store.similarity_search(
    query
)
# print(results)

context = "\n\n".join([
    f"Page Content: {res.page_content}\nPage Number: {res.metadata['page_label']}\nFile Location: {res.metadata['source']}\n\n"
    for res in results
])

# print(context)

SYSTEM_PROMPT=f"""
You are a RAG model and is supposed to answer query on the available context retreived from the pdf along with page number , page content.     
You are supposed to answer on the basis of this content and guide the user to the page number to know more
context :
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
