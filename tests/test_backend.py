from pathlib import Path

from backend import BackendStore
from core_engine import UserProfile, load_default_engine

ROOT = Path(__file__).resolve().parents[1]


def make_store(tmp_path: Path) -> BackendStore:
    # Copy only the seed catalog required by BackendStore.
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "sample_schemes.csv").write_bytes((ROOT / "sample_schemes.csv").read_bytes())
    return BackendStore(tmp_path, database_url=f"sqlite:///{tmp_path / 'test.db'}", retention_days=365)


def test_backend_seeds_and_uses_privacy_minimized_profile(tmp_path: Path):
    store = make_store(tmp_path)
    assert len(store.list_schemes(include_inactive=False)) > 0

    profile = UserProfile(
        age=27,
        annual_income=250000,
        gender="Female",
        marital_status="Married",
        state="Maharashtra",
        residence="Urban",
        social_category="SC",
        student=True,
        pregnant=True,
        disability=True,
        need_text="healthcare",
    )
    store.record_consent("demo-1", "impact_analytics", True)
    store.upsert_beneficiary("demo-1", profile, "hi", "Health and family", True)
    summary = store.beneficiary_summary("demo-1")
    saved = summary["profile"]
    assert saved["age_band"] == "25-34"
    assert saved["income_band"] == "₹1L-₹3L"
    assert saved["gender"] == "Not stored"
    assert saved["marital_status"] == "Not stored"
    assert "pregnant" not in saved["profile_flags_json"]
    assert "disability" not in saved["profile_flags_json"]


def test_journey_metrics_and_deletion(tmp_path: Path):
    store = make_store(tmp_path)
    profile = UserProfile(age=32, annual_income=400000, state="Kerala", residence="Rural", farmer=True)
    store.upsert_beneficiary("demo-2", profile, "ml", "Agriculture", True)
    store.record_event("profile_saved", beneficiary_id="demo-2", language="ml", state="Kerala")
    store.record_matches(
        "demo-2",
        [{"scheme_id": "x", "name": "Synthetic Test Scheme", "status": "Potential match", "score": 0.9}],
    )
    store.record_event("scheme_matches_generated", beneficiary_id="demo-2", language="ml", state="Kerala")
    store.record_event("application_started", beneficiary_id="demo-2", scheme_id="x", scheme_name="Synthetic Test Scheme")
    store.record_event("application_completed", beneficiary_id="demo-2", scheme_id="x", scheme_name="Synthetic Test Scheme", metadata={"self_reported": True})

    metrics = store.impact_metrics()
    assert metrics["consented_profiles"] == 1
    assert metrics["scheme_matches"] == 1
    assert metrics["potential_beneficiaries"] == 1
    assert metrics["application_journeys_started"] == 1
    assert metrics["application_journeys_completed"] == 1

    store.delete_beneficiary_data("demo-2")
    summary = store.beneficiary_summary("demo-2")
    assert summary["profile"] is None
    assert summary["journey_events"] == 0
    assert summary["scheme_matches"] == 0


def test_scheme_admin_round_trip_and_engine_reads_backend(tmp_path: Path):
    store = make_store(tmp_path)
    sid = store.upsert_scheme(
        {
            "scheme_id": "synthetic_student_support",
            "name": "Synthetic Student Support",
            "category": "Education",
            "state_scope": "ALL",
            "min_age": "16",
            "max_age": "30",
            "allowed_genders": "ALL",
            "marital_statuses": "ALL",
            "residence": "ALL",
            "required_flags": "student",
            "occupation_keywords": "student education",
            "need_keywords": "scholarship tuition education",
            "documents": "Identity proof|Enrollment proof",
            "benefits": "Synthetic education support used only for automated tests.",
            "official_url": "https://www.myscheme.gov.in/",
            "application_url": "https://www.myscheme.gov.in/",
            "application_steps": "Check official rules|Gather documents|Apply officially",
            "official_source": "https://www.myscheme.gov.in/",
            "last_verified": "",
            "verification_note": "Synthetic test record.",
            "special_rule": "",
            "active": True,
        }
    )
    assert sid == "synthetic_student_support"
    engine = load_default_engine(tmp_path, catalog_df=store.scheme_dataframe(active_only=True))
    results = engine.recommend(UserProfile(age=20, student=True, need_text="scholarship education tuition"), top_k=20)
    match = next(item for item in results if item["scheme_id"] == sid)
    assert match["application_steps"][0] == "Check official rules"
    assert match["official_source"] == "https://www.myscheme.gov.in/"
