import streamlit as st
import google.generativeai as genai
import chromadb
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from streamlit_agraph import agraph, Node, Edge, Config
from PIL import Image
from agents.workflow import build_workflow

# Compile LangGraph engine
agentic_workflow = build_workflow()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Grape-Mind AI", page_icon="🍇", layout="wide")
# Add this to Sidebar
# --- Language Selector ---
st.sidebar.header("🗣️ Language")
selected_language = st.sidebar.selectbox(
    "Choose Answer Language:",
    ["English", "Hindi", "Marathi", "Kannada", "Telugu"]
)
st.sidebar.markdown("---")


# --- LOAD SECRETS ---
load_dotenv(override=True)

# --- SETUP (Cached) ---

@st.cache_resource
def setup_connections():
    # 1. Setup Gemini with Safety Filters DISABLED (Important for Agri-Tech)
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # We allow "Dangerous Content" because we need to discuss Pesticides/Fungicides
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # Use the stable model version
    model = genai.GenerativeModel('gemini-2.5-flash', safety_settings=safety_settings)

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
# The legacy hybrid_query has been completely replaced by the LangGraph multi-agent engine!
# All logic is now handled in agents/workflow.py

# --- UI LAYOUT ---
st.title("🍇 Agri-Tech Graph RAG")
st.markdown("Ask about **Grapes**, **Diseases**, or **Treatments**.")

# Visual Diagnosis UI has been moved to a popover at the bottom and into the sidebar!


# Sidebar: Graph Visualizer
st.sidebar.markdown("---")
st.sidebar.header("📸 Attach Image (Sidebar)")
with st.sidebar.expander("Upload / Camera", expanded=False):
    side_uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg", "jpeg", "png"], key="side_upload")
    side_camera_image = st.camera_input("Take a Picture", key="side_cam")

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

        config = Config(width="100%", height=500, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6")
        st.write("### 🕸️ Live Database Structure")
        agraph(nodes=nodes, edges=edges, config=config)

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

popover = st.popover("➕ Attach Image")
with popover:
    st.markdown("**Attach an Image for Analysis**")
    main_uploaded_file = st.file_uploader("Upload File", type=["jpg", "jpeg", "png"], key="main_upload")
    main_camera_image = st.camera_input("Use Camera", key="main_cam")

image_to_process = main_uploaded_file or main_camera_image or side_uploaded_file or side_camera_image

analyze_button = False
if image_to_process:
    st.image(image_to_process, caption="Image Ready for Analysis", use_container_width=True)
    analyze_button = st.button("🔍 Analyze Image", use_container_width=True)

prompt = st.chat_input("Ex: How do I treat Chardonnay?")

if prompt or analyze_button:
    user_text = prompt if prompt else "Analyze this image."
    st.chat_message("user").markdown(user_text)
    st.session_state.messages.append({"role": "user", "content": user_text})

    with st.chat_message("assistant"):
        with st.spinner("Analyzing PDF Manuals & Graph Database..."):
            try:
                img_obj = Image.open(image_to_process) if image_to_process else None
                
                # Run the LangGraph Agentic Workflow!
                state_input = {
                    "question": prompt if prompt else "",
                    "image": img_obj,
                    "language": selected_language,
                    "model": model,
                    "driver": driver,
                    "collection": collection
                }
                
                final_state = agentic_workflow.invoke(state_input)
                
                answer = final_state["final_answer"]
                graph_debug = final_state["graph_context"]
                text_debug = final_state["vector_context"]
                entity_debug = final_state["extracted_entity"]
                
                st.markdown(answer)
                with st.expander("See System Reasoning"):
                    st.info(f"**Extracted Entity:** {entity_debug}")
                    st.info(f"**Graph Facts (Neo4j):** {graph_debug}")
                    st.warning(f"**PDF Context (ChromaDB):** {text_debug}")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Error: {e}")