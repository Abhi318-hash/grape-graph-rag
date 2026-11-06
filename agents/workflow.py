import os
from typing import TypedDict, Optional, List, Any
from langgraph.graph import StateGraph, END
from gemini_manager import get_gemini_manager, GeminiModelManager

class GraphState(TypedDict, total=False):
    question: str
    image: Any # PIL Image
    language: str
    model: Any # Legacy Gemini model reference (for backwards compatibility)
    driver: Any # Neo4j driver
    collection: Any # ChromaDB collection
    
    # Model management & failover config
    gemini_manager: Any
    preferred_model: Optional[str]
    auto_fallback: bool
    model_used: str
    fallback_history: List[dict]
    
    # Internal agent memory
    extracted_entity: str
    graph_context: str
    vector_context: str
    final_answer: str

def extractor_node(state: GraphState):
    """Agent: Extracts disease/variety entity from text/image"""
    print("[Agent 1] Extractor is running...")
    manager = state.get("gemini_manager") or get_gemini_manager()
    preferred_model = state.get("preferred_model")
    auto_fallback = state.get("auto_fallback", True)
    image = state.get("image")
    user_query = state.get("question", "")
    
    prompt = [image, "Analyze this image of a grape leaf/plant. Extract only the main grape disease name or grape variety. Respond with ONLY the name."] if image else f"Extract only the main grape variety or disease name from: {user_query}. Respond with ONLY the name."
    
    try:
        response, _, _ = manager.generate_content_with_fallback(
            contents=prompt,
            preferred_model=preferred_model,
            auto_fallback=auto_fallback
        )
        entity = response.text.strip()
    except Exception as e:
        print(f"Extraction error: {e}")
        entity = "Unknown"
        
    return {"extracted_entity": entity}

def diagnostician_node(state: GraphState):
    """Agent: Queries the Knowledge Graph for relationships"""
    print("[Agent 2] Diagnostician is querying Neo4j...")
    driver = state.get("driver")
    entity = state.get("extracted_entity", "Unknown")
    
    graph_context = "No specific graph data found."
    if driver:
        try:
            with driver.session() as session:
                result = session.run(
                    "MATCH (n {name: $name})-[:AFFECTS|TREATED_BY*1..2]-(related) RETURN DISTINCT related.name as info",
                    name=entity
                )
                data = [record["info"] for record in result]
                if data:
                    graph_context = ", ".join(data)
        except Exception as e:
            print(f"Diagnostician error (Neo4j unreachable): {e}")
            graph_context = "Graph database is currently offline or unreachable."
    else:
        graph_context = "Graph database driver not configured."
            
    return {"graph_context": graph_context}

def researcher_node(state: GraphState):
    """Agent: Queries Vector Database for detailed manuals"""
    print("[Agent 3] Researcher is querying ChromaDB...")
    collection = state.get("collection")
    user_query = state.get("question", "")
    entity = state.get("extracted_entity", "")
    
    text_context = "No relevant articles found."
    if collection:
        try:
            search_query = user_query if user_query else f"What is the treatment and medicine amount for {entity}?"
            vector_results = collection.query(query_texts=[search_query], n_results=1)
            if vector_results.get('documents') and vector_results['documents'][0]:
                text_context = vector_results['documents'][0][0]
        except Exception as e:
            print(f"Researcher error (ChromaDB query): {e}")
            text_context = "Vector database query failed."
        
    return {"vector_context": text_context}

def supervisor_node(state: GraphState):
    """Agent: Synthesizes final answer in requested language with model fallback"""
    print("[Agent 4] Supervisor is generating final response...")
    manager = state.get("gemini_manager") or get_gemini_manager()
    preferred_model = state.get("preferred_model")
    auto_fallback = state.get("auto_fallback", True)
    image = state.get("image")
    user_query = state.get("question", "")
    graph_context = state.get("graph_context", "")
    text_context = state.get("vector_context", "")
    language = state.get("language", "English")
    
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
    
    model_used = preferred_model or "Unknown"
    fallback_history = []
    try:
        final_response, model_used, fallback_history = manager.generate_content_with_fallback(
            contents=content_to_generate,
            preferred_model=preferred_model,
            auto_fallback=auto_fallback
        )
        answer = final_response.text
    except Exception as e:
        answer = f"⚠️ I could not generate a response: {e}"
        
    return {
        "final_answer": answer,
        "model_used": model_used,
        "fallback_history": fallback_history
    }

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
