# Database setup

## Zero-config mode: SQLite

If `DATABASE_URL` is blank, Adhikaar.ai creates:

```text
data/adhikaar.db
```

This is suitable for local development and a functional Streamlit demonstration. Streamlit Community Cloud does not guarantee local-file persistence across restarts/redeployments, so do not depend on SQLite there for durable beneficiary-impact data.

## Recommended durable mode: PostgreSQL

Provision a managed PostgreSQL database from an approved provider, require TLS, create a least-privilege application user, and add the connection string only in Streamlit Secrets:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require"
DATA_RETENTION_DAYS = "365"
```

The app automatically creates its tables on first connection and seeds schemes from `sample_schemes.csv` only when the `schemes` table is empty.

## Tables

- `beneficiaries`
- `consents`
- `journey_events`
- `scheme_matches`
- `help_requests`
- `schemes`

## Production controls

Do not expose the database to the public internet unless the provider/network architecture requires it. Use provider IP/network controls where available, encrypted backups, credential rotation, monitoring, and separate development/staging/production databases.
