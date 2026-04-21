"""
sentence_analyzer.py — C.S.S.C.P.S.G.P. Sentence Analysis Engine

Analyzes sentences for Correct Sentence Structure Communication Parse
Syntax Grammar Performance compliance.

Rules:
  - Must begin with a prepositional phrase (now-time prepositions only)
  - Nouns are primary fact-carriers
  - Verbs must be gerund form (-ING) for now-time validity
  - No adverb-verb-adverb-verb chains (null construction)
  - No pronouns (they remove the fact)
  - Past tense = dead time = fiction
  - Future tense = fiction
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ---------------------------------------------------------------------------
# ANSI color codes
# ---------------------------------------------------------------------------
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
GOLD = "\033[93m"
BLUE = "\033[34m"
CYAN = "\033[36m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ---------------------------------------------------------------------------
# Word lists for rule-based POS tagging
# ---------------------------------------------------------------------------

VALID_PREPOSITIONS = {"for", "by", "of", "with", "in", "against"}
INVALID_PREPOSITIONS = {"to", "from"}
ALL_PREPOSITIONS = VALID_PREPOSITIONS | INVALID_PREPOSITIONS | {
    "at", "on", "into", "upon", "through", "between", "among",
    "above", "below", "before", "after", "during", "within",
    "without", "under", "over", "about", "around", "behind",
    "beneath", "beside", "beyond", "concerning", "despite",
    "except", "toward", "towards", "until", "unto", "via",
}

ARTICLES = {"the", "a", "an"}

PRONOUNS = {
    "i", "me", "my", "mine", "myself",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",
    "who", "whom", "whose", "which", "that",
    "this", "these", "those",
    "one", "ones", "oneself",
    "somebody", "someone", "something",
    "anybody", "anyone", "anything",
    "nobody", "everyone", "everything",
    "each", "either", "neither",
}

MODAL_VERBS = {"shall", "will", "would", "could", "may", "might", "should", "must", "can"}

PAST_TENSE_MARKERS = {"was", "were", "had", "did", "been"}

LEGAL_ADVERBS = {
    "hereby", "thereof", "therein", "thereto", "forthwith",
    "henceforth", "whereas", "whereby", "wherein", "thereupon",
    "hereinafter", "hereinbefore", "aforementioned", "notwithstanding",
    "hereto", "herein", "heretofore", "thereafter", "thereunder",
    "therefor", "therefore", "moreover", "furthermore", "accordingly",
    "otherwise", "nevertheless", "howsoever", "whatsoever",
    "whosoever", "wheresoever",
}

COMMON_ADVERBS = LEGAL_ADVERBS | {
    "very", "really", "quickly", "slowly", "already", "always",
    "never", "often", "sometimes", "usually", "here", "there",
    "now", "then", "today", "tomorrow", "yesterday", "still",
    "just", "also", "too", "only", "ever", "not", "quite",
    "almost", "certainly", "clearly", "definitely", "simply",
    "merely", "probably", "perhaps", "possibly", "apparently",
    "evidently", "immediately", "subsequently", "previously",
}

COMMON_ADJECTIVES = {
    "good", "bad", "great", "small", "large", "big", "little",
    "old", "new", "young", "long", "short", "high", "low",
    "right", "wrong", "true", "false", "real", "full", "empty",
    "first", "last", "next", "other", "same", "different",
    "certain", "guilty", "innocent", "dead", "alive", "living",
    "whole", "due", "said", "such", "own", "public", "private",
    "legal", "lawful", "unlawful", "illegal", "civil", "criminal",
    "federal", "state", "local", "foreign", "domestic",
    "sovereign", "free", "subject", "liable", "responsible",
}

COMMON_NOUNS = {
    "man", "woman", "person", "people", "child", "children",
    "court", "law", "land", "soil", "water", "sea", "air",
    "state", "nation", "country", "government", "king", "queen",
    "judge", "jury", "attorney", "lawyer", "defendant", "plaintiff",
    "witness", "officer", "agent", "trustee", "beneficiary",
    "claim", "right", "rights", "duty", "obligation", "contract",
    "agreement", "trust", "estate", "property", "title", "deed",
    "bond", "mortgage", "lien", "charge", "debt", "sum",
    "money", "currency", "bank", "account", "payment", "tax",
    "name", "date", "time", "place", "number", "certificate",
    "document", "order", "notice", "warrant", "writ", "summons",
    "sentence", "judgment", "verdict", "penalty", "fine",
    "birth", "death", "life", "vessel", "ship", "flag",
    "citizen", "resident", "inhabitant", "being", "entity",
    "body", "corpus", "fiction", "fact", "truth", "fraud",
    "jurisdiction", "authority", "power", "consent", "standing",
    "world", "day", "year", "house", "home", "way", "thing",
    "case", "point", "part", "group", "company", "system",
    "program", "question", "work", "number", "night", "hand",
    "head", "side", "end", "area", "word", "family",
}

COMMON_VERBS = {
    "be", "is", "am", "are", "was", "were", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing", "done",
    "say", "said", "says", "saying",
    "go", "goes", "went", "going", "gone",
    "get", "gets", "got", "getting", "gotten",
    "make", "makes", "made", "making",
    "know", "knows", "knew", "knowing", "known",
    "take", "takes", "took", "taking", "taken",
    "come", "comes", "came", "coming",
    "see", "sees", "saw", "seeing", "seen",
    "find", "finds", "found", "finding",
    "give", "gives", "gave", "giving", "given",
    "pay", "pays", "paid", "paying",
    "order", "orders", "ordered", "ordering",
    "claim", "claims", "claimed", "claiming",
    "hold", "holds", "held", "holding",
    "stand", "stands", "stood", "standing",
    "appear", "appears", "appeared", "appearing",
    "file", "files", "filed", "filing",
    "grant", "grants", "granted", "granting",
    "deny", "denies", "denied", "denying",
    "charge", "charges", "charged", "charging",
    "convict", "convicts", "convicted", "convicting",
    "sentence", "sentenced", "sentencing",
    "execute", "executes", "executed", "executing",
    "owe", "owes", "owed", "owing",
}

CONJUNCTIONS = {
    "and", "or", "but", "nor", "yet", "so", "for",
    "that", "because", "although", "though", "while",
    "if", "when", "where", "unless", "since", "whether",
    "however", "therefore",
}

# ---------------------------------------------------------------------------
# POS tagging
# ---------------------------------------------------------------------------

def tag_word(word: str) -> str:
    """Assign a part-of-speech tag to a single word using rule-based logic."""
    w = word.lower().strip(".:;,!?\"'()[]{}#")
    if not w:
        return "PUNCT"

    # Check specific lists first
    if w in ARTICLES:
        return "ARTICLE"
    if w in PRONOUNS:
        return "PRONOUN"
    if w in MODAL_VERBS:
        return "MODAL_VERB"
    if w in PAST_TENSE_MARKERS:
        return "PAST_VERB"
    if w in ALL_PREPOSITIONS:
        return "PREPOSITION"
    if w in LEGAL_ADVERBS:
        return "LEGAL_ADVERB"

    # Gerund / present participle
    if w.endswith("ing") and len(w) > 4:
        return "GERUND"

    # Past tense -ed
    if w.endswith("ed") and len(w) > 3:
        # Could be adjective or past verb — lean toward PAST_VERB
        if w in COMMON_ADJECTIVES:
            return "ADJECTIVE"
        return "PAST_VERB"

    # Adverbs ending in -ly
    if w.endswith("ly") and len(w) > 3 and w not in COMMON_ADJECTIVES:
        return "ADVERB"

    if w in COMMON_ADVERBS:
        return "ADVERB"
    if w in COMMON_ADJECTIVES:
        return "ADJECTIVE"
    if w in COMMON_NOUNS:
        return "NOUN"
    if w in COMMON_VERBS:
        return "VERB"
    if w in CONJUNCTIONS:
        return "CONJUNCTION"

    # Heuristics for unknown words
    if w.endswith("tion") or w.endswith("sion") or w.endswith("ment") or w.endswith("ness"):
        return "NOUN"
    if w.endswith("ity") or w.endswith("ance") or w.endswith("ence"):
        return "NOUN"
    if w.endswith("able") or w.endswith("ible") or w.endswith("ful") or w.endswith("ous"):
        return "ADJECTIVE"
    if w.endswith("ize") or w.endswith("ise") or w.endswith("ify") or w.endswith("ate"):
        return "VERB"
    if w.endswith("er") and len(w) > 3:
        return "NOUN"
    if w.endswith("ist") or w.endswith("or"):
        return "NOUN"

    # Capitalized unknown words — likely nouns (proper)
    if word and word[0].isupper():
        return "NOUN"

    return "UNKNOWN"


def tokenize(sentence: str) -> list[str]:
    """Split sentence into tokens, preserving punctuation as separate tokens."""
    # Insert spaces around punctuation so they become separate tokens
    s = re.sub(r'([.,;:!?\'"()\[\]{}])', r' \1 ', sentence)
    return [t for t in s.split() if t]


def tag_sentence(sentence: str) -> list[tuple[str, str]]:
    """Return list of (word, POS) tuples for a sentence."""
    tokens = tokenize(sentence)
    return [(t, tag_word(t)) for t in tokens]


# ---------------------------------------------------------------------------
# Analysis checks
# ---------------------------------------------------------------------------

def _clean(word: str) -> str:
    return word.lower().strip(".:;,!?\"'()[]{}#")


def check_starts_with_preposition(tagged: list[tuple[str, str]]) -> tuple[bool, bool, str]:
    """Check if sentence starts with a prepositional phrase.
    Returns: (starts_with_prep, is_valid_prep, prep_word)
    """
    for word, tag in tagged:
        if tag == "PUNCT":
            continue
        w = _clean(word)
        if tag == "PREPOSITION":
            is_valid = w in VALID_PREPOSITIONS
            return True, is_valid, w
        return False, False, ""
    return False, False, ""


def count_nouns(tagged: list[tuple[str, str]]) -> int:
    """Count nouns (fact-carriers) in the sentence."""
    return sum(1 for _, tag in tagged if tag == "NOUN")


def has_gerund_verbs(tagged: list[tuple[str, str]]) -> bool:
    """Check if verbs are in gerund form (-ING)."""
    has_gerund = any(tag == "GERUND" for _, tag in tagged)
    return has_gerund


def has_non_gerund_verbs(tagged: list[tuple[str, str]]) -> bool:
    """Check if there are non-gerund verbs (not now-time)."""
    return any(tag in ("VERB", "PAST_VERB") for _, tag in tagged)


def has_past_tense(tagged: list[tuple[str, str]]) -> bool:
    """Check for past tense markers (dead time)."""
    for word, tag in tagged:
        if tag == "PAST_VERB":
            return True
        w = _clean(word)
        if w in PAST_TENSE_MARKERS:
            return True
    return False


def has_future_tense(tagged: list[tuple[str, str]]) -> bool:
    """Check for future/modal verbs (fiction)."""
    return any(tag == "MODAL_VERB" for _, tag in tagged)


def has_pronouns(tagged: list[tuple[str, str]]) -> bool:
    """Check for pronouns (they remove the fact)."""
    return any(tag == "PRONOUN" for _, tag in tagged)


def detect_null_chains(tagged: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
    """Detect adverb-verb-adverb-verb null chains."""
    chains = []
    current_chain = []
    adverb_tags = {"ADVERB", "LEGAL_ADVERB"}
    verb_tags = {"VERB", "MODAL_VERB", "PAST_VERB", "GERUND"}

    for word, tag in tagged:
        if tag in adverb_tags or tag in verb_tags:
            current_chain.append((word, tag))
        else:
            if len(current_chain) >= 3:
                # Check if it contains at least one adverb and one verb
                has_adv = any(t in adverb_tags for _, t in current_chain)
                has_vrb = any(t in verb_tags for _, t in current_chain)
                if has_adv and has_vrb:
                    chains.append(current_chain)
            current_chain = []

    # Check trailing chain
    if len(current_chain) >= 3:
        has_adv = any(t in {"ADVERB", "LEGAL_ADVERB"} for _, t in current_chain)
        has_vrb = any(t in {"VERB", "MODAL_VERB", "PAST_VERB", "GERUND"} for _, t in current_chain)
        if has_adv and has_vrb:
            chains.append(current_chain)

    return chains


def check_closure(tagged: list[tuple[str, str]]) -> bool:
    """Check if sentence has proper closure — at minimum PREP + NOUN."""
    has_prep = any(tag == "PREPOSITION" for _, tag in tagged)
    has_noun = any(tag == "NOUN" for _, tag in tagged)
    return has_prep and has_noun


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_sentence(sentence: str) -> dict:
    """Analyze a sentence for C.S.S.C.P.S.G.P. compliance.

    Returns a dict with: original, tokens, pos_tags, starts_with_preposition,
    valid_preposition, noun_count, has_gerund_verbs, has_past_tense,
    has_future_tense, has_null_chain, has_pronouns, score, grade, issues,
    corrections.
    """
    tagged = tag_sentence(sentence)
    tokens = [w for w, _ in tagged]
    pos_tags = [(w, t) for w, t in tagged]

    starts_with_prep, valid_prep, prep_word = check_starts_with_preposition(tagged)
    n_count = count_nouns(tagged)
    gerunds = has_gerund_verbs(tagged)
    non_gerunds = has_non_gerund_verbs(tagged)
    past = has_past_tense(tagged)
    future = has_future_tense(tagged)
    null_chains = detect_null_chains(tagged)
    prons = has_pronouns(tagged)
    closure = check_closure(tagged)

    issues = []
    corrections = []
    score = 100

    # Rule 1: Must begin with prepositional phrase
    if not starts_with_prep:
        issues.append("Does not begin with a prepositional phrase")
        corrections.append("Begin sentence with a valid preposition: FOR, BY, OF, WITH, IN, AGAINST")
        score -= 20
    elif not valid_prep:
        issues.append(f"Begins with invalid preposition '{prep_word.upper()}' (past/future tense)")
        corrections.append(f"Replace '{prep_word.upper()}' with a now-time preposition: FOR, BY, OF, WITH, IN, AGAINST")
        score -= 15

    # Rule 2: Nouns carry facts
    if n_count == 0:
        issues.append("ZERO nouns — sentence carries NO facts")
        corrections.append("Add noun fact-carriers (the WHAT and the WHO)")
        score -= 25
    elif n_count == 1:
        issues.append("Only one noun — minimal fact content")
        corrections.append("Add additional nouns to establish complete facts")
        score -= 10

    # Rule 3: Gerund verbs for now-time
    if not gerunds and non_gerunds:
        issues.append("No gerund (-ING) verbs — not in now-time")
        corrections.append("Convert verbs to gerund form (-ING) for now-time validity")
        score -= 15
    elif non_gerunds and gerunds:
        issues.append("Mixed verb tenses — some verbs not in gerund form")
        corrections.append("Use only gerund (-ING) form verbs for consistency")
        score -= 5

    # Rule 4: Past tense = dead time
    if past:
        issues.append("Contains past tense (dead time = fiction)")
        corrections.append("Remove past tense markers (-ED, WAS, WERE, HAD); use gerund form")
        score -= 15

    # Rule 5: Future tense = fiction
    if future:
        issues.append("Contains modal/future verbs (SHALL, WILL, etc. = fiction)")
        corrections.append("Remove modal verbs; state facts in now-time gerund form")
        score -= 15

    # Rule 6: Null chains
    if null_chains:
        chain_strs = [" ".join(w for w, _ in c) for c in null_chains]
        issues.append(f"Null adverb-verb chain(s) detected: {'; '.join(chain_strs)}")
        corrections.append("Remove adverb-verb chains; replace with noun-fact constructions")
        score -= 20

    # Rule 7: No pronouns
    if prons:
        pron_words = [w for w, t in tagged if t == "PRONOUN"]
        issues.append(f"Contains pronouns ({', '.join(set(w.lower() for w in pron_words))}) — facts removed")
        corrections.append("Replace all pronouns with actual nouns/names")
        score -= 10

    # Rule 8: Closure
    if not closure:
        issues.append("No proper closure — incomplete thought")
        corrections.append("Ensure sentence has prepositional grounding and noun anchors")
        score -= 10

    score = max(0, score)

    # Grade
    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    return {
        "original": sentence,
        "tokens": tokens,
        "pos_tags": pos_tags,
        "starts_with_preposition": starts_with_prep,
        "valid_preposition": valid_prep,
        "noun_count": n_count,
        "has_gerund_verbs": gerunds,
        "has_past_tense": past,
        "has_future_tense": future,
        "has_null_chain": len(null_chains) > 0,
        "null_chains": null_chains,
        "has_pronouns": prons,
        "has_closure": closure,
        "score": score,
        "grade": grade,
        "issues": issues,
        "corrections": corrections,
    }


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

TAG_COLORS = {
    "PREPOSITION": GREEN,
    "ARTICLE": DIM,
    "ADJECTIVE": CYAN,
    "NOUN": GOLD,
    "GERUND": GREEN,
    "VERB": YELLOW,
    "PAST_VERB": RED,
    "MODAL_VERB": RED,
    "ADVERB": YELLOW,
    "LEGAL_ADVERB": RED,
    "PRONOUN": RED,
    "CONJUNCTION": DIM,
    "PUNCT": DIM,
    "UNKNOWN": DIM,
}


def format_analysis(result: dict) -> str:
    """Format analysis result as colored terminal output."""
    lines = []
    lines.append("")
    lines.append(f"{BOLD}{CYAN}{'=' * 70}{RESET}")
    lines.append(f"{BOLD}  C.S.S.C.P.S.G.P. SENTENCE ANALYSIS{RESET}")
    lines.append(f"{CYAN}{'=' * 70}{RESET}")
    lines.append("")

    # Original sentence
    lines.append(f"  {DIM}Sentence:{RESET} {result['original']}")
    lines.append("")

    # POS tags with color
    tagged_display = []
    for word, tag in result["pos_tags"]:
        color = TAG_COLORS.get(tag, DIM)
        tagged_display.append(f"{color}{word}{RESET}{DIM}[{tag}]{RESET}")
    lines.append(f"  {DIM}Parse:{RESET}")
    lines.append(f"    {' '.join(tagged_display)}")
    lines.append("")

    # Score and grade
    grade = result["grade"]
    if grade == "A":
        grade_color = GREEN
    elif grade in ("B", "C"):
        grade_color = YELLOW
    else:
        grade_color = RED

    score_color = GREEN if result["score"] >= 75 else (YELLOW if result["score"] >= 50 else RED)
    lines.append(f"  {BOLD}Score:{RESET} {score_color}{result['score']}/100{RESET}  "
                 f"{BOLD}Grade:{RESET} {grade_color}{grade}{RESET}")
    lines.append("")

    # Checks
    lines.append(f"  {DIM}--- Structural Checks ---{RESET}")

    def check_line(label, passed, detail=""):
        mark = f"{GREEN}[PASS]{RESET}" if passed else f"{RED}[FAIL]{RESET}"
        d = f"  {DIM}{detail}{RESET}" if detail else ""
        return f"    {mark} {label}{d}"

    lines.append(check_line(
        "Begins with preposition",
        result["starts_with_preposition"] and result["valid_preposition"],
        "(now-time: FOR/BY/OF/WITH/IN/AGAINST)" if result["valid_preposition"] else ""
    ))
    lines.append(check_line(
        f"Noun count: {result['noun_count']}",
        result["noun_count"] >= 2,
        "fact-carriers"
    ))
    lines.append(check_line(
        "Gerund verbs (-ING)",
        result["has_gerund_verbs"]
    ))
    lines.append(check_line(
        "No past tense",
        not result["has_past_tense"],
        "(dead time = fiction)" if result["has_past_tense"] else ""
    ))
    lines.append(check_line(
        "No future/modal verbs",
        not result["has_future_tense"],
        "(SHALL/WILL/etc. = fiction)" if result["has_future_tense"] else ""
    ))
    lines.append(check_line(
        "No null adverb-verb chains",
        not result["has_null_chain"]
    ))
    lines.append(check_line(
        "No pronouns",
        not result["has_pronouns"]
    ))
    lines.append(check_line(
        "Proper closure",
        result.get("has_closure", False)
    ))

    # Issues
    if result["issues"]:
        lines.append("")
        lines.append(f"  {RED}{BOLD}Issues:{RESET}")
        for issue in result["issues"]:
            lines.append(f"    {RED}* {issue}{RESET}")

    # Corrections
    if result["corrections"]:
        lines.append("")
        lines.append(f"  {GOLD}{BOLD}Corrections:{RESET}")
        for corr in result["corrections"]:
            lines.append(f"    {GOLD}-> {corr}{RESET}")

    lines.append("")
    lines.append(f"{CYAN}{'=' * 70}{RESET}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Built-in examples
# ---------------------------------------------------------------------------

EXAMPLES = [
    {
        "label": "CORRECT: Parse-syntax valid sentence",
        "sentence": "FOR THE CLAIMING OF THE LAND BY THE LIVING MAN",
    },
    {
        "label": "FRAUDULENT: Typical court order (null chain)",
        "sentence": "The court hereby orders that you shall forthwith pay the sum",
    },
    {
        "label": "FRAUDULENT: Past tense / pronoun / no preposition",
        "sentence": "He was found guilty",
    },
    {
        "label": "FRAUDULENT: Future fiction / modal verbs",
        "sentence": "The defendant shall appear before the court and will pay all fines",
    },
    {
        "label": "FRAUDULENT: Adverb-verb chain / no facts",
        "sentence": "Whereas the party hereby agrees and shall forthwith comply therewith",
    },
    {
        "label": "CORRECT: Prepositional grounding with nouns",
        "sentence": "BY THE AUTHORITY OF THE LIVING CLAIM FOR THE LAND",
    },
    {
        "label": "FRAUDULENT: Contract language with fiction markers",
        "sentence": "The borrower shall make monthly payments to the lender from the date of execution",
    },
]


def run_examples():
    """Run all built-in examples and print results."""
    for ex in EXAMPLES:
        print(f"\n{BOLD}{BLUE}  [{ex['label']}]{RESET}")
        result = analyze_sentence(ex["sentence"])
        print(format_analysis(result))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="C.S.S.C.P.S.G.P. Sentence Analyzer — Parse-Syntax Grammar Analysis"
    )
    parser.add_argument(
        "sentence",
        nargs="?",
        help="Sentence to analyze"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Run built-in example analyses"
    )

    args = parser.parse_args()

    if args.examples:
        run_examples()
    elif args.sentence:
        result = analyze_sentence(args.sentence)
        print(format_analysis(result))
    else:
        parser.print_help()
        print(f"\n{DIM}  Try: python src/sentence_analyzer.py --examples{RESET}")


if __name__ == "__main__":
    main()
