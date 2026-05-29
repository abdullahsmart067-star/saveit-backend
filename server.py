import os
import uuid
import tempfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, origins="*")

@app.route('/')
def home():
    return jsonify({'status': 'Saveit backend running'})

@app.route('/info', methods=['POST', 'OPTIONS'])
def info():
    if request.method == 'OPTIONS':
        return '', 204
    data = request.json
    url = data.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({'title': info.get('title'), 'thumbnail': info.get('thumbnail')})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['GET', 'POST', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 204
    url = request.args.get('url') or request.json.get('url')
    fmt = request.args.get('format', 'mp4')
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, f'{uuid.uuid4()}.%(ext)s')
    ydl_opts = {
        'format': 'bestaudio/best' if fmt == 'mp3' else 'best',
        'outtmpl': out,
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                files = os.listdir(tmp)
                filename = os.path.join(tmp, files[0])
            return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
