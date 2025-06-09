import streamlit as st
import tempfile
import os
from io import StringIO

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

"""
## RAG CHAT APPLICATION

upload the pdf you want to chat about
"""

# uploaded_file = st.file_uploader("Choose a file", type="pdf")

# if uploaded_file:
    # st.write("File uploaded successfully!")

    # # Save uploaded file to temporary location
    # with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
    #     tmp_file.write(uploaded_file.read())
    #     tmp_file_path = tmp_file.name

    # # Now use the file path with PyPDFLoader
    # loader = PyPDFLoader(tmp_file_path)
    # docs = loader.load()

    # # Clean up temporary file
    # os.unlink(tmp_file_path)

    # st.write("chunking.....")
    # # step-2:
    # # Chunking
    # text_splitter = RecursiveCharacterTextSplitter(
    #     # Set a really small chunk size, just to show.
    #     chunk_size=1000,
    #     chunk_overlap=200,
    #     length_function=len,
    #     is_separator_regex=False,
    # )
    # st.write("chunked successfully")
    # splited_doc = text_splitter.split_documents(documents=docs)

    # Vector Embeddings
    # embedding_model = OpenAIEmbeddings(
    #     model="text-embedding-3-small"
    # )
    # st.write("adding to vector DB..")
    # qdrant = QdrantVectorStore.from_documents(
    #     documents=splited_doc,
    #     embedding=embedding_model,
    #     url='http://localhost:6333',
    #     prefer_grpc=True,  # Uses port 6334
    #     collection_name="my_streamlit_app",
    # )
    # st.write("added to vector DB successfully")






query = st.text_input("Enter your querry")
print(query)
if query:
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )
    client = OpenAI()


    vector_store = QdrantVectorStore.from_existing_collection(
        collection_name="my_streamlit_app",
        url="http://localhost:6333",
        embedding=embedding_model
    )
    # query = input("> ")
    st.write("searching in vector DB.....")
    results = vector_store.similarity_search(
        query
    )
    print(results)    

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

    st.write("Feeding data to GPT model...")
    st.write(f"☕️ {gpt_mini()}")