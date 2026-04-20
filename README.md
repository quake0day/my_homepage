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

The weekly Scholar citation refresh runs on **PVE LXC 181** (`citation-bot`,
`192.168.68.61`), not GitHub Actions. Google Scholar returns 403 for Azure
datacenter IPs, so the residential-IP home-lab container is the only reliable
runner.

**Container setup** (already deployed):
- Debian 12, 1 vCPU / 512 MB RAM / 4 GB disk, DHCP on vmbr0
- Shallow clone of this repo at `/root/my_homepage`, pulled via SSH deploy key
- `/root/my_homepage/.env` holds `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`
- Cron: `0 3 * * 0 /root/my_homepage/scripts/cron_update.sh >> /var/log/citation-bot.log 2>&1`
- `scripts/cron_update.sh`: pulls, runs updater, commits+pushes only if changed.

**Pipeline:** Scholar scrape → Cloudflare Workers AI (`@cf/moonshotai/kimi-k2.6`)
parses the HTML → fuzzy-match titles against `publications.json` → commit+push.

**Ops:**
```bash
ssh root@192.168.68.61                     # enter container
/root/my_homepage/scripts/cron_update.sh   # manual run
tail -n 50 /var/log/citation-bot.log       # check cron output
```

The `.github/workflows/update-citations.yml` file is kept as a `workflow_dispatch`
fallback only — schedule was disabled because it always 403'd.

## Deploy

Cloudflare Pages is wired to this repo's `main` branch with build command
`pnpm build` and output directory `dist`. The production domain is
`darlingtree.com` / `www.darlingtree.com`.
