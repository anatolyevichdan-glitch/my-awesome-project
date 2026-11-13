Don't Look Back EP1 remake - procedural 2D horror animation
Run with python venv (numpy, pillow, aggdraw, scipy) + ffmpeg:
 1) python render.py START END out.mp4 (frames at 30fps, 0..3252; split in parts and concat)
 2) python mkaudio.py (needs narr.mp3 + words) -> AUDIO_MIX.wav
 3) python mksrt.py -> subs.srt
 4) mux with ffmpeg; burn subs with subtitles filter.
Shots: shots1.py (A-F, 0-58.7s), shots2.py (G-L, 58.7-105s); end card in render.py.
