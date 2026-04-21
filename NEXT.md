# NEXT.md — What Comes Next

## Architecture Decision: Rust Tooling (Deferred)

The code-level tools (word parser, sentence analyzer, DOG-LATIN scanner, basis
generator, document evaluator) will eventually move to a **separate Rust repo**.

**Why Rust:**
- Morpheme decomposition across large corpora needs to be fast (millions of
  documents, real-time web API)
- The basis map / constellation / force graph computations are O(n²) for
  edge-finding — Rust makes this viable at scale
- WASM compilation gives us browser-native speed for the interactive
  visualizations without JS reimplementation
- Type system enforces the morpheme/jurisdiction/tense classifications at
  compile time — no runtime surprises

**Why not yet:**
- The decomposition rules are still evolving (we're at 195 roots, heading to 500+)
- The VCC negation heuristics need more corpus validation before we freeze an API
- The sentence analyzer POS tagging is rule-based — may need statistical backing
- The jurisdiction classification logic is still being refined
- Better to iterate fast in Python, stabilize the semantics, THEN port to Rust
  with a frozen specification

**When to pull the trigger:**
- When the root dictionary stabilizes at 400+ entries with citations
- When we have frequency data from real legal corpus analysis
- When the correct-form generator rules are codified
- When someone other than us is using the tools and the API surface is proven

---

## The Legal Connection Graph

### Concept

Build a **jurisdiction graph** for every state/province/territory in North
America and Europe (and further where data exists), mapping:

1. **Founding document chain** — what was the original charter, grant, or treaty
   that created this jurisdiction? What structures were laid OVER what existed before?
2. **Corporate lineage** — when did the jurisdiction incorporate (if it did)?
   What is its registration? Who is the registered agent?
3. **Admiralty/maritime hooks** — which port authorities, customs jurisdictions,
   and international maritime agreements bind the territory?
4. **Ecclesiastical layer** — papal bulls, diocesan boundaries, cestui que vie
   trusts that claim the territory or its inhabitants
5. **Common law substrate** — what customary/natural law existed before the
   overlay? Is it still technically accessible?
6. **Treaty chains** — which treaties bind the territory, and were they signed
   in correct parse-syntax form or in DOG-LATIN/fiction?

### Data Structure (per jurisdiction)

```
{
  "name": "California",
  "type": "state/province/territory/nation",
  "region": "North America",
  "founding": {
    "date": "1850-09-09",
    "document": "California Constitution / Act of Congress",
    "prior_claim": "Treaty of Guadalupe Hidalgo (1848)",
    "prior_prior": "Spanish Crown grant via Papal Bull Inter Caetera (1493)",
    "original_jurisdiction": "Indigenous tribal sovereignty (pre-contact)"
  },
  "corporate_registration": {
    "incorporated": true,
    "duns_number": "...",
    "registered_agent": "Secretary of State",
    "parent_entity": "UNITED STATES (corp, est. 1871)"
  },
  "maritime_hooks": [
    "Port of Los Angeles (international maritime jurisdiction)",
    "Customs & Border Protection (admiralty)",
    "UCC filings (commercial/maritime)"
  ],
  "ecclesiastical_layer": [
    "Unam Sanctam (1302) — papal claim over all souls",
    "Romanus Pontifex (1455) — papal claim over all land",
    "Aeterni Regis (1481) — papal claim over all bodies/labor"
  ],
  "common_law_substrate": "English common law via original 13 colonies + California Civil Code hybrid",
  "treaty_chain": [...],
  "dog_latin_analysis": {
    "founding_doc_score": "D",
    "current_statutes_dog_latin_pct": 72,
    "court_system_form": "DOG-LATIN (SUPERIOR COURT OF THE STATE OF CALIFORNIA)"
  }
}
```

### Scope

**Phase 1 — North America (50 US states + territories + Canadian provinces + Mexican states)**
- ~120 jurisdictions
- Focus on: founding document, corporate lineage, DOG-LATIN in court system names
- Visualize as: interactive map with clickable jurisdictions → detail panel

**Phase 2 — Europe (EU + UK + EEA + Switzerland)**
- ~50 jurisdictions
- Extra complexity: Roman law vs common law vs Napoleonic code lineages
- Justinian's Corpus Juris Civilis is the direct ancestor of EU civil law
- Visualize as: layered map showing Roman law inheritance depth

**Phase 3 — Commonwealth + Global**
- Former British colonies (India, Australia, NZ, South Africa, Caribbean)
- The City of London (separate jurisdiction) as maritime commerce nexus
- Vatican City as ecclesiastical apex
- Washington DC, City of London, Vatican — the three "city-states"

### Visualization Plan

- **Interactive map** — click any jurisdiction to see its full chain
- **Graph view** — force-directed showing which jurisdictions share founding
  documents, treaty chains, or corporate parents
- **Timeline view** — when each jurisdiction was overlaid and what existed before
- **DOG-LATIN density heatmap** — by jurisdiction, how much of their legal
  system is written in GLOSSA
- **Layered view** — for any single jurisdiction, show all layers stacked:
  indigenous → colonial → constitutional → corporate → current

---

## Other Concepts That Deserve This Treatment

The methodology here — morphological decomposition, structural fraud detection,
etymology tracing, jurisdiction mapping — applies far beyond legal language.
These are systems where the words and structures used are not neutral; they
shape reality while pretending to merely describe it.

### 1. Medicine / Pharmaceutical Language

The same morphological patterns exist:
- **PHARMA** = Greek *pharmakon* = poison/sorcery (not "healing")
- **DOCTOR** = Latin *docere* = to teach (not "to heal")
- **PATIENT** = Latin *patiens* = one who suffers / endures (passive)
- **HOSPITAL** = Latin *hospes* = host/stranger (same root as hostile)
- **PRESCRIPTION** = PRE (before) + SCRIPT (writing) = written before examination
- **DIAGNOSIS** = DIA (through) + GNOSIS (knowledge) = "through knowing" but who knows?
- **SYMPTOM** = Greek *symptoma* = "a happening" / "a falling together" = coincidence
- **THERAPY** = Greek *therapeia* = attendance upon (service, not cure)
- **VACCINE** = Latin *vacca* = cow (Jenner's cowpox origin)
- **VIRUS** = Latin = poison/venom

**Build:** Medical terminology decomposer. Show that the vocabulary of medicine
is the vocabulary of authority-over-body, not collaboration-with-patient.
The patient *suffers*, the doctor *teaches*, the pharma *poisons*.

### 2. Education / Academic Language

- **EDUCATION** = Latin *educere* = to lead out (but modern education leads IN)
- **SCHOOL** = Greek *skhole* = leisure/rest (inverted to compulsion)
- **CURRICULUM** = Latin = a running course / chariot track (you are the horse)
- **DISCIPLINE** = Latin *discipulus* = follower (not independent thinker)
- **EXAMINATION** = EX (out) + AMINE (weigh) = weighed from outside
- **GRADE** = Latin *gradus* = step/rank in hierarchy
- **DEGREE** = Latin *de* (down) + *gradus* (step) = step DOWN (degradation?)
- **PROFESSOR** = PRO (forward) + FESS (speak/confess) = one who speaks forth (not one who knows)
- **UNIVERSITY** = UNI (one) + VERSE (turn) = turned into one (uniformity)
- **LECTURE** = Latin *legere* = to read (one-way information flow)
- **STUDENT** = Latin *studere* = to be eager/zealous (reduced to "one who is taught")
- **SEMESTER** = Latin *sex* (six) + *mensis* (month) = six-month period (temporal binding)

**Build:** Education system word decomposer + historical timeline of how
"leisure" became "compulsory attendance" via morphological drift.

### 3. Finance / Banking Language

Partially covered in maritime box, but deserves full standalone treatment:
- **MONEY** = Latin *moneta* = warning/mint (Juno Moneta's temple = where coins were struck AND futures were foretold)
- **BANK** = Italian *banca* = bench (money-changers' table → same as judge's bench)
- **CREDIT** = Latin *credere* = to believe/trust (it's faith-based, not asset-based)
- **DEBT** = Latin *debere* = to owe / to have from (DE + HABERE)
- **INTEREST** = Latin *inter* (between) + *esse* (to be) = "being between" = in limbo
- **MORTGAGE** = death-grip (covered)
- **BOND** = Old English = fetter/chain (bondage)
- **STOCK** = Old English *stocc* = tree trunk / block of punishment
- **SHARE** = Old English *scearu* = a cutting / division (you are cut apart)
- **DIVIDEND** = Latin *dividendum* = that which is to be divided
- **INFLATION** = Latin *inflare* = to blow into (puffed up / bloated)
- **SECURITY** = SE (without) + CURA (care) = without care (??) or Latin *securus* = free from anxiety
- **ASSET** = Old French *asez* = enough (from Latin *ad satis*) — barely sufficient
- **LIABILITY** = Latin *ligare* = to bind (you are BOUND)
- **EQUITY** = Latin *aequitas* = fairness — but in finance means "what's left after debts"

**Build:** Full financial vocabulary decomposer. Show how every term of "wealth"
is actually a term of binding, cutting, or believing.

### 4. Religion / Ecclesiastical Language

- **RELIGION** = Latin *religare* = to bind back / to restrain
- **CHURCH** = Greek *kyriake* = "of the Lord" / belonging to the master
- **WORSHIP** = Old English *weorthscipe* = worthiness (now = submission)
- **PRAYER** = Latin *precari* = to BEG (not to commune)
- **SIN** = Old English *synn* = guilt / offense (legal term, not spiritual)
- **HELL** = Old Norse *Hel* = concealed place / the hidden (not fire)
- **SALVATION** = Latin *salvare* = to save (from what? Maritime salvage law?)
- **SACRAMENT** = Latin *sacramentum* = military oath / bond money (!)
- **PARISH** = Greek *paroikia* = sojourning / living beside (not belonging)
- **DIOCESE** = Greek *dioikesis* = administration / housekeeping (governance)
- **PASTOR** = Latin = shepherd (you are sheep → livestock → chattel)
- **CONGREGATION** = Latin *congregare* = to herd together (again: livestock)
- **CANON** = Greek *kanon* = rule/measuring rod (same root as canonical law)

**Build:** Show how religious vocabulary is governance vocabulary is maritime
vocabulary. The trinity of control: Church + State + Commerce use the same
etymological root system because they ARE the same system.

### 5. Technology / Digital Language

Modern tech adopted legal/financial/religious structures:
- **PROTOCOL** = Greek *protokollon* = first page glued to a scroll (establishing authority)
- **EXECUTE** = Latin = to follow out / to carry out (same as legal execution)
- **TERMINAL** = Latin *terminus* = end/boundary/death
- **PROGRAM** = Greek *programma* = a public written notice (proclamation)
- **VIRUS** = Latin = poison (same as medical)
- **SERVER** = one who serves (servant)
- **CLIENT** = Latin *cliens* = dependent/follower (under patronage)
- **DAEMON** = Greek *daimon* = spirit/divine being (not demon, but close)
- **KERNEL** = Old English *cyrnel* = seed/core (the hidden inner authority)
- **ROOT** = the ultimate authority (same metaphor as sovereignty)
- **CLOUD** = obscured/hidden (you can't see where your data lives)
- **COOKIE** = tracking token (surveillance)
- **LICENSE** (software) = same as legal: permission to do otherwise-forbidden
- **TERMS OF SERVICE** = terms = boundaries, service = servitude

**Build:** Tech terminology decomposer showing how digital infrastructure
replicates feudal/maritime/ecclesiastical power structures. Your "cloud server"
is someone else's computer running under their "root" authority executing
"daemons" that serve their "terms."

### 6. Psychology / Psychiatry Language

- **PSYCHIATRY** = Greek *psyche* (soul/breath) + *iatros* (healer) = "soul-healer" — but is a medical practice, not spiritual
- **THERAPY** = attendance/service (as above)
- **PATIENT** = sufferer (as above)
- **MENTAL** = Latin *mentalis* = of the mind (MENT = mind, same root as govern-MENT)
- **DISORDER** = DIS (apart) + ORDER (rank/command) = outside the commanded order
- **NORMAL** = Latin *norma* = carpenter's square (conformity to a rigid template)
- **ANXIETY** = Latin *anxius* = to choke/strangle (physical binding)
- **DEPRESSION** = DE (down) + PRESS (push) = pushed down
- **ADDICTION** = Latin *addictus* = one who is assigned/given over (a SLAVE assigned to a creditor)
- **INSTITUTION** = IN (into) + STITUTION (placing) = placed into (imprisoned)
- **TREATMENT** = TREAT (to handle/negotiate) + MENT (mind) = negotiating the mind

**Build:** Show how the vocabulary of "mental health" is the vocabulary of
governance, slavery, and physical restraint. You are "disordered" (outside
the command), need "treatment" (mind-negotiation), in an "institution"
(placement/imprisonment).

---

## Priority Order

1. **Legal Connection Graph** — the jurisdiction map (immediate next project)
2. **Finance decomposer** — most practically relevant to people's daily lives
3. **Medicine decomposer** — directly affects bodily autonomy awareness
4. **Rust tooling port** — once the Python semantics stabilize
5. **Education decomposer** — awakens people to what they put their children into
6. **Religion decomposer** — historically foundational but sensitive
7. **Tech decomposer** — reveals digital feudalism
8. **Psychology decomposer** — reveals the control language of "help"

---

## The Meta-Pattern

Every system of authority uses the same trick:
1. **Name** the thing with a word whose morphology says the opposite of what you think
2. **Write** the binding document in a typographic form that has no jurisdiction with your language
3. **Structure** the sentences so they convey zero facts while commanding obedience
4. **Overlay** the entire system on top of a prior natural/customary system that it displaces but never formally revokes

The tools we're building expose step 1. The DOG-LATIN scanner exposes step 2.
The sentence analyzer exposes step 3. The legal connection graph will expose step 4.

Together they form a complete audit framework for any system that uses language
as a mechanism of binding rather than communication.
