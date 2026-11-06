import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import chromadb
from gemini_manager import get_gemini_manager

load_dotenv()

# CONFIG
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") 
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Setup Gemini Model Manager (dynamic fallback)
gemini_mgr = get_gemini_manager()

# Setup ChromaDB (Persistent storage on your D: drive)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("grape_docs")

def hybrid_query(user_query: str):
    # 1. Entity Extraction with automatic fallback
    response, _, _ = gemini_mgr.generate_content_with_fallback(
        f"Extract only the main grape variety or disease name from: {user_query}. Respond with ONLY the name."
    )
    entity = response.text.strip()
    print(f"-> Searching for Entity: {entity}")

    # 2. Graph Retrieval (Structured Facts)
    graph_context = ""
    AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD) 
    
    if NEO4J_URI and NEO4J_USERNAME and NEO4J_PASSWORD:
        try:
            with GraphDatabase.driver(NEO4J_URI, auth=AUTH) as driver:
                with driver.session() as session:
                    result = session.run(
                        "MATCH (n {name: $name})-[:AFFECTS|TREATED_BY*1..2]-(related) RETURN DISTINCT related.name as info",
                        name=entity
                    )
                    graph_context = ", ".join([record["info"] for record in result])
        except Exception as e:
            print(f"Graph lookup notice: {e}")

    # 3. Vector Retrieval (Unstructured Text)
    vector_results = collection.query(query_texts=[user_query], n_results=2)
    
    if vector_results['documents'] and vector_results['documents'][0]:
        text_context = " ".join(vector_results['documents'][0])
    else:
        text_context = "No detailed articles found for this topic."

    # 4. Final Generation (Combining everything with automatic fallback)
    final_prompt = f"""
    Answer the user question using ONLY the following info.
    Graph Facts (from Database): {graph_context}
    Detailed Text (from Articles): {text_context}
    
    Question: {user_query}
    """
    resp, used_model, _ = gemini_mgr.generate_content_with_fallback(final_prompt)
    print(f"Generated using model: {used_model}")
    return resp.text

# --- RUN THE TEST ---
if __name__ == "__main__":
    print("\n--- FINAL ANSWER ---")
    print(hybrid_query("How do I treat diseases affecting Chardonnay?"))
