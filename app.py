import os
from google.cloud import speech
import time
import streamlit as st
import requests
import json
import matplotlib.pyplot as plt
from io import StringIO
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
import requests
import tempfile





if "show_extractor" not in st.session_state:
    st.session_state.show_extractor = False

def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_ai = load_lottie_url("https://assets4.lottiefiles.com/packages/lf20_u4yrau.json")
lottie_docs = load_lottie_url("https://assets6.lottiefiles.com/packages/lf20_touohxv0.json")

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
    ...
}

}
.left-block {
    flex: 1;
}
.right-block {
    flex: 1.1;
    padding-left: 2vw;
}
.title {
    font-size: 3.2em;
    font-weight: bold;
    color: white;
    margin-bottom: 0.5rem;
}
.subtitle {
    color: #c9d1d9;
    font-size: 1.1em;
    margin-bottom: 2rem;
}
.stButton > button {
    font-size: 1.1em;
    background-color: #00CFFF;
    color: black;
    border-radius: 8px;
    padding: 10px 30px;
    box-shadow: 0 0 20px #00CFFF;
    transition: 0.3s ease-in-out;
}
.stButton > button:hover {
    background-color: #0ff;
    transform: scale(1.05);
}



</style>
""", unsafe_allow_html=True)

# --- Welcome Section ---
if not st.session_state.show_extractor:
    st.markdown("""
        <style>
            .logo {
                margin-bottom: -10px;
            }
        </style>
    """, unsafe_allow_html=True)

    # Logo at top
    st.image("formsiq-logo.png", width=50)

    st.markdown("""
    <div class="centered-container" style="padding-top: 16px;">
""", unsafe_allow_html=True)


    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown('<div class="title">Welcome to <span style="color:#00E0FF;">FormsiQ</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">GenAI-powered 1003 field extraction from call transcripts — no more manual data entry.</div>', unsafe_allow_html=True)
        
        if st.button("Get Started", key="start"):
            st.session_state.show_extractor = True
            st.rerun()

    with col2:
        st.markdown("<h2 style='font-size: 40px; font-weight: 800;'>Proven performance at scale.</h2>", unsafe_allow_html=True)

        st.caption("Gen AI-powered processing for millions of mortgage transcripts — reliably and fast.")
        st.markdown("### Example Transcript")
        with st.expander("See Example"):
            st.code(
                "Hi, I'm Sarah Thompson. I'd like to apply for a $400,000 loan to purchase a single family home at 789 Maple Drive.",
                language="markdown",
            )

        st.markdown("---")

        colx1, colx2 = st.columns(2)
        with colx1:
            st.markdown("#### 📞 300+")
            st.caption("Call transcripts parsed")

        with colx2:
            st.markdown("#### 🧾 1,000+")
            st.caption("Mortgage field entries auto-filled")

        colx3, colx4 = st.columns(2)
        with colx3:
            st.markdown("#### ⚡ < 10 sec")
            st.caption("Avg. processing time")

        with colx4:
            st.markdown("#### 🔐 SOC 2 Ready")
            st.caption("Security-first by design")

        st.markdown("#### 🎯 98%+")
        st.caption("Accuracy in field extraction")

    st.markdown('</div>', unsafe_allow_html=True)




# --- Extractor Section ---
if st.session_state.show_extractor:     

   
    st.sidebar.header("Summary")
    st.markdown("""
    <div class="custom-success-box">
    🔹 <b>Note:</b> 🔒 Privacy First - Transcripts are processed securely. No data is stored or shared.
    </div>
    """, unsafe_allow_html=True)

    st.title("FormsiQ – 1003 Transcript Extractor")
    st.markdown("Paste a call transcript below to extract key 1003 loan application fields with confidence scores.")

    if "transcript" not in st.session_state:
        st.session_state.transcript = ""
    if "results" not in st.session_state:
        st.session_state.results = []

    def clear_results_only():
        st.session_state.results = []

    import random

    def clear_everything():
        keys_to_clear = ["transcript", "results", "response_time","audio_transcribed","audio_upload"]

        for key in keys_to_clear:
            st.session_state.pop(key, None)

        # 🔄 Force uploader to reset visually by changing its key
        st.session_state.uploader_key = str(random.randint(1, 1_000_000))
    method_options = ["Paste Text", "Upload File", "Upload Audio"]
    method = st.radio("Choose input method:", method_options)



    if method == "Paste Text":
        st.text_area("Transcript Input", key="transcript", height=250, placeholder='Type your transcript...')

    elif method == "Upload File":
        uploaded_file = st.file_uploader("Upload Transcript File", type=["txt"], key=st.session_state.get("uploader_key", "upload_file"))
        if uploaded_file:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            st.session_state.transcript = f'"{stringio.read().strip()}"'
            st.text_area("File Content Preview", value=st.session_state.transcript, height=250, disabled=True)
    
    
    elif method == "Upload Audio":
        audio_file = st.file_uploader("Upload Call Audio", type=["wav", "mp3", "m4a"], key=st.session_state.get("uploader_key", "audio_upload"))


        if audio_file is not None:
            if not st.session_state.get("audio_transcribed"):

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
                    st.session_state.audio_transcribed = True  # ✅ flag that transcription happened
                    st.success("Transcription complete!")

                except Exception as e:
                    st.error(f"❌ Transcription failed: {e}")

        # Always show preview
        st.text_area("Transcript Preview", value=st.session_state.transcript, height=200, disabled=True)

    
    col1, col2, col3 = st.columns(3)

    if col1.button("Extract Fields"):
        transcript = st.session_state.transcript.strip()
        if not transcript or len(transcript) < 20:
            st.warning("⚠️ Please enter a valid call transcript with more meaningful content.")
            st.session_state.results = []  # Clear previous results
            st.stop() 
        else:
            start_time = time.time()
            with st.spinner("Analyzing transcript..."):
                try:
                    response = requests.post("https://formsiq-1003-extractor-production.up.railway.app", json={"transcript": transcript})
                    end_time = time.time()
                    st.session_state.response_time = round(end_time - start_time, 2)
                    if response.status_code == 200:
                        st.session_state.results = response.json()["response"].get("fields", [])
                        if not st.session_state.results:
                            st.info("🤖 We didn’t find any extractable information. Please try again with a more complete transcript.")
                            st.session_state.results = []  # Clear previous results
                        else:
                            components.html("""
                                <script>
                                    setTimeout(() => {
                                        const target = window.parent.document.getElementById("extract-results");
                                        if (target) {
                                            target.scrollIntoView({ behavior: "smooth", block: "start" });
                                        }
                                    }, 300);
                                </script>
                            """, height=1)
                    else:
                        st.error("❌ Something went wrong with the API. Please try again.")
                except Exception:
                    st.error("❌ Couldn’t extract data. Try again with a better transcript.")
                    st.session_state.results = []  # Clear previous results

    if col2.button("Clear Results"):
        clear_results_only()

    if col3.button("New Transcript"):
        clear_everything()
        st.rerun()

    st.markdown("<div id='extract-results'></div>", unsafe_allow_html=True)

    if st.session_state.results:
        st.markdown("<div class='custom-success-box'>🎉 Fields extracted successfully!</div>", unsafe_allow_html=True)
        st.markdown("### Extracted Information")

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

        st.sidebar.markdown(f"""
        <div class='sidebar-box'>
        ✅ Fields Extracted: {len(st.session_state.results)}
        </div>
        """, unsafe_allow_html=True)
        if (
            "response_time" in st.session_state and 
            st.session_state.response_time is not None and 
            st.session_state.get("input_method") != "Upload Audio"
       ):
            st.sidebar.markdown(f"""
            <div class='sidebar-box'>
            ⏱️Response Time: {st.session_state.response_time} sec
            </div>
            """, unsafe_allow_html=True)


