from pathlib import Path

from core_engine import UserProfile, SchemeRecommender, redact_sensitive_text

ROOT = Path(__file__).resolve().parents[1]


def test_redaction():
    cleaned = redact_sensitive_text("Call 9876543210 and email test@example.com; id 123456789012")
    assert "9876543210" not in cleaned
    assert "test@example.com" not in cleaned
    assert "123456789012" not in cleaned


def test_recommendation_smoke(tmp_path):
    engine = SchemeRecommender(ROOT / "sample_schemes.csv", tmp_path / "bandit.json")
    profile = UserProfile(age=27, gender="Female", pregnant=True, need_text="pregnancy hospital maternal healthcare")
    results = engine.recommend(profile, top_k=5)
    assert len(results) == 5
    assert any("Janani" in item["name"] for item in results)
    assert all("verification_note" in item for item in results)


def test_feedback_is_aggregate(tmp_path):
    engine = SchemeRecommender(ROOT / "sample_schemes.csv", tmp_path / "bandit.json")
    engine.record_feedback("scholarship_search", True)
    assert engine.bandit.state["scholarship_search"]["positive"] == 1
