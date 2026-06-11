import streamlit as st
import os
import base64
from groq import Groq
from gtts import gTTS

# --- 1. Premium Orange & White Styling ---
st.set_page_config(page_title="Nightside AI Live", page_icon="🍊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    h1 { color: #FF6B00; font-weight: 800; text-align: center; font-size: 2.8rem; }
    .status-box {
        background-color: #FFF0E6;
        border: 2px solid #FF6B00;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        color: #333333;
        font-size: 1.1rem;
    }
    .chat-card {
        background-color: #F9FAFB;
        border-left: 5px solid #FF6B00;
        padding: 12px;
        margin: 10px 0;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>🍊 Nightside Ai Voice Call</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666;'>Continuous Live Agent — Zero Buttons, No Delay Rola</p>", unsafe_allow_html=True)
st.markdown("---")

# --- 2. Security API Check ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    st.error("⚠️ Please add your GROQ_API_KEY in Streamlit Secrets.")
else:
    client = Groq(api_key=GROQ_API_KEY)

    # Browser se jo text aayega usay handle karne ke liye parameters
    query_params = st.query_params
    
    if "speech_text" in query_params:
        user_text = query_params["speech_text"]
        
        # Immediate clear to prevent loop restart
        st.query_params.clear()
        
        if user_text.strip():
            st.markdown(f"<div class='chat-card'>🗣️ **You said:** {user_text}</div>", unsafe_allow_html=True)
            
            with st.spinner("⚡ Agent is answering..."):
                try:
                    # AI Brain (Fastest Llama 3.1 Model)
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a professional live phone receptionist for Nightside Ai software agency. Keep responses extremely short, max 10 words. Speak casually and naturally."},
                            {"role": "user", "content": user_text}
                        ],
                        model="llama-3.1-8b-instant"
                    )
                    ai_response = chat_completion.choices[0].message.content
                    
                    st.markdown(f"<div class='chat-card'>🤖 **Agent:** {ai_response}</div>", unsafe_allow_html=True)
                    
                    # Unlimited Free TTS Voice
                    tts = gTTS(text=ai_response, lang='en', tld='com')
                    tts.save("response.mp3")
                    
                    with open("response.mp3", "rb") as f:
                        audio_bytes = f.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode()
                    
                    # HTML5 Autoplay Hack (Bina button ke khud bolega)
                    st.markdown(f'<audio src="data:audio/mp3;base64,{audio_base64}" autoplay="true" />', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- 3. Live Continuous Mic Component ---
    st.markdown('<div class="status-box" id="box">🎙️ System Status: Listening Continually...</div>', unsafe_allow_html=True)

    # 100% Free Browser Web Speech Injection
    st.components.v1.html("""
        <div style="text-align: center; font-family: sans-serif;">
            <p id="indicator" style="color: #FF6B00; font-weight: bold; font-size: 18px;">🔴 Click anywhere on this white screen area once to activate mic loop!</p>
        </div>
        
        <script>
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.continuous = false; // Processes block by block naturally
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            document.body.onclick = function() {
                try {
                    recognition.start();
                    document.getElementById('indicator').innerText = "🟢 Mic Active - Speak Naturally Now";
                    document.getElementById('indicator').style.color = "#10B981";
                } catch(e) {
                    // Already running
                }
            };

            // Auto trigger on load if permissions allow
            try { recognition.start(); } catch(e){}

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                
                // Inject text back into Streamlit URL safely without CORS break
                const url = new window.parent.URL(window.parent.location.href);
                url.searchParams.set('speech_text', transcript);
                window.parent.location.href = url.toString();
            };

            recognition.onend = function() {
                // Restart listening automatically loop
                setTimeout(() => { recognition.start(); }, 400);
            };
        </script>
    """, height=120)
