# Adhikaar.ai architecture

```text
Citizen: web / WhatsApp link / future mobile client
                    |
       Session-processing consent
                    |
        text or voice + language
                    |
  transient profile + stated need in session
                    |
             core_engine.py
        / rules + relevance ML \
       /                       \
admin-managed catalog       need clustering
       |                       |
       +------ potential scheme matches ------+
                    |
  documents + application steps + official links
                    |
      start / self-report completion
                    |
      optional impact-analytics consent
                    |
                 backend.py
       SQLite demo OR PostgreSQL production
                    |
  beneficiaries / consents / matches / journey events
  help tickets / scheme catalog / aggregate metrics
                    |
       impact dashboard + admin operations
```

## Runtime components

### Streamlit citizen experience

`streamlit_app.py` provides personalized discovery, accessibility controls, nearby help, impact metrics, privacy controls, human assistance and the admin interface.

### Recommendation engine

`core_engine.py` separates transparent pre-screen rules from ML ranking. ML ranking does not create official eligibility.

### Backend

`backend.py` uses SQLAlchemy. SQLite provides a no-configuration launch path; a managed PostgreSQL `DATABASE_URL` is recommended for durable Streamlit Cloud persistence.

### Scheme catalog

The backend `schemes` table is the runtime source of truth. The bundled CSV is used only to seed an empty database. Admin updates can change eligibility metadata, documents, application steps, sources, last-verified date and active/inactive status.

### Privacy-minimized analytics

Opt-in analytics store coarse information only. Direct identifiers, raw audio, precise coordinates and free-form transcripts are excluded from the impact database by design.

### Visitor counter

The legacy cumulative app-user counter remains independent from beneficiary analytics. A GitHub-backed JSON option may be used for the non-identifying count only.

### Human assistance

A help-ticket queue stores redacted issue descriptions after separate consent. Production should route these tickets to an authenticated case-management/helpdesk system.

## Production separation recommended

- **Web UI:** Streamlit prototype or a hardened production frontend.
- **API/backend:** private FastAPI/service layer behind authentication, authorization, rate limiting and monitoring.
- **Database:** managed PostgreSQL with TLS, backups, encryption at rest and restricted network/access policy.
- **WhatsApp webhook:** separate public HTTPS service with signature/token validation and short-lived state.
- **Admin:** organization SSO/MFA + role-based authorization, not a shared password.
- **Scheme ingest:** authorized official data feed, provenance, validation, versioning and review workflow.
- **Language services:** approved ASR/translation/TTS or audited self-hosted models.
- **Human support:** authenticated helpdesk with defined service levels and grievance/escalation process.
