# DON'T LOOK BACK — Episode 1 (OPUS rebuild) — editable project

- `code/opus/episode.py` — full 36-shot timeline; every shot is a function of episode time.
- `code/opus/toon.py`, `motion.py`, `creature2.py`, `world.py` — character renderer, walk/run/stand motion, creature, environments.
- `code/opus/opening.py`, `reflection.py` — opening and reflection sequences (the reviewed gate shots, reused).
- `code/opus/render_episode.py` — `python render_episode.py all 12 2` renders segments, muxes the mix, burns subtitles.
- `code/opus/foley_gen.py` — derives `foley_events.json` from the animation's real foot contacts.
- `code/opus/contact.py` — contact sheet of any timestamps for review.
- `audio/` — original ElevenLabs narration (unchanged), mix/SFX scripts; `python mix.py` rebuilds stems and master.
- `subtitles/` — ASS (styled, Inter Bold from `fonts/`) and SRT.
- `render/` — the clean (no subtitles) master render.

Dependencies: Python 3 with skia-python, numpy, pillow; ffmpeg with libass.
