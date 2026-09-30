from pathlib import Path

from visitor_counter import increment_counter, increment_local_counter


def test_local_counter_increments_and_never_displays_zero(tmp_path: Path):
    path = tmp_path / "visitor_count.json"
    first = increment_local_counter(path)
    second = increment_local_counter(path)
    assert first.value == 1
    assert second.value == 2
    assert first.value > 0
    assert second.value > 0
    assert first.persistent_across_restarts is False


def test_counter_without_github_secret_uses_flat_file(tmp_path: Path):
    snapshot = increment_counter(counter_file=tmp_path / "visitor_count.json")
    assert snapshot.value == 1
    assert snapshot.backend == "local JSON file"
