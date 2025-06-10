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
        help="Upload a PDF document to chat about",
        key="pdf_uploader"
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
            # Update collection status
            st.session_state.collection_ready = True
        else:
            status_container.error(f"❌ Error processing PDF. Please try again.: {status_container.error}")
            st.session_state.collection_ready = False

    # Check if collection exists

    if rag.collection_exists('my_rag_pdf'):
        pass
    else:
        st.warning(f"⚠️ Collection not found. Please upload a PDF first.")


# Initialize chat history and collection status
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize collection status in session state
if "collection_ready" not in st.session_state:
    st.session_state.collection_ready = rag.collection_exists(collection_name)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input - only show if collection is ready
if uploaded_file:
    if prompt := st.chat_input("Ask a question about your document..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response with streaming
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            with st.spinner("🔍 Searching documents..."):
                # Get streaming response
                response_stream = rag.query_documents(prompt, collection_name, stream=True)

            # Handle streaming response
            try:
                for chunk in response_stream:
                    if hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + " ▌")

                # Final update without cursor
                message_placeholder.markdown(full_response)

            except Exception as e:
                # Fallback to non-streaming if streaming fails
                st.warning("Streaming failed, falling back to regular response...")
                full_response = rag.query_documents(prompt, collection_name, stream=False)
                message_placeholder.markdown(full_response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
else:
    # Show a message when no PDF is uploaded
    st.info("📄 Please upload and process a PDF document using the sidebar (tap the sidebar icon > if you don't see it) to start chatting!")

# Footer
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.collection_ready = False
        if 'pdf_uploader' in st.session_state:
            del st.session_state['pdf_uploader']
        st.rerun()

with col2:
    pass
