import pandas as pd

from app import build_filtered_queue


def test_build_filtered_queue_keeps_completed_rows_for_selected_validator():
    df = pd.DataFrame([
        {"Validated By": "alice", "Lead Ranking": "bad"},
        {"Validated By": "alice", "Lead Ranking": ""},
        {"Validated By": "bob", "Lead Ranking": "good"},
        {"Validated By": "alice", "Lead Ranking": ""},
    ])

    validated, filtered_queue = build_filtered_queue(df, "alice")

    assert validated == {0}
    assert filtered_queue == [0, 1, 3]
