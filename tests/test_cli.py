import pytest

from prompt_eval.cli import make_review_sheet, summarize_reviews


def test_review_sheet_creates_two_slots_per_case():
    sheet = make_review_sheet({"cases": [{"id": "case-1", "area": "coding"}]})
    assert len(sheet["reviews"]) == 2
    assert {row["prompt_version"] for row in sheet["reviews"]} == {"baseline", "structured"}


def test_review_sheet_rejects_duplicate_case_ids():
    with pytest.raises(ValueError, match="unique"):
        make_review_sheet({"cases": [{"id": "x", "area": "coding"}, {"id": "x", "area": "research"}]})


def test_summary_averages_ratings_by_version_and_area():
    reviews = []
    for version, score in (("baseline", 3), ("structured", 5)):
        reviews.append({
            "case_id": "case-1",
            "area": "coding",
            "prompt_version": version,
            "output": "A reviewed answer",
            "scores": {"accuracy": score, "relevance": score, "instruction_adherence": score},
            "evidence_notes": "The fixture confirms the expected format.",
        })
    result = summarize_reviews({"reviews": reviews})
    assert result["by_prompt_version"]["baseline"]["overall"] == 3
    assert result["by_prompt_version"]["structured"]["overall"] == 5
    assert result["by_area"]["coding"]["review_count"] == 2


def test_summary_rejects_unscored_or_blank_reviews():
    review = {
        "case_id": "case-1", "area": "coding", "prompt_version": "baseline", "output": "answer",
        "scores": {"accuracy": None, "relevance": 4, "instruction_adherence": 4}, "evidence_notes": "note",
    }
    with pytest.raises(ValueError, match="accuracy"):
        summarize_reviews({"reviews": [review]})
