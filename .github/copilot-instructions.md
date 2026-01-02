# Copilot instructions for agri-chatbot

Purpose
- Give concise, actionable guidance so AI coding agents can be productive immediately in this repo.

Big picture (what this repo does)
- Small collection of scripts that combine a vector DB (ChromaDB), a knowledge graph (Neo4j), and Google Generative AI (Gemini) to answer viticulture questions.
- Dataflow: entity extraction (Gemini) -> graph facts (Neo4j) -> text context (Chroma/ChromaDB) -> final generation (Gemini).

Key files & how they interact
- `ingest_data.py` — example of adding unstructured text to Chroma collection `grape_docs` using `collection.add(documents=[...], ids=[...])`.
- `populate_graph.py` — seeds Neo4j with nodes/relations (labels: `Variety`, `Disease`, `Treatment`; relations: `AFFECTS`, `TREATED_BY`) using `session.execute_write(...)`.
- `hybrid_retriever.py` — core pipeline: extracts entity with `model.generate_content`, queries Neo4j for related nodes, queries Chroma with `collection.query(..., n_results=2)`, then prompts Gemini for the final answer.
- `check_models.py` — shows how to list available Gemini models (`genai.list_models()`) and test for `generateContent` capability.

Environment & runtime notes
- Preferred env var: `GOOGLE_API_KEY` (used with `dotenv.load_dotenv()` in some scripts, and `os.getenv(...)`).
- Local Chroma DB lives at `./chroma_db` (sqlite file seen as `chroma_db/chroma.sqlite3`). The collection name used across code is `grape_docs`.
- Neo4j: URIs in code use `neo4j+ssc://...`; authenticate with `(NEO4J_USERNAME, NEO4J_PASSWORD)`. Some scripts have sample/hard-coded credentials — do not commit real secrets.

Command examples (how to run things locally)
- Install deps in a virtualenv and add your `GOOGLE_API_KEY` to `.env` or env vars.
- Run:
  - `python check_models.py` — lists usable models
  - `python populate_graph.py` — seed the Neo4j graph
  - `python ingest_data.py` — add sample articles to Chroma
  - `python hybrid_retriever.py` — run a smoke test of the full retrieval+generation flow

Project conventions discovered
- Small script-first approach (no package layout). Keep changes small and script-focused.
- Node/relationship naming is explicit (e.g., `Variety`, `Disease`, relations `AFFECTS` and `TREATED_BY`). Use those labels/relations when adding graph queries or data.
- Chroma usage: `collection.add(documents=[...], ids=[...])` and query via `collection.query(query_texts=[...], n_results=…)`.
- Gemini usage pattern: call `genai.configure(api_key=...)`, create `genai.GenerativeModel('gemini-2.5-flash')` and use `model.generate_content(prompt)`.

Safety & secrets
- Several files currently contain hard-coded API keys/credentials. Do not add secrets to source. Prefer `.env` + `os.getenv(...)` pattern that some scripts already use.

What agents should do (actionable behaviors)
- When editing/adding features, prefer using env vars for keys and ensure no secrets are committed.
- When changing retrieval prompts or graph queries, add a short smoke script (or update the existing script) that demonstrates end-to-end behavior.
- Preserve collection name `grape_docs` and Neo4j label names unless intentionally changing schema — document schema changes in PR descriptions.
- Add minimal manual test instructions in PRs (commands to run, expected console outputs).

If anything above is unclear or you want different emphasis (e.g., more detail on Neo4j schema, test harness, or CI), say which sections to expand and I will iterate. ✅
