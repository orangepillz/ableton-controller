"""Rendered-audio probes via temporary Live resampling tracks."""

from __future__ import annotations

import aifc
import argparse
import json
import shutil
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .arg_types import track_value


def render_audio(
    args: argparse.Namespace,
    sender: Callable[[argparse.Namespace, dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    output = Path(args.output).expanduser().resolve()
    if output.suffix.lower() != ".wav":
        raise ValueError("render-audio output must be a .wav file")
    output.parent.mkdir(parents=True, exist_ok=True)
    remove_previous_render(output)
    state_id = ""
    finished: dict[str, Any] | None = None
    try:
        prepared = sender(args, _prepare_payload(args, output))
        state_id = str(prepared["state_id"])
        time.sleep(float(prepared["wait_seconds"]))
        finished = sender(args, {"command": "render_audio_finish", "state_id": state_id})
        source_file = Path(str(finished["source_file"]))
        convert_recording(source_file, output)
        source_cleaned = cleanup_recorded_source(source_file, output)
        audio_info = verify_wav(output)
        manifest_path = None
        if args.create_manifest:
            manifest_path = write_render_manifest(args, output, prepared, finished, audio_info, source_cleaned)
        return {
            "done": True,
            "output_file": args.output,
            "output_file_abs": str(output),
            "manifest": str(manifest_path) if manifest_path else None,
            "audio": audio_info,
            "restored_state": bool(finished.get("restored_state", False)),
            "export_method": "resampling_track",
            "source_file": finished["source_file"],
            "source_file_cleaned": source_cleaned,
        }
    except Exception:
        if state_id and finished is None:
            try:
                sender(args, {"command": "render_audio_cancel", "state_id": state_id})
            except Exception:
                pass
        raise


def convert_recording(source: Path, output: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Recorded source file does not exist: {source}")
    if source.suffix.lower() == ".wav":
        shutil.copyfile(source, output)
        return
    if source.suffix.lower() not in {".aif", ".aiff", ".aifc"}:
        raise ValueError(f"Unsupported recorded audio format: {source.suffix}")
    with aifc.open(str(source), "rb") as audio:
        if audio.getcomptype() not in (b"NONE", "NONE"):
            raise ValueError(f"Unsupported AIFF compression: {audio.getcomptype()!r}")
        channels = audio.getnchannels()
        sample_width = audio.getsampwidth()
        sample_rate = audio.getframerate()
        frames = audio.readframes(audio.getnframes())
    pcm = _aiff_pcm_to_wav_pcm(frames, sample_width)
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)


def verify_wav(output: Path) -> dict[str, int | float]:
    try:
        with wave.open(str(output), "rb") as wav:
            frames = wav.getnframes()
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
    except (OSError, wave.Error) as exc:
        raise ValueError(f"Render did not produce a readable WAV file: {output}") from exc
    if frames <= 0 or sample_rate <= 0:
        raise ValueError(f"Rendered WAV has no audio frames: {output}")
    return {
        "frames": frames,
        "sample_rate": sample_rate,
        "channels": channels,
        "bit_depth": sample_width * 8,
        "duration_seconds": round(frames / float(sample_rate), 6),
    }


def cleanup_recorded_source(source: Path, output: Path) -> bool:
    try:
        if source.resolve() == output.resolve():
            return False
    except OSError:
        return False
    if not source.name.startswith("Codex AudioQA Render "):
        return False
    cleaned = False
    for path in (source, source.with_suffix(source.suffix + ".asd"), source.with_suffix(".asd")):
        try:
            if path.exists() and path.is_file():
                path.unlink()
                cleaned = True
        except OSError:
            pass
    return cleaned


def write_render_manifest(
    args: argparse.Namespace,
    output: Path,
    prepared: dict[str, Any],
    finished: dict[str, Any],
    audio_info: dict[str, int | float],
    source_cleaned: bool,
) -> Path:
    manifest_path = output.with_suffix(".manifest.json")
    manifest = {
        "render_id": output.stem,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "set_name": prepared.get("set_name") or "unsaved_live_set",
        "tempo_bpm": prepared.get("tempo_bpm"),
        "start_bar": args.start_bar,
        "start_beat": prepared.get("start_beat"),
        "bars": args.bars,
        "length_beats": prepared.get("length_beats"),
        "output_file": args.output,
        "output_file_abs": str(output),
        "sample_rate": args.sample_rate,
        "actual_sample_rate": audio_info["sample_rate"],
        "bit_depth": args.bit_depth,
        "actual_bit_depth": audio_info["bit_depth"],
        "normalize": args.normalize,
        "solo_tracks": _render_track_list(args.solo_track, args.solo_tracks),
        "solo_groups": list(args.solo_group or []),
        "muted_tracks": list(args.mute_track or []),
        "muted_groups": list(args.mute_group or []),
        "include_returns": bool(args.include_returns),
        "restored_state": bool(finished.get("restored_state", False)),
        "export_method": "resampling_track",
        "recorded_source_file": finished.get("source_file"),
        "recorded_source_cleaned": source_cleaned,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def remove_previous_render(output: Path) -> None:
    for path in (output, output.with_suffix(output.suffix + ".asd"), output.with_suffix(".asd")):
        if path.exists() and path.is_file():
            path.unlink()


def _prepare_payload(args: argparse.Namespace, output: Path) -> dict[str, Any]:
    return {
        "command": "render_audio_prepare",
        "start_bar": args.start_bar,
        "bars": args.bars,
        "output_file": args.output,
        "output_file_abs": str(output),
        "solo_tracks": _render_track_list(args.solo_track, args.solo_tracks),
        "solo_groups": list(args.solo_group or []),
        "muted_tracks": list(args.mute_track or []),
        "muted_groups": list(args.mute_group or []),
        "include_returns": args.include_returns,
        "sample_rate": args.sample_rate,
        "bit_depth": args.bit_depth,
        "normalize": args.normalize,
        "restore_state": args.restore_state,
    }


def _render_track_list(repeated, comma_separated):
    values = list(repeated or [])
    if comma_separated:
        values.extend(track_value(item.strip()) for item in comma_separated.split(",") if item.strip())
    return values


def _aiff_pcm_to_wav_pcm(frames: bytes, sample_width: int) -> bytes:
    if sample_width == 1:
        return bytes((byte + 128) & 0xFF for byte in frames)
    if sample_width not in {2, 3, 4}:
        raise ValueError(f"Unsupported AIFF sample width: {sample_width}")
    converted = bytearray(len(frames))
    for offset in range(0, len(frames), sample_width):
        converted[offset : offset + sample_width] = frames[offset : offset + sample_width][::-1]
    return bytes(converted)
