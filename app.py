import streamlit as st
import chromadb
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from streamlit_agraph import agraph, Node, Edge, Config
from PIL import Image
from agents.workflow import build_workflow
from gemini_manager import get_gemini_manager

# Compile LangGraph engine
agentic_workflow = build_workflow()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Grape-Mind AI", page_icon="🍇", layout="wide")

# --- LOAD SECRETS (Local .env + Streamlit Cloud Secrets) ---
load_dotenv(override=True)

# Bridge Streamlit Cloud Secrets into os.environ if running on Streamlit Cloud
if hasattr(st, "secrets"):
    try:
        for key in ["GOOGLE_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]:
            if key in st.secrets and key not in os.environ:
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass

# --- SIDEBAR CONFIGURATION ---

# 1. Model Selector & Dynamic Failover
st.sidebar.header("🤖 Gemini Model Engine")
try:
    gemini_mgr = get_gemini_manager()
    available_models = gemini_mgr.get_available_models()
except Exception as e:
    available_models = ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

default_index = 0
if "gemini-2.5-flash" in available_models:
    default_index = available_models.index("gemini-2.5-flash")

selected_model = st.sidebar.selectbox(
    "Active Model:",
    available_models,
    index=default_index,
    help="Select the primary Gemini model. If rate limits or timeouts occur, auto-failover seamlessly shifts to the next working model."
)

auto_fallback = st.sidebar.checkbox(
    "Auto-Failover on Quota / Error",
    value=True,
    help="Automatically loop through available models when 429 Quota Exceeded, 504 Timeout, or 404 is encountered."
)

st.sidebar.markdown("---")

# 2. Language Selector
st.sidebar.header("🗣️ Language")
selected_language = st.sidebar.selectbox(
    "Choose Answer Language:",
    ["English", "Hindi", "Marathi", "Kannada", "Telugu"]
)
st.sidebar.markdown("---")

# --- SETUP (Cached) ---
@st.cache_resource
def setup_connections():
    # 1. Gemini Manager
    mgr = get_gemini_manager()

    # 2. Setup Neo4j (Graph) with Cloud Resilience
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    
    driver = None
    neo4j_status = "Disconnected"
    if NEO4J_URI and NEO4J_USERNAME and NEO4J_PASSWORD:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            driver.verify_connectivity()
            neo4j_status = "Connected ✅"
        except Exception as e:
            print(f"Neo4j connection warning (database may be paused or offline): {e}")
            neo4j_status = "Paused / Offline ⚠️"

    # 3. Setup ChromaDB (Vector)
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("grape_docs")
    
    # Auto-initialize vector store if empty (for fresh cloud deploys)
    if collection.count() == 0 and os.path.exists("./data"):
        try:
            from ingest_data import ingest_files
            ingest_files("./data")
        except Exception as e:
            print(f"ChromaDB auto-ingest notice: {e}")
    
    return mgr, driver, collection, neo4j_status

try:
    mgr, driver, collection, neo4j_status = setup_connections()
    if "Connected" in neo4j_status:
        st.sidebar.success(f"System Online: Neo4j & ChromaDB Connected ({collection.count()} chunks) ✅")
    else:
        st.sidebar.warning(f"Neo4j {neo4j_status} (ChromaDB Active with {collection.count()} chunks) ⚠️")
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# --- UI LAYOUT ---
st.title("🍇 Agri-Tech Graph RAG")
st.markdown("Ask about **Grapes**, **Diseases**, or **Treatments**.")

# Sidebar: Graph Visualizer
st.sidebar.markdown("---")
st.sidebar.header("📸 Attach Image (Sidebar)")
with st.sidebar.expander("Upload / Camera", expanded=False):
    side_uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg", "jpeg", "png"], key="side_upload")
    side_camera_image = st.camera_input("Take a Picture", key="side_cam")

st.sidebar.markdown("---")
st.sidebar.header("🕸️ Knowledge Graph")
if st.sidebar.button("Visualize Graph"):
    if not driver:
        st.sidebar.error("⚠️ Neo4j is offline or paused. If using Neo4j Aura, resume your instance at console.neo4j.io.")
    else:
        try:
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

        except Exception as e:
            st.sidebar.error(f"⚠️ Knowledge Graph connection failed: {e}\n\nIf using Neo4j Aura, your database may be paused. Resume it in console.neo4j.io.")

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
                
                # Run the LangGraph Agentic Workflow with Fallback & Model Selection!
                state_input = {
                    "question": prompt if prompt else "",
                    "image": img_obj,
                    "language": selected_language,
                    "gemini_manager": mgr,
                    "preferred_model": selected_model,
                    "auto_fallback": auto_fallback,
                    "driver": driver,
                    "collection": collection
                }
                
                final_state = agentic_workflow.invoke(state_input)
                
                answer = final_state.get("final_answer", "No answer generated.")
                graph_debug = final_state.get("graph_context", "")
                text_debug = final_state.get("vector_context", "")
                entity_debug = final_state.get("extracted_entity", "")
                model_used = final_state.get("model_used", selected_model)
                fallback_history = final_state.get("fallback_history", [])
                
                st.markdown(answer)
                with st.expander("See System Reasoning & Model Telemetry"):
                    st.markdown(f"🤖 **Active Model Responded:** `{model_used}`")
                    if fallback_history:
                        st.warning(f"⚡ **Auto-Failover Activated ({len(fallback_history)} attempts shifted):**")
                        for h in fallback_history:
                            st.caption(f"• Failed on `{h['model']}`: **{h['error']}**")
                    st.info(f"**Extracted Entity:** {entity_debug}")
                    st.info(f"**Graph Facts (Neo4j):** {graph_debug}")
                    st.warning(f"**PDF Context (ChromaDB):** {text_debug}")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Error: {e}")
