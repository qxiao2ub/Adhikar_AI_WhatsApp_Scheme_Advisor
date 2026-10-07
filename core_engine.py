from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


MYScheme_HOME = "https://www.myscheme.gov.in/"


@dataclass
class UserProfile:
    age: Optional[int] = None
    annual_income: Optional[float] = None
    gender: str = "Prefer not to say"
    marital_status: str = "Prefer not to say"
    state: str = ""
    residence: str = "Prefer not to say"
    social_category: str = "Prefer not to say"
    student: bool = False
    pregnant: bool = False
    disability: bool = False
    entrepreneur: bool = False
    street_vendor: bool = False
    farmer: bool = False
    housing_need: bool = False
    bank_account: bool = False
    need_text: str = ""

    def safe_public_dict(self) -> Dict[str, Any]:
        """Return only fields needed for a single recommendation request."""
        return asdict(self)


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or str(value).strip() == ""


def _split(value: Any) -> List[str]:
    if _is_blank(value):
        return []
    return [part.strip() for part in re.split(r"[|,]", str(value)) if part.strip()]


def redact_sensitive_text(text: str) -> str:
    """Remove common identifiers before any optional analytics or diagnostics."""
    text = text or ""
    text = re.sub(r"\b\d{12}\b", "[REDACTED_AADHAAR_LIKE_NUMBER]", text)
    text = re.sub(r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b", "[REDACTED_PHONE]", text)
    text = re.sub(r"[\w.+'-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    return text.strip()


class BanditStore:
    """Aggregate, non-personalized beta-bandit feedback store.

    This prototype stores only counts per scheme. It does not store user profiles,
    voice recordings, phone numbers, or location history.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.state: Dict[str, Dict[str, int]] = {}
        self._load()

    def _load(self) -> None:
        try:
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self.state = {}

    def _save(self) -> None:
        try:
            self.path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except Exception:
            pass

    def mean_reward(self, scheme_id: str) -> float:
        item = self.state.get(scheme_id, {"positive": 0, "negative": 0})
        return (item.get("positive", 0) + 1.0) / (
            item.get("positive", 0) + item.get("negative", 0) + 2.0
        )

    def update(self, scheme_id: str, positive: bool) -> None:
        item = self.state.setdefault(scheme_id, {"positive": 0, "negative": 0})
        item["positive" if positive else "negative"] += 1
        self._save()


class SchemeRecommender:
    """Transparent pre-screening plus ML-assisted ranking.

    Government eligibility is never decided by ML in this prototype. Rules create
    a pre-screen status; ML and aggregate feedback only rank which potential matches
    are shown first.
    """

    def __init__(
        self,
        catalog_path: str | Path | None = None,
        bandit_path: str | Path | None = None,
        catalog_df: pd.DataFrame | None = None,
    ):
        if catalog_df is not None:
            self.catalog_path = Path(catalog_path) if catalog_path else Path("sample_schemes.csv")
            self.df = catalog_df.copy().fillna("")
        elif catalog_path is not None:
            self.catalog_path = Path(catalog_path)
            self.df = pd.read_csv(self.catalog_path).fillna("")
        else:
            raise ValueError("catalog_path or catalog_df is required")
        if self.df.empty:
            raise ValueError("Scheme catalog is empty")
        # Admin-managed catalogs may add fields over time. Keep ranking compatible.
        required_text_cols = ["name", "category", "occupation_keywords", "need_keywords", "benefits"]
        for col in required_text_cols:
            if col not in self.df.columns:
                self.df[col] = ""
        self.bandit = BanditStore(bandit_path or self.catalog_path.with_name("bandit_state.json"))
        self._fit_text_model()
        self._fit_demo_supervised_ranker()
        self._fit_need_clusterer()

    def _fit_text_model(self) -> None:
        text = (
            self.df["name"].astype(str) + " " + self.df["category"].astype(str) + " "
            + self.df["occupation_keywords"].astype(str) + " "
            + self.df["need_keywords"].astype(str) + " " + self.df["benefits"].astype(str)
        )
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.scheme_matrix = self.vectorizer.fit_transform(text)

    def _fit_demo_supervised_ranker(self) -> None:
        """Train a synthetic demonstration model.

        Replace this model with consented, audited, representative outcome data
        before any production use. The synthetic label mimics user-confirmed relevance,
        not government eligibility.
        """
        rng = np.random.default_rng(42)
        n = 1800
        rule_score = rng.uniform(0, 1, n)
        text_score = rng.beta(1.5, 4.0, n)
        missing_ratio = rng.uniform(0, 1, n)
        age_fit = rng.integers(0, 2, n)
        income_fit = rng.integers(0, 2, n)
        logits = 3.2 * rule_score + 2.1 * text_score + 0.5 * age_fit + 0.4 * income_fit - 1.3 * missing_ratio - 2.1
        p = 1 / (1 + np.exp(-logits))
        y = rng.binomial(1, p)
        X = np.column_stack([rule_score, text_score, missing_ratio, age_fit, income_fit])
        self.ml_ranker = RandomForestClassifier(
            n_estimators=100, max_depth=6, min_samples_leaf=8, random_state=42
        )
        self.ml_ranker.fit(X, y)

    def _fit_need_clusterer(self) -> None:
        persona_texts = [
            "student scholarship tuition books hostel education",
            "healthcare hospital pregnancy maternal child treatment",
            "business loan entrepreneur street vendor livelihood startup",
            "farmer crop agriculture rural income support",
            "pension old age senior citizen disability social welfare",
            "housing home shelter construction rent family",
            "skill training job apprenticeship employment youth",
        ]
        self.persona_names = [
            "Education and scholarships", "Health and family", "Enterprise and livelihood",
            "Agriculture", "Pension and social protection", "Housing", "Skills and employment"
        ]
        persona_matrix = self.vectorizer.transform(persona_texts)
        self.clusterer = KMeans(n_clusters=len(persona_texts), random_state=42, n_init=10)
        self.clusterer.fit(persona_matrix.toarray())
        labels = self.clusterer.labels_
        self.cluster_label_to_name = {int(label): name for label, name in zip(labels, self.persona_names)}

    def need_cluster(self, need_text: str) -> str:
        clean = redact_sensitive_text(need_text)
        if not clean:
            return "General discovery"
        vec = self.vectorizer.transform([clean]).toarray()
        label = int(self.clusterer.predict(vec)[0])
        return self.cluster_label_to_name.get(label, "General discovery")

    def _profile_flag(self, profile: UserProfile, name: str) -> Optional[bool]:
        return bool(getattr(profile, name, False)) if hasattr(profile, name) else None

    def _rule_assessment(self, profile: UserProfile, scheme: pd.Series) -> Dict[str, Any]:
        reasons: List[str] = []
        missing: List[str] = []
        failed: List[str] = []
        checks = 0
        passed = 0

        def check(condition: Optional[bool], pass_reason: str, fail_reason: str, missing_field: str = ""):
            nonlocal checks, passed
            checks += 1
            if condition is None:
                if missing_field:
                    missing.append(missing_field)
            elif condition:
                passed += 1
                reasons.append(pass_reason)
            else:
                failed.append(fail_reason)

        if not _is_blank(scheme.get("min_age")) or not _is_blank(scheme.get("max_age")):
            if profile.age is None:
                check(None, "", "", "age")
            else:
                min_age = int(float(scheme["min_age"])) if not _is_blank(scheme["min_age"]) else 0
                max_age = int(float(scheme["max_age"])) if not _is_blank(scheme["max_age"]) else 200
                check(min_age <= profile.age <= max_age,
                      f"Age {profile.age} is within the catalog pre-screen range.",
                      f"Age {profile.age} is outside the catalog pre-screen range {min_age}-{max_age}.")

        allowed_genders = _split(scheme.get("allowed_genders"))
        if allowed_genders and "ALL" not in [x.upper() for x in allowed_genders]:
            if profile.gender == "Prefer not to say":
                check(None, "", "", "gender")
            else:
                check(profile.gender.lower() in [x.lower() for x in allowed_genders],
                      "Gender matches this catalog condition.",
                      "Gender does not match this catalog condition.")

        if not _is_blank(scheme.get("max_income")):
            if profile.annual_income is None:
                check(None, "", "", "annual household income")
            else:
                max_income = float(scheme["max_income"])
                check(profile.annual_income <= max_income,
                      "Income is within this broad discovery threshold.",
                      "Income is above this broad discovery threshold; official rules may differ.")

        required_flags = _split(scheme.get("required_flags"))
        for flag in required_flags:
            val = self._profile_flag(profile, flag)
            check(val is True, f"Profile indicates {flag.replace('_', ' ')}.",
                  f"This catalog entry expects {flag.replace('_', ' ')}.")

        special = str(scheme.get("special_rule", "")).strip()
        if special == "standup":
            if profile.gender == "Prefer not to say" and profile.social_category == "Prefer not to say":
                check(None, "", "", "gender or eligible social category")
            else:
                cond = profile.gender == "Female" or profile.social_category in {"SC", "ST"}
                check(cond,
                      "Profile meets the broad women/SC/ST discovery condition.",
                      "This catalog pre-screen expects a woman entrepreneur or an SC/ST entrepreneur.")
        elif special == "apy":
            if not profile.bank_account:
                failed.append("This catalog pre-screen expects a savings bank or post-office savings account.")
            else:
                reasons.append("Profile indicates an eligible type of savings account may be available.")
        elif special == "jssk":
            # Government-facility admission is intentionally left for official confirmation.
            missing.append("confirmation from a government health institution")

        if failed:
            rule_score = 0.05
            status = "Unlikely based on supplied answers"
        elif missing:
            completion = passed / max(checks, 1)
            rule_score = 0.55 + 0.25 * completion
            status = "Needs official review"
        else:
            rule_score = 0.92 if checks else 0.72
            status = "Potential match"

        return {
            "rule_score": float(min(max(rule_score, 0), 1)),
            "status": status,
            "reasons": reasons,
            "missing": sorted(set(missing)),
            "failed": failed,
            "checks": checks,
            "passed": passed,
        }

    def recommend(self, profile: UserProfile, top_k: int = 6) -> List[Dict[str, Any]]:
        need_text = redact_sensitive_text(profile.need_text)
        query = " ".join([
            need_text,
            "student education scholarship" if profile.student else "",
            "pregnancy maternal healthcare" if profile.pregnant else "",
            "disability support" if profile.disability else "",
            "entrepreneur business loan" if profile.entrepreneur else "",
            "street vendor livelihood" if profile.street_vendor else "",
            "farmer agriculture" if profile.farmer else "",
            "housing shelter" if profile.housing_need else "",
        ]).strip() or "government benefit support"
        qvec = self.vectorizer.transform([query])
        text_scores = cosine_similarity(qvec, self.scheme_matrix).ravel()

        results: List[Dict[str, Any]] = []
        for idx, scheme in self.df.iterrows():
            rules = self._rule_assessment(profile, scheme)
            text_score = float(text_scores[idx])
            missing_ratio = len(rules["missing"]) / max(rules["checks"] + 1, 1)
            age_fit = 0 if any("Age" in x for x in rules["failed"]) else 1
            income_fit = 0 if any("Income" in x for x in rules["failed"]) else 1
            features = np.array([[rules["rule_score"], text_score, missing_ratio, age_fit, income_fit]])
            ml_probability = float(self.ml_ranker.predict_proba(features)[0, 1])
            feedback_score = self.bandit.mean_reward(str(scheme["scheme_id"]))

            if rules["failed"]:
                final_score = 0.12 * text_score + 0.03 * feedback_score + 0.05
            else:
                final_score = (
                    0.62 * rules["rule_score"] + 0.23 * text_score
                    + 0.10 * ml_probability + 0.05 * feedback_score
                )

            official_search_hint = f"Search this exact name on myScheme: {scheme['name']}"
            result = {
                "scheme_id": str(scheme["scheme_id"]),
                "name": str(scheme["name"]),
                "category": str(scheme["category"]),
                "status": rules["status"],
                "score": round(float(final_score), 4),
                "pre_screen_confidence": round(float(rules["rule_score"]), 3),
                "ml_relevance_probability": round(ml_probability, 3),
                "text_relevance": round(text_score, 3),
                "reasons": rules["reasons"],
                "missing": rules["missing"],
                "failed": rules["failed"],
                "documents": _split(scheme["documents"]),
                "benefits": str(scheme["benefits"]),
                "verification_note": str(scheme["verification_note"]),
                "official_url": str(scheme.get("official_url") or MYScheme_HOME),
                "application_url": str(scheme.get("application_url") or MYScheme_HOME),
                "application_steps": _split(scheme.get("application_steps", "")),
                "official_source": str(scheme.get("official_source") or scheme.get("official_url") or MYScheme_HOME),
                "last_verified": str(scheme.get("last_verified") or ""),
                "official_search_hint": official_search_hint,
                "share_text": quote_plus(
                    f"Potential scheme to verify: {scheme['name']}. Open official myScheme: {MYScheme_HOME}"
                ),
            }
            results.append(result)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[: max(1, int(top_k))]

    def record_feedback(self, scheme_id: str, helpful: bool) -> None:
        self.bandit.update(scheme_id, helpful)


def load_default_engine(
    project_dir: str | Path = ".",
    catalog_df: pd.DataFrame | None = None,
) -> SchemeRecommender:
    project_dir = Path(project_dir)
    return SchemeRecommender(
        project_dir / "sample_schemes.csv",
        project_dir / "bandit_state.json",
        catalog_df=catalog_df,
    )
