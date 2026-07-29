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
```

## Production separation

- Web UI: Streamlit or a production frontend.
- API: FastAPI behind authentication, rate limits, monitoring, and a web-application firewall.
- WhatsApp webhook: separate public HTTPS service.
- Catalog pipeline: versioned ingest, validation, legal approval, provenance, and change monitoring.
- Language services: approved ASR/translation/TTS provider or audited self-hosted models.
- Analytics: de-identified, consented, minimum necessary, with retention limits.
