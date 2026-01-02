import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 1. Initialize ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("grape_docs")

# 2. Sample Data (Replace with your actual article text)
articles = [
    {"id": "doc1", "text": "Powdery mildew appears as white, dusty spots on grape leaves. It is often treated with sulfur fungicides during the early growth stages to prevent spread."},
    {"id": "doc2", "text": "Downy mildew thrives in humid conditions and creates oily spots on leaves. Copper-based sprays are the standard organic treatment."}
]

# 3. Add to Collection
for doc in articles:
    collection.add(
        documents=[doc["text"]],
        ids=[doc["id"]]
    )
print("Articles ingested successfully!")