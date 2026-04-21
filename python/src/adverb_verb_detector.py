"""
adverb_verb_detector.py — Null Adverb-Verb Chain Detector

Detects ADVERB + VERB + ADVERB + VERB chains that convey ZERO facts.
These null constructions are pervasive in legal documents and create
the appearance of authority without communicating any substance.

A sentence without nouns carries zero facts. Adverb-verb chains
amplify this emptiness by stringing together modifiers and actions
with no anchor in reality.
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sentence_analyzer import (
    tag_sentence, tokenize, tag_word,
    LEGAL_ADVERBS, COMMON_ADVERBS, MODAL_VERBS,
    RED, GREEN, YELLOW, GOLD, BLUE, CYAN, DIM, BOLD, RESET,
)

# ---------------------------------------------------------------------------
# Null chain detection
# ---------------------------------------------------------------------------

ADVERB_TAGS = {"ADVERB", "LEGAL_ADVERB"}
VERB_TAGS = {"VERB", "MODAL_VERB", "PAST_VERB", "GERUND"}
NULL_TAGS = ADVERB_TAGS | VERB_TAGS
FILLER_TAGS = {"CONJUNCTION", "ARTICLE", "PUNCT"}  # allowed inside chains without breaking them


def detect_null_chains(text: str) -> list[dict]:
    """Find all null adverb-verb chain sequences in text.

    Returns a list of dicts, each with:
        - chain: list of (word, tag) tuples
        - start: character offset in original text
        - end: character offset end
        - text: the chain as a string
        - severity: 'critical' if 4+ null words, 'warning' if 3
    """
    tagged = tag_sentence(text)
    chains = []
    current_chain = []
    current_start = 0
    char_pos = 0

    # Build a map from token index to approximate char position
    positions = []
    search_from = 0
    for word, tag in tagged:
        idx = text.find(word, search_from)
        if idx == -1:
            # Try case-insensitive
            idx = text.lower().find(word.lower(), search_from)
        if idx == -1:
            idx = search_from
        positions.append(idx)
        search_from = idx + len(word)

    def flush_chain():
        nonlocal current_chain
        if not current_chain:
            return
        # Filter out pure filler — need at least one adverb and one verb
        core = [(w, t, i) for w, t, i in current_chain if t in NULL_TAGS]
        has_adverb = any(t in ADVERB_TAGS for _, t, _ in core)
        has_verb = any(t in VERB_TAGS for _, t, _ in core)
        if has_adverb and has_verb and len(core) >= 2:
            start_pos = current_chain[0][2]
            last_w, last_t, last_i = current_chain[-1]
            end_pos = last_i + len(last_w)
            chain_text = text[start_pos:end_pos]
            severity = "critical" if len(core) >= 4 else "warning"
            chains.append({
                "chain": [(w, t) for w, t, _ in current_chain if t not in FILLER_TAGS],
                "start": start_pos,
                "end": end_pos,
                "text": chain_text,
                "severity": severity,
            })
        current_chain = []

    for idx, (word, tag) in enumerate(tagged):
        pos = positions[idx] if idx < len(positions) else 0
        if tag in NULL_TAGS:
            if not current_chain:
                current_start = pos
            current_chain.append((word, tag, pos))
        elif tag in FILLER_TAGS and current_chain:
            # Allow fillers inside chains (e.g., "shall and will")
            current_chain.append((word, tag, pos))
        else:
            flush_chain()

    flush_chain()
    return chains


# ---------------------------------------------------------------------------
# Factual content scoring
# ---------------------------------------------------------------------------

def score_factual_content(text: str) -> dict:
    """Compute ratio of fact-carrying words (nouns) to null words.

    Returns:
        - total_words: int
        - noun_count: int (fact-carriers)
        - adverb_count: int (null modifiers)
        - modal_count: int (fiction markers)
        - null_word_count: int (adverbs + modals)
        - factual_ratio: float (nouns / total content words)
        - null_ratio: float (null words / total content words)
        - assessment: str
    """
    tagged = tag_sentence(text)
    content_tags = {"NOUN", "VERB", "GERUND", "PAST_VERB", "MODAL_VERB",
                    "ADVERB", "LEGAL_ADVERB", "ADJECTIVE", "PRONOUN"}

    total = len(tagged)
    content_words = [(w, t) for w, t in tagged if t in content_tags]
    content_count = len(content_words)

    noun_count = sum(1 for _, t in tagged if t == "NOUN")
    adverb_count = sum(1 for _, t in tagged if t in ADVERB_TAGS)
    modal_count = sum(1 for _, t in tagged if t == "MODAL_VERB")
    null_count = adverb_count + modal_count

    if content_count == 0:
        factual_ratio = 0.0
        null_ratio = 0.0
    else:
        factual_ratio = noun_count / content_count
        null_ratio = null_count / content_count

    # Assessment
    if factual_ratio >= 0.4 and null_ratio <= 0.1:
        assessment = "HIGH FACT CONTENT — sentence carries substantive meaning"
    elif factual_ratio >= 0.25 and null_ratio <= 0.25:
        assessment = "MODERATE FACT CONTENT — some substance present"
    elif null_ratio >= 0.4:
        assessment = "NULL CONSTRUCTION — dominated by adverbs and modal verbs, conveys zero facts"
    elif noun_count == 0:
        assessment = "ZERO FACTS — no nouns present, sentence carries no factual content"
    else:
        assessment = "LOW FACT CONTENT — mostly null/modifier words, minimal substance"

    return {
        "total_words": total,
        "noun_count": noun_count,
        "adverb_count": adverb_count,
        "modal_count": modal_count,
        "null_word_count": null_count,
        "factual_ratio": round(factual_ratio, 3),
        "null_ratio": round(null_ratio, 3),
        "assessment": assessment,
    }


# ---------------------------------------------------------------------------
# Highlighting
# ---------------------------------------------------------------------------

def highlight_null_chains(text: str) -> str:
    """Return text with ANSI highlighting: red for null chains, green for nouns."""
    tagged = tag_sentence(text)
    chains = detect_null_chains(text)

    # Build set of chain character ranges
    chain_ranges = []
    for c in chains:
        chain_ranges.append((c["start"], c["end"]))

    def in_chain(pos: int) -> bool:
        for start, end in chain_ranges:
            if start <= pos < end:
                return True
        return False

    # Rebuild text with coloring, word by word
    result_parts = []
    search_from = 0
    for word, tag in tagged:
        idx = text.find(word, search_from)
        if idx == -1:
            idx = text.lower().find(word.lower(), search_from)
        if idx == -1:
            idx = search_from

        # Add any whitespace/gap before this word
        if idx > search_from:
            result_parts.append(text[search_from:idx])

        if in_chain(idx):
            if tag in ADVERB_TAGS:
                result_parts.append(f"{RED}{BOLD}{word}{RESET}")
            elif tag in VERB_TAGS:
                result_parts.append(f"{RED}{word}{RESET}")
            else:
                result_parts.append(f"{RED}{DIM}{word}{RESET}")
        elif tag == "NOUN":
            result_parts.append(f"{GREEN}{BOLD}{word}{RESET}")
        elif tag == "MODAL_VERB":
            result_parts.append(f"{RED}{word}{RESET}")
        elif tag == "LEGAL_ADVERB":
            result_parts.append(f"{RED}{word}{RESET}")
        elif tag == "GERUND":
            result_parts.append(f"{GREEN}{word}{RESET}")
        elif tag == "PAST_VERB":
            result_parts.append(f"{YELLOW}{word}{RESET}")
        else:
            result_parts.append(word)

        search_from = idx + len(word)

    # Trailing text
    if search_from < len(text):
        result_parts.append(text[search_from:])

    return "".join(result_parts)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_detection(text: str) -> str:
    """Full formatted analysis of null chains in text."""
    chains = detect_null_chains(text)
    score = score_factual_content(text)
    highlighted = highlight_null_chains(text)

    lines = []
    lines.append("")
    lines.append(f"{BOLD}{CYAN}{'=' * 70}{RESET}")
    lines.append(f"{BOLD}  ADVERB-VERB NULL CHAIN DETECTOR{RESET}")
    lines.append(f"{CYAN}{'=' * 70}{RESET}")
    lines.append("")
    lines.append(f"  {DIM}Input:{RESET} {text}")
    lines.append(f"  {DIM}Highlighted:{RESET} {highlighted}")
    lines.append("")

    # Chains found
    if chains:
        lines.append(f"  {RED}{BOLD}Null Chains Found: {len(chains)}{RESET}")
        for i, c in enumerate(chains, 1):
            sev_color = RED if c["severity"] == "critical" else YELLOW
            lines.append(f"    {sev_color}[{c['severity'].upper()}]{RESET} \"{c['text']}\"")
            chain_parts = []
            for w, t in c["chain"]:
                if t in ADVERB_TAGS:
                    chain_parts.append(f"{RED}{w}(adverb){RESET}")
                elif t in VERB_TAGS:
                    chain_parts.append(f"{YELLOW}{w}(verb){RESET}")
                else:
                    chain_parts.append(f"{DIM}{w}({t.lower()}){RESET}")
            lines.append(f"      Parse: {' + '.join(chain_parts)}")
        lines.append("")
    else:
        lines.append(f"  {GREEN}No null chains detected.{RESET}")
        lines.append("")

    # Factual content score
    lines.append(f"  {DIM}--- Factual Content Score ---{RESET}")
    lines.append(f"    Nouns (facts):      {GOLD}{score['noun_count']}{RESET}")
    lines.append(f"    Adverbs (null):     {RED if score['adverb_count'] > 0 else DIM}{score['adverb_count']}{RESET}")
    lines.append(f"    Modal verbs (null): {RED if score['modal_count'] > 0 else DIM}{score['modal_count']}{RESET}")
    lines.append(f"    Factual ratio:      {score['factual_ratio']:.1%}")
    lines.append(f"    Null ratio:         {score['null_ratio']:.1%}")

    # Assessment
    if "ZERO" in score["assessment"] or "NULL" in score["assessment"]:
        a_color = RED
    elif "LOW" in score["assessment"]:
        a_color = YELLOW
    elif "HIGH" in score["assessment"]:
        a_color = GREEN
    else:
        a_color = YELLOW
    lines.append(f"    {a_color}{BOLD}{score['assessment']}{RESET}")

    lines.append("")
    lines.append(f"{CYAN}{'=' * 70}{RESET}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Built-in examples
# ---------------------------------------------------------------------------

EXAMPLES = [
    {
        "label": "NULL CHAIN: Typical court order",
        "text": "The court hereby orders that you shall forthwith pay the sum",
    },
    {
        "label": "NULL CHAIN: Legal boilerplate",
        "text": "Whereas the party hereby agrees and shall forthwith comply therewith and thereafter",
    },
    {
        "label": "NULL CHAIN: Contract language",
        "text": "The borrower shall hereinafter immediately remit and will subsequently deliver",
    },
    {
        "label": "FACT-CARRYING: Parse-syntax correct",
        "text": "FOR THE CLAIMING OF THE LAND BY THE LIVING MAN",
    },
    {
        "label": "FACT-CARRYING: Noun-heavy sentence",
        "text": "The claim of the man for the land by the authority of the trust",
    },
    {
        "label": "COMPARISON: Legal vs. factual",
        "text": "It is hereby ordered and adjudged that the defendant shall forthwith pay to the plaintiff the sum of ten thousand dollars",
    },
]


def run_examples():
    """Run all built-in examples."""
    for ex in EXAMPLES:
        print(f"\n{BOLD}{BLUE}  [{ex['label']}]{RESET}")
        print(format_detection(ex["text"]))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Adverb-Verb Null Chain Detector — Find empty legal constructions"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to analyze for null chains"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Run built-in example analyses"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to file to analyze"
    )

    args = parser.parse_args()

    if args.examples:
        run_examples()
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"{RED}Error: File not found: {args.file}{RESET}")
            sys.exit(1)
        text = path.read_text()
        # Analyze sentence by sentence
        sentences = re.split(r'[.!?]+', text)
        for sent in sentences:
            sent = sent.strip()
            if sent:
                print(format_detection(sent))
    elif args.text:
        print(format_detection(args.text))
    else:
        parser.print_help()
        print(f"\n{DIM}  Try: python src/adverb_verb_detector.py --examples{RESET}")


if __name__ == "__main__":
    main()
