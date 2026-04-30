"""
whatsapp_embed.py — Parse WhatsApp exports and compute embeddings

Parses WhatsApp chat export (.txt), extracts messages,
computes per-message features using the morpheme/coherence toolkit,
and reports dimensionality.

WhatsApp export format:
    [DD/MM/YYYY, HH:MM:SS] Contact Name: message text
    or
    DD/MM/YYYY, HH:MM - Contact Name: message text

Usage:
    python tools/whatsapp_embed.py path/to/chat.txt
    python tools/whatsapp_embed.py path/to/chat.txt --contact "Alice"
    python tools/whatsapp_embed.py --demo
"""

from __future__ import annotations

import re
import sys
import math
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# Allow imports from src/
_tools = Path(__file__).resolve().parent
_root = _tools.parent
sys.path.insert(0, str(_root / "src"))

from morpheme_negation import PREFIXES, ROOTS, SUFFIXES

# ---------------------------------------------------------------------------
# ANSI
# ---------------------------------------------------------------------------

RST = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GOLD = "\033[33m"
GREEN = "\033[32m"
PURPLE = "\033[35m"
RED = "\033[31m"

# ---------------------------------------------------------------------------
# WhatsApp parser
# ---------------------------------------------------------------------------

# Common WhatsApp export patterns
PATTERNS = [
    # [DD/MM/YYYY, HH:MM:SS] Name: msg
    re.compile(r"\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\]\s+([^:]+):\s+(.*)"),
    # DD/MM/YYYY, HH:MM - Name: msg
    re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*([^:]+):\s+(.*)"),
    # MM/DD/YY, HH:MM AM/PM - Name: msg
    re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])\s*[-–]\s*([^:]+):\s+(.*)"),
]

def parse_whatsapp(filepath: str) -> list[dict]:
    """Parse a WhatsApp export file into structured messages."""
    messages = []
    path = Path(filepath)

    if not path.exists():
        print(f"{RED}File not found: {filepath}{RST}")
        return []

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    current_msg = None

    for line in lines:
        matched = False
        for pattern in PATTERNS:
            m = pattern.match(line)
            if m:
                if current_msg:
                    messages.append(current_msg)
                current_msg = {
                    "date": m.group(1),
                    "time": m.group(2),
                    "sender": m.group(3).strip(),
                    "text": m.group(4).strip(),
                }
                matched = True
                break

        if not matched and current_msg:
            # Continuation line
            current_msg["text"] += " " + line.strip()

    if current_msg:
        messages.append(current_msg)

    return messages


# ---------------------------------------------------------------------------
# Feature extraction (no neural network — pure morpheme toolkit)
# ---------------------------------------------------------------------------

# Stop words for info calculation
STOPS = frozenset(
    "the a an is are was were be been to of in for on at by with from as "
    "and but or not no it its this that i me my you your he him his she her "
    "we us our they them their than very just also too then now".split()
)

# Word frequency ranks (top 200)
RANKS = {}
"the be to of and a in that have i it for not on with he as you do at this but his by from they we her she or an will my one all would there their what so up out if about who get which go me when make can like time no just him know take people into year your good some could them see other than then now look only come its over think also back after use two how our work first well way even new want because any these give day most us".split(" ")
for _i, _w in enumerate("the be to of and a in that have i it for not on with he as you do at this but his by from they we her she or an will my one all would there their what so up out if about who get which go me when make can like time no just him know take people into year your good some could them see other than then now look only come its over think also back after use two how our work first well way even new want because any these give day most us".split()):
    RANKS[_w] = _i + 1


def get_info(word: str) -> float:
    w = word.lower().strip()
    if not w:
        return 0
    rank = RANKS.get(w)
    if rank:
        return math.log2(rank) + 2
    return min(10 + len(w) * 0.5, 16)


def extract_features(text: str) -> dict:
    """Extract language features from a message."""
    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return {"word_count": 0, "info_density": 0, "content_ratio": 0,
                "vocab_richness": 0, "redundancy": 0, "coherence": 0}

    infos = [get_info(w) for w in words]
    avg_info = sum(infos) / len(infos) if infos else 0

    unique = set(words)
    vocab_richness = len(unique) / len(words) if words else 0

    content = [w for w in words if w not in STOPS and len(w) > 2]
    content_ratio = len(content) / len(words) if words else 0

    redundancy = 1 - vocab_richness

    # Emoji count
    emoji_count = len(re.findall(r"[\U0001f300-\U0001f9ff]", text))

    # Coherence (simplified)
    coherence = min(100, max(0,
        (avg_info / 12) * 30 +
        content_ratio * 30 +
        vocab_richness * 25 +
        (1 - redundancy) * 15
    ))

    return {
        "word_count": len(words),
        "char_count": len(text),
        "info_density": round(avg_info, 2),
        "content_ratio": round(content_ratio, 3),
        "vocab_richness": round(vocab_richness, 3),
        "redundancy": round(redundancy, 3),
        "coherence": round(coherence, 1),
        "emoji_count": emoji_count,
        "unique_words": len(unique),
    }


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_chat(messages: list[dict], contact_filter: str | None = None) -> dict:
    """Full analysis of a WhatsApp chat."""
    if contact_filter:
        messages = [m for m in messages if contact_filter.lower() in m["sender"].lower()]

    if not messages:
        return {"error": "No messages found"}

    # Extract features for each message
    for msg in messages:
        msg["features"] = extract_features(msg["text"])

    # Aggregate
    senders = Counter(m["sender"] for m in messages)
    total_words = sum(m["features"]["word_count"] for m in messages)
    total_chars = sum(m["features"]["char_count"] for m in messages)
    avg_coherence = sum(m["features"]["coherence"] for m in messages) / len(messages)
    avg_info = sum(m["features"]["info_density"] for m in messages if m["features"]["word_count"] > 0) / max(1, sum(1 for m in messages if m["features"]["word_count"] > 0))
    avg_words_per_msg = total_words / len(messages) if messages else 0

    # Dimensionality calculation
    features_per_msg = 800  # 768 embedding + 32 metadata
    total_dims = len(messages) * features_per_msg

    return {
        "total_messages": len(messages),
        "total_words": total_words,
        "total_chars": total_chars,
        "senders": dict(senders),
        "avg_coherence": round(avg_coherence, 1),
        "avg_info_density": round(avg_info, 2),
        "avg_words_per_msg": round(avg_words_per_msg, 1),
        "features_per_msg": features_per_msg,
        "total_continuous_dims": total_dims,
        "messages": messages,
    }


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

def demo():
    """Run with synthetic WhatsApp-like data."""
    demo_messages = [
        {"date": "01/01/2024", "time": "09:00", "sender": "Alice", "text": "did you see the new filing requirements? the court changed the deadline"},
        {"date": "01/01/2024", "time": "09:02", "sender": "Bob", "text": "which jurisdiction? the maritime rules or the common law ones"},
        {"date": "01/01/2024", "time": "09:03", "sender": "Alice", "text": "the federal court. they want the certificate of standing by thursday"},
        {"date": "01/01/2024", "time": "09:05", "sender": "Bob", "text": "the decomposition of that filing shows null chains in every paragraph. adverb verb adverb verb with zero noun facts"},
        {"date": "01/01/2024", "time": "09:06", "sender": "Alice", "text": "that's the point though. they structure it to command without communicating. no facts means no liability"},
        {"date": "01/01/2024", "time": "09:08", "sender": "Bob", "text": "right. the parse syntax analysis scores it F. zero prepositional grounding. future tense fiction throughout"},
        {"date": "01/01/2024", "time": "09:09", "sender": "Alice", "text": "can we encode our response using the basis set? strip it to pure facts"},
        {"date": "01/01/2024", "time": "09:11", "sender": "Bob", "text": "for the claiming of the land by the living man with the lawful standing of the sovereign authority"},
        {"date": "01/01/2024", "time": "09:12", "sender": "Alice", "text": "that compresses to eight glyphs. every word carries. no waste"},
        {"date": "01/01/2024", "time": "09:14", "sender": "Bob", "text": "the vector codec round trips at 100 percent for that sentence"},
        {"date": "01/01/2024", "time": "09:15", "sender": "Alice", "text": "perfect. file it in correct parse syntax form. prepositional opening. gerund verbs. noun facts only"},
        {"date": "01/01/2024", "time": "09:16", "sender": "Bob", "text": "done. coverage is 100 percent basis aligned. information density 7.9 bits per word"},
    ]
    return demo_messages


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_analysis(result: dict, contact_filter: str | None = None):
    """Pretty-print analysis results."""
    print(f"\n{BOLD}{'='*64}{RST}")
    print(f"  {CYAN}WHATSAPP DIMENSION ANALYSIS{RST}")
    if contact_filter:
        print(f"  {DIM}Filtered: {contact_filter}{RST}")
    print(f"{'='*64}")

    print(f"\n{GOLD}SCALE:{RST}")
    print(f"  Messages:     {result['total_messages']:>10,}")
    print(f"  Words:        {result['total_words']:>10,}")
    print(f"  Characters:   {result['total_chars']:>10,}")

    print(f"\n{GOLD}SENDERS:{RST}")
    for sender, count in sorted(result["senders"].items(), key=lambda x: -x[1]):
        pct = count / result["total_messages"] * 100
        bar = "█" * int(pct / 2)
        print(f"  {sender:25s} {count:>6,} ({pct:>5.1f}%) {bar}")

    print(f"\n{GOLD}LANGUAGE METRICS:{RST}")
    print(f"  Avg coherence:    {result['avg_coherence']:>8.1f} / 100")
    print(f"  Avg info density: {result['avg_info_density']:>8.2f} bits/word")
    print(f"  Avg msg length:   {result['avg_words_per_msg']:>8.1f} words")

    print(f"\n{PURPLE}DIMENSIONALITY:{RST}")
    print(f"  Features/message: {result['features_per_msg']:>10,}")
    print(f"  Total continuous: {result['total_continuous_dims']:>10,}")
    print(f"  As % of 101M:     {result['total_continuous_dims'] / 101_892_096 * 100:>9.2f}%")

    # Per-message coherence breakdown (top/bottom 3)
    msgs_with_score = [(m, m["features"]["coherence"]) for m in result["messages"]
                       if m["features"]["word_count"] > 3]
    if msgs_with_score:
        msgs_with_score.sort(key=lambda x: -x[1])
        print(f"\n{GREEN}HIGHEST COHERENCE:{RST}")
        for m, s in msgs_with_score[:3]:
            print(f"  {GREEN}{s:>5.1f}{RST}  {m['sender']}: {m['text'][:70]}{'...' if len(m['text']) > 70 else ''}")

        print(f"\n{RED}LOWEST COHERENCE:{RST}")
        for m, s in msgs_with_score[-3:]:
            print(f"  {RED}{s:>5.1f}{RST}  {m['sender']}: {m['text'][:70]}{'...' if len(m['text']) > 70 else ''}")

    print(f"{'='*64}\n")


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--demo":
        messages = demo()
        contact_filter = None
        if "--contact" in sys.argv:
            idx = sys.argv.index("--contact")
            contact_filter = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        result = analyze_chat(messages, contact_filter)
        print_analysis(result, contact_filter)
        return

    filepath = sys.argv[1]
    contact_filter = None
    if "--contact" in sys.argv:
        idx = sys.argv.index("--contact")
        contact_filter = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

    messages = parse_whatsapp(filepath)
    if not messages:
        print(f"{RED}No messages parsed from {filepath}{RST}")
        return

    result = analyze_chat(messages, contact_filter)
    print_analysis(result, contact_filter)


if __name__ == "__main__":
    main()
