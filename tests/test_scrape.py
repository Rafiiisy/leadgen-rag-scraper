# test_rag.py

from scraper import scrape_site, scrape_cta_text, remove_boilerplate, is_redundant
import cloudscraper
from bs4 import BeautifulSoup
import time
import requests


def retry_on_llm_failure(domain, max_retries=2, delay=3):
    from rag_runner import generate_insight

    for attempt in range(max_retries):
        print(f"\n🔍 Generating Insight for: {domain}\n" + "="*60)
        result = generate_insight(domain, "What is the mission of this organization?")

        # Only retry if 503 is explicitly mentioned in the LLM output
        if "503" in result:
            print(f"⚠️ LLM output 503 error detected (attempt {attempt+1}). Retrying in {delay}s...")
            time.sleep(delay)
        else:
            return result  # Success, no need to retry

    return "[Error] All retries failed. LLM service might be down."


if __name__ == "__main__":
    domain = "https://www.tokopedia.com/"
    print(f"\n🔍 Scraping Debug for: {domain}\n" + "="*60)

    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(domain, timeout=10)
        print(f"✅ Status Code: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            title = soup.title.string.strip() if soup.title and soup.title.string else "[No title found]"
            meta_desc = ""
            desc_tag = soup.find("meta", attrs={"name": "description"})
            if desc_tag and desc_tag.get("content"):
                meta_desc = desc_tag["content"]

            raw_text = soup.get_text(separator=" ", strip=True)
            cleaned_text, _ = remove_boilerplate(raw_text)

            print(f"\n📌 Page Title:\n  {title}")
            print(f"\n📝 Meta Description:\n  {meta_desc if meta_desc else '[No description meta tag found]'}")

            print("\n📄 Raw Body Text Preview (first 500 chars):")
            print(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)

            print("\n🧹 Cleaned Body Text Preview (first 500 chars):")
            print(cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text)

            combined_preview = f"{title}\n{meta_desc}\n{cleaned_text}"
            print("\n🔁 Duplicate Detected:", is_redundant(combined_preview))

            cta_output = scrape_cta_text(domain)
            print("\n🎯 CTA Detected:")
            print(cta_output if cta_output else "[No CTA elements found]")

    except requests.exceptions.ReadTimeout:
        print("❌ Read timeout while trying to scrape the domain.")
    except requests.exceptions.ConnectionError as ce:
        print(f"❌ Connection error: {ce}")
    except Exception as e:
        print(f"❌ An error occurred during scraping: {e}")

    print("\n\n🔎 Full Scraper Output from `scrape_site()`:\n" + "="*60)
    try:
        final_scraped_output = scrape_site(domain)
        print(final_scraped_output[:2000] + "..." if len(final_scraped_output) > 2000 else final_scraped_output)
    except Exception as e:
        print(f"❌ scrape_site() failed: {e}")

    print("\n\n🧠 Retrying LLM if needed:\n" + "="*60)
    print(retry_on_llm_failure(domain))
