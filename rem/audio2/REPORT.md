# Soundtrack v2 (rain, restrained accents)

Master: -16.0 LUFS integrated, LRA 5.6 LU, true peak -1.8 dBTP (ffmpeg ebur128 peak=true), 0 clipped samples (peak 0.81 FS).
Voice vs music during speech: music is 18.2 dB below the voice (RMS, >80 Hz; 15.8 dB full band). Music sits ~-33 dBFS in pauses and is present (>-70 dBFS) for 99.6% of the first 105 s. During speech SFX is ~15 dB, ambience ~23 dB, foley ~29 dB below the voice.
Whisper (small, ru) WER: mix 0.028, narration alone 0.019. Not listened to by a human; measurements only.

## Changes
- Narration untouched: only a global gain and the shared limiter (the previous version's EQ/compression is removed). Creature-voice processing and the «Тсс» reverb tail removed.
- Removed: inside_tone (51.8), black-eyes rumble/shimmer (71.8), creature voice (102.84), lamp pitch-down tones, collision ring, black-cut tail tones.
- Music: fade-in 0-1.5 s, fade-out 105.5-108.3 s to near silence; level +3 dB (-22 dB re voice). Drone / dissonant tones / metallic resonances, slow tension curve, no percussion or stings.
- Ambience: rain, drips/puddle plinks, distant city hum, wind, lamp buzz; fades over 105.5-108.3 s (no hard cut).
- Foley reads foley_events.json (gain in dB, default 0; kinds step/run_step/rustle/breath/impact/scuff/splash; who hero/creature). Steps wetter, new splash kind, creature steps softer/lower. Default cadence if file absent (placeholder walk 24-36 s, splashes 59.7-64.4 s). See foley_events.example.json.

## Accent list (event_log.json)
- 7.9: shadow swell (7.9-11.6, low, no hit)
- 17.6 / 18.05: phone vibration, two muffled pulses; 19.0: soft notification
- 38.6-43.4: reflection dropout (music/ambience/foley dip); glass squeak 40.95 very quiet
- 45.0: notification (same tone); 50.2: quieter, shorter notification (non-prominent)
- 56.60 / 57.37 / 58.20: lamps, clunk + dying buzz
- 59.1: escape whoosh (footsteps from foley)
- 64.9: collision, cloth + dull thud; dip to 66.6
- 95.2: reveal, slow deep swell 94.5-101.8 + distant groan 95.2-100.8

## Re-run
`cd /tmp/hoplite/workspace/rem/audio2 && /tmp/venv/bin/python mix.py` takes ~17 s (music/ambience/sfx cached in cache/). `--rebuild` regenerates everything (~45 s). check.py (~3 min, Whisper) verifies; analyze.py prints per-stem levels.

## Files
mix_master.wav, stem_{narration,music,ambience,foley,sfx}.wav (48 kHz/24-bit stereo, 5203200 samples each, sum to master, error 5e-7), music_only.wav, sfx_only.wav (foley+sfx), sound_test.wav (master 36-60 s), event_log.json, check_results.json.

## Uncertain
- The 41 Hz shadow swell and reveal sub are inaudible on phone speakers.
- Foley timing is a placeholder until the animator's file arrives.
