import os
import uuid
import threading
import time
import subprocess

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp

# ─── App setup ────────────────────────────────────────────────
app = Flask(__name__)
FRONTEND_URL = https://project-fmyux.vercel.app/
# Allow requests from Vercel frontend + localhost dev
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    os.environ.get("FRONTEND_URL", ""),   # set this on Railway
]
CORS(app, origins=[o for o in ALLOWED_ORIGINS if o], supports_credentials=True)

PORT         = int(os.environ.get("PORT", 5000))
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ─── Helpers ──────────────────────────────────────────────────
def time_to_sec(t: str) -> int:
    parts = str(t).strip().split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return 0
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return int(parts[0]) if parts else 0

def auto_delete(path: str, delay: int = 300):
    """Delete file after `delay` seconds in background."""
    def _run():
        time.sleep(delay)
        try:
            os.remove(path)
        except OSError:
            pass
    threading.Thread(target=_run, daemon=True).start()

def find_downloaded_file(uid: str) -> str | None:
    """Find the actual downloaded file by uid prefix."""
    for ext in ["mp4", "mkv", "webm", "m4v", "mov"]:
        path = os.path.join(DOWNLOAD_DIR, f"{uid}_raw.{ext}")
        if os.path.exists(path):
            return path
    return None

# ─── Routes ───────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """Health check — frontend uses this to confirm backend is reachable."""
    return jsonify({"ok": True, "version": "1.0.0"})


@app.route("/api/info", methods=["POST"])
def get_info():
    """
    POST { "url": "https://youtube.com/watch?v=..." }
    Returns title, duration, thumbnail, available qualities.
    """
    data = request.get_json(silent=True) or {}
    url  = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    ydl_opts = {
        "quiet":       True,
        "no_warnings": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to fetch video info: {e}"}), 500

    # Collect unique available heights
    seen, qualities = set(), []
    for f in info.get("formats", []):
        h = f.get("height")
        if h and f.get("vcodec", "none") != "none" and h not in seen:
            seen.add(h)
            qualities.append(h)
    qualities.sort(reverse=True)

    return jsonify({
        "title":      info.get("title", "Unknown"),
        "duration":   info.get("duration", 0),
        "thumbnail":  info.get("thumbnail", ""),
        "channel":    info.get("uploader", ""),
        "view_count": info.get("view_count", 0),
        "video_id":   info.get("id", ""),
        "qualities":  [str(q) for q in qualities],
    })


@app.route("/api/clip", methods=["POST"])
def clip_video():
    """
    POST {
      "url":     "https://youtube.com/watch?v=...",
      "start":   "0:30",
      "end":     "1:45",
      "quality": "720",      -- height in px
      "format":  "mp4"       -- mp4 | webm | mp3
    }
    Returns the clipped file as a download.
    """
    data    = request.get_json(silent=True) or {}
    url     = data.get("url",     "").strip()
    start   = data.get("start",   "0:00")
    end     = data.get("end",     "0:30")
    quality = str(data.get("quality", "720"))
    fmt     = data.get("format",  "mp4").lower()

    # ── Validate ──────────────────────────────────────────────
    if not url:
        return jsonify({"error": "URL is required"}), 400

    start_sec = time_to_sec(start)
    end_sec   = time_to_sec(end)
    duration  = end_sec - start_sec

    if duration <= 0:
        return jsonify({"error": "End time must be after start time"}), 400
    if duration > 600:
        return jsonify({"error": "Maximum clip length is 10 minutes"}), 400

    uid      = str(uuid.uuid4())[:8]
    raw_tmpl = os.path.join(DOWNLOAD_DIR, f"{uid}_raw.%(ext)s")

    # ── yt-dlp format string ──────────────────────────────────
    if fmt == "mp3":
        ydl_fmt = "bestaudio/best"
    else:
        ydl_fmt = (
            f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={quality}]+bestaudio"
            f"/best[height<={quality}]"
            f"/best"
        )

    ydl_opts = {
        "format":               ydl_fmt,
        "outtmpl":              raw_tmpl,
        "quiet":                True,
        "no_warnings":          True,
        "merge_output_format":  "mp4",
    }

    # ── Download ──────────────────────────────────────────────
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            dl   = ydl.prepare_filename(info)
    except Exception as e:
        return jsonify({"error": f"Download failed: {e}"}), 500

    # Resolve actual file path
    if not os.path.exists(dl):
        dl = find_downloaded_file(uid)
    if not dl:
        return jsonify({"error": "Downloaded file not found"}), 500

    # ── FFmpeg trim ───────────────────────────────────────────
    out_ext = "mp3" if fmt == "mp3" else ("webm" if fmt == "webm" else "mp4")
    out     = os.path.join(DOWNLOAD_DIR, f"{uid}_clip.{out_ext}")

    cmd = ["ffmpeg", "-y", "-ss", str(start_sec), "-i", dl, "-t", str(duration)]

    if fmt == "mp3":
        cmd += ["-vn", "-acodec", "libmp3lame", "-q:a", "2"]
    elif fmt == "webm":
        cmd += ["-c:v", "libvpx-vp9", "-c:a", "libopus", "-b:v", "0", "-crf", "30"]
    else:
        cmd += [
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
        ]

    cmd.append(out)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-800:])
    except Exception as e:
        try:
            os.remove(dl)
        except OSError:
            pass
        return jsonify({"error": f"FFmpeg trim failed: {e}"}), 500

    # Clean up full download
    try:
        os.remove(dl)
    except OSError:
        pass

    # Auto-delete clip after 5 minutes
    auto_delete(out, delay=300)

    # Safe filename for download header
    raw_title = info.get("title", "clip")
    safe_title = "".join(
        c if (c.isalnum() or c in "-_ ") else "_" for c in raw_title
    )[:60].strip()
    s_str = start.replace(":", "")
    e_str = end.replace(":", "")
    filename = f"{safe_title}_{s_str}_{e_str}.{out_ext}"

    mime_map = {"mp4": "video/mp4", "mp3": "audio/mpeg", "webm": "video/webm"}
    mime = mime_map.get(out_ext, "application/octet-stream")

    return send_file(out, as_attachment=True, download_name=filename, mimetype=mime)


# ─── Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀  ClipCutter backend → http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
