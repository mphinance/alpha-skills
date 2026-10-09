---
name: audio-production
description: Transcribe, surgically edit, master, and clean audio recordings (trading streams, community calls, podcasts, meetings) with automated silence/fluff trimming, noise reduction, loudness normalization (-16 LUFS), and transcription via OpenRouter mai-transcribe-2 or local faster-whisper. Always consolidate output into a single dedicated folder.
---

# Audio Production & Mastering Skill

A complete pipeline for transcribing, editing, mastering, and bundling spoken audio for Substack podcasts, YouTube replays, community calls, and dev logs.

## When to Use

- Transcribing audio files (`.mp3`, `.wav`, `.m4a`, `.webm`) into clean Markdown with timestamps and speaker labels.
- Analyzing an unedited recording for dead air, mic feedback, sensitive disclosures, or rambling.
- Performing surgical cuts with smooth crossfades (`acrossfade`) so transitions sound completely natural.
- Mastering audio to broadcast/podcast standard (**-16 LUFS**, 80Hz highpass filter, adaptive noise suppression).
- Packaging deliverables: Always consolidate the cleaned audio and structured markdown transcript into a single unified directory (e.g. `clean_session/` or `dist/audio/`).

---

## 🎙️ Transcription Engines

### 1. Cloud STT: OpenRouter `microsoft/mai-transcribe-2`
- **Cost/Speed:** ~$0.10/hr (half the price of Whisper Large v3 Turbo), 10x faster on long-form audio.
- **Key Location:** `~/projects/openrouter/.env_openrouter` or `$OPENROUTER_API_KEY`.
- **Endpoint:** `https://openrouter.ai/api/v1/audio/transcriptions`
- **25MB request cap, handled automatically.** OpenRouter's own docs cap a
  single transcription request at 25MB. A single `transcribe_openrouter()`
  call over that size will fail outright -- **use
  `transcribe_long_openrouter()` for anything that might be long**, which
  splits by measured bitrate (not a fixed duration guess, since a
  32kbps voice memo and a 320kbps studio recording need very different
  chunk lengths to land under the same byte cap), transcribes each piece,
  and stitches the timestamps back onto the *original* file's timeline.
  Verified 2026-09-15 against a real 57-minute / 110MB / 257kbps file:
  558 segments, zero backward-jumping timestamps across chunk boundaries,
  last segment's end time matched the file's true duration to five decimal
  places, transcribed in 64 seconds for about $0.10.
  ```python
  from audio_pipeline import transcribe_long_openrouter
  result = transcribe_long_openrouter("recording.m4a")  # any length, any size
  # result = {"text": "...", "segments": [{"start": 0.0, "end": 7.56, "text": "..."}, ...]}
  ```
  Or from the CLI: `python3 audio_pipeline.py -i recording.m4a --transcribe out.json`.
  Only reach for the unwrapped `transcribe_openrouter()` directly when the
  input is already known to be under 15MB (its internal safety margin below
  the 25MB cap).

### 2. Local Fallback: `faster-whisper`
- Runs directly on CPU/GPU using CTranslate2 int8 quantization, no size cap
  of its own (handles long files directly, no chunking wrapper needed).
  ```python
  from audio_pipeline import transcribe_whisper_local
  result = transcribe_whisper_local("audio.mp3", model_size="base.en")
  # same {"text", "segments"} shape as the OpenRouter path
  ```

---

## ✂️ The Editorial Framework: What to Cut

When reviewing raw streams or community calls, audit for:

1. **🚨 Liability & Sensitive Disclosures (Hard Cut if Public)**:
   - Day-job / employer admissions (e.g., coworkers/partners confessing low work hours).
   - Regulatory edge cases (Series 65/FINRA compliance disclaimers, unauthorized advice).
2. **🔇 Tech Fumbling & Setup Chaos**:
   - Audio feedback, Discord echo, mic permission loops, teaching someone how to server-mute.
   - Start the final cut right where the real substance or opening thesis begins.
3. **⏸️ Dead Air & Screen Waiting**:
   - Multi-second pauses waiting for market open, staring at phones, or frozen screens.
4. **⚠️ Self-Deprecating Fluffs & Missing Code**:
   - Rambling about missing git commits, lost branches, or personal cursing over forgotten UI buttons.
   - If producing for a **Public Cut**, snip cleanly. If producing for a **Private Community Cut**, keep authentic moments but tighten pauses.

---

## ✂️ Doing the Cut: `--remove` vs `--cuts`

`cut_and_master()` (and the `--cuts` CLI flag) always take KEEP segments --
that's what ffmpeg needs, but it's the wrong shape to *reason* about when
auditing a transcript for what's bad or too personal. Use `--remove`
instead: name the ranges you want gone, and `invert_segments()` computes
the keep-segments around them automatically (sorts unsorted input, handles
removals touching the very start/end, verified with unit tests
2026-09-15). This is the natural fit for the editorial framework above --
read the timestamped transcript, list the [start, end] ranges that match
the Hard Cut / Tech Fumbling / Dead Air / Fluff criteria, pass them to
`--remove`, done.

```bash
python3 audio_pipeline.py -i recording.m4a \
  --remove '[[612, 649], [1830, 1905]]' \
  -o recording_clean.mp3
```

---

## 🎚️ The Mastering Chain (FFmpeg)

Always apply broadcast mastering to eliminate whisper-to-shout volume swings:

```bash
# 1. High-Pass Filter: Strip mic bumps and AC rumble below 80Hz
# 2. Adaptive Noise Reduction: afftdn=nf=-25
# 3. EBU R128 Podcast Loudness: loudnorm=I=-16:TP=-1.5:LRA=11
ffmpeg -i input.mp3 \
  -filter:a "highpass=f=80,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -c:a libmp3lame -b:a 192k output_mastered.mp3
```

### Seam Crossfading
Never hard-cut audio without a transition. Use a **200ms triangular crossfade** (`acrossfade=d=0.2:c1=tri:c2=tri`) between all segments to prevent clicks and room-tone dropouts.

---

## 📦 Deliverables Rule: Single Output Folder

Whenever producing cleaned audio and transcripts, **never scatter files across root or subdirectories**. Always package them together in one dedicated folder:

```text
clean_session/
├── Session_Clean_Public.mp3                 # Mastered broadcast audio
└── 2026-09-15_Community_Session_Transcript.md # Formatted Markdown transcript
```

The Markdown transcript should contain:
- **Executive Summary**
- **Action Items & Dev Bug Log** (harvested from stream)
- **Full Timestamped Dialogue** with Speaker Tags

### Default destination for Michael's own recordings

For personal audio (podcasts, voice memos, dev streams -- not a one-off
scratch job), the real, established location is
`~/projects/tdpro/mphinance/transcripts/`, matching the file already there
(`2026-09-15_Community_Session_Transcript.md`) -- same naming convention:
`YYYY-MM-DD_Descriptive_Name_Transcript.md`. This isn't just a transcript
archive: it's raw material for two other things in the same project --
`VOICE.md` (the writing-style guide, itself mined from "the pre-AI AfterHour
corpus") gets more authentic material to draw from out of how Michael
actually *talks*, not just what he's already published, and a cleaned
transcript is a legitimate first draft for a Substack post when he asks for
one -- run it past VOICE.md's rules (banned phrases, the sign-off, the tone
rules) rather than treating the raw transcript as publishable as-is.
