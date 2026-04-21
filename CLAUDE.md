# CLAUDE.md -- morpheme.page

## Project

morpheme.page -- morphological analysis of authority language.

## Stack

- **Static site**: Cloudflare Pages (built from site/ -> dist/)
- **API**: Cloudflare Worker (worker/src/index.ts)
- **Database**: Cloudflare D1 (schema in worker/src/schema.sql)
- **Rate limiting**: Cloudflare KV

## Build

- `npm run build` runs build.sh, outputs to dist/
- `npm run dev` builds then serves on localhost:3000
- `npm run deploy` builds and deploys site + worker to Cloudflare

## Layout

- `site/` -- Static HTML, CSS, JS. Copied to dist/ by build.
- `viz/` -- Self-contained HTML visualizations. Copied to dist/viz/.
- `data/` -- JSON data: basis_720.json, decompositions.json, parse_rules.json. Copied to dist/data/.
- `worker/` -- Cloudflare Worker API. Deploys separately via wrangler.
- `python/` -- Standalone Python tools (word parser, sentence analyzer, etc.).
- `knowledge/` -- Markdown knowledge base. Feeds the AI system prompt in the worker.

## Template variables

build.sh replaces these in dist/index.html:
- `{{DECOMPOSITION_COUNT}}` -- number of entries in data/decompositions.json
- `{{LAST_UPDATED}}` -- current date (YYYY-MM-DD)

## Worker API routes

- `POST /api/ask` -- AI Q&A (Claude Haiku)
- `POST /api/submit` -- Contribution submissions
- `GET /api/browse` -- Query decompositions
- `GET /api/moderate` -- Moderation queue
