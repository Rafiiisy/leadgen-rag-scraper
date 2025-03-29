def evaluate_insight_quality(output: str, task: str, chunks: list[str]) -> dict:
    """
    Automatically estimate insight quality with heuristics.
    
    - Relevance: Check if task keywords appear in output.
    - Specificity: Look for named entities or URLs from chunks.
    - Faithfulness: Check if output phrases overlap with chunks.
    """
    task_keywords = set(task.lower().split())
    output_words = set(output.lower().split())
    chunk_text = " ".join(chunks).lower()

    relevance_score = len(task_keywords & output_words) / max(len(task_keywords), 1)

    specificity_score = sum(1 for word in output_words if word in chunk_text) / max(len(output_words), 1)

    phrase_overlap = sum(1 for phrase in output.split('.') if phrase.strip().lower() in chunk_text)
    faithfulness_score = phrase_overlap / max(len(output.split('.')), 1)

    return {
        "Relevance": round(relevance_score * 5, 1),
        "Specificity": round(specificity_score * 5, 1),
        "Faithfulness": round(faithfulness_score * 5, 1)
    }

def evaluate_retrieval_quality(chunks: list[str], task_prompt: str) -> dict:
    """
    Automatically score chunk-task alignment and content variety.
    """
    if not chunks:
        return {"Chunk Matching": 0.0, "Chunk Diversity": 0.0}

    task_words = set(task_prompt.lower().split())
    match_score = sum(1 for c in chunks if task_words & set(c.lower().split())) / len(chunks)
    diversity_score = len(set(c[:70] for c in chunks)) / len(chunks)

    return {
        "Chunk Matching": round(match_score * 5, 3),
        "Chunk Diversity": round(diversity_score * 5, 3)
    }

def log_scrape_result(site_type: str, passed: bool, used_fallback: bool, notes: str = "") -> dict:
    return {
        "Site Type Tested": site_type,
        "Pass?": "✅" if passed else "❌",
        "Fallback Used": "Yes" if used_fallback else "No",
        "Notes": notes
    }

def track_timing(scrape_sec: float, fallback_sec: float, llm_sec: float) -> dict:
    return {
        "Domain scrape (Cloudscraper)": f"~{scrape_sec:.2f} sec",
        "Fallback w/ Selenium": f"~{fallback_sec:.2f} sec" if fallback_sec > 0 else "N/A",
        "LLM Response (1-shot)": f"~{llm_sec:.2f} sec",
        "Overall task turnaround": f"~{scrape_sec + fallback_sec + llm_sec:.2f} sec"
    }
