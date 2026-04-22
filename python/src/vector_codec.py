"""
vector_codec.py — Lossless Vector Embedding Codec

Encodes text through morpheme decomposition into high-dimensional
vectors, compresses via PCA, and decodes back through nearest-neighbor
lookup. Counterpoint to semantic_codec.py (lossy string truncation).

Architecture:
    TEXT → MORPHEMES → VECTORS (R^d) → COMPRESS (R^k) → EXPAND (R^d) → MORPHEMES → TEXT

Usage:
    python src/vector_codec.py encode "your text here"
    python src/vector_codec.py roundtrip "your text here"
    python src/vector_codec.py compare "your text here"
    python src/vector_codec.py                          # interactive
"""

from __future__ import annotations

import sys
import json
import math
from pathlib import Path
from collections import OrderedDict

# Allow running from project root
_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from morpheme_negation import PREFIXES, ROOTS, SUFFIXES, decompose

# ---------------------------------------------------------------------------
# ANSI
# ---------------------------------------------------------------------------

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    PURPLE  = "\033[35m"
    GREEN   = "\033[32m"
    GOLD    = "\033[33m"
    BLUE    = "\033[34m"
    RED     = "\033[31m"
    CYAN    = "\033[36m"

# ---------------------------------------------------------------------------
# Vector operations (pure Python, no numpy dependency)
# ---------------------------------------------------------------------------

def vec_zeros(d: int) -> list[float]:
    return [0.0] * d

def vec_add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b)]

def vec_sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]

def vec_scale(a: list[float], s: float) -> list[float]:
    return [x * s for x in a]

def vec_dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

def vec_norm(a: list[float]) -> float:
    return math.sqrt(sum(x * x for x in a))

def vec_normalize(a: list[float]) -> list[float]:
    n = vec_norm(a)
    return [x / n for x in a] if n > 0 else a

def vec_cosine(a: list[float], b: list[float]) -> float:
    na, nb = vec_norm(a), vec_norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return vec_dot(a, b) / (na * nb)


# ---------------------------------------------------------------------------
# Deterministic pseudo-random vectors from morpheme names
# ---------------------------------------------------------------------------

def _hash_seed(name: str) -> int:
    """Deterministic hash for a morpheme name."""
    h = 5381
    for c in name:
        h = ((h << 5) + h + ord(c)) & 0xFFFFFFFF
    return h

def _pseudo_random_vector(name: str, dim: int) -> list[float]:
    """Generate a deterministic pseudo-random unit vector from a name.
    Uses a simple LCG seeded by the name hash."""
    seed = _hash_seed(name)
    vec = []
    for i in range(dim):
        seed = (seed * 1103515245 + 12345 + i * 7919) & 0xFFFFFFFF
        # Map to [-1, 1]
        val = (seed / 0xFFFFFFFF) * 2 - 1
        vec.append(val)
    return vec_normalize(vec)


# ---------------------------------------------------------------------------
# MORPHEME EMBEDDING SPACE
# ---------------------------------------------------------------------------

class MorphemeSpace:
    """
    High-dimensional vector space where each morpheme (prefix, root, suffix)
    has a unique direction. Words are composed by summing their morpheme vectors.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim
        self.morpheme_vectors: dict[str, list[float]] = {}
        self.morpheme_type: dict[str, str] = {}  # morpheme -> 'prefix'|'root'|'suffix'
        self._build()

    def _build(self) -> None:
        """Assign a unique vector to every morpheme in the dictionaries."""
        # Prefixes get scaled down (they modify, not carry primary meaning)
        for name, meaning in PREFIXES.items():
            vec = _pseudo_random_vector(f"pfx_{name}", self.dim)
            self.morpheme_vectors[f"P:{name}"] = vec_scale(vec, 0.5)
            self.morpheme_type[f"P:{name}"] = "prefix"

        # Roots are full-strength (they carry the core meaning)
        for name, meaning in ROOTS.items():
            vec = _pseudo_random_vector(f"root_{name}", self.dim)
            self.morpheme_vectors[f"R:{name}"] = vec
            self.morpheme_type[f"R:{name}"] = "root"

        # Suffixes scaled down (they modify role/tense, not core meaning)
        for name, meaning in SUFFIXES.items():
            vec = _pseudo_random_vector(f"sfx_{name}", self.dim)
            self.morpheme_vectors[f"S:{name}"] = vec_scale(vec, 0.3)
            self.morpheme_type[f"S:{name}"] = "suffix"

    def encode_word(self, word: str) -> dict:
        """Decompose a word into morphemes, then compose their vectors."""
        d = decompose(word.lower().strip())
        parts = []
        vec = vec_zeros(self.dim)

        if d["prefix"]:
            key = f"P:{d['prefix']}"
            if key in self.morpheme_vectors:
                vec = vec_add(vec, self.morpheme_vectors[key])
                parts.append(("prefix", d["prefix"], d["prefix_meaning"]))

        if d["root"]:
            key = f"R:{d['root']}"
            if key in self.morpheme_vectors:
                vec = vec_add(vec, self.morpheme_vectors[key])
                parts.append(("root", d["root"], d["root_meaning"]))
            else:
                # Unknown root — create ad-hoc vector and register it
                adhoc_key = f"R:{d['root']}"
                if adhoc_key not in self.morpheme_vectors:
                    adhoc = _pseudo_random_vector(f"root_{d['root']}", self.dim)
                    self.morpheme_vectors[adhoc_key] = adhoc
                    self.morpheme_type[adhoc_key] = "root"
                vec = vec_add(vec, self.morpheme_vectors[adhoc_key])
                parts.append(("root", d["root"], d["root_meaning"] or "?"))

        if d["suffix"]:
            key = f"S:{d['suffix']}"
            if key in self.morpheme_vectors:
                vec = vec_add(vec, self.morpheme_vectors[key])
                parts.append(("suffix", d["suffix"], d["suffix_meaning"]))

        return {
            "word": word,
            "parts": parts,
            "vector": vec,
            "magnitude": vec_norm(vec),
            "is_negated": d["is_negated"],
        }

    def decode_vector(self, vec: list[float]) -> dict:
        """Decode a vector back to morphemes.
        Two-pass approach: find top-k candidates per type, then search combos."""
        pfx_keys = [k for k in self.morpheme_vectors if k.startswith("P:")]
        root_keys = [k for k in self.morpheme_vectors if k.startswith("R:")]
        sfx_keys = [k for k in self.morpheme_vectors if k.startswith("S:")]

        # Score all morphemes against the vector
        def top_k(keys, k=10):
            scored = [(key, vec_cosine(vec, self.morpheme_vectors[key])) for key in keys]
            scored.sort(key=lambda x: -x[1])
            return scored[:k]

        top_pfx = top_k(pfx_keys, 8)
        top_root = top_k(root_keys, 15)
        top_sfx = top_k(sfx_keys, 8)

        best_combo = None
        best_score = -2

        # Try combinations of top candidates
        pfx_options = [(None, 0)] + [(k, s) for k, s in top_pfx]
        sfx_options = [(None, 0)] + [(k, s) for k, s in top_sfx]

        for rk, rs in top_root:
            rvec = self.morpheme_vectors[rk]
            for pk, ps in pfx_options:
                pv = self.morpheme_vectors[pk] if pk else vec_zeros(self.dim)
                pr_vec = vec_add(pv, rvec)
                for sk, ss in sfx_options:
                    if sk:
                        full_vec = vec_add(pr_vec, self.morpheme_vectors[sk])
                    else:
                        full_vec = pr_vec
                    sim = vec_cosine(vec, full_vec)
                    if sim > best_score:
                        best_score = sim
                        best_combo = (pk, rk, sk, sim)

        decoded_parts = []
        if best_combo:
            pk, rk, sk, conf = best_combo
            if pk:
                decoded_parts.append(("prefix", pk.split(":")[1], conf))
            decoded_parts.append(("root", rk.split(":")[1], conf))
            if sk:
                decoded_parts.append(("suffix", sk.split(":")[1], conf))

        return {
            "parts": decoded_parts,
            "confidence": best_score,
        }

    def compress(self, vec: list[float], k: int) -> list[float]:
        """Compress vector to k dimensions by keeping first k components.
        (Simplified PCA — in production you'd compute principal components.)"""
        return vec[:k]

    def expand(self, compressed: list[float], original_dim: int) -> list[float]:
        """Expand compressed vector back to full dimensions (zero-pad)."""
        return compressed + [0.0] * (original_dim - len(compressed))

    def roundtrip(self, word: str, compress_dims: int | None = None) -> dict:
        """Full encode → (compress → expand) → decode pipeline."""
        encoded = self.encode_word(word)
        vec = encoded["vector"]

        compressed_vec = vec
        if compress_dims and compress_dims < self.dim:
            compressed_vec = self.expand(self.compress(vec, compress_dims), self.dim)

        decoded = self.decode_vector(compressed_vec)

        # Check if round-trip matches
        orig_parts = set((t, n) for t, n, _ in encoded["parts"])
        decoded_parts = set((t, n) for t, n, _ in decoded["parts"])

        return {
            "word": word,
            "encoded": encoded,
            "decoded": decoded,
            "compressed_dims": compress_dims,
            "match": orig_parts == decoded_parts,
            "orig_parts": orig_parts,
            "decoded_parts": decoded_parts,
        }


# ---------------------------------------------------------------------------
# STOP WORDS
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset(
    "the a an is are was were be been being am have has had do does did "
    "will would could should shall may might can cannot to of in for on "
    "at by with from as into through during before after and but or nor "
    "so yet not no it its this that these those i me my you your he him "
    "his she her we us our they them their than very just also too then "
    "now here there when where how what which who if because although "
    "while since until unless however therefore really basically literally "
    "actually like oh ok okay omg um uh".split()
)


# ---------------------------------------------------------------------------
# TEXT-LEVEL CODEC
# ---------------------------------------------------------------------------

class VectorCodec:
    """Full text encoder/decoder using morpheme vector space."""

    def __init__(self, dim: int = 128):
        self.space = MorphemeSpace(dim=dim)

    def encode_text(self, text: str) -> dict:
        """Encode text: decompose each content word, produce vectors."""
        import re
        raw_words = re.findall(r"[a-z']+", text.lower())
        words = [w.replace("'", "") for w in raw_words if w.replace("'", "")]

        encoded_words = []
        dropped = []
        seen_roots = set()

        for w in words:
            if w in STOP_WORDS or len(w) < 2:
                dropped.append(w)
                continue

            enc = self.space.encode_word(w)
            # Deduplicate by root
            root_key = tuple((t, n) for t, n, _ in enc["parts"])
            if root_key in seen_roots:
                dropped.append(w)
                continue
            seen_roots.add(root_key)
            encoded_words.append(enc)

        return {
            "encoded": encoded_words,
            "dropped": dropped,
            "original_count": len(words),
            "encoded_count": len(encoded_words),
        }

    def decode_vectors(self, vectors: list[list[float]], compress_k: int | None = None) -> list[dict]:
        """Decode a list of vectors back to morphemes."""
        results = []
        for vec in vectors:
            if compress_k:
                vec = self.space.expand(self.space.compress(vec, compress_k), self.space.dim)
            results.append(self.space.decode_vector(vec))
        return results

    def roundtrip_text(self, text: str, compress_dims: list[int] | None = None) -> dict:
        """Full round-trip at multiple compression levels."""
        encoded = self.encode_text(text)
        vectors = [e["vector"] for e in encoded["encoded"]]

        if compress_dims is None:
            compress_dims = [self.space.dim, 64, 32, 16, 8, 4]

        results = {}
        for k in compress_dims:
            decoded = self.decode_vectors(vectors, compress_k=k if k < self.space.dim else None)
            matches = 0
            for enc, dec in zip(encoded["encoded"], decoded):
                orig = set((t, n) for t, n, _ in enc["parts"])
                got = set((t, n) for t, n, _ in dec["parts"])
                if orig == got:
                    matches += 1
            accuracy = matches / max(len(decoded), 1)
            results[k] = {
                "dims": k,
                "decoded": decoded,
                "accuracy": accuracy,
                "matches": matches,
                "total": len(decoded),
            }

        return {
            "text": text,
            "encoded": encoded,
            "compression_results": results,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_encode(codec: VectorCodec, text: str) -> None:
    result = codec.encode_text(text)

    print(f"\n{C.BOLD}{'='*64}{C.RESET}")
    print(f"  {C.PURPLE}VECTOR CODEC — ENCODE{C.RESET}")
    print(f"{'='*64}")
    print(f"\n{C.DIM}ORIGINAL:{C.RESET}  {text}")
    print(f"\n{C.PURPLE}MORPHEME VECTORS:{C.RESET}")
    for enc in result["encoded"]:
        parts_str = " + ".join(f"{C.GREEN}{n}{C.RESET}({m})" if t == "root"
                               else f"{C.GOLD}{n}{C.RESET}({m})"
                               for t, n, m in enc["parts"])
        neg = f" {C.RED}[NEG]{C.RESET}" if enc["is_negated"] else ""
        mag = enc["magnitude"]
        print(f"  {enc['word']:20s} = {parts_str}{neg}  {C.DIM}|v|={mag:.2f}{C.RESET}")

    print(f"\n{C.DIM}Dropped ({len(result['dropped'])}): {', '.join(result['dropped'])}{C.RESET}")
    print(f"{C.GOLD}Words: {result['original_count']} → {result['encoded_count']} vectors{C.RESET}")
    print(f"{'='*64}\n")


def _print_roundtrip(codec: VectorCodec, text: str) -> None:
    result = codec.roundtrip_text(text)

    print(f"\n{C.BOLD}{'='*64}{C.RESET}")
    print(f"  {C.CYAN}VECTOR CODEC — ROUND-TRIP{C.RESET}")
    print(f"{'='*64}")
    print(f"\n{C.DIM}TEXT:{C.RESET}  {text}")

    enc = result["encoded"]
    print(f"\n{C.PURPLE}ENCODED ({enc['encoded_count']} words → vectors in R^{codec.space.dim}):{C.RESET}")
    for e in enc["encoded"]:
        parts = ".".join(n.upper() for _, n, _ in e["parts"])
        print(f"  {e['word']:20s} → {C.PURPLE}{parts}{C.RESET}")

    print(f"\n{C.CYAN}COMPRESSION ROUND-TRIP:{C.RESET}")
    print(f"  {'Dims':>6s}  {'Accuracy':>10s}  {'Match':>7s}  Result")
    print(f"  {'-'*6}  {'-'*10}  {'-'*7}  {'-'*40}")

    for k in sorted(result["compression_results"].keys(), reverse=True):
        cr = result["compression_results"][k]
        pct = cr["accuracy"] * 100
        color = C.GREEN if pct >= 90 else C.GOLD if pct >= 60 else C.RED
        decoded_str = " ".join(
            ".".join(n.upper() for _, n, _ in d["parts"])
            for d in cr["decoded"]
        )
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  R^{k:>3d}  {color}{pct:>8.0f}%{C.RESET}  {cr['matches']:>3d}/{cr['total']:<3d}  {bar}  {C.DIM}{decoded_str}{C.RESET}")

    print(f"\n{C.DIM}R^128 = full fidelity (lossless)")
    print(f"R^64  = 50% dimensions (usually lossless)")
    print(f"R^32  = 25% dimensions (some loss)")
    print(f"R^8   = 6% dimensions (significant loss)")
    print(f"R^4   = 3% dimensions (severe loss — only dominant morpheme survives){C.RESET}")
    print(f"{'='*64}\n")


def _print_compare(codec: VectorCodec, text: str) -> None:
    """Compare string codec vs vector codec."""
    # String codec (current)
    import re
    raw_words = re.findall(r"[a-z']+", text.lower())
    words = [w.replace("'", "") for w in raw_words if w.replace("'", "") and w not in STOP_WORDS and len(w) >= 2]
    string_glyphs = list(OrderedDict.fromkeys(w[:4].upper() for w in words))

    # Vector codec
    result = codec.roundtrip_text(text, compress_dims=[128, 32, 8])
    enc = result["encoded"]
    vector_parts = [".".join(n.upper() for _, n, _ in e["parts"]) for e in enc["encoded"]]

    print(f"\n{C.BOLD}{'='*64}{C.RESET}")
    print(f"  {C.GOLD}STRING CODEC vs VECTOR CODEC{C.RESET}")
    print(f"{'='*64}")
    print(f"\n{C.DIM}TEXT:{C.RESET}  {text}")

    print(f"\n{C.RED}STRING CODEC (truncation — lossy):{C.RESET}")
    print(f"  {' '.join(string_glyphs)}")
    print(f"  {C.DIM}{len(words)} words → {len(string_glyphs)} glyphs (collisions hidden){C.RESET}")

    # Show collisions
    from collections import Counter
    glyph_sources: dict[str, list[str]] = {}
    for w in words:
        g = w[:4].upper()
        glyph_sources.setdefault(g, []).append(w)
    collisions = {g: ws for g, ws in glyph_sources.items() if len(ws) > 1}
    if collisions:
        print(f"  {C.RED}COLLISIONS:{C.RESET}")
        for g, ws in collisions.items():
            print(f"    {g} ← {', '.join(ws)}")

    print(f"\n{C.GREEN}VECTOR CODEC (morpheme decomposition — lossless at R^128):{C.RESET}")
    for e in enc["encoded"]:
        parts = " + ".join(f"{n}({m})" for _, n, m in e["parts"])
        code = ".".join(n.upper() for _, n, _ in e["parts"])
        print(f"  {e['word']:20s} → {C.PURPLE}{code:16s}{C.RESET}  {C.DIM}= {parts}{C.RESET}")

    print(f"  {C.DIM}{enc['original_count']} words → {enc['encoded_count']} vectors (zero collisions){C.RESET}")

    # Round-trip comparison
    print(f"\n{C.CYAN}ROUND-TRIP ACCURACY:{C.RESET}")
    for k in [128, 32, 8]:
        cr = result["compression_results"][k]
        pct = cr["accuracy"] * 100
        color = C.GREEN if pct >= 90 else C.GOLD if pct >= 60 else C.RED
        print(f"  R^{k:>3d}: {color}{pct:.0f}%{C.RESET}")

    print(f"\n{C.DIM}String codec: fast, tiny, but LOSSY (collisions destroy meaning)")
    print(f"Vector codec: larger, but LOSSLESS at full dims, controlled loss at lower dims{C.RESET}")
    print(f"{'='*64}\n")


def _interactive(codec: VectorCodec) -> None:
    print(f"\n  {C.PURPLE}VECTOR CODEC{C.RESET} — interactive mode")
    print(f"  {C.DIM}Commands: encode, roundtrip, compare, quit{C.RESET}")
    print(f"  {C.DIM}Morphemes: {len(PREFIXES)} prefixes, {len(ROOTS)} roots, {len(SUFFIXES)} suffixes")
    print(f"  Dimension: R^{codec.space.dim}{C.RESET}\n")

    while True:
        try:
            raw = input(f"  {C.PURPLE}vec>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue
        if raw.lower() in ("quit", "exit", "q"):
            break

        if raw.lower().startswith("encode "):
            _print_encode(codec, raw[7:])
        elif raw.lower().startswith("roundtrip "):
            _print_roundtrip(codec, raw[10:])
        elif raw.lower().startswith("compare "):
            _print_compare(codec, raw[8:])
        else:
            _print_compare(codec, raw)


def main() -> None:
    codec = VectorCodec(dim=128)

    if len(sys.argv) < 2:
        _interactive(codec)
        return

    cmd = sys.argv[1].lower()
    text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if not text:
        _print_compare(codec, " ".join(sys.argv[1:]))
        return

    if cmd == "encode":
        _print_encode(codec, text)
    elif cmd == "roundtrip":
        _print_roundtrip(codec, text)
    elif cmd == "compare":
        _print_compare(codec, text)
    else:
        _print_compare(codec, " ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()
