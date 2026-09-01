FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg nodejs gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} --timeout 300 app:app"]