# DON'T LOOK BACK ep.1 – sound design report

All sound is synthesized procedurally and seeded (numpy/scipy only, no samples). The narration is the original MP3 (108.356 s), never replaced or time-stretched; it only gets HP 70 Hz, +2 dB at 3.5 kHz, -1 dB at 250 Hz and a gentle 1.8:1 compressor.

## Files (all 48 kHz stereo, 24-bit PCM, exactly 108.4 s, t=0 aligned)
`stem_narration.wav stem_music.wav stem_ambience.wav stem_foley.wav stem_sfx.wav mix_master.wav music_only.wav sfx_only.wav (=foley+sfx)`, `event_log.json`, `check_results.json`, sources `dsp.py build.py build_sfx.py mix.py check.py`.
Stems are at their in-mix level and sum to the master (max error 5e-7), so each stem already carries the master gain and the shared limiter.

Re-run: `python mix.py` (music/ambience/sfx are cached in `cache/`; `--rebuild` to regenerate). Foley is rebuilt on every run and reads `foley_events.json` if present (list of `{t, kind: step|run_step|rustle|breath|impact|scuff, foot: -1|1, gain, [who:"creature"]}`; breath: foot -1 = inhale, +1 = exhale; unknown kinds fall back to rustle). `python check.py` repeats the verification (`--nowhisper` skips the transcription).

## Design
- **Music**: three detuned additive drones (A1; a minor-2nd partner whose interval wanders ~85-125 cents; a tritone that enters with tension), a 36.7 Hz sub with a slow soft-sine pulse (~0.4 Hz, not percussion), a quiet FM texture, resonant-noise cluster pad, dark air, plus 8 distant inharmonic metallic resonances (bar partials 1/2.76/5.4/8.93/13.34, soft bowed onset, 8 s reverb). The bed goes through a synthetic 6 s exponential-decay noise IR. Fade in from 0 s, tension swell to 95.5 s, thins to near silence from 106.7 s.
- **Ambience**: stereo rain (hiss + drops + puddle plinks, bright/dull crossfade per location), distant traffic with a few pass-bys, gusting wind rising 95-105 s, streetlight buzz (three lamps with a different 100 Hz hum each, dying at 56.6/57.4/58.2 s; layers drop out: traffic, wind, rain brightness), tight 0.45 s IR wet layer in the alley 59-64.5, courtyard window hum, hard cut at 105.4 s and a faint room-tone tail. Reflection dip 38.6-43.4 and a post-impact dip 64.9-66.6 apply to music/ambience/foley.
- **Foley**: wet-pavement steps, run steps, cloth rustle, breath, body impact, a shoe scuff. Creature steps are heavier and slower, with a soft low thump. Default cadence follows the brief (walk 1.9 steps/s, 2.6 steps/s to 14.3 s, run 3.0 to 4.2 steps/s from 59.1 to 64.85 s, breath 60.6-63.0 s, impact 64.9 s, grab 74.9 s, release 90.4 s).
- **Mix**: sidechain ducking from the voice envelope (attack 30 ms, release 400 ms): music -8 dB, ambience -6 dB, foley and sfx -3 dB. Music is calibrated to -25 dB RMS (>80 Hz) vs the voice's loud-speech level (V = 95th percentile of 50 ms RMS) while the narrator speaks. A look-ahead 4x-oversampled peak limiter (shared gain curve for all stems) sits on the master.

## Prominent accents (10 moments, 16 individual sounds)
| # | t (s) | Moment |
|---|---|---|
|1|1.2-3.8|shadow: low swell + sub pressure change|
|2|17.6 / 18.05; 19.0|phone vibration (2 pulses, muffled); soft notification|
|3|38.6-43.4; 40.95; 42.1|reflection: air-pressure dropout (no stinger), skin-on-glass squeak, breathy reverb tail of "Тсс"|
|4|45.0; 50.2; 51.8|second and third notifications (same tone, third shorter); low tonal swell|
|5|56.6 / 57.4 / 58.2|lamps: clunk + dying buzz + pitch-down tone, each different|
|7|64.9|collision: one dull impact + ringing silence|
|8|71.8|black eyes: restrained rumble + thin shimmer|
|9|95.2|rooftop: sub swell (94.5-101.8) + distant metallic groan|
|10|102.84|creature voice: narration segment -3 st, low-passed, 70 ms double + 2.4 s reverb|
|11|105.4|cut to black: near silence with a faint low tail|

Moment 6 (running) has foley only, as requested. Counted as meaningful moments there are 10, which is in the 8-12 range. The minimum gap between individual prominent sounds is 0.8 s (the three lamps, intentionally).

## Measured results (ffmpeg ebur128, peak=true; see check_results.json)
- **Master**: integrated -16.0 LUFS, LRA 4.4 LU, true peak -1.8 dBTP (limit -1.5), no clipped samples (sample peak 0.812). Short-term (3 s) max -11.8 LUFS, 10th percentile -18.7 LUFS.
- **Limiter**: it reduces more than 0.5 dB on only 0.12 % of samples, max 2.2 dB. The cause is the original narration's own peaks (-2.3 dBTP at -21.4 LUFS) needing +5.4 dB.
- **Music vs voice**: 22.6 dB below the voice's 95th-percentile level during speech (full band). Per-segment average music-minus-voice runs from -17 dB (opening) to -11 dB (rooftop), widening to -30 dB at the end. Music is above -70 dBFS for 99 % of the first 105 s.
- **Foley**: peak -23 dBFS vs voice peak -1.5 dBFS (about 22 dB lower).
- **Accents**: individual event windows sit roughly 14-25 dB below the voice in the same second (>150 Hz). The rooftop and eyes sub-bass has more full-band energy than that figure shows.
- **Intelligibility** (faster-whisper small, ru, vs the script, 211 words): final mix WER 0.028, narration alone WER 0.024. Both miss the same words ("Тсс", "нас обоих"), so the mix adds about one word-level difference. Whisper's own errors dominate.

## Honest limitations
- I cannot listen: levels, timbres and balance were checked only by measurement, spectral reasoning and the transcription test. A real listen on headphones and a phone speaker is still needed. The most likely tweaks are music level (`MUSIC_DB`), ambience level (`AMB_DB`) and the sub-bass amounts at 1.2 s and 95 s.
- Sub-bass content (34-48 Hz) will not reproduce on phone speakers. The mid layers (groan, shimmer, notification, lamp tones) carry those moments there.
- The default foley cadence is a guess. Replace it with `foley_events.json` from the animation and re-run `python mix.py`.
- The creature voice uses a simple phase-vocoder pitch shift, so some phasiness is expected; that suits the effect. It sits on top of the original word (dry 0.8, reverb 1.2 relative gain in the sfx stem, sfx ducked 3 dB under voice); the transcription test passed with it in the mix.
- The notification tone is a synthetic two-note bell, not a recorded phone sound.
