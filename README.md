# DownloadAnything 🎬

> A free, self-hosted, all-in-one video downloader for YouTube, Instagram Reels, TikTok, Twitter/X, and 1,000+ other platforms.

---

## 🚀 Quick Start

### Step 1 – Install Python (if not already installed)

Download Python **3.8 or newer** from → **https://www.python.org/downloads/**

> ⚠️ **IMPORTANT:** During installation, check the box **"Add Python to PATH"**

---

### Step 2 – Install dependencies

Open a **Command Prompt** or **PowerShell** in this folder and run:

```bash
python -m pip install flask flask-cors yt-dlp
```

Or simply **double-click `start.bat`** — it will detect Python, install everything, and launch the server automatically.

---

### Step 3 – Run the server

```bash
python app.py
```

Then open your browser and go to → **http://127.0.0.1:5000**

---

## 📁 Project Structure

```
Downloadanything/
├── app.py           # Flask backend (API + proxy)
├── index.html       # Frontend (Tailwind CSS + JS)
├── requirements.txt # Python dependencies
├── start.bat        # One-click Windows launcher
└── README.md        # This file
```

---

## 🛠 How It Works

1. User pastes a video URL into the web interface
2. Frontend sends a `POST /api/download` request to the Flask server
3. `yt-dlp` extracts the video metadata (title, thumbnail, duration, direct stream URL)
4. The result card appears with thumbnail + a **Download Now** button
5. Clicking **Download Now** streams the video through `/api/proxy` so the browser saves it as a file

---

## ✅ Supported Platforms

YouTube, Instagram Reels, TikTok, Twitter/X, Facebook, Twitch, Vimeo, Dailymotion, Reddit, Rumble, Bilibili, SoundCloud, LinkedIn, and **1,000+ more** (powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)).

---

## ⚙️ API Reference

### `POST /api/download`

**Request body:**
```json
{ "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" }
```

**Success response:**
```json
{
  "success": true,
  "title": "Rick Astley - Never Gonna Give You Up",
  "thumbnail": "https://...",
  "duration": "3:33",
  "uploader": "Rick Astley",
  "views": "1,400,000,000",
  "platform": "Youtube",
  "download_url": "https://...",
  "ext": "mp4"
}
```

**Error response:**
```json
{ "success": false, "error": "Video is unavailable or private." }
```

---

## 📝 Notes

- This tool is for **personal use only**. Respect platform Terms of Service.
- Some platforms (especially Instagram) may require cookies or login tokens for private content.
- yt-dlp is updated frequently — run `python -m pip install --upgrade yt-dlp` if you encounter extraction errors.
