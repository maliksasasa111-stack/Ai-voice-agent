import os
import json
import asyncio
from flask import Flask, request, jsonify, send_file, render_template_string
from groq import Groq
import edge_tts

app = Flask(__name__)

# -------------------------------------------------------------
# HARDCODED CONFIGURATION
# -------------------------------------------------------------
GROQ_API_KEY = "GROQ_API_KEY"  # <-- Apni actual Groq API key yahan likhein
client = Groq(api_key=GROQ_API_KEY)

# -------------------------------------------------------------
# FRONTEND UI (Embedded directly in Flask)
# -------------------------------------------------------------
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nightside AI - Voice Automation Engine</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .glow-active { animation: modern-pulse 1.8s infinite ease-in-out; }
        @keyframes modern-pulse {
            0% { transform: scale(0.96); box-shadow: 0 0 0 0 rgba(249, 115, 22, 0.6); }
            70% { transform: scale(1.04); box-shadow: 0 0 0 18px rgba(249, 115, 22, 0); }
            100% { transform: scale(0.96); box-shadow: 0 0 0 0 rgba(249, 115, 22, 0); }
        }
    </style>
</head>
<body class="bg-[#F8F9FA] flex items-center justify-center min-h-screen">
    <div class="bg-white p-8 rounded-[32px] shadow-2xl border border-gray-100 max-w-sm w-full text-center relative">
        <div class="absolute top-0 left-0 right-0 h-[6px] bg-gradient-to-r from-orange-500 to-orange-600 rounded-t-[32px]"></div>
        
        <div class="mb-1 text-xs font-bold text-orange-500 uppercase tracking-widest">Nightside AI Systems</div>
        <h2 class="text-2xl font-black text-gray-900 tracking-tight mb-3">Voice Receptionist</h2>
        <p class="text-gray-500 text-xs px-4 mb-8 leading-relaxed">Press the interface mic once to start speaking. Click stop when complete.</p>

        <div class="flex justify-center mb-8">
            <button id="actionBtn" class="w-24 h-24 bg-orange-500 hover:bg-orange-600 text-white rounded-full flex items-center justify-center text-3xl shadow-xl transition-all duration-300 cursor-pointer focus:outline-none">
                <i id="actionIcon" class="fa-solid fa-microphone"></i>
            </button>
        </div>

        <div id="runtimeStatus" class="text-xs font-extrabold text-orange-500 uppercase tracking-widest mb-4">System Standby</div>
        
        <div class="bg-gray-50 p-4 rounded-2xl border border-gray-100 text-left min-h-[70px] flex items-center">
            <p id="liveConsole" class="text-xs text-gray-400 italic font-medium leading-normal w-full text-center">
                Click button to capture audio feed...
            </p>
        </div>
    </div>

    <script>
        let recorderContext;
        let dataSegments = [];
        let executionFlag = false;

        const actionBtn = document.getElementById('actionBtn');
        const actionIcon = document.getElementById('actionIcon');
        const runtimeStatus = document.getElementById('runtimeStatus');
        const liveConsole = document.getElementById('liveConsole');

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(hardwareStream => {
                    recorderContext = new MediaRecorder(hardwareStream);
                    recorderContext.ondataavailable = dataEvent => { dataSegments.push(dataEvent.data); };
                    
                    recorderContext.onstop = () => {
                        runtimeStatus.innerText = "Analyzing...";
                        runtimeStatus.className = "text-xs font-extrabold text-gray-500 uppercase tracking-widest mb-4";
                        liveConsole.innerText = "Processing streaming frequency loops...";
                        
                        const CompiledBlob = new Blob(dataSegments, { type: 'audio/wav' });
                        const transmissionForm = new FormData();
                        transmissionForm.append('audio', CompiledBlob, 'audio.wav');

                        // Now it hits the relative path, no CORS issues!
                        fetch('/process-voice', { method: 'POST', body: transmissionForm })
                        .then(apiFeedback => {
                            if (!apiFeedback.ok) throw new Error("Network error");
                            return apiFeedback.blob();
                        })
                        .then(audioBinaryData => {
                            runtimeStatus.innerText = "Agent Speaking";
                            runtimeStatus.className = "text-xs font-extrabold text-green-500 uppercase tracking-widest mb-4";
                            liveConsole.innerText = "Voice generated successfully.";
                            
                            const streamingUrl = URL.createObjectURL(audioBinaryData);
                            const audioPlaybackEngine = new Audio(streamingUrl);
                            audioPlaybackEngine.play();

                            audioPlaybackEngine.onended = () => {
                                runtimeStatus.innerText = "System Standby";
                                runtimeStatus.className = "text-xs font-extrabold text-orange-500 uppercase tracking-widest mb-4";
                                actionBtn.classList.remove('glow-active');
                            };
                        }).catch(err => {
                            runtimeStatus.innerText = "API Error";
                            runtimeStatus.className = "text-xs font-extrabold text-red-500 uppercase tracking-widest mb-4";
                            liveConsole.innerText = "Please check your Groq API Key.";
                        });
                        dataSegments = [];
                    };
                }).catch(err => {
                    runtimeStatus.innerText = "Mic Blocked";
                    runtimeStatus.className = "text-xs font-extrabold text-red-500 uppercase tracking-widest mb-4";
                    liveConsole.innerText = "Please allow microphone access in browser URL bar.";
                });
        }

        actionBtn.addEventListener('click', () => {
            if (!recorderContext) return;
            if (!executionFlag) {
                dataSegments = [];
                recorderContext.start();
                executionFlag = true;
                actionIcon.className = "fa-solid fa-square text-2xl";
                actionBtn.classList.add('glow-active');
                runtimeStatus.innerText = "Listening...";
                runtimeStatus.className = "text-xs font-extrabold text-orange-600 uppercase tracking-widest mb-4";
                liveConsole.innerText = "Speak now. Hit stop when complete.";
            } else {
                recorderContext.stop();
                executionFlag = false;
                actionIcon.className = "fa-solid fa-microphone";
            }
        });
    </script>
</body>
</html>
"""

# -------------------------------------------------------------
# IN-MEMORY SESSION & CRM LOGIC
# -------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are an expert AI Voice Assistant for Nightside AI agency. Your goal is to guide visitors "
    "about our AI automation services and collect their lead information.\n"
    "1. Keep responses short and conversational (under 15 words).\n"
    "2. You MUST collect Their Name, Their Phone Number, and what service they need.\n"
    "3. Ask for only ONE piece of info at a time.\n"
    "4. Once collected, thank them and say goodbye."
)

sessions = {"default_user": [{"role": "system", "content": SYSTEM_PROMPT}]}

def push_to_crm(name, phone, requirements):
    print("\n" + "="*50)
    print("🚀 CRM SYNC ACTIVATED - NEW LEAD CAPTURED")
    print(f"👤 Name: {name}\n📞 Phone: {phone}\n📝 Requirements: {requirements}")
    print("="*50 + "\n")
    return True

async def save_voice_file(text, filepath):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(filepath)

# -------------------------------------------------------------
# FLASK ROUTES
# -------------------------------------------------------------
@app.route('/')
def home():
    # Jab browser direct 127.0.0.1:5000 hit karega, toh yeh UI render hoga
    return render_template_string(HTML_UI)

@app.route('/process-voice', methods=['POST'])
def process_voice():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio"}), 400
        
    audio_file = request.files['audio']
    audio_input_path = "user_input.wav"
    audio_output_path = "response.mp3"
    audio_file.save(audio_input_path)
    
    try:
        with open(audio_input_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_input_path, file.read()), model="whisper-large-v3", language="en"
            )
        user_text = transcription.text
        print(f"\n[STT] User Said: {user_text}")
        
        if "default_user" not in sessions:
            sessions["default_user"] = [{"role": "system", "content": SYSTEM_PROMPT}]
        sessions["default_user"].append({"role": "user", "content": user_text})
        
        chat_completion = client.chat.completions.create(
            messages=sessions["default_user"], model="llama3-70b-8192", temperature=0.4
        )
        ai_response = chat_completion.choices[0].message.content
        print(f"[LLM] Agent Response: {ai_response}")
        sessions["default_user"].append({"role": "assistant", "content": ai_response})
        
        # Lead extraction logic
        analysis_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Analyze conversation. Output JSON: {'complete': true/false, 'name': '...', 'phone': '...', 'requirements': '...'}"},
                {"role": "user", "content": str(sessions["default_user"][-4:])}
            ],
            model="llama3-8b-8192", response_format={"type": "json_object"}
        )
        
        try:
            analysis_data = json.loads(analysis_completion.choices[0].message.content)
            if analysis_data.get("complete") is True:
                push_to_crm(analysis_data.get("name"), analysis_data.get("phone"), analysis_data.get("requirements"))
                sessions["default_user"] = [{"role": "system", "content": SYSTEM_PROMPT}]
        except: pass
            
        asyncio.run(save_voice_file(ai_response, audio_output_path))
        return send_file(audio_output_path, mimetype="audio/mp3")
        
    except Exception as main_err:
        print(f"[ERROR]: {main_err}")
        return jsonify({"error": str(main_err)}), 500
    finally:
        if os.path.exists(audio_input_path): os.remove(audio_input_path)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
