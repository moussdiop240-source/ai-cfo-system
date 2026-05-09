"""
AI Copywriting Service – Lead Prospector
Scrapes Yellow Pages, audits websites, generates cold emails, tracks leads.
"""

import asyncio
import csv
import json
import os
import re
import time
import urllib.parse
from datetime import date

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ─────────────────────────────────────────────
# CONFIGURATION – edit these before running
# ─────────────────────────────────────────────
NICHES = ["hvac", "plumbing", "roofing", "real estate agent"]
CITIES = ["Los Angeles CA", "Phoenix AZ", "Houston TX"]
ALIAS = "Alex"
MAX_RESULTS_PER_SEARCH = 5
LEADS_CSV = "leads.csv"
EMAILS_DIR = "emails"
# ─────────────────────────────────────────────

JUNK_NAME_FRAGMENTS = [
    "best home savings", "compare hvac experts", "home savings",
    "compare pros", "local pros", "top rated local", "top rated",
    "best local", "local deals", "find pros", "get quotes",
]

HEADLINE_FALLBACKS = {
    "hvac": "24/7 Emergency HVAC Repair – We're Here in 60 Minutes or Less",
    "plumbing": "Burst Pipe? Emergency Plumber Available Now – Call 24/7",
    "roofing": "Roof Leaking? Immediate Emergency Repairs – Free Inspection",
    "real estate agent": "Find Your Dream Home Today – View Exclusive Listings Now",
}

CSV_COLUMNS = [
    "Company", "Trade", "City", "Website", "Phone",
    "Red Flags", "Contact Email", "Date Sent", "Status", "Email File",
]


# ── Helpers ──────────────────────────────────

def safe_filename(text: str, max_len: int = 50) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "_", text)
    return cleaned[:max_len].strip("_")


def is_junk_name(name: str) -> bool:
    lower = name.lower()
    return any(frag in lower for frag in JUNK_NAME_FRAGMENTS)


def is_junk_domain(url: str) -> bool:
    return "yellowpages.com" in url.lower()


# ── Yellow Pages Scraper ──────────────────────

def scrape_yellow_pages(niche: str, city: str, max_results: int) -> list[dict]:
    url = (
        "https://www.yellowpages.com/search?"
        + urllib.parse.urlencode({"search_terms": niche, "geo_location_terms": city})
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    print(f"  [YP] Fetching: {url}")
    try:
        resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [YP] Request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    seen = set()

    listings = soup.select("div.result, div.v-card, div.organic")
    if not listings:
        listings = soup.select("div[class*='result']")

    for listing in listings:
        if len(results) >= max_results:
            break

        # Business name
        name = ""
        for sel in [
            "span[itemprop='name']",
            "a.business-name span",
            "h2.n a",
            "a.business-name",
        ]:
            el = listing.select_one(sel)
            if el and el.get_text(strip=True):
                name = el.get_text(strip=True)
                break
        if not name:
            continue
        if is_junk_name(name):
            print(f"  [YP] Skipping junk name: {name}")
            continue

        # Website
        website = ""
        for sel in [
            "a.track-visit-website",
            "a.visit-website",
            "a[href*='yp.com/redirect']",
        ]:
            el = listing.select_one(sel)
            if el and el.get("href"):
                website = el["href"]
                break
        if not website:
            for a in listing.find_all("a"):
                text = a.get_text(strip=True).lower()
                if text in ("visit website", "website"):
                    website = a.get("href", "")
                    break

        # Resolve YP redirect URLs
        if website and "yp.com/redirect" in website:
            try:
                r = httpx.get(website, headers=headers, timeout=10, follow_redirects=True)
                website = str(r.url)
            except Exception:
                website = ""

        if not website or is_junk_domain(website):
            website = ""

        # Phone
        phone = ""
        for sel in ["div.phone", "span[itemprop='telephone']", "a.tel"]:
            el = listing.select_one(sel)
            if el and el.get_text(strip=True):
                phone = el.get_text(strip=True)
                break

        dedup_key = (name.lower(), website.lower())
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        results.append({"name": name, "website": website, "phone": phone})
        print(f"  [YP] Found: {name} | {website} | {phone}")

    return results


# ── Website Analysis (Playwright) ─────────────

async def get_above_fold_text(url: str, playwright_instance) -> str:
    try:
        browser = await playwright_instance.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        text = await page.evaluate("""() => {
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null
            );
            let result = '';
            let node;
            while ((node = walker.nextNode()) && result.length < 2000) {
                const parent = node.parentElement;
                if (!parent) continue;
                const style = window.getComputedStyle(parent);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                const rect = parent.getBoundingClientRect();
                if (rect.top < 800 && rect.bottom > 0) {
                    const val = node.nodeValue.trim();
                    if (val) result += val + ' ';
                }
            }
            return result.trim();
        }""")

        await browser.close()
        return text[:2000]
    except Exception as e:
        print(f"  [PW] Error fetching {url}: {e}")
        return ""


# ── AI Audit via Pollinations ─────────────────

def audit_with_ai(page_text: str) -> dict | None:
    prompt = (
        "Analyze this landing page text and return a JSON object with keys: "
        "passes_3_second_test, has_phone_or_call_button, headline_clear, too_many_cta, summary. "
        "Return only valid JSON, no markdown, no extra text.\n\n"
        + page_text[:1500]
    )
    encoded = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded}"
    try:
        resp = httpx.get(url, timeout=20)
        if resp.status_code != 200:
            return None
        raw = resp.text.strip()
        # Strip possible markdown fences
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
        data = json.loads(raw)
        if all(k in data for k in ["passes_3_second_test", "has_phone_or_call_button",
                                    "headline_clear", "too_many_cta"]):
            return data
        return None
    except Exception as e:
        print(f"  [AI] Audit failed: {e}")
        return None


# ── Offline Fallback Audit ────────────────────

def audit_offline(page_text: str) -> dict:
    phone_re = re.compile(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    cta_phrases = [
        "call now", "call us", "contact", "call today", "get a quote",
        "24/7", "emergency", "free estimate", "schedule", "book",
    ]
    vague_words = [
        "welcome to", "your experts", "quality you can trust",
        "best in", "premier", "proudly serving", "our story",
    ]

    lower_text = page_text.lower()
    first_200 = lower_text[:200]

    has_phone = bool(phone_re.search(page_text))
    has_cta = any(phrase in first_200 for phrase in cta_phrases)
    headline_vague = any(word in lower_text[:300] for word in vague_words)
    click_count = first_200.count("click") + first_200.count("learn more")
    too_many_cta = click_count > 3

    passes = (has_phone or has_cta) and not headline_vague and not too_many_cta

    return {
        "passes_3_second_test": passes,
        "has_phone_or_call_button": has_phone or has_cta,
        "headline_clear": not headline_vague,
        "too_many_cta": too_many_cta,
        "summary": "Offline fallback audit",
    }


# ── Determine Red Flags ───────────────────────

def get_red_flags(audit: dict) -> list[str]:
    flags = []
    if not audit.get("has_phone_or_call_button"):
        flags.append("No phone/CTA visible above fold")
    if not audit.get("headline_clear"):
        flags.append("Vague or unclear headline")
    if audit.get("too_many_cta"):
        flags.append("Too many competing CTAs")
    return flags


# ── Headline Generation via AI ────────────────

def generate_headline_ai(trade: str, page_text: str) -> str | None:
    prompt = (
        f"Write a better, urgent hero headline (under 15 words) for a {trade} company "
        f"to get phone calls. Current page text: {page_text[:500]}"
    )
    encoded = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded}"
    try:
        resp = httpx.get(url, timeout=20)
        if resp.status_code == 200 and resp.text.strip():
            headline = resp.text.strip().strip('"').strip("'")
            return headline[:120]
        return None
    except Exception as e:
        print(f"  [AI] Headline gen failed: {e}")
        return None


def get_fallback_headline(trade: str) -> str:
    lower = trade.lower()
    for key, val in HEADLINE_FALLBACKS.items():
        if key in lower:
            return val
    return f"Get Expert {trade.title()} Service – Call Now for a Free Estimate"


# ── Email Generation ──────────────────────────

def generate_email(
    business_name: str,
    trade: str,
    page_text: str,
    current_headline: str,
    better_headline: str,
) -> str:
    first_name = business_name.split()[0] if business_name else "there"
    body = f"""Hi {first_name},

I looked at {business_name}'s website and spotted something that's probably costing you calls.

Your headline: "{current_headline}"

Here's a free rewrite that would get more phone calls:
"{better_headline}"

No catch — if you like it and want ongoing optimization, I charge $397/month (first 3 months). Either way, hope it helps.

Best,
{ALIAS}"""
    return body


# ── CSV Management ────────────────────────────

def ensure_csv():
    if not os.path.exists(LEADS_CSV):
        with open(LEADS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()


def append_lead(row: dict):
    with open(LEADS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(row)


# ── Main Orchestration ────────────────────────

async def process_business(
    business: dict,
    niche: str,
    city: str,
    playwright_instance,
):
    name = business["name"]
    website = business["website"]
    phone = business["phone"]

    print(f"\n→ Processing: {name} ({website})")

    # Get above-fold text
    page_text = ""
    if website:
        page_text = await get_above_fold_text(website, playwright_instance)
        delay = 2 + (time.time() % 1)  # 2–3 second delay
        await asyncio.sleep(delay)

    if not page_text:
        print(f"  [SKIP] No page text retrieved for {name}")
        return

    # Audit
    audit = audit_with_ai(page_text)
    if audit is None:
        print("  [AUDIT] AI failed, using offline fallback")
        audit = audit_offline(page_text)
    else:
        print("  [AUDIT] AI audit succeeded")

    # Only proceed if it's a prospect (any flag failed)
    red_flags = get_red_flags(audit)
    if not red_flags and audit.get("passes_3_second_test"):
        print(f"  [PASS] {name} passed 3-second test – skipping")
        return

    print(f"  [PROSPECT] Red flags: {red_flags}")

    # Current headline
    lines = [l.strip() for l in page_text.splitlines() if l.strip()]
    current_headline = lines[0][:120] if lines else ""

    # Better headline
    better_headline = generate_headline_ai(niche, page_text)
    if not better_headline:
        better_headline = get_fallback_headline(niche)
    print(f"  [HEADLINE] {better_headline}")

    # Generate email
    email_body = generate_email(name, niche, page_text, current_headline, better_headline)
    subject = "Your homepage might be hiding your best asset"
    full_email = f"Subject: {subject}\n\n{email_body}"

    # Save email file
    os.makedirs(EMAILS_DIR, exist_ok=True)
    fname = safe_filename(name)
    email_file = os.path.join(EMAILS_DIR, f"email_{fname}.txt")
    try:
        with open(email_file, "w", encoding="utf-8") as f:
            f.write(full_email)
        print(f"  [EMAIL] Saved: {email_file}")
    except Exception as e:
        print(f"  [EMAIL] Save failed: {e}")
        email_file = ""

    # Append to CSV
    row = {
        "Company": name,
        "Trade": niche,
        "City": city,
        "Website": website,
        "Phone": phone,
        "Red Flags": "; ".join(red_flags),
        "Contact Email": "",
        "Date Sent": "",
        "Status": "Prospect",
        "Email File": email_file,
    }
    append_lead(row)
    print(f"  [CSV] Lead saved for {name}")


async def main():
    ensure_csv()
    os.makedirs(EMAILS_DIR, exist_ok=True)

    async with async_playwright() as pw:
        for niche in NICHES:
            for city in CITIES:
                print(f"\n{'='*60}")
                print(f"Niche: {niche} | City: {city}")
                print(f"{'='*60}")

                businesses = scrape_yellow_pages(niche, city, MAX_RESULTS_PER_SEARCH)
                print(f"  Found {len(businesses)} businesses after filtering")

                for biz in businesses:
                    try:
                        await process_business(biz, niche, city, pw)
                    except Exception as e:
                        print(f"  [ERROR] Failed processing {biz.get('name', '?')}: {e}")

                # Polite delay between searches
                await asyncio.sleep(3)

    print(f"\n✓ Done. Leads saved to {LEADS_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
