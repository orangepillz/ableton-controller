"""Command-line interface for Ableton AudioQA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import analyze_file
from .compare import SUPPORTED_COMPARE_TARGETS, compare_files
from .gates import SUPPORTED_TARGETS
from .llm_critic import critic_report
from .references import learn_references
from .reports import summarize_section, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ableton-audioqa", description="Analyze rendered Ableton WAV probes.")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Analyze one rendered WAV against a target gate.")
    analyze.add_argument("--file", required=True)
    analyze.add_argument("--target", required=True, choices=SUPPORTED_TARGETS)
    analyze.add_argument("--tempo", type=float)
    analyze.add_argument("--references", help="Optional .ableton-copilot/reference_features.json file.")
    analyze.add_argument("--render-manifest")
    analyze.add_argument("--output")

    compare = sub.add_parser("compare", help="Compare solo and context renders.")
    compare.add_argument("--primary", required=True)
    compare.add_argument("--context", required=True)
    compare.add_argument("--target", required=True, choices=SUPPORTED_COMPARE_TARGETS)
    compare.add_argument("--tempo", type=float)
    compare.add_argument("--output")

    learn = sub.add_parser("learn-references", help="Extract feature clusters from local references.")
    learn.add_argument("--root", required=True)
    learn.add_argument("--output", required=True)

    critic = sub.add_parser("llm-critic", help="Return optional JSON-only musical critic notes.")
    critic.add_argument("--file", required=True)
    critic.add_argument("--prompt-file", required=True)
    critic.add_argument("--output")

    summary = sub.add_parser("summarize-section", help="Combine audioqa reports into a section summary.")
    summary.add_argument("--section", required=True)
    summary.add_argument("--bars")
    summary.add_argument("--reports", nargs="+", required=True)
    summary.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        references = _load_json(args.references) if args.references else None
        payload = analyze_file(args.file, args.target, args.tempo, references, args.render_manifest)
        write_json(args.output, payload)
        return 0
    if args.command == "compare":
        payload = compare_files(args.primary, args.context, args.target, args.tempo)
        write_json(args.output, payload)
        return 0
    if args.command == "learn-references":
        payload = learn_references(args.root)
        write_json(args.output, payload)
        return 0
    if args.command == "llm-critic":
        payload = critic_report(args.file, args.prompt_file)
        write_json(args.output, payload)
        return 0
    if args.command == "summarize-section":
        payload = summarize_section(args.section, args.reports, args.bars)
        write_json(args.output, payload)
        return 0
    raise SystemExit(f"Unknown command: {args.command}")


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
