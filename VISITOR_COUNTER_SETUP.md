# Cumulative Visitor Counter (No Database)

The Streamlit app includes a visible **Cumulative app users** counter on the sidebar, a fixed badge, every functional tab, and the footer.

## How a visit is counted

- One increment is recorded per new Streamlit browser session.
- The counter does **not** store a name, phone number, WhatsApp ID, IP address, precise location, voice recording, or demographic profile.
- Refreshes/reruns within the same Streamlit session do not repeatedly increment the count.

## Default mode: local JSON file

The project works immediately with `data/visitor_count.json`. The app uses a file lock and atomic JSON write, so it does not need a database.

Streamlit Community Cloud can recreate the application container during a reboot, maintenance event, dependency change, or redeploy. A local file is not guaranteed to survive those events. The app increments before displaying the number, so it will not show `0`, but a local-only counter cannot honestly guarantee lifetime persistence across platform restarts.

## Recommended mode: GitHub-backed JSON file

For a cumulative number that survives Streamlit container replacement **without using a database**, configure the app to update the versioned `data/visitor_count.json` file in the GitHub repository.

Create a fine-grained GitHub token with **Contents: Read and write** access restricted to the single repository, then add these values in **Streamlit Community Cloud → App settings → Secrets**:

```toml
GITHUB_COUNTER_TOKEN = "github_pat_REPLACE_ME"
GITHUB_COUNTER_REPO = "qxiao2ub/AI_WhatsApp_Scheme_Advisor"
GITHUB_COUNTER_PATH = "data/visitor_count.json"
GITHUB_COUNTER_BRANCH = "main"
```

Do **not** commit the token to GitHub. The token belongs only in Streamlit Secrets.

The counter module retries update conflicts caused by simultaneous visitors. If GitHub is temporarily unavailable, the app falls back to the local JSON counter instead of crashing.

## Important interpretation

This is an **app-session headcount**, not a legally reliable count of unique human beings. Accurately deduplicating people across devices and browsers would require an account, cookie/device identifier, analytics service, or another persistent identifier. This prototype intentionally avoids that additional tracking.
