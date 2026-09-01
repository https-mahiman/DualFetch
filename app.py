from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import shutil
import traceback

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DOWNLOAD_FOLDER = "downloads"
CONVERTED_FOLDER = "converted"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def get_writable_cookie_path():
    """Copies read-only Render secret cookies to a writable /tmp directory."""
    render_secret_path = '/etc/secrets/cookies.txt'
    local_cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
    writable_path = '/tmp/cookies.txt'

    source_path = None
    if os.path.exists(render_secret_path):
        source_path = render_secret_path
    elif os.path.exists(local_cookie_path):
        source_path = local_cookie_path

    if source_path:
        try:
            shutil.copyfile(source_path, writable_path)
            return writable_path
        except Exception as err:
            print(f"Failed to copy cookies to /tmp: {err}")
            return source_path
    return None

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
            # Allow generic Web/mweb clients when using cookies
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'mweb', 'tv_embedded']
                }
            }
        }

        # Mount writable cookie path
        cookie_file = get_writable_cookie_path()
        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file
            print(f"Using writable cookies at: {cookie_file}")

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
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })

        # Execute extraction and download
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
    app.run(port=5000, debug=True)