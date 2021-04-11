FROM python:3.9-slim
# slim=debian-based. Not using alpine because it has poor python3 support.
ENV PYTHONUNBUFFERED=1
WORKDIR /PyBoss

RUN apt-get update -qq && apt-get install -y -qq ffmpeg
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .
