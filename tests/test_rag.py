# test_rag.py

import time
from scraper import scrape_site
from llm import query_llm
from vectorstore import HybridRetriever


def generate_insight(domain: str, task: str, top_k=7, retries=3, wait_sec=3):
    print(f"\n🔍 Generating Insight for: {domain}")
    print("=" * 60)

    context = scrape_site(domain)

    # if context.startswith("[Error]") or context.startswith("[Skipped]"):
    #     print("⚠️ Skipping due to scrape error or duplicate.")
    #     return context

    print("\n📄 Scraped Context Preview (First 800 chars):\n")
    print(context[:800])

    retriever = HybridRetriever(text=context, domain=domain)
    relevant_chunks = retriever.search(task, top_k=top_k)
    combined_context = "\n\n".join(relevant_chunks)

    print("\n🔍 Chunks Sent to LLM:\n")
    for i, chunk in enumerate(relevant_chunks):
        print(f"[{i+1}] {chunk[:300]}{'...' if len(chunk) > 300 else ''}\n")

    prompt = f"""
Task: {task}

Text:
{combined_context}

Answer:
"""
    print("\n🧠 LLM Prompt Preview (First 500 chars):\n")
    print(prompt[:500])

    # Retry if 503 or empty output
    for attempt in range(1, retries + 1):
        result = query_llm(prompt)
        if (
            result
            and "503" not in result
            and "Connection aborted" not in result
            and "Error" not in result
            and result.strip()
        ):
            break
        print(f"\n🔁 Retry {attempt}/{retries} after failure:\n{result[:100]}")
        time.sleep(wait_sec)
    else:
        result = "[Error] LLM failed after all retries."

    print("\n🧠 LLM Output:\n")
    print(result)

    return result


# Example usage
if __name__ == "__main__":
    domain = "https://www.tokopedia.com/"
    task = "What is the mission of this organization?"
    generate_insight(domain, task)
