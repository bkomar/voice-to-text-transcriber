const API = 'http://localhost:5000/api';

async function loadModel(model) {
  setStatus('Loading model...');
  const res = await fetch(`${API}/load_model`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({model_name: model})
  });
  const data = await res.json();
  setStatus(data.message || data.status);
  loadHistory();
}

// Load default model on page load
window.addEventListener('DOMContentLoaded', () => {
  const modelSelect = document.getElementById('model');
  loadModel(modelSelect.value);
  modelSelect.addEventListener('change', () => {
    loadModel(modelSelect.value);
  });
});

const recordBtn = document.getElementById('recordBtn');
const recordDot = document.getElementById('recordDot');
const recordLabel = document.getElementById('recordLabel');
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];

recordBtn.onclick = async () => {
  if (!isRecording) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Audio recording not supported in this browser.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };
      mediaRecorder.onstop = async () => {
        recordBtn.classList.remove('recording');
        recordLabel.textContent = "Record";
        isRecording = false;
        setStatus('Uploading audio...');
        const blob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', blob, 'recording.webm');
        // Upload audio to backend
        const uploadRes = await fetch(`${API}/record`, {
          method: 'POST',
          body: formData
        });
        const uploadData = await uploadRes.json();
        if (uploadData.status !== 'ok') {
          setStatus('Upload failed: ' + (uploadData.message || ''));
          return;
        }
        setStatus('Transcribing...');
        // Get selected language
        const language = document.getElementById('language').value;
        // Request transcription
        const transcribeRes = await fetch(`${API}/transcribe`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ filename: uploadData.filename, language })
        });
        const transcribeData = await transcribeRes.json();
        if (transcribeData.status === 'ok') {
          setStatus('Transcription complete.');
          document.getElementById('transcription').value = transcribeData.text || '';
        } else {
          setStatus('Transcription failed: ' + (transcribeData.message || ''));
        }
        setTimeout(loadHistory, 500);
      };
      mediaRecorder.start();
      recordBtn.classList.add('recording');
      recordLabel.textContent = "Stop";
      isRecording = true;
      setStatus('Recording...');
    } catch (err) {
      alert('Could not start recording: ' + err.message);
    }
  } else {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  }
};

function setStatus(msg) {
  document.getElementById('status').innerText = msg;
}

async function loadHistory() {
  const res = await fetch(`${API}/history`);
  const data = await res.json();
  const body = document.getElementById('historyBody');
  body.innerHTML = '';
  data.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td title="${row.filename}" style="cursor:pointer;">${row.filename}</td>
      <td>${row.duration || ''}</td>
      <td>${row.mtime || ''}</td>
      <td title="${row.text || row.summary}">${row.summary || ''}</td>
      <td>${row.language || ''}</td>
      <td>${row.model || ''}</td>
      <td class="history-actions">
        <button onclick="playAudio('${row.filename}');event.stopPropagation();" title="Play">▶</button>
        <button onclick="deleteAudio('${row.filename}');event.stopPropagation();" title="Delete">🗑</button>
      </td>
    `;
    tr.onclick = () => {
      document.getElementById('transcription').value = row.text || '';
    };
    body.appendChild(tr);
  });
}
window.loadHistory = loadHistory;

document.getElementById('refreshBtn').onclick = () => {
  loadHistory();
};

window.playAudio = (filename) => {
  const audio = new Audio(`${API.replace('/api','')}/api/audio/${filename}`);
  audio.play();
};

window.deleteAudio = async (filename) => {
  if (!confirm(`Delete ${filename}?`)) return;
  await fetch(`${API}/delete`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({filename})
  });
  loadHistory();
};

loadHistory();