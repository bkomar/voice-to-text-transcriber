
# Voice-to-Text Transcriber GUI — Offline Whisper Speech-to-Text App

**Voice-to-Text Transcriber GUI** is a lightweight, open-source Python desktop application that lets you record audio and transcribe speech to text **locally using OpenAI’s Whisper model** — with no internet connection required. Manage, playback, and delete your recordings and transcripts via a simple, intuitive graphical interface.

## 🚀 Key Features

- **Offline Speech-to-Text Transcription:** Powered by OpenAI Whisper models (`base` and `small`) running fully on your computer  
- **Multi-language support:** Transcribe in English (`en`), Ukrainian (`uk`), Spanish (`es`), and German (`de`)  
- **Real-time recording:** Capture audio directly from your microphone  
- **Playback & History:** Listen to recordings and view transcription history in an easy-to-use table  
- **Secure & Private:** No data leaves your machine — complete privacy and security  
- **Progress and status indicators** to keep you informed during transcription and playback

## 🔒 Privacy & Security

This app guarantees your privacy:

- **100% offline transcription** — no API calls, no cloud uploads, no external servers  
- Audio and text files stored only locally on your device  
- Ideal for privacy-conscious users, researchers, journalists, and developers seeking offline voice-to-text tools

## 🎯 Why Use This App?

- No reliance on paid APIs or internet connections  
- Supports popular Whisper models for flexible accuracy and speed  
- Easy-to-use Tkinter GUI suitable for beginners and advanced users alike  
- Manage and organize voice recordings with ease

## 📋 Requirements

- Python 3.7 or newer  
- FFmpeg installed and in your system PATH (used by `pydub` to process audio)

## ⚙️ Installation Steps

### Using a Virtual Environment (Recommended)
1. Install FFmpeg and PortAudio:
   ```bash
   sudo apt install ffmpeg  
   sudo apt install libportaudio2
   ```  

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-to-text-gui.git
   cd voice-to-text-gui
   ```

3. To avoid dependency conflicts and keep your environment clean, it's recommended to use a **virtual environment**.
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```



## ▶️ How to Run

Run the app with:

```bash
python main.py
```

- Select transcription language and Whisper model (`base` or `small`)  
- Click **Start Recording** to begin capturing audio  
- Click **Stop Recording** to save and transcribe  
- View and edit transcripts, playback recordings, or delete unwanted files  

## 📂 Project Structure

```
voice-to-text-gui/
├── recordings/           # Audio (.wav) files and transcripts storage
├── main.py               # Main application source code
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## 📝 License

This project is licensed under the MIT License.

---

### Keywords to improve discoverability:

offline speech to text, local voice transcription, Whisper model GUI, python voice recorder, private speech recognition, open source voice to text app, whisper transcription offline, audio recorder and transcriber

---

**Enjoy hassle-free, secure voice-to-text transcription — completely offline and open source!**
