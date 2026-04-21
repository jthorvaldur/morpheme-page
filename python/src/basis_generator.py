"""
basis_generator.py — Generate the 720-Word Basis Set

720 = 6! (six factorial). Six is the number of fundamental positions
in a correct sentence per C.S.S.C.P.S.G.P.:

    Position 1: PREPOSITION     (FOR, BY, OF, WITH, IN)
    Position 2: ARTICLE         (THE, A, AN)
    Position 3: ADJECTIVE       (descriptor)
    Position 4: NOUN            (fact-carrier)
    Position 5: VERB (gerund)   (action in now-time: -ING form)
    Position 6: ADVERB/MODIFIER (modifies the verb)

The 720-word basis set maps the foundational vocabulary. Each word is
decomposed into prefix/root/suffix, classified by parse-syntax role
and jurisdictional valence.

Usage:
    python src/basis_generator.py              # generate and save
    python src/basis_generator.py --stats      # print stats only
    python src/basis_generator.py --preview    # preview without saving
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from project root
_src_dir = str(Path(__file__).resolve().parent)
_project_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from morpheme_negation import decompose

# ---------------------------------------------------------------------------
# The six sentence positions
# ---------------------------------------------------------------------------

POSITIONS = {
    "PREPOSITION": {
        "position": 1,
        "description": "Grounding word — establishes relationship in now-time",
        "function": "Anchors the sentence to a prepositional framework",
    },
    "ARTICLE": {
        "position": 2,
        "description": "Pointer/determiner — identifies which noun is referenced",
        "function": "Points to the specific fact-carrier",
    },
    "ADJECTIVE": {
        "position": 3,
        "description": "Descriptor — opinion or quality, not a fact itself",
        "function": "Modifies the noun (the fact-carrier)",
    },
    "NOUN": {
        "position": 4,
        "description": "Fact-carrier — the primary vessel of meaning",
        "function": "Carries the FACT. No nouns = no facts = void sentence",
    },
    "VERB_GERUND": {
        "position": 5,
        "description": "Action in now-time — must be in -ING gerund form",
        "function": "The doing. Only now-time (-ING) is living/factual",
    },
    "ADVERB": {
        "position": 6,
        "description": "Modifier of the verb — says nothing alone",
        "function": "Modifies the action. Warning: adverb chains = null construction",
    },
}

# ---------------------------------------------------------------------------
# Word lists for each position
# ---------------------------------------------------------------------------

PREPOSITIONS = [
    "for", "by", "of", "with", "in",
    "against", "from", "to", "through", "between",
    "among", "within", "without", "upon", "under",
    "over", "before", "after", "during", "about",
]

ARTICLES = [
    "the", "a", "an",
    "this", "that", "these", "those",
    "every", "each", "some", "no", "all", "any",
]

ADJECTIVES = [
    "living", "dead", "correct", "false", "true",
    "valid", "void", "lawful", "legal", "private",
    "public", "sovereign", "foreign", "domestic", "natural",
    "artificial", "original", "counterfeit", "genuine", "fraudulent",
    "free", "bound", "whole", "partial", "proper",
    "actual", "real", "fictional", "present", "absent",
    "direct", "indirect", "written", "oral", "material",
    "substantial", "just", "unjust", "certain", "uncertain",
]

NOUNS = [
    "man", "woman", "claim", "land", "soil",
    "vessel", "cargo", "contract", "fact", "law",
    "right", "duty", "trust", "estate", "title",
    "property", "bond", "security", "authority", "court",
    "bank", "person", "citizen", "state", "nation",
    "flag", "seal", "post", "office", "document",
    "certificate", "register", "account", "name", "sign",
    "mark", "stamp", "record", "deed", "warrant",
    "notice", "evidence", "witness", "oath", "jury",
    "judge", "magistrate", "sheriff", "marshal", "sovereign",
    "constitution", "statute", "jurisdiction", "mortgage", "currency",
    "capital", "interest", "credit", "debit", "sentence",
    "charge", "bar", "dock", "berth", "subject",
    "opinion", "agreement", "government", "license", "insurance",
    "commerce", "parliament", "attorney", "science", "body",
    "mind", "spirit", "birth", "death", "water",
    "current", "port", "harbor", "ship", "captain",
    "master", "slave", "freedom", "liberty", "justice",
    "truth", "fraud", "fiction", "reality", "substance",
    "form", "action", "cause", "effect", "origin",
    "source", "power", "force", "will", "consent",
]

VERBS_GERUND = [
    "claiming", "standing", "living", "writing", "speaking",
    "signing", "sealing", "delivering", "posting", "recording",
    "filing", "noticing", "witnessing", "bonding", "securing",
    "holding", "carrying", "moving", "creating", "destroying",
    "charging", "discharging", "appearing", "presenting", "representing",
    "contracting", "agreeing", "consenting", "objecting", "protesting",
    "establishing", "maintaining", "operating", "governing", "judging",
    "executing", "sentencing", "binding", "freeing", "releasing",
    "granting", "revoking", "amending", "ratifying", "affirming",
    "denying", "asserting", "declaring", "publishing", "certifying",
]

ADVERBS = [
    "now", "here", "thereby", "hereby", "wherein",
    "thereof", "forthwith", "henceforth", "lawfully", "legally",
    "correctly", "voluntarily", "knowingly", "willingly", "freely",
    "directly", "properly", "actually", "truly", "falsely",
    "publicly", "privately", "formally", "materially", "substantially",
]

# Map role names to their word lists
ROLE_WORDS: dict[str, list[str]] = {
    "PREPOSITION": PREPOSITIONS,
    "ARTICLE": ARTICLES,
    "ADJECTIVE": ADJECTIVES,
    "NOUN": NOUNS,
    "VERB_GERUND": VERBS_GERUND,
    "ADVERB": ADVERBS,
}

# ---------------------------------------------------------------------------
# Jurisdiction heuristics
# ---------------------------------------------------------------------------

# Words strongly associated with maritime/sea jurisdiction
SEA_WORDS = {
    "vessel", "cargo", "dock", "berth", "port", "harbor", "ship",
    "captain", "current", "currency", "bank", "bar", "charge",
    "suit", "sentence", "execute", "commerce", "citizen", "person",
    "statute", "mortgage", "insurance", "certificate", "license",
    "capital", "credit", "debit", "bond", "court", "deliver",
    "appearing", "representing", "charging", "discharging",
    "sentencing", "executing", "governing", "legally", "hereby",
    "forthwith", "thereof", "thereby", "legal", "artificial",
    "corporate", "fictional", "fraudulent", "counterfeit", "void",
    "dead", "absent", "indirect", "bound", "subject",
}

# Words strongly associated with land/soil jurisdiction
LAND_WORDS = {
    "man", "woman", "claim", "land", "soil", "right", "duty",
    "trust", "property", "title", "estate", "flag", "seal",
    "oath", "witness", "evidence", "deed", "warrant", "jury",
    "judge", "sheriff", "marshal", "sovereign", "constitution",
    "justice", "truth", "reality", "substance", "freedom", "liberty",
    "birth", "spirit", "mind", "origin", "source", "consent",
    "will", "power", "cause", "fact", "law", "name",
    "claiming", "standing", "living", "writing", "speaking",
    "signing", "sealing", "witnessing", "holding", "creating",
    "freeing", "releasing", "granting", "affirming", "declaring",
    "publishing", "certifying", "protesting", "objecting",
    "lawfully", "correctly", "voluntarily", "knowingly", "willingly",
    "freely", "directly", "properly", "actually", "truly",
    "lawful", "natural", "genuine", "original", "real",
    "living", "free", "whole", "proper", "actual",
    "present", "direct", "written", "just", "certain",
    "sovereign", "private", "true", "valid", "correct",
}

# Words associated with air/ether jurisdiction
AIR_WORDS = {
    "authority", "office", "post", "nation", "state",
    "government", "parliament", "magistrate", "jurisdiction",
    "agreement", "register", "account", "interest",
    "establishing", "maintaining", "operating", "governing",
    "amending", "ratifying", "revoking", "judging",
    "formally", "materially", "substantially", "publicly",
    "public", "domestic", "foreign", "material", "substantial",
    "partial",
}


def _classify_jurisdiction(word: str) -> str:
    """Heuristic jurisdiction classification for a basis word."""
    w = word.lower()
    if w in SEA_WORDS:
        return "sea/water"
    if w in LAND_WORDS:
        return "land/soil"
    if w in AIR_WORDS:
        return "air/ether"
    # Default based on role could be applied by caller
    return "unclassified"


def _is_now_time_valid(word: str, role: str) -> bool:
    """
    Check if a word is valid in now-time.

    - Gerund verbs (-ing) are always now-time valid
    - Past tense (-ed) is dead time (but adjectives like 'written' may appear)
    - Future modals (shall, will) are fiction
    - Prepositions: 'to' and 'from' are NOT now-time
    - All nouns and articles are now-time by default
    """
    w = word.lower()

    if role == "PREPOSITION":
        invalid_preps = {"to", "from"}
        return w not in invalid_preps

    if role == "VERB_GERUND":
        return w.endswith("ing")

    if role == "ADVERB":
        # Adverbs that imply future or past
        dead_adverbs = {"formerly", "previously", "hereafter"}
        return w not in dead_adverbs

    if role == "ADJECTIVE":
        # Past-tense adjectives are dead-time descriptors
        dead_adjs = {"dead", "false", "void", "fraudulent", "counterfeit",
                     "fictional", "absent", "unjust", "uncertain", "bound"}
        return w not in dead_adjs

    # Nouns and articles are now-time valid by default
    return True


# ---------------------------------------------------------------------------
# Basis generation
# ---------------------------------------------------------------------------

def generate_basis() -> list[dict]:
    """
    Generate the 720-word basis set.

    Each word entry contains:
        word, role, position, decomposition, jurisdiction,
        now_time_valid, negated
    """
    basis = []
    seen = set()

    for role, words in ROLE_WORDS.items():
        position_info = POSITIONS[role]

        for word in words:
            w = word.lower().strip()

            # Avoid duplicates (a word may appear in multiple roles;
            # we keep the first occurrence and note it)
            key = (w, role)
            if key in seen:
                continue
            seen.add(key)

            # Decompose
            decomp = decompose(w)

            # Classify
            jurisdiction = _classify_jurisdiction(w)
            now_time = _is_now_time_valid(w, role)
            negated = decomp.get("is_negated", False)

            entry = {
                "word": w,
                "role": role,
                "position": position_info["position"],
                "position_description": position_info["description"],
                "decomposition": {
                    "prefix": decomp["prefix"],
                    "prefix_meaning": decomp["prefix_meaning"],
                    "root": decomp["root"],
                    "root_meaning": decomp["root_meaning"],
                    "suffix": decomp["suffix"],
                    "suffix_meaning": decomp["suffix_meaning"],
                },
                "true_meaning": decomp["true_meaning"],
                "apparent_meaning": decomp["apparent_meaning"],
                "jurisdiction": jurisdiction,
                "now_time_valid": now_time,
                "negated": negated,
            }

            basis.append(entry)

    return basis


def save_basis(basis: list[dict], path: str | Path | None = None) -> Path:
    """Save the basis set to a JSON file."""
    if path is None:
        path = Path(__file__).resolve().parent.parent / "data" / "basis_720.json"
    else:
        path = Path(path)

    # Ensure the directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "title": "720-Word Quantum Grammar Basis Set",
                "description": (
                    "720 = 6! — the complete permutation space of the six "
                    "sentence positions in C.S.S.C.P.S.G.P. correct grammar. "
                    "Each word is decomposed, classified by jurisdiction, and "
                    "evaluated for now-time validity."
                ),
                "positions": POSITIONS,
                "total_words": len(basis),
                "basis": basis,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    return path


def print_stats(basis: list[dict]) -> None:
    """Print summary statistics for the basis set."""
    total = len(basis)

    # By role
    role_counts: dict[str, int] = {}
    for entry in basis:
        role = entry["role"]
        role_counts[role] = role_counts.get(role, 0) + 1

    # By jurisdiction
    jur_counts: dict[str, int] = {}
    for entry in basis:
        j = entry["jurisdiction"]
        jur_counts[j] = jur_counts.get(j, 0) + 1

    # Negated
    negated_count = sum(1 for e in basis if e["negated"])

    # Now-time valid
    now_time_count = sum(1 for e in basis if e["now_time_valid"])

    print()
    print("=" * 56)
    print("  720-WORD QUANTUM GRAMMAR BASIS SET")
    print("=" * 56)
    print(f"  Total words: {total}")
    print(f"  Target: 720 (6! = six factorial)")
    print()

    print("  BY SENTENCE POSITION:")
    for role in POSITIONS:
        count = role_counts.get(role, 0)
        pos = POSITIONS[role]["position"]
        print(f"    {pos}. {role:20s} {count:4d} words")
    print()

    print("  BY JURISDICTION:")
    for j in sorted(jur_counts.keys()):
        count = jur_counts[j]
        pct = (count / total * 100) if total else 0
        print(f"    {j:20s} {count:4d} words  ({pct:5.1f}%)")
    print()

    print("  ANALYSIS:")
    neg_pct = (negated_count / total * 100) if total else 0
    now_pct = (now_time_count / total * 100) if total else 0
    print(f"    VCC-negated words : {negated_count:4d}  ({neg_pct:5.1f}%)")
    print(f"    Now-time valid    : {now_time_count:4d}  ({now_pct:5.1f}%)")
    print(f"    Dead/future time  : {total - now_time_count:4d}  ({100 - now_pct:5.1f}%)")
    print()


def print_preview(basis: list[dict], limit: int = 20) -> None:
    """Print a preview of the first N basis entries."""
    print(f"\n  PREVIEW (first {limit} of {len(basis)} entries):\n")
    for entry in basis[:limit]:
        neg = " [NEG]" if entry["negated"] else ""
        now = " [NOW]" if entry["now_time_valid"] else " [DEAD]"
        print(
            f"    {entry['word']:20s}  "
            f"{entry['role']:16s}  "
            f"{entry['jurisdiction']:14s}"
            f"{neg}{now}"
        )
    if len(basis) > limit:
        print(f"    ... and {len(basis) - limit} more")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    args = set(sys.argv[1:])

    # Generate the basis
    basis = generate_basis()

    # Always print stats
    print_stats(basis)

    if "--preview" in args:
        print_preview(basis, limit=30)

    if "--stats" not in args and "--preview" not in args:
        # Save to file
        output_path = save_basis(basis)
        print(f"  Saved to: {output_path}")
        print(f"  Words generated: {len(basis)}")
        print()
    elif "--stats" in args:
        # Stats only, don't save
        pass


if __name__ == "__main__":
    main()
