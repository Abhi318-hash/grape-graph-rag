import streamlit as st
import google.generativeai as genai
import chromadb
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from streamlit_agraph import agraph, Node, Edge, Config

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Grape-Mind AI", page_icon="🍇", layout="wide")

# --- LOAD SECRETS (Make sure .env is in the same folder) ---
load_dotenv()

# --- SETUP (Cached to run once) ---
@st.cache_resource
def setup_connections():
    # 1. Setup Gemini
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash') # Or 'gemini-pro'

    # 2. Setup Neo4j (Graph)
    # Note: Using +ssc for self-signed certificate (your network fix)
    NEO4J_URI = os.getenv("NEO4J_URI") # e.g. "neo4j+ssc://..."
    NEO4J_AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    # 3. Setup ChromaDB (Vector)
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("grape_docs")
    
    return model, driver, collection

try:
    model, driver, collection = setup_connections()
    st.sidebar.success("System Connected: Neo4j & ChromaDB Online ✅")
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- THE HYBRID LOGIC ---
def hybrid_query(user_query):
    # 1. Entity Extraction
    response = model.generate_content(f"Extract only the main grape variety or disease name from: {user_query}. Respond with ONLY the name.")
    entity = response.text.strip()
    
    # 2. Graph Retrieval
    graph_context = "No specific graph data found."
    with driver.session() as session:
        # Using the corrected query
        result = session.run(
            "MATCH (n {name: $name})-[:AFFECTS|TREATED_BY*1..2]-(related) RETURN DISTINCT related.name as info",
            name=entity
        )
        data = [record["info"] for record in result]
        if data:
            graph_context = ", ".join(data)

    # 3. Vector Retrieval
    vector_results = collection.query(query_texts=[user_query], n_results=1)
    text_context = "No relevant articles found."
    if vector_results['documents'] and vector_results['documents'][0]:
        text_context = vector_results['documents'][0][0]

    # 4. Final Generation
    final_prompt = f"""
    You are an expert Agronomist. Answer the user question based on this data:
    
    [STRUCTURED KNOWLEDGE - HIGH RELIABILITY]
    {graph_context}
    
    [UNSTRUCTURED MANUALS - DETAILED CONTEXT]
    {text_context}
    
    User Question: {user_query}
    """
    return model.generate_content(final_prompt).text, graph_context, text_context

# --- THE USER INTERFACE ---
st.title("🍇 Agri-Tech Graph RAG")
st.markdown("Ask questions about **Grape Varieties**, **Diseases**, and **Treatments**.")
# --- Add this at the top with imports ---


# --- Add this in the Sidebar section ---
st.sidebar.markdown("---")
st.sidebar.header("🕸️ Graph Visualizer")

if st.sidebar.button("Visualize Knowledge Graph"):
    with driver.session() as session:
        # Get all nodes and relationships
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50")
        
        nodes = []
        edges = []
        node_ids = set()
        
        for record in result:
            n = record['n']
            m = record['m']
            r = record['r']
            
            # Add Source Node
            if n.element_id not in node_ids:
                nodes.append(Node(id=n.element_id, label=n.get("name"), size=25, shape="circularImage", image="https://cdn-icons-png.flaticon.com/512/763/763065.png"))
                node_ids.add(n.element_id)
            
            # Add Target Node
            if m.element_id not in node_ids:
                nodes.append(Node(id=m.element_id, label=m.get("name"), size=25, shape="circularImage", image="https://cdn-icons-png.flaticon.com/512/2822/2822261.png"))
                node_ids.add(m.element_id)
            
            # Add Edge
            edges.append(Edge(source=n.element_id, target=m.element_id, label=r.type))

        config = Config(width=700, height=500, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6")
        
        st.write("### 🕸️ Interactive Knowledge Graph")
        agraph(nodes=nodes, edges=edges, config=config)

# Chat History Session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ex: How do I treat Chardonnay diseases?"):
    # Show user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing Graph & Vector Databases..."):
            try:
                answer, graph_debug, text_debug = hybrid_query(prompt)
                
                # Show the main answer
                st.markdown(answer)
                
                # Show "How it worked" (Good for demos!)
                with st.expander("See System Reasoning (Debug)"):
                    st.info(f"**Graph Facts Found:** {graph_debug}")
                    st.warning(f"**Article Context Found:** {text_debug}")
                
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"An error occurred: {e}")