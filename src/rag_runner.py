# rag_runner.py

import time
from src.scraper import scrape_site
from src.llm import query_llm
from src.vectorstore import HybridRetriever

def generate_insight(domain: str, task: str, top_k: int = 7, retries: int = 3, wait_sec: int = 3):
    print(f"\n🔍 Generating Insight for: {domain}")
    print("=" * 60)

    context = scrape_site(domain)

    print("\n📄 Scraped Context Preview:\n")
    if isinstance(context, str):
        print(context[:1000] if len(context) > 1000 else context)
    else:
        print("[Warning] Context is not a string.")

    # if context.startswith("[Error]") or context.startswith("[Skipped]"):
    #     print("⚠️ Skipping due to scrape error or duplicate.")
    #     return context

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
""".strip()

    print("\n🧠 LLM Prompt Preview (First 500 chars):\n")
    print(prompt[:500])

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

if __name__ == "__main__":
    domain = "https://www.capraecapital.com/"
    task = "Tell me the company's name?"
    result = generate_insight(domain, task)
    print("\n🧠 Final Result:\n", result)
