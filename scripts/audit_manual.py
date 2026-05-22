#!/usr/bin/env python3
"""Extract the Ableton Live manual and generate a feature-control audit seed."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = PROJECT_ROOT / "data" / "manual" / "live12-manual-en-2026-04-30.pdf"
DEFAULT_AUDIT_DIR = PROJECT_ROOT / "audit"
DEFAULT_DOC = PROJECT_ROOT / "docs" / "live12-feature-control-audit.md"


@dataclass
class OutlineEntry:
    id: str
    title: str
    level: int
    page: int
    end_page: int


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def flatten_outline(reader: PdfReader) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def walk(items: list[Any], level: int) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, level + 1)
                continue
            try:
                page = reader.get_destination_page_number(item) + 1
            except Exception:
                page = 0
            entries.append(
                {
                    "id": f"F{len(entries) + 1:04d}",
                    "title": str(getattr(item, "title", "")).strip(),
                    "level": level,
                    "page": page,
                    "end_page": page,
                }
            )

    walk(reader.outline, 0)
    for index, entry in enumerate(entries):
        next_page = len(reader.pages) + 1
        for following in entries[index + 1 :]:
            if following["page"] >= entry["page"] and following["level"] <= entry["level"]:
                next_page = following["page"]
                break
        entry["end_page"] = max(entry["page"], next_page - 1)
    return entries


def extract(args: argparse.Namespace) -> None:
    pdf = Path(args.pdf).expanduser()
    audit_dir = Path(args.audit_dir).expanduser()
    pages_dir = audit_dir / "manual_pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(pdf))

    ledger_path = audit_dir / "manual_pages.jsonl"
    with ledger_path.open("w", encoding="utf-8") as ledger:
        for index, page in enumerate(reader.pages, start=1):
            text = normalize_text(page.extract_text() or "")
            text_path = pages_dir / f"page_{index:04d}.txt"
            text_path.write_text(text + "\n", encoding="utf-8")
            ledger.write(
                json.dumps(
                    {
                        "page": index,
                        "text_file": str(text_path.relative_to(PROJECT_ROOT)),
                        "chars": len(text),
                        "words": words(text),
                        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    outline = flatten_outline(reader)
    (audit_dir / "manual_outline.json").write_text(json.dumps(outline, indent=2), encoding="utf-8")

    manifest = {
        "source_pdf": str(pdf.relative_to(PROJECT_ROOT)),
        "source_url": args.source_url,
        "pdf_sha256": file_sha256(pdf),
        "page_count": len(reader.pages),
        "outline_entries": len(outline),
        "page_ledger": str(ledger_path.relative_to(PROJECT_ROOT)),
        "outline_file": str((audit_dir / "manual_outline.json").relative_to(PROJECT_ROOT)),
    }
    (audit_dir / "manual_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_markdown_seed(Path(args.output).expanduser(), manifest, outline)
    print(json.dumps(manifest, indent=2))


def write_markdown_seed(output: Path, manifest: dict[str, Any], outline: list[dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Ableton Live 12 Feature Control Audit",
        "",
        "Status: IN PROGRESS",
        "",
        "## Source Manual",
        "",
        f"- URL: {manifest['source_url']}",
        f"- Local PDF: `{manifest['source_pdf']}`",
        f"- SHA-256: `{manifest['pdf_sha256']}`",
        f"- Pages extracted/read ledger: `{manifest['page_ledger']}`",
        f"- Page count: {manifest['page_count']}",
        f"- PDF outline entries collected: {manifest['outline_entries']}",
        "",
        "## Coverage Legend",
        "",
        "- TODO: feature/function has been identified but not yet checked against the CLI.",
        "- COVERED: verified controllable or inspectable via `abletonctl.py` or the Live bridge.",
        "- PARTIAL: some meaningful control exists, but Live exposes more behavior than the CLI currently covers.",
        "- NOT POSSIBLE: best-effort investigation found no non-UI interface; reasoning is recorded.",
        "",
        "## Feature And Function Inventory",
        "",
        "| ID | Manual Pages | Level | Feature / Function | CLI Coverage | Evidence / Notes |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for entry in outline:
        page_range = str(entry["page"]) if entry["page"] == entry["end_page"] else f"{entry['page']}-{entry['end_page']}"
        title = entry["title"].replace("|", "\\|")
        lines.append(f"| {entry['id']} | {page_range} | {entry['level']} | {title} | TODO | Pending verification. |")
    lines.extend(
        [
            "",
            "## Page Extraction Ledger",
            "",
            "Every PDF page has been extracted to `audit/manual_pages/page_####.txt` and logged in",
            "`audit/manual_pages.jsonl` with page number, word count, character count, and text SHA-256.",
            "The feature inventory above is seeded from the PDF outline; subsequent passes expand entries",
            "where pages contain multiple distinct controls under one section.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    extract_parser = sub.add_parser("extract", help="Extract manual text and generate audit seed.")
    extract_parser.add_argument("--pdf", default=str(DEFAULT_PDF))
    extract_parser.add_argument("--audit-dir", default=str(DEFAULT_AUDIT_DIR))
    extract_parser.add_argument("--output", default=str(DEFAULT_DOC))
    extract_parser.add_argument(
        "--source-url",
        default="https://cdn-resources.ableton.com/resources/pdfs/live-manual/12/2026-04-30/live12-manual-en.pdf",
    )
    extract_parser.set_defaults(func=extract)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

