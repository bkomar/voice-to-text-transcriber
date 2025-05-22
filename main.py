import os
import json
from flask import Flask, request, jsonify, send_from_directory
import sounddevice as sd
import numpy as np
import wave
import threading
import whisper
from datetime import datetime
from pydub import AudioSegment


RECORDINGS_DIR = "recordings"
TRANSCRIPTS_FILE = os.path.join(RECORDINGS_DIR, "transcripts.json")
SAMPLE_RATE = 16000
CHANNELS = 1

app = Flask(__name__)
model = None
model_name = "base"
transcripts = {}

def load_transcripts():
    if os.path.exists(TRANSCRIPTS_FILE):
        try:
            with open(TRANSCRIPTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_transcripts():
    try:
        with open(TRANSCRIPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(transcripts, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Saving transcripts failed: {e}")

@app.route('/api/load_model', methods=['POST'])
def api_load_model():
    global model, model_name
    data = request.json
    model_name = data.get('model_name', 'base')
    try:
        model = whisper.load_model(model_name)
        return jsonify({'status': 'ok', 'message': f"Model '{model_name}' loaded."})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/record', methods=['POST'])
def api_record():
    # Check if audio file is in the request
    if 'audio' not in request.files:
        return jsonify({'status': 'error', 'message': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".wav"
    filepath = os.path.join(RECORDINGS_DIR, filename)

    try:
        # Save the uploaded file (webm) temporarily
        temp_path = filepath + ".webm"
        audio_file.save(temp_path)

        # Convert webm to wav using pydub
        audio = AudioSegment.from_file(temp_path)
        audio = audio.set_channels(CHANNELS).set_frame_rate(SAMPLE_RATE)
        audio.export(filepath, format="wav")
        os.remove(temp_path)

        return jsonify({'status': 'ok', 'filename': filename})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    global transcripts
    filename = request.json.get('filename')
    language = request.json.get('language', 'en')
    filepath = os.path.join(RECORDINGS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
    try:
        result = model.transcribe(filepath, language=language)
        text = result['text']
        transcripts[filename] = {
            "text": text,
            "language": language,
            "model": model_name
        }
        save_transcripts()
        return jsonify({'status': 'ok', 'text': text})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def api_history():
    files = []
    for filename in sorted(os.listdir(RECORDINGS_DIR), reverse=True):
        if filename.endswith(".wav"):
            filepath = os.path.join(RECORDINGS_DIR, filename)
            stat = os.stat(filepath)
            duration = get_audio_duration(filepath)
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            entry = transcripts.get(filename, {})
            text = entry.get("text", "") if isinstance(entry, dict) else entry
            lang = entry.get("language", "") if isinstance(entry, dict) else ""
            model_used = entry.get("model", "") if isinstance(entry, dict) else ""
            short_text = (text[:50] + "...") if len(text) > 50 else text
            files.append({
                "filename": filename,
                "duration": f"{duration:.1f}s",
                "mtime": mtime,
                "summary": short_text,
                "text": text,  # <-- Add this line
                "language": lang,
                "model": model_used
            })
    return jsonify(files)

@app.route('/api/audio/<filename>')
def api_audio(filename):
    return send_from_directory(RECORDINGS_DIR, filename)

@app.route('/api/delete', methods=['POST'])
def api_delete():
    global transcripts
    filename = request.json.get('filename')
    filepath = os.path.join(RECORDINGS_DIR, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        if filename in transcripts:
            del transcripts[filename]
            save_transcripts()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_audio_duration(filepath):
    try:
        audio = AudioSegment.from_file(filepath)
        return len(audio) / 1000.0
    except Exception:
        return 0.0

if __name__ == "__main__":
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    transcripts = load_transcripts()
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        print(f"Failed to load model: {e}")
    app.run(port=5000, debug=True)
