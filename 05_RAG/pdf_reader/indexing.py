from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
#step-1: pdf to text
# It breaks down the pdf page by page into an array. Each array index consists one page
file_path = "./nodejs.pdf"
loader = PyPDFLoader(file_path)
docs = loader.load()

#step-2:
# Chunking
text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)
splited_doc = text_splitter.split_documents(documents=docs)

# Vector Embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

qdrant = QdrantVectorStore.from_documents(
    documents = splited_doc,
    embedding = embedding_model,
    url='http://localhost:6333',
    prefer_grpc=True,  # Uses port 6334
    collection_name="my_documents",
)