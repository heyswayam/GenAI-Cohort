# rag_processor.py - Handles both indexing and querying functionality

import tempfile
import os
from typing import List, Optional, Callable

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class RAGProcessor:
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.qdrant_url = qdrant_url
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.openai_client = OpenAI()

    def process_pdf(self, uploaded_file, collection_name: str = "my_documents") -> bool:
        """
        Process uploaded PDF file and store in vector database
        """
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name

            # Load PDF
            loader = PyPDFLoader(tmp_file_path)
            docs = loader.load()

            # Clean up temporary file
            os.unlink(tmp_file_path)

            # Chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                is_separator_regex=False,
            )
            split_docs = text_splitter.split_documents(documents=docs)

            # Store in vector database
            QdrantVectorStore.from_documents(
                documents=split_docs,
                embedding=self.embedding_model,
                url=self.qdrant_url,
                collection_name=collection_name,
            )

            return True

        except Exception as e:
            print(f"Error processing PDF: {e}")
            return False

    def query_documents(self, query: str, collection_name: str = "my_documents", num_results: int = 4) -> str:
        """
        Query the vector database and get AI response
        """
        try:
            # Connect to existing collection
            vector_store = QdrantVectorStore.from_existing_collection(
                collection_name=collection_name,
                url=self.qdrant_url,
                embedding=self.embedding_model
            )

            # Search for similar documents
            results = vector_store.similarity_search(query, k=num_results)

            if not results:
                return "No relevant documents found for your query."

            # Format context
            context = "\n\n".join([
                f"Page Content: {res.page_content}\n"
                f"Page Number: {res.metadata.get('page_label', 'Unknown')}\n"
                f"File Location: {res.metadata.get('source', 'Unknown')}"
                for res in results
            ])

            # Create system prompt
            system_prompt = f"""
            You are a RAG (Retrieval-Augmented Generation) model designed to answer queries based on the provided context from PDF documents. 
            
            Instructions:
            - Answer questions based solely on the provided context
            - Include page numbers when referencing specific information
            - If information is not in the context, say so clearly
            - Be concise but comprehensive
            - Guide users to specific page numbers for more details
            
            Context:
            {context}
            """

            # Get AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {'role': "system", 'content': system_prompt},
                    {'role': "user", 'content': query}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error querying documents: {str(e)}"

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists in the vector database
        """
        try:
            vector_store = QdrantVectorStore.from_existing_collection(
                collection_name=collection_name,
                url=self.qdrant_url,
                embedding=self.embedding_model
            )
            return True
        except:
            return False
