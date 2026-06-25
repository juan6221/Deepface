# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template_string
import traceback

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DeepFace — Análisis Facial</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      min-height: 100vh; font-family: 'Segoe UI', sans-serif; color: #fff; padding: 20px;
    }
    h1 { text-align: center; font-size: 2rem; margin-bottom: 8px;
         background: linear-gradient(90deg, #a855f7, #3b82f6); -webkit-background-clip: text;
         -webkit-text-fill-color: transparent; }
    .subtitle { text-align: center; color: #94a3b8; margin-bottom: 30px; }

    /* TABS */
    .tabs { display: flex; justify-content: center; gap: 12px; margin-bottom: 30px; }
    .tab-btn {
      padding: 12px 32px; border-radius: 50px; border: 2px solid #a855f7;
      background: transparent; color: #a855f7; font-size: 1rem; cursor: pointer;
      transition: all 0.3s;
    }
    .tab-btn.active { background: linear-gradient(90deg, #a855f7, #3b82f6); color: #fff; border-color: transparent; }
    .tab-btn:hover { transform: translateY(-2px); }

    .tab-content { display: none; }
    .tab-content.active { display: block; }

    /* UPLOAD */
    .upload-box {
      border: 2px dashed #4f46e5; border-radius: 16px; padding: 40px;
      text-align: center; cursor: pointer; transition: all 0.3s; margin-bottom: 20px;
      background: rgba(255,255,255,0.03);
    }
    .upload-box:hover { border-color: #a855f7; background: rgba(168,85,247,0.08); }
    .upload-icon { font-size: 3rem; margin-bottom: 12px; }
    .upload-box p { color: #94a3b8; }
    .file-name { color: #a855f7; margin-top: 8px; font-weight: 600; }
    #file-input { display: none; }

    /* CAMERA */
    .camera-container { text-align: center; }
    #video { width: 100%; max-width: 640px; border-radius: 16px; border: 2px solid #4f46e5; }
    #canvas { display: none; }
    .camera-controls { display: flex; justify-content: center; gap: 12px; margin-top: 16px; flex-wrap: wrap; }

    /* BUTTONS */
    .btn {
      padding: 14px 40px; border-radius: 50px; border: none; font-size: 1rem;
      font-weight: 700; cursor: pointer; transition: all 0.3s; width: 100%;
    }
    .btn-primary {
      background: linear-gradient(90deg, #a855f7, #3b82f6); color: #fff;
    }
    .btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
    .btn-primary:not(:disabled):hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(168,85,247,0.4); }
    .btn-secondary {
      background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2);
      width: auto; padding: 12px 28px;
    }
    .btn-danger { background: #ef4444; color: #fff; width: auto; padding: 12px 28px; }

    /* RESULTS */
    #results { margin-top: 30px; }
    .result-img { width: 100%; border-radius: 16px; margin-bottom: 20px; }
    .face-card {
      background: rgba(255,255,255,0.07); border-radius: 16px; padding: 20px;
      margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.1);
    }
    .face-card h3 { color: #a855f7; margin-bottom: 12px; font-size: 1.1rem; }
    .face-row { display: flex; justify-content: space-between; padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.05); }
    .face-row:last-child { border-bottom: none; }
    .face-label { color: #94a3b8; }
    .face-value { font-weight: 600; }
    .loading { text-align: center; padding: 30px; color: #a855f7; font-size: 1.1rem; }
    .error { background: rgba(239,68,68,0.15); border: 1px solid #ef4444;
             border-radius: 12px; padding: 16px; color: #fca5a5; margin-top: 16px; }
    .live-badge {
      display: inline-block; background: #ef4444; color: #fff; font-size: 0.75rem;
      padding: 3px 10px; border-radius: 20px; margin-left: 8px; animation: pulse 1.5s infinite;
    }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
    .max-w { max-width: 680px; margin: 0 auto; }
  </style>
</head>
<body>
<div class="max-w">
  <h1>🧠 DeepFace</h1>
  <p class="subtitle">Análisis facial con IA · Género · Etnia · Edad · Emoción</p>

  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('upload')">📁 Subir imagen</button>
    <button class="tab-btn" onclick="switchTab('camera')">📷 Cámara en vivo</button>
  </div>

  <!-- TAB 1: UPLOAD -->
  <div id="tab-upload" class="tab-content active">
    <div class="upload-box" onclick="document.getElementById('file-input').click()">
      <div class="upload-icon">📤</div>
      <p><strong>Haz clic para seleccionar una imagen</strong></p>
      <p>PNG, JPG, JPEG</p>
      <p class="file-name" id="file-name"></p>
    </div>
    <input type="file" id="file-input" accept="image/*">
    <button class="btn btn-primary" id="analyze-btn" disabled onclick="analyzeFile()">Analizar rostro</button>
  </div>

  <!-- TAB 2: CAMERA -->
  <div id="tab-camera" class="tab-content">
    <div class="camera-container">
      <video id="video" autoplay playsinline></video>
      <canvas id="canvas"></canvas>
      <div class="camera-controls">
        <button class="btn btn-secondary" id="start-cam" onclick="startCamera()">▶ Iniciar cámara</button>
        <button class="btn btn-secondary" id="stop-cam" onclick="stopCamera()" style="display:none">⏹ Detener</button>
        <button class="btn btn-secondary" id="capture-btn" onclick="captureAndAnalyze()" style="display:none">📸 Capturar y analizar</button>
        <button class="btn btn-secondary" id="live-btn" onclick="toggleLive()" style="display:none">🔴 Análisis en vivo</button>
      </div>
    </div>
  </div>

  <div id="results"></div>
</div>

<script>
  let selectedFile = null;
  let stream = null;
  let liveInterval = null;
  let liveActive = false;

  // ---- TABS ----
  function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', (tab==='upload'&&i===0)||(tab==='camera'&&i===1)));
    document.getElementById('tab-upload').classList.toggle('active', tab==='upload');
    document.getElementById('tab-camera').classList.toggle('active', tab==='camera');
    if (tab==='upload') { stopCamera(); }
    document.getElementById('results').innerHTML = '';
  }

  // ---- UPLOAD ----
  document.getElementById('file-input').addEventListener('change', e => {
    selectedFile = e.target.files[0];
    if (selectedFile) {
      document.getElementById('file-name').textContent = selectedFile.name;
      document.getElementById('analyze-btn').disabled = false;
    }
  });

  async function analyzeFile() {
    if (!selectedFile) return;
    showLoading();
    const fd = new FormData();
    fd.append('image', selectedFile);
    await sendToAPI(fd);
  }

  // ---- CAMERA ----
  async function startCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      document.getElementById('video').srcObject = stream;
      document.getElementById('start-cam').style.display = 'none';
      document.getElementById('stop-cam').style.display = 'inline-block';
      document.getElementById('capture-btn').style.display = 'inline-block';
      document.getElementById('live-btn').style.display = 'inline-block';
    } catch(e) {
      showError('No se pudo acceder a la cámara: ' + e.message);
    }
  }

  function stopCamera() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    if (liveInterval) { clearInterval(liveInterval); liveInterval = null; liveActive = false; }
    document.getElementById('start-cam').style.display = 'inline-block';
    document.getElementById('stop-cam').style.display = 'none';
    document.getElementById('capture-btn').style.display = 'none';
    document.getElementById('live-btn').style.display = 'none';
    document.getElementById('live-btn').textContent = '🔴 Análisis en vivo';
  }

  function captureFrame() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    return new Promise(res => canvas.toBlob(res, 'image/jpeg', 0.85));
  }

  async function captureAndAnalyze() {
    showLoading();
    const blob = await captureFrame();
    const fd = new FormData();
    fd.append('image', blob, 'captura.jpg');
    await sendToAPI(fd);
  }

  function toggleLive() {
    if (liveActive) {
      clearInterval(liveInterval); liveInterval = null; liveActive = false;
      document.getElementById('live-btn').textContent = '🔴 Análisis en vivo';
    } else {
      liveActive = true;
      document.getElementById('live-btn').innerHTML = '⏸ Pausar <span class="live-badge">EN VIVO</span>';
      liveInterval = setInterval(async () => {
        const blob = await captureFrame();
        const fd = new FormData();
        fd.append('image', blob, 'live.jpg');
        await sendToAPI(fd, true);
      }, 3000);
    }
  }

  // ---- API ----
  async function sendToAPI(fd, silent=false) {
    if (!silent) showLoading();
    try {
      const resp = await fetch('/analyze', { method: 'POST', body: fd });
      const data = await resp.json();
      if (data.error) { showError(data.error); return; }
      renderResults(data);
    } catch(e) {
      showError('Error de conexión: ' + e.message);
    }
  }

  function renderResults(data) {
    const { faces, annotated_image } = data;
    let html = '';
    if (annotated_image) {
      html += `<img class="result-img" src="data:image/jpeg;base64,${annotated_image}">`;
    }
    if (!faces || faces.length === 0) {
      html += '<div class="error">No se detectaron rostros en la imagen.</div>';
    } else {
      faces.forEach((face, i) => {
        html += `
          <div class="face-card">
            <h3>👤 Rostro ${i+1}</h3>
            <div class="face-row"><span class="face-label">Género</span><span class="face-value">${face.genero} (${face.genero_confianza}%)</span></div>
            <div class="face-row"><span class="face-label">Etnia</span><span class="face-value">${face.raza_dominante}</span></div>
            <div class="face-row"><span class="face-label">Edad estimada</span><span class="face-value">${face.edad_estimada} años</span></div>
            <div class="face-row"><span class="face-label">Emoción</span><span class="face-value">${face.emocion}</span></div>
          </div>`;
      });
    }
    document.getElementById('results').innerHTML = html;
  }

  function showLoading() {
    document.getElementById('results').innerHTML = '<div class="loading">⏳ Analizando imagen...</div>';
  }

  function showError(msg) {
    document.getElementById('results').innerHTML = `<div class="error">❌ ${msg}</div>`;
  }
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No se recibió ninguna imagen."}), 400
    file = request.files["image"]
    try:
        from analyzer import analyze_from_bytes
        faces, img_b64 = analyze_from_bytes(file.read())
        return jsonify({"faces": faces, "annotated_image": img_b64})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    print("App corriendo en http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)