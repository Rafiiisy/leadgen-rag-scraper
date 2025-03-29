# app.py

import streamlit as st
import pandas as pd
from src.rag_runner import generate_insight
from src.evaluation import (
    evaluate_insight_quality,
    evaluate_retrieval_quality,
    log_scrape_result,
    track_timing,
)
from PIL import Image
import time

# ---------- Setup ----------
st.set_page_config(page_title="LeadGen RAG Scraper", layout="wide")

# ✅ Load CSS
with open("style.css") as css:
    st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

# ✅ Ensure domain_tables is always initialized
if "domain_tables" not in st.session_state:
    st.session_state.domain_tables = {}

# ---------- Logo and App Info ----------
logo_path = "assets/leadgen logo.png"
logo = Image.open(logo_path)
st.image(logo, use_container_width=True)


# ---------- Sidebar Navigation ----------
st.sidebar.title("Navigation")


nav_option = st.sidebar.radio("Go to:", ["Home", "Domain Tables", "Evaluation"])

# # Define selected_domain safely
# selected_domain = None
# if nav_option == "Domain Tables" and st.session_state.domain_tables:
#     selected_domain = st.sidebar.selectbox("📂 Select a Domain", list(st.session_state.domain_tables.keys()))


# ---------- Evaluation Page ----------
if nav_option == "Evaluation":
    st.title("📊 Evaluation Dashboard")

    domain = st.text_input("🌍 Domain", placeholder="e.g., https://example.com", key="eval_domain")
    task = st.text_input("🧠 Task", placeholder="e.g., What is the mission of this organization?", key="eval_task")

    if st.button("Run Evaluation"):
        with st.spinner("Evaluating..."):
            total_start = time.time()
            scrape_start = time.time()

            output = generate_insight(domain, task)
            scrape_end = time.time()

            retriever = HybridRetriever(text=output, domain=domain)
            chunks = retriever.search(task, top_k=5)

            llm_time = 0.8  # Estimate
            total_end = time.time()

            timing_result = track_timing(scrape_end - scrape_start, 0.0, llm_time)
            insight_scores = evaluate_insight_quality(output, task, chunks)
            retrieval_scores = evaluate_retrieval_quality(chunks, task)
            robustness = log_scrape_result("Static (HTML only)", True, False, "Simple HTML")

            st.subheader("⚡ Runtime")
            st.table(pd.DataFrame(timing_result.items(), columns=["Metric", "Time"]))

            st.subheader("🧠 Insight Quality")
            st.table(pd.DataFrame(insight_scores.items(), columns=["Metric", "Score"]))

            st.subheader("🔍 Retrieval Quality")
            st.table(pd.DataFrame(retrieval_scores.items(), columns=["Metric", "Score"]))

            st.subheader("🧪 Scraping Robustness")
            st.table(pd.DataFrame([robustness]))



# ---------- Domain Tables Page ----------
elif nav_option == "Domain Tables":
    st.sidebar.markdown("### Domain Navigator")

    # Add new domain
    with st.sidebar.expander("➕ Add New Domain"):
        new_domain = st.text_input("Enter domain (e.g. https://example.com)", key="new_domain_box")
        if st.button("Create Domain Table"):
            new_domain = new_domain.strip()
            if new_domain:
                if new_domain not in st.session_state.domain_tables:
                    st.session_state.domain_tables[new_domain] = pd.DataFrame(columns=["No", "Task", "Output"])
                    st.success(f"✅ Created: {new_domain}")
                    st.rerun()  # 👈 instantly refresh UI after adding
                else:
                    st.warning("Domain already exists.")
            else:
                st.warning("Please enter a valid domain.")

    # Delete domain
    if st.session_state.domain_tables:
        with st.sidebar.expander("🗑️ Delete Domain"):
            delete_domain = st.selectbox("Select domain to delete", list(st.session_state.domain_tables.keys()), key="delete_domain_box")
            if st.button("Delete Selected Domain"):
                if delete_domain in st.session_state.domain_tables:
                    del st.session_state.domain_tables[delete_domain]
                    st.success(f"Deleted domain: {delete_domain}")
                    st.rerun()

    # ✅ Select domain after domain creation
    selected_domain = st.sidebar.selectbox("📂 Select a Domain", list(st.session_state.domain_tables.keys()))

    # Task Manager for Selected Domain
    if selected_domain:
        st.markdown(f"### Insight Tasks for: {selected_domain}")
        task_input = st.text_input("Enter a new task (e.g. What are their services?)", key="task_input_box")
        if st.button("Run and Add Task"):
            if task_input.strip():
                with st.spinner("Generating insight using RAG..."):
                    output = generate_insight(selected_domain, task_input)

                if not output or output.strip() == "":
                    output = "[No clear answer generated.]"
                elif output.lower().startswith("[error"):
                    output = f"⚠️ {output}"

                df = st.session_state.domain_tables[selected_domain]
                new_row = {
                    "No": len(df) + 1,
                    "Task": task_input,
                    "Output": output
                }
                st.session_state.domain_tables[selected_domain] = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("✅ Task added!")
            else:
                st.warning("Task cannot be empty.")

        st.markdown("#### Results Table")
        st.dataframe(
            st.session_state.domain_tables[selected_domain].drop(columns=["No"]).reset_index(drop=True),
            use_container_width=True,
            height=400
        )



# ---------- Home Page ----------
elif nav_option == "Home":
    st.subheader("Welcome to LeadGen Scraper")
    st.markdown("""
    This tool helps you generate insights from any public domain using Retrieval-Augmented Generation (RAG).

    ### Features
    - Create separate domain-specific tables
    - Add insight tasks to each domain
    - View and export structured responses

    ### Tech Stack
    - Streamlit for UI
    - Python (BeautifulSoup, Cloudscraper, Selenium)
    - Custom Hybrid VectorStore
    - LLM integration for insight generation

    ### Example Use Cases
    - Understand company mission/vision
    - Extract service/product offerings
    - Analyze call-to-actions from landing pages

    Try adding a new domain from the sidebar to get started.
    """)