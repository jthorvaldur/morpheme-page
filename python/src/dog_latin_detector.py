"""
dog_latin_detector.py — DOG-LATIN / GLOSSA Detection Engine

DOG-LATIN (GLOSSA) is unhyphenated all-uppercase text that follows English
grammatical rules but uses Latin symbolic form. It is neither English nor
Latin. Per Black's Law Dictionary (4th Ed): "the language of the illiterate."

Per Chicago Manual of Styles Art. 11:147: a foreign language text has NO
JURISDICTION with another language on the same page. DOG-LATIN on the same
document as English creates a jurisdictional void.

Classification:
  ALL CAPS, no hyphens  -> DOG-LATIN (maritime / dead / corporate)
  ALL CAPS, with hyphens -> Correct Latin Sign Language (valid)
  :Colon-Hyphen-Form:   -> Parse-Syntax Correct (quantum / now-time / living)
  Mixed case             -> English proper noun (common law / living)
  All lowercase          -> Diminished (no standing)
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
# Token classification
# ---------------------------------------------------------------------------

# Short words that are not DOG-LATIN even in all-caps context
STOP_WORDS = {
    "A", "AN", "THE", "OF", "FOR", "BY", "IN", "TO", "AT", "ON",
    "IS", "IT", "OR", "AS", "IF", "SO", "NO", "DO", "BE", "AM",
    "VS", "VS.", "AND", "BUT", "NOR", "NOT", "YET",
}


def classify_token(token: str) -> dict:
    """Classify a single token by its case/hyphen form.

    Returns:
        - token: original token
        - cleaned: token with surrounding punctuation stripped
        - form_type: DOG_LATIN | CORRECT_SIGN | PARSE_SYNTAX | ENGLISH | DIMINISHED | STOP | NUMERIC | PUNCT
        - jurisdiction: Maritime/Dead/Corporate | Latin/Connected | Quantum/Now-Time/Living | Common Law/Living | No standing | N/A
        - status: FRAUDULENT | VALID | CORRECT | WARNING | N/A
        - explanation: human-readable explanation
    """
    # Parse-syntax correct: :Colon-Hyphen-Form: — check BEFORE stripping colons
    # Also match single-word forms like :John: (min 1 alpha char between colons)
    if re.match(r'^:[\w][\w-]*:$', token.strip(".,;!?\"'()[]{}#")):
        cleaned_ps = token.strip(".,;!?\"'()[]{}#")
        return {
            "token": token,
            "cleaned": cleaned_ps,
            "form_type": "PARSE_SYNTAX",
            "jurisdiction": "Quantum / Now-Time / Living",
            "status": "CORRECT",
            "explanation": "Parse-syntax correct form — colon-bounded, hyphenated. Living claim in now-time.",
        }

    cleaned = token.strip(".,;:!?\"'()[]{}#")
    if not cleaned:
        return {
            "token": token,
            "cleaned": "",
            "form_type": "PUNCT",
            "jurisdiction": "N/A",
            "status": "N/A",
            "explanation": "Punctuation mark",
        }

    # Numeric
    if re.match(r'^[\d.,/$%]+$', cleaned):
        return {
            "token": token,
            "cleaned": cleaned,
            "form_type": "NUMERIC",
            "jurisdiction": "N/A",
            "status": "N/A",
            "explanation": "Numeric value",
        }

    # Legacy parse-syntax check (should not reach here, but just in case)
    if re.match(r'^:[\w][\w-]*:$', cleaned):
        return {
            "token": token,
            "cleaned": cleaned,
            "form_type": "PARSE_SYNTAX",
            "jurisdiction": "Quantum / Now-Time / Living",
            "status": "CORRECT",
            "explanation": "Parse-syntax correct form — colon-bounded, hyphenated. Living claim in now-time.",
        }

    # Check if contains hyphens
    has_hyphens = "-" in cleaned

    # All uppercase check (ignoring hyphens, digits)
    alpha_only = re.sub(r'[^a-zA-Z]', '', cleaned)
    if not alpha_only:
        return {
            "token": token,
            "cleaned": cleaned,
            "form_type": "PUNCT",
            "jurisdiction": "N/A",
            "status": "N/A",
            "explanation": "Non-alphabetic token",
        }

    is_all_upper = alpha_only.isupper()
    is_all_lower = alpha_only.islower()
    is_mixed = not is_all_upper and not is_all_lower

    # Stop words (short functional words) — not DOG-LATIN by themselves
    if cleaned.upper() in STOP_WORDS and len(alpha_only) <= 3:
        return {
            "token": token,
            "cleaned": cleaned,
            "form_type": "STOP",
            "jurisdiction": "N/A",
            "status": "N/A",
            "explanation": "Functional/grammatical word",
        }

    # ALL CAPS with hyphens — Correct Latin Sign Language
    if is_all_upper and has_hyphens:
        return {
            "token": token,
            "cleaned": cleaned,
            "form_type": "CORRECT_SIGN",
            "jurisdiction": "Latin / Connected Quantum",
            "status": "VALID",
            "explanation": "Correct Latin Sign Language — hyphens bond signs into connected quanta of meaning.",
        }

    # ALL CAPS without hyphens — DOG-LATIN
    if is_all_upper and not has_hyphens and len(alpha_only) > 1:
        return {
            "token": token,
            "cleaned": cleaned,
            "form_type": "DOG_LATIN",
            "jurisdiction": "Maritime / Dead / Corporate",
            "status": "FRAUDULENT",
            "explanation": "DOG-LATIN (GLOSSA) — unhyphenated all-caps. Addresses a corporate fiction, not a living being. "
                           "Per Black's Law 4th Ed: 'the language of the illiterate.'",
        }

    # All lowercase — diminished
    if is_all_lower:
        return {
            "token": token,
            "cleaned": cleaned,
            "form_type": "DIMINISHED",
            "jurisdiction": "No standing",
            "status": "WARNING",
            "explanation": "Diminished form — lowercase carries no standing or authority.",
        }

    # Mixed case — English
    if is_mixed:
        if has_hyphens and cleaned[0].isupper():
            return {
                "token": token,
                "cleaned": cleaned,
                "form_type": "ENGLISH_HYPHENATED",
                "jurisdiction": "Common Law / Living",
                "status": "VALID",
                "explanation": "Hyphenated English proper noun — common law, living jurisdiction.",
            }
        return {
            "token": token,
            "cleaned": cleaned,
            "form_type": "ENGLISH",
            "jurisdiction": "Common Law / Living",
            "status": "VALID",
            "explanation": "English proper noun or mixed-case word — common law, living jurisdiction.",
        }

    return {
        "token": token,
        "cleaned": cleaned,
        "form_type": "UNKNOWN",
        "jurisdiction": "Undetermined",
        "status": "N/A",
        "explanation": "Could not classify token form.",
    }


# ---------------------------------------------------------------------------
# Multi-token DOG-LATIN detection
# ---------------------------------------------------------------------------

def detect_dog_latin(text: str) -> list[dict]:
    """Find all DOG-LATIN tokens in text with positions.

    Returns a list of dicts, each with:
        - token: the word/phrase
        - start: character offset
        - end: character offset end
        - classification: result from classify_token
    """
    results = []
    # Tokenize preserving positions
    for match in re.finditer(r'\S+', text):
        token = match.group()
        start = match.start()
        end = match.end()
        classification = classify_token(token)
        if classification["form_type"] in ("DOG_LATIN", "CORRECT_SIGN", "PARSE_SYNTAX"):
            results.append({
                "token": token,
                "start": start,
                "end": end,
                "classification": classification,
            })
    return results


# ---------------------------------------------------------------------------
# Document scanning
# ---------------------------------------------------------------------------

def scan_document(text: str) -> dict:
    """Full document scan with statistics.

    Returns:
        - total_tokens: int
        - dog_latin_count: int
        - dog_latin_pct: float
        - correct_sign_count: int
        - parse_syntax_count: int
        - english_count: int
        - diminished_count: int
        - jurisdiction_mixing: bool
        - jurisdictions_found: list[str]
        - tokens: list of all classified tokens
        - warnings: list[str]
        - assessment: str
    """
    tokens = []
    counts = {
        "DOG_LATIN": 0,
        "CORRECT_SIGN": 0,
        "PARSE_SYNTAX": 0,
        "ENGLISH": 0,
        "ENGLISH_HYPHENATED": 0,
        "DIMINISHED": 0,
        "STOP": 0,
        "NUMERIC": 0,
        "PUNCT": 0,
        "UNKNOWN": 0,
    }

    for match in re.finditer(r'\S+', text):
        token = match.group()
        classification = classify_token(token)
        ft = classification["form_type"]
        counts[ft] = counts.get(ft, 0) + 1
        tokens.append({
            "token": token,
            "start": match.start(),
            "end": match.end(),
            "classification": classification,
        })

    # Content tokens exclude stops, numerics, and punctuation
    content_count = sum(v for k, v in counts.items()
                        if k not in ("STOP", "NUMERIC", "PUNCT", "UNKNOWN"))
    total = len(tokens)

    dog_latin_count = counts["DOG_LATIN"]
    dog_latin_pct = (dog_latin_count / content_count * 100) if content_count > 0 else 0.0

    english_count = counts["ENGLISH"] + counts["ENGLISH_HYPHENATED"]

    # Jurisdiction analysis
    jurisdictions_found = set()
    if dog_latin_count > 0:
        jurisdictions_found.add("Maritime / Dead / Corporate")
    if counts["CORRECT_SIGN"] > 0:
        jurisdictions_found.add("Latin / Connected Quantum")
    if counts["PARSE_SYNTAX"] > 0:
        jurisdictions_found.add("Quantum / Now-Time / Living")
    if english_count > 0:
        jurisdictions_found.add("Common Law / Living")
    if counts["DIMINISHED"] > 0:
        jurisdictions_found.add("No standing")

    jurisdiction_mixing = len(jurisdictions_found) > 1 and "Maritime / Dead / Corporate" in jurisdictions_found

    warnings = []
    if jurisdiction_mixing:
        warnings.append(
            "JURISDICTION MIXING — DOG-LATIN and English/living text on the same document. "
            "Per Chicago Manual of Styles Art. 11:147: a foreign language has NO JURISDICTION "
            "with another language on the same page."
        )
    if dog_latin_pct > 50:
        warnings.append(
            f"Document is {dog_latin_pct:.0f}% DOG-LATIN — predominantly addresses "
            "corporate fiction / dead entities."
        )
    if dog_latin_count > 0 and english_count > 0:
        warnings.append(
            "Mixed jurisdictional addressing: some tokens address living beings (English), "
            "some address corporate fictions (DOG-LATIN). Document is internally contradictory."
        )

    # Assessment
    if dog_latin_count == 0 and counts["PARSE_SYNTAX"] > 0:
        assessment = "CORRECT — Parse-syntax valid document, living jurisdiction"
    elif dog_latin_count == 0 and english_count > 0:
        assessment = "VALID — English common law text, no DOG-LATIN detected"
    elif dog_latin_pct > 75:
        assessment = "FRAUDULENT — Overwhelmingly DOG-LATIN, addresses only corporate fictions"
    elif dog_latin_pct > 25:
        assessment = "SUSPECT — Significant DOG-LATIN content, jurisdictional fraud likely"
    elif dog_latin_count > 0:
        assessment = "WARNING — DOG-LATIN present, verify jurisdictional integrity"
    else:
        assessment = "INDETERMINATE — Insufficient content for assessment"

    return {
        "total_tokens": total,
        "dog_latin_count": dog_latin_count,
        "dog_latin_pct": round(dog_latin_pct, 1),
        "correct_sign_count": counts["CORRECT_SIGN"],
        "parse_syntax_count": counts["PARSE_SYNTAX"],
        "english_count": english_count,
        "diminished_count": counts["DIMINISHED"],
        "jurisdiction_mixing": jurisdiction_mixing,
        "jurisdictions_found": sorted(jurisdictions_found),
        "tokens": tokens,
        "warnings": warnings,
        "assessment": assessment,
    }


# ---------------------------------------------------------------------------
# Highlighting
# ---------------------------------------------------------------------------

FORM_COLORS = {
    "DOG_LATIN": RED,
    "CORRECT_SIGN": GREEN,
    "PARSE_SYNTAX": GOLD,
    "ENGLISH": "",         # default (no color)
    "ENGLISH_HYPHENATED": GREEN,
    "DIMINISHED": DIM,
    "STOP": "",
    "NUMERIC": DIM,
    "PUNCT": DIM,
    "UNKNOWN": DIM,
}


def highlight_dog_latin(text: str) -> str:
    """Return text with ANSI highlighting by jurisdictional classification.

    Red = DOG-LATIN / GLOSSA (fraudulent)
    Gold/bright yellow = parse-syntax correct
    Green = correct sign language / hyphenated English
    White (no color) = English common law
    Dim = diminished / no standing
    """
    result_parts = []
    last_end = 0

    for match in re.finditer(r'\S+', text):
        token = match.group()
        start = match.start()
        end = match.end()

        # Add whitespace gap
        if start > last_end:
            result_parts.append(text[last_end:start])

        classification = classify_token(token)
        ft = classification["form_type"]
        color = FORM_COLORS.get(ft, "")

        if ft == "DOG_LATIN":
            result_parts.append(f"{RED}{BOLD}{token}{RESET}")
        elif ft == "PARSE_SYNTAX":
            result_parts.append(f"{GOLD}{BOLD}{token}{RESET}")
        elif ft == "CORRECT_SIGN":
            result_parts.append(f"{GREEN}{BOLD}{token}{RESET}")
        elif ft == "DIMINISHED":
            result_parts.append(f"{DIM}{token}{RESET}")
        elif color:
            result_parts.append(f"{color}{token}{RESET}")
        else:
            result_parts.append(token)

        last_end = end

    # Trailing text
    if last_end < len(text):
        result_parts.append(text[last_end:])

    return "".join(result_parts)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_scan(scan_result: dict, text: str = "") -> str:
    """Format a document scan as colored terminal output."""
    lines = []
    lines.append("")
    lines.append(f"{BOLD}{CYAN}{'=' * 70}{RESET}")
    lines.append(f"{BOLD}  DOG-LATIN / GLOSSA DETECTOR{RESET}")
    lines.append(f"{CYAN}{'=' * 70}{RESET}")
    lines.append("")

    if text:
        highlighted = highlight_dog_latin(text)
        lines.append(f"  {DIM}Input:{RESET}")
        # Wrap long text
        for line in text.split("\n"):
            lines.append(f"    {highlight_dog_latin(line)}")
        lines.append("")

    # Statistics
    lines.append(f"  {DIM}--- Token Classification ---{RESET}")
    lines.append(f"    Total tokens:            {scan_result['total_tokens']}")

    dl = scan_result['dog_latin_count']
    dl_color = RED if dl > 0 else DIM
    lines.append(f"    DOG-LATIN (fraudulent):  {dl_color}{dl}{RESET}  ({scan_result['dog_latin_pct']}%)")

    cs = scan_result['correct_sign_count']
    cs_color = GREEN if cs > 0 else DIM
    lines.append(f"    Correct Sign Language:   {cs_color}{cs}{RESET}")

    ps = scan_result['parse_syntax_count']
    ps_color = GOLD if ps > 0 else DIM
    lines.append(f"    Parse-Syntax Correct:    {ps_color}{ps}{RESET}")

    en = scan_result['english_count']
    lines.append(f"    English (common law):    {en}")

    dm = scan_result['diminished_count']
    dm_color = YELLOW if dm > 0 else DIM
    lines.append(f"    Diminished (no standing):{dm_color} {dm}{RESET}")
    lines.append("")

    # Jurisdictions
    lines.append(f"  {DIM}--- Jurisdictions Found ---{RESET}")
    for j in scan_result["jurisdictions_found"]:
        if "Maritime" in j or "Dead" in j:
            lines.append(f"    {RED}{BOLD}{j}{RESET}")
        elif "Quantum" in j or "Living" in j:
            lines.append(f"    {GOLD}{j}{RESET}")
        elif "Common Law" in j:
            lines.append(f"    {GREEN}{j}{RESET}")
        else:
            lines.append(f"    {YELLOW}{j}{RESET}")

    if scan_result["jurisdiction_mixing"]:
        lines.append("")
        lines.append(f"    {RED}{BOLD}** JURISDICTION MIXING DETECTED **{RESET}")
        lines.append(f"    {RED}Per Chicago Manual of Styles Art. 11:147:{RESET}")
        lines.append(f"    {RED}A foreign language text has NO JURISDICTION{RESET}")
        lines.append(f"    {RED}with another language on the same page.{RESET}")

    # Warnings
    if scan_result["warnings"]:
        lines.append("")
        lines.append(f"  {RED}{BOLD}Warnings:{RESET}")
        for w in scan_result["warnings"]:
            lines.append(f"    {RED}* {w}{RESET}")

    # Assessment
    lines.append("")
    assessment = scan_result["assessment"]
    if "CORRECT" in assessment:
        a_color = GOLD
    elif "VALID" in assessment:
        a_color = GREEN
    elif "FRAUDULENT" in assessment:
        a_color = RED
    elif "SUSPECT" in assessment:
        a_color = RED
    else:
        a_color = YELLOW
    lines.append(f"  {BOLD}Assessment:{RESET} {a_color}{BOLD}{assessment}{RESET}")

    lines.append("")
    lines.append(f"{CYAN}{'=' * 70}{RESET}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="DOG-LATIN / GLOSSA Detector — Identify jurisdictional fraud in text"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to scan for DOG-LATIN"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to file to scan"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode — enter text line by line"
    )

    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"{RED}Error: File not found: {args.file}{RESET}")
            sys.exit(1)
        text = path.read_text()
        result = scan_document(text)
        print(format_scan(result, text))
    elif args.interactive:
        print(f"\n{BOLD}{CYAN}DOG-LATIN DETECTOR — Interactive Mode{RESET}")
        print(f"{DIM}Enter text to scan. Type 'quit' or 'exit' to stop.{RESET}\n")
        while True:
            try:
                text = input(f"{CYAN}> {RESET}")
            except (EOFError, KeyboardInterrupt):
                print(f"\n{DIM}Exiting.{RESET}")
                break
            if text.strip().lower() in ("quit", "exit", "q"):
                break
            if text.strip():
                result = scan_document(text)
                print(format_scan(result, text))
    elif args.text:
        result = scan_document(args.text)
        print(format_scan(result, args.text))
    else:
        # Show built-in examples
        examples = [
            ("Birth certificate (DOG-LATIN)", "CERTIFICATE OF LIVE BIRTH  JOHN JAMES PUBLIC"),
            ("Court case (DOG-LATIN + jurisdiction mixing)",
             "THE STATE OF TEXAS VS. JOHN DOE"),
            ("Correct parse-syntax", ":John-James: :Public:"),
            ("Correct Latin Sign Language", "JOHN-JAMES-PUBLIC"),
            ("English common law", "John James Public"),
            ("Diminished form", "john james public"),
            ("Mixed document",
             "CERTIFICATE OF LIVE BIRTH\nName: JOHN JAMES PUBLIC\nMother: Jane Public\nDate: :January-First:"),
        ]
        print(f"\n{BOLD}{CYAN}DOG-LATIN / GLOSSA DETECTOR — Built-in Examples{RESET}\n")
        for label, text in examples:
            print(f"\n{BOLD}{BLUE}  [{label}]{RESET}")
            result = scan_document(text)
            print(format_scan(result, text))


if __name__ == "__main__":
    main()
