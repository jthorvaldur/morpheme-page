#!/usr/bin/env python3
"""
basis_map_viz.py -- Generate an interactive HTML visualization of the 720-word basis set.

Reads data/basis_720.json (or generates inline sample if not found).
Outputs a self-contained HTML file to data/basis_map.html with:
  - Dark background (#0a0a0a), monospace font
  - Force-directed graph (D3.js from CDN) showing all 720 words
  - Nodes colored by sentence role
  - Node size by morphological complexity
  - Edges connecting words that share roots
  - Click to see word decomposition
  - Filter by role, jurisdiction, negation status
  - Search box
  - Stats panel

Usage:
    python src/basis_map_viz.py
"""

import sys
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASIS_PATH = PROJECT_ROOT / "data" / "basis_720.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "basis_map.html"

# ── VCC Negation Prefixes ────────────────────────────────────────────────────

VCC_PREFIXES = {
    "in": "no", "im": "no", "il": "no", "ir": "no",
    "as": "no", "a": "no/without", "o": "no",
    "un": "not/reverse", "ab": "away from", "ex": "out of",
    "en": "into", "em": "into",
}

VOWELS = set("aeiou")


def is_vcc_negated(word: str) -> bool:
    """Check if a word begins with a VCC negation prefix."""
    w = word.lower()
    for prefix in sorted(VCC_PREFIXES, key=len, reverse=True):
        if w.startswith(prefix) and len(w) > len(prefix) + 1:
            after = w[len(prefix)]
            if after not in VOWELS:
                return True
    return False


def morpheme_count(word: str) -> int:
    """Estimate morphological complexity by syllable-like heuristic."""
    w = word.lower()
    count = 0
    prev_vowel = False
    for ch in w:
        if ch in VOWELS:
            if not prev_vowel:
                count += 1
            prev_vowel = True
        else:
            prev_vowel = False
    return max(count, 1)


# ── 720-Word Basis Generator ─────────────────────────────────────────────────

# Representative words for each of the six parse-syntax roles and three
# jurisdictions, drawn from the C.S.S.C.P.S.G.P. and maritime/legal lexicon.

ROLE_WORDS = {
    "preposition": [
        "for", "by", "of", "with", "in", "against", "from", "to", "at",
        "through", "upon", "into", "within", "without", "between", "among",
        "before", "after", "under", "over", "across", "beyond", "during",
        "about", "above", "below", "behind", "beside", "near", "toward",
        "onto", "throughout", "since", "until", "past", "around", "along",
        "beneath", "outside", "inside", "except", "per", "via", "despite",
        "amid", "amongst", "atop", "concerning", "regarding", "alongside",
        "versus", "notwithstanding", "pending", "barring", "aboard", "like",
        "off", "out", "up", "down", "opposite", "unlike",
    ],
    "article": [
        "the", "a", "an", "this", "that", "these", "those", "every", "each",
        "all", "some", "any", "no", "my", "your", "his", "her", "its", "our",
        "their", "many", "few", "several", "both", "such", "other", "another",
        "either", "neither", "enough", "more", "most", "less", "least", "much",
        "certain", "own", "same", "next", "last", "first", "second", "third",
        "whole", "half", "double", "triple", "one", "two", "three", "four",
        "five", "six", "seven", "eight", "nine", "ten", "hundred", "thousand",
        "null", "zero", "sole", "only",
    ],
    "adjective": [
        "lawful", "legal", "living", "dead", "corporate", "sovereign",
        "maritime", "common", "natural", "civil", "criminal", "statutory",
        "constitutional", "judicial", "private", "public", "foreign",
        "domestic", "federal", "territorial", "municipal", "original",
        "certified", "registered", "bonded", "secured", "unsecured",
        "fraudulent", "fictitious", "correct", "incorrect", "valid",
        "invalid", "binding", "voluntary", "involuntary", "express",
        "implied", "written", "oral", "ancient", "modern", "current",
        "prior", "subsequent", "superior", "inferior", "equitable",
        "admiralty", "ecclesiastical", "commercial", "military", "royal",
        "imperial", "papal", "canonical", "customary", "traditional",
        "fundamental", "inherent", "inalienable", "absolute", "conditional",
        "provisional", "temporary", "permanent", "perpetual", "executory",
        "contractual", "fiduciary", "beneficial", "nominal", "actual",
        "constructive", "presumptive", "apparent", "real", "personal",
        "tangible", "intangible", "material", "immaterial", "substantial",
        "procedural", "substantive", "remedial", "punitive", "compensatory",
        "declaratory", "injunctive", "mandatory", "discretionary", "penal",
        "fiscal", "monetary", "pecuniary", "proprietary", "possessory",
        "testamentary", "intestate", "probate", "marital", "parental",
        "filial", "collateral", "direct", "indirect", "primary",
        "secondary", "tertiary", "quantum", "morphological", "syntactic",
        "grammatical", "prepositional", "adverbial", "verbal", "nominal",
        "gerundive", "participial", "infinitive", "imperative", "indicative",
        "subjunctive", "operative", "dispositive", "performative",
    ],
    "noun": [
        "man", "woman", "child", "land", "soil", "water", "sea", "ship",
        "vessel", "dock", "port", "harbor", "berth", "canal", "current",
        "bank", "currency", "capital", "mortgage", "bond", "surety",
        "certificate", "title", "claim", "right", "duty", "obligation",
        "contract", "agreement", "trust", "estate", "property", "chattel",
        "person", "citizen", "subject", "sovereign", "king", "court",
        "bench", "bar", "judge", "jury", "attorney", "lawyer", "counsel",
        "plaintiff", "defendant", "witness", "evidence", "fact", "opinion",
        "law", "statute", "code", "regulation", "ordinance", "decree",
        "order", "warrant", "summons", "complaint", "indictment", "charge",
        "sentence", "verdict", "judgment", "appeal", "motion", "petition",
        "brief", "record", "document", "instrument", "deed", "will",
        "testament", "probate", "executor", "administrator", "guardian",
        "ward", "heir", "beneficiary", "grantor", "grantee", "lessor",
        "lessee", "mortgagor", "mortgagee", "creditor", "debtor", "lien",
        "pledge", "security", "collateral", "insurance", "premium",
        "policy", "underwriter", "risk", "liability", "damage", "remedy",
        "relief", "restitution", "compensation", "penalty", "fine",
        "forfeiture", "seizure", "arrest", "detention", "imprisonment",
        "bail", "parole", "probation", "acquittal", "conviction",
        "execution", "discharge", "release", "freedom", "liberty",
        "jurisdiction", "venue", "forum", "tribunal", "commission",
        "authority", "power", "dominion", "sovereignty", "flag", "seal",
        "stamp", "signature", "name", "identity", "birth", "death",
        "marriage", "divorce", "adoption", "corporation", "company",
        "partnership", "association", "foundation", "treasury", "revenue",
        "tax", "assessment", "levy", "duty", "tariff", "toll", "fee",
        "payment", "consideration", "value", "exchange", "trade",
        "commerce", "merchant", "cargo", "freight", "bill", "note",
        "draft", "check", "voucher", "receipt", "invoice", "account",
        "ledger", "register", "registry", "archive", "glossa", "digest",
        "codex", "institute", "novella", "corpus", "body", "head",
        "hand", "foot", "tongue", "eye", "ear", "mind", "soul", "spirit",
        "flesh", "blood", "bone", "heart", "voice", "sound", "word",
        "language", "grammar", "syntax", "parse", "morpheme", "prefix",
        "root", "suffix", "vowel", "consonant", "syllable", "sentence",
        "clause", "phrase", "noun", "verb", "adverb", "preposition",
        "article", "adjective", "pronoun", "conjunction", "interjection",
    ],
    "verb": [
        "claiming", "conveying", "granting", "securing", "binding",
        "contracting", "agreeing", "declaring", "certifying", "registering",
        "recording", "filing", "noticing", "serving", "appearing",
        "standing", "moving", "petitioning", "appealing", "objecting",
        "sustaining", "overruling", "ordering", "directing", "commanding",
        "executing", "enforcing", "compelling", "requiring", "mandating",
        "permitting", "authorizing", "licensing", "prohibiting", "barring",
        "enjoining", "restraining", "seizing", "arresting", "detaining",
        "imprisoning", "releasing", "discharging", "acquitting", "convicting",
        "sentencing", "fining", "forfeiting", "levying", "assessing",
        "taxing", "paying", "compensating", "indemnifying", "subrogating",
        "insuring", "underwriting", "bonding", "pledging", "mortgaging",
        "encumbering", "liening", "attaching", "garnishing", "foreclosing",
        "redeeming", "conveying", "transferring", "assigning", "delegating",
        "devising", "bequeathing", "inheriting", "distributing",
        "administering", "managing", "governing", "ruling", "legislating",
        "adjudicating", "arbitrating", "mediating", "negotiating",
        "settling", "compromising", "waiving", "estopping", "ratifying",
        "confirming", "validating", "voiding", "annulling", "rescinding",
        "revoking", "amending", "modifying", "supplementing", "replacing",
        "superseding", "repealing", "abrogating", "incorporating",
        "chartering", "organizing", "dissolving", "liquidating",
        "bankrupting", "restructuring", "merging", "acquiring", "divesting",
        "trading", "exchanging", "purchasing", "selling", "leasing",
        "renting", "borrowing", "lending", "investing", "profiting",
        "losing", "defaulting", "breaching", "violating", "infringing",
        "trespassing", "encroaching", "damaging", "injuring", "harming",
        "defrauding", "deceiving", "misrepresenting", "concealing",
        "disclosing", "revealing", "publishing", "communicating",
        "notifying", "informing", "instructing", "advising", "counseling",
        "representing", "advocating", "defending", "prosecuting",
    ],
    "adverb": [
        "hereby", "herein", "hereof", "hereto", "hereafter", "herewith",
        "thereby", "therein", "thereof", "thereto", "thereafter", "therewith",
        "whereby", "wherein", "whereof", "whereto", "whereafter",
        "forthwith", "immediately", "promptly", "duly", "properly",
        "lawfully", "legally", "unlawfully", "illegally", "voluntarily",
        "involuntarily", "knowingly", "willfully", "intentionally",
        "negligently", "recklessly", "fraudulently", "maliciously",
        "expressly", "impliedly", "constructively", "presumptively",
        "actually", "nominally", "substantially", "materially",
        "procedurally", "summarily", "jointly", "severally", "individually",
        "collectively", "personally", "officially", "privately", "publicly",
        "domestically", "internationally", "federally", "locally",
        "originally", "finally", "provisionally", "permanently",
        "temporarily", "conditionally", "unconditionally", "absolutely",
        "relatively", "partially", "wholly", "entirely", "fully",
        "completely", "specifically", "generally", "particularly",
        "exclusively", "inclusively", "respectively", "mutually",
        "reciprocally", "simultaneously", "subsequently", "previously",
        "currently", "presently", "formerly", "henceforth", "heretofore",
        "notwithstanding", "nevertheless", "moreover", "furthermore",
        "additionally", "alternatively", "otherwise", "accordingly",
        "consequently", "therefore", "thus", "hence", "now", "then",
        "always", "never", "often", "seldom", "rarely", "usually",
        "sometimes", "already", "still", "yet", "also", "only",
        "merely", "simply", "directly", "indirectly",
    ],
}

JURISDICTIONS = ["land/soil", "sea/water", "air/ether"]

# Words strongly associated with each jurisdiction
JURISDICTION_HINTS = {
    "land/soil": {
        "man", "woman", "child", "land", "soil", "claim", "right", "freedom",
        "liberty", "sovereign", "lawful", "common", "natural", "customary",
        "traditional", "inherent", "inalienable", "living", "fundamental",
        "claiming", "standing", "lawfully", "for", "by", "of", "with",
    },
    "sea/water": {
        "ship", "vessel", "dock", "port", "harbor", "berth", "canal",
        "current", "bank", "currency", "capital", "mortgage", "bond",
        "insurance", "court", "bench", "bar", "attorney", "corporation",
        "maritime", "admiralty", "statutory", "commercial", "legal",
        "person", "citizen", "subject", "certificate", "registered",
        "hereby", "therein", "forthwith", "shall",
    },
    "air/ether": {
        "trust", "estate", "will", "testament", "probate", "executor",
        "guardian", "ward", "ecclesiastical", "canonical", "papal",
        "spirit", "soul", "foundation", "beneficiary",
    },
}


def assign_jurisdiction(word: str) -> str:
    """Assign a jurisdiction based on keyword hints."""
    w = word.lower()
    for jur, keywords in JURISDICTION_HINTS.items():
        if w in keywords:
            return jur
    # Default distribution weighted toward sea/water (most legal terms)
    r = hash(w) % 100
    if r < 40:
        return "land/soil"
    elif r < 80:
        return "sea/water"
    else:
        return "air/ether"


def extract_root(word: str) -> str:
    """Extract an approximate root from a word for edge-linking."""
    w = word.lower()
    # Strip common suffixes
    for suffix in ["ment", "tion", "sion", "ness", "ance", "ence", "ity",
                    "ing", "ful", "less", "able", "ible", "ous", "ive",
                    "ary", "ory", "ure", "ize", "ise", "ate", "fy",
                    "ly", "al", "er", "or", "ed", "es", "en", "an"]:
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            w = w[:-len(suffix)]
            break
    # Strip common prefixes
    for prefix in ["un", "re", "in", "im", "ir", "il", "dis", "mis",
                    "over", "under", "out", "pre", "non"]:
        if w.startswith(prefix) and len(w) - len(prefix) >= 3:
            w = w[len(prefix):]
            break
    return w


def generate_basis() -> list[dict]:
    """Generate the 720-word basis set with full metadata."""
    basis = []
    seen = set()

    for role, words in ROLE_WORDS.items():
        for word in words:
            w_lower = word.lower()
            if w_lower in seen:
                continue
            seen.add(w_lower)
            entry = {
                "word": word,
                "role": role,
                "jurisdiction": assign_jurisdiction(word),
                "negated": is_vcc_negated(word),
                "complexity": morpheme_count(word),
                "root": extract_root(word),
            }
            basis.append(entry)

    # Pad to exactly 720 if needed with additional legal/grammatical terms
    extra_words = [
        ("noun", "affidavit"), ("noun", "deposition"), ("noun", "subpoena"),
        ("noun", "injunction"), ("noun", "mandamus"), ("noun", "certiorari"),
        ("noun", "habeas"), ("noun", "writ"), ("noun", "statute"),
        ("noun", "precedent"), ("noun", "equity"), ("noun", "remedy"),
        ("noun", "tort"), ("noun", "negligence"), ("noun", "intent"),
        ("noun", "malice"), ("noun", "fraud"), ("noun", "duress"),
        ("noun", "coercion"), ("noun", "consent"), ("noun", "assent"),
        ("noun", "consideration"), ("noun", "performance"), ("noun", "breach"),
        ("noun", "waiver"), ("noun", "estoppel"), ("noun", "laches"),
        ("noun", "ratification"), ("noun", "novation"), ("noun", "subrogation"),
        ("noun", "indemnity"), ("noun", "guaranty"), ("noun", "suretyship"),
        ("noun", "bailment"), ("noun", "lien"), ("noun", "easement"),
        ("noun", "covenant"), ("noun", "servitude"), ("noun", "tenancy"),
        ("noun", "freehold"), ("noun", "leasehold"), ("noun", "fee"),
        ("verb", "navigating"), ("verb", "docking"), ("verb", "anchoring"),
        ("verb", "charting"), ("verb", "piloting"), ("verb", "salvaging"),
        ("verb", "towing"), ("verb", "loading"), ("verb", "unloading"),
        ("verb", "shipping"), ("verb", "delivering"), ("verb", "accepting"),
        ("verb", "rejecting"), ("verb", "protesting"), ("verb", "noting"),
        ("verb", "dishonoring"), ("verb", "endorsing"), ("verb", "presenting"),
        ("adjective", "navigable"), ("adjective", "merchantable"),
        ("adjective", "negotiable"), ("adjective", "assignable"),
        ("adjective", "transferable"), ("adjective", "revocable"),
        ("adjective", "irrevocable"), ("adjective", "voidable"),
        ("adjective", "enforceable"), ("adjective", "unenforceable"),
        ("adjective", "bilateral"), ("adjective", "unilateral"),
        ("adjective", "executory"), ("adjective", "executed"),
        ("adverb", "proximately"), ("adverb", "remotely"),
        ("adverb", "foreseeable"), ("adverb", "reasonably"),
        ("adverb", "unreasonably"), ("adverb", "equitably"),
        ("preposition", "pursuant"), ("preposition", "excepting"),
        ("preposition", "save"), ("preposition", "absent"),
    ]

    idx = 0
    while len(basis) < 720 and idx < len(extra_words):
        role, word = extra_words[idx]
        idx += 1
        w_lower = word.lower()
        if w_lower in seen:
            continue
        seen.add(w_lower)
        basis.append({
            "word": word,
            "role": role,
            "jurisdiction": assign_jurisdiction(word),
            "negated": is_vcc_negated(word),
            "complexity": morpheme_count(word),
            "root": extract_root(word),
        })

    # If still under 720, truncate or pad with synthetic entries
    basis = basis[:720]

    return basis


def load_or_generate_basis() -> list[dict]:
    """Load basis_720.json if it exists, otherwise generate and save."""
    if BASIS_PATH.exists():
        try:
            with open(BASIS_PATH, "r") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                # Ensure all entries have required fields
                for entry in data:
                    if "root" not in entry:
                        entry["root"] = extract_root(entry.get("word", ""))
                    if "complexity" not in entry:
                        entry["complexity"] = morpheme_count(entry.get("word", ""))
                    if "negated" not in entry:
                        entry["negated"] = is_vcc_negated(entry.get("word", ""))
                    if "jurisdiction" not in entry:
                        entry["jurisdiction"] = assign_jurisdiction(entry.get("word", ""))
                    if "role" not in entry:
                        entry["role"] = "noun"
                print(f"Loaded {len(data)} words from {BASIS_PATH}")
                return data
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse {BASIS_PATH}: {e}")
            print("Generating basis inline...")

    basis = generate_basis()
    # Save for next time
    BASIS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BASIS_PATH, "w") as f:
        json.dump(basis, f, indent=2)
    print(f"Generated {len(basis)} words -> {BASIS_PATH}")
    return basis


def build_edges(basis: list[dict]) -> list[dict]:
    """Build edges between words that share a root."""
    root_groups: dict[str, list[int]] = {}
    for i, entry in enumerate(basis):
        root = entry["root"]
        if len(root) >= 3:  # Only link on roots of reasonable length
            root_groups.setdefault(root, []).append(i)

    edges = []
    for root, indices in root_groups.items():
        if 2 <= len(indices) <= 8:  # Skip singletons and overly large groups
            for j in range(len(indices)):
                for k in range(j + 1, len(indices)):
                    edges.append({
                        "source": indices[j],
                        "target": indices[k],
                        "root": root,
                    })
    return edges


def generate_html(basis: list[dict], edges: list[dict]) -> str:
    """Generate the self-contained HTML visualization."""
    nodes_json = json.dumps(basis)
    edges_json = json.dumps(edges)

    # Compute stats
    role_counts = {}
    jur_counts = {}
    neg_count = 0
    for entry in basis:
        role_counts[entry["role"]] = role_counts.get(entry["role"], 0) + 1
        jur_counts[entry["jurisdiction"]] = jur_counts.get(entry["jurisdiction"], 0) + 1
        if entry.get("negated"):
            neg_count += 1

    stats_role = json.dumps(role_counts)
    stats_jur = json.dumps(jur_counts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>720-Word Basis Map -- Quantum Grammar</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    background: #0a0a0a;
    color: #c0c0c0;
    font-family: 'Courier New', Courier, monospace;
    overflow: hidden;
    width: 100vw;
    height: 100vh;
}}
#graph-container {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
}}
svg {{
    width: 100%;
    height: 100%;
}}
.link {{
    stroke: #333;
    stroke-opacity: 0.4;
    stroke-width: 0.5;
}}
.link.highlighted {{
    stroke: #c0a060;
    stroke-opacity: 0.8;
    stroke-width: 1.5;
}}
.node circle {{
    stroke: #222;
    stroke-width: 0.5;
    cursor: pointer;
}}
.node circle:hover {{
    stroke: #c0a060;
    stroke-width: 2;
}}
.node text {{
    fill: #888;
    font-size: 8px;
    pointer-events: none;
    font-family: 'Courier New', monospace;
}}
.node.selected circle {{
    stroke: #c0a060;
    stroke-width: 2.5;
}}
.node.search-match circle {{
    stroke: #fff;
    stroke-width: 2;
}}
.node.dimmed circle {{
    opacity: 0.15;
}}
.node.dimmed text {{
    opacity: 0.1;
}}

/* Controls Panel */
#controls {{
    position: absolute;
    top: 12px;
    left: 12px;
    background: rgba(15, 15, 15, 0.92);
    border: 1px solid #333;
    padding: 14px;
    border-radius: 4px;
    z-index: 10;
    width: 260px;
    max-height: calc(100vh - 24px);
    overflow-y: auto;
}}
#controls h2 {{
    color: #c0a060;
    font-size: 14px;
    margin-bottom: 10px;
    letter-spacing: 1px;
}}
#controls h3 {{
    color: #888;
    font-size: 11px;
    margin: 10px 0 5px 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
#search {{
    width: 100%;
    background: #1a1a1a;
    border: 1px solid #444;
    color: #c0c0c0;
    padding: 6px 8px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    border-radius: 3px;
    margin-bottom: 8px;
}}
#search:focus {{
    outline: none;
    border-color: #c0a060;
}}
.filter-group {{
    margin-bottom: 6px;
}}
.filter-group label {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    cursor: pointer;
    margin-right: 6px;
    margin-bottom: 3px;
}}
.filter-group input[type="checkbox"] {{
    accent-color: #c0a060;
}}
.color-dot {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 2px;
}}

/* Info Panel */
#info-panel {{
    position: absolute;
    bottom: 12px;
    right: 12px;
    background: rgba(15, 15, 15, 0.92);
    border: 1px solid #333;
    padding: 14px;
    border-radius: 4px;
    z-index: 10;
    width: 320px;
    display: none;
}}
#info-panel h2 {{
    color: #c0a060;
    font-size: 16px;
    margin-bottom: 8px;
}}
#info-panel .field {{
    font-size: 11px;
    margin-bottom: 4px;
}}
#info-panel .field span.label {{
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
#info-panel .field span.value {{
    color: #c0c0c0;
}}
#info-panel .field span.negated {{
    color: #cc4444;
}}
#info-panel .field span.direct {{
    color: #44aa44;
}}
#info-panel .related {{
    margin-top: 8px;
    font-size: 11px;
    color: #888;
}}
#info-panel .related span {{
    color: #c0a060;
    cursor: pointer;
}}
#info-panel .related span:hover {{
    text-decoration: underline;
}}

/* Stats Panel */
#stats {{
    position: absolute;
    top: 12px;
    right: 12px;
    background: rgba(15, 15, 15, 0.92);
    border: 1px solid #333;
    padding: 14px;
    border-radius: 4px;
    z-index: 10;
    width: 220px;
}}
#stats h2 {{
    color: #c0a060;
    font-size: 14px;
    margin-bottom: 10px;
    letter-spacing: 1px;
}}
#stats .stat-row {{
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    margin-bottom: 3px;
}}
#stats .stat-row .stat-label {{
    color: #888;
}}
#stats .stat-row .stat-value {{
    color: #c0c0c0;
    font-weight: bold;
}}
#stats .stat-section {{
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #222;
}}
#stats .stat-section:last-child {{
    border-bottom: none;
    margin-bottom: 0;
}}
.stat-section h3 {{
    color: #666;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 5px;
}}
</style>
</head>
<body>
<div id="graph-container"></div>

<div id="controls">
    <h2>720-WORD BASIS MAP</h2>
    <input type="text" id="search" placeholder="Search words...">

    <h3>Role Filter</h3>
    <div class="filter-group" id="role-filters">
        <label><input type="checkbox" data-role="preposition" checked><span class="color-dot" style="background:#9b59b6"></span>Preposition</label><br>
        <label><input type="checkbox" data-role="article" checked><span class="color-dot" style="background:#7f8c8d"></span>Article</label><br>
        <label><input type="checkbox" data-role="adjective" checked><span class="color-dot" style="background:#00bcd4"></span>Adjective</label><br>
        <label><input type="checkbox" data-role="noun" checked><span class="color-dot" style="background:#2d5a27"></span>Noun</label><br>
        <label><input type="checkbox" data-role="verb" checked><span class="color-dot" style="background:#1a4a7a"></span>Verb</label><br>
        <label><input type="checkbox" data-role="adverb" checked><span class="color-dot" style="background:#c0392b"></span>Adverb</label><br>
    </div>

    <h3>Jurisdiction</h3>
    <div class="filter-group" id="jur-filters">
        <label><input type="checkbox" data-jur="land/soil" checked><span class="color-dot" style="background:#2d5a27"></span>Land/Soil</label><br>
        <label><input type="checkbox" data-jur="sea/water" checked><span class="color-dot" style="background:#1a4a7a"></span>Sea/Water</label><br>
        <label><input type="checkbox" data-jur="air/ether" checked><span class="color-dot" style="background:#7a4a1a"></span>Air/Ether</label><br>
    </div>

    <h3>Negation</h3>
    <div class="filter-group" id="neg-filters">
        <label><input type="checkbox" data-neg="true" checked><span class="color-dot" style="background:#cc4444"></span>VCC Negated</label><br>
        <label><input type="checkbox" data-neg="false" checked><span class="color-dot" style="background:#44aa44"></span>Direct</label><br>
    </div>
</div>

<div id="stats">
    <h2>STATISTICS</h2>
    <div class="stat-section">
        <h3>By Role</h3>
        <div id="stats-role"></div>
    </div>
    <div class="stat-section">
        <h3>By Jurisdiction</h3>
        <div id="stats-jur"></div>
    </div>
    <div class="stat-section">
        <h3>Negation</h3>
        <div id="stats-neg"></div>
    </div>
</div>

<div id="info-panel">
    <h2 id="info-word"></h2>
    <div class="field"><span class="label">Role: </span><span class="value" id="info-role"></span></div>
    <div class="field"><span class="label">Jurisdiction: </span><span class="value" id="info-jur"></span></div>
    <div class="field"><span class="label">Root: </span><span class="value" id="info-root"></span></div>
    <div class="field"><span class="label">Complexity: </span><span class="value" id="info-complexity"></span></div>
    <div class="field"><span class="label">VCC Negation: </span><span id="info-neg"></span></div>
    <div class="related" id="info-related"></div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
(function() {{
    const nodes = {nodes_json};
    const edges = {edges_json};
    const roleStats = {stats_role};
    const jurStats = {stats_jur};
    const negCount = {neg_count};
    const totalCount = nodes.length;

    // Color maps
    const roleColors = {{
        preposition: '#9b59b6',
        article: '#7f8c8d',
        adjective: '#00bcd4',
        noun: '#2d5a27',
        verb: '#1a4a7a',
        adverb: '#c0392b'
    }};

    const jurColors = {{
        'land/soil': '#2d5a27',
        'sea/water': '#1a4a7a',
        'air/ether': '#7a4a1a'
    }};

    // Populate stats
    const statsRole = document.getElementById('stats-role');
    for (const [role, count] of Object.entries(roleStats)) {{
        statsRole.innerHTML += '<div class="stat-row"><span class="stat-label">' +
            role + '</span><span class="stat-value">' + count + '</span></div>';
    }}

    const statsJur = document.getElementById('stats-jur');
    for (const [jur, count] of Object.entries(jurStats)) {{
        statsJur.innerHTML += '<div class="stat-row"><span class="stat-label">' +
            jur + '</span><span class="stat-value">' + count + '</span></div>';
    }}

    const statsNeg = document.getElementById('stats-neg');
    statsNeg.innerHTML = '<div class="stat-row"><span class="stat-label">VCC Negated</span>' +
        '<span class="stat-value">' + negCount + '</span></div>' +
        '<div class="stat-row"><span class="stat-label">Direct</span>' +
        '<span class="stat-value">' + (totalCount - negCount) + '</span></div>' +
        '<div class="stat-row"><span class="stat-label">Total</span>' +
        '<span class="stat-value">' + totalCount + '</span></div>';

    // Build SVG
    const width = window.innerWidth;
    const height = window.innerHeight;

    const svg = d3.select('#graph-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Zoom behavior
    const g = svg.append('g');
    const zoom = d3.zoom()
        .scaleExtent([0.1, 8])
        .on('zoom', (event) => {{
            g.attr('transform', event.transform);
        }});
    svg.call(zoom);

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(edges).id((d, i) => i).distance(60).strength(0.3))
        .force('charge', d3.forceManyBody().strength(-15))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => Math.sqrt(d.complexity) * 3 + 4));

    // Draw edges
    const link = g.append('g')
        .selectAll('line')
        .data(edges)
        .join('line')
        .attr('class', 'link');

    // Draw nodes
    const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    node.append('circle')
        .attr('r', d => Math.sqrt(d.complexity) * 3 + 2)
        .attr('fill', d => roleColors[d.role] || '#666');

    node.append('text')
        .attr('dx', d => Math.sqrt(d.complexity) * 3 + 4)
        .attr('dy', 3)
        .text(d => d.word);

    // Click handler for info panel
    let selectedNode = null;

    node.on('click', function(event, d) {{
        event.stopPropagation();
        selectedNode = d;
        showInfo(d);
        highlightConnections(d);
        d3.selectAll('.node').classed('selected', false);
        d3.select(this).classed('selected', true);
    }});

    svg.on('click', function() {{
        selectedNode = null;
        document.getElementById('info-panel').style.display = 'none';
        d3.selectAll('.node').classed('selected', false);
        d3.selectAll('.link').classed('highlighted', false);
        d3.selectAll('.node').classed('dimmed', false);
    }});

    function showInfo(d) {{
        const panel = document.getElementById('info-panel');
        panel.style.display = 'block';
        document.getElementById('info-word').textContent = d.word.toUpperCase();
        document.getElementById('info-role').textContent = d.role;
        document.getElementById('info-jur').textContent = d.jurisdiction;
        document.getElementById('info-root').textContent = d.root;
        document.getElementById('info-complexity').textContent = d.complexity + ' morpheme(s)';

        const negSpan = document.getElementById('info-neg');
        if (d.negated) {{
            negSpan.className = 'negated';
            negSpan.textContent = 'YES -- VCC prefix inverts root meaning';
        }} else {{
            negSpan.className = 'direct';
            negSpan.textContent = 'NO -- direct meaning';
        }}

        // Find related words (shared root)
        const related = nodes.filter(n => n.root === d.root && n.word !== d.word);
        const relDiv = document.getElementById('info-related');
        if (related.length > 0) {{
            relDiv.innerHTML = '<span class="label">Shared root [' + d.root + ']: </span>' +
                related.map(r => '<span onclick="selectWord(\\'' + r.word + '\\')">' + r.word + '</span>').join(', ');
        }} else {{
            relDiv.innerHTML = '<span class="label">No shared-root connections</span>';
        }}
    }}

    function highlightConnections(d) {{
        const idx = nodes.indexOf(d);
        const connectedIndices = new Set();
        connectedIndices.add(idx);

        link.classed('highlighted', function(l) {{
            const src = typeof l.source === 'object' ? nodes.indexOf(l.source) : l.source;
            const tgt = typeof l.target === 'object' ? nodes.indexOf(l.target) : l.target;
            if (src === idx || tgt === idx) {{
                connectedIndices.add(src);
                connectedIndices.add(tgt);
                return true;
            }}
            return false;
        }});

        node.classed('dimmed', function(n) {{
            return !connectedIndices.has(nodes.indexOf(n));
        }});
    }}

    // Global function for clicking related words
    window.selectWord = function(word) {{
        const d = nodes.find(n => n.word === word);
        if (d) {{
            showInfo(d);
            highlightConnections(d);
            d3.selectAll('.node').classed('selected', false);
            d3.selectAll('.node').filter(n => n.word === word).classed('selected', true);
        }}
    }};

    // Search
    const searchInput = document.getElementById('search');
    searchInput.addEventListener('input', function() {{
        const query = this.value.toLowerCase().trim();
        if (query === '') {{
            d3.selectAll('.node').classed('search-match', false).classed('dimmed', false);
            d3.selectAll('.node text').style('font-size', null);
            return;
        }}
        node.classed('search-match', d => d.word.toLowerCase().includes(query));
        node.classed('dimmed', d => !d.word.toLowerCase().includes(query));
    }});

    // Filters
    function applyFilters() {{
        const activeRoles = new Set();
        document.querySelectorAll('#role-filters input:checked').forEach(cb => {{
            activeRoles.add(cb.dataset.role);
        }});

        const activeJurs = new Set();
        document.querySelectorAll('#jur-filters input:checked').forEach(cb => {{
            activeJurs.add(cb.dataset.jur);
        }});

        const activeNegs = new Set();
        document.querySelectorAll('#neg-filters input:checked').forEach(cb => {{
            activeNegs.add(cb.dataset.neg);
        }});

        node.style('display', d => {{
            const roleMatch = activeRoles.has(d.role);
            const jurMatch = activeJurs.has(d.jurisdiction);
            const negMatch = activeNegs.has(String(d.negated));
            return (roleMatch && jurMatch && negMatch) ? null : 'none';
        }});

        link.style('display', l => {{
            const src = typeof l.source === 'object' ? l.source : nodes[l.source];
            const tgt = typeof l.target === 'object' ? l.target : nodes[l.target];
            const srcVisible = activeRoles.has(src.role) && activeJurs.has(src.jurisdiction) && activeNegs.has(String(src.negated));
            const tgtVisible = activeRoles.has(tgt.role) && activeJurs.has(tgt.jurisdiction) && activeNegs.has(String(tgt.negated));
            return (srcVisible && tgtVisible) ? null : 'none';
        }});
    }}

    document.querySelectorAll('#controls input[type="checkbox"]').forEach(cb => {{
        cb.addEventListener('change', applyFilters);
    }});

    // Simulation tick
    simulation.on('tick', () => {{
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => 'translate(' + d.x + ',' + d.y + ')');
    }});

    // Drag functions
    function dragstarted(event, d) {{
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }}

    function dragged(event, d) {{
        d.fx = event.x;
        d.fy = event.y;
    }}

    function dragended(event, d) {{
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }}

    // Initial zoom to fit
    svg.call(zoom.transform, d3.zoomIdentity.translate(0, 0).scale(0.8));

}})();
</script>
</body>
</html>"""

    return html


def main():
    """Main entry point: load/generate basis, build edges, write HTML."""
    print("720-Word Basis Map Generator")
    print("=" * 40)

    basis = load_or_generate_basis()
    edges = build_edges(basis)

    print(f"Nodes: {len(basis)}")
    print(f"Edges: {len(edges)}")

    html = generate_html(basis, edges)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(html)

    print(f"\nOutput: {OUTPUT_PATH.resolve()}")
    print("Open in a browser to explore the interactive force-directed graph.")


if __name__ == "__main__":
    main()
