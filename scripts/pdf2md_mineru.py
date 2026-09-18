#!/usr/bin/env python3
"""Batch-convert PDFs to markdown using MinerU (mineru-kit, local basic tier).

Usage:
    .venv/bin/python scripts/pdf2md_mineru.py [input_dir] [output_dir] [--force]

Defaults:
    input_dir  = docs/papers
    output_dir = docs/papers-mineru

One markdown file per PDF, named <pdf-stem>.md. Skips PDFs that already have
an output file unless --force is given. Prints per-file timing.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

MINERU_KIT = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "mineru-kit"


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch PDF -> markdown via MinerU")
    parser.add_argument("input_dir", nargs="?", default="docs/papers")
    parser.add_argument("output_dir", nargs="?", default="docs/papers-mineru")
    parser.add_argument("--force", action="store_true", help="reconvert even if output exists")
    parser.add_argument("--tier", default="basic", choices=["flash", "basic", "standard", "advanced"])
    args = parser.parse_args()

    if not MINERU_KIT.exists():
        print(f"Error: {MINERU_KIT} not found. Create venv: python3 -m venv .venv && "
              f".venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu && "
              f".venv/bin/pip install mineru && .venv/bin/mineru-kit models download --tier basic",
              file=sys.stderr)
        return 1

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory", file=sys.stderr)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {input_dir}", file=sys.stderr)
        return 1

    total_start = time.monotonic()
    ok, skipped, failed = 0, 0, []

    for pdf in pdfs:
        out_md = output_dir / (pdf.stem + ".md")
        if out_md.exists() and not args.force:
            print(f"SKIP   {pdf.name} (exists: {out_md})")
            skipped += 1
            continue

        print(f"PARSE  {pdf.name} ...", flush=True)
        start = time.monotonic()
        proc = subprocess.run(
            [str(MINERU_KIT), "parse", str(pdf), "-o", str(output_dir), "--tier", args.tier],
            capture_output=True, text=True,
        )
        elapsed = time.monotonic() - start
        if proc.returncode != 0:
            print(f"FAIL   {pdf.name} (rc={proc.returncode}, {elapsed:.1f}s)")
            print(proc.stderr[-2000:], file=sys.stderr)
            failed.append(pdf.name)
            continue
        if not out_md.exists():
            print(f"FAIL   {pdf.name}: no output produced after {elapsed:.1f}s")
            failed.append(pdf.name)
            continue
        size_kb = out_md.stat().st_size / 1024
        print(f"OK     {pdf.name} -> {out_md} ({size_kb:.0f} KB, {elapsed:.1f}s)")
        ok += 1

    total = time.monotonic() - total_start
    print(f"\nDone: {ok} converted, {skipped} skipped, {len(failed)} failed, {total:.0f}s total")
    if failed:
        print(f"Failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
