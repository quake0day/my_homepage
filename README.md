# darlingtree.com — Si Chen personal homepage

Static site built with [Astro](https://astro.build/), deployed on Cloudflare Pages.
Publications data lives in `src/data/publications.json` and is refreshed weekly
from Google Scholar by a GitHub Action.

## Local dev

```bash
pnpm install
pnpm dev        # http://localhost:4321
pnpm build      # → dist/
pnpm preview    # serve dist/
```

## Editing content

- Personal info, awards, services, teaching — edit directly in `src/pages/index.astro`.
- Publications — edit `src/data/publications.json`. Each entry uses the schema:

```json
{
  "id": 99,
  "type": 1,                     // 1=Conference, 2=Journal, 3=Preprint, 4=Book Chapter
  "title": "...",
  "author": "...",
  "confname": "...",
  "urlpaper": "https://...",    // optional, main paper link
  "urlslides": "/static/slides/xxx.pdf",
  "urlpdf": "https://arxiv.org/...",
  "urlcite": "...",              // optional
  "video": "",
  "urlaward": "/static/files/...",  // optional, award PDF
  "text": "🏆 Best Paper Award",    // optional, award label
  "cite": 0,
  "place": "Macao, China, Dec 4-7, 2025",
  "year": 2025,
  "cluster": "",
  "hidden": 0                    // 1 to hide behind "Show All"
}
```

- PDFs / slides / images go under `public/static/...` and are served verbatim.

## Citation auto-update

`.github/workflows/update-citations.yml` runs every Sunday at 03:00 UTC.
It scrapes Google Scholar (profile `DDLTYpAAAAAJ`), uses **Cloudflare Workers AI
(Kimi K2.6)** to parse results, matches them to `publications.json` by title
similarity, and commits any changes back — which triggers the next deploy.

Required GitHub secrets (Settings → Secrets and variables → Actions):
- `CLOUDFLARE_API_TOKEN` — API token with **Workers AI Read** permission. Create
  at https://dash.cloudflare.com/profile/api-tokens ("Create Token" → use the
  "Workers AI" template, or custom with `Account.Workers AI: Read`).
- `CLOUDFLARE_ACCOUNT_ID` — your Cloudflare account ID
  (`046c617ae6ff124ea360c3a6117188d5`).

No third-party API key needed — everything runs through Cloudflare.

## Deploy

Cloudflare Pages is wired to this repo's `main` branch with build command
`pnpm build` and output directory `dist`. The production domain is
`darlingtree.com` / `www.darlingtree.com`.
