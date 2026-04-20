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
It scrapes Google Scholar (profile `DDLTYpAAAAAJ`), uses Claude Haiku to parse
results, matches them to `publications.json` by title similarity, and commits
any changes back — which triggers a new Cloudflare Pages build.

Required secret: `ANTHROPIC_API_KEY` (set in GitHub → Settings → Secrets).

## Deploy

Cloudflare Pages is wired to this repo's `main` branch with build command
`pnpm build` and output directory `dist`. The production domain is
`darlingtree.com` / `www.darlingtree.com`.
