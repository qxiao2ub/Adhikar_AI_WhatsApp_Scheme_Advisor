# Architecture

```text
WhatsApp shared link / Web browser / Future SwiftUI client
                         |
                  Consent and locale
                         |
        Voice input -> ASR -> language/translation adapter
                         |
             Structured profile + stated need
                         |
       Approved scheme catalog + transparent rule engine
                         |
    Candidate set -> supervised relevance ranker -> display
                         |
  Local-language text/TTS + documents + official verification
                         |
  Optional aggregate helpful/not-helpful bandit (no identity)

New Streamlit session
        |
visitor_counter.py
        |
GitHub JSON file (recommended) OR local JSON fallback
        |
Visible cumulative count on every app area
```

## Production separation

- Web UI: Streamlit or a production frontend.
- Preserved UI source: `ui_source/adhikar/` contains the attached Lovable/TanStack design materials and is not required by Streamlit at runtime.
- API: FastAPI behind authentication, rate limits, monitoring, and a web-application firewall.
- WhatsApp webhook: separate public HTTPS service.
- Catalog pipeline: versioned ingest, validation, legal approval, provenance, and change monitoring.
- Language services: approved ASR/translation/TTS provider or audited self-hosted models.
- Visitor count: anonymous app-session count only; GitHub-backed JSON is the no-database durable option.
- Analytics: de-identified, consented, minimum necessary, with retention limits.
