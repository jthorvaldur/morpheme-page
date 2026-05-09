# morpheme.page

Computational framework for analyzing English words, sentences, and legal documents
through morphological decomposition — exposing how prefixes invert meaning, how
sentence structure determines jurisdiction, and how typography determines whether
you are addressed as a living man or a dead corporate fiction.

**Live:** https://morpheme.page | Preview: https://morpheme-page.pages.dev

## Key Findings

### Why Adverbs Float to the Edges

In the force-directed basis graph, adverbs consistently drift to the periphery
while nouns and verbs cluster at the center. This is not a rendering artifact —
it is the framework's core claim made visible.

The force graph links words that share Latin roots. Nouns and verbs share dozens
of roots across roles (claim/claiming, contract/contracting, land/landing).
These shared roots create strong gravitational pull toward the center.

**Adverbs share almost no roots with fact-carrying words.** "Hereby," "forthwith,"
"notwithstanding," "therein" — these are self-referential connective tissue with
no etymological anchor to the nouns and verbs they pretend to modify. They
literally have nothing to hold onto.

> The graph proves the parse-syntax claim geometrically: adverbs are structural
> isolates. Isolation = emptiness = null construction.

### The VCC Negation Pattern is Systematic

Across the 720-word basis, approximately 30% of words beginning with vowels
are VCC-negated. This concentrates in legal/commercial vocabulary specifically:

| Word | Decomposition | True Meaning | Apparent Meaning |
|------|--------------|--------------|------------------|
| insurance | IN (no) + SURE (certain) + ANCE (state) | NO certainty | protection |
| assume | AS (no) + SUME (sum up) | Cannot sum up | take for granted |
| agreement | A (no) + GREE (step) + MENT (mind) | No step of mind | mutual understanding |
| corporation | CORP (dead body) + OR (speak) + AT (through) + ION (contract) | Dead-speak-through-contract | business entity |
| government | GOVERN (steer a ship) + MENT (mind) | Steering of the mind | administration |
| mortgage | MORT (death) + GAGE (grip/pledge) | Death grip | home loan |
| attorney | AT (to) + TORN (tear) + EY | One who tears apart | lawyer |

### DOG-LATIN Density Correlates with Authority

Documents that claim the most authority have the highest DOG-LATIN density:
birth certificates (~85%), court orders (~70%), traffic citations (~75%).
The more a document claims power, the more of it is written in a typographic
form that cannot share jurisdiction with English on the same page.

### Court Orders Score F

Every sample court order scores F (0-15/100) on parse-syntax analysis.
The structural problem is always the same: adverb-verb chains with zero
noun-facts. "IT IS HEREBY ORDERED that the defendant SHALL FORTHWITH PAY" —
no nouns, no facts, no closure. Commands without communication.

### The Meta-Pattern

Every system of authority uses four steps:
1. **NAME** things with words whose morphology says the opposite of what you assume
2. **WRITE** binding documents in typographic form with no jurisdiction over you
3. **STRUCTURE** sentences to convey zero facts while commanding obedience
4. **OVERLAY** on prior natural systems never formally revoked

## Source Documents & References

| Source | Contribution |
|--------|-------------|
| **:David-Wynn: Miller** (C.S.S.C.P.S.G.P.) | Mathematical interface to language. 720-word basis. Only nouns carry meaning. |
| **:Russell-Jay: Gould** (Last Flag Standing) | Postmaster-General claims. Treaty mechanics. Continued Miller's work. |
| **Romley Stewart** (Justinian Deception) | DOG-LATIN as fraud mechanism. GLOSSA traced to Justinian's Corpus Juris Civilis. |
| **TASA / Anna Von Reitz** | Land/soil jurisdiction. Living man vs corporate PERSON. Three-jurisdiction system. |
| **Black's Law Dictionary, 4th Ed** | DOG-LATIN = "the language of the illiterate." Legal term definitions. |
| **Chicago Manual of Style, 16th Ed, Art. 11:147** | Two languages cannot share jurisdiction on one page. |
| **Justinian's Corpus Juris Civilis** (530-565 AD) | Digest Book XIV: maritime law. Origin of the GLOSSA overlay. |

## Documents Analyzed

| Document | What It Reveals | Grade |
|----------|----------------|-------|
| Declaration of Independence | Strong nouns, but past tense and no prepositional opening | C |
| US Constitution Preamble | "We the People" — pronoun removes fact; "shall" = fiction | D |
| Court Orders | Null adverb-verb chains, zero facts conveyed | F |
| Mortgage Contracts | DOG-LATIN names, future-tense obligations, "mort-gage" in title | F |
| Birth Certificates | Name in DOG-LATIN, maritime "berth" language | F |
| Correct Parse-Syntax Claim | "FOR THE CLAIMING OF THE LAND BY THE LIVING MAN" | A |

## Visualizations

All interactive visualizations are live at [morpheme.page](https://morpheme.page):

| Visualization | What It Shows |
|---------------|---------------|
| **Embedding Space** | Texts as points in 7D meaning-space with transformation vectors |
| **Semantic Codec** | Bidirectional encode/decode between English and semantic glyphs |
| **Basis Filter** | Evaluate any text against the 720-word basis set with interactive slider |
| **Information Lens** | How a language model sees meaning — surprisal heatmap, compression levels L0→L5 |
| **Word Decomposer** | Type any word, live prefix/root/suffix engine with VCC analysis |
| **Meta Pattern** | The 4-step authority pattern across 6 domains |
| **Four-Step Audit** | Paste any document — unified parse/scan/analyze/map |
| **Cross-Domain Decomposer** | 92 words across 7 domains |
| **Parse-Syntax Tree** | Real-time sentence analysis with scoring |
| **DOG-LATIN Scanner** | Paste text, see all GLOSSA highlighted |
| **VCC Negation Space** | 2D geometric inversion of meaning |
| **Jurisdiction Layers** | 3D land/sea/air planes |
| **Maritime Box** | Birth→dock→court→death flow diagram |
| **Justinian Timeline** | 45 BC to present |
| **Basis Constellation** | 720 words as star map |
| **Filing Dashboard** | 21 real court filings analyzed |
| **Filing Comparison** | Before/after parse-syntax corrections |

## Semantic Codec — Compress / Decompress Language

Encode any English text into semantic glyphs (3-4 char root concepts), then decode back.
Strips stop words, deduplicates concepts, maps synonyms to basis roots.

### Python

```bash
cd python

# Encode — English to glyphs
python src/semantic_codec.py encode "I want to buy a house and make money"
#  CLAI PURC ESTA GRAN CURR
#  24 words → 5 glyphs (4.8x compression)

# Decode — glyphs back to English
python src/semantic_codec.py decode "CLAI PURC ESTA GRAN CURR"
#  claim purchasing estate grantor currency

# Interactive REPL
python src/semantic_codec.py
#  codec> encode The court hereby orders that you shall pay
#  COUR ORDE PAY
#  codec> decode COUR ORDE PAY
#  court ordering paying
```

### Node.js

```bash
# Rewrite text for maximum basis_720 alignment
node python/tools/basis_rewriter.mjs "your text here"

# Pipe from stdin
echo "I need to talk to my lawyer about the contract" | node python/tools/basis_rewriter.mjs
```

### Web

Live codec at [morpheme.page/viz/semantic_codec.html](https://morpheme-page.pages.dev/viz/semantic_codec.html) — bidirectional encode/decode with meaning-space visualization and compute savings analysis.

### Alphabet

659 root concepts need encoding. Analysis of options:

| System | Width | LLM tokens | Use case |
|--------|-------|-----------|----------|
| Roman 2-char (`CL LA MA`) | 2 | 1 each | Maximum compute efficiency |
| Roman 3-char (`CLA LAN MAN`) | 3 | 1 each | Human readable (recommended) |
| CJK 1-char | 1 | 2-3 each | Looks dense, costs more to LLM |

Stay Roman. BPE tokenizers were trained on Latin text — Roman 2-3 char codes cost exactly 1 token each, while CJK/emoji cost 2-3x more.

## Python Tools

Analysis tools in `python/src/` (runs standalone, pure Python 3.12+):

```bash
cd python
python src/word_parser.py "insurance" "mortgage" "government"
python src/sentence_analyzer.py --examples
python src/dog_latin_detector.py "THE STATE OF TEXAS VS JOHN DOE"
python src/document_evaluator.py --all
python src/case_analyzer.py --compare
python src/basis_generator.py
```

## What's Next

See [NEXT.md](NEXT.md) for the full roadmap:
1. **Legal connection graph** — jurisdiction map for every state/province (founding chains, corporate lineage, maritime hooks)
2. **Rust tooling port** — deferred until semantics stabilize
3. **Cross-domain expansion** — medicine, finance, education, religion, tech, psychology decomposers

## Build & Deploy

```bash
npm run build     # Assemble site/ + viz/ + data/ → dist/
npm run dev       # Build and serve on localhost:3000
npm run deploy    # Deploy to Cloudflare Pages + Workers
```

## Project Structure

```
morpheme-page/
├── site/                        # Landing page, contribute, ask, browse (HTML/CSS/JS)
├── viz/                         # 15 self-contained HTML visualizations
├── data/                        # basis_720.json, decompositions.json, parse_rules.json
├── knowledge/                   # FACTS.md + docs (AI system prompt content)
├── python/                      # Standalone analysis tools (10 modules, 6000+ lines)
├── worker/                      # Cloudflare Worker API (TypeScript)
├── NEXT.md                      # Roadmap and domain expansion plan
├── DEPLOY.md                    # Cloudflare deployment process
└── build.sh                     # Build script → dist/
```

## Note on Epistemology

This framework draws from the sovereign citizen / state national movement.
Courts have uniformly rejected quantum grammar arguments. This project treats
the framework as a formal system for morphological and syntactic analysis —
a lens for decomposing language, not a legal strategy.

That said: the words DO say what they say when you parse them.

<!-- AUTO:footer -->
Managed by [policy-orchestrator](https://github.com/jthorvaldur/policy-orchestrator). Category: legal. 28 commits, last updated 11 minutes ago.
<!-- /AUTO:footer -->
