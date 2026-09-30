from __future__ import annotations

import base64
import io
import json
import os
import tempfile
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
from visitor_counter import CounterSnapshot, increment_counter

PROJECT_DIR = Path(__file__).resolve().parent
AUTHOR_NAME = os.getenv("APP_AUTHOR", "Praneel Bembey")
MENTOR_NAME = os.getenv("APP_MENTOR", "Dr. Qingyang Xiao")
APP_NAME = os.getenv("APP_NAME", "Adhikar AI Scheme Advisor")
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
def get_engine():
    return load_default_engine(PROJECT_DIR)

engine = get_engine()
VISITOR_COUNTER = get_or_increment_visitor_count()


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
        geo = Nominatim(user_agent="adhikar-ai-scheme-advisor-prototype")
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
        "<h2>Adhikar AI</h2>"
        "<p>Government support, made easier to find</p>"
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
    st.markdown("**Data policy:** session processing; no intentional raw-audio or precise-location retention.")
    st.warning("Never enter Aadhaar numbers, bank passwords, OTPs, or full medical records.")
    share_url = f"https://wa.me/?text={quote_plus('Try the Adhikar AI Scheme Advisor: ' + APP_PUBLIC_URL)}"
    st.link_button("Share app link on WhatsApp", share_url, use_container_width=True)
    st.link_button("Open official myScheme", "https://www.myscheme.gov.in/", use_container_width=True)

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
    f"<div class='adhikar-wordmark'><span class='adhikar-mark'>A</span><strong>Adhikar</strong></div>"
    f"<div class='adhikar-top-meta'>Private · multilingual · transparent pre-screening<br>"
    f"Author: {escape(AUTHOR_NAME)} · Mentor: {escape(MENTOR_NAME)}</div>"
    f"</div>"
    f"<section class='adhikar-home-hero'>"
    f"<div><div class='adhikar-eyebrow'>13 Indian languages · voice supported</div>"
    f"<h1>Find government support that may be right for you.</h1>"
    f"<p class='lead'>Answer a few optional questions, describe your needs in your own language, and discover government schemes worth checking. Adhikar explains why each result appeared, what documents may be needed, and where to verify the official rules.</p>"
    f"<span class='adhikar-app-name'>{escape(APP_NAME)}</span></div>"
    f"<figure class='adhikar-hero-photo'>{hero_html}<figcaption class='adhikar-photo-caption'>UI adapted from the attached Adhikar Lovable design source.</figcaption></figure>"
    f"</section>",
    unsafe_allow_html=True,
)

st.markdown(
    "<section class='adhikar-section'><div class='adhikar-eyebrow'>Why Adhikar</div>"
    "<h2>Government support should not be hard to find.</h2>"
    "<p>Welfare information can be scattered across websites, languages, eligibility rules and application procedures. This prototype brings discovery, explanation and official verification links into one simpler workflow.</p></section>"
    "<div class='adhikar-steps'>"
    "<div class='adhikar-step'><div class='num'>01</div><h3>Tell us about yourself</h3><p>Answer only the optional questions relevant to your situation and describe the support you need.</p></div>"
    "<div class='adhikar-step'><div class='num'>02</div><h3>Discover relevant schemes</h3><p>Transparent rules and ML relevance ranking surface schemes that may be worth checking.</p></div>"
    "<div class='adhikar-step'><div class='num'>03</div><h3>Understand your options</h3><p>Review benefits, documents, possible mismatches, nearby help and official verification links.</p></div>"
    "</div>",
    unsafe_allow_html=True,
)

tab_advisor, tab_nearby, tab_ai, tab_deploy, tab_team = st.tabs([
    "Find schemes",
    "Nearby help",
    "How the AI works",
    "WhatsApp & deployment",
    "Project team",
])

with tab_advisor:
    render_project_credit()
    language_name = st.selectbox("Preferred language", list(LANGUAGES.keys()))
    lang_code = LANGUAGES[language_name]["code"]
    locale = LANGUAGES[language_name]["locale"]
    st.info(local_ui(lang_code, "welcome"))
    st.warning(local_ui(lang_code, "disclaimer"))
    consent = st.checkbox(local_ui(lang_code, "consent"))
    external_processing = st.checkbox("Allow the transcript and generated summary to be sent to a configured translation/voice service for this session.")

    with st.form("profile_form"):
        c1, c2, c3 = st.columns(3)
        age = c1.number_input("Age", min_value=0, max_value=120, value=25)
        income_known = c2.checkbox("I know annual household income", value=False)
        annual_income = c2.number_input("Annual household income (INR)", min_value=0.0, value=0.0, step=10000.0, disabled=not income_known)
        gender = c3.selectbox("Gender", ["Prefer not to say", "Female", "Male", "Transgender", "Other"])
        marital_status = c1.selectbox("Marital status", ["Prefer not to say", "Single", "Married", "Widowed", "Divorced", "Separated"])
        state = c2.text_input("State / Union Territory")
        residence = c3.selectbox("Residence", ["Prefer not to say", "Urban", "Rural"])
        social_category = c1.selectbox("Social category (optional; only used when a scheme explicitly requires it)", ["Prefer not to say", "General", "OBC", "SC", "ST", "Other"])

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

        typed_need = st.text_area("Describe what support you need in your language", placeholder="Example: I need help paying for hospital treatment or finding a scholarship.")
        audio_value = st.audio_input("Or record a short voice message") if hasattr(st, "audio_input") else st.file_uploader("Upload a WAV voice message", type=["wav"])
        submitted = st.form_submit_button("Find potential schemes", type="primary", use_container_width=True)

    if submitted:
        if not consent:
            st.error("Consent is required before processing this session.")
        else:
            transcript = typed_need.strip()
            if audio_value is not None:
                audio_bytes = audio_value.getvalue()
                recognized, asr_note = transcribe_wav(audio_bytes, locale)
                if recognized:
                    transcript = (transcript + " " + recognized).strip()
                    st.success(f"Voice transcript: {recognized}")
                else:
                    st.warning(asr_note)

            safe_transcript = redact_sensitive_text(transcript)
            english_need = basic_keyword_normalize(safe_transcript)
            if lang_code != "en" and external_processing and safe_transcript:
                english_need = external_translate(safe_transcript, lang_code, "en")

            profile = UserProfile(
                age=int(age), annual_income=float(annual_income) if income_known else None,
                gender=gender, marital_status=marital_status, state=state.strip(), residence=residence,
                social_category=social_category, student=student, pregnant=pregnant,
                disability=disability, entrepreneur=entrepreneur, street_vendor=street_vendor,
                farmer=farmer, housing_need=housing_need, bank_account=bank_account,
                need_text=english_need,
            )
            results = engine.recommend(profile, top_k=6)
            st.session_state["last_results"] = results
            st.session_state["lang_code"] = lang_code
            st.session_state["external_processing"] = external_processing
            st.session_state["need_cluster"] = engine.need_cluster(english_need)

    results = st.session_state.get("last_results", [])
    if results:
        st.subheader(local_ui(st.session_state.get("lang_code", "en"), "potential"))
        st.caption(f"Need cluster for recommendation organization only: {st.session_state.get('need_cluster', 'General discovery')}. It does not determine eligibility.")
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
                with st.expander(local_ui(st.session_state.get("lang_code", "en"), "documents")):
                    for doc in item["documents"]:
                        st.write("• " + doc)
                st.caption(item["verification_note"])
                st.info(item["official_search_hint"])
                a, b, c, d = st.columns(4)
                a.link_button("Open official myScheme", item["official_url"], use_container_width=True)
                b.link_button("Share on WhatsApp", f"https://wa.me/?text={item['share_text']}", use_container_width=True)
                if c.button("👍 Helpful", key=f"up_{item['scheme_id']}", use_container_width=True):
                    engine.record_feedback(item["scheme_id"], True); st.toast("Aggregate feedback recorded")
                if d.button("👎 Not helpful", key=f"down_{item['scheme_id']}", use_container_width=True):
                    engine.record_feedback(item["scheme_id"], False); st.toast("Aggregate feedback recorded")

                summary_en = f"Potential match: {item['name']}. {item['benefits']} This is not a final eligibility decision. Verify on the official myScheme portal."
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
    st.caption("Browser location is used only in the current session. You can use a district, city, or PIN code instead.")
    components.html("""
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
    """, height=95)

    place = st.text_input("Or enter city, district, State, or PIN code", placeholder="Example: Pune, Maharashtra")
    lat_q = st.query_params.get("lat")
    lon_q = st.query_params.get("lon")
    coords = None
    label = ""
    if lat_q and lon_q:
        try:
            coords = (float(lat_q), float(lon_q)); label = "Browser-provided current location"
        except Exception:
            coords = None
    if st.button("Search near entered place", use_container_width=True) and place:
        found = geocode_place(place)
        if found:
            coords = (found[0], found[1]); label = found[2]
            st.session_state["manual_coords"] = coords
            st.session_state["manual_label"] = label
        else:
            st.error("Could not locate that place. Try a city plus State or a PIN code.")
    if coords is None and "manual_coords" in st.session_state:
        coords = st.session_state["manual_coords"]; label = st.session_state.get("manual_label", "Entered location")

    if coords:
        st.success(f"Searching around: {label}")
        data = nearby_services(coords[0], coords[1])
        map_df = pd.DataFrame([{"lat": coords[0], "lon": coords[1], "name": "Your search location"}] + data)
        st.map(map_df, latitude="lat", longitude="lon", size=70)
        if data:
            for item in data:
                maps = f"https://www.google.com/maps/search/?api=1&query={item['lat']},{item['lon']}"
                st.markdown(f"**{item['name']}** — {item['type']} — approximately {item['distance_km']} km  ")
                st.link_button("Open map", maps, key=f"map_{item['lat']}_{item['lon']}")
        else:
            st.warning("Live open-map search was unavailable. Use the map-search links below.")
        gov_maps = f"https://www.google.com/maps/search/government+office/@{coords[0]},{coords[1]},13z"
        health_maps = f"https://www.google.com/maps/search/government+hospital/@{coords[0]},{coords[1]},13z"
        c1, c2 = st.columns(2)
        c1.link_button("Search nearby government offices", gov_maps, use_container_width=True)
        c2.link_button("Search nearby government hospitals", health_maps, use_container_width=True)

with tab_ai:
    render_project_credit()
    st.subheader("Responsible AI architecture")
    st.markdown("""
1. **Voice and language layer (deep learning/NLP):** speech-to-text, language detection, translation, and text-to-speech use pretrained models or approved language APIs. Clustering is not translation.
2. **Eligibility pre-screen (transparent rules):** age, income, residence, and program-specific answers are checked against an approved scheme catalog. This is the only layer allowed to produce a pre-screen status.
3. **Supervised ML ranker:** a demonstration model ranks which already-plausible schemes are likely relevant. The included model uses synthetic data and must be replaced with audited, consented data before production.
4. **Clustering:** groups the user’s stated need into broad topics only to organize results. It never changes eligibility.
5. **Reinforcement-learning concept:** an aggregate beta-bandit uses thumbs-up/down counts to reorder helpful results. It stores no profile, phone number, raw voice, or location history.
6. **Human and official verification:** the final decision remains with myScheme and the responsible government authority.
""")
    st.error("Do not train on raw voice, Aadhaar, OTPs, precise location history, caste, religion, health records, or WhatsApp identifiers without a lawful purpose, explicit notice, strong security, and an approved retention policy.")

with tab_deploy:
    render_project_credit()
    st.subheader("Phase 1: link sharing on WhatsApp")
    st.write("Deploy this repository on Streamlit Community Cloud, set APP_PUBLIC_URL in secrets, and share the generated link through WhatsApp.")
    st.subheader("Phase 2: direct WhatsApp chatbot")
    st.write("Use the included FastAPI webhook scaffold on a public HTTPS backend. Streamlit Community Cloud is for the web UI; it is not the recommended webhook host.")
    st.code("uvicorn whatsapp_webhook:app --host 0.0.0.0 --port 8080")
    st.subheader("Phase 3: iOS")
    st.write("Use the included mobile_api.py as the backend contract for a native SwiftUI client. Add a privacy policy, consent, deletion workflow, accessibility testing, and App Store metadata before review.")
    st.info("This repository includes README.md, PRIVACY.md, COPYRIGHT_CHECKLIST.md, tests, and Streamlit Cloud deployment files.")

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
        "The names above identify the student author/project lead and mentor for this prototype. "
        "Government scheme descriptions, myScheme materials, third-party services, and open-source libraries remain subject to their respective owners and licenses."
    )



st.markdown(
    "<footer class='adhikar-footer'><div class='adhikar-footer-content'>"
    "<h3 style='margin:.1rem 0 .45rem;color:white;font-family:Georgia,serif'>Adhikar AI Scheme Advisor</h3>"
    "<p style='margin:.2rem 0;line-height:1.55'>This prototype provides educational pre-screening only. It does not make an official eligibility decision. Verify every result with the responsible authority and the official myScheme portal.</p>"
    f"<p style='margin:.55rem 0 0'><strong>Cumulative app users:</strong> {VISITOR_COUNTER.value:,} &nbsp; · &nbsp; <a href='https://www.myscheme.gov.in/' target='_blank'>Visit myscheme.gov.in</a></p>"
    "</div></footer>",
    unsafe_allow_html=True,
)
