# Prototype Privacy Notice and Production Checklist

## Prototype behavior

The prototype processes information in the active Streamlit session to generate potential scheme matches. It is designed not to intentionally persist raw audio, exact browser coordinates, Aadhaar numbers, OTPs, passwords, bank credentials, or medical records.

The aggregate `bandit_state.json` stores only positive and negative feedback counts by scheme ID. It does not store user identifiers or profiles.

## Information the user may choose to provide

- Age and approximate annual household income
- Gender, marital status, broad residence type, and State/UT
- Optional scheme-specific conditions such as student, pregnancy, disability, occupation, or housing need
- A typed or spoken description of the requested support
- Current coordinates or a place name for a one-time nearby-service search

## External processing

Speech recognition, translation, text-to-speech, geocoding, map search, WhatsApp, and hosting providers may receive data when those features are enabled. The production privacy notice must name each provider, purpose, data category, retention period, location of processing, and deletion route.

## Required production controls

1. Collect only fields necessary for a selected scheme question.
2. Use layered consent in the user’s language.
3. Provide a clear deletion and consent-withdrawal mechanism.
4. Encrypt data in transit and at rest; rotate keys and tokens.
5. Separate identity/session data from recommendation data.
6. Use expiring sessions and short retention by default.
7. Restrict employee access and maintain audit logs.
8. Perform security, privacy, language-quality, accessibility, and bias testing.
9. Establish child-user safeguards and parental/guardian consent where legally required.
10. Never infer caste, religion, disability, health status, or income from voice, name, accent, or location.
11. Never request Aadhaar, OTP, bank password, or full medical records in chat.
12. Publish incident-response and grievance-contact information.

This document is a project checklist, not legal advice. Obtain qualified Indian privacy and platform counsel before launch.
