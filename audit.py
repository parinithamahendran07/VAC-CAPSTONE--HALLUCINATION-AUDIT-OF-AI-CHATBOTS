"""Educational baseline for auditing chatbot answers against reference facts."""
from __future__ import annotations

import csv
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "sample_answers.csv"
OUTPUT_FILE = ROOT / "reports" / "audit_report.csv"

# Demonstration threshold only. It is not scientifically validated.
SIMILARITY_THRESHOLD = 0.25


def split_sentences(text: str) -> list[str]:
    """Split text into simple sentences."""
    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", text.strip())
        if part.strip()
    ]


def similarity(sentence: str, reference: str) -> float:
    """Return a basic character-sequence similarity score between 0 and 1."""
    return SequenceMatcher(
        None, sentence.lower(), reference.lower()
    ).ratio()


def audit_answer(answer: str, reference_facts: list[str]) -> list[dict]:
    """Compare each answer sentence with the closest supplied reference fact."""
    results = []

    for sentence in split_sentences(answer):
        best_score = max(
            (similarity(sentence, fact) for fact in reference_facts if fact.strip()),
            default=0.0,
        )
        status = (
            "SUPPORTED"
            if best_score >= SIMILARITY_THRESHOLD
            else "REVIEW NEEDED"
        )
        results.append({
            "sentence": sentence,
            "similarity": round(best_score, 3),
            "status": status,
        })

    return results


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    review_needed = 0

    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"question", "chatbot_answer", "reference_facts"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV must contain columns: {', '.join(sorted(required))}")

        with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as target:
            fieldnames = [
                "question", "sentence", "similarity", "status"
            ]
            writer = csv.DictWriter(target, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                facts = [
                    fact.strip()
                    for fact in row["reference_facts"].split(";")
                    if fact.strip()
                ]
                for result in audit_answer(row["chatbot_answer"], facts):
                    writer.writerow({
                        "question": row["question"],
                        **result,
                    })
                    total += 1
                    if result["status"] == "REVIEW NEEDED":
                        review_needed += 1

    print("Hallucination audit completed.")
    print(f"Sentences checked: {total}")
    print(f"Sentences needing human review: {review_needed}")
    print(f"Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
