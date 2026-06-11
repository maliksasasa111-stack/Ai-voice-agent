import streamlit as st
import os
import json
import base64
from groq import Groq
from gtts import gTTS

# Page styling & Premium Orange/White Theme
st.set_page_config(page_title="Nightside AI Realtime", page_icon="🍊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    h1 { color: #FF6B00; font-weight: 800; text-align: center; }
    .status-box {
        background-color: #FFF0E6;
        border: 2px solid #FF6B00;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        color: #333333;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>🍊 Nightside Ai Continuous Live Call</h1>", unsafe_allow_html=True)
st.write("This system uses continuous streaming. No buttons to click after starting!")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    st.error("Please add your GROQ_API_KEY in Streamlit Secrets.")
else:
    client = Groq(api_key=GROQ_API_KEY)

    # Simple session state to keep track of conversation
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content": "You are a live phone voice agent for Nightside Ai. Keep responses extremely short, under 10 words. Speak naturally."}
        ]

    # Query params to handle background data transmission from HTML5 to Streamlit
    query_params = st.query_params
    if "user_audio_text" in query_params:
        user_text = query_params["user_audio_text"]
        
        # Clear the param so it doesn't loop
        st.query_params.clear()
        
        # Process through Groq
        st.session_state.chat_history.append({"role": "user", "content": user_text})
        
        try:
            chat_completion = client.chat.completions.create(
                messages=st.session_state.chat_history,
                model="llama-3.1-8b-instant"
            )
            ai_response = chat_completion.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            
            st.write(f"🗣️ **You:** {user_text}")
            st.write(f"🤖 **Agent:** {ai_response}")
            
            # Generate Free TTS
            tts = gTTS(text=ai_response, lang='en', tld='com')
            tts.save("response.mp3")
            
            with open("response.mp3", "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
            # Autoplay response back to user
            st.markdown(f'<audio src="data:audio/mp3;base64,{audio_base64}" autoplay="true" />', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error: {e}")

    # --- THE MAGIC TEXT/HTML INTERFACE FOR CONTINUOUS MIC ---
    st.markdown('<div class="status-box">🎙️ System Status: Continuous Listening Active</div>', unsafe_allow_html=True)

    # HTML5 Web Speech API Component (100% Free, handles continuous mic activation)
    st.components.v1.html("""
        <div style="text-align: center; margin-top: 20px;">
            <p id="mic-indicator" style="color: #FF6B00; font-weight: bold;">🔴 Listening... Speak now without pressing buttons.</p>
        </div>
        
        <script>
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = function() {
                document.getElementById('mic-indicator').innerText = "🟢 Mic Live - Speak Naturally";
                document.getElementById('mic-indicator').style.color = "#00cc44";
            };

            recognition.onresult = function(event) {
                const resultIndex = event.resultIndex;
                const transcript = event.results[resultIndex][0].transcript;
                
                // Stream data straight into Streamlit URL parameters to force update
                const url = new URL(window.parent.location.href);
                url.searchParams.set('user_audio_text', transcript);
                window.parent.location.href = url.toString();
            };

            recognition.onend = function() {
                // Keep the mic alive automatically forever (Continuous Loop)
                recognition.start();
            };

            // Automatically start microphone on page load
            recognition.start();
        </script>
    """, height=100)
