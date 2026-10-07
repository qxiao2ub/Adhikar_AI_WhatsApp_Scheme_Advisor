# Adhikaar.ai

**Adhikaar.ai** is a multilingual government-scheme discovery and access prototype built with Python and Streamlit. It is designed to help a user move from **"What support might I qualify for?"** to **"What documents and steps do I need, where is the official application, and did I begin or complete the journey?"**

**Author / Project Lead:** Praneel Bembey  
**Mentor:** Dr. Qingyang Xiao

> Important: Adhikaar.ai provides educational pre-screening and navigation support. It does **not** make an official eligibility, entitlement, approval, payment, or legal decision. Always verify current rules with the responsible government department and official scheme source.

## What changed in this version

This repository implements the requested product evolution:

1. **Product rebrand** to `Adhikaar.ai` throughout the Streamlit app and deployment configuration.
2. **Backend + beneficiary-impact database** with explicit consent, privacy-minimized profiles, scheme matches, user-journey events, help tickets, and retention/deletion controls.
3. **Personalized proactive discovery**: users do not need to know a scheme name; they provide a few basic details and a need description.
4. **End-to-end access journey**: each result includes documents, application steps, official source, official application link, start-journey and self-reported-completion actions.
5. **Scheme-management admin panel** to add/edit/deactivate schemes, rules, documents, links, sources and `last_verified` date.
6. **Privacy and consent from the start**: session-processing consent, separate opt-in impact analytics, data minimization, retention cleanup, and user-triggered deletion.
7. **Impact dashboard**: users reached, consented profiles, scheme matches, potential beneficiaries, journeys initiated/completed, geography, language and need category.
8. **Accessibility**: multilingual text, voice input, text-to-speech, larger text, higher contrast, location alternatives and WhatsApp sharing.
9. **Human assistance escalation**: anonymous/redacted help tickets with an admin support queue and optional external assistance URL.

## Streamlit Cloud quick start

The repository is ready for Streamlit Community Cloud.

1. Create a GitHub repository and upload the **contents** of this folder to the repository root.
2. In Streamlit Community Cloud choose `streamlit_app.py` as the app entry point.
3. The app can launch with **no external database**; it will create a local SQLite database under `data/adhikaar.db`.
4. For durable production analytics on Streamlit Cloud, configure a managed PostgreSQL `DATABASE_URL` in Streamlit Secrets. Local Streamlit filesystem persistence is not guaranteed across restarts/redeployments.
5. Configure an admin password hash in Streamlit Secrets if you want to use the Admin panel.

Copy settings from `.streamlit/secrets.toml.example` into **App settings -> Secrets**. Never commit real secrets.

### Minimum production-style secrets

```toml
APP_NAME = "Adhikaar.ai"
APP_PUBLIC_URL = "https://your-app.streamlit.app/"
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require"
DATA_RETENTION_DAYS = "365"
ADMIN_PASSWORD_HASH = "<sha256-of-a-strong-password>"
```

Generate an admin password hash locally:

```bash
python -c "import hashlib,getpass; print(hashlib.sha256(getpass.getpass().encode()).hexdigest())"
```

## Backend architecture

`backend.py` uses SQLAlchemy and supports:

- **SQLite** for a zero-configuration demo/development launch.
- **PostgreSQL** through `DATABASE_URL` for durable deployments.

The backend creates these logical data domains:

- `beneficiaries`: privacy-minimized opt-in analytics profiles.
- `consents`: consent events and consent version.
- `scheme_matches`: matches shown to an opt-in beneficiary.
- `journey_events`: profile saved, matches generated, application started and self-reported completed.
- `help_requests`: redacted human-assistance tickets.
- `schemes`: admin-managed scheme catalog, eligibility metadata, documents, application links, official source and last-verified date.

### Data minimization

The impact database intentionally does **not** persist:

- names
- phone numbers
- email addresses
- Aadhaar numbers
- OTPs or passwords
- full street addresses
- raw voice recordings
- precise latitude/longitude
- free-form transcripts
- social-category selection
- pregnancy/disability status
- full medical records

Exact age and income used during a recommendation session are converted to bands before analytics storage. Sensitive fields needed for a scheme pre-screen are used transiently in the session and are not intentionally stored in the beneficiary-impact database.

## Personalized discovery

`core_engine.py` combines:

- transparent rule-based pre-screening
- TF-IDF semantic relevance
- a demonstration supervised ML ranker trained on synthetic relevance labels
- need clustering for organization only
- aggregate thumbs-up/down beta-bandit feedback

ML is allowed to **rank** likely useful results. It is not allowed to silently override official eligibility rules.

The active scheme catalog is loaded from the backend database so changes made in the Admin panel become part of discovery without editing source code.

## End-to-end scheme access

A result can show:

- potential-match status and why it appeared
- information still needing official confirmation
- commonly requested documents
- application steps
- official scheme-information source
- official application link
- catalog verification note and last-verified date
- WhatsApp share link
- start-application action
- self-reported completion action
- local-language summary and audio output

Application journey metrics are persisted only when the user has opted into impact analytics.

## Scheme administration

The **Admin** tab is disabled until an admin secret is configured.

An authenticated admin can:

- add a new scheme
- edit existing eligibility metadata
- update benefits and keywords
- update document requirements
- update application steps
- update official information/application URLs
- set an official source
- record a last-verified date
- activate/deactivate a scheme
- export the current catalog to CSV
- review redacted human-help tickets and change their status
- inspect aggregate database metrics
- run retention cleanup

This prototype uses a single shared admin secret. A real production deployment should replace this with organization SSO/MFA, role-based access control, audit logging, rate limits, secrets management and security monitoring.

## Privacy center

The **Human help & privacy** tab includes:

- impact-analytics status
- retention-window disclosure
- a user-readable summary of the stored privacy-minimized record for the current pseudonymous browser-session ID
- a delete-my-stored-analytics control
- human-help ticket consent

Retention cleanup removes expired beneficiary records and related journey/match/consent/help rows according to `DATA_RETENTION_DAYS`.

## Impact dashboard

The dashboard reports product-impact indicators rather than official government outcomes:

- cumulative app users
- consented analytics profiles
- scheme matches generated
- potential beneficiaries identified
- application journeys initiated
- self-reported application completions
- State/UT distribution
- language distribution
- need-category distribution

Small geography/language groups are suppressed until a minimum of 3 consented profiles are present.

A self-reported completion is **not** equivalent to a verified government approval or benefit received. A future authorized integration would be required to measure that outcome reliably.

## Human assistance

Users can create redacted, consented help tickets when the AI does not resolve a question. The Admin panel contains a basic support queue. You can also configure:

```toml
HUMAN_ASSISTANCE_URL = "https://your-approved-help-service.example/"
```

Do not use the help-ticket form for direct identifiers or highly sensitive records.

## Accessibility and language

The Streamlit interface includes:

- English and major Indian-language options
- voice input
- text-to-speech
- larger-text mode
- higher-contrast mode
- manual city/district/State/PIN entry when browser geolocation is not appropriate
- WhatsApp share links

The repository includes adapters/placeholders for authorized production language services. The built-in translation/voice fallbacks are prototypes and should be replaced with reviewed services before public deployment.

## WhatsApp and mobile

- `whatsapp_webhook.py`: FastAPI scaffold for a future WhatsApp Cloud API bot.
- `mobile_api.py`: FastAPI recommendation scaffold for a future native mobile client.

Deploy webhooks/APIs on an appropriate public HTTPS backend with authentication, rate limiting, monitoring and secret storage. Streamlit Community Cloud is intended for the web UI, not as the recommended WhatsApp webhook host.

## Visitor counter

`visitor_counter.py` preserves the prior cumulative, non-identifying app-user counter. It can use:

- a local JSON file, or
- an optional GitHub-backed JSON file configured through secrets for improved persistence without putting beneficiary data in GitHub.

**Do not store beneficiary records in the GitHub counter file.** The beneficiary backend and the visitor counter are intentionally separate.

## Repository structure

```text
streamlit_app.py          Citizen UI + impact/admin/help flows
backend.py                SQL backend, consent, journeys, schemes, metrics
core_engine.py            Rule + ML recommendation engine
visitor_counter.py        Non-identifying cumulative app-user counter
sample_schemes.csv        Initial seed catalog
whatsapp_webhook.py       WhatsApp Cloud API scaffold
mobile_api.py             Future mobile API scaffold
PRIVACY.md                Privacy design and production checklist
ARCHITECTURE.md           System architecture
DATABASE_SETUP.md         PostgreSQL / Streamlit Cloud backend setup
ADMIN_GUIDE.md            Admin and scheme-management guidance
IMPACT_METRICS.md         Metric definitions and limitations
ui_source/adhikar/        Preserved attached Lovable UI source materials
assets/                   Runtime visual assets
```

## Local run

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Tests

```bash
pytest -q
```

The test suite covers recommendation behavior, redaction, visitor counting and the new database functions including consented profile storage, journey analytics, deletion, scheme administration and impact metrics.

## Production-readiness boundary

This repository is a functional prototype, not a complete production benefits platform. Before real beneficiaries rely on it, add at minimum: official/authorized scheme data ingestion, professional legal/privacy review, formal threat modeling, security testing, organization-grade authentication, authorization and audit logs, reliable managed persistence/backups, incident response, deletion/grievance operations, accessibility testing, language-quality testing, model/bias evaluation and a verified human-support process.
