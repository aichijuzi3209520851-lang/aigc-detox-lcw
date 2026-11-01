#!/usr/bin/env python3
"""Post-rewrite verification: compare a source DOCX against its rewritten copy.

None of the five source skills verified their own output. This closes that loop.

It answers three questions mechanically:
  1. Did the rewrite actually lower the risk signals?  (delta per feature)
  2. Did it damage any facts?  (citations / numbers / headings lost)
  3. Did it introduce NEW risk that was not there before?  (regressions)

Usage:
    python aigc_detox_lcw_compare.py before.docx after.docx
    python aigc_detox_lcw_compare.py before.docx after.docx --json out.json
    python aigc_detox_lcw_compare.py before.docx after.docx --require-delta 0.2
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aigc_detox_lcw_scan import (  # noqa: E402
    count_chars,
    iter_body_paragraph_elements,
    paragraph_element_text,
    scan_trace_features,
    split_sentences,
)

CITATION_RE = re.compile(r"\[\d+(?:\s*[-–,，、]\s*\d+)*\]")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def paragraphs(path: Path) -> list[str]:
    try:
        from docx import Document
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("python-docx is required: python -m pip install python-docx") from exc
    document = Document(str(path))
    return [
        text.strip()
        for text in (paragraph_element_text(p) for p in iter_body_paragraph_elements(document, include_tables=True))
        if text.strip()
    ]


def body_text(lines: list[str]) -> str:
    return "\n".join(lines)


def facts(text: str) -> dict[str, set[str]]:
    return {
        "citations": set(CITATION_RE.findall(text)),
        "numbers": set(NUMBER_RE.findall(text)),
    }


def feature_vector(text: str) -> dict[str, Any]:
    features = scan_trace_features(text)
    return {
        "riskSignalCount": len(features.riskSignals),
        "riskSignals": features.riskSignals,
        "mitigatingSignalCount": len(features.mitigatingSignals),
        "mitigatingSignals": features.mitigatingSignals,
        "templatePhraseCount": len(features.templatePhrases),
        "genericClaimCount": features.genericClaimCount,
        "connectorDensity": features.connectorDensity,
        "sentenceLengthCV": features.sentenceLengthCV,
        "uniformSentenceRhythm": features.uniformSentenceRhythm,
    }


def sentence_lengths(text: str) -> list[int]:
    # Must use count_chars, the same Chinese-aware counter the scanner uses,
    # or this CV cannot be compared with the scanner's own threshold.
    return [count_chars(s) for s in split_sentences(re.sub(r"\s+", " ", text))]


def cv_of(lengths: list[int]) -> float | None:
    if not lengths:
        return None
    avg = sum(lengths) / len(lengths)
    if not avg:
        return None
    var = sum((n - avg) ** 2 for n in lengths) / len(lengths)
    return round((var**0.5) / avg, 3)


def compare(before: list[str], after: list[str]) -> dict[str, Any]:
    before_text = body_text(before)
    after_text = body_text(after)

    before_facts = facts(before_text)
    after_facts = facts(after_text)

    lost_citations = sorted(before_facts["citations"] - after_facts["citations"])
    lost_numbers = sorted(before_facts["numbers"] - after_facts["numbers"], key=lambda n: (len(n), n))
    added_citations = sorted(after_facts["citations"] - before_facts["citations"])
    added_numbers = sorted(after_facts["numbers"] - before_facts["numbers"], key=lambda n: (len(n), n))

    before_vec = feature_vector(before_text)
    after_vec = feature_vector(after_text)

    new_risk = sorted(set(after_vec["riskSignals"]) - set(before_vec["riskSignals"]))
    fixed_risk = sorted(set(before_vec["riskSignals"]) - set(after_vec["riskSignals"]))
    kept_risk = sorted(set(after_vec["riskSignals"]) & set(before_vec["riskSignals"]))

    before_len = sentence_lengths(before_text)
    after_len = sentence_lengths(after_text)
    before_cv = cv_of(before_len)
    after_cv = cv_of(after_len)

    # A rewrite that is uniform-rhythmed when the source was not is a regression.
    rhythm_regression = (
        after_vec["uniformSentenceRhythm"] and not before_vec["uniformSentenceRhythm"]
    )
    # Flattening the length spread toward uniformity even without crossing the threshold.
    rhythm_flattened = (
        before_cv is not None and after_cv is not None and after_cv < before_cv * 0.6
    )

    return {
        "paragraphs": {"before": len(before), "after": len(after)},
        "chars": {"before": len(before_text), "after": len(after_text)},
        "risk": {
            "before": before_vec["riskSignalCount"],
            "after": after_vec["riskSignalCount"],
            "delta": after_vec["riskSignalCount"] - before_vec["riskSignalCount"],
            "fixed": fixed_risk,
            "kept": kept_risk,
            "introduced": new_risk,
        },
        "mitigating": {
            "before": before_vec["mitigatingSignalCount"],
            "after": after_vec["mitigatingSignalCount"],
            "delta": after_vec["mitigatingSignalCount"] - before_vec["mitigatingSignalCount"],
        },
        "templatePhrases": {
            "before": before_vec["templatePhraseCount"],
            "after": after_vec["templatePhraseCount"],
        },
        "genericClaims": {
            "before": before_vec["genericClaimCount"],
            "after": after_vec["genericClaimCount"],
        },
        "connectorDensity": {
            "before": before_vec["connectorDensity"],
            "after": after_vec["connectorDensity"],
        },
        "sentenceRhythm": {
            "beforeCV": before_cv,
            "afterCV": after_cv,
            "lengthsBefore": before_len,
            "lengthsAfter": after_len,
            "regression": rhythm_regression,
            "flattened": rhythm_flattened,
        },
        "facts": {
            "lostCitations": lost_citations,
            "lostNumbers": lost_numbers,
            "addedCitations": added_citations,
            "addedNumbers": added_numbers,
            "lostNumberCount": len(lost_numbers),
            "lostCitationCount": len(lost_citations),
        },
    }


def verdict_of(report: dict[str, Any]) -> tuple[str, list[str]]:
    problems: list[str] = []
    if report["facts"]["lostCitationCount"]:
        problems.append(f"丢失引用标记 {report['facts']['lostCitations']}")
    if report["facts"]["lostNumberCount"]:
        problems.append(f"丢失数字 {report['facts']['lostNumbers']}")
    if report["risk"]["introduced"]:
        problems.append(f"新增风险信号 {report['risk']['introduced']}")
    if report["sentenceRhythm"]["regression"]:
        problems.append("改写后句式节奏反而变得均匀（新的机器味）")
    elif report["sentenceRhythm"]["flattened"]:
        problems.append("句长分布被压平，节奏趋同")
    if report["risk"]["delta"] >= 0:
        problems.append(f"风险信号未下降（{report['risk']['before']} → {report['risk']['after']}）")
    if report["mitigating"]["delta"] < 0:
        problems.append("缓解信号减少，具体证据可能被改掉了")

    if not problems:
        return "PASS", problems
    hard = [p for p in problems if "丢失" in p]
    if hard:
        return "FAIL", problems
    return "WARN", problems


def render(report: dict[str, Any], verdict: str, problems: list[str]) -> str:
    r = report
    lines = [
        "=" * 62,
        "改写后复检报告 / post-rewrite verification",
        "=" * 62,
        "",
        f"段落数      {r['paragraphs']['before']} → {r['paragraphs']['after']}",
        f"正文字数    {r['chars']['before']} → {r['chars']['after']}",
        "",
        "── 风险信号 ──",
        f"  风险信号数  {r['risk']['before']} → {r['risk']['after']}  (Δ {r['risk']['delta']:+d})",
        f"  缓解信号数  {r['mitigating']['before']} → {r['mitigating']['after']}  (Δ {r['mitigating']['delta']:+d})",
        f"  模板短语    {r['templatePhrases']['before']} → {r['templatePhrases']['after']}",
        f"  泛化套话    {r['genericClaims']['before']} → {r['genericClaims']['after']}",
        f"  连接词密度  {r['connectorDensity']['before']} → {r['connectorDensity']['after']}",
        "",
        "── 句子节奏 ──",
        f"  句长变异系数 {r['sentenceRhythm']['beforeCV']} → {r['sentenceRhythm']['afterCV']}",
        f"  改写后句长   {r['sentenceRhythm']['lengthsAfter']}",
        "",
        "── 事实保全 ──",
        f"  丢失引用    {r['facts']['lostCitations'] or '无'}",
        f"  丢失数字    {r['facts']['lostNumbers'] or '无'}",
        f"  新增数字    {r['facts']['addedNumbers'] or '无'}",
        "",
        "── 风险评估 ──",
        f"  已消除  {r['risk']['fixed'] or '无'}",
        f"  仍存在  {r['risk']['kept'] or '无'}",
        f"  新引入  {r['risk']['introduced'] or '无'}",
        "",
        "=" * 62,
        f"结论：{verdict}",
    ]
    if problems:
        lines.append("")
        for problem in problems:
            lines.append(f"  · {problem}")
    lines.append("=" * 62)
    return "\n".join(lines)


def force_utf8_stdout() -> None:
    """Windows 控制台默认 GBK，中文报告会变乱码。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    force_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="Verify that a rewrite actually lowered risk and damaged no facts."
    )
    parser.add_argument("before", help="source DOCX")
    parser.add_argument("after", help="rewritten DOCX")
    parser.add_argument("--json", dest="json_path", help="write the full report as JSON")
    parser.add_argument("--quiet", action="store_true", help="print only the verdict line")
    args = parser.parse_args(argv)

    before_path, after_path = Path(args.before), Path(args.after)
    for path in (before_path, after_path):
        if not path.exists():
            print(f"文件不存在: {path}", file=sys.stderr)
            return 2

    report = compare(paragraphs(before_path), paragraphs(after_path))
    verdict, problems = verdict_of(report)
    report["verdict"] = verdict
    report["problems"] = problems
    report["paths"] = {"before": str(before_path.resolve()), "after": str(after_path.resolve())}

    if args.json_path:
        out = Path(args.json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.quiet:
        print(verdict)
    else:
        print(render(report, verdict, problems))

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
