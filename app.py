import streamlit as st
import google.generativeai as genai
import chromadb
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from streamlit_agraph import agraph, Node, Edge, Config

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Grape-Mind AI", page_icon="🍇", layout="wide")
# Add this to Sidebar
language = st.sidebar.selectbox("Select Language", ["English", "Hindi", "Marathi"])

# --- LOAD SECRETS ---
load_dotenv()

# --- SETUP (Cached) ---
@st.cache_resource
def setup_connections():
    # 1. Setup Gemini (Updated Model)
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash') 

    # 2. Setup Neo4j (Graph)
    NEO4J_URI = os.getenv("NEO4J_URI") 
    NEO4J_AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    # 3. Setup ChromaDB (Vector)
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("grape_docs")
    
    return model, driver, collection

try:
    model, driver, collection = setup_connections()
    st.sidebar.success("System Online: Neo4j & ChromaDB Connected ✅")
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- LOGIC ---
def hybrid_query(user_query):
    # 1. Extract Entity
    response = model.generate_content(f"Extract only the main grape variety or disease name from: {user_query}. Respond with ONLY the name.")
    entity = response.text.strip()
    
    # 2. Graph Search
    graph_context = "No specific graph data found."
    with driver.session() as session:
        result = session.run(
            "MATCH (n {name: $name})-[:AFFECTS|TREATED_BY*1..2]-(related) RETURN DISTINCT related.name as info",
            name=entity
        )
        data = [record["info"] for record in result]
        if data:
            graph_context = ", ".join(data)

    # 3. Vector Search (PDFs)
    vector_results = collection.query(query_texts=[user_query], n_results=1)
    text_context = "No relevant articles found."
    if vector_results['documents'] and vector_results['documents'][0]:
        text_context = vector_results['documents'][0][0]

    # 4. Answer Generation
    final_prompt = f"""
    You are an expert Agronomist. Answer based on this data:
    [FACTS]: {graph_context}
    [MANUALS]: {text_context}

     User Question: {user_query}

       IMPORTANT: Output your answer in {language}.
    """
    return model.generate_content(final_prompt).text, graph_context, text_context

# --- UI LAYOUT ---
st.title("🍇 Agri-Tech Graph RAG")
st.markdown("Ask about **Grapes**, **Diseases**, or **Treatments**.")


# Sidebar: Graph Visualizer
st.sidebar.markdown("---")
st.sidebar.header("🕸️ Knowledge Graph")
if st.sidebar.button("Visualize Graph"):
    with driver.session() as session:
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50")
        nodes = []
        edges = []
        node_ids = set()
        
        for record in result:
            n = record['n']
            m = record['m']
            r = record['r']
            
            # Helper to add nodes safely
            def add_node(node_obj, img_url):
                if node_obj.element_id not in node_ids:
                    nodes.append(Node(
                        id=node_obj.element_id, 
                        label=node_obj.get("name"), 
                        size=25, 
                        shape="circularImage", 
                        image=img_url
                    ))
                    node_ids.add(node_obj.element_id)

            # Add nodes with icons
            add_node(n, "https://cdn-icons-png.flaticon.com/512/763/763065.png")
            add_node(m, "https://cdn-icons-png.flaticon.com/512/883/883407.png")
            
            edges.append(Edge(source=n.element_id, target=m.element_id, label=r.type))

        config = Config(width=700, height=500, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6")
        st.write("### 🕸️ Live Database Structure")
        agraph(nodes=nodes, edges=edges, config=config)

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ex: How do I treat Chardonnay?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Analyzing PDF Manuals & Graph Database..."):
            try:
                answer, graph_debug, text_debug = hybrid_query(prompt)
                st.markdown(answer)
                with st.expander("See System Reasoning"):
                    st.info(f"**Graph Facts:** {graph_debug}")
                    st.warning(f"**PDF Context:** {text_debug}")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Error: {e}")