from flask import Flask, request, jsonify, send_file, send_from_directory
import os
from yt_dlp import YoutubeDL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__)

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

# ---------- ANALYZE ----------
@app.route("/analyze")
def analyze():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL missing"}), 400
    try:
        with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            "title": info.get("title"),
            "uploader": info.get("uploader") or info.get("channel") or "Unknown",
            "thumbnail": info.get("thumbnail"),
            "qualities": [144, 240, 360, 480, 720, 1080]
        })
    except Exception:
        return jsonify({"error": "Invalid or private link"}), 400

# ---------- DOWNLOAD ----------
@app.route("/download")
def download():
    url = request.args.get("url")
    mode = request.args.get("type", "video")
    q = request.args.get("q", "720")

    if not url:
        return "URL missing", 400

    try:
        # 🎵 AUDIO (NO ABORT)
        if mode == "audio":
            outtmpl = os.path.join(DOWNLOAD_DIR, "%(title)s - %(uploader)s.%(ext)s")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": outtmpl,
                "quiet": True,
                "noplaylist": True,
                "abort_on_error": False
            }
            mimetype = "audio/mpeg"

        # 🎬 VIDEO (NO MERGE, NO FFMPEG)
        else:
            outtmpl = os.path.join(DOWNLOAD_DIR, "%(title)s - %(uploader)s.%(ext)s")
            ydl_opts = {
                "format": f"best[ext=mp4][height<={q}]/best",
                "outtmpl": outtmpl,
                "quiet": True,
                "noplaylist": True,
                "abort_on_error": False
            }
            mimetype = "video/mp4"

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(
            filename,
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype=mimetype
        )

    except Exception as e:
        return f"Download failed: {str(e)}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
