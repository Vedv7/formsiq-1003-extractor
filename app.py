import os
import streamlit as st
import json
from google.cloud import speech
import time
import requests
import matplotlib.pyplot as plt
from io import StringIO
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
import requests

# --- Credential Setup ---
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "audio_transcribed" not in st.session_state:
    st.session_state.audio_transcribed = False
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = "audio_upload"

# ✅ Fixed: write secret correctly
with open("temp_gcp_key.json", "w") as f:
    f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])  # no json.dump, use f.write

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "temp_gcp_key.json"

# --- Streamlit App ---
st.set_page_config(page_title="FormsiQ Extractor", layout="wide")

if "show_extractor" not in st.session_state:
    st.session_state.show_extractor = False

def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_ai = load_lottie_url("https://assets4.lottiefiles.com/packages/lf20_u4yrau.json")
lottie_docs = load_lottie_url("https://assets6.lottiefiles.com/packages/lf20_touohxv0.json")

# --- Your CSS (unchanged) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700&display=swap');
html, body {
    overflow-x: hidden !important;
    width: 100%;
    max-width: 100vw;
    box-sizing: border-box;
}
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
section.main > div {
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(20px);
    padding: 2rem;
    border-radius: 20px;
    box-shadow: 0 0 25px rgba(0,0,0,0.2);
}
.stTextArea textarea {
    background-color: rgba(255,255,255,0.07);
    color: white;
    border-radius: 10px;
    border: 1px solid #555;
}
.field-card {
    background-color: rgba(255, 255, 255, 0.05);
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 15px;
    border-left: 5px solid #00e5ff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
.confidence-high { color: #4caf50; }
.confidence-medium { color: #ffb300; }
.confidence-low { color: #e53935; }
.stButton > button, .stDownloadButton > button {
    all: unset;
    background-color: #007c91;
    color: white !important;
    padding: 10px 24px;
    font-weight: bold;
    border-radius: 10px;
    text-align: center;
    cursor: pointer;
    transition: 0.2s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background-color: #00acc1;
}
.custom-success-box {
    background: rgba(0,124,145, 0.12);
    backdrop-filter: blur(6px);
    padding: 15px;
    border-radius: 10px;
    color: #00e6ff;
    font-weight: bold;
    margin: 1rem 0;
}
.sidebar-box {
    background-color: rgba(0, 188, 212, 0.1);
    padding: 15px;
    border-radius: 12px;
    border-left: 4px solid #00e5ff;
    color: #e0f7fa;
    margin-top: 1rem;
    font-weight: bold;
}
.centered-container {
    width: 100%;
    max-width: 100vw;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# --- Welcome Page ---
if not st.session_state.show_extractor:
    st.image("formsiq-logo.png", width=50)
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.title("Welcome to FormsiQ")
        st.markdown("GenAI-powered 1003 field extraction from call transcripts — no more manual data entry.")

        if st.button("Get Started", key="start"):
            st.session_state.show_extractor = True
            st.rerun()

    with col2:
        st.subheader("Proven performance at scale.")
        st.caption("Gen AI-powered processing for millions of mortgage transcripts.")
        with st.expander("Example Transcript"):
            st.code(
                "Hi, I'm Sarah Thompson. I'd like to apply for a $400,000 loan to purchase a single family home at 789 Maple Drive.",
                language="markdown",
            )

# --- Extractor Section ---
if st.session_state.show_extractor:

    st.sidebar.header("Summary")
    st.title("FormsiQ – 1003 Transcript Extractor")
    st.markdown("Paste a call transcript below to extract key 1003 loan application fields with confidence scores.")

    if "results" not in st.session_state:
        st.session_state.results = []

    def clear_results_only():
        st.session_state.results = []

    def clear_everything():
        keys_to_clear = ["transcript", "results", "response_time","audio_transcribed","audio_upload"]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        st.session_state.uploader_key = str(random.randint(1, 1_000_000))

    method = st.radio("Choose input method:", ["Paste Text", "Upload File", "Upload Audio"])
    st.session_state.input_method = method

    if method == "Paste Text":
        st.text_area("Transcript Input", key="transcript", height=250, placeholder='Type your transcript...')

    elif method == "Upload File":
        uploaded_file = st.file_uploader("Upload Transcript File", type=["txt"], key=st.session_state.get("uploader_key", "upload_file"))
        if uploaded_file:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            st.session_state.transcript = f'"{stringio.read().strip()}"'
            st.text_area("File Content Preview", value=st.session_state.transcript, height=250, disabled=True)

    elif method == "Upload Audio":
        audio_file = st.file_uploader("Upload Call Audio", type=["wav", "mp3", "m4a"], key=st.session_state.uploader_key)
        if audio_file is not None and not st.session_state.get("audio_transcribed"):

            def transcribe_audio(file):
                client = speech.SpeechClient()
                content = file.read()
                audio = speech.RecognitionAudio(content=content)
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                    language_code="en-US"
                )
                response = client.recognize(config=config, audio=audio)
                return " ".join([result.alternatives[0].transcript for result in response.results])

            try:
                st.info("Transcribing audio...")
                transcript = transcribe_audio(audio_file)
                st.session_state.transcript = transcript
                st.session_state.audio_transcribed = True
                st.success("Transcription complete!")
            except Exception as e:
                st.error(f"❌ Transcription failed: {e}")

        st.text_area("Transcript Preview", value=st.session_state.transcript, height=200, disabled=True)

    col1, col2, col3 = st.columns(3)

    if col1.button("Extract Fields"):
        transcript = st.session_state.transcript.strip()
        if not transcript or len(transcript) < 20:
            st.warning("⚠️ Please enter a valid call transcript with more meaningful content.")
            st.session_state.results = []
        else:
            start_time = time.time()
            with st.spinner("Analyzing transcript..."):
                try:
                    response = requests.post("https://formsiq-1003-extractor.onrender.com/extract-fields", json={"transcript": transcript})
                    end_time = time.time()
                    st.session_state.response_time = round(end_time - start_time, 2)
                    if response.status_code == 200:
                        st.session_state.results = response.json()["response"].get("fields", [])
                        if not st.session_state.results:
                            st.info("🤖 No extractable information found.")
                    else:
                        st.error("❌ API call failed.")
                except Exception:
                    st.error("❌ Extraction error.")
                    st.session_state.results = []

    if col2.button("Clear Results"):
        clear_results_only()

    if col3.button("New Transcript"):
        clear_everything()
        st.rerun()

    if st.session_state.results:
        st.success("🎉 Fields extracted successfully!")
        for field in st.session_state.results:
            confidence = field['confidence_score']
            color_class = (
                "confidence-high" if confidence >= 0.9 else
                "confidence-medium" if confidence >= 0.7 else
                "confidence-low"
            )
            st.markdown(f"""
            <div class='field-card'>
                <strong>{field['field_name']}</strong><br>
                {field['field_value']}<br>
                <span class='{color_class}'><strong>Confidence:</strong> {confidence:.2f}</span>
            </div>
            """, unsafe_allow_html=True)

        json_output = json.dumps(st.session_state.results, indent=2)
        st.download_button("Download JSON", data=json_output, file_name="extracted_fields.json", mime="application/json")

