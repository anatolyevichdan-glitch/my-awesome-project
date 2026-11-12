#!/bin/bash
# Assemble deliverables from rendered frames + audio stems.  Usage: ./assemble.sh [narration.mp3]
set -e
cd "$(dirname "$0")"
mkdir -p out
ffmpeg -y -framerate 30 -i frames/%05d.jpg -c:v libx264 -preset veryfast -crf 26 -maxrate 3200k -bufsize 6400k -pix_fmt yuv420p -movflags +faststart out/DONT_LOOK_BACK_EP1_CLEAN.mp4
ffmpeg -y -i out/DONT_LOOK_BACK_EP1_CLEAN.mp4 -i audio/mix_no_voice.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart out/DONT_LOOK_BACK_EP1_NO_VOICE.mp4
if [ -n "$1" ]; then
  ffmpeg -y -i out/DONT_LOOK_BACK_EP1_NO_VOICE.mp4 -i "$1" -filter_complex "[0:a]volume=0.55[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k out/PREVIEW_WITH_NARRATION.mp4
fi
