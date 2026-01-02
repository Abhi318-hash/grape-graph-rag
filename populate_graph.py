from neo4j import GraphDatabase

# --- CONFIGURATION (Must match your Retriever) ---
# 1. Paste your URI (Make sure it has +ssc)


# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyB9ft4PkcX90h5Sz_sa_a96WSaAr12cgQo"
NEO4J_URI = "neo4j+ssc://a00a356a.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "32jUhBF4eQjhXV4x3RSTyemIIFbvicnRnuiDHR_JXQ0"


# --- DATA INJECTION ---
def add_viticulture_data(tx):
    print("Injecting data...")
    
    # 1. Create Chardonnay -> Powdery Mildew
    tx.run("MERGE (v:Variety {name: 'Chardonnay'}) "
           "MERGE (d:Disease {name: 'Powdery Mildew'}) "
           "MERGE (v)-[:AFFECTS]->(d)")
    
    # 2. Create Powdery Mildew -> Sulfur
    tx.run("MERGE (d:Disease {name: 'Powdery Mildew'}) "
           "MERGE (t:Treatment {name: 'Sulfur Fungicide'}) "
           "MERGE (d)-[:TREATED_BY]->(t)")

    # 3. Create Cabernet -> Downy Mildew
    tx.run("MERGE (v:Variety {name: 'Cabernet Sauvignon'}) "
           "MERGE (d:Disease {name: 'Downy Mildew'}) "
           "MERGE (v)-[:AFFECTS]->(d)")

    # 4. Create Downy Mildew -> Copper
    tx.run("MERGE (d:Disease {name: 'Downy Mildew'}) "
           "MERGE (t:Treatment {name: 'Copper Spray'}) "
           "MERGE (d)-[:TREATED_BY]->(t)")
    
    print("Data injection complete!")

# --- EXECUTION ---
if __name__ == "__main__":
    AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)
    try:
        with GraphDatabase.driver(NEO4J_URI, auth=AUTH) as driver:
            with driver.session() as session:
                session.execute_write(add_viticulture_data)
        print("SUCCESS: Graph populated.")
    except Exception as e:
        print(f"ERROR: {e}")