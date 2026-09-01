from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import shutil
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get('PORT', '5000'))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted')

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)


def get_cookie_file():
    """Return a readable cookie file path for sites that require authentication."""
    candidate_paths = [
        os.environ.get('YOUTUBE_COOKIES'),
        os.environ.get('COOKIE_FILE'),
        '/etc/secrets/cookies.txt',
        os.path.join(BASE_DIR, 'cookies.txt'),
        os.path.join(os.getcwd(), 'cookies.txt'),
    ]

    seen = set()
    for raw_path in candidate_paths:
        if not raw_path:
            continue
        if raw_path in seen:
            continue
        seen.add(raw_path)

        if not os.path.exists(raw_path):
            continue

        try:
            if os.path.isfile(raw_path):
                if os.access(raw_path, os.R_OK):
                    source = raw_path
                    writable_path = '/tmp/cookies.txt'
                    try:
                        if source != writable_path:
                            shutil.copyfile(source, writable_path)
                        return writable_path
                    except Exception as err:
                        print(f"Failed to copy cookies to /tmp: {err}")
                        return source
        except Exception as err:
            print(f"Cookie path check failed for {raw_path}: {err}")

    return None

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'message': 'DualFetch Media API is running successfully!',
        'port': PORT,
    }), 200

@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({
        'status': 'ok',
        'service': 'dualfetch-media-api'
    }), 200

@app.route('/download', methods=['POST'])
def download_media():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    download_type = data.get('type', 'video').lower()

    if not url:
        return jsonify({'success': False, 'error': 'Please provide a valid URL'}), 400

    is_youtube_url = 'youtube.com' in url.lower() or 'youtu.be' in url.lower()
    if is_youtube_url:
        cookie_file = get_cookie_file()
        if not cookie_file:
            return jsonify({
                'success': False,
                'error': 'YouTube requires a valid cookies.txt file. Add cookies.txt to the app root or set YOUTUBE_COOKIES / COOKIE_FILE in the hosting environment.'
            }), 403

    try:
        ydl_opts = {
            'restrictfilenames': True,
            'noplaylist': True,
            'concurrent_fragment_downloads': 4,
            'http_chunk_size': 10485760,
            'buffersize': 1024 * 64,
            'retries': 10,
            'fragment_retries': 10,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'mweb', 'tv_embedded']
                }
            }
        }

        # Mount a writable cookie path to prevent read-only filesystem crash
        cookie_file = get_cookie_file()
        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file
            print(f"Using writable cookies from: {cookie_file}")

        # Universal fallback formats with FFmpeg processing
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
            ydl_opts.update({
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'format': 'bv*+ba/b',
                'merge_output_format': 'mp4',
                'postprocessor_args': {
                    'Merger': ['-c:v', 'copy', '-c:a', 'aac']
                }
            })

        # Process download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'media')
            extractor = info.get('extractor_key', 'Generic')
            base_filepath = os.path.splitext(ydl.prepare_filename(info))[0]

            final_file = f"{base_filepath}.mp3" if download_type == 'audio' else f"{base_filepath}.mp4"
            target_folder = CONVERTED_FOLDER if download_type == 'audio' else DOWNLOAD_FOLDER

        return jsonify({
            'success': True,
            'message': f"{download_type.capitalize()} downloaded successfully!",
            'platform': extractor,
            'title': title,
            'type': download_type,
            'folder': target_folder,
            'file_path': final_file
        }), 200

    except Exception as e:
        error_msg = str(e)
        trace_text = traceback.format_exc()
        print("Backend Download Error:\n", trace_text)
        return jsonify({
            'success': False,
            'error': error_msg,
            'traceback': trace_text
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)