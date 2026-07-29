# Sahayak AI Scheme Advisor

**Author / Project Lead:** Praneel Bembey  
**Mentor:** Dr. Qingyang Xiao

A Colab-generated, GitHub-ready prototype for multilingual government-scheme discovery through a Streamlit web app, shareable WhatsApp link, optional WhatsApp Cloud API webhook, and a mobile API scaffold for a future iOS client.

## What the prototype does

- Accepts demographic and need information with explicit consent.
- Accepts typed local-language text and a short WAV/browser voice recording.
- Uses a transparent rule engine for eligibility **pre-screening**.
- Uses supervised ML only to rank potentially relevant results.
- Groups stated needs into broad topics for navigation; clustering does not determine eligibility.
- Uses aggregate thumbs-up/down feedback as a reinforcement-learning demonstration.
- Shows commonly requested documents and links to the official myScheme portal for verification.
- Requests browser location permission or accepts a city/district/PIN code, then searches open map data for nearby public/community services.
- Generates text and optional voice summaries.

## Important limitation

This app does **not** make an official eligibility decision. The included catalog is an educational sample and deliberately simplifies many rules. Users must verify every result on the official myScheme portal or with the responsible ministry, department, bank, hospital, or local authority.

As of the project build date (2026-07-13), no documented public citizen API for arbitrary third-party myScheme eligibility integration was identified in the official public materials reviewed. Do not scrape or reverse-engineer private endpoints. Obtain written authorization or an approved data feed/API before production integration.

Official portal: https://www.myscheme.gov.in/

## Project files

- `streamlit_app.py` — web UI, voice/text workflow, local-language UI, location search, feedback.
- `core_engine.py` — transparent pre-screen rules, TF-IDF retrieval, synthetic supervised ranker, need clustering, aggregate bandit.
- `sample_schemes.csv` — illustrative discovery catalog.
- `whatsapp_webhook.py` — direct WhatsApp Cloud API text-conversation scaffold for a separate HTTPS backend.
- `mobile_api.py` — FastAPI contract for a future SwiftUI/iOS client.
- `PRIVACY.md` — prototype privacy and data-minimization requirements.
- `COPYRIGHT_CHECKLIST.md` — source-code copyright preparation checklist.
- `tests/test_core.py` — smoke tests.

## Run locally or in Colab

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The generated Colab notebook includes a cell that launches Streamlit through the Colab proxy and a final cell that creates a GitHub-ready ZIP.

## Deploy on Streamlit Community Cloud

1. Upload all generated project files to the root of a GitHub repository.
2. Sign in to Streamlit Community Cloud and create an app from that repository.
3. Select `streamlit_app.py` as the entry point.
4. Add secrets in Streamlit settings instead of committing tokens.
5. Set `APP_PUBLIC_URL` to the deployed Streamlit URL.
6. Optionally set `APP_AUTHOR` and `APP_MENTOR`; the repository defaults are `Praneel Bembey` and `Dr. Qingyang Xiao`.
7. Reboot the app after changing dependencies or secrets.

Streamlit Community Cloud reads the GitHub repository as the source of the deployed app. Keep `requirements.txt` in the repository root.

## WhatsApp deployment paths

### Fast path: shared link

Use the sidebar button to share the Streamlit URL in WhatsApp. The user taps the link and opens the web app. This requires no WhatsApp bot approval.

### Direct chatbot path

Deploy `whatsapp_webhook.py` on a public HTTPS backend. Configure the WhatsApp Cloud API app, webhook verification token, access token, phone-number ID, message templates, privacy policy, and production-grade session storage. Streamlit Community Cloud should not be used as the webhook service.

The included webhook handles text and a minimal consent-first conversation. Voice-note processing is intentionally not enabled until an authorized media-download and ASR adapter is configured.

## Language services

The demo can use browser/WAV speech recognition and an optional third-party translation fallback. Those services may transmit data outside your application. Production should use an approved BHASHINI or other authorized Indian-language service with a documented contract, consent notice, regional/data-residency review, security controls, and deletion process.

## Responsible ML plan

- **ASR / translation / TTS:** pretrained deep-learning models or approved APIs.
- **Rules:** authoritative pre-screen logic from a versioned, reviewed scheme catalog.
- **Supervised ranking:** trained only on consented relevance feedback, with bias and performance audits.
- **Clustering:** used only to organize stated needs.
- **Bandit/RL:** adjusts presentation order from aggregate helpful/not-helpful counts; never changes eligibility.
- **Evaluation:** precision@k, recall of relevant schemes, language-level word error rate, translation adequacy, demographic parity diagnostics, abstention rate, and official-verification disagreement rate.

## Phase schedule

- **June 24–August/September:** Colab prototype, sample catalog, multilingual voice/text flow, transparent matching, testing.
- **August/September–September/October:** Streamlit deployment, approved myScheme/BHASHINI integration, WhatsApp webhook pilot, security and privacy review.
- **After pilot:** native SwiftUI app against `mobile_api.py`, App Store preparation, accessibility, deletion workflow, monitoring, and incident response.

## GitHub and copyright

The prototype UI and documentation identify Praneel Bembey as Author / Project Lead and Dr. Qingyang Xiao as Mentor. Replace the copyright owner placeholder with the correct legal claimant before publication. Do not claim ownership of government scheme descriptions, logos, myScheme content, BHASHINI models, third-party libraries, or map data. Keep a dependency/license inventory and preserve Git history showing authorship.

See `COPYRIGHT_CHECKLIST.md`. This repository contains general information, not legal advice.
