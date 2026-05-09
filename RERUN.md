# RERUN.md — How to Rebuild Everything from Source

## The Current Problem

Each visualization has **hardcoded inline data**. When the Python source
(morpheme_negation.py) is updated with new roots, prefixes, or decompositions,
the viz files don't change. There are 5+ copies of decomposition data across
the codebase, all potentially out of sync.

## The Fix: Single Source of Truth Pipeline

### Step 1: Canonical Data Export

All data flows from Python → JSON → HTML.

```bash
# Re-export all data from Python source
python python/tools/export_all.py
```

This script (to be created) does:
1. Export `KNOWN_DECOMPOSITIONS` → `data/decompositions.json` (currently 66 entries)
2. Export `PREFIXES` dict → `data/prefixes.json` (56 entries)
3. Export `ROOTS` dict → `data/roots.json` (195 entries)
4. Export `SUFFIXES` dict → `data/suffixes.json` (52 entries)
5. Regenerate `data/basis_720.json` from `basis_generator.py`
6. Export cross-domain decompositions → `data/domains.json` (for domain_decomposer)

### Step 2: Viz Files Load Data at Runtime

Convert each viz file from inline data to `fetch()`:

**Before (current):**
```javascript
const WORDS = { insurance: { prefix: "in", ... }, ... }; // 44 entries hardcoded
```

**After:**
```javascript
let WORDS = {};
fetch('/data/decompositions.json')
  .then(r => r.json())
  .then(data => { WORDS = data; init(); });
```

Files that need conversion:
- `viz/word_decomposer.html` — loads decompositions.json
- `viz/domain_decomposer.html` — loads domains.json
- `viz/vcc_negation_space.html` — loads decompositions.json (negated subset)
- `viz/basis_constellation.html` — loads basis_720.json
- `viz/basis_map.html` — loads basis_720.json
- `viz/four_step_audit.html` — loads decompositions.json
- `viz/parse_syntax_tree.html` — loads parse_rules.json
- `site/index.html` — hero decomposer loads decompositions.json
- `site/browse.html` — already loads decompositions.json (correct)

Files that DON'T need conversion (pure concept visualizations):
- `viz/maritime_box_flow.html` — static flow diagram
- `viz/jurisdiction_layers.html` — static 3D layers
- `viz/justinian_timeline.html` — static timeline
- `viz/meta_pattern.html` — static concept diagram
- `viz/dog_latin_scanner.html` — rule-based, no word data
- `viz/filing_dashboard.html` — uses filing_analysis.json (separate)
- `viz/filing_comparison.html` — static comparison
- `viz/summary.html` — static text
- `viz/about.html` — static text
- `viz/never_be_you.html` — static text
- `viz/case_study_structural.html` — static text

### Step 3: Build Pipeline

```bash
npm run rebuild    # Full pipeline:
                   # 1. python python/tools/export_all.py  (regenerate all JSON)
                   # 2. bash build.sh                       (assemble dist/)
                   # 3. npx wrangler pages deploy dist      (deploy)
```

Add to `package.json`:
```json
"rebuild": "python python/tools/export_all.py && bash build.sh",
"rebuild:deploy": "npm run rebuild && npm run deploy:site"
```

### Step 4: Embedding Pipeline (for WhatsApp, contacts, documents)

The WhatsApp data, contact data, and legal documents need a separate
processing pipeline that feeds into the visualization system.

**Data sources:**
- WhatsApp chat: `~/div_legal/data/WhatsApp Chat - Party A.zip`
  - 8,591 messages, 98,877 words, 1,972 attachments
  - Needs: extract _chat.txt → parse → aggregate → JSON
- Contacts: `~/projects/jthorvaldur.github.io/r/contacts/` (encrypted)
  - Needs: decrypt → parse → JSON
- Legal filings: `~/div_legal/FILING_*/` (22 PDFs)
  - Already processed → `data/filing_analysis.json`
- IPFS scrolls: `~/projects/party_a/` (17 files)
  - Already mapped → needs JSON export

**Processing script: `python/tools/process_comms.py`**

```python
# 1. Extract WhatsApp chat → data/whatsapp_party_a.json
#    - Daily aggregates (messages, words, topics per day)
#    - Hourly heatmap data
#    - Cumulative word counts
#    - Topic classification per message
#    - Attachment inventory

# 2. Extract scroll metadata → data/scroll_network.json
#    - Node/link format for force graph
#    - Author connections
#    - Temporal sequence

# 3. Generate communication map → viz/maps/
#    - All visualizations load from data/ JSONs
```

### Step 5: Dependency Map

```
Python Source (morpheme_negation.py)
  │
  ├── export_all.py ──→ data/decompositions.json
  │                 ──→ data/prefixes.json
  │                 ──→ data/roots.json
  │                 ──→ data/suffixes.json
  │                 ──→ data/basis_720.json
  │                 ──→ data/domains.json
  │
  ├── process_comms.py ──→ data/whatsapp_party_a.json
  │                    ──→ data/scroll_network.json
  │
  └── batch_evaluate.py ──→ data/filing_analysis.json

Data JSONs
  │
  ├── viz/*.html (fetch at runtime)
  ├── site/index.html (hero decomposer)
  ├── site/browse.html (dictionary)
  └── viz/maps/*.html (communication maps)

build.sh
  │
  └── dist/ (site + viz + data) → Cloudflare Pages
```

## How to Rerun Everything Now

```bash
cd ~/projects/morpheme-page

# 1. Regenerate core data from Python
python -c "
import sys, json
sys.path.insert(0, 'python/src')
from morpheme_negation import KNOWN_DECOMPOSITIONS, PREFIXES, ROOTS, SUFFIXES
from basis_generator import generate_basis

# Decompositions
entries = []
for word, data in sorted(KNOWN_DECOMPOSITIONS.items()):
    entries.append({**data, 'word': word, 'domain': 'legal', 'status': 'approved'})
json.dump(entries, open('data/decompositions.json','w'), indent=2)
print(f'decompositions.json: {len(entries)}')

# Prefixes, roots, suffixes
json.dump(PREFIXES, open('data/prefixes.json','w'), indent=2)
json.dump(ROOTS, open('data/roots.json','w'), indent=2)
json.dump(SUFFIXES, open('data/suffixes.json','w'), indent=2)
print(f'prefixes: {len(PREFIXES)}, roots: {len(ROOTS)}, suffixes: {len(SUFFIXES)}')

# Basis
basis = generate_basis()
json.dump(basis, open('data/basis_720.json','w'), indent=2)
print(f'basis_720.json: {len(basis)}')
"

# 2. Process WhatsApp data
python python/tools/process_comms.py  # (when created)

# 3. Build
npm run build

# 4. Deploy
npm run deploy:site
```

## Priority Order for Conversion

1. **Create export_all.py** — canonical data export from Python
2. **Convert site/index.html** hero decomposer to fetch
3. **Convert viz/word_decomposer.html** — most-used tool
4. **Convert viz/domain_decomposer.html** — 92 inline entries
5. **Convert viz/basis_constellation.html** — 720 inline entries
6. **Convert viz/basis_map.html** — already loads from JSON (verify)
7. **Create process_comms.py** — WhatsApp + scroll pipeline
8. **Convert remaining viz files** — vcc_negation, four_step_audit, parse_syntax
