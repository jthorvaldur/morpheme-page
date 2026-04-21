"""
word_parser.py — Quantum Grammar Word Parser

Full word analysis: VCC negation check, morpheme decomposition,
jurisdiction classification, and now-time validity.

Uses the morpheme_negation module for core decomposition.

Usage:
    python src/word_parser.py "insurance" "assume" "corporation"
    python src/word_parser.py          # interactive mode
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Allow running from project root: python src/word_parser.py
_src_dir = str(Path(__file__).resolve().parent)
_project_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from morpheme_negation import (
    decompose,
    is_vcc_negated,
    detect_negation_prefix,
    VCC_NEGATION_PREFIXES,
    KNOWN_DECOMPOSITIONS,
)

# ---------------------------------------------------------------------------
# ANSI color codes
# ---------------------------------------------------------------------------

class Color:
    """ANSI escape codes for terminal output."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDERLINE = "\033[4m"

    # Standard colors
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # Bright colors
    BRED    = "\033[91m"
    BGREEN  = "\033[92m"
    BYELLOW = "\033[93m"
    BBLUE   = "\033[94m"
    BMAGENTA= "\033[95m"
    BCYAN   = "\033[96m"

    # Jurisdiction colors (matching the viz design language)
    LAND    = "\033[32m"   # green — land/soil
    SEA     = "\033[34m"   # blue — sea/water/maritime
    AIR     = "\033[33m"   # amber — air/ether
    FRAUD   = "\033[91m"   # red — fraud/DOG-LATIN/fiction
    CORRECT = "\033[93m"   # gold — correct parse-syntax / living
    DEAD    = "\033[90m"   # gray — dead/past time


def _color(text: str, color: str) -> str:
    """Wrap text in an ANSI color code."""
    return f"{color}{text}{Color.RESET}"


# ---------------------------------------------------------------------------
# Jurisdiction classification
# ---------------------------------------------------------------------------

class Jurisdiction:
    LAND_SOIL   = "land/soil"
    SEA_WATER   = "sea/water (maritime)"
    AIR_ETHER   = "air/ether"
    UNKNOWN     = "unknown"


def classify_jurisdiction(word: str) -> dict:
    """
    Classify the jurisdiction of a word based on its textual form.

    Case and hyphen rules:
        ALL CAPS NO HYPHENS  -> DOG-LATIN / GLOSSA -> maritime/dead/corporate (FRAUD)
        ALL-CAPS-HYPHENATED  -> Correct Latin Sign Language -> valid
        :Colon-Form:         -> Parse-Syntax Correct -> quantum/now-time/living
        Title Case            -> English proper noun -> common law / living
        lower case            -> diminished -> no standing (warning)
    """
    original = word.strip()

    if not original:
        return {
            "form": "",
            "classification": "empty",
            "jurisdiction": Jurisdiction.UNKNOWN,
            "status": "VOID",
            "warning": "Empty input",
        }

    # :Colon-Form: — parse-syntax correct, living claim
    if original.startswith(":") and original.endswith(":"):
        inner = original[1:-1]
        if "-" in inner:
            return {
                "form": original,
                "classification": "parse-syntax correct (colon-hyphenated)",
                "jurisdiction": Jurisdiction.LAND_SOIL,
                "status": "CORRECT — living claim in now-time",
                "warning": None,
            }
        else:
            return {
                "form": original,
                "classification": "colon-wrapped (no hyphens)",
                "jurisdiction": Jurisdiction.LAND_SOIL,
                "status": "PARTIAL — colons present but hyphens missing",
                "warning": "Add hyphens between name parts for full quantum sign",
            }

    # ALL CAPS with hyphens — correct Latin sign language
    stripped = original.replace("-", "").replace(" ", "")
    if stripped.isupper() and "-" in original and len(stripped) > 1:
        return {
            "form": original,
            "classification": "correct Latin sign language (hyphenated caps)",
            "jurisdiction": Jurisdiction.LAND_SOIL,
            "status": "VALID — connected quantum signs",
            "warning": None,
        }

    # ALL CAPS without hyphens — DOG-LATIN / GLOSSA
    no_spaces = original.replace(" ", "")
    if no_spaces.isupper() and "-" not in original and len(no_spaces) > 1:
        return {
            "form": original,
            "classification": "DOG-LATIN / GLOSSA",
            "jurisdiction": Jurisdiction.SEA_WATER,
            "status": "FRAUDULENT — unhyphenated all-caps is dead language",
            "warning": (
                "DOG-LATIN: each word is a separate unconnected symbol. "
                "This form addresses a corporate fiction, not a living being. "
                "Per Black's Law 4th Ed: 'the language of the illiterate.'"
            ),
        }

    # Title Case — English proper noun
    words_in = original.split()
    if len(words_in) >= 1 and all(w[0].isupper() for w in words_in if w):
        # Check if it's truly title case (not all caps)
        if not no_spaces.isupper():
            return {
                "form": original,
                "classification": "English proper noun (title case)",
                "jurisdiction": Jurisdiction.LAND_SOIL,
                "status": "VALID — common law / living form",
                "warning": None,
            }

    # all lowercase
    if original.islower():
        return {
            "form": original,
            "classification": "diminished (all lowercase)",
            "jurisdiction": Jurisdiction.UNKNOWN,
            "status": "WARNING — no standing / diminished form",
            "warning": "All-lowercase form has no standing. Consider proper case.",
        }

    # Mixed / other
    return {
        "form": original,
        "classification": "mixed form",
        "jurisdiction": Jurisdiction.UNKNOWN,
        "status": "INDETERMINATE — mixed case form",
        "warning": None,
    }


# ---------------------------------------------------------------------------
# Now-time validity
# ---------------------------------------------------------------------------

def check_now_time(word: str) -> dict:
    """
    Check if a word is in now-time (present/living) or dead-time (past/future).

    Now-time: -ing gerund form = living, present, factual
    Dead-time: -ed past form = dead, completed, fiction
    Future-time: shall/will/would/could = fiction, hasn't happened
    """
    w = word.lower().strip()

    # Gerund / present participle — NOW-TIME (living)
    if w.endswith("ing"):
        return {
            "word": w,
            "tense": "now-time (gerund / present participle)",
            "is_now_time": True,
            "status": "LIVING — present action in now-time",
        }

    # Past tense — DEAD TIME
    if w.endswith("ed"):
        return {
            "word": w,
            "tense": "past (dead time)",
            "is_now_time": False,
            "status": "DEAD — past tense, completed, no longer factual",
        }

    # Future / modal verbs — FICTION
    future_words = {"shall", "will", "would", "could", "should", "might", "may"}
    if w in future_words:
        return {
            "word": w,
            "tense": "future/modal (fiction)",
            "is_now_time": False,
            "status": "FICTION — future tense, has not happened, cannot contract",
        }

    # Base form — indeterminate but potentially now-time
    return {
        "word": w,
        "tense": "base form (atemporal)",
        "is_now_time": True,  # base nouns are now-time by default
        "status": "NEUTRAL — base form, evaluate in sentence context",
    }


# ---------------------------------------------------------------------------
# Full parse
# ---------------------------------------------------------------------------

def parse_word(word: str) -> dict:
    """
    Full quantum grammar analysis of a single word.

    Returns a dict with:
        - decomposition: morpheme breakdown (prefix/root/suffix)
        - jurisdiction: case/hyphen jurisdiction classification
        - now_time: tense/time analysis
        - vcc_negated: whether the VCC negation operator is active
        - negation_prefix: the negation prefix and remainder, if any
        - summary: one-line summary
    """
    clean = word.strip()
    lower = clean.lower()

    # Core decomposition
    decomp = decompose(lower)

    # Jurisdiction classification (preserves original case)
    juris = classify_jurisdiction(clean)

    # Now-time check
    now_time = check_now_time(lower)

    # VCC negation
    negated = is_vcc_negated(lower)
    neg_prefix = detect_negation_prefix(lower)

    # Build summary
    parts = []
    if negated:
        parts.append("VCC-NEGATED")
    if juris["jurisdiction"] == Jurisdiction.SEA_WATER:
        parts.append("DOG-LATIN/MARITIME")
    elif juris["jurisdiction"] == Jurisdiction.LAND_SOIL:
        parts.append("LAND/SOIL")
    if not now_time["is_now_time"]:
        parts.append("DEAD-TIME")
    else:
        parts.append("NOW-TIME")

    summary = f"{clean}: {' | '.join(parts)}"

    return {
        "word": clean,
        "word_lower": lower,
        "decomposition": decomp,
        "jurisdiction": juris,
        "now_time": now_time,
        "vcc_negated": negated,
        "negation_prefix": {
            "prefix": neg_prefix[0] if neg_prefix else None,
            "remainder": neg_prefix[1] if neg_prefix else None,
        },
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Pretty-print formatting
# ---------------------------------------------------------------------------

def format_parse(result: dict) -> str:
    """
    Format a parse result as a colorized, human-readable string
    for terminal output.
    """
    lines = []
    decomp = result["decomposition"]
    juris = result["jurisdiction"]
    now = result["now_time"]

    # Header
    word_display = result["word"].upper()
    neg_tag = ""
    if result["vcc_negated"]:
        neg_tag = _color(" [VCC NEGATED]", Color.FRAUD)

    header = f"{_color(word_display, Color.BOLD + Color.BCYAN)}{neg_tag}"
    border = _color("=" * 64, Color.DIM)
    lines.append(border)
    lines.append(f"  {header}")
    lines.append(border)

    # Morpheme breakdown
    lines.append(f"  {_color('MORPHEME DECOMPOSITION', Color.BOLD + Color.WHITE)}")
    if decomp["prefix"]:
        pfx_color = Color.FRAUD if result["vcc_negated"] else Color.YELLOW
        lines.append(
            f"    prefix : {_color(decomp['prefix'] + '-', pfx_color)}"
            f"  ({decomp['prefix_meaning']})"
        )
    root_display = decomp["root"] if decomp["root"] else "?"
    lines.append(
        f"    root   : {_color(root_display, Color.BGREEN)}"
        f"  ({decomp['root_meaning'] or 'unknown'})"
    )
    if decomp["suffix"]:
        lines.append(
            f"    suffix : {_color('-' + decomp['suffix'], Color.BLUE)}"
            f"  ({decomp['suffix_meaning']})"
        )

    # True vs apparent meaning
    lines.append("")
    lines.append(f"  {_color('MEANING', Color.BOLD + Color.WHITE)}")
    lines.append(
        f"    TRUE meaning     : {_color(decomp['true_meaning'], Color.CORRECT)}"
    )
    lines.append(
        f"    APPARENT meaning : {_color(decomp['apparent_meaning'], Color.DIM)}"
    )

    # Jurisdiction
    lines.append("")
    lines.append(f"  {_color('JURISDICTION', Color.BOLD + Color.WHITE)}")
    jur = juris["jurisdiction"]
    if jur == Jurisdiction.SEA_WATER:
        jur_color = Color.FRAUD
    elif jur == Jurisdiction.LAND_SOIL:
        jur_color = Color.LAND
    else:
        jur_color = Color.DIM

    lines.append(
        f"    form           : {juris['form']}"
    )
    lines.append(
        f"    classification : {_color(juris['classification'], jur_color)}"
    )
    lines.append(
        f"    jurisdiction   : {_color(juris['jurisdiction'], jur_color)}"
    )
    lines.append(
        f"    status         : {_color(juris['status'], jur_color)}"
    )
    if juris.get("warning"):
        lines.append(
            f"    {_color('WARNING', Color.BRED)}: {_color(juris['warning'], Color.RED)}"
        )

    # Now-time
    lines.append("")
    lines.append(f"  {_color('TEMPORAL', Color.BOLD + Color.WHITE)}")
    time_color = Color.BGREEN if now["is_now_time"] else Color.DEAD
    lines.append(
        f"    tense  : {_color(now['tense'], time_color)}"
    )
    lines.append(
        f"    status : {_color(now['status'], time_color)}"
    )

    lines.append(border)
    return "\n".join(lines)


def format_parse_plain(result: dict) -> str:
    """Format a parse result as plain text (no ANSI codes)."""
    lines = []
    decomp = result["decomposition"]
    juris = result["jurisdiction"]
    now = result["now_time"]

    word_display = result["word"].upper()
    neg_tag = " [VCC NEGATED]" if result["vcc_negated"] else ""

    lines.append("=" * 60)
    lines.append(f"  {word_display}{neg_tag}")
    lines.append("=" * 60)

    lines.append("  MORPHEME DECOMPOSITION")
    if decomp["prefix"]:
        lines.append(f"    prefix : {decomp['prefix']}- ({decomp['prefix_meaning']})")
    lines.append(f"    root   : {decomp['root']} ({decomp['root_meaning'] or 'unknown'})")
    if decomp["suffix"]:
        lines.append(f"    suffix : -{decomp['suffix']} ({decomp['suffix_meaning']})")

    lines.append("")
    lines.append("  MEANING")
    lines.append(f"    TRUE meaning     : {decomp['true_meaning']}")
    lines.append(f"    APPARENT meaning : {decomp['apparent_meaning']}")

    lines.append("")
    lines.append("  JURISDICTION")
    lines.append(f"    form           : {juris['form']}")
    lines.append(f"    classification : {juris['classification']}")
    lines.append(f"    jurisdiction   : {juris['jurisdiction']}")
    lines.append(f"    status         : {juris['status']}")
    if juris.get("warning"):
        lines.append(f"    WARNING: {juris['warning']}")

    lines.append("")
    lines.append("  TEMPORAL")
    lines.append(f"    tense  : {now['tense']}")
    lines.append(f"    status : {now['status']}")

    lines.append("=" * 60)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Comparison display — show multiple forms of the same name
# ---------------------------------------------------------------------------

def compare_forms(name: str) -> str:
    """
    Show how different case/hyphen forms of a name change its jurisdiction.
    E.g., compare_forms("John Doe") shows: John Doe, JOHN DOE,
    JOHN-DOE, :John-Doe:, john doe
    """
    parts = name.split()
    if len(parts) < 2:
        parts = [name]

    forms = [
        " ".join(parts),                                # Title Case
        " ".join(p.upper() for p in parts),             # ALL CAPS
        "-".join(p.upper() for p in parts),             # HYPHENATED CAPS
        ":" + "-".join(p.capitalize() for p in parts) + ":",  # :Colon-Form:
        " ".join(p.lower() for p in parts),             # all lower
    ]

    lines = [
        "",
        _color("JURISDICTION COMPARISON", Color.BOLD + Color.BCYAN),
        _color(f"  Name basis: {name}", Color.DIM),
        "",
    ]

    for form in forms:
        juris = classify_jurisdiction(form)
        if juris["jurisdiction"] == Jurisdiction.SEA_WATER:
            jc = Color.FRAUD
        elif juris["jurisdiction"] == Jurisdiction.LAND_SOIL:
            jc = Color.LAND
        else:
            jc = Color.DIM

        lines.append(f"  {_color(form, jc):40s} -> {_color(juris['status'], jc)}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _interactive_mode() -> None:
    """Run the parser in interactive REPL mode."""
    print(_color("\n  QUANTUM GRAMMAR WORD PARSER", Color.BOLD + Color.BCYAN))
    print(_color("  ─" * 30, Color.DIM))
    print(f"  Type a word to parse it. Commands:")
    print(f"    {_color('/compare', Color.YELLOW)} <name>  — compare jurisdiction forms")
    print(f"    {_color('/batch', Color.YELLOW)} w1 w2 ... — parse multiple words")
    print(f"    {_color('/negated', Color.YELLOW)}         — list all known VCC-negated words")
    print(f"    {_color('/list', Color.YELLOW)}            — list all known words")
    print(f"    {_color('/quit', Color.YELLOW)}            — exit")
    print()

    while True:
        try:
            raw = input(_color("  parse> ", Color.BCYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if not raw:
            continue

        if raw.lower() in ("/quit", "/exit", "/q", "quit", "exit"):
            break

        if raw.lower().startswith("/compare"):
            name = raw[len("/compare"):].strip() or "John Doe"
            print(compare_forms(name))
            continue

        if raw.lower().startswith("/batch"):
            words = raw[len("/batch"):].strip().split()
            for w in words:
                result = parse_word(w)
                print(format_parse(result))
            continue

        if raw.lower() in ("/negated",):
            from morpheme_negation import list_negated_words
            negated = list_negated_words()
            print(f"\n  {_color('VCC-NEGATED WORDS', Color.BOLD + Color.FRAUD)} ({len(negated)}):\n")
            for w in sorted(negated):
                print(f"    {_color(w, Color.FRAUD)}")
            print()
            continue

        if raw.lower() in ("/list",):
            from morpheme_negation import list_known_words
            known = list_known_words()
            print(f"\n  {_color('KNOWN WORDS', Color.BOLD + Color.BCYAN)} ({len(known)}):\n")
            for w in known:
                print(f"    {w}")
            print()
            continue

        # Parse the word(s)
        words = raw.split()
        for w in words:
            result = parse_word(w)
            print(format_parse(result))


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) > 1:
        # Command-line arguments mode
        words = sys.argv[1:]
        for word in words:
            result = parse_word(word)
            print(format_parse(result))
    else:
        # Interactive mode
        _interactive_mode()


if __name__ == "__main__":
    main()
