# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential packages
    curl \
    wget \
    git \
    # FFmpeg for video encoding
    ffmpeg \
    # Transmission for torrents
    transmission-daemon \
    transmission-cli \
    # Image processing
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    # Audio processing
    libopus-dev \
    libfdk-aac-dev \
    # Build tools
    build-essential \
    gcc \
    g++ \
    # Other utilities
    unzip \
    aria2 \
    mediainfo \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY . .

# Create necessary directories
RUN mkdir -p /app/downloads \
    /app/encode \
    /app/logs \
    /app/temp \
    /app/thumbnails

# Set permissions
RUN chmod +x /app/bot/__main__.py

# Create transmission config directory
RUN mkdir -p /root/.config/transmission-daemon

# Create transmission settings
RUN echo '{\
    "alt-speed-down": 50,\
    "alt-speed-enabled": false,\
    "alt-speed-time-begin": 540,\
    "alt-speed-time-day": 127,\
    "alt-speed-time-enabled": false,\
    "alt-speed-time-end": 1020,\
    "alt-speed-up": 50,\
    "bind-address-ipv4": "0.0.0.0",\
    "bind-address-ipv6": "::",\
    "blocklist-enabled": false,\
    "blocklist-url": "http://www.example.com/blocklist",\
    "cache-size-mb": 4,\
    "dht-enabled": true,\
    "download-dir": "/app/downloads",\
    "download-queue-enabled": true,\
    "download-queue-size": 5,\
    "encryption": 1,\
    "idle-seeding-limit": 30,\
    "idle-seeding-limit-enabled": false,\
    "incomplete-dir": "/app/downloads/incomplete",\
    "incomplete-dir-enabled": true,\
    "lpd-enabled": false,\
    "message-level": 2,\
    "peer-congestion-algorithm": "",\
    "peer-id-ttl-hours": 6,\
    "peer-limit-global": 200,\
    "peer-limit-per-torrent": 50,\
    "peer-port": 51413,\
    "peer-port-random-high": 65535,\
    "peer-port-random-low": 49152,\
    "peer-port-random-on-start": false,\
    "peer-socket-tos": "default",\
    "pex-enabled": true,\
    "port-forwarding-enabled": true,\
    "preallocation": 1,\
    "prefetch-enabled": true,\
    "queue-stalled-enabled": true,\
    "queue-stalled-minutes": 30,\
    "ratio-limit": 2,\
    "ratio-limit-enabled": false,\
    "rename-partial-files": true,\
    "rpc-authentication-required": false,\
    "rpc-bind-address": "0.0.0.0",\
    "rpc-enabled": true,\
    "rpc-host-whitelist": "",\
    "rpc-host-whitelist-enabled": true,\
    "rpc-password": "{c8c85e31e7bec8ff4d89ad1adaaaa0b0f31ead6dQPzNy5aw",\
    "rpc-port": 9091,\
    "rpc-url": "/transmission/",\
    "rpc-username": "",\
    "rpc-whitelist": "127.*.*.*,10.*.*.*,192.168.*.*",\
    "rpc-whitelist-enabled": true,\
    "scrape-paused-torrents-enabled": true,\
    "script-torrent-done-enabled": false,\
    "script-torrent-done-filename": "",\
    "seed-queue-enabled": false,\
    "seed-queue-size": 10,\
    "speed-limit-down": 100,\
    "speed-limit-down-enabled": false,\
    "speed-limit-up": 100,\
    "speed-limit-up-enabled": false,\
    "start-added-torrents": true,\
    "trash-original-torrent-files": false,\
    "umask": 18,\
    "upload-slots-per-torrent": 14,\
    "utp-enabled": true\
}' > /root/.config/transmission-daemon/settings.json

# Expose ports
EXPOSE 9091 51413

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting Transmission daemon..."\n\
transmission-daemon --foreground --log-info --logfile /app/logs/transmission.log &\n\
sleep 5\n\
echo "Starting Anime Bot..."\n\
cd /app\n\
python3 -m bot\n\
' > /app/start.sh && chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9091/transmission/rpc || exit 1

# Set the default command
CMD ["/app/start.sh"]
