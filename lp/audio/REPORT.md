# ПОСЛЕДНИЙ ПАССАЖИР — soundtrack (measured only, not listened to)

Rebuild everything: `cd /tmp/hoplite/workspace/lp/audio && ./build_all.sh` (≈9 min incl. Whisper; `./build_all.sh --nowhisper` ≈3 min; `build.py` synth ~1 min, `mix.py` ~30 s).

## Files
mix_master.wav, stem_{narration,music,ambience,foley,sfx}.wav — 48 kHz, 24-bit, stereo, 6 476 278 samples = 134.9225 s (= narration). Stems sum to master, max error 4.8e-7. event_log.json (all events with times/levels), check_results.json, script_ru.txt.
Optional: mix_master_alt_-16LUFS_limited.wav (master +1.5 dB + true-peak limiter; touches narration peaks, stems do not sum to it).
Code: lib.py (loudness meter, helpers), synth.py (clip synthesis), build.py (stems), mix.py (calibration/guards/master), check.py.

## Master
- Narration: resampled 44.1→48 kHz, ONE global gain +1.455 dB, nothing else (residual vs original×gain 1.2e-7).
- Integrated -17.5 LUFS (ffmpeg ebur128, LRA 6.6), true peak -1.51 dBTP, 0 clipped samples (sample peak 0.839).
- **-16 LUFS is not reachable with gain only**: the narration alone peaks -3.0 dBTP, so the +1.5 dB cap for TP ≤ -1.5 gives -17.5 LUFS. The alt file reaches -16.0 LUFS / -1.6 dBTP with a limiter (≈1.5 dB peak reduction, narration altered). Choose per taste.

## Balance (400 ms momentary K-weighted loudness vs the voice at the same time; windows fully inside speech)
Speech median voice -17.4 LUFS. Closest = loudest relative to voice.
| stem | median | closest | windows within 8 LU |
|---|---|---|---|
| music | -21.8 LU | -18.4 | 0 (0 within 10) |
| ambience | -17.3 | -10.4 | 0 |
| foley | -24.2 | -10.7 | 0 |
| sfx | -23.8 | -9.5 | 0 (2 within 10) |
| all non-voice summed | -15.0 | -8.5 | 0 (61 within 10) |
Excluded: the sting window 132.1–133.0 (sfx stem has 5 windows within 8 LU there — the only deliberate exception, sting allowed up to the voice's typical loudness). 100 ms short-term foley/sfx power stays ≤ -6.7 / -7.3 LU vs voice momentary (p99 -11).
Ducking: music -4 dB under speech (attack 0.12 s / release 0.5 s) plus a hard guard that keeps it ≥18 LU under the instantaneous voice (guard cuts up to 21 dB briefly at voice dips). Pauses: music does not really come up (pause median measured lower than speech because pauses are short, 0.3–0.5 s); allowed in design but not required.
All stems have per-stem and summed guards (smooth gain curves, ≥8.5 LU under voice incl. dips) — effects whose design levels were louder were automatically reduced (e.g. impact at 44.5 is under speech, peak ≈ -15 dBFS; runs at 60.92/61.22/99.57 are reduced by speech overlap).

## Special regions
- 127.1–132.3: music exactly 0 (fades 126.96–127.1), foley 0, sfx ≤ -68 dBFS RMS, ambience -54.0 dBFS RMS; all non-voice -53.8 dBFS RMS (≤ -50 ✓). Heartbeat stops at 127.0.
- 108.6–112.6: ambience -47.3, music -53.2 dBFS RMS (faint rain, near silence); music returns from 112.6.
- 92.55 blackout: music + interior bed gone, non-voice (music+ambience) -72.7 dBFS RMS at 92.6–93.3; engine idle returns 93.4–93.55; music returns softly from 94.6.
- Sting 132.3: peak -14.5 dBFS (sfx stem), master true peak in 132–133 s -10.2 dBTP (with narration tail), ≤0.5 s audible; all non-voice faded 132.65–132.8, **exactly 0 after 132.8** (max abs 0.0); no title tone added (optional, skipped).
- Sting is intentionally not louder than the narration's typical loudness (task rule) → the "biggest accent" is large by contrast with the preceding near-silence, not by peak level. If the parent wants it harder, raise STING_REL in mix.py (e.g. -3) and re-check TP/Whisper.

## Intelligibility (faster-whisper small, ru, vs script_ru.txt, digits normalised, 262 words)
mix WER 0.0153, narration-only WER 0.0229 → delta -0.0076 (≤ +0.01 ✓). Window 130–133 s (word «обгорело» under the sting) transcribed identically in mix and narration-only: «только его лицо полностью обгорело.»

## Notes / not done
- Not auditioned by a human; everything is procedural (no samples). Effect realism (squeals, brake screech, diesel) is synthetic.
- The impact at 44.5 sits under narration (words «Сзади раздаётся женский голос» run 44.28–46.04), so under the 8 LU rule it is modest (peak ≈ -15 dBFS); big sub content is not counted by K-weighting and is inaudible on phones.
- Reverb: small metal-box IR inside the bus, long wet IR outdoors, phone-band tones for phone sounds. Hum/engine/rain beds are time-switched exterior⇄interior per the timeline.
- Optional title-card tone skipped. dbg*.py are throwaway diagnostics.
