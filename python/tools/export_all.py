#!/usr/bin/env python3
"""
export_all.py — Canonical data export from Python source to JSON.

Single source of truth pipeline:
  Python (morpheme_negation.py, basis_generator.py)
    → data/*.json
      → viz/*.html (fetch at runtime)

Usage:
    python python/tools/export_all.py
"""

import sys
import json
from pathlib import Path

# Setup paths
PROJECT = Path(__file__).resolve().parent.parent.parent
SRC = PROJECT / "python" / "src"
DATA = PROJECT / "data"
sys.path.insert(0, str(SRC))

from morpheme_negation import (
    KNOWN_DECOMPOSITIONS, PREFIXES, ROOTS, SUFFIXES,
    is_vcc_negated, decompose
)
from basis_generator import generate_basis

DATA.mkdir(exist_ok=True)


def export_decompositions():
    """Export all known decompositions to JSON."""
    entries = []
    for word, data in sorted(KNOWN_DECOMPOSITIONS.items()):
        entry = {
            "word": word,
            "prefix": data.get("prefix", ""),
            "prefix_meaning": data.get("prefix_meaning", ""),
            "root": data.get("root", ""),
            "root_meaning": data.get("root_meaning", ""),
            "suffix": data.get("suffix", ""),
            "suffix_meaning": data.get("suffix_meaning", ""),
            "is_negated": data.get("is_negated", False),
            "true_meaning": data.get("true_meaning", ""),
            "apparent_meaning": data.get("apparent_meaning", ""),
            "domain": "legal",
            "status": "approved",
        }
        entries.append(entry)

    path = DATA / "decompositions.json"
    path.write_text(json.dumps(entries, indent=2))
    print(f"  decompositions.json: {len(entries)} entries")
    return entries


def export_dictionaries():
    """Export prefix, root, suffix dictionaries."""
    (DATA / "prefixes.json").write_text(json.dumps(PREFIXES, indent=2))
    (DATA / "roots.json").write_text(json.dumps(ROOTS, indent=2))
    (DATA / "suffixes.json").write_text(json.dumps(SUFFIXES, indent=2))
    print(f"  prefixes.json: {len(PREFIXES)} entries")
    print(f"  roots.json: {len(ROOTS)} entries")
    print(f"  suffixes.json: {len(SUFFIXES)} entries")


def export_basis():
    """Regenerate the 720-word basis set."""
    basis = generate_basis()
    path = DATA / "basis_720.json"
    path.write_text(json.dumps(basis, indent=2))
    print(f"  basis_720.json: {len(basis)} entries")
    return basis


def export_domains(decompositions):
    """Export cross-domain decomposition data for the domain decomposer."""
    # The domain decomposer needs words categorized by domain
    # For now, all known decompositions are "legal" domain
    # Add cross-domain words from the domain_decomposer's inline data
    domains = {
        "legal": [],
        "medical": [
            {"word": "pharmacy", "root": "pharma", "root_meaning": "poison/drug", "true_meaning": "Place of poisons — Greek pharmakon = poison/sorcery", "apparent_meaning": "Place to get medicine"},
            {"word": "doctor", "root": "doc", "root_meaning": "teach", "true_meaning": "One who teaches — Latin docere, not 'one who heals'", "apparent_meaning": "Medical professional"},
            {"word": "patient", "root": "pat", "root_meaning": "suffer/endure", "true_meaning": "One who suffers — Latin patiens = enduring passively", "apparent_meaning": "Person receiving care"},
            {"word": "hospital", "root": "hospit", "root_meaning": "host/stranger", "true_meaning": "Place for strangers — Latin hospes, same root as hostile", "apparent_meaning": "Place of healing"},
            {"word": "prescription", "prefix": "pre", "prefix_meaning": "before", "root": "script", "root_meaning": "write", "true_meaning": "Written before examination — pre-scripted remedy", "apparent_meaning": "Doctor's medication order"},
            {"word": "diagnosis", "prefix": "dia", "prefix_meaning": "through", "root": "gnos", "root_meaning": "know", "true_meaning": "Through knowing — but who knows?", "apparent_meaning": "Identification of disease"},
            {"word": "symptom", "root": "symptom", "root_meaning": "happening/falling together", "true_meaning": "A coincidence — Greek symptoma = a happening", "apparent_meaning": "Sign of illness"},
            {"word": "therapy", "root": "therap", "root_meaning": "attend/serve", "true_meaning": "Attendance upon — service, not cure", "apparent_meaning": "Treatment for healing"},
            {"word": "vaccine", "root": "vacc", "root_meaning": "cow", "true_meaning": "Of the cow — Latin vacca, from Jenner's cowpox origin", "apparent_meaning": "Immunization"},
            {"word": "virus", "root": "virus", "root_meaning": "poison/venom", "true_meaning": "Poison — Latin virus = poison, slime, venom", "apparent_meaning": "Infectious agent"},
        ],
        "financial": [
            {"word": "money", "root": "monet", "root_meaning": "warn/mint", "true_meaning": "Warning — Latin Moneta, Juno's temple where coins struck AND futures foretold", "apparent_meaning": "Medium of exchange"},
            {"word": "bank", "root": "banc", "root_meaning": "bench/table", "true_meaning": "Bench — Italian banca, same as judge's bench in court", "apparent_meaning": "Financial institution"},
            {"word": "credit", "root": "cred", "root_meaning": "believe/trust", "true_meaning": "Belief — Latin credere = to believe. Faith-based, not asset-based", "apparent_meaning": "Borrowing power"},
            {"word": "debt", "prefix": "de", "prefix_meaning": "from", "root": "hab", "root_meaning": "have", "true_meaning": "To have from — Latin debere = to owe, de + habere", "apparent_meaning": "Money owed"},
            {"word": "interest", "prefix": "inter", "prefix_meaning": "between", "root": "esse", "root_meaning": "to be", "true_meaning": "Being between — in limbo, neither here nor there", "apparent_meaning": "Return on investment"},
            {"word": "bond", "root": "bond", "root_meaning": "fetter/chain", "true_meaning": "Fetter — Old English = chain, bondage, restraint", "apparent_meaning": "Investment instrument"},
            {"word": "stock", "root": "stocc", "root_meaning": "trunk/block", "true_meaning": "Block of punishment — Old English stocc = tree trunk, pillory", "apparent_meaning": "Company ownership share"},
            {"word": "capital", "root": "capit", "root_meaning": "head", "true_meaning": "Head — Latin caput, as in per-capita = per head of livestock/cargo", "apparent_meaning": "Wealth/assets"},
            {"word": "currency", "root": "curr", "root_meaning": "run/flow", "true_meaning": "That which flows — Latin currere, like a water current through banks", "apparent_meaning": "Money in circulation"},
            {"word": "security", "prefix": "se", "prefix_meaning": "without/apart", "root": "cur", "root_meaning": "care", "true_meaning": "Without care — Latin securus = free from anxiety", "apparent_meaning": "Safety/investment"},
        ],
        "education": [
            {"word": "education", "prefix": "e", "prefix_meaning": "out of", "root": "duc", "root_meaning": "lead", "true_meaning": "To lead out — but modern education leads IN (indoctrination)", "apparent_meaning": "Process of learning"},
            {"word": "school", "root": "schol", "root_meaning": "leisure/rest", "true_meaning": "Leisure — Greek skhole = rest/free time, inverted to compulsion", "apparent_meaning": "Place of learning"},
            {"word": "curriculum", "root": "curric", "root_meaning": "running course", "true_meaning": "Chariot track — Latin curriculum = a running course. You are the horse", "apparent_meaning": "Course of study"},
            {"word": "discipline", "root": "discip", "root_meaning": "follower/learner", "true_meaning": "Follower — Latin discipulus, not independent thinker", "apparent_meaning": "Training/control"},
            {"word": "degree", "prefix": "de", "prefix_meaning": "down", "root": "gree", "root_meaning": "step/grade", "true_meaning": "Step down — Latin de + gradus = degradation?", "apparent_meaning": "Academic qualification"},
            {"word": "university", "prefix": "uni", "prefix_meaning": "one", "root": "vers", "root_meaning": "turn", "true_meaning": "Turned into one — uniformity, not diversity", "apparent_meaning": "Institution of higher learning"},
            {"word": "professor", "prefix": "pro", "prefix_meaning": "forward/forth", "root": "fess", "root_meaning": "speak/declare", "true_meaning": "One who speaks forth — not necessarily one who knows", "apparent_meaning": "Academic expert"},
            {"word": "student", "root": "stud", "root_meaning": "be eager/zealous", "true_meaning": "One who is eager — Latin studere, reduced to 'one who is taught'", "apparent_meaning": "Learner"},
        ],
        "religion": [
            {"word": "religion", "prefix": "re", "prefix_meaning": "back/again", "root": "lig", "root_meaning": "bind", "true_meaning": "To bind back — Latin religare = to restrain, to tie back", "apparent_meaning": "System of faith"},
            {"word": "worship", "root": "worth", "root_meaning": "worthy/value", "suffix": "ship", "suffix_meaning": "state/condition", "true_meaning": "State of worthiness — Old English weorthscipe, now = submission", "apparent_meaning": "Devotion to God"},
            {"word": "prayer", "root": "prec", "root_meaning": "beg/entreat", "true_meaning": "To beg — Latin precari = to BEG, not to commune", "apparent_meaning": "Communication with God"},
            {"word": "sacrament", "root": "sacr", "root_meaning": "holy/sacred", "suffix": "ment", "suffix_meaning": "mind/state", "true_meaning": "Military oath — Latin sacramentum = soldier's oath, bond money", "apparent_meaning": "Holy ritual"},
            {"word": "pastor", "root": "pastor", "root_meaning": "shepherd", "true_meaning": "Shepherd — Latin pastor. You are the sheep = livestock = chattel", "apparent_meaning": "Religious leader"},
            {"word": "congregation", "prefix": "con", "prefix_meaning": "together", "root": "greg", "root_meaning": "flock/herd", "true_meaning": "Herded together — Latin congregare = to herd (livestock language)", "apparent_meaning": "Religious community"},
        ],
        "technology": [
            {"word": "protocol", "root": "proto", "root_meaning": "first", "suffix": "col", "suffix_meaning": "glued", "true_meaning": "First page glued to scroll — Greek protokollon, establishing authority", "apparent_meaning": "Set of rules"},
            {"word": "terminal", "root": "termin", "root_meaning": "end/boundary/death", "true_meaning": "End/death — Latin terminus = boundary, death point", "apparent_meaning": "Computer interface"},
            {"word": "server", "root": "serv", "root_meaning": "serve/slave", "true_meaning": "One who serves — a servant", "apparent_meaning": "Computer providing services"},
            {"word": "client", "root": "client", "root_meaning": "dependent/follower", "true_meaning": "Dependent — Latin cliens = one under patronage, a follower", "apparent_meaning": "User of a service"},
            {"word": "daemon", "root": "daemon", "root_meaning": "spirit/divine being", "true_meaning": "Spirit — Greek daimon = spirit, divine being", "apparent_meaning": "Background process"},
            {"word": "kernel", "root": "kern", "root_meaning": "seed/core", "true_meaning": "Hidden inner authority — Old English cyrnel = seed, the core of power", "apparent_meaning": "OS core"},
            {"word": "execute", "prefix": "ex", "prefix_meaning": "out/carry out", "root": "sequ", "root_meaning": "follow", "true_meaning": "To follow out / to carry out — same as legal execution (kill)", "apparent_meaning": "Run a program"},
        ],
        "psychology": [
            {"word": "psychiatry", "root": "psych", "root_meaning": "soul/breath", "suffix": "iatry", "suffix_meaning": "healing", "true_meaning": "Soul-healing — but practiced as medical, not spiritual", "apparent_meaning": "Mental health medicine"},
            {"word": "disorder", "prefix": "dis", "prefix_meaning": "apart/away", "root": "ord", "root_meaning": "order/rank/command", "true_meaning": "Outside the commanded order — deviation from the norm", "apparent_meaning": "Medical condition"},
            {"word": "normal", "root": "norm", "root_meaning": "carpenter's square/rule", "true_meaning": "Conformity to a rigid template — Latin norma = measuring tool", "apparent_meaning": "Typical/healthy"},
            {"word": "anxiety", "root": "anxi", "root_meaning": "choke/strangle", "true_meaning": "Choking — Latin anxius = to choke, strangle. Physical binding", "apparent_meaning": "Mental worry"},
            {"word": "depression", "prefix": "de", "prefix_meaning": "down", "root": "press", "root_meaning": "push/squeeze", "true_meaning": "Pushed down — literally pressed downward", "apparent_meaning": "Mental health condition"},
            {"word": "addiction", "prefix": "ad", "prefix_meaning": "toward/assigned to", "root": "dict", "root_meaning": "say/declare", "true_meaning": "One assigned/given over — Latin addictus = SLAVE assigned to a creditor", "apparent_meaning": "Compulsive dependency"},
            {"word": "institution", "prefix": "in", "prefix_meaning": "into", "root": "stit", "root_meaning": "place/stand", "true_meaning": "Placed into — imprisoned, institutionalized", "apparent_meaning": "Established organization"},
        ],
    }

    # Add legal domain from known decompositions
    for entry in decompositions:
        domains["legal"].append(entry)

    path = DATA / "domains.json"
    path.write_text(json.dumps(domains, indent=2))
    total = sum(len(v) for v in domains.values())
    print(f"  domains.json: {total} entries across {len(domains)} domains")


def main():
    print("=== export_all.py — Canonical Data Export ===\n")

    decompositions = export_decompositions()
    export_dictionaries()
    basis = export_basis()
    export_domains(decompositions)

    print(f"\n=== Done. All data exported to {DATA}/ ===")
    print(f"Files: decompositions.json, prefixes.json, roots.json, suffixes.json, basis_720.json, domains.json")


if __name__ == "__main__":
    main()
