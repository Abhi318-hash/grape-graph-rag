# 🍇 Grape-Mind AI — Agricultural Graph RAG Chatbot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-Google_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)

**An AI-powered chatbot for grape farmers that combines Knowledge Graphs + Vector Search + Generative AI to deliver expert agronomic advice in multiple Indian languages.**

</div>

---

## 📌 Overview

Grape-Mind AI is a **Graph RAG (Retrieval-Augmented Generation)** system designed for viticulture and grape farming. Instead of relying on a single AI model's memory, it retrieves **structured facts from a Neo4j knowledge graph** and **relevant passages from agricultural PDF manuals** before generating a precise, grounded answer.

### Key Highlights
- 🔍 **Hybrid Retrieval** — Combines structured graph data + unstructured PDF knowledge
- 🌐 **Multi-language Support** — Answers in English, Hindi, Marathi, Kannada, Telugu
- 🕸️ **Live Graph Visualization** — Explore the knowledge graph interactively in the sidebar
- 🔒 **Safety-Aware** — Safety filters tuned for agricultural content (pesticides, fungicides)
- 💬 **Chat Interface** — Persistent conversation with reasoning transparency

---

## 🏗️ System Architecture

```
👨‍🌾 User Question
        │
        ▼
┌─────────────────────┐
│   Streamlit UI      │  ← app.py
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Entity Extraction  │  ← Gemini 2.5 Flash
│  "Chardonnay"       │     extracts key term
└────┬────────────────┘
     │
     ├──────────────────────┐
     ▼                      ▼
┌──────────────┐    ┌──────────────────┐
│  Neo4j Graph │    │   ChromaDB       │
│  Database    │    │   Vector Store   │
│  (Structured │    │   (PDF Manuals)  │
│   Facts)     │    │                  │
└──────┬───────┘    └───────┬──────────┘
       │                    │
       └──────────┬─────────┘
                  ▼
        ┌──────────────────┐
        │  Final Prompt    │
        │  (Context Merge) │
        └────────┬─────────┘
                 ▼
        ┌──────────────────┐
        │  Gemini 2.5 Flash│  ← Answer in selected language
        │  Answer Generator│
        └──────────────────┘
```

---

## 🧠 How It Works — 4-Step Pipeline

| Step | Component | What Happens |
|------|-----------|--------------|
| **1. Entity Extraction** | Gemini AI | Extracts the main entity from the query (e.g., `"Chardonnay"`, `"Powdery Mildew"`) |
| **2. Graph Retrieval** | Neo4j | Traverses `AFFECTS` and `TREATED_BY` relationships to find connected facts |
| **3. Vector Retrieval** | ChromaDB | Searches embedded PDF chunks for the most semantically relevant passages |
| **4. Answer Generation** | Gemini AI | Combines graph facts + PDF context into a final answer in the selected language |

---

## 🗂️ Project Structure

```
agrichatbot/
├── app.py                  # 🚀 Main Streamlit application (UI + logic)
├── hybrid_retriever.py     # 🔬 Standalone test script for the RAG pipeline
├── ingest_data.py          # 📥 PDF ingestion → chunking → ChromaDB storage
├── populate_graph.py       # 🌱 Seeds Neo4j with grape variety/disease/treatment data
├── expand_data.py          # 📈 Expands the knowledge graph dataset
├── check_models.py         # ✅ Utility to verify Gemini model availability
├── requirements.txt        # 📦 Python dependencies
├── .env                    # 🔑 API keys and DB credentials (not committed)
├── chroma_db/              # 🗄️ Persistent local ChromaDB vector store
└── data/                   # 📂 Place your agricultural PDF manuals here
```

---

## 🕸️ Knowledge Graph Schema

The Neo4j graph uses 3 node types connected by 2 relationship types:

```
(:Variety) ──[:AFFECTS]──► (:Disease) ──[:TREATED_BY]──► (:Treatment)

Examples:
  Chardonnay        ──AFFECTS──►  Powdery Mildew  ──TREATED_BY──►  Sulfur Fungicide
  Cabernet Sauvignon ──AFFECTS──►  Downy Mildew    ──TREATED_BY──►  Copper Spray
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- A [Neo4j AuraDB](https://neo4j.com/cloud/platform/aura-graph-database/) account (free tier works)
- A [Google AI Studio](https://aistudio.google.com/) API key (Gemini)

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/agrichatbot.git
cd agrichatbot
```

### 2. Create a Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_gemini_api_key
NEO4J_URI=neo4j+ssc://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### 5. Populate the Knowledge Graph
```bash
python populate_graph.py
```

### 6. Ingest PDF Manuals
Place your agricultural PDF files inside the `data/` folder, then run:
```bash
python ingest_data.py
```

### 7. Launch the App
```bash
streamlit run app.py
```

---

## 🌍 Multi-Language Support

The chatbot can answer questions in:

| Language | Script |
|----------|--------|
| English | Latin |
| Hindi | देवनागरी |
| Marathi | मराठी |
| Kannada | ಕನ್ನಡ |
| Telugu | తెలుగు |

Select your preferred language from the sidebar before asking a question.

---

## 🖥️ Features

- **💬 Persistent Chat** — Full conversation history maintained in session
- **🔍 Reasoning Transparency** — Expand "See System Reasoning" to view raw graph facts and PDF context used
- **🕸️ Graph Visualizer** — Click "Visualize Graph" in the sidebar to see the live Neo4j knowledge graph rendered interactively
- **⚡ Cached Connections** — Database connections are cached with `@st.cache_resource` for performance
- **🛡️ Expert Fallback** — If data is not found in the DB, Gemini answers from general agronomic knowledge and labels it as "General Advice"

---

## 📦 Dependencies

```
streamlit          # Web UI framework
google-generativeai # Gemini AI SDK
chromadb           # Local vector database
neo4j              # Graph database driver
python-dotenv      # Environment variable management
streamlit-agraph   # Interactive graph visualization
pypdf              # PDF text extraction
```

---

## 🔮 Roadmap

- [ ] Add more grape varieties and diseases to the knowledge graph
- [ ] Support image upload for visual disease diagnosis
- [ ] Add weather API integration for location-based advice
- [ ] Deploy to Streamlit Community Cloud
- [ ] Support farmer voice input (speech-to-text)
- [ ] Export chat history as PDF report

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add: your feature description"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

---

## ⚠️ Disclaimer

This tool is intended to **assist** farmers and agronomists with information. Always consult a certified agricultural expert before applying any treatment, pesticide, or fungicide. The developers are not responsible for crop losses resulting from decisions made solely based on this tool's output.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Made with ❤️ for Indian Grape Farmers

</div>
