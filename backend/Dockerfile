# backend/Dockerfile
FROM python:3.9

WORKDIR /app

COPY user-requirements.txt .

RUN apt-get update
RUN apt-get install -y portaudio19-dev python3-pyaudio ffmpeg libsm6 libxext6 libgl1 libglib2.0-0 libgl1-mesa-glx libfontconfig1 libxrender1

RUN pip install --no-cache-dir -r user-requirements.txt

COPY . .

CMD ["gunicorn", "flaskserver:app", "-b", "0.0.0.0:7000", "--workers", "1"]
