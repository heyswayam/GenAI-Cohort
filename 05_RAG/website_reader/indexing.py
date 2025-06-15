import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore


def scrape_chai_docs(urls):
    docs = []

    for i, url in enumerate(urls):
        print(f"Scraping {i+1}/{len(urls)}: {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer"]):
                element.extract()

            # Extract text content
            content = soup.get_text(separator=' ', strip=True)
            content = ' '.join(content.split())  # Clean whitespace

            # Create document
            # Extract custom title from URL
            try:
                # Example: https://chaidocs.vercel.app/youtube/chai-aur-git/diff-stash-tags/
                parts = url.strip('/').split('/')
                # Find the segment after 'youtube'
                youtube_idx = parts.index('youtube')
                course = parts[youtube_idx + 1]  # e.g., 'chai-aur-git'
                lesson = parts[youtube_idx + 2]  # e.g., 'diff-stash-tags'
                # Format course and lesson
                course_title = course.replace('chai-aur-', '').replace('-', ' ').strip()
                lesson_title = lesson.replace('-', ' ').strip()
                custom_title = f"{course_title} - {lesson_title}"
            except Exception:
                custom_title = soup.title.string if soup.title else ""

            doc = Document(
                page_content=content,
                metadata={
                    "link": url,
                    "title": custom_title,
                }
            )

            docs.append(doc)

        except Exception as e:
            print(f"Error scraping {url}: {e}")

        time.sleep(0.5)  # Be nice to the server

    return docs


# Your URLs
urls = [
    'https://chaidocs.vercel.app/youtube/chai-aur-html/introduction/',
    'https://chaidocs.vercel.app/youtube/chai-aur-html/emmit-crash-course/',
    'https://chaidocs.vercel.app/youtube/chai-aur-html/html-tags/',
    'https://chaidocs.vercel.app/youtube/chai-aur-git/welcome/',
    'https://chaidocs.vercel.app/youtube/chai-aur-git/introduction/',
    'https://chaidocs.vercel.app/youtube/chai-aur-git/terminology/',
    'https://chaidocs.vercel.app/youtube/chai-aur-git/behind-the-scenes/',
    'https://chaidocs.vercel.app/youtube/chai-aur-git/branches/',
    'https://chaidocs.vercel.app/youtube/chai-aur-git/diff-stash-tags/',
    'https://chaidocs.vercel.app/youtube/chai-aur-git/managing-history/',
    'https://chaidocs.vercel.app/youtube/chai-aur-git/github/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/welcome/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/introduction/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/hello-world/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/variables-and-constants/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/data-types/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/operators/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/control-flow/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/loops/',
    'https://chaidocs.vercel.app/youtube/chai-aur-c/functions/',
    'https://chaidocs.vercel.app/youtube/chai-aur-django/welcome/',
    'https://chaidocs.vercel.app/youtube/chai-aur-django/getting-started/',
    'https://chaidocs.vercel.app/youtube/chai-aur-django/jinja-templates/',
    'https://chaidocs.vercel.app/youtube/chai-aur-django/tailwind/',
    'https://chaidocs.vercel.app/youtube/chai-aur-django/models/',
    'https://chaidocs.vercel.app/youtube/chai-aur-django/relationships-and-forms/',
    'https://chaidocs.vercel.app/youtube/chai-aur-sql/welcome/',
    'https://chaidocs.vercel.app/youtube/chai-aur-sql/introduction/',
    'https://chaidocs.vercel.app/youtube/chai-aur-sql/postgres/',
    'https://chaidocs.vercel.app/youtube/chai-aur-sql/normalization/',
    'https://chaidocs.vercel.app/youtube/chai-aur-sql/database-design-exercise/',
    'https://chaidocs.vercel.app/youtube/chai-aur-sql/joins-and-keys/',
    'https://chaidocs.vercel.app/youtube/chai-aur-sql/joins-exercise/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/welcome/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/setup-vpc/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/setup-nginx/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/nginx-rate-limiting/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/nginx-ssl-setup/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/node-nginx-vps/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/postgresql-docker/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/postgresql-vps/',
    'https://chaidocs.vercel.app/youtube/chai-aur-devops/node-logger/'
]

# Scrape all URLs
docs = scrape_chai_docs(urls)
print(f"Scraped {len(docs)} documents")


# print(docs[4])
# print(docs[5])

#step-2:
# Chunking
print("chunking.....")
text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)
splited_doc = text_splitter.split_documents(documents=docs)
print("Vector Embeddings...")

# Vector Embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

qdrant = QdrantVectorStore.from_documents(
    documents = splited_doc,
    embedding = embedding_model,
    url='http://localhost:6333',
    prefer_grpc=True,  # Uses port 6334
    collection_name="chai_docs_youtube",
)