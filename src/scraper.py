# scraper.py

import cloudscraper
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
from difflib import SequenceMatcher

BOILERPLATE_PATTERNS = [
    r'accept cookies?',
    r'terms of use',
    r'privacy policy',
    r'all rights reserved',
    r'copyright \d{4}',
    r'^sign in$|^log in$',
]

CONTACT_REGEX = {
    "email": re.compile(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\+?\d[\d\s\-\(\)]{7,}\d"),
    "location": re.compile(r"\d{1,5}\s+\w+(\s+\w+)*,?\s*\w+,?\s*[A-Z]{2}\s*\d{5}(-\d{4})?")
}

SECTION_TAGS = ["h1", "h2", "h3", "section", "article"]


def remove_boilerplate(text):
    lines = text.splitlines()
    cleaned = []
    junk = []
    for line in lines:
        line_lower = line.lower().strip()
        if len(line_lower) > 3 and not any(re.search(pat, line_lower) for pat in BOILERPLATE_PATTERNS):
            cleaned.append(line.strip())
        else:
            junk.append(line.strip())
    return "\n".join(cleaned), "\n".join(junk)


def is_redundant(new_text, threshold=0.95):
    cache_file = ".scrape_cache.txt"
    try:
        with open(cache_file, "r") as f:
            cached = f.read()
        ratio = SequenceMatcher(None, cached, new_text).ratio()
        return ratio >= threshold
    except:
        return False


def update_cache(text):
    with open(".scrape_cache.txt", "w") as f:
        f.write(text)


def scrape_cta_text(domain):
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(domain, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        cta_elements = soup.find_all(["a", "button"])
        ctas = set()

        for el in cta_elements:
            text = el.get_text(strip=True)
            if text and len(text) < 80:
                ctas.add(text)

        return "\n".join(sorted(ctas)) if ctas else "[No CTA elements found]"
    except Exception as e:
        return f"[Error - CTA Extraction] {str(e)}"


def extract_metadata_from_tags(soup):
    sections = {}
    for tag in SECTION_TAGS:
        for element in soup.find_all(tag):
            label = element.get_text(strip=True).lower()
            if len(label.split()) <= 12 and len(label) > 3:
                section_key = f"{tag.upper()}: {label}"
                content = []
                cta_count = 0
                para_count = 0

                for sibling in element.find_next_siblings():
                    if sibling.name in SECTION_TAGS:
                        break
                    sibling_text = sibling.get_text(" ", strip=True)
                    if sibling_text:
                        content.append(sibling_text)
                    if sibling.find_all("button") or sibling.find_all("a"):
                        cta_count += len(sibling.find_all("button")) + len(sibling.find_all("a"))
                    if sibling.name == "p":
                        para_count += 1

                content_block = " ".join(content)
                if cta_count >= 3 and para_count < 2:
                    section_key = f"CTA CLUSTER: {label}"
                sections[section_key] = content_block
    return sections


def extract_contacts(text):
    contacts = []
    for label, pattern in CONTACT_REGEX.items():
        found = pattern.findall(text)
        if found:
            contacts.extend(set(found))
    return contacts


def scrape_site(domain: str, max_chars: int = 10000) -> str:
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(domain, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"]

        body_text = soup.get_text(separator=" ", strip=True)[:max_chars] if soup else ""

        # Fallback if too short
        if len(body_text) < 200:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")

                driver = webdriver.Chrome(options=chrome_options)
                driver.get(domain)
                time.sleep(5)
                html = driver.execute_script("return document.documentElement.innerHTML;")
                driver.quit()

                soup = BeautifulSoup(html, "html.parser")
                body_text = soup.get_text(separator=" ", strip=True)[:max_chars]
            except Exception as se:
                return f"[Error - Selenium Fallback] {str(se)}"

        cleaned_text, junk_text = remove_boilerplate(body_text)
        if not cleaned_text.strip():
            print("⚠️ Fallback to original body_text (cleaned text is empty)")
            cleaned_text = body_text

        cta_text = scrape_cta_text(domain)
        structured_sections = extract_metadata_from_tags(soup)
        contacts = extract_contacts(cleaned_text)

        combined = f"{title}\n{meta_desc}\n{cleaned_text}"

        if "[Error" not in cta_text:
            combined += f"\n\n[CTA Section]\n{cta_text}"

        for k, v in structured_sections.items():
            if v:
                combined += f"\n\n[{k}]\n{v}"

        if contacts:
            combined += f"\n\n[CONTACTS]\n" + "\n".join(contacts)

        if junk_text.strip():
            combined += f"\n\n[JUNK]\n{junk_text}"

        if is_redundant(combined):
            return "[Skipped] Duplicate content previously scraped."

        update_cache(combined)

        print("Final text length:", len(cleaned_text))
        print("Final text preview:", cleaned_text[:500])

        return combined if combined else "[Error] Could not extract content."

    except Exception as e:
        return f"[Error] {str(e)}"