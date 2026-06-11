import os
import re
import tempfile
import threading
import urllib.request
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': '*/*',
    'Referer': 'https://www.google.com/',
}

# Temp dir for downloaded files
DOWNLOAD_DIR = tempfile.mkdtemp(prefix='dlany_')

# ─────────────────────────────────────────────
#  Setup bundled ffmpeg from imageio_ffmpeg
# ─────────────────────────────────────────────
FFMPEG_PATH = None

def setup_ffmpeg():
    global FFMPEG_PATH
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_exe):
            FFMPEG_PATH = ffmpeg_exe
            # Add its directory to PATH so yt-dlp can find it
            ffmpeg_dir = os.path.dirname(ffmpeg_exe)
            if ffmpeg_dir not in os.environ.get('PATH', ''):
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            print(f'    ffmpeg found: {ffmpeg_exe}')
            return True
    except Exception as e:
        print(f'    imageio_ffmpeg error: {e}')
    return False

def ffmpeg_available():
    return FFMPEG_PATH is not None

# Run setup at import time
setup_ffmpeg()

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def format_duration(seconds):
    if not seconds:
        return 'N/A'
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f'{h}:{m:02d}:{s:02d}' if h > 0 else f'{m}:{s:02d}'


def cleanup_file(path, delay=180):
    """Delete temp file after delay seconds."""
    def _del():
        import time
        time.sleep(delay)
        try:
            os.remove(path)
        except Exception:
            pass
    threading.Thread(target=_del, daemon=True).start()


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return app.send_static_file('index.html')


# ── 1. Extract metadata only ──────────────────
@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()

    if not url:
        return jsonify({'success': False, 'error': 'No URL provided.'}), 400
    if not re.match(r'https?://', url):
        return jsonify({'success': False, 'error': 'Please enter a valid URL.'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'http_headers': HEADERS,
        'extractor_args': {
            'youtube': {'player_client': ['ios', 'android', 'web']},
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if info is None:
            return jsonify({'success': False, 'error': 'Could not extract video. Link may be private or unsupported.'}), 422

        if info.get('_type') == 'playlist':
            entries = info.get('entries') or []
            if not entries:
                return jsonify({'success': False, 'error': 'Playlist is empty.'}), 422
            info = entries[0]

        title     = info.get('title') or 'Untitled Video'
        thumbnail = info.get('thumbnail') or ''
        duration  = format_duration(info.get('duration'))
        uploader  = info.get('uploader') or info.get('channel') or 'Unknown'
        view_count = info.get('view_count')
        views     = f'{view_count:,}' if view_count else 'N/A'
        platform  = info.get('extractor_key') or 'Unknown'

        return jsonify({
            'success': True,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'uploader': uploader,
            'views': views,
            'platform': platform,
            'original_url': url,
            'ext': 'mp4',
        })

    except yt_dlp.utils.DownloadError as e:
        msg = re.sub(r'^ERROR:\s*', '', str(e), flags=re.IGNORECASE)
        return jsonify({'success': False, 'error': msg}), 422
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 500


# ── 2. Download video server-side & stream it ─
@app.route('/api/savevideo', methods=['POST'])
def api_savevideo():
    data = request.get_json(silent=True) or {}
    original_url = (data.get('original_url') or '').strip()
    title = (data.get('title') or 'video').strip()

    if not original_url:
        return jsonify({'error': 'No URL provided.'}), 400

    safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)[:60]
    out_template = os.path.join(DOWNLOAD_DIR, f'{safe_name}_%(id)s.%(ext)s')

    has_ffmpeg = ffmpeg_available()

    if has_ffmpeg:
        # Best quality with merge
        fmt = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best'
    else:
        # IMPORTANT: Without ffmpeg, only pick formats that already have BOTH
        # video AND audio in a single file (no merging needed)
        fmt = 'best[ext=mp4]/best[ext=webm]/best'

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'outtmpl': out_template,
        'http_headers': HEADERS,
        'format': fmt,
        'extractor_args': {
            'youtube': {'player_client': ['ios', 'android', 'web']},
        },
    }

    if has_ffmpeg:
        ydl_opts['merge_output_format'] = 'mp4'
        ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_PATH)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(original_url, download=True)

            if info is None:
                return jsonify({'error': 'Download failed. Could not extract info.'}), 500

            if info.get('_type') == 'playlist':
                entries = info.get('entries') or []
                if entries:
                    info = entries[0]

            filepath = ydl.prepare_filename(info)

        # yt-dlp might change extension after processing
        if not os.path.exists(filepath):
            base = os.path.splitext(filepath)[0]
            for candidate_ext in ['mp4', 'webm', 'mkv', 'avi', 'mov', 'm4v']:
                candidate = f'{base}.{candidate_ext}'
                if os.path.exists(candidate):
                    filepath = candidate
                    break

        # Also search by pattern in download dir if still not found
        if not os.path.exists(filepath):
            for fname in os.listdir(DOWNLOAD_DIR):
                if safe_name[:20] in fname:
                    filepath = os.path.join(DOWNLOAD_DIR, fname)
                    break

        if not os.path.exists(filepath):
            return jsonify({'error': 'Downloaded file not found. Try again.'}), 500

        actual_ext = os.path.splitext(filepath)[1].lstrip('.') or 'mp4'
        dl_name = re.sub(r'[\\/*?:"<>|]', '_', title)[:80] + '.' + actual_ext

        # Schedule cleanup
        cleanup_file(filepath, delay=180)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=dl_name,
            mimetype='video/' + actual_ext,
        )

    except yt_dlp.utils.DownloadError as e:
        msg = re.sub(r'^ERROR:\s*', '', str(e), flags=re.IGNORECASE)
        return jsonify({'error': msg}), 422
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


# ── 3. Status / debug endpoint ────────────────
@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        'status': 'online',
        'ffmpeg': ffmpeg_available(),
        'download_dir': DOWNLOAD_DIR,
    })


if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    has_ff = ffmpeg_available()
    print('\n[*] All-in-One Video Downloader is running!')
    print('    Open --> http://127.0.0.1:5000')
    print(f'    ffmpeg: {"FOUND - best quality mode" if has_ff else "NOT FOUND - using single-file mode (lower quality)"}')
    print(f'    Temp dir: {DOWNLOAD_DIR}\n')
    app.run(debug=True, host='0.0.0.0', port=5000)
