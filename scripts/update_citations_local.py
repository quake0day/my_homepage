#!/usr/bin/env python3
"""Run the citation update WITHOUT Cloudflare Workers AI.

The only thing the Workers AI step did was decode HTML entities in the
pre-extracted Scholar rows -> we do that locally with html.unescape().
All scraping + title-matching logic is reused verbatim from
update_citations.py, so results match the weekly bot.

Also parses the profile's summary table for h-index / i10-index and prints
them so index.astro lines 43-44 can be updated by hand if they changed.

Run:  python3 scripts/update_citations_local.py
"""
import html as _html
import re

import update_citations as uc


def parse_citations_local(html):
    rows = uc.extract_scholar_rows(html)
    if not rows:
        uc.log.error("No rows extracted from Scholar HTML")
        return None
    uc.log.info("Pre-extracted %d rows from HTML", len(rows))
    out = []
    for row in rows:
        title, _, cites = row.rpartition(" ||| ")
        try:
            c = int(cites.strip())
        except ValueError:
            c = 0
        out.append({"title": _html.unescape(title).strip(), "citations": c})
    return out


def parse_summary_metrics(html):
    """Extract All-time citations / h-index / i10-index from gsc_rsb_st."""
    nums = re.findall(r'class="gsc_rsb_std">(\d+)</td>', html)
    # order: citations(all), citations(since), h(all), h(since), i10(all), i10(since)
    if len(nums) >= 5:
        return {
            "citations_all": int(nums[0]),
            "h_index": int(nums[2]),
            "i10_index": int(nums[4]),
        }
    return None


def main():
    uc.parse_citations_with_ai = parse_citations_local  # bypass Workers AI
    html = uc.fetch_scholar_profile()
    if not html:
        uc.log.error("Failed to fetch any Scholar data. Exiting.")
        raise SystemExit(1)
    uc.log.info("Fetched %d bytes of Scholar HTML", len(html))

    metrics = parse_summary_metrics(html)

    data = parse_citations_local(html)
    uc.log.info("Parsed %d papers from Scholar", len(data))
    updated, total = uc.update_publications(data)
    uc.log.info("Done. %d updates, %d total citations (summed onto JSON).", updated, total)

    if metrics:
        uc.log.info(
            "Scholar profile metrics -> citations(all)=%d  h-index=%d  i10-index=%d",
            metrics["citations_all"], metrics["h_index"], metrics["i10_index"],
        )
        uc.log.info("If changed, update src/pages/index.astro lines 43-44 (hIndex / i10Index).")
    else:
        uc.log.warning("Could not parse h-index/i10-index summary table.")


if __name__ == "__main__":
    main()
