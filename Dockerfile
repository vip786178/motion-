#FROM python:3.9.7-slim-buster
FROM python:3.10.8-slim-buster

RUN apt-get update -y && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends gcc libffi-dev musl-dev ffmpeg aria2 python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/
RUN python -m pip install --upgrade pip
ENV COOKIES_FILE_PATH="/modules/youtube_cookies.txt"
CMD gunicorn app:app & python3 modules/main.py
RUN pip install -U yt-dlp
ENV COOKIES_FILE_PATH="/modules/youtube_cookies.txt"
CMD gunicorn app:app & python3 modules/main.py