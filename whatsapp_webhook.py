"""WhatsApp Cloud API webhook scaffold.

Deploy on a public HTTPS backend such as Cloud Run, Azure, AWS, or another
approved service. Do not expose tokens in GitHub. This scaffold handles text
and a minimal consent-first conversation. Voice-note download/transcription
must be connected to an authorized ASR service before production.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

from core_engine import UserProfile, load_default_engine, redact_sensitive_text
from backend import BackendStore

ROOT = Path(__file__).resolve().parent
store = BackendStore(ROOT, database_url=os.getenv("DATABASE_URL", ""))
engine = load_default_engine(ROOT, catalog_df=store.scheme_dataframe(active_only=True))
app = FastAPI(title="Adhikaar.ai WhatsApp Webhook")

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "change-me")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
GRAPH_VERSION = os.getenv("WHATSAPP_GRAPH_VERSION", "v23.0")

# In-memory demo only. Replace with encrypted, expiring storage and a deletion workflow.
SESSIONS: Dict[str, Dict[str, Any]] = {}


@app.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


def send_text(to: str, body: str) -> None:
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print(f"[DEMO outbound to {to}] {body}")
        return
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{PHONE_NUMBER_ID}/messages"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"},
        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body[:3900]}},
        timeout=25,
    )
    response.raise_for_status()


def next_prompt(session: Dict[str, Any]) -> str:
    if not session.get("consent"):
        return "Reply YES to consent to session-only processing for scheme discovery. Do not send Aadhaar, OTPs, passwords, or full medical records."
    for key, prompt in [
        ("age", "What is your age?"),
        ("state", "Which State or Union Territory do you live in?"),
        ("residence", "Do you live in an Urban or Rural area?"),
        ("gender", "What is your gender? Reply Female, Male, Transgender, Other, or Skip."),
        ("income", "What is your approximate annual household income in INR? Reply Skip if unknown."),
        ("need_text", "What help do you need? You may write in your preferred language."),
    ]:
        if key not in session:
            session["awaiting"] = key
            return prompt
    return "READY"


def consume_answer(session: Dict[str, Any], text: str) -> str:
    clean = redact_sensitive_text(text)
    if not session.get("consent"):
        if clean.strip().lower() in {"yes", "y", "agree", "i agree"}:
            session["consent"] = True
            return next_prompt(session)
        return next_prompt(session)

    key = session.get("awaiting")
    if key == "age":
        try:
            session["age"] = int(clean)
        except ValueError:
            return "Please send age as a number, for example 35."
    elif key == "state":
        session["state"] = clean[:80]
    elif key == "residence":
        val = clean.strip().lower()
        if val not in {"urban", "rural"}:
            return "Please reply Urban or Rural."
        session["residence"] = val.title()
    elif key == "gender":
        session["gender"] = "Prefer not to say" if clean.lower() == "skip" else clean[:30].title()
    elif key == "income":
        if clean.lower() == "skip":
            session["income"] = None
        else:
            try:
                session["income"] = float(clean.replace(",", ""))
            except ValueError:
                return "Please send a number such as 250000, or reply Skip."
    elif key == "need_text":
        session["need_text"] = clean[:1000]
    session.pop("awaiting", None)

    prompt = next_prompt(session)
    if prompt != "READY":
        return prompt

    profile = UserProfile(
        age=session.get("age"), annual_income=session.get("income"),
        gender=session.get("gender", "Prefer not to say"), state=session.get("state", ""),
        residence=session.get("residence", "Prefer not to say"), need_text=session.get("need_text", ""),
    )
    results = engine.recommend(profile, top_k=3)
    lines = ["Potential matches only—verify officially on myScheme:"]
    for item in results:
        lines.append(f"\n• {item['name']}\n  {item['status']}\n  Documents: {', '.join(item['documents'][:3])}")
    lines.append("\nOfficial portal: https://www.myscheme.gov.in/")
    lines.append("Reply RESTART to clear this demo session.")
    return "\n".join(lines)


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    try:
        changes = payload["entry"][0]["changes"][0]["value"]
        messages = changes.get("messages", [])
        for msg in messages:
            sender = msg.get("from", "")
            msg_type = msg.get("type")
            if not sender:
                continue
            if msg_type == "text":
                text = msg.get("text", {}).get("body", "")
                if text.strip().lower() == "restart":
                    SESSIONS.pop(sender, None)
                    send_text(sender, "Session cleared. " + next_prompt(SESSIONS.setdefault(sender, {})))
                    continue
                session = SESSIONS.setdefault(sender, {})
                send_text(sender, consume_answer(session, text))
            elif msg_type in {"audio", "voice"}:
                send_text(sender, "Voice-note support requires the authorized media-download and ASR adapter. For this prototype, please send text.")
            else:
                send_text(sender, "Please send a text message for this prototype.")
    except Exception as exc:
        print("Webhook parse error:", exc)
    return {"status": "ok"}
