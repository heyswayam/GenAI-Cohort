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
