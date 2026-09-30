from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from filelock import FileLock


@dataclass(frozen=True)
class CounterSnapshot:
    value: int
    backend: str
    persistent_across_restarts: bool
    detail: str = ""


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _payload(count: int) -> dict[str, Any]:
    return {
        "count": max(0, int(count)),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Adhikar AI cumulative visitor counter. No user identity is stored.",
    }


def increment_local_counter(counter_file: Path) -> CounterSnapshot:
    """Increment a flat JSON file atomically. This uses no database.

    Streamlit Community Cloud can recreate an app container after a reboot or redeploy,
    so this local-file backend is durable only for the lifetime of that container.
    The UI never displays zero because the file is incremented before the value is shown.
    """
    counter_file.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(counter_file) + ".lock", timeout=10)
    with lock:
        count = 0
        if counter_file.exists():
            try:
                count = _safe_int(json.loads(counter_file.read_text(encoding="utf-8")).get("count"))
            except Exception:
                count = 0
        count += 1
        temp = counter_file.with_suffix(counter_file.suffix + ".tmp")
        temp.write_text(json.dumps(_payload(count), indent=2), encoding="utf-8")
        os.replace(temp, counter_file)
    return CounterSnapshot(
        value=max(1, count),
        backend="local JSON file",
        persistent_across_restarts=False,
        detail="Works with no setup; Streamlit can reset local files on a container restart or redeploy.",
    )


def increment_github_counter(
    *,
    token: str,
    repo: str,
    counter_path: str = "data/visitor_count.json",
    branch: str = "main",
    timeout: int = 15,
    max_attempts: int = 4,
) -> CounterSnapshot:
    """Increment a JSON file through the GitHub Contents API.

    This keeps the counter outside Streamlit's ephemeral filesystem while still using
    a simple versioned JSON file rather than a database. The token must have Contents
    read/write access to only the target repository.
    """
    token = (token or "").strip()
    repo = (repo or "").strip().strip("/")
    counter_path = (counter_path or "data/visitor_count.json").strip().lstrip("/")
    branch = (branch or "main").strip()
    if not token or "/" not in repo:
        raise ValueError("GitHub counter requires a token and an owner/repository name.")

    api_url = f"https://api.github.com/repos/{repo}/contents/{counter_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Adhikar-AI-Visitor-Counter",
    }

    last_error = ""
    for attempt in range(max_attempts):
        response = requests.get(api_url, headers=headers, params={"ref": branch}, timeout=timeout)
        sha = None
        current = 0
        if response.status_code == 200:
            data = response.json()
            sha = data.get("sha")
            try:
                decoded = base64.b64decode(data.get("content", "")).decode("utf-8")
                current = _safe_int(json.loads(decoded).get("count"))
            except Exception:
                current = 0
        elif response.status_code != 404:
            last_error = f"GitHub read failed ({response.status_code})."
            time.sleep(0.25 * (attempt + 1))
            continue

        updated = current + 1
        encoded = base64.b64encode(json.dumps(_payload(updated), indent=2).encode("utf-8")).decode("ascii")
        body: dict[str, Any] = {
            "message": "chore: increment Adhikar AI visitor count",
            "content": encoded,
            "branch": branch,
        }
        if sha:
            body["sha"] = sha

        write = requests.put(api_url, headers=headers, json=body, timeout=timeout)
        if write.status_code in (200, 201):
            return CounterSnapshot(
                value=max(1, updated),
                backend="GitHub JSON file",
                persistent_across_restarts=True,
                detail="Versioned flat-file counter; no visitor identity is stored.",
            )

        last_error = f"GitHub write failed ({write.status_code})."
        # A concurrent visit can update the same SHA. Re-read and retry.
        if write.status_code in (409, 422):
            time.sleep(0.2 * (attempt + 1))
            continue
        break

    raise RuntimeError(last_error or "GitHub counter update failed.")


def increment_counter(
    *,
    counter_file: Path,
    github_token: str = "",
    github_repo: str = "",
    github_path: str = "data/visitor_count.json",
    github_branch: str = "main",
) -> CounterSnapshot:
    """Prefer the persistent GitHub flat-file backend, then fall back to local JSON."""
    if (github_token or "").strip() and (github_repo or "").strip():
        try:
            return increment_github_counter(
                token=github_token,
                repo=github_repo,
                counter_path=github_path,
                branch=github_branch,
            )
        except Exception as exc:
            local = increment_local_counter(counter_file)
            return CounterSnapshot(
                value=local.value,
                backend=local.backend,
                persistent_across_restarts=False,
                detail=f"Persistent counter temporarily unavailable; local fallback is active. {exc}",
            )
    return increment_local_counter(counter_file)
