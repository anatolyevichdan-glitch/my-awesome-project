DON'T LOOK BACK - EP1 project. Procedural 2.5D (Python/PIL/numpy).
render.py renders frames/%05d.jpg (1080x1920, 30fps, 108s); scenes_a/b/c.py = scene timeline; rig.py = characters; world.py = environments; comp.py = lighting/fx.
audio/: music.wav, ambience.wav, sfx.wav separate stems; mix_no_voice.wav = mix; audio.py regenerates.
./assemble.sh [narration.mp3] encodes the videos; narration runs ~108.4s and matches the 108s timeline.
