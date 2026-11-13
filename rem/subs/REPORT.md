# Subtitle verification report

Files: `subs_final.ass`, `subs_final.srt`, `subs_events.json` (72 phrases + word list), `preview.png`, `side.png`; build: `build.py` (all params), `voiced.json`.

## Text
Words come from `align.json` (208 words, covers the full audio incl. the tail after «Его лицо меняется»), uppercased, trailing `.,;:` stripped (`?`/`!` kept). No text invented. Faster-whisper `medium` (ru, word timestamps) transcript matches the 208 words 1:1 (only differences: «кто-то», «куда-то», «по-настоящему» split at the hyphen, «Тсс!» transcribed «Тсссс…»).

## Timing verification
1. Forced-aligner words vs Whisper: 55 words differ by >100 ms start or >150 ms end. Nearly all are Whisper end-padding (Whisper ends run 0.1–0.5 s late). Starts differing >0.25 s were checked against an independent 5 ms energy envelope (voiced segments = level > p8 floor + 12 dB):
   - «Ты» 58 (Whisper 29.00, aligner 29.41): voiced segment starts 29.39, Whisper had grabbed the previous word's tail → aligner right.
   - «медленно» 76 (39.14 vs 39.49), «Один» 110 (56.34 vs 56.65), «совершенно» 144 (72.66 vs 72.97), «Его» 169 (84.92 vs 85.29), «и» 196 (100.26 vs 100.62), «не» 66 (34.16 vs 34.38): in every case the voiced onset is within 0–40 ms of the aligner, Whisper is early (it absorbs the preceding pause). Aligner kept.
   - «ты» 134 (Whisper 68.96 vs aligner 68.63): voiced onset 68.62 → aligner right.
2. Low-confidence words: «шаг» 27 (12.62–12.86) — voiced to 13.00, end extended; «к» 79 (41.07–41.09, 20 ms, inside continuous voicing; Whisper 41.12–41.26; it is never a phrase boundary, so no effect); «Тсс!» 81 (aligned 42.13–42.43; energy shows the hiss as one voiced segment 42.11–42.95, Whisper 42.48–43.28 is padded) → onset 42.11, end 42.95.
3. Phrase snapping (96 adjustments listed in `adjust_notes.txt`): phrase start = voiced onset when one lies in [aligned start −120 ms, +30 ms] (aligner sentence-initial words are 0–60 ms late; max shift observed 126 ms), else aligned start. Phrase end = word end, or the voiced-segment end if it lies 30–600 ms later and the next word is >150 ms away (the aligner clips word tails), plus 80 ms hold. Never overlaps the next phrase (display end is cut to next phrase start).
4. Frame policy: start/end rounded to the nearest 30 fps frame; ASS time = `floor(frame*100/30)` centiseconds (max 0.9 cs early relative to the frame instant, so event is never visible a frame early and never a frame late); SRT = round(frame*1000/30) ms. Residual error vs the true voice onset is ≤ ½ frame (16 ms) plus ≤ 1 cs ASS truncation. I cannot claim one-frame accuracy for each word: the aligner itself has ~±30–50 ms uncertainty, verified only by the energy envelope at phrase starts, not by ear.
5. Checks run (`chk.py`): no overlaps; displayed lead −126…+17 ms vs aligner first word, trail +24…+606 ms (>250 ms only for «улице», «видишь себя», «прямо на тебя», «ТСС!», «Один», «только глаза», «Нет» where voiced tail extends beyond the aligned end; «ТСС!» 0.61 s is the hiss).

## Style
- Font: **Oswald Bold** (static wght=700 instance generated from `Oswald[wght].ttf` with fontTools → `fonts/Oswald-Bold-static.ttf`, because libass may ignore variable-font axes). Anton and Bebas Neue files in `fonts/` have NO Cyrillic glyphs (render as .notdef boxes), so they were unusable. Oswald Bold is visually close in condensed heavy construction but is **not** claimed to be the original font; the references are slightly narrower/tighter and a bit heavier. ffmpeg log confirms `Loading font file fonts/Oswald-Bold-static.ttf`; render shows the real face (no fallback). Always burn with `ass=subs_final.ass:fontsdir=<dir with Oswald-Bold-static.ttf>`; copy `fonts/Oswald-Bold-static.ttf` along with the ASS.
- ASS size 151 (cap height ≈ 71 px at 1080 wide, refs ≈ 70–75), outline 9, shadow 4 (alpha 0x78), spacing 0.5, Alignment 2, MarginV 272 → ink bottom ≈ y 1640, width ≤ ~880 px, max 2 lines (breaks inserted by width; WrapStyle 2).
- Animation per event: `\fad(70,80)`, scale 94→100 % over 120 ms, no bounce.
- Colours: yellow `&H0000D4FF` (#FFD400) on 20 words (НЕ ОБОРАЧИВАЙСЯ, КАМЕРА, ЧЁРНЫЙ СИЛУЭТ, ОТРАЖЕНИИ ВИТРИНЫ, ОТРАЖЕНИЕ, ПАЛЕЦ, ТСС, СООБЩЕНИЕ ×2, ОДИН/ВТОРОЙ/ТРЕТИЙ, ТЫ САМ, ИСПУГАННЫМ, НАСТОЯЩИЙ…); red `&H002020E0` (#E02020) on 14 words (ОН ВНУТРИ ТЕБЯ, СОВЕРШЕННО ЧЁРНЫЕ, ОН НАШЁЛ НАС ОБОИХ, ОГРОМНАЯ ЧЁРНАЯ ФИГУРА, ПРОДОЛЖЕНИЕ СЛЕДУЕТ). Edit in `build.py` (`P` list).
- Phrase of 4 words «Он нашёл нас обоих» etc. are split on two lines when >860 px or ≥7 words.

## Not verified
- No listening check by ear; alignment confirmed only against energy/Whisper analysis.
- Preview rendered with libass via ffmpeg on a flat background (no moving fade check by eye, only static frames at 10 moments).
- «Чёрный экран.» is shown as spoken (105.4 s).
