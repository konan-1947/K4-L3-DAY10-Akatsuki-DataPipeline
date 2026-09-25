from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Create a deterministic evaluation set from the cleaned dataframe.

    Pseudo-code:
    1. Kiem tra so luong document toi thieu.
    2. Chon mot so paper dai dien.
    3. Tao nhieu loai cau hoi:
       - summary
       - authors
       - date
       - categories
    4. Moi row can co:
       - id
       - question_type
       - question
       - ground_truth
       - ground_truth_doc_ids
    5. Ghi file JSON vao output_path.
    """
    if df.empty or len(df) < 4:
        raise ValueError("At least four cleaned documents are required to build the evaluation set.")

    rows = df.drop_duplicates(subset=["paper_id"]).head(10).to_dict(orient="records")
    if len(rows) < 4:
        raise ValueError("Evaluation set requires at least four unique documents.")

    # Ten deterministic questions, balanced across the four required types.
    plan = [
        ("summary", 0),
        ("summary", 1),
        ("summary", 2),
        ("authors", 3),
        ("authors", 4),
        ("authors", 5),
        ("date", 6),
        ("date", 7),
        ("categories", 8),
        ("categories", 9),
    ]
    test_set: list[dict[str, Any]] = []
    for number, (question_type, row_index) in enumerate(plan, start=1):
        row = rows[row_index % len(rows)]
        title = str(row["title"])
        paper_id = str(row["paper_id"])
        if question_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(str(row.get("summary", "")))
        elif question_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = str(row.get("authors_joined", ""))
        elif question_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = str(row.get("published", ""))
        else:
            question = f"What categories does the paper '{title}' belong to?"
            ground_truth = str(row.get("categories_joined", ""))
        test_set.append(
            {
                "id": f"eval_{number:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    write_json(output_path, test_set)
    return test_set
