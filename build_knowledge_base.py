import os
import time
import wikipediaapi
import google.generativeai as genai
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") 
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize Wikipedia API
# User-Agent is required by Wikipedia API
wiki = wikipediaapi.Wikipedia(
    user_agent='GrapeMindAI/1.0 (contact@example.com)',
    language='en'
)

# Targeted list of articles to prevent hitting limits
TARGET_ARTICLES = [
    "Powdery mildew",
    "Downy mildew",
    "Phylloxera",
    "Black rot (grape disease)",
    "Botrytis cinerea",
    "Fungicide",
    "Bordeaux mixture",
    "Cabernet Sauvignon",
    "Chardonnay",
]

def fetch_wikipedia_text(title):
    print(f"Fetching Wikipedia article: {title}")
    page = wiki.page(title)
    if not page.exists():
        print(f"Page '{title}' does not exist.")
        return None
    
    # Save to data folder
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", f"{title.replace(' ', '_')}.txt")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(page.text)
        
    print(f"Saved to {file_path}")
    return page.text

def extract_and_inject_graph(text, driver):
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
        response = model.generate_content(prompt)
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
    print("Starting Knowledge Base Builder...")
    AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)
    driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH)
    
    for title in TARGET_ARTICLES:
        text = fetch_wikipedia_text(title)
        if text:
            print("   - Extracting graph relationships via Gemini...")
            extract_and_inject_graph(text, driver)
            
            # Pause to respect API rate limits (15 requests per minute for free tier)
            print("   - Sleeping for 5 seconds to respect API limits...")
            time.sleep(5)
            
    driver.close()
    print("Knowledge Base Build Complete!")
    print("Next step: Run 'python ingest_data.py' to embed the downloaded text into ChromaDB!")

if __name__ == "__main__":
    main()
