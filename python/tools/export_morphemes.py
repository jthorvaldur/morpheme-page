"""
export_morphemes.py — Export all morpheme data to a single JSON file

Single source of truth: python/src/morpheme_negation.py
Output: data/morphemes.json (consumed by all viz pages)

Run during build to keep everything in sync:
    python python/tools/export_morphemes.py

Exports:
    - prefixes (56 entries with meanings)
    - roots (195 entries with meanings)
    - suffixes (52 entries with meanings)
    - vcc_negation_prefixes (13 entries)
    - known_decompositions (66+ entries)
    - word_frequency_ranks (500 entries for info calculation)
    - synonym_map (common English → basis root)
    - stats (counts, version)
"""

import json
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))

from morpheme_negation import (
    PREFIXES, ROOTS, SUFFIXES,
    VCC_NEGATION_PREFIXES,
    KNOWN_DECOMPOSITIONS,
)

# Word frequency ranks — top 500 English words by frequency
WORD_RANKS_LIST = (
    "the be to of and a in that have i it for not on with he as you do at "
    "this but his by from they we her she or an will my one all would there "
    "their what so up out if about who get which go me when make can like "
    "time no just him know take people into year your good some could them "
    "see other than then now look only come its over think also back after "
    "use two how our work first well way even new want because any these "
    "give day most us great big high small long little much before right "
    "too mean old where still should call world through keep last never let "
    "begin seem help show hear play run move live believe hold bring happen "
    "write provide sit stand lose pay meet include continue set learn change "
    "lead understand watch follow stop create speak read allow add spend "
    "grow open walk win offer remember love consider appear buy wait serve "
    "die send expect build stay fall cut reach kill remain suggest raise "
    "pass sell require report decide pull develop feel say tell ask try "
    "need find leave put man woman child hand eye head face body house room "
    "home water money book word law court land power name death government "
    "person fact case point part place end question state number school "
    "right city company system program war country problem group line side "
    "night god light earth life thing kind form door car table family "
    "mother father story girl boy son daughter morning reason mind voice "
    "heart air nothing something everything food friend class game month "
    "week church blood fire market trade ship vessel contract authority "
    "property title claim trust estate capital currency jurisdiction "
    "sovereign statute certificate mortgage insurance opinion agreement "
    "corporation register license sentence charge dock bar suit bank bond "
    "security credit debit interest account value tax duty warrant judge "
    "jury counsel attorney witness evidence verdict arrest bail plaintiff "
    "defendant tribunal decree ordinance lien summons parole dominion "
    "liberty freedom commerce instrument document seal signature"
).split()

# Synonym map — common English → basis root
SYNONYM_MAP = {
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


def export():
    output = {
        "version": "1.0",
        "prefixes": PREFIXES,
        "roots": ROOTS,
        "suffixes": SUFFIXES,
        "vcc_negation_prefixes": VCC_NEGATION_PREFIXES,
        "known_decompositions": KNOWN_DECOMPOSITIONS,
        "word_frequency_ranks": {w: i+1 for i, w in enumerate(WORD_RANKS_LIST)},
        "synonym_map": SYNONYM_MAP,
        "stats": {
            "prefix_count": len(PREFIXES),
            "root_count": len(ROOTS),
            "suffix_count": len(SUFFIXES),
            "total_morphemes": len(PREFIXES) + len(ROOTS) + len(SUFFIXES),
            "decomposition_count": len(KNOWN_DECOMPOSITIONS),
            "vcc_prefix_count": len(VCC_NEGATION_PREFIXES),
            "synonym_count": len(SYNONYM_MAP),
            "frequency_rank_count": len(WORD_RANKS_LIST),
        },
    }

    out_path = _root.parent / "data" / "morphemes.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Exported to {out_path}")
    print(f"  Prefixes: {len(PREFIXES)}")
    print(f"  Roots: {len(ROOTS)}")
    print(f"  Suffixes: {len(SUFFIXES)}")
    print(f"  VCC negation: {len(VCC_NEGATION_PREFIXES)}")
    print(f"  Decompositions: {len(KNOWN_DECOMPOSITIONS)}")
    print(f"  Word ranks: {len(WORD_RANKS_LIST)}")
    print(f"  Synonyms: {len(SYNONYM_MAP)}")


if __name__ == "__main__":
    export()
