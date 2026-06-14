import chromadb
import google.generativeai as genai
import os
from pypdf import PdfReader
from dotenv import load_dotenv

# Load API Keys
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 1. Initialize ChromaDB (Persistent)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("grape_docs")

def ingest_files(folder_path):
    print(f"Scanning folder: {folder_path}...")
    
    if not os.path.exists(folder_path):
        print("Error: 'data' folder not found. Please create it and add files.")
        return

    count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf") or filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            
            # Extract Text
            try:
                text = ""
                if filename.endswith(".pdf"):
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                elif filename.endswith(".txt"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                
                # Basic chunking (splitting text into smaller pieces)
                # Ideally, you split by paragraphs, but 1000 chars is good for a start
                chunk_size = 1000
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                
                # Add chunks to Vector DB
                for i, chunk in enumerate(chunks):
                    collection.add(
                        documents=[chunk],
                        ids=[f"{filename}_chunk_{i}"],
                        metadatas=[{"source": filename}]
                    )
                
                print(f"Ingested: {filename} ({len(chunks)} chunks)")
                count += 1
            except Exception as e:
                print(f"Failed to read {filename}: {e}")

    print(f"Success! Processed {count} files.")

# Run the ingestion
if __name__ == "__main__":
    ingest_files("./data")