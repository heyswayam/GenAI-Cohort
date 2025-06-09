from dotenv import load_dotenv
from rag_processor import RAGProcessor
import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="RAG Chat Application",
    page_icon="📚",
    layout="wide"
)


load_dotenv()

# Initialize RAG processor


rag = RAGProcessor()
collection_name = rag.collection_name

# Main title
st.title("📚 RAG Chat Application")
st.markdown("Upload a PDF document and ask questions about its content!")

# Sidebar for file upload and settings
with st.sidebar:
    st.header("📁 Document Upload")

    # # Collection name input
    # collection_name = st.text_input(
    #     "Collection Name",
    #     value="my_documents",
    #     help="Name for your document collection in the vector database"
    # )

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF document to chat about"
    )

    # Upload button
    if uploaded_file and st.button("🚀 Process PDF", type="primary"):
        # Create progress bar and status containers
        progress_bar = st.progress(0)
        status_container = st.empty()

        # Define progress callback function
        def update_progress(progress: int, message: str):
            progress_bar.progress(progress)
            status_container.info(message)

        # Process the PDF with real-time progress
        success = rag.process_pdf(uploaded_file, progress_callback=update_progress)

        if success:
            status_container.success("✅ PDF processed successfully!")
            st.balloons()
        else:
            status_container.error("❌ Error processing PDF. Please try again.")

    # Check if collection exists

    if rag.collection_exists('my_rag_pdf'):
        pass
    else:
        st.warning(f"⚠️ Collection not found. Please upload a PDF first.")

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
col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()


with col2:
    st.markdown("**Model:** GPT-4o-mini + OpenAI Embeddings")
