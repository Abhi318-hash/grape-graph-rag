from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# CONFIG (Same as before)
NEO4J_URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

def bulk_import(tx):
    # List of (Grape, Disease)
    data = [
        ("Thompson Seedless", "Downy Mildew"),
        ("Thompson Seedless", "Mealybug"),
        ("Bangalore Blue", "Anthracnose"),
        ("Bangalore Blue", "Rust"),
        ("Anab-e-Shahi", "Powdery Mildew"),
        ("Shiraz", "Leaf Roll Virus"),
        ("Merlot", "Botrytis Bunch Rot"),
    ]
    
    # List of (Disease, Treatment)
    treatments = [
        ("Mealybug", "Neem Oil Spray"),
        ("Anthracnose", "Mancozeb Fungicide"),
        ("Rust", "Tridemorph"),
        ("Leaf Roll Virus", "Remove Infected Vines"),
        ("Botrytis Bunch Rot", "Fenhexamid"),
    ]

    print("Injecting Grape Data...")
    for grape, disease in data:
        tx.run("MERGE (g:Variety {name: $g}) MERGE (d:Disease {name: $d}) MERGE (g)-[:AFFECTS]->(d)", g=grape, d=disease)
        
    print("Injecting Treatment Data...")
    for disease, treat in treatments:
        tx.run("MERGE (d:Disease {name: $d}) MERGE (t:Treatment {name: $t}) MERGE (d)-[:TREATED_BY]->(t)", d=disease, t=treat)

with GraphDatabase.driver(NEO4J_URI, auth=AUTH) as driver:
    with driver.session() as session:
        session.execute_write(bulk_import)
        print("✅ Expansion Complete! Your bot is now much smarter.")