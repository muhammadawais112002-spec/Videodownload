// DownloadAnything - main.js  v3
// Loaded fresh every time (no caching issue)

let currentResult = null;

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('video-url').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') fetchVideo();
  });
  console.log('[DA] main.js v3 loaded - savevideo mode active');
});

// ── Fetch video metadata ──────────────────────────────────
async function fetchVideo() {
  const urlInput = document.getElementById('video-url');
  const url = urlInput.value.trim();

  if (!url) {
    shakeInput();
    showError('Please paste a video URL first.');
    return;
  }

  hideAll();
  setLoading(true, 'Fetching video info');

  try {
    const res = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });

    const data = await res.json();
    setLoading(false);

    if (!data.success) {
      showError(data.error || 'An unknown error occurred.');
      return;
    }

    currentResult = data;
    showResult(data);

  } catch (err) {
    setLoading(false);
    showError('Cannot connect to server. Make sure Flask is running on port 5000.');
  }
}

// ── Show result card ──────────────────────────────────────
function showResult(data) {
  document.getElementById('result-thumb').src = data.thumbnail || '';
  document.getElementById('result-title').textContent    = data.title    || 'Untitled';
  document.getElementById('result-duration').textContent = data.duration || '';
  document.getElementById('result-uploader').textContent = data.uploader || 'Unknown';
  document.getElementById('result-views').textContent    = data.views    || 'N/A';
  document.getElementById('result-platform').textContent = (data.platform || 'Video').toUpperCase();

  const card = document.getElementById('result-card');
  card.classList.remove('visible');
  card.style.display = 'none';
  void card.offsetHeight;
  card.classList.add('visible');
}

// ── Trigger actual download via /api/savevideo ────────────
async function triggerDownload() {
  if (!currentResult) return;

  const btn = document.getElementById('download-btn');
  const dlStatus = document.getElementById('dl-status');

  btn.disabled = true;
  btn.innerHTML = `
    <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
    </svg>
    Downloading… please wait`;

  if (dlStatus) dlStatus.textContent = 'Server is downloading the video. This may take 10–60 seconds depending on video size…';

  const resetBtn = () => {
    btn.disabled = false;
    btn.innerHTML = `
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
      </svg>
      Download Now`;
    if (dlStatus) dlStatus.textContent = '';
  };

  try {
    console.log('[DA] Calling /api/savevideo for:', currentResult.original_url);

    const res = await fetch('/api/savevideo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_url: currentResult.original_url,
        title: currentResult.title,
        ext: currentResult.ext || 'mp4',
      }),
    });

    console.log('[DA] /api/savevideo response status:', res.status);

    if (!res.ok) {
      let errMsg = 'Download failed on server.';
      try {
        const errData = await res.json();
        errMsg = errData.error || errMsg;
      } catch (_) {}
      showError('Server error: ' + errMsg);
      resetBtn();
      return;
    }

    // Stream blob to browser
    const blob = await res.blob();
    console.log('[DA] Blob received, size:', blob.size);

    if (blob.size < 1000) {
      showError('Downloaded file is too small — possibly an error. Try another video.');
      resetBtn();
      return;
    }

    const safeTitle = (currentResult.title || 'video').replace(/[^\w\- ]/g, '_').substring(0, 80);
    const ext = currentResult.ext || 'mp4';

    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = `${safeTitle}.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    setTimeout(() => URL.revokeObjectURL(objectUrl), 10000);
    if (dlStatus) dlStatus.textContent = 'Download started! Check your Downloads folder.';
    setTimeout(resetBtn, 3000);

  } catch (err) {
    console.error('[DA] Download error:', err);
    showError('Network error: ' + err.message);
    resetBtn();
  }
}

// ── UI helpers ────────────────────────────────────────────
function hideAll() {
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('loading').classList.remove('flex');
  document.getElementById('error-box').classList.add('hidden');
  const card = document.getElementById('result-card');
  card.classList.remove('visible');
  card.style.display = 'none';
}

function setLoading(show, text) {
  const el = document.getElementById('loading');
  const lt = document.getElementById('loading-text');
  if (text && lt) lt.textContent = text;
  if (show) {
    el.classList.remove('hidden');
    el.classList.add('flex');
  } else {
    el.classList.add('hidden');
    el.classList.remove('flex');
  }
}

function showError(msg) {
  document.getElementById('error-msg').textContent = msg;
  document.getElementById('error-box').classList.remove('hidden');
}

function shakeInput() {
  const input = document.getElementById('video-url');
  input.classList.remove('shake');
  void input.offsetHeight;
  input.classList.add('shake');
  input.addEventListener('animationend', () => input.classList.remove('shake'), { once: true });
}
