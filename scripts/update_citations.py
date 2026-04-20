#!/usr/bin/env python3
"""
Weekly citation updater for publications.json.

Scrapes Google Scholar, uses Claude API to parse, updates src/data/publications.json.
Ported from the original SQLite-based updater for the static site.
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus  # noqa: F401
from urllib.request import Request, urlopen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(REPO_ROOT, "src", "data", "publications.json")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SCHOLAR_PROFILE = os.environ.get("SCHOLAR_PROFILE", "DDLTYpAAAAAJ")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


def fetch_url(url, retries=3):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(3, 8))
            req = Request(url, headers=headers)
            resp = urlopen(req, timeout=30)
            return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:
            log.warning(
                "Fetch attempt %d failed for %s: %s",
                attempt + 1,
                url[:80],
                exc,
            )
            if attempt < retries - 1:
                time.sleep(random.uniform(10, 20))
    return None


def fetch_scholar_profile():
    pages = []
    for start in range(0, 200, 20):
        url = (
            "https://scholar.google.com/citations?user={}&hl=en"
            "&cstart={}&pagesize=20&sortby=pubdate"
        ).format(SCHOLAR_PROFILE, start)
        log.info("Fetching scholar page cstart=%d", start)
        html = fetch_url(url)
        if html is None:
            log.error("Failed to fetch scholar page at cstart=%d", start)
            break
        pages.append(html)
        if (
            "There are no articles" in html
            or html.count('class="gsc_a_tr"') == 0
        ):
            break
    return "\n<!-- PAGE_BREAK -->\n".join(pages)


def call_claude(prompt, max_tokens=4096):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    }
    body = json.dumps(
        {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        resp = urlopen(req, timeout=60)
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]
    except Exception as exc:
        log.error("Claude API call failed: %s", exc)
        return None


def extract_scholar_rows(html):
    rows = []
    parts = html.split('class="gsc_a_tr"')
    for part in parts[1:]:
        title = ""
        citations = 0
        at_start = part.find('class="gsc_a_at"')
        if at_start >= 0:
            tag_end = part.find(">", at_start)
            close_tag = part.find("</a>", tag_end)
            if tag_end >= 0 and close_tag >= 0:
                title = part[tag_end + 1 : close_tag].strip()
        ac_start = part.find('class="gsc_a_ac')
        if ac_start >= 0:
            tag_end = part.find(">", ac_start)
            close_tag = part.find("</a>", tag_end)
            if tag_end >= 0 and close_tag >= 0:
                cite_str = part[tag_end + 1 : close_tag].strip()
                if cite_str.isdigit():
                    citations = int(cite_str)
        if title:
            rows.append("{} ||| {}".format(title, citations))
    return rows


def parse_citations_with_ai(html):
    raw_rows = extract_scholar_rows(html)
    if not raw_rows:
        log.error("No rows extracted from Scholar HTML")
        return None
    log.info("Pre-extracted %d rows from HTML", len(raw_rows))
    prompt = (
        "I have pre-extracted paper data from Google Scholar in the format:\n"
        "TITLE ||| CITATION_COUNT\n\n"
        "Clean up the titles (decode HTML entities) and return a JSON array.\n"
        'Each element: {"title": "clean title", "citations": number}\n\n'
        "Return ONLY the JSON array, nothing else.\n\n"
        "Data:\n" + "\n".join(raw_rows)
    )
    log.info("Calling Claude API to parse citations...")
    result = call_claude(prompt)
    if result is None:
        return None
    try:
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
    except json.JSONDecodeError as exc:
        log.error("Failed to parse Claude response as JSON: %s", exc)
    return None


def score_match(a, b):
    a = a.strip().lower()
    b = b.strip().lower()
    if a == b:
        return 100
    if a in b or b in a:
        return 80
    if len(a) > 40 and a[:40] == b[:40]:
        return 70
    a_words = set(a.split())
    b_words = set(b.split())
    if len(a_words) > 3 and len(b_words) > 3:
        overlap = len(a_words & b_words) / max(len(a_words), len(b_words))
        if overlap > 0.7:
            return int(overlap * 60)
    return 0


def update_publications(citation_data):
    with open(DATA_PATH, "r", encoding="utf-8") as fh:
        entries = json.load(fh)

    updated = 0
    matched_ids = set()

    for paper in citation_data:
        scholar_title = paper.get("title", "")
        try:
            citations = int(paper.get("citations", 0))
        except (TypeError, ValueError):
            continue

        best_id = None
        best_score = 0
        best_title = ""
        for entry in entries:
            if entry["id"] in matched_ids:
                continue
            score = score_match(scholar_title, entry["title"])
            if score > best_score:
                best_score = score
                best_id = entry["id"]
                best_title = entry["title"]

        if best_id is not None and best_score >= 50:
            for entry in entries:
                if entry["id"] == best_id and entry.get("cite", 0) != citations:
                    entry["cite"] = citations
                    log.info(
                        "Updated [%d] %s -> %d (score=%d)",
                        best_id,
                        best_title[:50],
                        citations,
                        best_score,
                    )
                    updated += 1
            matched_ids.add(best_id)

    with open(DATA_PATH, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    total = sum(e.get("cite", 0) for e in entries)
    with_cites = sum(1 for e in entries if e.get("cite", 0) > 0)
    log.info("=== Summary ===")
    log.info("Papers updated: %d / %d", updated, len(entries))
    log.info("Papers with citations: %d", with_cites)
    log.info("Total citations: %d", total)
    return updated, total


def main():
    log.info("=" * 50)
    log.info("Citation update started at %s", datetime.now(timezone.utc).isoformat())

    if not API_KEY:
        log.error("ANTHROPIC_API_KEY not set. Exiting.")
        sys.exit(1)
    if not os.path.exists(DATA_PATH):
        log.error("Data not found at %s", DATA_PATH)
        sys.exit(1)

    html = fetch_scholar_profile()
    if not html:
        log.error("Failed to fetch any Scholar data. Exiting.")
        sys.exit(1)
    log.info("Fetched %d bytes of Scholar HTML", len(html))

    citation_data = parse_citations_with_ai(html)
    if not citation_data:
        log.error("Failed to parse citations. Exiting.")
        sys.exit(1)
    log.info("Parsed %d papers from Scholar", len(citation_data))

    updated, total = update_publications(citation_data)
    log.info("Done. %d updates, %d total citations.", updated, total)


if __name__ == "__main__":
    main()
