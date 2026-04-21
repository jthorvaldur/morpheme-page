"""
document_evaluator.py — Comprehensive Legal Document Evaluator

Evaluates legal documents using ALL analysis tools:
  - sentence_analyzer: C.S.S.C.P.S.G.P. compliance
  - adverb_verb_detector: null chain detection
  - dog_latin_detector: DOG-LATIN / GLOSSA detection
  - case_analyzer: case form jurisdiction classification
  - word_parser: morpheme decomposition (optional)

Combines all analyses into a unified evaluation with overall grade,
jurisdiction assessment, and detailed findings.
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sentence_analyzer import analyze_sentence, format_analysis
from adverb_verb_detector import detect_null_chains, score_factual_content, highlight_null_chains
from dog_latin_detector import scan_document, highlight_dog_latin, detect_dog_latin
from case_analyzer import analyze_case_form

# Optional: word_parser may not exist yet
try:
    from word_parser import parse_word
    HAS_WORD_PARSER = True
except ImportError:
    HAS_WORD_PARSER = False

    def parse_word(word: str) -> dict:
        """Stub when word_parser is not available."""
        return {"word": word, "available": False}

# ---------------------------------------------------------------------------
# ANSI color codes
# ---------------------------------------------------------------------------
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
GOLD = "\033[93m"
BLUE = "\033[34m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ---------------------------------------------------------------------------
# Built-in document excerpts
# ---------------------------------------------------------------------------

BUILTIN_DOCUMENTS = {
    "declaration": {
        "title": "Declaration of Independence (Opening)",
        "text": (
            "When in the Course of human Events, it becomes necessary for one People "
            "to dissolve the Political Bands which have connected them with another, "
            "and to assume among the Powers of the Earth, the separate and equal "
            "Station to which the Laws of Nature and of Nature's God entitle them, "
            "a decent Respect to the Opinions of Mankind requires that they should "
            "declare the causes which impel them to the Separation."
        ),
    },
    "constitution": {
        "title": "US Constitution Preamble",
        "text": (
            "We the People of the United States, in Order to form a more perfect "
            "Union, establish Justice, insure domestic Tranquility, provide for the "
            "common defence, promote the general Welfare, and secure the Blessings "
            "of Liberty to ourselves and our Posterity, do ordain and establish this "
            "Constitution for the United States of America."
        ),
    },
    "first_amendment": {
        "title": "First Amendment",
        "text": (
            "Congress shall make no law respecting an establishment of religion, "
            "or prohibiting the free exercise thereof; or abridging the freedom of "
            "speech, or of the press; or the right of the people peaceably to "
            "assemble, and to petition the Government for a redress of grievances."
        ),
    },
    "court_order": {
        "title": "Sample Court Order",
        "text": (
            "IT IS HEREBY ORDERED, ADJUDGED AND DECREED that the Defendant, "
            "JOHN JAMES DOE, shall forthwith appear before this Court and shall "
            "pay to the Plaintiff the sum of TEN THOUSAND DOLLARS ($10,000.00), "
            "together with all costs and fees thereof, and that the Defendant shall "
            "comply with all terms and conditions herein set forth, notwithstanding "
            "any prior agreements to the contrary."
        ),
    },
    "mortgage": {
        "title": "Sample Mortgage Contract Language",
        "text": (
            "THE BORROWER hereby covenants and agrees that the BORROWER shall make "
            "monthly payments of principal and interest to the LENDER at the address "
            "stated herein. The BORROWER further agrees that upon default in any "
            "payment, the entire unpaid balance shall immediately become due and "
            "payable, and the LENDER may forthwith proceed to foreclose upon the "
            "PROPERTY described herein. THE BORROWER acknowledges that this MORTGAGE "
            "constitutes a lien upon said PROPERTY."
        ),
    },
    "birth_certificate": {
        "title": "Birth Certificate Language",
        "text": (
            "CERTIFICATE OF LIVE BIRTH\n"
            "STATE OF CALIFORNIA\n"
            "DEPARTMENT OF PUBLIC HEALTH\n\n"
            "CHILD'S NAME: JOHN JAMES PUBLIC\n"
            "DATE OF BIRTH: JANUARY 15 1990\n"
            "PLACE OF BIRTH: LOS ANGELES CALIFORNIA\n"
            "MOTHER'S MAIDEN NAME: JANE MARIE SMITH\n"
            "FATHER'S NAME: ROBERT JAMES PUBLIC\n\n"
            "THIS IS TO CERTIFY THAT THE ABOVE IS A TRUE COPY OR ABSTRACT "
            "OF THE RECORD ON FILE IN THE STATE REGISTRAR'S OFFICE."
        ),
    },
    "traffic_ticket": {
        "title": "Traffic Ticket Language",
        "text": (
            "CITATION NUMBER: 2024-TC-00847\n"
            "THE PEOPLE OF THE STATE OF CALIFORNIA\n"
            "VS.\n"
            "JOHN Q PUBLIC\n\n"
            "YOU ARE HEREBY NOTIFIED that you did unlawfully operate a motor "
            "vehicle in excess of the posted speed limit. You are ordered to "
            "appear before the TRAFFIC COURT of the COUNTY OF LOS ANGELES "
            "on the date specified below or pay the fine indicated."
        ),
    },
    "correct_claim": {
        "title": "Correct Parse-Syntax Claim",
        "text": (
            "FOR THE ESTABLISHING OF THE CLAIM BY THE LIVING :John-James: :Public: "
            "OF THE LAND AND SOIL JURISDICTION IN THE STATE OF CALIFORNIA "
            "BY THE AUTHORITY OF THE LIVING BEING "
            "FOR THE CORRECTING OF THE FRAUDULENT RECORD "
            "WITH THE CLAIMING OF THE BIRTH-RIGHT "
            "BY THE STANDING OF THE MAN ON THE LAND."
        ),
    },
}

# ---------------------------------------------------------------------------
# Document evaluation
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences. Handle newlines as sentence breaks too."""
    # Replace newlines with period-space if they don't already end sentences
    normalized = re.sub(r'\n+', '. ', text)
    # Split on sentence-ending punctuation
    raw = re.split(r'(?<=[.!?])\s+', normalized)
    sentences = []
    for s in raw:
        s = s.strip()
        if s and len(s) > 3:
            sentences.append(s)
    return sentences


def evaluate_document(text: str, title: str = "") -> dict:
    """Evaluate a legal document using all analysis tools.

    Returns:
        - title: str
        - text: original text
        - sentence_analyses: list of sentence analysis dicts
        - avg_sentence_score: float
        - dog_latin_scan: document scan result
        - dog_latin_pct: float
        - null_chains: list of detected null chains
        - null_chain_count: int
        - factual_score: dict from score_factual_content
        - case_form: overall case form analysis
        - overall_score: int (0-100)
        - overall_grade: str (A-F)
        - jurisdiction: str (primary jurisdiction determination)
        - findings: list[str]
        - recommendations: list[str]
    """
    findings = []
    recommendations = []

    # 1. Sentence-level analysis
    sentences = _split_sentences(text)
    sentence_analyses = []
    total_sentence_score = 0

    for sent in sentences:
        if len(sent.strip()) < 4:
            continue
        analysis = analyze_sentence(sent)
        sentence_analyses.append(analysis)
        total_sentence_score += analysis["score"]

    avg_sentence_score = (total_sentence_score / len(sentence_analyses)) if sentence_analyses else 0

    # 2. DOG-LATIN scan
    dl_scan = scan_document(text)
    dog_latin_pct = dl_scan["dog_latin_pct"]

    # 3. Null chain detection
    null_chains = detect_null_chains(text)
    null_chain_count = len(null_chains)

    # 4. Factual content score
    factual = score_factual_content(text)

    # 5. Overall case form analysis
    case_form = analyze_case_form(text[:200])  # Analyze first 200 chars for overall form

    # ---------------------------------------------------------------------------
    # Compute overall score
    # ---------------------------------------------------------------------------
    overall_score = 100

    # Sentence structure score (40% weight)
    sentence_penalty = max(0, (100 - avg_sentence_score) * 0.4)
    overall_score -= sentence_penalty

    # DOG-LATIN penalty (25% weight)
    if dog_latin_pct > 0:
        dl_penalty = min(25, dog_latin_pct * 0.5)
        overall_score -= dl_penalty
        if dog_latin_pct > 50:
            findings.append(
                f"Document is {dog_latin_pct:.0f}% DOG-LATIN — predominantly addresses "
                "corporate fictions / dead entities."
            )
            recommendations.append(
                "Replace all DOG-LATIN (unhyphenated all-caps) with either English "
                "proper nouns or parse-syntax correct :Colon-Hyphen: forms."
            )
        elif dog_latin_pct > 10:
            findings.append(
                f"Document contains {dog_latin_pct:.0f}% DOG-LATIN — addresses "
                "corporate fiction alongside living text."
            )

    # Null chain penalty (20% weight)
    if null_chain_count > 0:
        nc_penalty = min(20, null_chain_count * 5)
        overall_score -= nc_penalty
        findings.append(
            f"Found {null_chain_count} null adverb-verb chain(s) — "
            "these constructions convey ZERO facts."
        )
        recommendations.append(
            "Replace adverb-verb chains with noun-fact constructions. "
            "A sentence without nouns carries no facts."
        )

    # Factual content penalty (15% weight)
    if factual["noun_count"] == 0:
        overall_score -= 15
        findings.append("ZERO nouns in document — carries NO factual content whatsoever.")
    elif factual["null_ratio"] > 0.4:
        overall_score -= 10
        findings.append(
            f"Document is {factual['null_ratio']:.0%} null words (adverbs + modal verbs). "
            "Dominated by empty modifiers."
        )

    # Jurisdiction mixing
    if dl_scan["jurisdiction_mixing"]:
        overall_score -= 10
        findings.append(
            "JURISDICTION MIXING detected — DOG-LATIN and English on the same document. "
            "Per Chicago Manual of Styles Art. 11:147, creates a jurisdictional void."
        )
        recommendations.append(
            "A document must use ONE consistent jurisdiction. Choose either "
            "parse-syntax (:Colon-Hyphen:) or English, never DOG-LATIN."
        )

    # Collect sentence-level issues
    all_issues = set()
    for sa in sentence_analyses:
        for issue in sa["issues"]:
            all_issues.add(issue)

    if any("past tense" in i.lower() for i in all_issues):
        findings.append(
            "Contains past tense markers — past tense = dead time = fiction. "
            "Cannot contract with the dead."
        )
        recommendations.append("Convert all past tense to now-time gerund (-ING) form.")

    if any("modal" in i.lower() or "future" in i.lower() for i in all_issues):
        findings.append(
            "Contains modal/future verbs (SHALL, WILL, WOULD, etc.) — "
            "future tense = fiction. Cannot contract with what hasn't happened."
        )
        recommendations.append(
            "Remove all modal verbs. State facts in now-time: "
            "'FOR THE CLAIMING...' not 'shall claim...'"
        )

    if any("pronoun" in i.lower() for i in all_issues):
        findings.append(
            "Contains pronouns — pronouns REMOVE the fact. "
            "'He shall pay' — WHO is 'he'? No fact established."
        )
        recommendations.append("Replace all pronouns with actual nouns/names.")

    overall_score = max(0, int(overall_score))

    # Grade
    if overall_score >= 90:
        grade = "A"
    elif overall_score >= 75:
        grade = "B"
    elif overall_score >= 60:
        grade = "C"
    elif overall_score >= 40:
        grade = "D"
    else:
        grade = "F"

    # Primary jurisdiction determination
    if dl_scan["dog_latin_pct"] > 50:
        jurisdiction = "Maritime / Admiralty (Sea) — Dead / Corporate"
    elif dl_scan["parse_syntax_count"] > 0 and dl_scan["dog_latin_count"] == 0:
        jurisdiction = "Quantum / Now-Time / Living (Land & Soil)"
    elif dl_scan["jurisdiction_mixing"]:
        jurisdiction = "MIXED / VOID — jurisdictional conflict"
    elif dl_scan["english_count"] > 0 and dl_scan["dog_latin_count"] == 0:
        jurisdiction = "Common Law / Living (Land)"
    else:
        jurisdiction = "Indeterminate — requires further analysis"

    return {
        "title": title,
        "text": text,
        "sentence_analyses": sentence_analyses,
        "avg_sentence_score": round(avg_sentence_score, 1),
        "dog_latin_scan": dl_scan,
        "dog_latin_pct": dog_latin_pct,
        "null_chains": null_chains,
        "null_chain_count": null_chain_count,
        "factual_score": factual,
        "case_form": case_form,
        "overall_score": overall_score,
        "overall_grade": grade,
        "jurisdiction": jurisdiction,
        "findings": findings,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_evaluation(result: dict) -> str:
    """Format a full document evaluation as colored terminal output."""
    lines = []
    lines.append("")
    lines.append(f"{BOLD}{MAGENTA}{'#' * 78}{RESET}")
    title = result["title"] or "Document Evaluation"
    lines.append(f"{BOLD}{MAGENTA}##  {title.upper()}{RESET}")
    lines.append(f"{MAGENTA}{'#' * 78}{RESET}")
    lines.append("")

    # Overall score and grade
    score = result["overall_score"]
    grade = result["overall_grade"]

    if grade == "A":
        grade_color = GREEN
    elif grade in ("B", "C"):
        grade_color = YELLOW
    else:
        grade_color = RED

    score_color = GREEN if score >= 75 else (YELLOW if score >= 50 else RED)

    lines.append(f"  {BOLD}OVERALL SCORE:{RESET} {score_color}{BOLD}{score}/100{RESET}    "
                 f"{BOLD}GRADE:{RESET} {grade_color}{BOLD}{grade}{RESET}")
    lines.append("")

    # Jurisdiction
    jur = result["jurisdiction"]
    if "Maritime" in jur or "Dead" in jur or "VOID" in jur:
        j_color = RED
    elif "Quantum" in jur or "Living" in jur:
        j_color = GOLD
    elif "Common Law" in jur:
        j_color = GREEN
    else:
        j_color = YELLOW
    lines.append(f"  {BOLD}JURISDICTION:{RESET} {j_color}{jur}{RESET}")
    lines.append("")

    # Document text (highlighted)
    lines.append(f"  {DIM}--- Document Text (highlighted) ---{RESET}")
    highlighted = highlight_dog_latin(result["text"])
    for line in highlighted.split("\n"):
        lines.append(f"    {line}")
    lines.append("")

    # Component scores
    lines.append(f"  {DIM}--- Component Analysis ---{RESET}")
    lines.append("")

    # Sentence structure
    avg_ss = result["avg_sentence_score"]
    ss_color = GREEN if avg_ss >= 75 else (YELLOW if avg_ss >= 50 else RED)
    lines.append(f"    {BOLD}Sentence Structure (C.S.S.C.P.S.G.P.):{RESET} {ss_color}{avg_ss:.0f}/100{RESET}")
    lines.append(f"    {DIM}Sentences analyzed: {len(result['sentence_analyses'])}{RESET}")

    # Show worst sentences
    worst = sorted(result["sentence_analyses"], key=lambda x: x["score"])[:3]
    if worst:
        lines.append(f"    {DIM}Lowest-scoring sentences:{RESET}")
        for w in worst:
            w_color = GREEN if w["score"] >= 75 else (YELLOW if w["score"] >= 50 else RED)
            orig = w["original"]
            if len(orig) > 60:
                orig = orig[:57] + "..."
            lines.append(f"      {w_color}[{w['score']}]{RESET} {DIM}{orig}{RESET}")
    lines.append("")

    # DOG-LATIN
    dl_pct = result["dog_latin_pct"]
    dl_color = RED if dl_pct > 10 else (YELLOW if dl_pct > 0 else GREEN)
    lines.append(f"    {BOLD}DOG-LATIN Content:{RESET} {dl_color}{dl_pct:.0f}%{RESET}")
    dl_scan = result["dog_latin_scan"]
    lines.append(f"    {DIM}DOG-LATIN tokens: {dl_scan['dog_latin_count']} | "
                 f"English tokens: {dl_scan['english_count']} | "
                 f"Parse-syntax: {dl_scan['parse_syntax_count']}{RESET}")
    if dl_scan["jurisdiction_mixing"]:
        lines.append(f"    {RED}{BOLD}** JURISDICTION MIXING **{RESET}")
    lines.append("")

    # Null chains
    nc = result["null_chain_count"]
    nc_color = RED if nc > 0 else GREEN
    lines.append(f"    {BOLD}Null Adverb-Verb Chains:{RESET} {nc_color}{nc} found{RESET}")
    for chain in result["null_chains"][:3]:
        lines.append(f"      {RED}\"{chain['text']}\"{RESET}")
    lines.append("")

    # Factual content
    fs = result["factual_score"]
    fr = fs["factual_ratio"]
    fr_color = GREEN if fr >= 0.3 else (YELLOW if fr >= 0.15 else RED)
    lines.append(f"    {BOLD}Factual Content:{RESET} {fr_color}{fr:.0%}{RESET} "
                 f"{DIM}({fs['noun_count']} nouns, {fs['null_word_count']} null words){RESET}")
    lines.append(f"    {DIM}{fs['assessment']}{RESET}")
    lines.append("")

    # Findings
    if result["findings"]:
        lines.append(f"  {RED}{BOLD}--- FINDINGS ---{RESET}")
        for i, f in enumerate(result["findings"], 1):
            lines.append(f"    {RED}{i}. {f}{RESET}")
        lines.append("")

    # Recommendations
    if result["recommendations"]:
        lines.append(f"  {GOLD}{BOLD}--- RECOMMENDATIONS ---{RESET}")
        for i, r in enumerate(result["recommendations"], 1):
            lines.append(f"    {GOLD}{i}. {r}{RESET}")
        lines.append("")

    lines.append(f"{MAGENTA}{'#' * 78}{RESET}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def list_builtins():
    """List available built-in documents."""
    print(f"\n{BOLD}{CYAN}Available Built-in Documents:{RESET}\n")
    for key, doc in BUILTIN_DOCUMENTS.items():
        print(f"  {GOLD}{key:<22}{RESET} {DIM}{doc['title']}{RESET}")
    print(f"\n{DIM}Usage: python src/document_evaluator.py --builtin <name>{RESET}")
    print(f"{DIM}       python src/document_evaluator.py --all{RESET}")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Comprehensive Legal Document Evaluator — All analysis tools combined"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to evaluate"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all built-in documents"
    )
    parser.add_argument(
        "--builtin",
        type=str,
        metavar="NAME",
        help="Evaluate a specific built-in document (use --list to see names)"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to file to evaluate"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available built-in documents"
    )

    args = parser.parse_args()

    if args.list:
        list_builtins()
    elif args.all:
        for key, doc in BUILTIN_DOCUMENTS.items():
            result = evaluate_document(doc["text"], doc["title"])
            print(format_evaluation(result))
            print()
    elif args.builtin:
        key = args.builtin.lower().replace("-", "_").replace(" ", "_")
        if key not in BUILTIN_DOCUMENTS:
            print(f"{RED}Unknown document: '{args.builtin}'{RESET}")
            list_builtins()
            sys.exit(1)
        doc = BUILTIN_DOCUMENTS[key]
        result = evaluate_document(doc["text"], doc["title"])
        print(format_evaluation(result))
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"{RED}Error: File not found: {args.file}{RESET}")
            sys.exit(1)
        text = path.read_text()
        title = path.name
        result = evaluate_document(text, title)
        print(format_evaluation(result))
    elif args.text:
        result = evaluate_document(args.text)
        print(format_evaluation(result))
    else:
        parser.print_help()
        print(f"\n{DIM}  Try: python src/document_evaluator.py --all{RESET}")
        print(f"{DIM}  Or:  python src/document_evaluator.py --list{RESET}")
        print(f"{DIM}  Or:  python src/document_evaluator.py --builtin court_order{RESET}")


if __name__ == "__main__":
    main()
