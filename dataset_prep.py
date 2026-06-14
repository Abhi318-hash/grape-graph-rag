import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(override=True)

NEO4J_URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH)

def extract_dataset():
    dataset = []
    print("Fetching Graph Relationships from Neo4j...")
    
    with driver.session() as session:
        # Get Disease -> Treatment
        result = session.run("MATCH (d:Disease)-[:TREATED_BY]->(t:Treatment) RETURN d.name as disease, t.name as treatment")
        for record in result:
            dataset.append({
                "instruction": f"What is the recommended treatment for {record['disease']}?",
                "output": f"The recommended chemical treatment for {record['disease']} is {record['treatment']}."
            })
            
        # Get Variety -> Disease
        result2 = session.run("MATCH (v:Variety)-[:AFFECTS]->(d:Disease) RETURN v.name as variety, d.name as disease")
        for record in result2:
            dataset.append({
                "instruction": f"Which disease commonly affects the {record['variety']} grape variety?",
                "output": f"The {record['variety']} grape variety is highly susceptible to {record['disease']}."
            })

    # Save to JSONL
    with open("agri_dataset.jsonl", "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")
            
    print(f"Successfully created agri_dataset.jsonl with {len(dataset)} training examples!")

if __name__ == "__main__":
    extract_dataset()
