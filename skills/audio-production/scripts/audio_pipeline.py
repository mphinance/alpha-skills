#!/usr/bin/env python3
"""
Audio Production Pipeline:
1. Fast transcription using OpenRouter STT (microsoft/mai-transcribe-2) or local faster-whisper.
2. Surgical splicing with crossfades to remove dead air, feedback, sensitive slip-ups.
3. Broadcast mastering (-16 LUFS loudnorm, highpass 80Hz, adaptive noise reduction).
4. Clean bundle export to unified destination folder.
"""

import os
import sys
import argparse
import subprocess
import json
import re

OPENROUTER_STT_URL = "https://openrouter.ai/api/v1/audio/transcriptions"

# OpenRouter's transcription endpoint caps multipart uploads at 25MB (its
# own docs: "an OpenAI-style multipart file up to 25 MB"). Chunk well under
# that, not right up against it -- bitrate estimation below is a ceiling
# assumption (VBR / metadata can push a file bigger than duration x bitrate
# alone would suggest), and there's no value in cutting it close for a
# ~$0.10/hr API call. 15MB leaves real headroom at any normal voice-memo
# bitrate while keeping chunk counts (and therefore API calls) low.
MAX_CHUNK_BYTES = 15 * 1024 * 1024

def get_openrouter_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    env_file = os.path.expanduser("~/projects/openrouter/.env_openrouter")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.strip().split("=", 1)[1]
    return None

def get_audio_duration(audio_file):
    """Duration in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_file,
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed to read duration: {res.stderr}")
    return float(res.stdout.strip())

def transcribe_openrouter(audio_file, model="microsoft/mai-transcribe-2", timestamps=True):
    """Transcribe a single audio file (must already be under OpenRouter's
    25MB request cap -- see transcribe_long_openrouter for files that
    aren't) via OpenRouter STT API.

    With timestamps=True (default), requests response_format=verbose_json
    so the result carries segment-level start/end times -- required for
    precise editing (cut_and_master works in seconds, not "somewhere in
    the middle of paragraph 3"). Returns {"text": str, "segments": [...]}
    either way; segments is [] if the provider didn't return any (verified
    live 2026-09-15 that mai-transcribe-2 does).
    """
    key = get_openrouter_key()
    if not key:
        raise RuntimeError("No OPENROUTER_API_KEY found in env or ~/projects/openrouter/.env_openrouter")

    cmd = [
        "curl", "-s", "-X", "POST", OPENROUTER_STT_URL,
        "-H", f"Authorization: Bearer {key}",
        "-F", f"file=@{audio_file}",
        "-F", f"model={model}",
    ]
    if timestamps:
        cmd += ["-F", "response_format=verbose_json"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"OpenRouter STT failed: {res.stderr}")
    data = json.loads(res.stdout)
    if "error" in data:
        raise RuntimeError(f"OpenRouter STT error: {data['error']}")
    segments = [
        {"start": s.get("start", 0.0), "end": s.get("end", 0.0), "text": (s.get("text") or "").strip()}
        for s in (data.get("segments") or [])
    ]
    return {"text": data.get("text", ""), "segments": segments}

def transcribe_long_openrouter(audio_file, model="microsoft/mai-transcribe-2", max_chunk_bytes=MAX_CHUNK_BYTES):
    """Transcribe a file of any length/size by splitting into chunks that
    fit under OpenRouter's 25MB request cap, transcribing each, and
    re-assembling into one timeline spanning the *original* file.

    Sizes chunks by measured bitrate (bytes / duration) rather than a fixed
    duration guess, so this stays correct across wildly different source
    quality (a 320kbps studio recording and a 32kbps voice memo need very
    different chunk lengths to land under the same byte cap). Each chunk's
    segment timestamps are offset by its start time in the original file,
    so the returned segments are directly usable by cut_and_master without
    any further translation -- this is what makes "listen to the
    transcript, tell me what to cut" workable on an hours-long file.
    """
    total_bytes = os.path.getsize(audio_file)
    if total_bytes <= max_chunk_bytes:
        return transcribe_openrouter(audio_file, model=model)

    duration = get_audio_duration(audio_file)
    bytes_per_second = total_bytes / duration
    chunk_seconds = max(30.0, (max_chunk_bytes / bytes_per_second) * 0.9)  # 10% safety margin

    all_text = []
    all_segments = []
    tmp_dir = f"/tmp/audio_pipeline_chunks_{os.getpid()}"
    os.makedirs(tmp_dir, exist_ok=True)
    try:
        offset = 0.0
        chunk_idx = 0
        while offset < duration:
            chunk_path = os.path.join(tmp_dir, f"chunk_{chunk_idx:04d}.mp3")
            cmd = [
                "ffmpeg", "-y", "-ss", str(offset), "-t", str(chunk_seconds),
                "-i", audio_file, "-c:a", "libmp3lame", "-b:a", "96k", chunk_path,
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"ffmpeg chunk split failed at offset {offset}: {res.stderr[-500:]}")
            if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
                break  # ran past the end of the file

            result = transcribe_openrouter(chunk_path, model=model)
            all_text.append(result["text"])
            for seg in result["segments"]:
                all_segments.append({
                    "start": seg["start"] + offset,
                    "end": seg["end"] + offset,
                    "text": seg["text"],
                })
            offset += chunk_seconds
            chunk_idx += 1
    finally:
        for f in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, f))
        os.rmdir(tmp_dir)

    return {"text": " ".join(all_text), "segments": all_segments}

def invert_segments(remove_ranges, total_duration):
    """Given ranges to CUT OUT [(start, end), ...], return the complementary
    KEEP ranges cut_and_master actually wants. Lets the caller (a human or
    an agent reading the transcript) specify what's bad/sensitive/wants
    removing directly, instead of manually computing everything around it.
    """
    remove_ranges = sorted(remove_ranges)
    keep = []
    cursor = 0.0
    for start, end in remove_ranges:
        if start > cursor:
            keep.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < total_duration:
        keep.append((cursor, total_duration))
    return keep

def transcribe_whisper_local(audio_file, model_size="base.en"):
    """Local fallback using faster-whisper. Handles files of any length
    itself (no OpenRouter-style size cap), so no chunking wrapper needed.
    Returns the same {"text": str, "segments": [...]} shape as the
    OpenRouter path for a consistent interface either way.
    """
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_file, beam_size=1)
    results = []
    for s in segments:
        results.append({
            "start": s.start,
            "end": s.end,
            "text": s.text.strip()
        })
    return {"text": " ".join(s["text"] for s in results), "segments": results}

def cut_and_master(input_file, output_file, keep_segments, target_lufs=-16.0, sample_rate=44100, bitrate="192k"):
    """
    Surgically keeps specified segments [ (start, end), ... ],
    applies 200ms triangular crossfades at seams,
    and runs broadcast mastering: highpass(80Hz) + afftdn + loudnorm.
    """
    filter_parts = []
    for i, (start, end) in enumerate(keep_segments):
        filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")

    prev = "a0"
    for i in range(1, len(keep_segments)):
        next_node = f"f{i}" if i < len(keep_segments) - 1 else "merged"
        filter_parts.append(f"[{prev}][a{i}]acrossfade=d=0.2:c1=tri:c2=tri[{next_node}]")
        prev = next_node

    filter_parts.append(f"[merged]highpass=f=80,afftdn=nf=-25,loudnorm=I={target_lufs}:TP=-1.5:LRA=11[out]")
    filter_complex = ";\n".join(filter_parts)

    script_path = f"/tmp/ffmpeg_filter_{os.getpid()}.txt"
    with open(script_path, "w") as f:
        f.write(filter_complex)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex_script", script_path,
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-b:a", bitrate,
        "-ar", str(sample_rate),
        output_file
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {res.stderr[-1000:]}")
    finally:
        if os.path.exists(script_path):
            os.remove(script_path)

    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Production Pipeline")
    parser.add_argument("--input", "-i", required=True, help="Input audio file")
    parser.add_argument("--output", "-o", help="Output mastered audio file")
    parser.add_argument("--cuts", help="JSON file or string of KEEP segments: [[start, end], ...]")
    parser.add_argument("--remove", help="JSON file or string of REMOVE (cut out) ranges: "
                                          "[[start, end], ...] -- inverted into keep segments "
                                          "automatically. Use this instead of --cuts when it's "
                                          "easier to name what's bad than what to keep around it.")
    parser.add_argument("--transcribe", metavar="OUT.json",
                         help="Transcribe --input (any length -- auto-chunks under OpenRouter's "
                              "25MB cap) and write {\"text\", \"segments\"} JSON here. Read this "
                              "before deciding --cuts/--remove ranges on a real recording.")
    parser.add_argument("--model", default="microsoft/mai-transcribe-2",
                         help="OpenRouter STT model for --transcribe (default: microsoft/mai-transcribe-2)")
    args = parser.parse_args()

    if args.transcribe:
        result = transcribe_long_openrouter(args.input, model=args.model)
        with open(args.transcribe, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Transcribed {len(result['segments'])} segments "
              f"({len(result['text'])} chars) to: {args.transcribe}")

    if args.cuts or args.remove:
        if not args.output:
            parser.error("--output is required with --cuts/--remove")
        if args.remove:
            if os.path.exists(args.remove):
                with open(args.remove) as f:
                    remove_ranges = json.load(f)
            else:
                remove_ranges = json.loads(args.remove)
            segments = invert_segments(remove_ranges, get_audio_duration(args.input))
        else:
            if os.path.exists(args.cuts):
                with open(args.cuts) as f:
                    segments = json.load(f)
            else:
                segments = json.loads(args.cuts)
        cut_and_master(args.input, args.output, segments)
        print(f"Mastered cut exported to: {args.output}")
