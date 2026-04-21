# morpheme.page

Morphological analysis of authority language. Decompose words into prefix, root, and suffix to reveal structural meaning hidden by convention.

## Build

```bash
npm run build
```

Compiles site/, viz/, and data/ into dist/.

## Develop

```bash
npm run dev
```

Builds and serves on localhost:3000.

## Deploy

```bash
npm run deploy
```

Deploys the static site to Cloudflare Pages and the API worker to Cloudflare Workers. Requires a Cloudflare account and `wrangler` authentication.

## Structure

```
site/           Static site (HTML, CSS, JS) -> dist/
viz/            Self-contained HTML visualizations -> dist/viz/
data/           JSON data files (basis, decompositions, rules) -> dist/data/
worker/         Cloudflare Worker API (TypeScript)
python/         Standalone Python analysis tools
knowledge/      Markdown knowledge base for AI system prompts
```

See [DEPLOY.md](DEPLOY.md) for full infrastructure documentation.
