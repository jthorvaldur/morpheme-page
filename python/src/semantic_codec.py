"""
semantic_codec.py — Bidirectional Semantic Compression

Encode English text into semantic glyphs (2-3 char codes).
Decode glyphs back to English.

Each glyph represents one root concept from the 720-word
quantum grammar basis set. Grammar is implicit, redundancy
is eliminated.

Usage:
    python src/semantic_codec.py encode "your text here"
    python src/semantic_codec.py decode "CLA LAN MAN LAW SOV"
    python src/semantic_codec.py analyze "your text here"
    python src/semantic_codec.py        # interactive mode
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_src = Path(__file__).resolve().parent
_root = _src.parent.parent
_basis_path = _root / "data" / "basis_720.json"

# ---------------------------------------------------------------------------
# Stop words — zero-information tokens
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset(
    "the a an is are was were be been being am have has had do does did "
    "will would could should shall may might can cannot to of in for on "
    "at by with from as into through during before after above below "
    "between and but or nor so yet not no it its this that these those "
    "i me my you your he him his she her we us our they them their than "
    "very just also too then now here there when where how what which who "
    "if because although while since until unless however therefore really "
    "basically literally actually like oh ok okay omg um uh been some any".split()
)

# ---------------------------------------------------------------------------
# Synonym map — common English → basis root
# ---------------------------------------------------------------------------

SYNONYMS: dict[str, str] = {
    "want": "claim", "need": "requir", "make": "grant", "create": "grant",
    "build": "construct", "do": "execut", "use": "employ", "say": "declar",
    "tell": "inform", "talk": "communicat", "think": "consider", "know": "cogn",
    "see": "witness", "look": "inspect", "find": "discover", "go": "proceed",
    "come": "appear", "take": "seiz", "give": "grant", "get": "acquir",
    "buy": "purchas", "sell": "trad", "pay": "pay", "work": "labor",
    "help": "aid", "try": "attempt", "ask": "petition", "call": "summon",
    "run": "execut", "keep": "retain", "let": "permit", "put": "place",
    "show": "demonstrat", "turn": "convert", "move": "transfer",
    "live": "inhabit", "die": "mort", "lose": "forfeit", "win": "prevail",
    "begin": "commenc", "start": "commenc", "end": "terminat", "stop": "ceas",
    "hold": "retain", "house": "estat", "home": "estat", "money": "currenc",
    "cash": "currenc", "dollar": "currenc", "job": "labor", "car": "vessel",
    "person": "person", "people": "person", "man": "man", "woman": "woman",
    "child": "minor", "thing": "property", "stuff": "property",
    "place": "venue", "world": "dominion", "country": "nation",
    "city": "municipal", "town": "municipal", "law": "law", "right": "right",
    "power": "authority", "rule": "statute", "good": "lawful",
    "bad": "fraudulent", "big": "substantial", "small": "minor",
    "old": "prior", "new": "novel", "true": "valid", "false": "invalid",
    "important": "material", "free": "sovereign", "dead": "mort",
    "name": "identity", "word": "morpheme", "language": "grammar",
    "meaning": "sense", "idea": "concept", "government": "authority",
    "court": "tribunal", "judge": "magistrat", "bank": "treasury",
    "tax": "levy", "debt": "obligation", "loan": "mortgage",
    "contract": "contract", "agreement": "agreement",
    "document": "instrument", "land": "land", "water": "water",
    "sea": "sea", "earth": "soil", "body": "corpus", "blood": "blood",
    "heart": "heart", "mind": "mind", "fire": "fire", "spirit": "spirit",
    "soul": "soul", "death": "mort", "king": "sovereign", "ship": "vessel",
    "trade": "commerce", "market": "commerce", "hard": "binding",
    "much": "substantial", "many": "several", "every": "each",
    "own": "proprietary", "real": "actual", "sure": "certain",
    "must": "mandat", "always": "perpetual", "never": "null",
    "here": "present", "now": "current", "best": "optimal",
    "only": "sole", "more": "additional", "most": "primary",
    "analysis": "assessment", "constraint": "restriction",
    "example": "precedent", "test": "proof", "page": "document",
    "evaluate": "assess", "level": "degree", "optimal": "maximal",
    "compression": "reduction",
}

# ---------------------------------------------------------------------------
# Codec state
# ---------------------------------------------------------------------------

class SemanticCodec:
    """Bidirectional English ↔ Glyph codec built from basis_720."""

    def __init__(self, basis_path: Path = _basis_path):
        self.glyph_to_words: dict[str, dict] = {}
        self.word_to_glyph: dict[str, str] = {}
        self._load(basis_path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            print(f"Warning: {path} not found. Codec will work with synonyms only.", file=sys.stderr)
            return

        with open(path) as f:
            data = json.load(f)

        # Group by root
        roots: dict[str, dict] = {}
        for entry in data:
            r = entry["root"].lower()
            if r not in roots:
                roots[r] = {"words": [], "roles": set(), "jurisdiction": entry["jurisdiction"]}
            roots[r]["words"].append(entry["word"].lower())
            roots[r]["roles"].add(entry["role"])

        # Build glyph dictionaries
        for root, info in roots.items():
            glyph = root[:4].upper()
            if glyph not in self.glyph_to_words:
                self.glyph_to_words[glyph] = {
                    "words": info["words"],
                    "roles": list(info["roles"]),
                    "jurisdiction": info["jurisdiction"],
                    "root": root,
                }
                for w in info["words"]:
                    self.word_to_glyph[w] = glyph

        # Map synonyms
        for word, root in SYNONYMS.items():
            glyph = root[:4].upper()
            if word not in self.word_to_glyph:
                self.word_to_glyph[word] = glyph

        # Build compact 2-char codes for maximum density
        self.compact: dict[str, str] = {}  # 4-char -> 2-char
        self.decompact: dict[str, str] = {}  # 2-char -> 4-char
        glyphs_sorted = sorted(self.glyph_to_words.keys())
        idx = 0
        for g in glyphs_sorted:
            c1 = chr(65 + idx // 26)  # A-Z
            c2 = chr(65 + idx % 26)   # A-Z
            code2 = c1 + c2
            self.compact[g] = code2
            self.decompact[code2] = g
            idx += 1

    # -------------------------------------------------------------------
    # ENCODE: English → Glyphs
    # -------------------------------------------------------------------

    def encode(self, text: str, mode: str = "standard") -> dict:
        """
        Encode English text into semantic glyphs.

        mode:
            "standard" — 3-4 char mnemonic glyphs (CLA, LAN, MAN)
            "compact"  — 2 char codes (AA, AB, AC) — maximum density
        """
        import re
        words = re.findall(r"[a-z']+", text.lower())
        glyphs = []
        changes = []
        seen: set[str] = set()

        for w in words:
            clean = w.replace("'", "")
            if not clean:
                continue

            # Skip stop words
            if clean in STOP_WORDS:
                changes.append({"word": clean, "action": "dropped"})
                continue

            # Direct match
            if clean in self.word_to_glyph:
                g = self.word_to_glyph[clean]
                if g not in seen:
                    glyphs.append(g)
                    seen.add(g)
                    changes.append({"word": clean, "action": "encoded", "glyph": g})
                else:
                    changes.append({"word": clean, "action": "deduped", "glyph": g})
                continue

            # Synonym
            if clean in SYNONYMS:
                g = SYNONYMS[clean][:4].upper()
                if g not in seen:
                    glyphs.append(g)
                    seen.add(g)
                    changes.append({"word": clean, "action": "synonym", "glyph": g})
                else:
                    changes.append({"word": clean, "action": "deduped", "glyph": g})
                continue

            # Unknown — create ad-hoc glyph
            g = clean[:4].upper()
            if g not in seen:
                glyphs.append(g)
                seen.add(g)
                if g not in self.glyph_to_words:
                    self.glyph_to_words[g] = {"words": [clean], "roles": ["unknown"], "root": clean}
                changes.append({"word": clean, "action": "new-glyph", "glyph": g})
            else:
                changes.append({"word": clean, "action": "deduped", "glyph": g})

        # Apply compact mode if requested
        if mode == "compact":
            glyphs = [self.compact.get(g, g) for g in glyphs]

        return {
            "glyphs": glyphs,
            "changes": changes,
            "original_words": len(words),
            "glyph_count": len(glyphs),
            "mode": mode,
        }

    # -------------------------------------------------------------------
    # DECODE: Glyphs → English
    # -------------------------------------------------------------------

    def decode(self, glyph_text: str) -> dict:
        """Decode glyphs back to English words."""
        tokens = glyph_text.strip().split()
        words = []

        for g in tokens:
            gu = g.upper()
            # Try direct lookup
            if gu in self.glyph_to_words:
                words.append(self.glyph_to_words[gu]["words"][0])
            # Try decompact (2-char → 4-char → word)
            elif gu in self.decompact:
                full = self.decompact[gu]
                if full in self.glyph_to_words:
                    words.append(self.glyph_to_words[full]["words"][0])
                else:
                    words.append(g.lower())
            else:
                words.append(g.lower())

        return {"words": words, "glyphs": tokens}

    # -------------------------------------------------------------------
    # ANALYZE: Show compression metrics
    # -------------------------------------------------------------------

    def analyze(self, text: str) -> dict:
        """Full analysis: encode + metrics."""
        result = self.encode(text)
        compact_result = self.encode(text, mode="compact")

        original_chars = len(text)
        standard_text = " ".join(result["glyphs"])
        compact_text = " ".join(compact_result["glyphs"])

        return {
            **result,
            "standard_text": standard_text,
            "compact_text": compact_text,
            "original_chars": original_chars,
            "standard_chars": len(standard_text),
            "compact_chars": len(compact_text),
            "char_savings_standard": round((1 - len(standard_text) / max(original_chars, 1)) * 100, 1),
            "char_savings_compact": round((1 - len(compact_text) / max(original_chars, 1)) * 100, 1),
            "token_ratio": round(result["original_words"] / max(result["glyph_count"], 1), 1),
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

ANSI_PURPLE = "\033[35m"
ANSI_GREEN = "\033[32m"
ANSI_GOLD = "\033[33m"
ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


def _print_encode(codec: SemanticCodec, text: str) -> None:
    result = codec.analyze(text)

    print(f"\n{ANSI_BOLD}{'='*60}{ANSI_RESET}")
    print(f"  {ANSI_PURPLE}SEMANTIC CODEC — ENCODE{ANSI_RESET}")
    print(f"{'='*60}")

    print(f"\n{ANSI_DIM}ORIGINAL:{ANSI_RESET}")
    print(f"  {text}")

    print(f"\n{ANSI_PURPLE}STANDARD GLYPHS:{ANSI_RESET}")
    print(f"  {result['standard_text']}")

    print(f"\n{ANSI_GREEN}COMPACT (2-char):{ANSI_RESET}")
    print(f"  {result['compact_text']}")

    print(f"\n{ANSI_GOLD}METRICS:{ANSI_RESET}")
    print(f"  Words: {result['original_words']} → {result['glyph_count']} glyphs ({result['token_ratio']}x compression)")
    print(f"  Chars: {result['original_chars']} → {result['standard_chars']} standard ({result['char_savings_standard']}% saved)")
    print(f"  Chars: {result['original_chars']} → {result['compact_chars']} compact ({result['char_savings_compact']}% saved)")

    # Changelog
    actions = {}
    for c in result["changes"]:
        a = c["action"]
        actions.setdefault(a, []).append(c)

    print(f"\n{ANSI_DIM}CHANGELOG:{ANSI_RESET}")
    for action in ["encoded", "synonym", "new-glyph", "dropped", "deduped"]:
        items = actions.get(action, [])
        if not items:
            continue
        if action == "dropped":
            print(f"  {ANSI_DIM}Dropped ({len(items)}): {', '.join(c['word'] for c in items)}{ANSI_RESET}")
        elif action == "deduped":
            print(f"  {ANSI_DIM}Deduped ({len(items)}): {', '.join(c['word'] for c in items)}{ANSI_RESET}")
        else:
            for c in items:
                label = "→" if action == "encoded" else "≈" if action == "synonym" else "+"
                print(f"  {c['word']} {label} {ANSI_PURPLE}{c['glyph']}{ANSI_RESET}")

    print(f"{'='*60}\n")


def _print_decode(codec: SemanticCodec, glyph_text: str) -> None:
    result = codec.decode(glyph_text)

    print(f"\n{ANSI_BOLD}{'='*60}{ANSI_RESET}")
    print(f"  {ANSI_GREEN}SEMANTIC CODEC — DECODE{ANSI_RESET}")
    print(f"{'='*60}")
    print(f"\n{ANSI_PURPLE}GLYPHS:{ANSI_RESET}")
    print(f"  {glyph_text}")
    print(f"\n{ANSI_GREEN}ENGLISH:{ANSI_RESET}")
    print(f"  {' '.join(result['words'])}")
    print(f"{'='*60}\n")


def _interactive(codec: SemanticCodec) -> None:
    print(f"\n  {ANSI_PURPLE}SEMANTIC CODEC{ANSI_RESET} — interactive mode")
    print(f"  {ANSI_DIM}Commands: encode <text>, decode <glyphs>, analyze <text>, quit{ANSI_RESET}")
    print(f"  {ANSI_DIM}Dictionary: {len(codec.glyph_to_words)} glyphs from {len(codec.word_to_glyph)} words{ANSI_RESET}\n")

    while True:
        try:
            raw = input(f"  {ANSI_PURPLE}codec>{ANSI_RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue
        if raw.lower() in ("quit", "exit", "q"):
            break

        if raw.lower().startswith("encode "):
            _print_encode(codec, raw[7:])
        elif raw.lower().startswith("decode "):
            _print_decode(codec, raw[7:])
        elif raw.lower().startswith("analyze "):
            _print_encode(codec, raw[8:])
        else:
            # Default: encode
            _print_encode(codec, raw)


def main() -> None:
    codec = SemanticCodec()

    if len(sys.argv) < 2:
        _interactive(codec)
        return

    cmd = sys.argv[1].lower()
    text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if not text and cmd not in ("help",):
        # Treat entire argv as text to encode
        _print_encode(codec, " ".join(sys.argv[1:]))
        return

    if cmd == "encode":
        _print_encode(codec, text)
    elif cmd == "decode":
        _print_decode(codec, text)
    elif cmd == "analyze":
        _print_encode(codec, text)
    else:
        _print_encode(codec, " ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()
