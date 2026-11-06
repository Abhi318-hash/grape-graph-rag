import os
import time
import wikipediaapi
from neo4j import GraphDatabase
from dotenv import load_dotenv
from gemini_manager import get_gemini_manager

# Load Environment Variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") 
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Gemini Manager with automatic fallback
gemini_mgr = get_gemini_manager()

# Initialize Wikipedia API
wiki = wikipediaapi.Wikipedia(
    user_agent='GrapeMindAI/1.0 (contact@example.com)',
    language='en'
)

# Comprehensive list of 26 core grape cultivation, disease, variety, and treatment articles
TARGET_ARTICLES = [
    # Diseases & Pathologies
    "Powdery mildew",
    "Downy mildew",
    "Black rot (grape disease)",
    "Botrytis cinerea",
    "Anthracnose",
    "Phylloxera",
    "Pierce's disease",
    "Esca (grape disease)",
    "Crown gall",
    "Grapevine fanleaf virus",
    "Grapevine leafroll-associated virus",
    
    # Treatments & Chemicals
    "Bordeaux mixture",
    "Fungicide",
    "Sulfur",
    "Mancozeb",
    
    # Viticulture & Agronomy Practices
    "Viticulture",
    "Grape",
    "Table grape",
    "Vine training",
    "Irrigation in viticulture",
    "Rootstock",
    
    # Commercial Grape Varieties
    "Sultana (grape)",          # Thompson Seedless - largest grown in India
    "Chardonnay",
    "Cabernet Sauvignon",
    "Merlot",
    "Syrah",
]

def fetch_wikipedia_text(title: str):
    print(f"Fetching Wikipedia article: {title}")
    try:
        page = wiki.page(title)
        if not page.exists():
            print(f"   ⚠️ Page '{title}' does not exist on Wikipedia.")
            return None
        
        # Save to data folder
        os.makedirs("data", exist_ok=True)
        safe_filename = title.replace(' ', '_').replace("'", "")
        file_path = os.path.join("data", f"{safe_filename}.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page.text)
            
        print(f"   ✅ Saved {len(page.text)} characters to {file_path}")
        return page.text
    except Exception as e:
        print(f"   ❌ Error fetching '{title}': {e}")
        return None

def extract_and_inject_graph(text: str, driver):
    if not driver:
        return
        
    prompt = """
    You are an AI extracting agricultural data into a Neo4j Knowledge Graph.
    
    Read the following text and extract ANY relationships matching:
    (Grape Variety)-[:AFFECTS]->(Disease)
    (Disease)-[:TREATED_BY]->(Treatment)
    
    If the text only mentions a Disease and Treatment, just output that.
    If it mentions a Variety and Disease, output that.
    
    Output EXACTLY as Cypher MERGE queries.
    Format examples:
    MERGE (v:Variety {name: 'Chardonnay'}) MERGE (d:Disease {name: 'Powdery Mildew'}) MERGE (v)-[:AFFECTS]->(d)
    MERGE (d:Disease {name: 'Powdery Mildew'}) MERGE (t:Treatment {name: 'Sulfur'}) MERGE (d)-[:TREATED_BY]->(t)
    
    Rules:
    - NO markdown formatting (do not use ```cypher).
    - NO explanations.
    - ONLY output the raw MERGE queries separated by newlines.
    - If no relationships exist, output NOTHING.
    
    Text to analyze:
    """ + text[:15000] # Limit text to prevent massive token usage
    
    try:
        response, used_model, _ = gemini_mgr.generate_content_with_fallback(prompt)
        print(f"   - Extraction performed with model: {used_model}")
        queries = response.text.strip().split('\n')
        
        valid_queries = [q.strip() for q in queries if q.strip().startswith("MERGE")]
        
        if not valid_queries:
            print("   - No valid graph relationships found in this article.")
            return

        with driver.session() as session:
            for query in valid_queries:
                try:
                    session.run(query)
                    print(f"   - Graph Injected: {query[:60]}...")
                except Exception as e:
                    print(f"   - Error running query: {e}")
                    
    except Exception as e:
        print(f"   - Gemini API Error during extraction: {e}")

def main():
    print(f"=== Starting Knowledge Base Builder ({len(TARGET_ARTICLES)} Articles) ===")
    
    driver = None
    if NEO4J_URI and NEO4J_USERNAME and NEO4J_PASSWORD:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            driver.verify_connectivity()
            print("Neo4j Knowledge Graph Connected ✅")
        except Exception as e:
            print(f"Neo4j notice: Database offline or paused ({e}). Proceeding to download articles for ChromaDB vector store.")
            driver = None

    downloaded_count = 0
    for idx, title in enumerate(TARGET_ARTICLES, 1):
        print(f"\n[{idx}/{len(TARGET_ARTICLES)}] Processing: {title}")
        text = fetch_wikipedia_text(title)
        if text:
            downloaded_count += 1
            if driver:
                print("   - Extracting graph relationships via Gemini...")
                extract_and_inject_graph(text, driver)
                # Sleep to respect rate limits
                time.sleep(3)
                
    if driver:
        driver.close()
        
    print(f"\n🎉 Knowledge Base Build Complete! Downloaded {downloaded_count} articles to ./data/")
    print("Next step: Run 'python ingest_data.py' to embed the downloaded articles into ChromaDB!")

if __name__ == "__main__":
    main()
