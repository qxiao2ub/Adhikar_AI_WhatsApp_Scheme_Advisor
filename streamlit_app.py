from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import tempfile
import uuid
from pathlib import Path
from html import escape
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from gtts import gTTS

from core_engine import UserProfile, load_default_engine, redact_sensitive_text
from backend import BackendStore, CONSENT_VERSION
from visitor_counter import CounterSnapshot, increment_counter

PROJECT_DIR = Path(__file__).resolve().parent
AUTHOR_NAME = os.getenv("APP_AUTHOR", "Praneel Bembey")
MENTOR_NAME = os.getenv("APP_MENTOR", "Dr. Qingyang Xiao")
APP_NAME = os.getenv("APP_NAME", "Adhikaar.ai")
APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", "https://ai-whatsapp-scheme-advisor.streamlit.app/")
HERO_PATH = PROJECT_DIR / "assets" / "adhikar-hero.jpg"
DASHBOARD_PATH = PROJECT_DIR / "assets" / "dashboard-demo.jpg"
COUNTER_FILE = PROJECT_DIR / "data" / "visitor_count.json"

LANGUAGES = {
    "English": {"code": "en", "locale": "en-IN"},
    "Hindi / हिन्दी": {"code": "hi", "locale": "hi-IN"},
    "Bengali / বাংলা": {"code": "bn", "locale": "bn-IN"},
    "Telugu / తెలుగు": {"code": "te", "locale": "te-IN"},
    "Marathi / मराठी": {"code": "mr", "locale": "mr-IN"},
    "Tamil / தமிழ்": {"code": "ta", "locale": "ta-IN"},
    "Gujarati / ગુજરાતી": {"code": "gu", "locale": "gu-IN"},
    "Kannada / ಕನ್ನಡ": {"code": "kn", "locale": "kn-IN"},
    "Malayalam / മലയാളം": {"code": "ml", "locale": "ml-IN"},
    "Punjabi / ਪੰਜਾਬੀ": {"code": "pa", "locale": "pa-IN"},
    "Odia / ଓଡ଼ିଆ": {"code": "or", "locale": "or-IN"},
    "Urdu / اردو": {"code": "ur", "locale": "ur-IN"},
}

UI_TEXT = {
    "en": {
        "welcome": "Tell me about the support you need. I will show potential matches and the documents to verify.",
        "disclaimer": "This is an educational pre-screen, not an official eligibility decision. Always verify on myScheme or with the responsible department.",
        "potential": "Potential scheme matches",
        "documents": "Documents commonly requested",
        "verify": "Verify this exact scheme name on the official myScheme portal.",
        "consent": "I consent to processing the information in this session for scheme discovery. Raw audio and precise location are not intentionally stored by this prototype.",
    },
    "hi": {
        "welcome": "आपको किस सहायता की आवश्यकता है, बताइए। मैं संभावित योजनाएँ और जाँच के लिए आवश्यक दस्तावेज़ दिखाऊँगा।",
        "disclaimer": "यह केवल शैक्षिक प्रारंभिक जाँच है, आधिकारिक पात्रता निर्णय नहीं। myScheme या संबंधित विभाग से अवश्य सत्यापित करें।",
        "potential": "संभावित योजना मिलान",
        "documents": "आमतौर पर माँगे जाने वाले दस्तावेज़",
        "verify": "आधिकारिक myScheme पोर्टल पर इसी योजना नाम से सत्यापित करें।",
        "consent": "मैं इस सत्र में योजना खोज के लिए दी गई जानकारी के प्रसंस्करण की सहमति देता/देती हूँ। यह प्रोटोटाइप जानबूझकर कच्ची ऑडियो या सटीक स्थान संग्रहीत नहीं करता।",
    },
    "bn": {
        "welcome": "আপনার কী সহায়তা দরকার বলুন। আমি সম্ভাব্য প্রকল্প ও যাচাইয়ের নথি দেখাব।",
        "disclaimer": "এটি শিক্ষামূলক প্রাথমিক যাচাই, সরকারি যোগ্যতার চূড়ান্ত সিদ্ধান্ত নয়। myScheme বা সংশ্লিষ্ট দপ্তরে যাচাই করুন।",
        "potential": "সম্ভাব্য প্রকল্প মিল",
        "documents": "সাধারণত প্রয়োজনীয় নথি",
        "verify": "সরকারি myScheme পোর্টালে একই প্রকল্পের নাম দিয়ে যাচাই করুন।",
        "consent": "আমি এই সেশনে প্রকল্প খোঁজার জন্য দেওয়া তথ্য প্রক্রিয়াকরণে সম্মতি দিচ্ছি। এই প্রোটোটাইপ ইচ্ছাকৃতভাবে কাঁচা অডিও বা নির্দিষ্ট অবস্থান সংরক্ষণ করে না।",
    },
    "ta": {
        "welcome": "உங்களுக்கு தேவையான உதவியைச் சொல்லுங்கள். சாத்தியமான திட்டங்களையும் சரிபார்க்க வேண்டிய ஆவணங்களையும் காட்டுகிறேன்.",
        "disclaimer": "இது கல்வி நோக்கிலான முன்-தேர்வு மட்டுமே; அதிகாரப்பூர்வ தகுதி முடிவு அல்ல. myScheme அல்லது சம்பந்தப்பட்ட துறையில் சரிபார்க்கவும்.",
        "potential": "சாத்தியமான திட்ட பொருத்தங்கள்",
        "documents": "பொதுவாக கேட்கப்படும் ஆவணங்கள்",
        "verify": "அதிகாரப்பூர்வ myScheme தளத்தில் இதே திட்டப் பெயரைச் சரிபார்க்கவும்.",
        "consent": "இந்த அமர்வில் திட்டத் தேடலுக்காக வழங்கிய தகவலை செயலாக்க நான் சம்மதிக்கிறேன். மூல ஒலி அல்லது துல்லிய இருப்பிடத்தை இந்த முன்மாதிரி நோக்கமுடன் சேமிக்காது.",
    },
    "te": {
        "welcome": "మీకు ఏ సహాయం కావాలో చెప్పండి. సాధ్యమైన పథకాలు మరియు ధృవీకరణకు కావలసిన పత్రాలను చూపిస్తాను.",
        "disclaimer": "ఇది విద్యాపరమైన ప్రాథమిక పరిశీలన మాత్రమే; అధికారిక అర్హత నిర్ణయం కాదు. myScheme లేదా సంబంధిత శాఖలో ధృవీకరించండి.",
        "potential": "సాధ్యమైన పథకాల సరిపోలికలు",
        "documents": "సాధారణంగా అడిగే పత్రాలు",
        "verify": "అధికారిక myScheme పోర్టల్‌లో ఇదే పథకం పేరుతో ధృవీకరించండి.",
        "consent": "ఈ సెషన్‌లో పథకం శోధన కోసం ఇచ్చిన సమాచారాన్ని ప్రాసెస్ చేయడానికి నేను అంగీకరిస్తున్నాను. ఈ ప్రోటోటైప్ ముడి ఆడియో లేదా ఖచ్చిత స్థానాన్ని ఉద్దేశపూర్వకంగా నిల్వ చేయదు.",
    },
    "mr": {
        "welcome": "आपल्याला कोणत्या मदतीची गरज आहे ते सांगा. मी संभाव्य योजना आणि पडताळणीसाठी आवश्यक कागदपत्रे दाखवेन.",
        "disclaimer": "ही केवळ शैक्षणिक प्राथमिक तपासणी आहे; अधिकृत पात्रता निर्णय नाही. myScheme किंवा संबंधित विभागाकडे पडताळणी करा.",
        "potential": "संभाव्य योजना जुळणी",
        "documents": "सामान्यतः मागितली जाणारी कागदपत्रे",
        "verify": "अधिकृत myScheme पोर्टलवर याच योजनेच्या नावाने पडताळणी करा.",
        "consent": "या सत्रात योजना शोधासाठी दिलेल्या माहितीवर प्रक्रिया करण्यास मी संमती देतो/देते. हा प्रोटोटाइप जाणीवपूर्वक कच्चा ऑडिओ किंवा अचूक स्थान साठवत नाही.",
    },
}

KEYWORD_TRANSLATIONS = {
    "स्वास्थ्य": "healthcare", "इलाज": "treatment", "अस्पताल": "hospital", "छात्रवृत्ति": "scholarship",
    "पेंशन": "pension", "रोजगार": "employment", "किसान": "farmer", "गर्भावस्था": "pregnancy",
    "স্বাস্থ্য": "healthcare", "চিকিৎসা": "treatment", "বৃত্তি": "scholarship", "পেনশন": "pension",
    "ஆரோக்கியம்": "healthcare", "மருத்துவம்": "treatment", "உதவித்தொகை": "scholarship", "ஓய்வூதியம்": "pension",
    "ఆరోగ్యం": "healthcare", "చికిత్స": "treatment", "ఉపకార వేతనం": "scholarship", "పెన్షన్": "pension",
    "आरोग्य": "healthcare", "उपचार": "treatment", "शिष्यवृत्ती": "scholarship", "निवृत्तीवेतन": "pension",
}

st.set_page_config(page_title=APP_NAME, page_icon="🇮🇳", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root {
  --adhikar-ivory: #F8F3E7;
  --adhikar-paper: #FFFCF5;
  --adhikar-navy: #243052;
  --adhikar-navy-soft: #324064;
  --adhikar-terracotta: #C87535;
  --adhikar-saffron: #E9973E;
  --adhikar-green: #4B745C;
  --adhikar-border: #DED4BE;
  --adhikar-muted: #6D7180;
  --adhikar-soft: #F1EADC;
}
html, body, [class*="css"] {font-family: Inter, "Noto Sans", "Segoe UI", Arial, sans-serif;}
.stApp {background: var(--adhikar-ivory); color: var(--adhikar-navy);}
[data-testid="stHeader"] {background: rgba(248,243,231,.94); border-bottom: 1px solid var(--adhikar-border);}
.block-container {max-width: 1180px; padding-top: 1rem; padding-bottom: 3rem;}

/* Lovable-inspired editorial shell */
.adhikar-topbar {
  display:flex; align-items:center; justify-content:space-between; gap:1rem;
  padding:.65rem 0 1rem; border-bottom:1px solid var(--adhikar-border); margin-bottom:2.3rem;
}
.adhikar-wordmark {display:flex; align-items:center; gap:.7rem; min-width:0;}
.adhikar-mark {
  width:34px; height:34px; position:relative; display:inline-flex; align-items:center; justify-content:center;
  color:var(--adhikar-navy); font-family:Georgia,"Noto Serif",serif; font-size:1.55rem; font-weight:700;
}
.adhikar-mark:after {content:""; position:absolute; width:13px; height:2px; background:var(--adhikar-terracotta); bottom:4px; left:10px;}
.adhikar-wordmark strong {font-family:Georgia,"Noto Serif",serif; font-size:1.35rem; font-weight:500; letter-spacing:-.01em;}
.adhikar-top-meta {font-size:.8rem; color:var(--adhikar-muted); text-align:right;}

.adhikar-home-hero {display:grid; grid-template-columns:1.05fr 1fr; gap:3.4rem; align-items:center; margin-bottom:5rem;}
.adhikar-eyebrow {font-size:.79rem; font-weight:800; text-transform:uppercase; letter-spacing:.14em; color:var(--adhikar-terracotta);}
.adhikar-home-hero h1 {font-family:Georgia,"Noto Serif",serif; font-weight:400; letter-spacing:-.02em; font-size:clamp(2.65rem,5vw,4.4rem); line-height:1.04; margin:.7rem 0 1.25rem; color:var(--adhikar-navy);}
.adhikar-home-hero .lead {font-size:1.12rem; line-height:1.75; color:var(--adhikar-muted); max-width:39rem;}
.adhikar-app-name {display:inline-block; margin-top:1.3rem; padding:.43rem .72rem; background:var(--adhikar-soft); border:1px solid var(--adhikar-border); border-radius:8px; font-size:.86rem; font-weight:800;}
.adhikar-hero-photo img {width:100%; aspect-ratio:16/11; object-fit:cover; object-position:center; border:1px solid var(--adhikar-border); border-radius:12px; display:block;}
.adhikar-photo-caption {font-size:.72rem; color:var(--adhikar-muted); margin-top:.4rem;}

.adhikar-section {margin:4.8rem 0 0; max-width:900px;}
.adhikar-section h2 {font-family:Georgia,"Noto Serif",serif; font-weight:400; font-size:clamp(2rem,3vw,2.55rem); line-height:1.12; margin:.55rem 0 .8rem; color:var(--adhikar-navy);}
.adhikar-section p {font-size:1.04rem; line-height:1.75; color:var(--adhikar-muted);}
.adhikar-steps {display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:2rem; margin:2.2rem 0 4.5rem;}
.adhikar-step {border-top:1px solid var(--adhikar-border); padding-top:1.1rem;}
.adhikar-step .num {font-family:Georgia,"Noto Serif",serif; font-size:1.7rem; color:var(--adhikar-terracotta);}
.adhikar-step h3 {font-size:1.05rem; margin:.2rem 0 .45rem; color:var(--adhikar-navy);}
.adhikar-step p {font-size:.92rem; line-height:1.6; color:var(--adhikar-muted); margin:0;}

/* Counter is always visible and repeated inside every tab credit strip. */
.visitor-fixed {
  position:fixed; top:4.25rem; right:1rem; z-index:999;
  display:flex; align-items:center; gap:.55rem; padding:.55rem .75rem;
  border:1px solid var(--adhikar-border); border-radius:999px; background:rgba(255,252,245,.96);
  box-shadow:0 6px 18px rgba(36,48,82,.08); color:var(--adhikar-navy); font-size:.78rem; font-weight:700;
}
.visitor-dot {width:8px;height:8px;border-radius:50%;background:var(--adhikar-green);box-shadow:0 0 0 4px rgba(75,116,92,.13);}
.visitor-fixed strong {font-size:.92rem;}
.visitor-card {border:1px solid rgba(255,255,255,.18); border-radius:10px; padding:.7rem .75rem; margin:.7rem 0; background:rgba(255,255,255,.08); text-align:center;}
.visitor-card .count {font-family:Georgia,"Noto Serif",serif; font-size:1.65rem; color:#FFF8E8; line-height:1;}
.visitor-card .label {font-size:.72rem; opacity:.82; margin-top:.32rem;}

section[data-testid="stSidebar"] {background:var(--adhikar-navy); border-right:3px solid var(--adhikar-terracotta);}
section[data-testid="stSidebar"] * {color:#FFF9EC;}
section[data-testid="stSidebar"] a {color:#FFF9EC !important;}
section[data-testid="stSidebar"] [data-testid="stAlert"] {background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);}
section[data-testid="stSidebar"] [data-testid="stLinkButton"] a {background:var(--adhikar-terracotta);color:white !important;border:none;font-weight:800;}
.adhikar-sidebar-brand {text-align:center; padding:.2rem .25rem .6rem;}
.adhikar-sidebar-logo {width:54px;height:54px;margin:0 auto .55rem;border:1px solid rgba(255,255,255,.35);border-radius:10px;display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-size:1.7rem;color:#FFF9EC;position:relative;}
.adhikar-sidebar-logo:after {content:"";position:absolute;width:15px;height:2px;background:var(--adhikar-saffron);bottom:9px;}
.adhikar-sidebar-brand h2 {font-family:Georgia,serif;font-size:1.35rem;margin:.15rem 0;color:white;font-weight:500;}
.adhikar-sidebar-brand p {font-size:.79rem;opacity:.75;margin:0;}

.credit-strip {display:flex;flex-wrap:wrap;gap:.45rem 1rem;align-items:center;padding:.68rem .85rem;margin:.05rem 0 1rem;border-radius:8px;background:var(--adhikar-paper);border:1px solid var(--adhikar-border);color:#31405E;font-size:.86rem;}
.credit-strip .users {margin-left:auto;font-weight:800;color:var(--adhikar-green);}
.team-card {padding:1.1rem 1.2rem;border:1px solid var(--adhikar-border);border-radius:10px;background:var(--adhikar-paper);margin-bottom:1rem;}
[data-baseweb="tab-list"] {gap:.25rem;background:var(--adhikar-paper);border-radius:10px;padding:.28rem;border:1px solid var(--adhikar-border);}
[data-baseweb="tab"] {border-radius:7px;padding:.58rem .8rem;}
[aria-selected="true"][data-baseweb="tab"] {background:var(--adhikar-navy);color:white;}
[data-testid="stForm"] {background:var(--adhikar-paper);border:1px solid var(--adhikar-border);border-radius:10px;padding:1rem;}
[data-testid="stVerticalBlockBorderWrapper"] {background:var(--adhikar-paper);border-color:var(--adhikar-border)!important;border-radius:10px;box-shadow:none;}
.stButton>button[kind="primary"], .stFormSubmitButton>button {background:var(--adhikar-navy);border:none;border-radius:8px;font-weight:800;}
.stButton>button[kind="primary"]:hover, .stFormSubmitButton>button:hover {background:var(--adhikar-navy-soft);}
.stLinkButton>a {border-radius:8px;font-weight:700;}
.adhikar-footer {margin-top:3rem;padding:1.35rem 1.5rem;border-top:1px solid var(--adhikar-border);background:transparent;color:var(--adhikar-muted);}
.adhikar-footer h3 {color:var(--adhikar-navy)!important;}
.adhikar-footer a {color:var(--adhikar-navy)!important;font-weight:800;}

@media (max-width: 850px) {
  .adhikar-home-hero {grid-template-columns:1fr;gap:1.7rem;margin-bottom:3.2rem;}
  .adhikar-home-hero h1 {font-size:2.65rem;}
  .adhikar-steps {grid-template-columns:1fr;gap:1.25rem;margin-bottom:3rem;}
  .visitor-fixed {top:auto;bottom:.8rem;right:.7rem;}
  .adhikar-top-meta {display:none;}
  .block-container {padding-left:.8rem;padding-right:.8rem;}
}
</style>
""", unsafe_allow_html=True)

def image_data_uri(path: Path) -> str:
    """Return a local image as a data URI so the Lovable hero works on Streamlit Cloud."""
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return ""


def app_setting(name: str, default: str = "") -> str:
    """Read a Streamlit secret when available, then fall back to an environment variable."""
    try:
        value = st.secrets.get(name, None)
        if value is not None:
            return str(value)
    except Exception:
        pass
    return str(os.getenv(name, default))


def get_or_increment_visitor_count() -> CounterSnapshot:
    """Count one visit per Streamlit browser session, without storing a user identity."""
    if "visitor_counter_snapshot" not in st.session_state:
        snapshot = increment_counter(
            counter_file=COUNTER_FILE,
            github_token=app_setting("GITHUB_COUNTER_TOKEN"),
            github_repo=app_setting("GITHUB_COUNTER_REPO", "qxiao2ub/AI_WhatsApp_Scheme_Advisor"),
            github_path=app_setting("GITHUB_COUNTER_PATH", "data/visitor_count.json"),
            github_branch=app_setting("GITHUB_COUNTER_BRANCH", "main"),
        )
        st.session_state["visitor_counter_snapshot"] = snapshot
    return st.session_state["visitor_counter_snapshot"]


@st.cache_resource
def get_backend() -> BackendStore:
    return BackendStore(
        project_dir=PROJECT_DIR,
        database_url=app_setting("DATABASE_URL"),
        retention_days=int(app_setting("DATA_RETENTION_DAYS", "365") or 365),
    )


BACKEND = get_backend()
if "retention_checked" not in st.session_state:
    try:
        BACKEND.purge_expired_data()
    except Exception:
        pass
    st.session_state["retention_checked"] = True


@st.cache_resource
def get_engine(catalog_revision: str):
    catalog_df = BACKEND.scheme_dataframe(active_only=True)
    if catalog_df.empty:
        return load_default_engine(PROJECT_DIR)
    return load_default_engine(PROJECT_DIR, catalog_df=catalog_df)


engine = get_engine(BACKEND.scheme_revision())
VISITOR_COUNTER = get_or_increment_visitor_count()


def beneficiary_id() -> str:
    if "beneficiary_id" not in st.session_state:
        st.session_state["beneficiary_id"] = uuid.uuid4().hex
    return st.session_state["beneficiary_id"]


def analytics_enabled() -> bool:
    return bool(st.session_state.get("analytics_consent", False))


def admin_password_ok(candidate: str) -> bool:
    configured_hash = app_setting("ADMIN_PASSWORD_HASH").strip().lower()
    configured_plain = app_setting("ADMIN_PASSWORD").strip()
    if configured_hash:
        digest = hashlib.sha256((candidate or "").encode("utf-8")).hexdigest().lower()
        return hmac.compare_digest(digest, configured_hash)
    if configured_plain:
        return hmac.compare_digest(candidate or "", configured_plain)
    return False


def render_project_credit() -> None:
    """Show attribution and the cumulative app-user count inside every main tab/page."""
    st.markdown(
        f"<div class='credit-strip'><span><strong>Author / Project Lead:</strong> {escape(AUTHOR_NAME)}</span>"
        f"<span><strong>Mentor:</strong> {escape(MENTOR_NAME)}</span>"
        f"<span class='users'>● Cumulative app users: {VISITOR_COUNTER.value:,}</span></div>",
        unsafe_allow_html=True,
    )


def local_ui(code: str, key: str) -> str:
    return UI_TEXT.get(code, UI_TEXT["en"]).get(key, UI_TEXT["en"][key])


def basic_keyword_normalize(text: str) -> str:
    out = text or ""
    for source, target in KEYWORD_TRANSLATIONS.items():
        out = out.replace(source, f" {target} ")
    return out


def external_translate(text: str, source_code: str, target_code: str) -> str:
    """Demo translation adapter. Use an authorized BHASHINI implementation in production."""
    if not text or source_code == target_code:
        return text
    api_url = os.getenv("BHASHINI_TRANSLATE_URL", "").strip()
    api_key = os.getenv("BHASHINI_API_KEY", "").strip()
    if api_url and api_key:
        try:
            response = requests.post(
                api_url,
                json={"source_language": source_code, "target_language": target_code, "text": text},
                headers={"Authorization": f"Bearer {api_key}"}, timeout=25,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("translated_text") or data.get("translation") or text
        except Exception:
            pass
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source=source_code if source_code != "auto" else "auto", target=target_code).translate(text)
    except Exception:
        return text


def transcribe_wav(audio_bytes: bytes, locale: str) -> tuple[str, str]:
    """Prototype ASR. Replace with authorized BHASHINI ASR or an audited local model."""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=locale)
        return text, "Demo web speech recognizer"
    except Exception as exc:
        return "", f"Transcription unavailable: {exc}"


def synthesize(text: str, lang_code: str) -> bytes | None:
    try:
        fp = io.BytesIO()
        gTTS(text=text, lang=lang_code if lang_code in {"en","hi","bn","te","mr","ta","gu","kn","ml","pa","ur"} else "en").write_to_fp(fp)
        return fp.getvalue()
    except Exception:
        return None


def geocode_place(place: str):
    try:
        geo = Nominatim(user_agent="adhikaar-ai-scheme-advisor-prototype")
        loc = geo.geocode(place, country_codes="in", timeout=10)
        if loc:
            return float(loc.latitude), float(loc.longitude), loc.address
    except Exception:
        return None
    return None


def nearby_services(lat: float, lon: float, radius_m: int = 12000):
    query = f"""[out:json][timeout:20];(
      nwr(around:{radius_m},{lat},{lon})["office"="government"];
      nwr(around:{radius_m},{lat},{lon})["amenity"~"hospital|clinic|townhall|community_centre"];
    );out center tags 35;"""
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=30)
        response.raise_for_status()
        items = []
        for element in response.json().get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name") or tags.get("operator") or "Government/community service location"
            elat = element.get("lat") or element.get("center", {}).get("lat")
            elon = element.get("lon") or element.get("center", {}).get("lon")
            if elat is None or elon is None:
                continue
            distance = geodesic((lat, lon), (elat, elon)).km
            items.append({"name": name, "type": tags.get("amenity") or tags.get("office") or "service", "lat": elat, "lon": elon, "distance_km": round(distance, 2)})
        items.sort(key=lambda x: x["distance_km"])
        return items[:12]
    except Exception:
        return []


with st.sidebar:
    st.markdown(
        "<div class='adhikar-sidebar-brand'>"
        "<div class='adhikar-sidebar-logo'>A</div>"
        "<h2>Adhikaar.ai</h2>"
        "<p>Discover, understand and access government benefits</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='visitor-card'><div class='count'>{VISITOR_COUNTER.value:,}</div>"
        "<div class='label'>CUMULATIVE APP USERS</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Author / Project Lead:** {escape(AUTHOR_NAME)}")
    st.markdown(f"**Mentor:** {escape(MENTOR_NAME)}")
    st.caption(f"Backend: {BACKEND.database_label()}")
    st.markdown("**Privacy:** direct identifiers, raw audio and precise coordinates are not intentionally stored by the impact database.")
    st.warning("Never enter Aadhaar numbers, bank passwords, OTPs, or full medical records.")
    accessibility_large_text = st.toggle("Larger text", value=bool(st.session_state.get("large_text", False)))
    accessibility_high_contrast = st.toggle("Higher contrast", value=bool(st.session_state.get("high_contrast", False)))
    st.session_state["large_text"] = accessibility_large_text
    st.session_state["high_contrast"] = accessibility_high_contrast
    share_url = f"https://wa.me/?text={quote_plus('Try Adhikaar.ai: ' + APP_PUBLIC_URL)}"
    st.link_button("Share Adhikaar.ai on WhatsApp", share_url, use_container_width=True)
    st.link_button("Open official myScheme", "https://www.myscheme.gov.in/", use_container_width=True)

if accessibility_large_text or accessibility_high_contrast:
    extra_css = []
    if accessibility_large_text:
        extra_css.append(".stApp {font-size: 1.08rem;} .stMarkdown p, .stMarkdown li {line-height:1.75;}")
    if accessibility_high_contrast:
        extra_css.append(".stApp {background:#fff !important;color:#111 !important;} .stTabs [data-baseweb='tab-list'] {background:#fff;} .credit-strip {border-color:#111 !important;}")
    st.markdown("<style>" + "\n".join(extra_css) + "</style>", unsafe_allow_html=True)

# A fixed badge keeps the cumulative count visible regardless of the selected tab.
st.markdown(
    f"<div class='visitor-fixed'><span class='visitor-dot'></span>"
    f"Cumulative app users <strong>{VISITOR_COUNTER.value:,}</strong></div>",
    unsafe_allow_html=True,
)

hero_uri = image_data_uri(HERO_PATH)
hero_html = (
    f"<img src='{hero_uri}' alt='Community members in India meeting together'>"
    if hero_uri else
    "<div style='aspect-ratio:16/11;background:#EDE3CF;border:1px solid #DED4BE;border-radius:12px'></div>"
)

st.markdown(
    f"<div class='adhikar-topbar'>"
    f"<div class='adhikar-wordmark'><span class='adhikar-mark'>A</span><strong>Adhikaar.ai</strong></div>"
    f"<div class='adhikar-top-meta'>Privacy-minimized · multilingual · transparent pre-screening<br>"
    f"Author: {escape(AUTHOR_NAME)} · Mentor: {escape(MENTOR_NAME)}</div>"
    f"</div>"
    f"<section class='adhikar-home-hero'>"
    f"<div><div class='adhikar-eyebrow'>12 language options · voice supported · WhatsApp ready</div>"
    f"<h1>From scheme discovery to the application journey.</h1>"
    f"<p class='lead'>Tell Adhikaar.ai a few basic details and the support you need. It proactively surfaces schemes worth checking, explains why they may fit, lists documents and application steps, links to official sources, and can track an opt-in beneficiary journey from discovery to self-reported completion.</p>"
    f"<span class='adhikar-app-name'>{escape(APP_NAME)}</span></div>"
    f"<figure class='adhikar-hero-photo'>{hero_html}<figcaption class='adhikar-photo-caption'>Interface adapted from the attached Lovable Adhikar UI source and extended for end-to-end access.</figcaption></figure>"
    f"</section>",
    unsafe_allow_html=True,
)

st.markdown(
    "<section class='adhikar-section'><div class='adhikar-eyebrow'>The platform vision</div>"
    "<h2>Discover. Understand. Apply. Measure impact.</h2>"
    "<p>Adhikaar.ai is designed to evolve beyond a scheme-information search box. The prototype combines personalized discovery, transparent pre-screening, documents and application guidance, opt-in journey analytics, scheme administration, accessibility, and human-help escalation while keeping official government sources as the final authority.</p></section>"
    "<div class='adhikar-steps'>"
    "<div class='adhikar-step'><div class='num'>01</div><h3>Tell us only what is needed</h3><p>Use text or voice in a supported language. Sensitive details are processed for the session and are not intentionally persisted in analytics.</p></div>"
    "<div class='adhikar-step'><div class='num'>02</div><h3>Receive proactive matches</h3><p>Transparent rules create a pre-screen status; ML helps rank relevant schemes but never makes the official eligibility decision.</p></div>"
    "<div class='adhikar-step'><div class='num'>03</div><h3>Move toward access</h3><p>Review documents, steps and official links, start an application journey, request help, and optionally contribute privacy-minimized impact metrics.</p></div>"
    "</div>",
    unsafe_allow_html=True,
)

(
    tab_advisor,
    tab_nearby,
    tab_impact,
    tab_help,
    tab_access,
    tab_ai,
    tab_admin,
    tab_team,
) = st.tabs([
    "Discover schemes",
    "Nearby help",
    "Impact dashboard",
    "Human help & privacy",
    "Accessibility & WhatsApp",
    "How the AI works",
    "Admin",
    "Project team",
])

with tab_advisor:
    render_project_credit()
    st.subheader("Personalized scheme discovery")
    st.write("You do not need to know a scheme name. Provide a few basic details and Adhikaar.ai will proactively identify schemes worth checking.")
    language_name = st.selectbox("Preferred language", list(LANGUAGES.keys()), key="discover_language")
    lang_code = LANGUAGES[language_name]["code"]
    locale = LANGUAGES[language_name]["locale"]
    st.info(local_ui(lang_code, "welcome"))
    st.warning(local_ui(lang_code, "disclaimer"))
    consent = st.checkbox(local_ui(lang_code, "consent"), key="session_processing_consent")
    if st.session_state.pop("force_analytics_off", False):
        st.session_state.pop("analytics_consent_widget", None)
    analytics_consent = st.checkbox(
        "Optional: I consent to saving a privacy-minimized, pseudonymous profile and journey metrics so the project can measure reach and impact. Exact age/income are converted to bands; direct identifiers, raw audio, precise location, social category, pregnancy/disability status and free-form transcript are not stored in analytics.",
        value=bool(st.session_state.get("analytics_consent", False)),
        key="analytics_consent_widget",
    )
    external_processing = st.checkbox(
        "Allow the transcript and generated summary to be sent to a configured translation/voice service for this session.",
        key="external_processing_widget",
    )

    with st.form("profile_form"):
        c1, c2, c3 = st.columns(3)
        age = c1.number_input("Age", min_value=0, max_value=120, value=25)
        income_known = c2.checkbox("I know annual household income", value=False)
        annual_income = c2.number_input(
            "Annual household income (INR)", min_value=0.0, value=0.0, step=10000.0, disabled=not income_known
        )
        gender = c3.selectbox("Gender", ["Prefer not to say", "Female", "Male", "Transgender", "Other"])
        marital_status = c1.selectbox("Marital status", ["Prefer not to say", "Single", "Married", "Widowed", "Divorced", "Separated"])
        state = c2.text_input("State / Union Territory", help="Use only a State/UT, not a street address.")
        residence = c3.selectbox("Residence", ["Prefer not to say", "Urban", "Rural"])
        social_category = c1.selectbox(
            "Social category (optional; only used transiently when a scheme explicitly requires it)",
            ["Prefer not to say", "General", "OBC", "SC", "ST", "Other"],
        )

        st.markdown("**Select only conditions relevant to your request**")
        f1, f2, f3, f4 = st.columns(4)
        student = f1.checkbox("Student")
        pregnant = f1.checkbox("Pregnant")
        disability = f2.checkbox("Person with disability")
        entrepreneur = f2.checkbox("Entrepreneur / planning a business")
        street_vendor = f3.checkbox("Street vendor")
        farmer = f3.checkbox("Farmer")
        housing_need = f4.checkbox("Needs housing support")
        bank_account = f4.checkbox("Has savings bank/post-office account")

        typed_need = st.text_area(
            "Describe what support you need in your language",
            placeholder="Example: I need help paying for hospital treatment or finding a scholarship.",
        )
        audio_value = (
            st.audio_input("Or record a short voice message")
            if hasattr(st, "audio_input")
            else st.file_uploader("Upload a WAV voice message", type=["wav"])
        )
        submitted = st.form_submit_button("Discover potential schemes", type="primary", use_container_width=True)

    if submitted:
        if not consent:
            st.error("Session-processing consent is required before Adhikaar.ai can use these answers for matching.")
        else:
            transcript = typed_need.strip()
            if audio_value is not None:
                audio_bytes = audio_value.getvalue()
                recognized, asr_note = transcribe_wav(audio_bytes, locale)
                if recognized:
                    transcript = (transcript + " " + recognized).strip()
                    st.success(f"Voice transcript for this session: {recognized}")
                else:
                    st.warning(asr_note)

            safe_transcript = redact_sensitive_text(transcript)
            english_need = basic_keyword_normalize(safe_transcript)
            if lang_code != "en" and external_processing and safe_transcript:
                english_need = external_translate(safe_transcript, lang_code, "en")

            profile = UserProfile(
                age=int(age),
                annual_income=float(annual_income) if income_known else None,
                gender=gender,
                marital_status=marital_status,
                state=state.strip(),
                residence=residence,
                social_category=social_category,
                student=student,
                pregnant=pregnant,
                disability=disability,
                entrepreneur=entrepreneur,
                street_vendor=street_vendor,
                farmer=farmer,
                housing_need=housing_need,
                bank_account=bank_account,
                need_text=english_need,
            )
            need_cluster = engine.need_cluster(english_need)
            results = engine.recommend(profile, top_k=6)
            st.session_state["last_results"] = results
            st.session_state["lang_code"] = lang_code
            st.session_state["external_processing"] = external_processing
            st.session_state["need_cluster"] = need_cluster
            previous_analytics = analytics_enabled()
            if previous_analytics and not analytics_consent:
                try:
                    BACKEND.record_consent(beneficiary_id(), "impact_analytics", False)
                except Exception:
                    pass
            st.session_state["analytics_consent"] = bool(analytics_consent)
            st.session_state["last_profile_state"] = state.strip()

            if analytics_consent:
                bid = beneficiary_id()
                try:
                    if not st.session_state.get("analytics_consent_recorded"):
                        BACKEND.record_consent(bid, "impact_analytics", True)
                        st.session_state["analytics_consent_recorded"] = True
                    BACKEND.upsert_beneficiary(
                        beneficiary_id=bid,
                        profile=profile,
                        language=lang_code,
                        need_category=need_cluster,
                        analytics_consent=True,
                    )
                    BACKEND.record_event(
                        "profile_saved",
                        beneficiary_id=bid,
                        language=lang_code,
                        state=state.strip(),
                        metadata={"need_category": need_cluster},
                    )
                    BACKEND.record_matches(bid, results)
                    BACKEND.record_event(
                        "scheme_matches_generated",
                        beneficiary_id=bid,
                        language=lang_code,
                        state=state.strip(),
                        metadata={"match_count": len(results), "need_category": need_cluster},
                    )
                except Exception as exc:
                    st.warning(f"Recommendations are available, but impact analytics could not be saved: {exc}")

    results = st.session_state.get("last_results", [])
    if results:
        st.subheader(local_ui(st.session_state.get("lang_code", "en"), "potential"))
        st.caption(
            f"Need cluster for recommendation organization only: {st.session_state.get('need_cluster', 'General discovery')}. "
            "It does not determine official eligibility."
        )
        for i, item in enumerate(results, 1):
            with st.container(border=True):
                st.markdown(f"### {i}. {item['name']}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Pre-screen status", item["status"])
                m2.metric("Transparent rule score", f"{item['pre_screen_confidence']:.0%}")
                m3.metric("ML relevance rank", f"{item['ml_relevance_probability']:.0%}")
                st.write(item["benefits"])
                if item["reasons"]:
                    st.markdown("**Why it appeared**")
                    for reason in item["reasons"]:
                        st.write("• " + reason)
                if item["missing"]:
                    st.markdown("**Still needs official confirmation**")
                    for missing in item["missing"]:
                        st.write("• " + missing)
                if item["failed"]:
                    st.markdown("**Possible mismatch**")
                    for fail in item["failed"]:
                        st.write("• " + fail)

                cdocs, csteps = st.columns(2)
                with cdocs:
                    with st.expander("Documents commonly requested", expanded=True):
                        docs = item.get("documents") or ["Check the official source for the latest document list."]
                        for doc in docs:
                            st.write("• " + doc)
                with csteps:
                    with st.expander("Application steps", expanded=True):
                        steps = item.get("application_steps") or [
                            "Review the official eligibility rules.",
                            "Gather the required documents.",
                            "Open the official application portal or designated office.",
                            "Submit and save your acknowledgement/reference number.",
                        ]
                        for n, step in enumerate(steps, 1):
                            st.write(f"{n}. {step}")

                st.caption(item["verification_note"])
                if item.get("last_verified"):
                    st.caption(f"Catalog last verified by project admin: {item['last_verified']}")
                else:
                    st.caption("Catalog verification date has not yet been entered by the project admin. Verify before relying on the result.")
                st.markdown(f"**Official source:** {item.get('official_source') or item['official_url']}")

                a, b, c, d = st.columns(4)
                a.link_button("Official scheme source", item["official_url"], use_container_width=True)
                b.link_button("Official application link", item["application_url"], use_container_width=True)
                if c.button("Start application journey", key=f"start_{item['scheme_id']}", use_container_width=True):
                    st.session_state.setdefault("journey_started", set()).add(item["scheme_id"])
                    if analytics_enabled():
                        BACKEND.record_event(
                            "application_started",
                            beneficiary_id=beneficiary_id(),
                            scheme_id=item["scheme_id"],
                            scheme_name=item["name"],
                            language=st.session_state.get("lang_code", "en"),
                            state=st.session_state.get("last_profile_state", ""),
                        )
                        st.toast("Application journey recorded in opt-in impact analytics.")
                    else:
                        st.toast("Journey started for this session. Enable impact analytics to include it in aggregate metrics.")
                if d.button("Mark completed", key=f"complete_{item['scheme_id']}", use_container_width=True):
                    st.session_state.setdefault("journey_completed", set()).add(item["scheme_id"])
                    if analytics_enabled():
                        BACKEND.record_event(
                            "application_completed",
                            beneficiary_id=beneficiary_id(),
                            scheme_id=item["scheme_id"],
                            scheme_name=item["name"],
                            language=st.session_state.get("lang_code", "en"),
                            state=st.session_state.get("last_profile_state", ""),
                            metadata={"self_reported": True},
                        )
                        st.toast("Self-reported completion recorded.")
                    else:
                        st.toast("Completion marked for this session only.")

                a2, b2, c2 = st.columns(3)
                a2.link_button("Share scheme on WhatsApp", f"https://wa.me/?text={item['share_text']}", use_container_width=True)
                if b2.button("👍 Helpful", key=f"up_{item['scheme_id']}", use_container_width=True):
                    engine.record_feedback(item["scheme_id"], True)
                    st.toast("Aggregate ranking feedback recorded")
                if c2.button("👎 Not helpful", key=f"down_{item['scheme_id']}", use_container_width=True):
                    engine.record_feedback(item["scheme_id"], False)
                    st.toast("Aggregate ranking feedback recorded")

                summary_en = (
                    f"Potential match: {item['name']}. {item['benefits']} "
                    "This is not a final eligibility decision. Verify on the official scheme source."
                )
                output_lang = st.session_state.get("lang_code", "en")
                summary_out = summary_en
                if output_lang != "en" and st.session_state.get("external_processing", False):
                    summary_out = external_translate(summary_en, "en", output_lang)
                st.write(summary_out)
                audio = synthesize(summary_out, output_lang)
                if audio:
                    st.audio(audio, format="audio/mp3")

with tab_nearby:
    render_project_credit()
    st.subheader("Find nearby government and community service locations")
    st.caption("Browser location is processed in the current session only. For better privacy, you can enter a city, district, State or PIN code instead.")
    components.html(
        """
        <button id='locbtn' style='padding:10px 16px;border-radius:10px;border:1px solid #999;background:white;cursor:pointer'>Use my current location</button>
        <p id='status' style='font-family:sans-serif;font-size:13px'></p>
        <script>
        document.getElementById('locbtn').onclick = function(){
          const status = document.getElementById('status');
          if(!navigator.geolocation){ status.innerText='Geolocation is not supported by this browser.'; return; }
          status.innerText='Requesting permission...';
          navigator.geolocation.getCurrentPosition(function(pos){
            const u = new URL(window.parent.location.href);
            u.searchParams.set('lat', pos.coords.latitude.toFixed(6));
            u.searchParams.set('lon', pos.coords.longitude.toFixed(6));
            window.parent.location.href = u.toString();
          }, function(err){ status.innerText='Location permission was not granted: ' + err.message; });
        };
        </script>
        """,
        height=95,
    )

    place = st.text_input("Or enter city, district, State, or PIN code", placeholder="Example: Pune, Maharashtra", key="nearby_place")
    lat_q = st.query_params.get("lat")
    lon_q = st.query_params.get("lon")
    coords = None
    label = ""
    if lat_q and lon_q:
        try:
            coords = (float(lat_q), float(lon_q))
            label = "Browser-provided current location"
        except Exception:
            coords = None
    if st.button("Search near entered place", use_container_width=True) and place:
        found = geocode_place(place)
        if found:
            coords = (found[0], found[1])
            label = found[2]
            st.session_state["manual_coords"] = coords
            st.session_state["manual_label"] = label
        else:
            st.error("Could not locate that place. Try a city plus State or a PIN code.")
    if coords is None and "manual_coords" in st.session_state:
        coords = st.session_state["manual_coords"]
        label = st.session_state.get("manual_label", "Entered location")

    if coords:
        st.success(f"Searching around: {label}")
        data = nearby_services(coords[0], coords[1])
        map_df = pd.DataFrame([{"lat": coords[0], "lon": coords[1], "name": "Search location"}] + data)
        st.map(map_df, latitude="lat", longitude="lon", size=70)
        if data:
            for item in data:
                maps = f"https://www.google.com/maps/search/?api=1&query={item['lat']},{item['lon']}"
                st.markdown(f"**{item['name']}** — {item['type']} — approximately {item['distance_km']} km")
                st.link_button("Open map", maps, key=f"map_{item['lat']}_{item['lon']}")
        else:
            st.warning("Live open-map search was unavailable. Use the map-search links below.")
        gov_maps = f"https://www.google.com/maps/search/government+office/@{coords[0]},{coords[1]},13z"
        health_maps = f"https://www.google.com/maps/search/government+hospital/@{coords[0]},{coords[1]},13z"
        c1, c2 = st.columns(2)
        c1.link_button("Search nearby government offices", gov_maps, use_container_width=True)
        c2.link_button("Search nearby government hospitals", health_maps, use_container_width=True)

with tab_impact:
    render_project_credit()
    st.subheader("Impact dashboard")
    st.caption("Only privacy-minimized, opt-in analytics are used here. Geography and language groups are suppressed until at least 3 consented profiles are present.")
    try:
        metrics = BACKEND.impact_metrics()
        m1, m2, m3 = st.columns(3)
        m1.metric("Users reached", f"{VISITOR_COUNTER.value:,}", help="Cumulative app visits from the non-identifying visitor counter.")
        m2.metric("Consented analytics profiles", f"{metrics['consented_profiles']:,}")
        m3.metric("Scheme matches generated", f"{metrics['scheme_matches']:,}")
        m4, m5, m6 = st.columns(3)
        m4.metric("Potential beneficiaries identified", f"{metrics['potential_beneficiaries']:,}")
        m5.metric("Application journeys initiated", f"{metrics['application_journeys_started']:,}")
        m6.metric("Self-reported completions", f"{metrics['application_journeys_completed']:,}")

        funnel = BACKEND.journey_funnel()
        if not funnel.empty:
            st.markdown("#### Beneficiary journey funnel")
            st.bar_chart(funnel.set_index("stage"), y="users")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Geography (State/UT)")
            geo_df = BACKEND.aggregate_breakdown("state", minimum_group_size=3)
            if geo_df.empty:
                st.info("Not enough consented records to display geography safely yet.")
            else:
                st.bar_chart(geo_df.set_index("state"), y="count")
        with c2:
            st.markdown("#### Language")
            lang_df = BACKEND.aggregate_breakdown("language", minimum_group_size=3)
            if lang_df.empty:
                st.info("Not enough consented records to display language safely yet.")
            else:
                st.bar_chart(lang_df.set_index("language"), y="count")

        st.markdown("#### Need categories")
        need_df = BACKEND.aggregate_breakdown("need_category", minimum_group_size=3)
        if need_df.empty:
            st.info("Need-category groups will appear when there are enough consented records.")
        else:
            st.bar_chart(need_df.set_index("need_category"), y="count")
        st.caption("Impact metrics are product analytics, not proof of government benefit approval. Application completion is self-reported unless a future official integration verifies it.")
    except Exception as exc:
        st.error(f"Impact dashboard unavailable: {exc}")

with tab_help:
    render_project_credit()
    st.subheader("Human assistance escalation")
    st.write("When AI cannot resolve a question, create an anonymous help ticket for a future human-support workflow. Do not include names, phone numbers, Aadhaar, exact addresses, passwords, OTPs or medical records.")
    scheme_options = {"General / no scheme selected": ""}
    for scheme in BACKEND.list_schemes(include_inactive=False):
        scheme_options[scheme["name"]] = scheme["scheme_id"]
    with st.form("help_request_form"):
        help_topic = st.selectbox("Issue type", ["Eligibility clarification", "Documents", "Application steps", "Official link", "Language/voice accessibility", "Technical issue", "Other"])
        selected_scheme_name = st.selectbox("Scheme", list(scheme_options.keys()))
        help_language = st.selectbox("Preferred response language", list(LANGUAGES.keys()), key="help_language")
        help_description = st.text_area("Describe the problem without personal identifiers", max_chars=2000)
        help_consent = st.checkbox("I consent to saving this redacted help request for support follow-up and product improvement.")
        help_submit = st.form_submit_button("Create help ticket", type="primary")
    if help_submit:
        if not help_consent:
            st.error("Consent is required to save a help request.")
        elif not help_description.strip():
            st.error("Please describe the issue.")
        else:
            ticket = BACKEND.create_help_request(
                beneficiary_id=beneficiary_id() if analytics_enabled() else None,
                topic=help_topic,
                description=help_description,
                language=LANGUAGES[help_language]["code"],
                scheme_id=scheme_options[selected_scheme_name],
            )
            st.success(f"Help request created. Your reference code is **{ticket}**.")
            assistance_url = app_setting("HUMAN_ASSISTANCE_URL")
            if assistance_url:
                st.link_button("Open configured human-assistance service", assistance_url)
            else:
                st.info("No external human-assistance service is configured yet. An administrator can review this ticket in the Admin tab.")

    st.divider()
    st.subheader("Privacy center")
    st.write(
        f"Default analytics retention: **{app_setting('DATA_RETENTION_DAYS', '365')} days**. "
        "The backend stores only privacy-minimized profile bands and journey events when analytics consent is enabled."
    )
    if analytics_enabled():
        summary = BACKEND.beneficiary_summary(beneficiary_id())
        st.markdown("**Your currently stored analytics summary**")
        if summary.get("profile"):
            safe_profile = dict(summary["profile"])
            safe_profile.pop("beneficiary_id", None)
            safe_profile.pop("profile_flags_json", None)
            st.json({
                "profile_bands": safe_profile,
                "journey_events": summary["journey_events"],
                "scheme_matches": summary["scheme_matches"],
                "help_requests": summary["help_requests"],
            })
        else:
            st.info("No persisted analytics profile was found for this browser session.")
        confirm_delete = st.checkbox("I understand that deleting my stored analytics cannot be undone.", key="confirm_delete_data")
        if st.button("Delete my stored analytics", type="secondary", disabled=not confirm_delete):
            BACKEND.delete_beneficiary_data(beneficiary_id())
            st.session_state["analytics_consent"] = False
            st.session_state["analytics_consent_recorded"] = False
            st.session_state["force_analytics_off"] = True
            st.success("Stored analytics associated with this pseudonymous browser-session ID were deleted.")
            st.rerun()
    else:
        st.info("Impact analytics are currently off for this session. Scheme discovery still works without saving a beneficiary profile.")

with tab_access:
    render_project_credit()
    st.subheader("Accessibility, regional languages and WhatsApp")
    st.markdown(
        """
- **Regional languages:** the prototype offers English plus major Indian-language options, with translation adapters for text output.
- **Voice input:** users can record a short voice message; speech-to-text can be replaced with an authorized BHASHINI or audited local ASR service for production.
- **Voice output:** matched-scheme summaries can be read aloud using text-to-speech.
- **Low-literacy workflow:** the personalized questionnaire does not require the user to know a scheme name.
- **Display accessibility:** larger-text and higher-contrast switches are available in the sidebar; the UI uses native Streamlit controls for keyboard and screen-reader compatibility where possible.
- **WhatsApp:** the app link and individual scheme results can be shared through WhatsApp. The included webhook scaffold supports a future direct WhatsApp Cloud API chatbot.
"""
    )
    share_url = f"https://wa.me/?text={quote_plus('Try Adhikaar.ai: ' + APP_PUBLIC_URL)}"
    st.link_button("Share Adhikaar.ai on WhatsApp", share_url, use_container_width=True)
    st.subheader("Deployment path")
    st.write("The Streamlit app is the citizen-facing web experience. For direct WhatsApp messaging, deploy the included FastAPI webhook on a public HTTPS backend rather than using Streamlit as the webhook server.")
    st.code("uvicorn whatsapp_webhook:app --host 0.0.0.0 --port 8080")
    st.write("For iOS, the included mobile_api.py can serve as a starting API contract for a native client after production authentication, privacy and security review.")

with tab_ai:
    render_project_credit()
    st.subheader("Responsible AI architecture")
    st.markdown(
        """
1. **Voice and language layer:** speech-to-text, language detection, translation and text-to-speech use pretrained models or approved language APIs. Language models do not determine legal eligibility.
2. **Personalized discovery:** the user can provide basic profile details and a need description without knowing any scheme name. The engine searches the active admin-managed catalog.
3. **Eligibility pre-screen:** transparent rules check catalog conditions such as age, income, residence and scheme-specific flags. The output is a *potential match* or *needs review*, never an official benefits decision.
4. **ML relevance ranking:** a demonstration supervised model ranks already-plausible schemes. The bundled model uses synthetic data and must be replaced with audited, consented and representative data before production.
5. **Clustering:** groups the stated need into broad topics to organize results; it never changes eligibility.
6. **Feedback/RL concept:** an aggregate beta-bandit uses thumbs-up/down counts to improve ranking. It does not learn from raw voice, exact locations or direct identifiers.
7. **End-to-end journey:** documents, application steps and official links are surfaced from the managed scheme catalog. Application starts/completions are tracked only with opt-in analytics and completion is self-reported.
8. **Human-in-the-loop:** unresolved cases can be escalated into a redacted help-ticket queue.
"""
    )
    st.error("Do not train on or persist Aadhaar, OTPs, passwords, raw voice, precise location history, full medical records or other direct identifiers. Production use requires legal/privacy review, secure authentication, access controls, encryption, monitoring and an approved retention policy.")
    st.markdown("#### Backend data model")
    st.write("The repository includes a SQL backend with tables for privacy-minimized beneficiary profiles, consent records, scheme matches, journey events, help tickets and admin-managed schemes. SQLite is the zero-config demo backend; set DATABASE_URL to managed PostgreSQL for durable Streamlit Cloud deployments.")

with tab_admin:
    render_project_credit()
    st.subheader("Scheme management & operations")
    if not (app_setting("ADMIN_PASSWORD") or app_setting("ADMIN_PASSWORD_HASH")):
        st.warning("Admin access is disabled until ADMIN_PASSWORD_HASH (recommended) or ADMIN_PASSWORD is configured in Streamlit Secrets.")
        st.code('ADMIN_PASSWORD_HASH = "<sha256-of-a-strong-password>"')
    else:
        if not st.session_state.get("admin_authenticated", False):
            admin_candidate = st.text_input("Admin password", type="password", key="admin_password_candidate")
            if st.button("Unlock admin panel"):
                if admin_password_ok(admin_candidate):
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")
        else:
            col_logout, col_status = st.columns([1, 3])
            if col_logout.button("Lock admin panel"):
                st.session_state["admin_authenticated"] = False
                st.rerun()
            col_status.success(f"Admin unlocked · {BACKEND.database_label()}")

            admin_scheme, admin_support, admin_database = st.tabs(["Scheme manager", "Human-help queue", "Database & retention"])

            with admin_scheme:
                schemes = BACKEND.list_schemes(include_inactive=True)
                label_to_id = {f"{s['name']} ({'active' if s['active'] else 'inactive'})": s["scheme_id"] for s in schemes}
                choices = ["➕ Add a new scheme"] + list(label_to_id.keys())
                selected = st.selectbox("Select scheme", choices, key="admin_scheme_select")
                record = None if selected.startswith("➕") else BACKEND.get_scheme(label_to_id[selected])

                with st.form("scheme_admin_form"):
                    c1, c2, c3 = st.columns(3)
                    sid = c1.text_input("Scheme ID", value=(record.get("scheme_id", "") if record else ""), disabled=bool(record))
                    name = c2.text_input("Scheme name", value=(record.get("name", "") if record else ""))
                    category = c3.text_input("Category", value=(record.get("category", "General") if record else "General"))
                    state_scope = c1.text_input("State scope", value=(record.get("state_scope", "ALL") if record else "ALL"))
                    min_age = c2.text_input("Minimum age (optional)", value=(str(record.get("min_age") or "") if record else ""))
                    max_age = c3.text_input("Maximum age (optional)", value=(str(record.get("max_age") or "") if record else ""))
                    max_income = c1.text_input("Maximum income INR (optional)", value=(str(record.get("max_income") or "") if record else ""))
                    allowed_genders = c2.text_input("Allowed genders", value=(record.get("allowed_genders", "ALL") if record else "ALL"), help="Pipe-separated, e.g. Female|Male, or ALL")
                    residence_rule = c3.text_input("Residence rule", value=(record.get("residence", "ALL") if record else "ALL"))
                    marital_rule = c1.text_input("Marital statuses", value=(record.get("marital_statuses", "ALL") if record else "ALL"))
                    required_flags = c2.text_input("Required profile flags", value=(record.get("required_flags", "") if record else ""), help="Pipe-separated internal flags such as student|farmer")
                    special_rule = c3.text_input("Special rule key", value=(record.get("special_rule", "") if record else ""))
                    occupation_keywords = st.text_area("Occupation keywords", value=(record.get("occupation_keywords", "") if record else ""))
                    need_keywords = st.text_area("Need keywords", value=(record.get("need_keywords", "") if record else ""))
                    benefits = st.text_area("Benefits summary", value=(record.get("benefits", "") if record else ""))
                    documents = st.text_area("Documents (pipe-separated)", value=(record.get("documents", "") if record else ""))
                    application_steps = st.text_area("Application steps (pipe-separated)", value=(record.get("application_steps", "") if record else ""))
                    official_url = st.text_input("Official scheme information URL", value=(record.get("official_url", "https://www.myscheme.gov.in/") if record else "https://www.myscheme.gov.in/"))
                    application_url = st.text_input("Official application URL", value=(record.get("application_url", "https://www.myscheme.gov.in/") if record else "https://www.myscheme.gov.in/"))
                    official_source = st.text_input("Official source / department URL", value=(record.get("official_source", "https://www.myscheme.gov.in/") if record else "https://www.myscheme.gov.in/"))
                    last_verified = st.text_input("Last verified date (YYYY-MM-DD)", value=(record.get("last_verified", "") if record else ""))
                    verification_note = st.text_area("Verification note", value=(record.get("verification_note", "") if record else ""))
                    admin_notes = st.text_area("Admin notes", value=(record.get("admin_notes", "") if record else ""))
                    active = st.checkbox("Active in citizen discovery", value=(bool(record.get("active", True)) if record else True))
                    save_scheme = st.form_submit_button("Save scheme", type="primary")

                if save_scheme:
                    if not name.strip():
                        st.error("Scheme name is required.")
                    else:
                        payload = {
                            "scheme_id": sid.strip() or uuid.uuid4().hex,
                            "name": name.strip(),
                            "category": category.strip() or "General",
                            "state_scope": state_scope.strip() or "ALL",
                            "min_age": min_age.strip(),
                            "max_age": max_age.strip(),
                            "allowed_genders": allowed_genders.strip() or "ALL",
                            "max_income": max_income.strip(),
                            "marital_statuses": marital_rule.strip() or "ALL",
                            "residence": residence_rule.strip() or "ALL",
                            "required_flags": required_flags.strip(),
                            "occupation_keywords": occupation_keywords.strip(),
                            "need_keywords": need_keywords.strip(),
                            "documents": documents.strip(),
                            "benefits": benefits.strip(),
                            "official_url": official_url.strip(),
                            "application_url": application_url.strip(),
                            "application_steps": application_steps.strip(),
                            "official_source": official_source.strip(),
                            "last_verified": last_verified.strip(),
                            "verification_note": verification_note.strip(),
                            "special_rule": special_rule.strip(),
                            "active": active,
                            "admin_notes": admin_notes.strip(),
                        }
                        saved_id = BACKEND.upsert_scheme(payload)
                        get_engine.clear()
                        st.success(f"Scheme saved: {saved_id}")
                        st.rerun()

                st.download_button(
                    "Download scheme catalog CSV",
                    data=BACKEND.export_schemes_csv(),
                    file_name="adhikaar_ai_scheme_catalog.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with admin_support:
                tickets = BACKEND.list_help_requests(limit=200)
                if not tickets:
                    st.info("No help requests yet.")
                else:
                    ticket_labels = {f"{t['ticket_id']} · {t['status']} · {t['topic']}": t for t in tickets}
                    ticket_label = st.selectbox("Help ticket", list(ticket_labels.keys()))
                    ticket = ticket_labels[ticket_label]
                    st.write(f"**Created:** {ticket['created_at']}")
                    st.write(f"**Language:** {ticket.get('language') or 'Not specified'}")
                    st.write(f"**Scheme ID:** {ticket.get('scheme_id') or 'General'}")
                    st.text_area("Redacted issue", value=ticket["description_redacted"], disabled=True)
                    new_status = st.selectbox("Status", ["Open", "In review", "Resolved", "Closed"], index=["Open", "In review", "Resolved", "Closed"].index(ticket["status"]) if ticket["status"] in ["Open", "In review", "Resolved", "Closed"] else 0)
                    if st.button("Update ticket status"):
                        BACKEND.update_help_status(ticket["ticket_id"], new_status)
                        st.success("Ticket updated.")
                        st.rerun()

            with admin_database:
                st.write(f"**Backend type:** {BACKEND.database_label()}")
                st.write(f"**Retention window:** {app_setting('DATA_RETENTION_DAYS', '365')} days")
                if BACKEND.database_label().startswith("SQLite"):
                    st.warning("SQLite launches with zero configuration, but Streamlit Community Cloud local storage is not guaranteed to persist across redeploys/restarts. Configure DATABASE_URL with managed PostgreSQL for durable beneficiary/journey data.")
                db_metrics = BACKEND.impact_metrics()
                st.json(db_metrics)
                if st.button("Run retention cleanup now"):
                    deleted = BACKEND.purge_expired_data()
                    st.success(f"Retention cleanup finished: {deleted}")
                st.info("The admin interface intentionally exposes aggregate operations and redacted help text rather than a raw list of beneficiary profiles.")

with tab_team:
    render_project_credit()
    st.subheader("Project team and attribution")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"<div class='team-card'><h3>Author / Project Lead</h3>"
            f"<p><strong>{escape(AUTHOR_NAME)}</strong></p>"
            "<p>Leads the product concept, application design, prototype development, testing, documentation, and deployment preparation.</p></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='team-card'><h3>Mentor</h3>"
            f"<p><strong>{escape(MENTOR_NAME)}</strong></p>"
            "<p>Provides technical mentorship, responsible-AI guidance, software-engineering review, and project-development support.</p></div>",
            unsafe_allow_html=True,
        )
    st.info(
        "Government scheme descriptions, official portals, third-party language services, mapping services and open-source libraries remain subject to their respective owners, terms and licenses."
    )

st.markdown(
    "<footer class='adhikar-footer'><div class='adhikar-footer-content'>"
    "<h3 style='margin:.1rem 0 .45rem;color:white;font-family:Georgia,serif'>Adhikaar.ai</h3>"
    "<p style='margin:.2rem 0;line-height:1.55'>Discover, understand and access benefits through a privacy-aware, multilingual workflow. This prototype provides educational pre-screening only and does not make an official eligibility or benefit decision.</p>"
    f"<p style='margin:.55rem 0 0'><strong>Cumulative app users:</strong> {VISITOR_COUNTER.value:,} &nbsp; · &nbsp; <a href='https://www.myscheme.gov.in/' target='_blank'>Visit myscheme.gov.in</a></p>"
    "</div></footer>",
    unsafe_allow_html=True,
)
