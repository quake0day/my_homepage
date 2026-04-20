# R2 large-asset backup

Files over CF Pages' 25 MiB per-file limit live in the **`darlingtree-assets`**
R2 bucket (kept in git as well, but stripped from `dist/` before deploy).

**Public r2.dev base URL:**
`https://pub-1c5db85189b141deba911473ca303106.r2.dev`

| File | Size | R2 URL |
|---|---|---|
| `files/2025AC-Brochure.pdf` | 27.6 MB | [link](https://pub-1c5db85189b141deba911473ca303106.r2.dev/files/2025AC-Brochure.pdf) |
| `files/ieeetaleRAG_presentation_Arial.pptx` | 41.2 MB | [link](https://pub-1c5db85189b141deba911473ca303106.r2.dev/files/ieeetaleRAG_presentation_Arial.pptx) |
| `slides/ieeetaleRAG_presentation_Arial.pptx` | 41.2 MB | [link](https://pub-1c5db85189b141deba911473ca303106.r2.dev/slides/ieeetaleRAG_presentation_Arial.pptx) |

## Why R2

Cloudflare Pages rejects any single file > 25 MiB during upload. Rather than
delete these files, they stay in git `public/static/...` for local access and
backup, and are also mirrored to R2 for public URL access. The `pnpm run publish:cf`
script deletes files >24 MiB from `dist/` right before `wrangler pages deploy`
so the upload succeeds.

## Adding more large files

```bash
# upload to R2
wrangler r2 object put "darlingtree-assets/files/foo.pdf" \
  --file=public/static/files/foo.pdf \
  --content-type=application/pdf --remote
```

## Managing the bucket

```bash
wrangler r2 bucket info darlingtree-assets
wrangler r2 object delete darlingtree-assets/path/to/file --remote
```
