from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

client = OpenAI()

response = client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small"
)
# response = client.responses.create(
#     model="gpt-4.1",
#     input="Write a one-sentence bedtime story about a unicorn."
# )

print(len(response.data[0].embedding))
