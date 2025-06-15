# RAG PDF Chat Application

A Retrieval-Augmented Generation (RAG) application that allows you to upload PDF documents and chat with them using AI.

## Features

-   📚 **PDF Upload & Processing**: Upload PDFs and automatically extract, chunk, and embed the content
-   💬 **Interactive Chat**: Ask questions about your PDF content with AI-powered responses
-   🔍 **Semantic Search**: Find relevant content using vector similarity search
-   📄 **Page References**: Get page numbers and source references in responses
-   🌐 **Web Interface**: Beautiful Streamlit web application
-   💻 **CLI Interface**: Command-line tools for batch processing

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Start Vector Database

```bash
# Start Qdrant vector database using Docker
docker-compose up -d
```

## Usage

### Web Interface (Recommended)

```bash
streamlit run streamlit_web.py
```

Then:

1. Upload a PDF file using the sidebar
2. Wait for processing to complete
3. Start chatting with your document!

### Command Line Interface

#### Index a PDF document:

```bash
python indexing.py path/to/your/document.pdf
```

#### Chat with indexed documents:

```bash
python chat.py
```

## Project Structure

```
pdf_reader/
├── rag_processor.py      # Core RAG functionality
├── streamlit_web.py      # Web interface
├── indexing.py          # CLI indexing script
├── chat.py              # CLI chat interface
├── docker-compose.yml   # Vector database setup
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## How It Works

1. **Document Processing**: PDFs are loaded and split into chunks
2. **Embedding**: Text chunks are converted to vector embeddings using OpenAI
3. **Storage**: Embeddings are stored in Qdrant vector database
4. **Retrieval**: User queries are embedded and matched against document chunks
5. **Generation**: Retrieved context is sent to GPT-4o-mini for response generation

## Configuration

### Chunking Parameters (in `rag_processor.py`)

-   `chunk_size`: 1000 characters
-   `chunk_overlap`: 200 characters

### Models Used

-   **Embeddings**: `text-embedding-3-small` (OpenAI)
-   **LLM**: `gpt-4o-mini` (OpenAI)
-   **Vector DB**: Qdrant

## Troubleshooting

### Vector Database Connection Issues

```bash
# Check if Qdrant is running
docker ps

# Restart if needed
docker-compose down && docker-compose up -d
```

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### OpenAI API Issues

-   Verify your API key in `.env`
-   Check your OpenAI account credits
-   Ensure the models are available in your region

## Features to Add

-   [ ] Support for multiple PDF uploads
-   [ ] Document deletion functionality
-   [ ] Export chat history
-   [ ] Support for other document formats (DOCX, TXT)
-   [ ] Custom embedding models
-   [ ] Response streaming


# How does this work?

Great question! Let me break down how the progress callback mechanism works step by step.

## 1. **Callback Function Concept**

A callback is a function that gets passed to another function as a parameter, and the receiving function can "call back" (execute) that function at specific points.

```python
# Basic callback example
def my_callback(message):
    print(f"Callback called with: {message}")

def do_work(callback_func):
    callback_func("Starting work...")
    # Do some work
    callback_func("Work complete!")

# Usage
do_work(my_callback)
```

## 2. **In Your RAG Application**

### **Step 1: Defining the Callback Type**
```python
# In rag_processor.py
from typing import Optional, Callable

# This means: a function that takes (int, str) and returns None
progress_callback: Optional[Callable[[int, str], None]] = None
```

### **Step 2: The Callback Function (Streamlit Side)**
```python
# In streamlit_web.py
def update_progress(progress: int, message: str):
    progress_bar.progress(progress)      # Update progress bar
    status_container.info(message)       # Update status message
```

### **Step 3: Passing the Callback**
```python
# In streamlit_web.py
success = rag.process_pdf(
    uploaded_file, 
    collection_name, 
    progress_callback=update_progress  # Pass the function itself (no parentheses!)
)
```

### **Step 4: Using the Callback (RAG Processor Side)**
```python
# In rag_processor.py
def process_pdf(self, uploaded_file, collection_name, progress_callback=None):
    # Check if callback was provided
    if progress_callback:
        progress_callback(10, "📄 Saving PDF file...")  # Call the function
    
    # Do some work...
    
    if progress_callback:
        progress_callback(25, "📖 Loading PDF content...")  # Call again
```

## 3. **The Flow Visualization**

```
Streamlit (UI)                    RAGProcessor (Backend)
     |                                  |
     |  1. User clicks "Process PDF"    |
     |                                  |
     |  2. Create progress_bar &        |
     |     status_container             |
     |                                  |
     |  3. Define update_progress()     |
     |     function                     |
     |                                  |
     |  4. Call rag.process_pdf()       |
     |     with callback                |
     |--------------------------------->|
     |                                  |  5. Start processing
     |                                  |
     |<---------------------------------|  6. progress_callback(10, "Saving...")
     |  7. Update UI (progress=10%)     |
     |                                  |
     |<---------------------------------|  8. progress_callback(25, "Loading...")
     |  9. Update UI (progress=25%)     |
     |                                  |
     |<---------------------------------|  10. progress_callback(50, "Chunking...")
     |  11. Update UI (progress=50%)    |
     |                                  |
     |<---------------------------------|  12. progress_callback(75, "Embeddings...")
     |  13. Update UI (progress=75%)    |
     |                                  |
     |<---------------------------------|  14. progress_callback(100, "Complete!")
     |  15. Update UI (progress=100%)   |
     |                                  |
     |<---------------------------------|  16. Return success=True
     |  17. Show balloons & success     |
```

## 4. **Key Benefits**

1. **Separation of Concerns**: 
   - RAGProcessor focuses on PDF processing
   - Streamlit handles UI updates
   - No UI code mixed with business logic

2. **Flexibility**: 
   - Same RAGProcessor can work with different UIs
   - Could use console progress, web progress, etc.

3. **Real-time Updates**: 
   - User sees progress immediately
   - No waiting with blank screen

## 5. **Alternative Without Callback**

Without callbacks, you'd have to do something like:

```python
# Bad approach - mixed concerns
def process_pdf(self, uploaded_file, progress_bar, status_container):
    progress_bar.progress(10)  # UI code in business logic!
    status_container.info("Saving...")
    # This ties RAGProcessor to Streamlit specifically
```

## 6. **The Magic**

The "magic" is that `update_progress` has access to Streamlit's `progress_bar` and `status_container` through **closure** - it "remembers" the variables from where it was defined, even when called from inside RAGProcessor.

```python
# This works because of closure
progress_bar = st.progress(0)        # Created in Streamlit
status_container = st.empty()        # Created in Streamlit

def update_progress(progress, message):
    progress_bar.progress(progress)      # Can access outer variables!
    status_container.info(message)       # Even when called from elsewhere!
```

This is a clean, professional pattern used in many frameworks for handling asynchronous operations with progress updates!