import google.generativeai as genai
import chromadb
import os

from neo4j import GraphDatabase

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyB9ft4PkcX90h5Sz_sa_a96WSaAr12cgQo"
NEO4J_URI = "neo4j+ssc://a00a356a.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "32jUhBF4eQjhXV4x3RSTyemIIFbvicnRnuiDHR_JXQ0"

# Setup Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Setup ChromaDB (Persistent storage on your D: drive)
# This ensures your "Articles" stay saved after you close the script
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("grape_docs")

def hybrid_query(user_query):
    # 1. Entity Extraction
    response = model.generate_content(f"Extract only the main grape variety or disease name from: {user_query}. Respond with ONLY the name.")
    entity = response.text.strip()
    print(f"-> Searching for Entity: {entity}")

    # 2. Graph Retrieval (Structured Facts)
    graph_context = ""
    # FIX: Use the variables defined at the top
    AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD) 
    
    with GraphDatabase.driver(NEO4J_URI, auth=AUTH) as driver:
        with driver.session() as session:
            result = session.run(
                "MATCH (n {name: $name})-[:AFFECTS|TREATED_BY*1..2]-(related) RETURN DISTINCT related.name as info",
                name=entity
            )
            graph_context = ", ".join([record["info"] for record in result])

    # 3. Vector Retrieval (Unstructured Text)
    # n_results=2 means find the 2 best matching sentences from your articles
    vector_results = collection.query(query_texts=[user_query], n_results=2)
    
    # Check if we actually found any articles
    if vector_results['documents'] and vector_results['documents'][0]:
        text_context = " ".join(vector_results['documents'][0])
    else:
        text_context = "No detailed articles found for this topic."

    # 4. Final Generation (Combining everything)
    final_prompt = f"""
    Answer the user question using ONLY the following info.
    Graph Facts (from Database): {graph_context}
    Detailed Text (from Articles): {text_context}
    
    Question: {user_query}
    """
    return model.generate_content(final_prompt).text

# --- RUN THE TEST ---
print("\n--- FINAL ANSWER ---")
print(hybrid_query("How do I treat diseases affecting Chardonnay?"))