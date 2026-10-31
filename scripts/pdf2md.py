#!/usr/bin/env python3
# AI-assisted code: generated and revised with GLM-5.2
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Convert PDF files to markdown using PyMuPDF (fitz).

Usage:
    python3 scripts/pdf2md.py <input.pdf> [output.md]
    python3 scripts/pdf2md.py --batch docs/papers/

Features:
- Extracts text page by page with "## Page N" headers
- Preserves section structure (detects headings by font size)
- Extracts tables as markdown tables (best-effort)
- Outputs UTF-8 markdown
- Batch mode: converts all PDFs in a directory

Note: For papers with heavy math, consider using MinerU or Docling for
LaTeX-quality equation extraction. This script is sufficient for prose
and tables.
"""

import argparse
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    print("Error: pymupdf not installed. Run: pip3 install pymupdf", file=sys.stderr)
    sys.exit(1)


def extract_text_by_page(doc: pymupdf.Document) -> list[str]:
    """Extract text from each page, preserving structure."""
    pages = []
    for i, page in enumerate(doc):
        blocks = page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE)["blocks"]
        lines = []
        for block in blocks:
            if block["type"] != 0:  # skip non-text blocks (images)
                continue
            for line in block["lines"]:
                spans = line["spans"]
                if not spans:
                    continue
                text = "".join(span["text"] for span in spans).rstrip()
                if not text:
                    continue
                avg_size = sum(s["size"] for s in spans) / len(spans)
                is_bold = any("bold" in s["font"].lower() or "heavy" in s["font"].lower() for s in spans)
                lines.append((text, avg_size, is_bold))

        if not lines:
            pages.append("")
            continue

        sizes = [s for _, s, _ in lines]
        if sizes:
            body_size = max(set(sizes), key=sizes.count)
        else:
            body_size = 10.0

        page_text = []
        for text, size, is_bold in lines:
            if size > body_size + 2 and len(text) < 100:
                level = "###" if size > body_size + 4 else "####"
                page_text.append(f"{level} {text}")
            elif is_bold and len(text) < 100 and not text.endswith("."):
                page_text.append(f"**{text}**")
            else:
                page_text.append(text)

        pages.append("\n".join(page_text))

    return pages


def extract_tables(doc: pymupdf.Document) -> list[str]:
    """Best-effort table extraction."""
    tables = []
    for i, page in enumerate(doc):
        try:
            page_tables = page.find_tables()
            for tbl in page_tables:
                rows = tbl.extract()
                if not rows:
                    continue
                md_rows = []
                for j, row in enumerate(rows):
                    cells = [
                        str(c).replace("|", "\\|").replace("\n", " ").strip() if c else ""
                        for c in row
                    ]
                    md_rows.append("| " + " | ".join(cells) + " |")
                    if j == 0:
                        md_rows.append("| " + " | ".join("---" for _ in cells) + " |")
                tables.append(f"\n**Table (page {i+1}):**\n\n" + "\n".join(md_rows) + "\n")
        except Exception as e:
            print(f"  table extraction error on page {i+1}: {e}", file=sys.stderr)
    return tables


def convert_pdf_to_md(pdf_path: str, md_path: str | None = None) -> str:
    """Convert a single PDF to markdown."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found", file=sys.stderr)
        return ""

    if md_path is None:
        md_path = pdf_path.with_suffix(".md")
    else:
        md_path = Path(md_path)

    try:
        doc = pymupdf.open(str(pdf_path))
    except pymupdf.MupdfError as e:
        print(f"Error opening {pdf_path}: {e}", file=sys.stderr)
        return ""

    try:
        title = doc.metadata.get("title", "") or pdf_path.stem
        pages = extract_text_by_page(doc)
        tables = extract_tables(doc)

        md_lines = [
            f"# {title}",
            "",
            f"*Source: {pdf_path.name}*",
            f"*Pages: {len(pages)}*",
            "",
        ]

        for i, page_text in enumerate(pages):
            md_lines.append(f"## Page {i + 1}")
            md_lines.append("")
            md_lines.append(page_text)
            md_lines.append("")

        if tables:
            md_lines.append("---")
            md_lines.append("")
            md_lines.append("## Extracted Tables")
            md_lines.append("")
            md_lines.extend(tables)

        md_content = "\n".join(md_lines)

        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_content, encoding="utf-8")
        print(f"Converted: {pdf_path} -> {md_path} ({len(pages)} pages)")
        return str(md_path)
    except pymupdf.MupdfError as e:
        print(f"Error processing {pdf_path}: {e}", file=sys.stderr)
        return ""
    finally:
        doc.close()


def batch_convert(directory: str) -> list[str]:
    """Convert all PDFs in a directory."""
    directory = Path(directory)
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        return []

    pdfs = sorted(directory.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {directory}", file=sys.stderr)
        return []

    converted = []
    for pdf in pdfs:
        md = convert_pdf_to_md(str(pdf))
        if md:
            converted.append(md)

    return converted


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to markdown using PyMuPDF"
    )
    parser.add_argument(
        "input", help="Input PDF file or directory (with --batch)"
    )
    parser.add_argument(
        "output", nargs="?", default=None, help="Output markdown file (single file mode)"
    )
    parser.add_argument(
        "--batch", action="store_true", help="Convert all PDFs in input directory"
    )
    args = parser.parse_args()

    if args.batch:
        results = batch_convert(args.input)
        print(f"\nConverted {len(results)} files.")
    else:
        convert_pdf_to_md(args.input, args.output)


if __name__ == "__main__":
    main()
