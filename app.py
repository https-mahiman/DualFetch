from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = "downloads"
CONVERTED_FOLDER = "converted"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'message': 'DualFetch Media API is running successfully!'
    }), 200

@app.route('/download', methods=['POST'])
def download_media():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    download_type = data.get('type', 'video').lower()

    if not url:
        return jsonify({'success': False, 'error': 'Please provide a valid URL'}), 400

    try:
        # Base speed-optimized options
        ydl_opts = {
    'restrictfilenames': True,
    'noplaylist': True,
    
    # Speed & Network Settings
    'concurrent_fragment_downloads': 8,
    'http_chunk_size': 10485760,
    'buffersize': 1024 * 64,
    'retries': 10,
    'fragment_retries': 10,

    # Browser Impersonation (Bypasses Cloudflare 403)
    'impersonate': 'chrome',
    'extractor_args': {
        'youtube': {
            'player_client': ['tv_embedded', 'creator', 'mweb', 'ios', 'android'],
            'player_skip': ['webpage', 'configs']
        },
        'generic': {
            'impersonate': ['chrome']
        }
    }
}

        # Auto-detect cookies.txt if provided in root folder
        cookie_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        if download_type == 'audio':
            ydl_opts.update({
                'outtmpl': os.path.join(CONVERTED_FOLDER, '%(title)s.%(ext)s'),
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # Direct stream muxing (Instant container merge without CPU re-encoding)
            ydl_opts.update({
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })

        # Process the download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'media')
            extractor = info.get('extractor_key', 'Generic')
            base_filepath = os.path.splitext(ydl.prepare_filename(info))[0]

            if download_type == 'audio':
                final_file = f"{base_filepath}.mp3"
                target_folder = CONVERTED_FOLDER
            else:
                final_file = f"{base_filepath}.mp4"
                target_folder = DOWNLOAD_FOLDER

        return jsonify({
            'success': True,
            'message': f"{download_type.capitalize()} downloaded successfully!",
            'platform': extractor,
            'title': title,
            'type': download_type,
            'folder': target_folder,
            'file_path': final_file
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)