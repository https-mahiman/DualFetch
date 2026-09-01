# DualFetch Media API

This project downloads media through a Flask API and uses `yt-dlp` with authenticated browser cookies for YouTube.

## Local cookie export

Run the exporter on a machine where you are already logged in to YouTube in Chrome/Edge/Brave/Firefox:

```bash
python export_cookies.py
```

This creates a `cookies.txt` file in the project root.

## Render secret setup

1. In Render, open your service.
2. Go to Environment.
3. Add a secret file or environment variable:
   - `COOKIE_FILE=/etc/secrets/cookies.txt`
   - `YOUTUBE_COOKIES=/etc/secrets/cookies.txt`
4. Upload a valid `cookies.txt` generated from your browser session.
5. Redeploy the service.

## Browser export notes

The exporter tries to read cookies from installed browsers via `browser-cookie3`.

To generate a valid cookies file manually:

- Open the browser you use for YouTube
- Log in to YouTube
- Export cookies in Netscape format
- Save as `cookies.txt`
- Upload this file to Render as a secret or mount it into the container

## Deployment health

Use:

```bash
curl https://YOUR-APP-URL/healthz
```

This should return a JSON payload with `status: ok`.
