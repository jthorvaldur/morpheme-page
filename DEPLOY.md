# DEPLOY.md — Domain Registration, Hosting, and AI Backend Process

## The Stack (Cloudflare-Centric)

Every layer uses Cloudflare's free tier except domain registration. This is the
cheapest viable production stack for running many projects simultaneously.

| Layer | Provider | Cost |
|-------|----------|------|
| Domains | Cloudflare Registrar (at-cost) | ~$10/yr per .com |
| DNS | Cloudflare (free) | $0 |
| Static Hosting | Cloudflare Pages (free) | $0 |
| CDN | Cloudflare (free, unlimited BW) | $0 |
| Backend API | Cloudflare Workers (free tier) | $0 (100k req/day) |
| AI Inference | Claude Haiku API via Worker | ~$1-20/mo depending on traffic |
| Vector DB (if needed) | Context-stuffing in prompt | $0 |
| **Total (10 sites)** | | **~$9-15/mo** |

---

## Step-by-Step Process: New Project Deployment

### 1. Register Domain (~2 minutes)

```bash
# Option A: Cloudflare dashboard
# dashboard.cloudflare.com → Domain Registration → Search → Purchase

# Option B: Porkbun (sometimes $1-2 cheaper, then transfer to CF)
# porkbun.com → Search → Purchase → Transfer to Cloudflare after 60 days
```

**Pricing per TLD:**

| TLD | Cloudflare | Porkbun | Namecheap |
|-----|-----------|---------|-----------|
| .com | $10.11/yr | $9.73/yr | $9.58/yr |
| .xyz | $10.11/yr | $7.95/yr | $1.98 yr1 |
| .dev | $12.00/yr | $11.23/yr | $12.98/yr |
| .io | $33.98/yr | $32.89/yr | $32.98/yr |
| .org | $10.11/yr | $9.73/yr | $9.98/yr |

**Recommendation:** Use .com or .xyz for cost. Avoid .io for anything long-term
(IANA ownership issues). Register through Cloudflare for zero-hassle DNS integration.

### 2. Connect DNS (~1 minute if domain is at Cloudflare)

If domain is already at Cloudflare Registrar, DNS is automatic. Otherwise:

```
# Point nameservers to Cloudflare:
ns1: adalyn.ns.cloudflare.com
ns2: chad.ns.cloudflare.com
# (actual names assigned per domain)
```

### 3. Create Cloudflare Pages Project (~5 minutes)

```bash
# Option A: Git-connected (auto-deploy on push)
# dashboard.cloudflare.com → Pages → Create project → Connect GitHub repo

# Option B: Direct upload (for standalone HTML)
npx wrangler pages deploy ./viz --project-name=quantum-grammar

# Option C: CLI from scratch
npm install -g wrangler
wrangler login
wrangler pages project create my-project-name
wrangler pages deploy ./build --project-name=my-project-name
```

### 4. Bind Custom Domain (~2 minutes)

```
# Dashboard: Pages project → Custom domains → Add domain
# Or via API:
curl -X POST "https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}/domains" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"name":"yourdomain.com"}'
```

Cloudflare auto-provisions SSL certificate. No configuration needed.

### 5. Add AI Backend (Cloudflare Worker) (~15 minutes first time, 5 after)

See architecture section below.

---

## Repeatable Deploy Script

```bash
#!/usr/bin/env bash
# deploy.sh — Deploy a new project with custom domain
# Usage: ./deploy.sh <project-name> <domain> <build-dir>

PROJECT=$1
DOMAIN=$2
BUILD_DIR=$3

if [ -z "$PROJECT" ] || [ -z "$DOMAIN" ] || [ -z "$BUILD_DIR" ]; then
  echo "Usage: ./deploy.sh <project-name> <domain> <build-dir>"
  exit 1
fi

echo "=== Deploying $PROJECT to $DOMAIN ==="

# 1. Deploy static files
echo "[1/3] Uploading to Cloudflare Pages..."
npx wrangler pages deploy "$BUILD_DIR" --project-name="$PROJECT"

# 2. Bind custom domain (if not already bound)
echo "[2/3] Binding $DOMAIN..."
# This is idempotent — safe to run repeatedly
npx wrangler pages project list | grep -q "$PROJECT" && \
  echo "Project exists, binding domain via dashboard or API"

# 3. Verify
echo "[3/3] Verifying..."
echo "Site should be live at: https://$DOMAIN"
echo "Also available at: https://$PROJECT.pages.dev"

echo "=== Done ==="
```

---

## AI Backend Architecture

### Architecture Diagram

```
User's Browser (static HTML)
  │
  ├── Static assets served by Cloudflare Pages (free, global CDN)
  │
  └── fetch('/api/ask', { body: { question, context } })
        │
        Cloudflare Worker (edge function, ~0ms cold start)
        │
        ├── Rate limit check (KV store, per-IP, 10 req/min)
        ├── CORS origin check (only allow your domains)
        ├── Assemble prompt:
        │     System: [FACTS.md content stuffed in, ~15K tokens]
        │     User: [question]
        │
        └── Claude Haiku API call (stream response back)
              │
              └── Streamed to browser via SSE/ReadableStream
```

### Worker Code (api/ask.js)

```javascript
export default {
  async fetch(request, env) {
    // CORS
    const origin = request.headers.get('Origin');
    const allowed = ['https://yourdomain.com', 'https://quantum-grammar.pages.dev'];
    if (!allowed.includes(origin)) {
      return new Response('Forbidden', { status: 403 });
    }

    // Rate limit (10 req/min per IP)
    const ip = request.headers.get('CF-Connecting-IP');
    const key = `rate:${ip}`;
    const count = parseInt(await env.KV.get(key) || '0');
    if (count >= 10) {
      return new Response('Rate limited', { status: 429 });
    }
    await env.KV.put(key, String(count + 1), { expirationTtl: 60 });

    // Parse request
    const { question } = await request.json();
    if (!question || question.length > 500) {
      return new Response('Bad request', { status: 400 });
    }

    // Call Claude Haiku
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 1024,
        system: env.SYSTEM_PROMPT, // FACTS.md content stored in Worker env var
        messages: [{ role: 'user', content: question }],
      }),
    });

    const data = await response.json();
    return new Response(JSON.stringify({
      answer: data.content[0].text,
    }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': origin,
      },
    });
  }
};
```

### Cost Estimates by Traffic

| Daily Users | Queries/mo | AI API Cost/mo | Worker Cost | Total/mo |
|-------------|-----------|----------------|-------------|----------|
| 10 | 900 | ~$0.01 | $0 (free) | **~$0** |
| 100 | 9,000 | ~$0.05 | $0 (free) | **~$0.05** |
| 500 | 45,000 | ~$0.25 | $0 (free) | **~$0.25** |
| 1,000 | 90,000 | ~$0.50 | $0 (free) | **~$0.50** |
| 5,000 | 450,000 | ~$2.50 | $0 (free) | **~$2.50** |
| 10,000 | 900,000 | ~$5.00 | $5 (paid) | **~$10** |

Assumes Claude Haiku at $0.80/MTok in + $4.00/MTok out, 500 tokens in / 1000 out per query.

**At 100 users/day, AI costs are literally pennies.** The domain registration
($10/yr per .com) is your biggest expense.

---

## AI Model Selection Guide

| Need | Model | Cost per query | Quality |
|------|-------|---------------|---------|
| Cheapest possible | Gemini 2.0 Flash | $0.0001 | Good for simple Q&A |
| Best value | Claude Haiku 4.5 | $0.004 | Strong reasoning, fast |
| High quality | Claude Sonnet 4.6 | $0.018 | Best for nuanced analysis |
| Maximum | Claude Opus 4.6 | $0.090 | Overkill for most queries |

**Recommendation:** Start with Haiku. If users complain about answer quality,
upgrade specific query types to Sonnet. Never need Opus for serving user queries.

### Context Strategy: Stuffing vs RAG

Your knowledge base (FACTS.md + word decomposition data) is ~15K tokens.

| Approach | When to use | Cost impact |
|----------|------------|-------------|
| **Context stuffing** | Knowledge base < 30K tokens | +$0.001/query for the extra input |
| **RAG (vector search)** | Knowledge base > 30K tokens | Saves input tokens but adds DB cost |
| **Hybrid** | Large KB, some queries need full context | Best of both |

**At 15K tokens, context stuffing wins.** Just put FACTS.md in the system prompt.
Switch to RAG only when the knowledge base exceeds ~30K tokens (about 20 pages).

---

## Cost Summary: Running 10 Projects

| Item | Monthly | Annual |
|------|---------|--------|
| 10 x .com domains | — | $101 |
| Cloudflare Pages (10 sites) | $0 | $0 |
| Cloudflare DNS (10 domains) | $0 | $0 |
| Cloudflare CDN | $0 | $0 |
| Cloudflare Workers (API) | $0-5 | $0-60 |
| Claude Haiku API (all sites combined) | $1-5 | $12-60 |
| **Total** | **~$9-14/mo** | **~$113-221/yr** |

At scale (50 sites, 1000 users/day across all):

| Item | Monthly | Annual |
|------|---------|--------|
| 50 x .com domains | — | $506 |
| Cloudflare Pages Pro | $20 | $240 |
| Workers Paid | $5 | $60 |
| Claude Haiku API | $5-15 | $60-180 |
| **Total** | **~$50-65/mo** | **~$866-986/yr** |

---

## Checklist: Deploy New Project

```
[ ] Register domain (Cloudflare Registrar, ~$10)
[ ] Domain appears in Cloudflare DNS (automatic if registered there)
[ ] Create Pages project (wrangler pages deploy ./build --project-name=NAME)
[ ] Bind custom domain (Pages → Custom domains → Add)
[ ] SSL auto-provisioned (verify green lock in browser)
[ ] Create Worker for AI backend (if needed)
[ ] Set ANTHROPIC_API_KEY secret on Worker
[ ] Set SYSTEM_PROMPT env var with knowledge base content
[ ] Add rate limiting KV namespace
[ ] Test: static site loads, AI endpoint responds, rate limiting works
[ ] Add to monitoring (Cloudflare Analytics, free)
```

---

## Alternatives Considered (and why not)

| Option | Why not |
|--------|---------|
| Vercel | Hobby tier forbids commercial use. Pro = $20/user/mo. |
| Netlify | 100GB bandwidth cap on free. Less integrated than CF. |
| AWS (S3+CloudFront+Lambda+Route53) | Works but 5x more complex to set up. Route53 = $0.50/domain/mo. |
| GitHub Pages | No serverless functions. No unlimited bandwidth guarantee. |
| Self-hosted AI | $150-350/mo for GPU rental vs $1-5/mo for API. Not worth it under 100K queries/day. |
| Fly.io | Good for persistent backends but overkill for our serverless pattern. |

---

## Future: When to Upgrade

| Trigger | Action |
|---------|--------|
| > 500 builds/month | Cloudflare Pages Pro ($20/mo) |
| > 100K Worker requests/day | Workers Paid ($5/mo) |
| > 30K token knowledge base | Add Cloudflare Vectorize for RAG |
| > 10K users/day total | Consider Sonnet for complex queries, Haiku for simple |
| Need auth/user accounts | Add Cloudflare Access (free for <50 users) |
| Need databases | Cloudflare D1 (SQLite at edge, free tier generous) |
