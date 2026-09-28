"""Create review sheets and summarize human-rated prompt evaluations."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

DIMENSIONS = ("accuracy", "relevance", "instruction_adherence")
VERSIONS = ("baseline", "structured")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def make_review_sheet(cases_data: dict[str, Any]) -> dict[str, Any]:
    cases = cases_data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list")
    seen: set[str] = set()
    reviews = []
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValueError("every case must have a unique, non-empty id")
        seen.add(case_id)
        for version in VERSIONS:
            reviews.append(
                {
                    "case_id": case_id,
                    "area": case["area"],
                    "task": case.get("task", ""),
                    "reference_context": case.get("reference_context", ""),
                    "constraints": case.get("constraints", []),
                    "prompt_version": version,
                    "output": "",
                    "scores": {dimension: None for dimension in DIMENSIONS},
                    "evidence_notes": "",
                }
            )
    return {
        "run_metadata": {"model": "", "date": "", "settings": ""},
        "rubric_dimensions": list(DIMENSIONS),
        "reviews": reviews,
    }


def summarize_reviews(review_data: dict[str, Any]) -> dict[str, Any]:
    reviews = review_data.get("reviews")
    if not isinstance(reviews, list) or not reviews:
        raise ValueError("reviews must be a non-empty list")

    by_version: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_area: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for review in reviews:
        case_id = review.get("case_id")
        version = review.get("prompt_version")
        area = review.get("area")
        if not all(isinstance(value, str) and value for value in (case_id, version, area)):
            raise ValueError("each review needs case_id, prompt_version, and area")
        if version not in VERSIONS:
            raise ValueError(f"unsupported prompt_version: {version}")
        key = (case_id, version)
        if key in seen:
            raise ValueError(f"duplicate review for case {case_id} and version {version}")
        seen.add(key)
        scores = review.get("scores")
        if not isinstance(scores, dict):
            raise ValueError(f"review {case_id}/{version} needs a scores object")
        for dimension in DIMENSIONS:
            score = scores.get(dimension)
            if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
                raise ValueError(f"{case_id}/{version}: {dimension} must be an integer from 1 to 5")
        if not str(review.get("output", "")).strip():
            raise ValueError(f"{case_id}/{version}: output cannot be blank")
        if not str(review.get("evidence_notes", "")).strip():
            raise ValueError(f"{case_id}/{version}: evidence_notes cannot be blank")
        by_version[version].append(review)
        by_area[area].append(review)

    def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "review_count": len(rows),
            "dimensions": {
                dimension: round(mean(row["scores"][dimension] for row in rows), 2)
                for dimension in DIMENSIONS
            },
            "overall": round(
                mean(
                    score
                    for row in rows
                    for score in (row["scores"][dimension] for dimension in DIMENSIONS)
                ),
                2,
            ),
        }

    return {
        "run_metadata": review_data.get("run_metadata", {}),
        "review_count": len(reviews),
        "by_prompt_version": {key: aggregate(value) for key, value in sorted(by_version.items())},
        "by_area": {key: aggregate(value) for key, value in sorted(by_area.items())},
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Prompt Evaluation Summary",
        "",
        f"Reviews: {report['review_count']}",
        "",
        "## By prompt version",
        "",
        "| Version | Reviews | Accuracy | Relevance | Instruction adherence | Overall |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for version, summary in report["by_prompt_version"].items():
        scores = summary["dimensions"]
        lines.append(
            f"| {version} | {summary['review_count']} | {scores['accuracy']:.2f} | "
            f"{scores['relevance']:.2f} | {scores['instruction_adherence']:.2f} | {summary['overall']:.2f} |"
        )
    lines.extend(["", "## By task area", "", "| Area | Reviews | Overall |", "| --- | ---: | ---: |"])
    for area, summary in report["by_area"].items():
        lines.append(f"| {area} | {summary['review_count']} | {summary['overall']:.2f} |")
    lines.extend(
        [
            "",
            "> Scores summarize human reviews in the input file; they do not establish objective model quality.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="create a blank review sheet")
    init_parser.add_argument("--cases", required=True, type=Path)
    init_parser.add_argument("--output", required=True, type=Path)
    score_parser = subparsers.add_parser("score", help="validate reviews and write summary reports")
    score_parser.add_argument("--input", required=True, type=Path)
    score_parser.add_argument("--json", required=True, type=Path)
    score_parser.add_argument("--markdown", required=True, type=Path)
    args = parser.parse_args()

    if args.command == "init":
        result = make_review_sheet(load_json(args.cases))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Created review sheet: {args.output} ({len(result['reviews'])} review slots)")
    else:
        result = summarize_reviews(load_json(args.input))
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        args.markdown.write_text(render_markdown(result), encoding="utf-8")
        print(f"Scored {result['review_count']} reviews; wrote {args.json} and {args.markdown}")


if __name__ == "__main__":
    main()
