FROM python:3.10-slim-bullseye

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

# Update and install all required OS-level packages
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
       git wget pv jq python3-dev mediainfo gcc \
       libsm6 libxext6 libfontconfig1 libxrender1 libgl1-mesa-glx \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Copy static ffmpeg binaries
COPY --from=mwader/static-ffmpeg:6.1 /ffmpeg  /bin/ffmpeg
COPY --from=mwader/static-ffmpeg:6.1 /ffprobe /bin/ffprobe

COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "bot"]
