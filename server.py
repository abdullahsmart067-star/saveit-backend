from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os, tempfile, re

app = Flask(__name__)
CORS(app)  # allows all origins; restrict to your domain after deploy

QUALITY_MAP = {
    "360p":  "bestvideo[height<=360][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=360]+bestaudio/best[height<=360]",
    "480p":  "bestvideo[height<=480][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=480]+bestaudio/best[height<=480]",
    "720p":  "bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
    "1080p": "bestvideo[height<=1080][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "1440p": "bestvideo[height<=1440][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "2K":    "bestvideo[height<=1440][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=1440]+bestaudio/best",
}

BITRATE_MAP = {
    "128 kbps": "128",
    "192 kbps": "192",
    "256 kbps": "256",
    "320 kbps": "320",
}

@app.route("/download")
def download():
    url     = request.args.get("url", "").strip()
    fmt     = request.args.get("format", "mp4").lower()
    quality = request.args.get("quality", "720p")
    bitrate = request.args.get("bitrate", "192 kbps")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    tmpdir = tempfile.mkdtemp()

    try:
        if fmt == "mp3":
            abr = BITRATE_MAP.get(bitrate, "192")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": abr,
                }],
                "quiet": True,
            }
        else:
            fmt_str = QUALITY_MAP.get(quality, QUALITY_MAP["720p"])
            ydl_opts = {
                "format": fmt_str,
                "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                "merge_output_format": "mp4",
                "quiet": True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = os.listdir(tmpdir)
        if not files:
            return jsonify({"error": "Download produced no file"}), 500

        filepath = os.path.join(tmpdir, files[0])
        ext = "mp3" if fmt == "mp3" else "mp4"
        safe_name = re.sub(r"[^\w\-.]", "_", files[0])

        return send_file(
            filepath,
            as_attachment=True,
            download_name=safe_name,
            mimetype="audio/mpeg" if ext == "mp3" else "video/mp4"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway/Render set PORT automatically
    print(f"\n✅  Saveit server running on port {port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
