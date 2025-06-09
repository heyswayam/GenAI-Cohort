from dotenv import load_dotenv
from rag_processor import RAGProcessor
import time
import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="RAG Chat Application",
    page_icon="📚",
    layout="wide"
)


load_dotenv()

# Initialize RAG processor


@st.cache_resource
def get_rag_processor():
    return RAGProcessor()


rag = get_rag_processor()

# Main title
st.title("📚 RAG Chat Application")
st.markdown("Upload a PDF document and ask questions about its content!")

# Sidebar for file upload and settings
with st.sidebar:
    st.header("📁 Document Upload")

    # Collection name input
    collection_name = st.text_input(
        "Collection Name",
        value="my_documents",
        help="Name for your document collection in the vector database"
    )

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF document to chat about"
    )

    # Upload button
    if uploaded_file and st.button("🚀 Process PDF", type="primary"):
        with st.spinner("Processing PDF..."):
            # Progress bar
            progress_bar = st.progress(0)

            progress_bar.progress(25)
            st.info("📄 Loading PDF...")
            time.sleep(0.5)

            progress_bar.progress(50)
            st.info("✂️ Chunking text...")
            time.sleep(0.5)

            progress_bar.progress(75)
            st.info("🧠 Creating embeddings...")
            time.sleep(0.5)

            progress_bar.progress(90)
            st.info("💾 Storing in vector database...")

            # Process the PDF
            success = rag.process_pdf(uploaded_file, collection_name)

            progress_bar.progress(100)

            if success:
                st.success("✅ PDF processed successfully!")
                st.balloons()
            else:
                st.error("❌ Error processing PDF. Please try again.")

    # Check if collection exists
    if collection_name:
        if rag.collection_exists(collection_name):
            st.success(f"✅ Collection '{collection_name}' is ready!")
        else:
            st.warning(f"⚠️ Collection '{collection_name}' not found. Please upload a PDF first.")

# Main chat interface
st.header("💬 Chat with your Document")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your document..."):
    # Check if collection exists
    if not rag.collection_exists(collection_name):
        st.error("❌ Please upload and process a PDF first!")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching documents..."):
                response = rag.query_documents(prompt, collection_name)
            st.markdown(response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

with col2:
    st.markdown("**Status:** Vector Database Connected")

with col3:
    st.markdown("**Model:** GPT-4o-mini + OpenAI Embeddings")
