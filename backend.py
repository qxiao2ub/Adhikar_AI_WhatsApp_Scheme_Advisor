from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    and_,
    create_engine,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine

from core_engine import UserProfile, redact_sensitive_text


CONSENT_VERSION = "2026-10-07-v1"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def age_band(age: Optional[int]) -> str:
    if age is None:
        return "Unknown"
    if age < 18:
        return "Under 18"
    if age < 25:
        return "18-24"
    if age < 35:
        return "25-34"
    if age < 45:
        return "35-44"
    if age < 55:
        return "45-54"
    if age < 65:
        return "55-64"
    return "65+"


def income_band(value: Optional[float]) -> str:
    if value is None:
        return "Unknown"
    if value < 100_000:
        return "<₹1L"
    if value < 300_000:
        return "₹1L-₹3L"
    if value < 500_000:
        return "₹3L-₹5L"
    if value < 1_000_000:
        return "₹5L-₹10L"
    return "₹10L+"


def sanitize_state(value: str) -> str:
    # Coarse geography only. This deliberately rejects long free-form addresses.
    value = " ".join((value or "").strip().split())
    if len(value) > 80:
        value = value[:80]
    return redact_sensitive_text(value)


class BackendStore:
    """Privacy-first backend for Adhikaar.ai.

    The default zero-config backend is SQLite so the repository launches on
    Streamlit Community Cloud without any external service. For durable production
    persistence, set DATABASE_URL to a managed PostgreSQL database in Streamlit
    Secrets. The schema intentionally avoids direct identifiers such as name,
    phone, Aadhaar, email, exact address, raw audio, and precise coordinates.
    """

    def __init__(
        self,
        project_dir: str | Path,
        database_url: str = "",
        retention_days: int = 365,
    ) -> None:
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        (self.project_dir / "data").mkdir(parents=True, exist_ok=True)
        self.database_url = self._normalize_url(database_url)
        self.retention_days = max(1, int(retention_days))
        self.engine = self._make_engine(self.database_url)
        self.metadata = MetaData()
        self._define_tables()
        self.metadata.create_all(self.engine)
        self.seed_schemes_from_csv(self.project_dir / "sample_schemes.csv")

    def _normalize_url(self, database_url: str) -> str:
        database_url = (database_url or os.getenv("DATABASE_URL", "")).strip()
        if not database_url:
            return f"sqlite:///{(self.project_dir / 'data' / 'adhikaar.db').as_posix()}"
        if database_url.startswith("postgres://"):
            return "postgresql+psycopg://" + database_url[len("postgres://"):]
        if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
            return "postgresql+psycopg://" + database_url[len("postgresql://"):]
        return database_url

    @staticmethod
    def _make_engine(url: str) -> Engine:
        kwargs: Dict[str, Any] = {"pool_pre_ping": True, "future": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        return create_engine(url, **kwargs)

    def _define_tables(self) -> None:
        m = self.metadata
        self.beneficiaries = Table(
            "beneficiaries",
            m,
            Column("beneficiary_id", String(64), primary_key=True),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("updated_at", DateTime(timezone=True), nullable=False),
            Column("analytics_consent", Boolean, nullable=False, default=False),
            Column("consent_version", String(64), nullable=False),
            Column("language", String(32), nullable=False, default="en"),
            Column("state", String(80), nullable=False, default=""),
            Column("residence", String(32), nullable=False, default="Prefer not to say"),
            Column("age_band", String(32), nullable=False, default="Unknown"),
            Column("income_band", String(32), nullable=False, default="Unknown"),
            Column("gender", String(32), nullable=False, default="Prefer not to say"),
            Column("marital_status", String(32), nullable=False, default="Prefer not to say"),
            Column("need_category", String(120), nullable=False, default="General discovery"),
            Column("profile_flags_json", Text, nullable=False, default="{}"),
        )
        self.consents = Table(
            "consents",
            m,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("beneficiary_id", String(64), nullable=False, index=True),
            Column("consent_type", String(64), nullable=False),
            Column("consent_version", String(64), nullable=False),
            Column("granted", Boolean, nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        self.journey_events = Table(
            "journey_events",
            m,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("beneficiary_id", String(64), nullable=True, index=True),
            Column("event_type", String(64), nullable=False, index=True),
            Column("scheme_id", String(120), nullable=True, index=True),
            Column("scheme_name", String(250), nullable=True),
            Column("language", String(32), nullable=True),
            Column("state", String(80), nullable=True),
            Column("metadata_json", Text, nullable=False, default="{}"),
            Column("created_at", DateTime(timezone=True), nullable=False, index=True),
        )
        self.scheme_matches = Table(
            "scheme_matches",
            m,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("beneficiary_id", String(64), nullable=False, index=True),
            Column("scheme_id", String(120), nullable=False, index=True),
            Column("scheme_name", String(250), nullable=False),
            Column("status", String(100), nullable=False),
            Column("score", Float, nullable=False, default=0.0),
            Column("matched_at", DateTime(timezone=True), nullable=False, index=True),
        )
        self.help_requests = Table(
            "help_requests",
            m,
            Column("ticket_id", String(40), primary_key=True),
            Column("beneficiary_id", String(64), nullable=True, index=True),
            Column("scheme_id", String(120), nullable=True),
            Column("topic", String(120), nullable=False),
            Column("description_redacted", Text, nullable=False),
            Column("language", String(32), nullable=True),
            Column("status", String(32), nullable=False, default="Open"),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("updated_at", DateTime(timezone=True), nullable=False),
        )
        self.schemes = Table(
            "schemes",
            m,
            Column("scheme_id", String(120), primary_key=True),
            Column("name", String(250), nullable=False),
            Column("category", String(120), nullable=False, default="General"),
            Column("state_scope", String(120), nullable=False, default="ALL"),
            Column("min_age", Float, nullable=True),
            Column("max_age", Float, nullable=True),
            Column("allowed_genders", String(250), nullable=False, default="ALL"),
            Column("max_income", Float, nullable=True),
            Column("marital_statuses", String(250), nullable=False, default="ALL"),
            Column("residence", String(120), nullable=False, default="ALL"),
            Column("required_flags", Text, nullable=False, default=""),
            Column("occupation_keywords", Text, nullable=False, default=""),
            Column("need_keywords", Text, nullable=False, default=""),
            Column("documents", Text, nullable=False, default=""),
            Column("benefits", Text, nullable=False, default=""),
            Column("official_url", Text, nullable=False, default="https://www.myscheme.gov.in/"),
            Column("application_url", Text, nullable=False, default="https://www.myscheme.gov.in/"),
            Column("application_steps", Text, nullable=False, default=""),
            Column("official_source", Text, nullable=False, default="https://www.myscheme.gov.in/"),
            Column("last_verified", String(32), nullable=False, default=""),
            Column("verification_note", Text, nullable=False, default=""),
            Column("special_rule", String(120), nullable=False, default=""),
            Column("active", Boolean, nullable=False, default=True),
            Column("admin_notes", Text, nullable=False, default=""),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("updated_at", DateTime(timezone=True), nullable=False),
        )

    def database_label(self) -> str:
        return "PostgreSQL" if self.database_url.startswith("postgres") else "SQLite (demo/local persistence)"

    def seed_schemes_from_csv(self, csv_path: Path) -> None:
        if not csv_path.exists():
            return
        with self.engine.begin() as conn:
            count = conn.execute(select(func.count()).select_from(self.schemes)).scalar_one()
            if count:
                return
        df = pd.read_csv(csv_path).fillna("")
        now = utcnow()
        rows: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            steps = row.get("application_steps", "")
            if not str(steps).strip():
                steps = (
                    "Review the current official eligibility rules|"
                    "Gather the required documents listed by the responsible authority|"
                    "Open the official application portal or visit the designated office|"
                    "Submit the application and save any acknowledgement/reference number|"
                    "Follow up with the responsible authority for status updates"
                )
            rows.append(
                {
                    "scheme_id": str(row.get("scheme_id", "")).strip(),
                    "name": str(row.get("name", "")).strip(),
                    "category": str(row.get("category", "General")),
                    "state_scope": str(row.get("state_scope", "ALL")),
                    "min_age": self._to_float(row.get("min_age")),
                    "max_age": self._to_float(row.get("max_age")),
                    "allowed_genders": str(row.get("allowed_genders", "ALL")),
                    "max_income": self._to_float(row.get("max_income")),
                    "marital_statuses": str(row.get("marital_statuses", "ALL")),
                    "residence": str(row.get("residence", "ALL")),
                    "required_flags": str(row.get("required_flags", "")),
                    "occupation_keywords": str(row.get("occupation_keywords", "")),
                    "need_keywords": str(row.get("need_keywords", "")),
                    "documents": str(row.get("documents", "")),
                    "benefits": str(row.get("benefits", "")),
                    "official_url": str(row.get("official_url", "https://www.myscheme.gov.in/")),
                    "application_url": str(row.get("application_url", "https://www.myscheme.gov.in/")),
                    "application_steps": str(steps),
                    "official_source": str(row.get("official_source", row.get("official_url", "https://www.myscheme.gov.in/"))),
                    "last_verified": str(row.get("last_verified", "")),
                    "verification_note": str(row.get("verification_note", "")),
                    "special_rule": str(row.get("special_rule", "")),
                    "active": True,
                    "admin_notes": "Seeded from sample_schemes.csv; verify against the official source before production use.",
                    "created_at": now,
                    "updated_at": now,
                }
            )
        rows = [r for r in rows if r["scheme_id"] and r["name"]]
        if rows:
            with self.engine.begin() as conn:
                conn.execute(insert(self.schemes), rows)

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        try:
            if value is None or value == "" or pd.isna(value):
                return None
            return float(value)
        except Exception:
            return None

    def scheme_dataframe(self, active_only: bool = True) -> pd.DataFrame:
        stmt = select(self.schemes)
        if active_only:
            stmt = stmt.where(self.schemes.c.active.is_(True))
        with self.engine.begin() as conn:
            rows = [dict(r._mapping) for r in conn.execute(stmt).fetchall()]
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        # Datetime/admin fields are not used by the recommendation engine.
        keep = [
            "scheme_id", "name", "category", "state_scope", "min_age", "max_age",
            "allowed_genders", "max_income", "marital_statuses", "residence",
            "required_flags", "occupation_keywords", "need_keywords", "documents",
            "benefits", "official_url", "application_url", "application_steps",
            "official_source", "last_verified", "verification_note", "special_rule",
        ]
        return df[[c for c in keep if c in df.columns]].fillna("")

    def scheme_revision(self) -> str:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(func.count(self.schemes.c.scheme_id), func.max(self.schemes.c.updated_at))
            ).one()
        return f"{row[0]}:{row[1]}"

    def list_schemes(self, include_inactive: bool = True) -> List[Dict[str, Any]]:
        stmt = select(self.schemes).order_by(self.schemes.c.name.asc())
        if not include_inactive:
            stmt = stmt.where(self.schemes.c.active.is_(True))
        with self.engine.begin() as conn:
            return [dict(r._mapping) for r in conn.execute(stmt).fetchall()]

    def get_scheme(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        with self.engine.begin() as conn:
            row = conn.execute(select(self.schemes).where(self.schemes.c.scheme_id == scheme_id)).first()
        return dict(row._mapping) if row else None

    def upsert_scheme(self, values: Dict[str, Any]) -> str:
        sid = str(values.get("scheme_id", "")).strip()
        if not sid:
            sid = str(uuid.uuid4())
        now = utcnow()
        allowed = {c.name for c in self.schemes.columns}
        payload = {k: v for k, v in values.items() if k in allowed}
        payload["scheme_id"] = sid
        payload["updated_at"] = now
        payload.setdefault("created_at", now)
        for key in ("min_age", "max_age", "max_income"):
            payload[key] = self._to_float(payload.get(key))
        payload["active"] = bool(payload.get("active", True))
        with self.engine.begin() as conn:
            exists = conn.execute(select(self.schemes.c.scheme_id).where(self.schemes.c.scheme_id == sid)).first()
            if exists:
                payload.pop("created_at", None)
                conn.execute(update(self.schemes).where(self.schemes.c.scheme_id == sid).values(**payload))
            else:
                conn.execute(insert(self.schemes).values(**payload))
        return sid

    def deactivate_scheme(self, scheme_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                update(self.schemes)
                .where(self.schemes.c.scheme_id == scheme_id)
                .values(active=False, updated_at=utcnow())
            )

    def record_consent(self, beneficiary_id: str, consent_type: str, granted: bool) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.consents).values(
                    beneficiary_id=beneficiary_id,
                    consent_type=consent_type,
                    consent_version=CONSENT_VERSION,
                    granted=bool(granted),
                    created_at=utcnow(),
                )
            )

    def upsert_beneficiary(
        self,
        beneficiary_id: str,
        profile: UserProfile,
        language: str,
        need_category: str,
        analytics_consent: bool,
    ) -> None:
        if not analytics_consent:
            return
        flags = {
            k: bool(v)
            for k, v in profile.safe_public_dict().items()
            if k in {
                "student", "entrepreneur", "street_vendor", "farmer",
                "housing_need", "bank_account",
            }
        }
        now = utcnow()
        payload = {
            "beneficiary_id": beneficiary_id,
            "updated_at": now,
            "analytics_consent": True,
            "consent_version": CONSENT_VERSION,
            "language": (language or "en")[:32],
            "state": sanitize_state(profile.state),
            "residence": str(profile.residence)[:32],
            "age_band": age_band(profile.age),
            "income_band": income_band(profile.annual_income),
            # Sensitive demographic details can be used transiently for matching but
            # are deliberately not persisted in the impact database.
            "gender": "Not stored",
            "marital_status": "Not stored",
            "need_category": str(need_category or "General discovery")[:120],
            "profile_flags_json": json.dumps(flags, sort_keys=True),
        }
        with self.engine.begin() as conn:
            exists = conn.execute(
                select(self.beneficiaries.c.beneficiary_id)
                .where(self.beneficiaries.c.beneficiary_id == beneficiary_id)
            ).first()
            if exists:
                conn.execute(
                    update(self.beneficiaries)
                    .where(self.beneficiaries.c.beneficiary_id == beneficiary_id)
                    .values(**payload)
                )
            else:
                conn.execute(insert(self.beneficiaries).values(created_at=now, **payload))

    def record_matches(self, beneficiary_id: str, results: Iterable[Dict[str, Any]]) -> None:
        now = utcnow()
        rows = []
        for item in results:
            rows.append(
                {
                    "beneficiary_id": beneficiary_id,
                    "scheme_id": str(item.get("scheme_id", "")),
                    "scheme_name": str(item.get("name", ""))[:250],
                    "status": str(item.get("status", ""))[:100],
                    "score": float(item.get("score", 0.0) or 0.0),
                    "matched_at": now,
                }
            )
        if rows:
            with self.engine.begin() as conn:
                conn.execute(insert(self.scheme_matches), rows)

    def record_event(
        self,
        event_type: str,
        beneficiary_id: Optional[str] = None,
        scheme_id: Optional[str] = None,
        scheme_name: Optional[str] = None,
        language: Optional[str] = None,
        state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        safe_meta = metadata or {}
        # Never persist free-form raw user text through this generic event channel.
        safe_meta = {
            str(k)[:80]: (str(v)[:500] if not isinstance(v, (int, float, bool, type(None))) else v)
            for k, v in safe_meta.items()
            if str(k) not in {"raw_text", "transcript", "name", "phone", "email", "address", "aadhaar"}
        }
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.journey_events).values(
                    beneficiary_id=beneficiary_id,
                    event_type=str(event_type)[:64],
                    scheme_id=(str(scheme_id)[:120] if scheme_id else None),
                    scheme_name=(str(scheme_name)[:250] if scheme_name else None),
                    language=(str(language)[:32] if language else None),
                    state=(sanitize_state(state or "") if state else None),
                    metadata_json=json.dumps(safe_meta, ensure_ascii=False),
                    created_at=utcnow(),
                )
            )

    def create_help_request(
        self,
        beneficiary_id: Optional[str],
        topic: str,
        description: str,
        language: str,
        scheme_id: str = "",
    ) -> str:
        ticket_id = "HELP-" + uuid.uuid4().hex[:10].upper()
        safe_description = redact_sensitive_text(description)[:2000]
        now = utcnow()
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.help_requests).values(
                    ticket_id=ticket_id,
                    beneficiary_id=beneficiary_id,
                    scheme_id=(scheme_id or None),
                    topic=(topic or "General help")[:120],
                    description_redacted=safe_description,
                    language=(language or "en")[:32],
                    status="Open",
                    created_at=now,
                    updated_at=now,
                )
            )
        return ticket_id

    def list_help_requests(self, limit: int = 200) -> List[Dict[str, Any]]:
        stmt = select(self.help_requests).order_by(self.help_requests.c.created_at.desc()).limit(max(1, int(limit)))
        with self.engine.begin() as conn:
            return [dict(r._mapping) for r in conn.execute(stmt).fetchall()]

    def update_help_status(self, ticket_id: str, status: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                update(self.help_requests)
                .where(self.help_requests.c.ticket_id == ticket_id)
                .values(status=status[:32], updated_at=utcnow())
            )

    def beneficiary_summary(self, beneficiary_id: str) -> Dict[str, Any]:
        with self.engine.begin() as conn:
            beneficiary = conn.execute(
                select(self.beneficiaries).where(self.beneficiaries.c.beneficiary_id == beneficiary_id)
            ).first()
            events = conn.execute(
                select(func.count()).select_from(self.journey_events)
                .where(self.journey_events.c.beneficiary_id == beneficiary_id)
            ).scalar_one()
            matches = conn.execute(
                select(func.count()).select_from(self.scheme_matches)
                .where(self.scheme_matches.c.beneficiary_id == beneficiary_id)
            ).scalar_one()
            tickets = conn.execute(
                select(func.count()).select_from(self.help_requests)
                .where(self.help_requests.c.beneficiary_id == beneficiary_id)
            ).scalar_one()
        return {
            "profile": dict(beneficiary._mapping) if beneficiary else None,
            "journey_events": int(events or 0),
            "scheme_matches": int(matches or 0),
            "help_requests": int(tickets or 0),
        }

    def delete_beneficiary_data(self, beneficiary_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(self.scheme_matches).where(self.scheme_matches.c.beneficiary_id == beneficiary_id))
            conn.execute(delete(self.journey_events).where(self.journey_events.c.beneficiary_id == beneficiary_id))
            conn.execute(delete(self.help_requests).where(self.help_requests.c.beneficiary_id == beneficiary_id))
            conn.execute(delete(self.consents).where(self.consents.c.beneficiary_id == beneficiary_id))
            conn.execute(delete(self.beneficiaries).where(self.beneficiaries.c.beneficiary_id == beneficiary_id))

    def purge_expired_data(self) -> Dict[str, int]:
        cutoff = utcnow() - timedelta(days=self.retention_days)
        deleted_counts: Dict[str, int] = {}
        with self.engine.begin() as conn:
            # First identify expired beneficiary IDs so dependent rows are removed too.
            expired_ids = [
                r[0]
                for r in conn.execute(
                    select(self.beneficiaries.c.beneficiary_id)
                    .where(self.beneficiaries.c.updated_at < cutoff)
                ).fetchall()
            ]
            if expired_ids:
                for table, name in [
                    (self.scheme_matches, "scheme_matches"),
                    (self.journey_events, "journey_events"),
                    (self.help_requests, "help_requests"),
                    (self.consents, "consents"),
                ]:
                    result = conn.execute(delete(table).where(table.c.beneficiary_id.in_(expired_ids)))
                    deleted_counts[name] = int(result.rowcount or 0)
                result = conn.execute(delete(self.beneficiaries).where(self.beneficiaries.c.beneficiary_id.in_(expired_ids)))
                deleted_counts["beneficiaries"] = int(result.rowcount or 0)
        return deleted_counts

    def impact_metrics(self) -> Dict[str, Any]:
        with self.engine.begin() as conn:
            beneficiaries = conn.execute(select(func.count()).select_from(self.beneficiaries)).scalar_one()
            matches = conn.execute(select(func.count()).select_from(self.scheme_matches)).scalar_one()
            potential_beneficiaries = conn.execute(
                select(func.count(func.distinct(self.scheme_matches.c.beneficiary_id)))
                .where(self.scheme_matches.c.status.in_(["Potential match", "Needs official review"]))
            ).scalar_one()
            initiated = conn.execute(
                select(func.count(func.distinct(self.journey_events.c.beneficiary_id)))
                .where(self.journey_events.c.event_type == "application_started")
            ).scalar_one()
            completed = conn.execute(
                select(func.count(func.distinct(self.journey_events.c.beneficiary_id)))
                .where(self.journey_events.c.event_type == "application_completed")
            ).scalar_one()
            help_open = conn.execute(
                select(func.count()).select_from(self.help_requests)
                .where(self.help_requests.c.status == "Open")
            ).scalar_one()
        return {
            "consented_profiles": int(beneficiaries or 0),
            "scheme_matches": int(matches or 0),
            "potential_beneficiaries": int(potential_beneficiaries or 0),
            "application_journeys_started": int(initiated or 0),
            "application_journeys_completed": int(completed or 0),
            "open_help_requests": int(help_open or 0),
        }

    def aggregate_breakdown(self, field: str, minimum_group_size: int = 3) -> pd.DataFrame:
        allowed = {
            "state": self.beneficiaries.c.state,
            "language": self.beneficiaries.c.language,
            "need_category": self.beneficiaries.c.need_category,
            "age_band": self.beneficiaries.c.age_band,
        }
        col = allowed.get(field)
        if col is None:
            return pd.DataFrame(columns=[field, "count"])
        stmt = (
            select(col.label(field), func.count().label("count"))
            .select_from(self.beneficiaries)
            .group_by(col)
            .order_by(func.count().desc())
        )
        with self.engine.begin() as conn:
            rows = [dict(r._mapping) for r in conn.execute(stmt).fetchall()]
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=[field, "count"])
        df[field] = df[field].replace("", "Not provided")
        return df[df["count"] >= max(1, int(minimum_group_size))].reset_index(drop=True)

    def journey_funnel(self) -> pd.DataFrame:
        event_types = [
            "profile_saved",
            "scheme_matches_generated",
            "application_started",
            "application_completed",
        ]
        rows = []
        with self.engine.begin() as conn:
            for event_type in event_types:
                count = conn.execute(
                    select(func.count(func.distinct(self.journey_events.c.beneficiary_id)))
                    .where(self.journey_events.c.event_type == event_type)
                ).scalar_one()
                rows.append({"stage": event_type.replace("_", " ").title(), "users": int(count or 0)})
        return pd.DataFrame(rows)

    def export_schemes_csv(self) -> bytes:
        rows = self.list_schemes(include_inactive=True)
        if not rows:
            return b""
        df = pd.DataFrame(rows)
        for col in ("created_at", "updated_at"):
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df.to_csv(index=False).encode("utf-8")
