# Adhikaar.ai privacy design

## Consent model

The prototype separates two purposes:

1. **Session processing** — required to use the profile answers, text/voice transcript and matching engine for the current interaction.
2. **Impact analytics** — optional. When enabled, Adhikaar.ai stores a privacy-minimized pseudonymous profile and journey events for impact measurement.

A separate consent is required to store a human-help ticket.

## What impact analytics stores

- random pseudonymous browser-session ID
- language
- State/UT if provided
- urban/rural residence category
- age band, not exact age
- income band, not exact income
- broad need category
- limited non-sensitive profile flags
- schemes matched
- journey events such as application started/completed
- consent version and timestamp

## What is intentionally excluded from the impact database

- name
- phone number
- email address
- Aadhaar number
- passwords or OTPs
- full street address
- raw voice recording
- precise latitude/longitude
- free-form transcript
- social-category selection
- pregnancy/disability status
- full medical records

Sensitive values may be used transiently in the current session when a scheme rule genuinely requires them, but the analytics backend is designed not to persist them.

## Retention and deletion

`DATA_RETENTION_DAYS` controls the analytics retention window. `backend.py` can purge expired beneficiary profiles and related records. The Privacy Center also lets a user delete analytics linked to the current pseudonymous browser-session ID.

## Aggregation privacy

Geography and language breakdowns are suppressed until at least three consented profiles occur in a group. Production deployments should consider stronger statistical disclosure controls where required.

## External services

Speech recognition, translation, text-to-speech, geocoding, map search, WhatsApp, hosting and database providers can receive data when their features are enabled. A production privacy notice must name the actual providers, purposes, data categories, retention periods and deletion/grievance route.

## Production controls still required

- professional privacy/legal review for the intended jurisdiction and beneficiaries
- TLS for every network connection and encryption at rest
- managed secrets and key rotation
- SSO/MFA and role-based access control for staff/admins
- audit logs for administrative changes and data access
- database backups and tested recovery
- vulnerability management and dependency scanning
- rate limiting, abuse prevention and monitoring
- incident-response and grievance workflows
- child-user safeguards where applicable
- accessibility and language-quality testing
- data-processing/vendor agreements as required
- documented lawful basis and retention schedule for every production data category

This file is an engineering privacy checklist, not legal advice.
