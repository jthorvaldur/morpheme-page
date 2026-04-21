#!/usr/bin/env python3
"""
batch_evaluate.py — Run full quantum grammar analysis on a directory of text files.

Runs: DOG-LATIN detection, sentence analysis, null chain detection, word decomposition,
and jurisdiction mapping on each document. Outputs a comprehensive report.

Usage:
    python tools/batch_evaluate.py <input_dir> [--output report.md]
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from morpheme_negation import decompose, is_vcc_negated, KNOWN_DECOMPOSITIONS
from dog_latin_detector import scan_document, classify_token
from sentence_analyzer import analyze_sentence
from adverb_verb_detector import detect_null_chains, score_factual_content
from case_analyzer import analyze_case_form

INPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/tmp/qwl_analysis"
OUTPUT_FILE = None
for i, arg in enumerate(sys.argv):
    if arg == "--output" and i + 1 < len(sys.argv):
        OUTPUT_FILE = sys.argv[i + 1]


def analyze_document(text: str, filename: str) -> dict:
    """Run all analysis tools on a document."""
    result = {
        "filename": filename,
        "char_count": len(text),
        "word_count": len(text.split()),
    }

    # DOG-LATIN scan
    dog_latin = scan_document(text)
    total_tok = dog_latin.get("total_tokens", 1)
    dl_count = dog_latin.get("dog_latin_count", 0)
    eng_count = dog_latin.get("english_count", 0)
    dim_count = dog_latin.get("diminished_count", 0)
    result["dog_latin"] = {
        "total_tokens": total_tok,
        "dog_latin_count": dl_count,
        "dog_latin_pct": dog_latin.get("dog_latin_pct", round(dl_count / total_tok * 100, 1) if total_tok else 0),
        "english_pct": round(eng_count / total_tok * 100, 1) if total_tok else 0,
        "diminished_pct": round(dim_count / total_tok * 100, 1) if total_tok else 0,
        "jurisdiction_mixing": dog_latin.get("jurisdiction_mixing", False),
        "warnings": dog_latin.get("warnings", []),
        "assessment": dog_latin.get("assessment", ""),
    }

    # Sentence analysis (sample first 10 sentences)
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]
    sentence_scores = []
    sentence_issues = []
    total_nouns = 0
    total_null_chains = 0
    has_past_tense = 0
    has_future_tense = 0
    has_pronouns = 0

    for sent in sentences[:20]:  # Analyze up to 20 sentences
        try:
            analysis = analyze_sentence(sent)
            sentence_scores.append(analysis.get("score", 0))
            total_nouns += analysis.get("noun_count", 0)
            if analysis.get("has_null_chain"):
                total_null_chains += 1
            if analysis.get("has_past_tense"):
                has_past_tense += 1
            if analysis.get("has_future_tense"):
                has_future_tense += 1
            if analysis.get("has_pronouns"):
                has_pronouns += 1
            for issue in analysis.get("issues", []):
                sentence_issues.append(issue)
        except Exception:
            pass

    avg_score = sum(sentence_scores) / len(sentence_scores) if sentence_scores else 0
    if avg_score >= 80:
        grade = "A"
    elif avg_score >= 60:
        grade = "B"
    elif avg_score >= 40:
        grade = "C"
    elif avg_score >= 20:
        grade = "D"
    else:
        grade = "F"

    result["sentence_analysis"] = {
        "sentences_analyzed": len(sentence_scores),
        "average_score": round(avg_score, 1),
        "grade": grade,
        "total_nouns": total_nouns,
        "null_chains": total_null_chains,
        "past_tense_sentences": has_past_tense,
        "future_tense_sentences": has_future_tense,
        "pronoun_sentences": has_pronouns,
        "top_issues": list(set(sentence_issues))[:10],
    }

    # Null chain detection
    null_chains = detect_null_chains(text)
    result["null_chains"] = {
        "count": len(null_chains),
        "examples": [nc.get("text", nc.get("chain", ""))[:80] for nc in null_chains[:5]],
    }

    # Factual content score
    try:
        factual = score_factual_content(text)
        result["factual_content"] = {
            "noun_ratio": round(factual.get("noun_ratio", 0), 3),
            "null_ratio": round(factual.get("null_ratio", 0), 3),
            "fact_score": round(factual.get("fact_score", factual.get("noun_ratio", 0)) * 100, 1),
        }
    except Exception:
        result["factual_content"] = {"noun_ratio": 0, "null_ratio": 0, "fact_score": 0}

    # VCC negation - check key words in the document
    words = set(text.lower().split())
    negated_words = []
    for word in words:
        clean = "".join(c for c in word if c.isalpha())
        if clean and is_vcc_negated(clean) and clean in KNOWN_DECOMPOSITIONS:
            dec = KNOWN_DECOMPOSITIONS[clean]
            negated_words.append({
                "word": clean,
                "true_meaning": dec.get("true_meaning", ""),
            })

    result["vcc_negated_terms"] = negated_words[:15]

    # Jurisdiction determination
    dog_pct = result["dog_latin"]["dog_latin_pct"]
    if dog_pct > 50:
        jurisdiction = "SEA/WATER — Maritime/Admiralty"
    elif dog_pct > 20:
        jurisdiction = "MIXED — Sea/Water dominant with Land elements"
    elif avg_score > 60:
        jurisdiction = "LAND/SOIL — Common Law"
    else:
        jurisdiction = "SEA/WATER — Statute/Corporate"

    result["jurisdiction"] = jurisdiction

    return result


def format_report(results: list[dict]) -> str:
    """Generate a markdown report from all analyses."""
    lines = []
    lines.append("# QUANTUM GRAMMAR ANALYSIS — Court Filing Evaluation\n")
    lines.append(f"**Documents analyzed:** {len(results)}")
    lines.append(f"**Analysis date:** 2026-04-21\n")
    lines.append("---\n")

    # Summary table
    lines.append("## SUMMARY\n")
    lines.append("| # | Document | Grade | DOG-LATIN % | Null Chains | Nouns | Jurisdiction |")
    lines.append("|---|----------|-------|-------------|-------------|-------|--------------|")
    for i, r in enumerate(results, 1):
        name = r["filename"].replace(".txt", "")
        grade = r["sentence_analysis"]["grade"]
        dl_pct = r["dog_latin"]["dog_latin_pct"]
        nc = r["null_chains"]["count"]
        nouns = r["sentence_analysis"]["total_nouns"]
        jur = r["jurisdiction"].split("—")[0].strip()
        lines.append(f"| {i} | {name} | **{grade}** | {dl_pct:.0f}% | {nc} | {nouns} | {jur} |")

    lines.append("")

    # Aggregate stats
    all_grades = [r["sentence_analysis"]["grade"] for r in results]
    all_dl = [r["dog_latin"]["dog_latin_pct"] for r in results]
    all_nc = [r["null_chains"]["count"] for r in results]
    avg_dl = sum(all_dl) / len(all_dl) if all_dl else 0
    total_nc = sum(all_nc)
    grade_f_count = all_grades.count("F")
    grade_d_count = all_grades.count("D")

    lines.append("## AGGREGATE FINDINGS\n")
    lines.append(f"- **Average DOG-LATIN density:** {avg_dl:.1f}%")
    lines.append(f"- **Total null chains across all documents:** {total_nc}")
    lines.append(f"- **Documents scoring F:** {grade_f_count}/{len(results)}")
    lines.append(f"- **Documents scoring D or below:** {grade_f_count + grade_d_count}/{len(results)}")
    lines.append(f"- **Jurisdiction mixing detected:** {sum(1 for r in results if r['dog_latin']['jurisdiction_mixing'])}/{len(results)} documents")
    lines.append("")

    # Per-document detail
    lines.append("## DOCUMENT DETAILS\n")
    for i, r in enumerate(results, 1):
        name = r["filename"].replace(".txt", "")
        lines.append(f"### {i}. {name}\n")
        lines.append(f"- **Words:** {r['word_count']}")
        lines.append(f"- **Grade:** {r['sentence_analysis']['grade']} ({r['sentence_analysis']['average_score']}/100)")
        lines.append(f"- **DOG-LATIN:** {r['dog_latin']['dog_latin_pct']:.1f}% ({r['dog_latin']['dog_latin_count']}/{r['dog_latin']['total_tokens']} tokens)")
        lines.append(f"- **Jurisdiction mixing:** {'YES' if r['dog_latin']['jurisdiction_mixing'] else 'No'}")
        lines.append(f"- **Null chains:** {r['null_chains']['count']}")
        lines.append(f"- **Nouns (fact-carriers):** {r['sentence_analysis']['total_nouns']}")
        lines.append(f"- **Past tense (dead time):** {r['sentence_analysis']['past_tense_sentences']}/{r['sentence_analysis']['sentences_analyzed']} sentences")
        lines.append(f"- **Future/modal (fiction):** {r['sentence_analysis']['future_tense_sentences']}/{r['sentence_analysis']['sentences_analyzed']} sentences")
        lines.append(f"- **Pronouns (fact removal):** {r['sentence_analysis']['pronoun_sentences']}/{r['sentence_analysis']['sentences_analyzed']} sentences")
        lines.append(f"- **Jurisdiction:** {r['jurisdiction']}")

        if r["vcc_negated_terms"]:
            lines.append(f"- **VCC-negated terms found:** {', '.join(w['word'] + '=' + w['true_meaning'] for w in r['vcc_negated_terms'][:5])}")

        if r["null_chains"]["examples"]:
            lines.append(f"- **Null chain examples:**")
            for ex in r["null_chains"]["examples"][:3]:
                lines.append(f"  - \"{ex}...\"")

        if r["sentence_analysis"]["top_issues"]:
            lines.append(f"- **Top issues:**")
            for issue in r["sentence_analysis"]["top_issues"][:5]:
                lines.append(f"  - {issue}")

        lines.append("")

    # Meta-pattern assessment
    lines.append("## META-PATTERN ASSESSMENT\n")
    lines.append("### Step 1 — NAME (Morphological Inversion)")
    all_negated = set()
    for r in results:
        for w in r["vcc_negated_terms"]:
            all_negated.add(f"{w['word']} = {w['true_meaning']}")
    if all_negated:
        lines.append(f"\nVCC-negated terms found across all documents:")
        for term in sorted(all_negated):
            lines.append(f"- {term}")
    lines.append("")

    lines.append("### Step 2 — WRITE (Typographic Fraud)")
    lines.append(f"\n- Average DOG-LATIN density: {avg_dl:.1f}%")
    lines.append(f"- Jurisdiction mixing in {sum(1 for r in results if r['dog_latin']['jurisdiction_mixing'])}/{len(results)} documents")
    lines.append(f"- Per Chicago Manual 11:147: DOG-LATIN and English cannot share jurisdiction on one page")
    lines.append("")

    lines.append("### Step 3 — STRUCTURE (Null Construction)")
    lines.append(f"\n- Total null chains: {total_nc}")
    lines.append(f"- Documents with zero noun-facts in sampled sentences: check individual reports above")
    lines.append("")

    lines.append("### Step 4 — OVERLAY (Jurisdiction Mapping)")
    sea_count = sum(1 for r in results if "SEA" in r["jurisdiction"])
    land_count = sum(1 for r in results if "LAND" in r["jurisdiction"])
    lines.append(f"\n- Documents operating in Sea/Water (Maritime): {sea_count}/{len(results)}")
    lines.append(f"- Documents operating in Land/Soil (Common Law): {land_count}/{len(results)}")
    lines.append("")

    lines.append("---\n")
    lines.append("*Generated by words_quantum_legal analysis suite*")
    lines.append("*Tools: document_evaluator, dog_latin_detector, sentence_analyzer, adverb_verb_detector, case_analyzer, morpheme_negation*")

    return "\n".join(lines)


def main():
    input_path = Path(INPUT_DIR)
    if not input_path.exists():
        print(f"Error: {INPUT_DIR} does not exist")
        sys.exit(1)

    files = sorted(input_path.glob("*.txt"))
    if not files:
        print(f"No .txt files found in {INPUT_DIR}")
        sys.exit(1)

    print(f"Analyzing {len(files)} documents...\n")

    results = []
    for f in files:
        text = f.read_text(errors="replace")
        if len(text.strip()) < 50:
            print(f"  SKIP {f.name} (too short)")
            continue
        print(f"  Analyzing: {f.name} ({len(text.split())} words)")
        result = analyze_document(text, f.name)
        results.append(result)
        print(f"    → Grade: {result['sentence_analysis']['grade']} | DOG-LATIN: {result['dog_latin']['dog_latin_pct']:.0f}% | Null chains: {result['null_chains']['count']}")

    print(f"\n{'='*60}")
    print(f"ANALYSIS COMPLETE: {len(results)} documents")
    print(f"{'='*60}\n")

    report = format_report(results)

    if OUTPUT_FILE:
        Path(OUTPUT_FILE).write_text(report)
        print(f"Report saved to: {OUTPUT_FILE}")
    else:
        print(report)

    # Also save JSON for programmatic use
    json_path = Path(OUTPUT_FILE).with_suffix(".json") if OUTPUT_FILE else Path(INPUT_DIR) / "analysis_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"JSON data saved to: {json_path}")


if __name__ == "__main__":
    main()
