# CLAUDE.md -- morpheme.page

## Project

morpheme.page -- morphological analysis of authority language + semantic compression tools.

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
- `data/` -- JSON data: basis_720.json, decompositions.json, parse_rules.json, filing_analysis.json. Copied to dist/data/.
- `worker/` -- Cloudflare Worker API. Deploys separately via wrangler.
- `python/src/` -- Analysis tools: morpheme_negation.py (VCC engine), word_parser.py, sentence_analyzer.py, semantic_codec.py (string codec), vector_codec.py (lossless embedding codec).
- `python/tools/` -- CLI tools: basis_rewriter.mjs (Node.js rewriter).
- `knowledge/` -- Markdown knowledge base. Feeds the AI system prompt in the worker.

## Key data files

- `data/basis_720.json` -- 720 quantum grammar basis words with role, jurisdiction, negated, complexity, root. Core vocabulary constraint.
- `data/decompositions.json` -- 66 hand-curated morpheme decompositions (prefix/root/suffix with meanings).
- `data/parse_rules.json` -- C.S.S.C.P.S.G.P. sentence structure rules.

## Codec tools

Two compression approaches:
- `python/src/semantic_codec.py` -- String truncation codec (fast, lossy). Encode/decode/interactive.
- `python/src/vector_codec.py` -- Morpheme vector embedding codec (R^128, lossless). Decomposes words via morpheme_negation.py, embeds as vectors, round-trips at controllable compression levels.

## Viz pages

24 self-contained HTML pages in viz/. Each loads data from /data/ via fetch. Key pages:
- `word_decomposer.html` -- Live decomposition engine (any word). Uses 3-tier lookup: curated -> basis_720 -> algorithmic.
- `basis_filter.html` -- 720-word basis analysis with slider (6->720), 8 example texts, rewriter. Hidden div fix: use classList.add('visible') not style.display=''.
- `information_lens.html` -- Information-theoretic view. L0-L5 compression levels, glyph dictionary.
- `semantic_codec.html` -- Bidirectional encode/decode web UI.
- `embedding_space.html` -- 7D text embedding plot with axis controls.
- `codec_docs.html` -- CLI documentation with real output examples.

## CSS gotcha

Never use `element.style.display = ''` to show elements hidden by CSS `#id{display:none}`. That clears the inline style, letting the CSS rule win. Use `classList.add('visible')` with a `.visible{display:block}` rule instead.

## Template variables

build.sh replaces these in dist/index.html:
- `{{DECOMPOSITION_COUNT}}` -- number of entries in data/decompositions.json
- `{{LAST_UPDATED}}` -- current date (YYYY-MM-DD)

## Worker API routes

- `POST /api/ask` -- AI Q&A (Claude Haiku)
- `POST /api/submit` -- Contribution submissions
- `GET /api/browse` -- Query decompositions
- `GET /api/moderate` -- Moderation queue

## Data-First Protocol
When answering questions about data, facts, documents, conversations, or history:
1. **Query the vector DB first.** Use `devctl search "query"` or direct Qdrant search before answering from memory or general knowledge. The DB has 2M+ vectors across legal docs, chats, sessions, and facts.
2. **Know the search scopes.** `devctl search` defaults to ingested docs, court files, facts, and algorithms — AI-assistant chats are excluded (they carry questions and assertions, not ground truth). Use `--claude` for AI chat history (Claude Code, Claude.ai, ChatGPT), `--facts` for the fact registry / case facts, `--algos` for algorithms, `--all` to include everything.
3. **Cite the source.** Include collection name, confidence level, and date when referencing DB results.
4. **Distinguish confidence levels.** A bank statement (verified) is not the same as an email claim (asserted). Never present asserted facts as verified.
5. **Log new facts.** When you discover or confirm a fact during work, log it: `devctl log-fact --fact "..." --source-type X --confidence Y --domain Z`
