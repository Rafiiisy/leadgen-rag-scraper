# 🧠 LeadGen RAG Scraper

## 📌 Project Overview
LeadGen RAG Scraper is a tool designed to generate structured, insightful information from any public domain using Retrieval-Augmented Generation (RAG). It is tailored for lead generation tasks such as extracting company missions, services, and call-to-actions from websites, and organizing them into task-specific tables per domain.

---

## 🎯 Goals & Missions
- **Simplify web-based lead intelligence** through an easy-to-use UI.
- **Support automated, explainable insights** powered by LLMs.
- **Allow domain-specific task evaluation**, enabling marketing teams, researchers, and analysts to retrieve targeted website summaries.
- **Offer performance diagnostics** to evaluate scraping robustness, LLM quality, and retrieval effectiveness.

---

## ✨ Novelties Compared to Existing Tools
| Feature | LeadGen Scraper | CohesiveAI / Other Scrapers |
|--------|------------------|-----------------------------|
| Per-domain task tables | ✅ | ❌ |
| Built-in insight evaluation dashboard | ✅ | ❌ |
| Hybrid retrieval (BM25 + FAISS) | ✅ | Limited |
| Manual + automatic domain input | ✅ | ✅ |
| Streamlit UI + persistent state | ✅ | Varies |
| Emphasis on interpretability | ✅ | ❌ |

---

## 🧰 Tech Stack & Rationale

| Component | Tool | Reasoning |
|----------|------|-----------|
| **Frontend** | Streamlit | Simple yet powerful for rapid dashboard development |
| **Scraping** | Cloudscraper, BeautifulSoup, Selenium | Handles both static and JS-heavy websites |
| **LLM Access** | HuggingFace / Local Model API | Cost-effective and controllable model deployment |
| **Retrieval** | FAISS + BM25 (HybridRetriever) | Combines vector similarity and keyword relevance |
| **Data Storage** | Streamlit Session State (in-memory) | Suitable for ephemeral, per-session task tables |

---

## 🏗️ Architecture Diagram
```text
+------------+      +-------------------+      +--------------+
| User Input | ---> | Scraper (Cloud/JS) | ---> |  Context     |
+------------+      +-------------------+      +--------------+
                                                  |
                             +----------------+    v
                             | HybridRetriever |--> Prompt + Chunks
                             +----------------+    |
                                                  v
                                             +------------+
                                             |   LLM API   |
                                             +------------+
                                                  |
                                                  v
                                          +----------------+
                                          | Insight + Eval |
                                          +----------------+
```

---

## 🔄 Workflow

1. **User adds a domain** via UI → Creates a domain-specific task table.
2. **User adds a task** (e.g., "What is the mission?").
3. **System scrapes** the webpage and falls back to Selenium if needed.
4. **Chunks generated** from webpage text.
5. **HybridRetriever** selects relevant chunks using BM25 + FAISS.
6. **LLM** generates an answer based on prompt + chunks.
7. **Answer is stored** in the domain's table.
8. **(Optional)** Evaluation dashboard benchmarks runtime, insight quality, retrieval quality, and scraping robustness.

---

## 🧪 Evaluation Dashboard

### 1. ⚡ Runtime
- Tracks durations for scraping, fallback, LLM response, and overall turnaround.

### 2. 🧠 Insight Quality (Auto-evaluated)
- **Relevance**: Do output words overlap with task keywords?
- **Specificity**: Does the answer use actual tokens from the site?
- **Faithfulness**: Do phrases match retrieved chunks?

### 3. 🔍 Retrieval Quality
- **Chunk Matching**: Are retrieved chunks semantically relevant?
- **Chunk Diversity**: Do chunks cover diverse sections or just repeat?

### 4. 🧪 Scraping Robustness
- Verifies if fallback is triggered.
- Logs site types, status, and notes.

---

## ⚙️ Setup Instructions

### 📁 Clone the repository
```bash
git clone https://github.com/Rafiiisy/leadgen-rag-scraper.git
cd leadgen-rag-scraper
```

### 🐍 Create virtual environment
```bash
python3 -m venv myenv
source myenv/bin/activate
```

### 📦 Install dependencies
```bash
pip install -r requirements.txt
```

### 📄 Configure API Keys (Optional)
Create a `.env` file:
```
HUGGINGFACE_API_KEY=your_key_here
```

### 🚀 Run the App
```bash
streamlit run app.py
```

---

## 📁 Project Structure
```
.
├── app.py                  # Streamlit app UI
├── config.py               # API config
├── style.css               # UI styles
├── requirements.txt        # All dependencies
├── .env                    # Your secrets (gitignored)
├── assets/                 # Logo and images
├── src/
│   ├── rag_runner.py       # Main logic (scrape → retrieve → query LLM)
│   ├── scraper.py          # Cloudscraper + fallback logic
│   ├── vectorstore.py      # BM25 + FAISS hybrid retriever
│   ├── evaluation.py       # Heuristic scoring methods
│   └── llm.py              # LLM query endpoint
└── tests/
    └── test_rag.py         # Unit tests
```

---

## 🚀 Future Improvements
- [ ] Add PDF and image parsing (OCR for flyers)
- [ ] Persistent storage (SQLite / Supabase backend)
- [ ] PDF/CSV export of task tables
- [ ] User authentication for multi-user support
- [ ] Customize prompt templates per domain type
- [ ] LLM caching & retry analytics

---

## 📬 Contact & Contributions
Feel free to fork or submit issues! Created by [@Rafiiisy](https://github.com/Rafiiisy) for exploration and research in lead generation tools using open-source LLMs.
