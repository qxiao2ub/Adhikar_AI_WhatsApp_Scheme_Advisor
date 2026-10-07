# Admin guide

## Enable the prototype admin panel

Set either `ADMIN_PASSWORD_HASH` (recommended) or `ADMIN_PASSWORD` in Streamlit Secrets. Generate a SHA-256 password hash locally:

```bash
python -c "import hashlib,getpass; print(hashlib.sha256(getpass.getpass().encode()).hexdigest())"
```

## Scheme manager

For every scheme, maintain:

- unique scheme ID
- name and category
- State/UT scope
- age/income/residence/gender metadata if applicable
- required profile flags
- relevance keywords
- benefit summary
- required documents
- application steps
- official information URL
- official application URL
- official source/department URL
- last-verified date
- verification note
- active/inactive status

Do not mark a scheme as verified unless a project reviewer actually checked the current official source.

## Human-help queue

Admins can review the redacted issue text and set the ticket status to Open, In review, Resolved or Closed. The prototype intentionally avoids a raw beneficiary-profile browser.

## Production warning

The shared-password panel is for a prototype. Replace it with organization SSO/MFA, role-based authorization, audit logging and formal change approval before production.
