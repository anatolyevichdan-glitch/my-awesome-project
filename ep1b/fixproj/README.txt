DONT LOOK BACK EP1 fixed remake
Render: cd src; python render2.py START END out.mp4 (30fps frames; run halves in parallel), concat, mux audio/mix_final.wav, burn subs/subs_fixed2.ass (ffmpeg ass filter, fontsdir=fonts).
Audio: python mkaudio2.py (needs narr.mp3), then ffmpeg loudnorm I=-16 TP=-1.5.
Note: shots2.py and old rig kept in repo history; shots3-6 are the v2 articulated rig shots.
