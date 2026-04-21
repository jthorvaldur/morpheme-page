"""
case_analyzer.py — Case Form & Hyphenation Jurisdiction Classifier

Analyzes text forms to determine their jurisdictional classification
based on case (upper/lower/mixed) and hyphenation patterns.

The Jurisdiction Map:
  JOHN DOE       -> DOG-LATIN / GLOSSA     -> Maritime / Dead / Corporate   -> FRAUDULENT
  JOHN-DOE       -> Correct Latin Sign Lang -> Latin / Connected Quantum     -> VALID
  :John-Doe:     -> Parse-Syntax Correct    -> Quantum / Now-Time / Living   -> CORRECT
  John Doe       -> English proper noun     -> Common Law / Living           -> VALID
  john doe       -> Diminished              -> No standing                   -> WARNING
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dog_latin_detector import classify_token, scan_document, highlight_dog_latin

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
# Status colors
# ---------------------------------------------------------------------------
STATUS_COLORS = {
    "FRAUDULENT": RED,
    "VALID": GREEN,
    "CORRECT": GOLD,
    "WARNING": YELLOW,
    "N/A": DIM,
}

JURISDICTION_COLORS = {
    "Maritime / Dead / Corporate": RED,
    "Latin / Connected Quantum": GREEN,
    "Quantum / Now-Time / Living": GOLD,
    "Common Law / Living": GREEN,
    "No standing": YELLOW,
}

# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyze_case_form(text: str) -> dict:
    """Analyze a text string's case form and return jurisdictional classification.

    Returns:
        - text: original text
        - form_type: DOG_LATIN | CORRECT_SIGN | PARSE_SYNTAX | ENGLISH | DIMINISHED | MIXED
        - jurisdiction: str
        - status: FRAUDULENT | VALID | CORRECT | WARNING
        - explanation: str
        - tokens: list of individual token classifications
    """
    tokens = text.split()
    token_results = []

    for t in tokens:
        token_results.append(classify_token(t))

    # Determine overall form from token analysis
    form_types = set()
    for tr in token_results:
        ft = tr["form_type"]
        if ft not in ("STOP", "NUMERIC", "PUNCT", "UNKNOWN"):
            form_types.add(ft)

    # Determine overall classification
    if len(form_types) == 0:
        form_type = "UNKNOWN"
        jurisdiction = "Undetermined"
        status = "N/A"
        explanation = "No classifiable content."
    elif form_types == {"PARSE_SYNTAX"}:
        form_type = "PARSE_SYNTAX"
        jurisdiction = "Quantum / Now-Time / Living"
        status = "CORRECT"
        explanation = (
            "Parse-syntax correct form. Colon-bounded, hyphenated. "
            "Addresses a living being in now-time quantum grammar. "
            "This is the CORRECT form for identifying a living man or woman."
        )
    elif form_types == {"CORRECT_SIGN"}:
        form_type = "CORRECT_SIGN"
        jurisdiction = "Latin / Connected Quantum"
        status = "VALID"
        explanation = (
            "Correct Latin Sign Language. Hyphens bond the signs into connected "
            "quanta of meaning. Each hyphenated compound is a single quantum. VALID."
        )
    elif form_types == {"DOG_LATIN"} or (form_types == {"DOG_LATIN", "STOP"}):
        form_type = "DOG_LATIN"
        jurisdiction = "Maritime / Dead / Corporate"
        status = "FRAUDULENT"
        explanation = (
            "DOG-LATIN / GLOSSA. Unhyphenated all-uppercase. Each word is a separate, "
            "disconnected symbol with no grammatical bond to its neighbors. "
            "Addresses a corporate fiction / dead entity, not a living being. "
            "Per Black's Law 4th Ed: 'the language of the illiterate.' FRAUDULENT."
        )
    elif form_types == {"DIMINISHED"}:
        form_type = "DIMINISHED"
        jurisdiction = "No standing"
        status = "WARNING"
        explanation = (
            "Diminished form. All lowercase carries no standing, no authority, "
            "no claim. The identity is reduced to nothing."
        )
    elif "ENGLISH" in form_types or "ENGLISH_HYPHENATED" in form_types:
        if "DOG_LATIN" in form_types:
            form_type = "MIXED_DOG_LATIN"
            jurisdiction = "MIXED — Maritime + Common Law"
            status = "FRAUDULENT"
            explanation = (
                "Mixed jurisdiction. Contains both DOG-LATIN (corporate fiction) "
                "and English (living) forms. Per Chicago Manual of Styles Art. 11:147: "
                "two languages cannot share jurisdiction on one document. VOID."
            )
        else:
            form_type = "ENGLISH"
            jurisdiction = "Common Law / Living"
            status = "VALID"
            explanation = (
                "English proper noun. Mixed case (capital first letter). Addresses a "
                "living being under common law jurisdiction. VALID."
            )
    else:
        # Mixed forms
        if "DOG_LATIN" in form_types:
            form_type = "MIXED_DOG_LATIN"
            jurisdiction = "MIXED — jurisdictional conflict"
            status = "FRAUDULENT"
            explanation = (
                "Mixed jurisdictional forms detected. DOG-LATIN present alongside other "
                "forms. Document exhibits jurisdictional fraud."
            )
        else:
            form_type = "MIXED"
            jurisdiction = "Mixed"
            status = "WARNING"
            explanation = "Multiple form types detected. Verify jurisdictional consistency."

    return {
        "text": text,
        "form_type": form_type,
        "jurisdiction": jurisdiction,
        "status": status,
        "explanation": explanation,
        "tokens": token_results,
    }


# ---------------------------------------------------------------------------
# Form comparison
# ---------------------------------------------------------------------------

def compare_forms(name: str) -> list[dict]:
    """Take a name and generate all possible forms with jurisdictions.

    Given a name like "John Doe", produces:
        JOHN DOE        -> DOG-LATIN
        JOHN-DOE        -> Correct Latin Sign Language
        :John-Doe:      -> Parse-Syntax Correct
        John Doe        -> English
        john doe        -> Diminished
    """
    # Normalize the name to parts
    # Strip colons, hyphens for base parts
    cleaned = re.sub(r'[:.]', '', name)
    parts = re.split(r'[\s-]+', cleaned)
    parts = [p for p in parts if p]

    if not parts:
        return []

    forms = []

    # 1. DOG-LATIN: ALL CAPS, no hyphens
    dog_latin = " ".join(p.upper() for p in parts)
    forms.append(analyze_case_form(dog_latin))

    # 2. Correct Latin Sign Language: ALL CAPS with hyphens
    correct_sign = "-".join(p.upper() for p in parts)
    forms.append(analyze_case_form(correct_sign))

    # 3. Parse-Syntax Correct: :Title-Case-Hyphenated:
    # Each name part gets its own colon-bounded form
    parse_parts = []
    for p in parts:
        titled = p.capitalize()
        parse_parts.append(f":{titled}:")
    parse_syntax = " ".join(parse_parts)
    forms.append(analyze_case_form(parse_syntax))

    # Also show the full hyphenated parse form if multi-part
    if len(parts) > 1:
        full_parse = ":" + "-".join(p.capitalize() for p in parts) + ":"
        forms.append(analyze_case_form(full_parse))

    # 4. English proper noun: Title Case
    english = " ".join(p.capitalize() for p in parts)
    forms.append(analyze_case_form(english))

    # 5. Diminished: all lowercase
    diminished = " ".join(p.lower() for p in parts)
    forms.append(analyze_case_form(diminished))

    return forms


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_comparison(results: list[dict]) -> str:
    """Format a comparison of case forms as a pretty table."""
    lines = []
    lines.append("")
    lines.append(f"{BOLD}{CYAN}{'=' * 78}{RESET}")
    lines.append(f"{BOLD}  CASE FORM JURISDICTION COMPARISON{RESET}")
    lines.append(f"{CYAN}{'=' * 78}{RESET}")
    lines.append("")

    # Table header
    h_form = "FORM"
    h_type = "CLASSIFICATION"
    h_jur = "JURISDICTION"
    h_stat = "STATUS"
    lines.append(f"  {DIM}{h_form:<28} {h_type:<22} {h_jur:<26} {h_stat}{RESET}")
    lines.append(f"  {DIM}{'-' * 28} {'-' * 22} {'-' * 26} {'-' * 10}{RESET}")

    for r in results:
        form_text = r["text"]
        form_type = r["form_type"]
        jurisdiction = r["jurisdiction"]
        status = r["status"]

        s_color = STATUS_COLORS.get(status, DIM)
        j_color = JURISDICTION_COLORS.get(jurisdiction, DIM)

        # Truncate long values
        if len(form_text) > 26:
            form_display = form_text[:23] + "..."
        else:
            form_display = form_text

        if len(jurisdiction) > 24:
            jur_display = jurisdiction[:21] + "..."
        else:
            jur_display = jurisdiction

        lines.append(
            f"  {s_color}{form_display:<28}{RESET} "
            f"{DIM}{form_type:<22}{RESET} "
            f"{j_color}{jur_display:<26}{RESET} "
            f"{s_color}{BOLD}{status}{RESET}"
        )

    lines.append("")

    # Explanations
    lines.append(f"  {DIM}--- Explanations ---{RESET}")
    for r in results:
        s_color = STATUS_COLORS.get(r["status"], DIM)
        lines.append(f"  {s_color}{r['text']}{RESET}")
        lines.append(f"    {DIM}{r['explanation']}{RESET}")
        lines.append("")

    lines.append(f"{CYAN}{'=' * 78}{RESET}")
    return "\n".join(lines)


def format_single_analysis(result: dict) -> str:
    """Format a single case form analysis."""
    lines = []
    lines.append("")
    lines.append(f"{BOLD}{CYAN}{'=' * 70}{RESET}")
    lines.append(f"{BOLD}  CASE FORM ANALYSIS{RESET}")
    lines.append(f"{CYAN}{'=' * 70}{RESET}")
    lines.append("")

    s_color = STATUS_COLORS.get(result["status"], DIM)

    lines.append(f"  {DIM}Text:{RESET}          {highlight_dog_latin(result['text'])}")
    lines.append(f"  {DIM}Form Type:{RESET}     {result['form_type']}")

    j_color = JURISDICTION_COLORS.get(result["jurisdiction"], DIM)
    lines.append(f"  {DIM}Jurisdiction:{RESET}  {j_color}{result['jurisdiction']}{RESET}")
    lines.append(f"  {DIM}Status:{RESET}        {s_color}{BOLD}{result['status']}{RESET}")
    lines.append("")
    lines.append(f"  {s_color}{result['explanation']}{RESET}")

    # Token breakdown
    if result["tokens"]:
        lines.append("")
        lines.append(f"  {DIM}--- Token Breakdown ---{RESET}")
        for tr in result["tokens"]:
            tc = STATUS_COLORS.get(tr["status"], DIM)
            lines.append(f"    {tc}{tr['cleaned']:<20}{RESET} {DIM}{tr['form_type']:<18} {tr['jurisdiction']}{RESET}")

    lines.append("")
    lines.append(f"{CYAN}{'=' * 70}{RESET}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Built-in comparisons
# ---------------------------------------------------------------------------

BUILTIN_NAMES = [
    "John James Public",
    "Mary Jane Smith",
    "David Wynn Miller",
    "Russell Jay Gould",
    "United States of America",
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Case Form Jurisdiction Analyzer — Classify text by case/hyphen form"
    )
    parser.add_argument(
        "form",
        nargs="?",
        help="Text form to analyze (e.g., 'JOHN DOE' or ':John-Doe:')"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run built-in comparisons showing all forms for common names"
    )
    parser.add_argument(
        "--compare-name",
        type=str,
        metavar="NAME",
        help="Generate all forms for a specific name"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode"
    )

    args = parser.parse_args()

    if args.compare:
        for name in BUILTIN_NAMES:
            print(f"\n{BOLD}{BLUE}  Comparing forms for: {name}{RESET}")
            results = compare_forms(name)
            print(format_comparison(results))
    elif args.compare_name:
        results = compare_forms(args.compare_name)
        print(format_comparison(results))
    elif args.interactive:
        print(f"\n{BOLD}{CYAN}CASE FORM ANALYZER — Interactive Mode{RESET}")
        print(f"{DIM}Enter a name or text form. Type 'compare NAME' to compare all forms.{RESET}")
        print(f"{DIM}Type 'quit' or 'exit' to stop.{RESET}\n")
        while True:
            try:
                text = input(f"{CYAN}> {RESET}")
            except (EOFError, KeyboardInterrupt):
                print(f"\n{DIM}Exiting.{RESET}")
                break
            if text.strip().lower() in ("quit", "exit", "q"):
                break
            if text.strip().lower().startswith("compare "):
                name = text.strip()[8:]
                results = compare_forms(name)
                print(format_comparison(results))
            elif text.strip():
                result = analyze_case_form(text.strip())
                print(format_single_analysis(result))
    elif args.form:
        result = analyze_case_form(args.form)
        print(format_single_analysis(result))
    else:
        parser.print_help()
        print(f"\n{DIM}  Try: python src/case_analyzer.py --compare{RESET}")
        print(f"{DIM}  Or:  python src/case_analyzer.py 'JOHN DOE'{RESET}")
        print(f"{DIM}  Or:  python src/case_analyzer.py ':John-Doe:'{RESET}")


if __name__ == "__main__":
    main()
