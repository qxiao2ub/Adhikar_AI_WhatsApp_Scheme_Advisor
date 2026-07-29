from __future__ import annotations

import io
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from gtts import gTTS

from core_engine import UserProfile, load_default_engine, redact_sensitive_text

PROJECT_DIR = Path(__file__).resolve().parent
AUTHOR_NAME = os.getenv("APP_AUTHOR", "Praneel")
APP_NAME = os.getenv("APP_NAME", "Sahayak AI Scheme Advisor")
APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", "https://your-app-name.streamlit.app")

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

st.set_page_config(page_title=APP_NAME, page_icon="🇮🇳", layout="wide")
st.markdown("""
<style>
.main {background: linear-gradient(180deg, #fffdf6 0%, #f6fbff 100%);} 
.hero {padding: 1.2rem 1.4rem; border-radius: 18px; background: linear-gradient(120deg,#ffefe0,#eef8ff); border:1px solid #e8e8e8;}
.scheme-card {padding: 1rem 1.1rem; border:1px solid #dedede; border-radius:16px; margin-bottom:1rem; background:white;}
.small-note {font-size:.86rem; color:#555;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_engine():
    return load_default_engine(PROJECT_DIR)

engine = get_engine()


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
        geo = Nominatim(user_agent="sahayak-ai-scheme-advisor-prototype")
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
    st.title("🇮🇳 Sahayak AI")
    st.caption("Multilingual government-scheme discovery prototype")
    st.markdown(f"**Author / project lead:** {AUTHOR_NAME}")
    st.markdown("**Data policy:** session processing; no intentional raw-audio or precise-location retention.")
    st.warning("Never enter Aadhaar numbers, bank passwords, OTPs, or full medical records.")
    share_url = f"https://wa.me/?text={quote_plus('Try the Sahayak AI Scheme Advisor: ' + APP_PUBLIC_URL)}"
    st.link_button("Share app link on WhatsApp", share_url, use_container_width=True)

st.markdown(f"<div class='hero'><h1>{APP_NAME}</h1><p>Voice + text scheme discovery in Indian languages, with transparent pre-screening and official verification.</p></div>", unsafe_allow_html=True)

tab_advisor, tab_nearby, tab_ai, tab_deploy = st.tabs(["💬 Scheme advisor", "📍 Nearby services", "🧠 How the AI works", "🚀 WhatsApp & deployment"])

with tab_advisor:
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
    st.subheader("Phase 1: link sharing on WhatsApp")
    st.write("Deploy this repository on Streamlit Community Cloud, set APP_PUBLIC_URL in secrets, and share the generated link through WhatsApp.")
    st.subheader("Phase 2: direct WhatsApp chatbot")
    st.write("Use the included FastAPI webhook scaffold on a public HTTPS backend. Streamlit Community Cloud is for the web UI; it is not the recommended webhook host.")
    st.code("uvicorn whatsapp_webhook:app --host 0.0.0.0 --port 8080")
    st.subheader("Phase 3: iOS")
    st.write("Use the included mobile_api.py as the backend contract for a native SwiftUI client. Add a privacy policy, consent, deletion workflow, accessibility testing, and App Store metadata before review.")
    st.info("The notebook also generates README.md, PRIVACY.md, COPYRIGHT_CHECKLIST.md, tests, and a GitHub-ready ZIP.")
