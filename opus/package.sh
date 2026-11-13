#!/bin/bash
# Assemble the seven deliverables into final/deliver/
set -e
O=/tmp/hoplite/workspace/opus; A=/tmp/hoplite/workspace/rem/audio2; S=/tmp/hoplite/workspace/rem/subs2; F=$O/final
D=$F/deliver; rm -rf "$D"; mkdir -p "$D"
cp "$F/DONT_LOOK_BACK_EP1_OPUS_FINAL.mp4" "$F/DONT_LOOK_BACK_EP1_OPUS_NO_SUBS.mp4" "$D/"
cp "$S/subs.ass" "$D/DONT_LOOK_BACK_EP1_OPUS_SUBTITLES.ass"
cp "$S/subs.srt" "$D/DONT_LOOK_BACK_EP1_OPUS_SUBTITLES.srt"
T=$(mktemp -d)

mkdir -p "$T/STEMS"
cp "$A/mix_master.wav" "$A"/stem_narration.wav "$A"/stem_music.wav "$A"/stem_ambience.wav "$A"/stem_foley.wav "$A"/stem_sfx.wav "$T/STEMS/"
cp "$A/foley_events.json" "$A/check_results.json" "$A/REPORT.md" "$T/STEMS/"
(cd "$T" && zip -qr "$D/DONT_LOOK_BACK_EP1_OPUS_AUDIO_STEMS.zip" STEMS)

mkdir -p "$T/PREVIEWS"
cp "$O"/out/TEST_*.mp4 /tmp/verify/opus_turn.png /tmp/verify/opus_expr.png /tmp/verify/ep_contact_final.jpg "$T/PREVIEWS/"
(cd "$T" && zip -qr "$D/DONT_LOOK_BACK_EP1_OPUS_PREVIEWS.zip" PREVIEWS)

P="$T/DONT_LOOK_BACK_EP1_OPUS_PROJECT"
mkdir -p "$P/code/opus" "$P/code/shared" "$P/audio" "$P/subtitles" "$P/fonts" "$P/render"
cp "$O"/*.py "$O/package.sh" "$P/code/opus/"
cp /tmp/hoplite/workspace/rem/rig.py /tmp/hoplite/workspace/rem/gfx.py "$P/code/shared/"
cp "$A"/*.py "$A"/*.json "$A/REPORT.md" "$P/audio/"
cp /tmp/hoplite/workspace/rem/audio/narration_original.mp3 "$P/audio/"
cp -r "$S"/fonts/* "$P/fonts/"
cp "$D"/DONT_LOOK_BACK_EP1_OPUS_SUBTITLES.* "$P/subtitles/"
cp "$D/DONT_LOOK_BACK_EP1_OPUS_NO_SUBS.mp4" "$P/render/"
cp "$O/PROJECT_README.md" "$P/README.md"
(cd "$T" && zip -qr "$D/DONT_LOOK_BACK_EP1_OPUS_PROJECT.zip" DONT_LOOK_BACK_EP1_OPUS_PROJECT)
rm -rf "$T"
ls -la "$D"
