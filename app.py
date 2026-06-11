import streamlit as st
import os
import asyncio
from groq import Groq
import edge_tts

st.set_page_config(page_title="Nightside AI Agent", page_icon="🤖")

st.title("🤖 Nightside AI Voice Agent")
st.write("Professional Voice Assistant Service")

# Streamlit Cloud ke Secrets se API key uthayega
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    st.warning("⚠️ Please add your GROQ_API_KEY in Streamlit Secrets to activate the AI.")
else:
    client = Groq(api_key=GROQ_API_KEY)
    
    # Streamlit ka apna inbuilt Audio Input Recorder
    audio_value = st.audio_input("Record your voice here")
    
    if audio_value:
        st.write("🎙️ Audio received! Processing...")
        
        # Audio ko save karna temporary
        with open("input_audio.wav", "wb") as f:
            f.write(audio_value.read())
            
        try:
            # 1. Transcribe (Speech to Text) using Groq Whisper
            with open("input_audio.wav", "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                )
            
            user_text = transcription.text
            st.write(f"**You said:** {user_text}")
            
            # 2. Get AI Brain Response (Llama 3)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional business voice receptionist. Keep responses short and friendly."},
                    {"role": "user", "content": user_text}
                ],
                model="llama-3.1-8b-instant",
            )
            
            ai_response = chat_completion.choices[0].message.content
            st.write(f"**Agent Response:** {ai_response}")
            
            # 3. Text to Speech (Edge TTS)
            output_audio = "response.mp3"
            asyncio.run(edge_tts.Communicate(ai_response, "en-US-ChristopherNeural").save(output_audio))
            
            # Play Audio on Streamlit
            st.audio(output_audio)
            
        except Exception as e:
            st.error(f"Error during processing: {e}")
