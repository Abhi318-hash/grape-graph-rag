import os
from typing import TypedDict
from langgraph.graph import StateGraph, END

class GraphState(TypedDict):
    question: str
    image: any # PIL Image
    language: str
    model: any # Gemini model
    driver: any # Neo4j driver
    collection: any # ChromaDB collection
    
    extracted_entity: str
    graph_context: str
    vector_context: str
    final_answer: str

def extractor_node(state: GraphState):
    """Agent: Extracts disease/variety entity from text/image"""
    print("🤖 Agent 1 (Extractor) is running...")
    model = state["model"]
    image = state["image"]
    user_query = state["question"]
    
    try:
        if image:
            response = model.generate_content([image, "Analyze this image of a grape leaf/plant. Extract only the main grape disease name or grape variety. Respond with ONLY the name."])
        else:
            response = model.generate_content(f"Extract only the main grape variety or disease name from: {user_query}. Respond with ONLY the name.")
        entity = response.text.strip()
    except Exception as e:
        print(f"Extraction error: {e}")
        entity = "Unknown"
        
    return {"extracted_entity": entity}

def diagnostician_node(state: GraphState):
    """Agent: Queries the Knowledge Graph for relationships"""
    print("🤖 Agent 2 (Diagnostician) is querying Neo4j...")
    driver = state["driver"]
    entity = state["extracted_entity"]
    
    graph_context = "No specific graph data found."
    with driver.session() as session:
        result = session.run(
            "MATCH (n {name: $name})-[:AFFECTS|TREATED_BY*1..2]-(related) RETURN DISTINCT related.name as info",
            name=entity
        )
        data = [record["info"] for record in result]
        if data:
            graph_context = ", ".join(data)
            
    return {"graph_context": graph_context}

def researcher_node(state: GraphState):
    """Agent: Queries Vector Database for detailed manuals"""
    print("🤖 Agent 3 (Researcher) is querying ChromaDB...")
    collection = state["collection"]
    user_query = state["question"]
    entity = state["extracted_entity"]
    
    search_query = user_query if user_query else f"What is the treatment and medicine amount for {entity}?"
    vector_results = collection.query(query_texts=[search_query], n_results=1)
    
    text_context = "No relevant articles found."
    if vector_results['documents'] and vector_results['documents'][0]:
        text_context = vector_results['documents'][0][0]
        
    return {"vector_context": text_context}

def supervisor_node(state: GraphState):
    """Agent: Synthesizes final answer in requested language"""
    print("🤖 Agent 4 (Supervisor) is generating final response...")
    model = state["model"]
    image = state["image"]
    user_query = state["question"]
    graph_context = state["graph_context"]
    text_context = state["vector_context"]
    language = state["language"]
    
    final_prompt = f"""
    You are the Supervisor Agronomist Agent.
    
    INSTRUCTIONS:
    1. Read the Graph Database Facts and the Vector DB Manuals below.
    2. If an image is provided, identify the disease and use the facts to recommend the medicine and dosage.
    3. Output your answer ONLY in {language}.
    
    [GRAPH DATABASE FACTS]
    {graph_context}
    
    [VECTOR DB MANUALS]
    {text_context}
    
    User Question: {user_query if user_query else "Analyze the image and provide treatment."}
    """
    
    content_to_generate = [image, final_prompt] if image else final_prompt
    
    try:
        final_response = model.generate_content(content_to_generate)
        answer = final_response.text
    except Exception as e:
        answer = f"⚠️ I could not generate a response: {e}"
        
    return {"final_answer": answer}

# Build the LangGraph
def build_workflow():
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("diagnostician", diagnostician_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("supervisor", supervisor_node)
    
    # Define edges (Linear pipeline)
    workflow.set_entry_point("extractor")
    workflow.add_edge("extractor", "diagnostician")
    workflow.add_edge("diagnostician", "researcher")
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("supervisor", END)
    
    return workflow.compile()
