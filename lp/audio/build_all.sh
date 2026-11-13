#!/bin/bash
# One command rebuilds the whole soundtrack: synthesis -> calibrated mix/stems -> optional loud alt master -> measurements (incl. Whisper WER).
set -e
cd "$(dirname "$0")"
PY=${PY:-/tmp/venv/bin/python}
$PY build.py && $PY mix.py
# optional alternate master: +1.5 dB and a true-peak limiter -> -16 LUFS (touches narration peaks; stems do not sum to it)
ffmpeg -y -loglevel error -i mix_master.wav -af "volume=1.5dB,alimiter=limit=0.82:attack=5:release=60:level=0" -c:a pcm_s24le mix_master_alt_-16LUFS_limited.wav
$PY check.py "$@"
