from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import traceback

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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
        ydl_opts = {
            'restrictfilenames': True,
            'noplaylist': True,
            'concurrent_fragment_downloads': 4,
            'http_chunk_size': 10485760,
            'buffersize': 1024 * 64,
            'retries': 10,
            'fragment_retries': 10,
            'quiet': False,
            'no_warnings': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web']
                }
            }
        }

        # Check for cookies.txt in both default working directory and Render's /etc/secrets path
        possible_cookie_paths = [
            os.path.join(os.getcwd(), 'cookies.txt'),
            '/etc/secrets/cookies.txt',
            os.path.join(os.path.dirname(__file__), 'cookies.txt')
        ]
        
        for cpath in possible_cookie_paths:
            if os.path.exists(cpath):
                ydl_opts['cookiefile'] = cpath
                print(f"Loaded cookies from: {cpath}")
                break

        # Configure formats
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
    app.run(port=5000, debug=True)