#!/usr/bin/env python3
"""Deterministic arXiv source preflight.

This script finds mechanical problems and produces a citation inventory. It does
not validate scientific claims, external citation metadata, rights, or arXiv
acceptance. Exit codes: 0 = no findings, 1 = warnings only, 2 = blocker(s).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


ALLOWED_COMPONENT = re.compile(r"^[A-Za-z0-9_+.,=-]+$")
ARXIV_ID = re.compile(
    r"arXiv:(?:\d{4}\.\d{4,5}|[A-Za-z-]+(?:\.[A-Za-z-]+)?/\d{7})(?:v\d+)?(?:\s*\[[A-Za-z.-]+\])?"
)
DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.IGNORECASE)
URL = re.compile(r"https?://[^\s{}<>\\]+", re.IGNORECASE)
BIB_KEY = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.IGNORECASE)
BIBITEM = re.compile(r"\\bibitem(?:\s*\[[^]]*\])?\s*\{([^}]+)\}")
BIBLATEX_ENTRY = re.compile(r"\\entry\s*\{([^}]+)\}\s*\{[^}]*\}\s*\{")
CITE_START = re.compile(
    r"\\(?:cite|citep|citet|citealp|citealt|autocite|parencite|textcite|footcite|smartcite|supercite|nocite)\w*\*?"
    r"(?:\s*\[[^]]*\]){0,2}\s*\{"
)
REF_START = re.compile(r"\\(?:ref|eqref|pageref|autoref|cref|Cref)\*?\s*\{")
LABEL_START = re.compile(r"\\label\s*\{")
DEPENDENCY_PATTERNS = {
    "tex": re.compile(r"\\(?:input|include|subfile)\s*\{"),
    "graphic": re.compile(r"\\includegraphics(?:\s*\[[^]]*\])?\s*\{"),
    "bib": re.compile(r"\\bibliography\s*\{"),
    "bibresource": re.compile(r"\\addbibresource(?:\s*\[[^]]*\])?\s*\{"),
}
GENERATED_SUFFIXES = {
    ".aux", ".log", ".toc", ".lot", ".lof", ".out", ".dvi", ".synctex",
    ".fls", ".fdb_latexmk", ".blg", ".bcf", ".run.xml", ".nav", ".snm",
}
UPLOAD_ALLOWED_SUFFIXES = {
    ".tex", ".bib", ".bbl", ".bst", ".cls", ".sty", ".cfg", ".def", ".fd",
    ".ind", ".gls", ".nls", ".ist",
    ".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps",
    ".otf", ".ttf", ".pfb", ".afm", ".map", ".enc", ".bb", ".xbb",
}
CODE_OR_ARTIFACT_SUFFIXES = {
    ".py", ".pyc", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp",
    ".rs", ".go", ".java", ".js", ".ts", ".sh", ".bat", ".ps1",
    ".lean", ".olean", ".v", ".vo", ".thy", ".agda", ".ipynb",
    ".csv", ".tsv", ".json", ".jsonl", ".yaml", ".yml", ".toml",
    ".lp", ".mps", ".cnf", ".smt", ".smt2", ".log", ".dat", ".bin",
}
NESTED_ARCHIVE_SUFFIXES = {".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar"}
ADMINISTRATIVE_NAMES = re.compile(
    r"(?:ARXIV_(?:AUDIT|METADATA)|BLOCKER|CHECKLIST|SHA256SUMS|CHECKSUM|MANIFEST)",
    re.IGNORECASE,
)
SECRET_NAMES = re.compile(r"(^|/)(\.env|.*credentials.*|.*secret.*|.*private.*\.key|.*\.pem)$", re.IGNORECASE)
PLACEHOLDERS = {
    "TODO/FIXME marker": re.compile(r"\b(?:TODO|FIXME|XXX)\b"),
    "unresolved question marks": re.compile(r"(?<!\?)\?\?(?!\?)"),
    "line-number command": re.compile(r"\\(?:linenumbers|pagewiselinenumbers)\b"),
    "margin-note command": re.compile(r"\\marginpar\b|\\todo(?:\s*\[|\s*\{)"),
    "highlight/edit markup": re.compile(r"\\(?:hl|sout|uwave|textcolor)\s*(?:\[[^]]*\])?\s*\{"),
    "draft/referee mode": re.compile(r"(?:\\documentclass\s*\[[^]]*\b(?:draft|review)\b|\\usepackage\s*\[[^]]*\b(?:draft|final)\b[^]]*\]\s*\{lineno\})"),
    "hidden/prompt-injection text": re.compile(r"(?:ignore (?:all|any|the) previous instructions|positive review only|hidden prompt)", re.IGNORECASE),
}
HARD_SOURCE_HYGIENE = {
    "dynamic \\today date": re.compile(r"\\today\b"),
    "shell-escape command": re.compile(r"\\(?:immediate\s*)?write18\b|\\ShellEscape\b"),
    "machine-local path": re.compile(r"(?:/home/|/Users/|(?<![A-Za-z0-9])[A-Za-z]:[\\/])"),
}
AI_DISCLOSURE = re.compile(
    r"(?:generative\s+AI|large\s+language\s+model|\bLLM\b|ChatGPT|OpenAI|Claude|Gemini|Copilot)",
    re.IGNORECASE,
)
AI_EXACT_MODEL = re.compile(
    r"(?:OpenAI\s+(?:GPT[- ]?[0-9][A-Za-z0-9.-]*(?:\s+Sol)?|o[0-9][A-Za-z0-9.-]*)|Anthropic\s+(?:Claude\s+)?(?:Opus|Sonnet|Haiku)\s*[0-9][A-Za-z0-9.-]*|Google\s+Gemini\s*[0-9][A-Za-z0-9.-]*|Meta\s+Llama\s*[0-9][A-Za-z0-9.-]*)",
    re.IGNORECASE,
)
AI_MODE = re.compile(
    r"\b(?:extra[- ]high|xhigh|high|medium|low|max|ultra)\s+(?:thinking|reasoning)\s+mode\b",
    re.IGNORECASE,
)
AI_ROLE = re.compile(
    r"\b(?:research|proof|literature|citation|code|experiment|figure|data|drafting|editing|revision|referee|review)\w*\b",
    re.IGNORECASE,
)
ARTIFACT_TERM = re.compile(
    r"\b(?:artifact|source code|code repository|implementation|certificate|checker|proof script|formalization|Lean|Coq|Isabelle|Agda|dataset|benchmark|notebook|supplementary material|supplementary files|reproducibility package|solver log)\b",
    re.IGNORECASE,
)
EXTERNAL_ARTIFACT_CUE = re.compile(
    r"(?:\bavailable\s+(?:at|from|in)\b|\b(?:code )?repository\b|\bGitHub\b|\bsupplementary (?:material|files)\b|\breproducibility package\b|\bproof scripts?\b|\bsource code\b|\bour (?:artifact|code|implementation|formalization|dataset|notebook)\b|\bartifact(?:s)?\s+(?:contains?|includes?|is|are)\b)",
    re.IGNORECASE,
)
GITHUB_URL = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", re.IGNORECASE)
ARTIFACT_ROLE = re.compile(
    r"\b(?:logically required|supporting|regression[- ]only|proof premise|not (?:a )?proof premise)\b",
    re.IGNORECASE,
)
NOVELTY_CLAIM = re.compile(
    r"\b(?:first|novel|new exact|resolves?|settles?|open problem|best[- ]known|optimal|exact(?:ly)?\s+\d+)\b",
    re.IGNORECASE,
)
METADATA_FIELDS = [
    "Title",
    "Authors",
    "Comments",
    "Subjects",
    "MSC classes",
    "ACM classes",
    "Report number",
    "Journal reference",
    "DOI",
    "License",
    "Submitter is author",
    "External artifacts",
    "AI disclosure",
]

# arXiv form-only fields. These are entered in the submission web form, not
# shipped in the source download, so they are legitimately absent from the
# canonical TeX block. They are optional here: present-and-empty or absent is
# fine; a present non-empty value is still checked for ASCII/duplicates.
OPTIONAL_METADATA_FIELDS = {
    "Report number",
    "Journal reference",
    "DOI",
    "Submitter is author",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    location: str | None = None


ARXIV_POLICY_CODES = {
    "FILENAME", "HIDDEN_FILE", "GENERATED_FILE", "GENERATED_MAIN_PDF",
    "MAIN_NOT_FOUND", "MAIN_MISSING", "MAIN_AMBIGUOUS", "ABSOLUTE_PATH",
    "CASE_MISMATCH", "MISSING_DEPENDENCY", "BBL_NAME", "BIBLATEX_BBL_COMPAT",
    "TITLE_MISSING", "AUTHOR_MISSING", "ABSTRACT_MISSING", "ABSTRACT_LENGTH",
    "ABSTRACT_HEADING", "SUBJECTS_FORMAT", "ACM_CLASS_FORMAT", "MSC_CLASS_FORMAT",
    "ARTIFACT_PUBLIC_REPOSITORY", "SHELL_ESCAPE", "ARCHIVE_UNSAFE_PATH",
    "ARCHIVE_ENCRYPTED", "ARCHIVE_CORRUPT", "ARCHIVE_EXTRANEOUS",
    "METADATA_NON_ASCII", "COMMENTS_PAGE_COUNT", "MANUSCRIPT_POLICY",
    "ARCHIVE_UNEXPECTED_FILE", "ARCHIVE_ADMIN_FILE", "ARCHIVE_NESTED_ARCHIVE",
}
GREGORY_PREFERENCE_CODES = {
    "METADATA_BLOCK", "METADATA_BLOCK_FORMAT", "METADATA_PERCENT_COMMENTS",
    "METADATA_NESTED_CONDITIONAL", "METADATA_MALFORMED_LINE",
    "METADATA_DUPLICATE_FIELD", "METADATA_UNKNOWN_FIELD", "METADATA_FIELD",
    "ABSTRACT_METADATA_MODE", "ABSTRACT_SOURCE_VALUE", "METADATA_SYNC",
}


def requirement_basis(code: str) -> str:
    if code in ARXIV_POLICY_CODES:
        return "ARXIV POLICY"
    if code in GREGORY_PREFERENCE_CODES:
        return "GREGORY PREFERENCE"
    return "STRICT PUBLICATION DEFAULT"


def finding_dict(item: Finding) -> dict[str, object]:
    return {**asdict(item), "basis": requirement_basis(item.code)}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def inspect_and_extract_zip(
    source: Path, allow_ancillary: bool
) -> tuple[Path, tempfile.TemporaryDirectory[str], dict[str, object], list[Finding]]:
    findings: list[Finding] = []
    temporary = tempfile.TemporaryDirectory(prefix="arxiv-upload-audit-")
    root = Path(temporary.name).resolve()
    members: list[dict[str, object]] = []
    safe_members: list[zipfile.ZipInfo] = []
    seen_names: Counter[str] = Counter()
    total_size = 0

    try:
        archive = zipfile.ZipFile(source)
    except (OSError, zipfile.BadZipFile) as exc:
        findings.append(Finding("BLOCKER", "ARCHIVE_CORRUPT", f"Cannot open ZIP archive: {exc}", source.name))
        return root, temporary, {"input": str(source), "members": members}, findings

    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename
            pure = PurePosixPath(name)
            seen_names[name] += 1
            total_size += info.file_size
            entry = {
                "path": name,
                "bytes": info.file_size,
                "compressed_bytes": info.compress_size,
            }
            members.append(entry)
            unsafe = pure.is_absolute() or ".." in pure.parts or "\\" in name or not pure.parts
            if unsafe:
                findings.append(Finding("BLOCKER", "ARCHIVE_UNSAFE_PATH", "ZIP member has an absolute, parent-traversal, empty, or backslash path.", name))
                continue
            unix_mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(unix_mode):
                findings.append(Finding("BLOCKER", "ARCHIVE_UNSAFE_PATH", "ZIP member is a symbolic link.", name))
                continue
            if info.flag_bits & 0x1:
                findings.append(Finding("BLOCKER", "ARCHIVE_ENCRYPTED", "Encrypted ZIP members are not valid upload dependencies.", name))
                continue

            lower_parts = [part.lower() for part in pure.parts]
            in_ancillary = bool(lower_parts and lower_parts[0] == "anc")
            suffix = PurePosixPath(name).suffix.lower()
            basename = pure.name
            if in_ancillary and not allow_ancillary:
                findings.append(Finding("BLOCKER", "ARCHIVE_ANCILLARY_OPT_IN", "Ancillary files require explicit author opt-in; the strict default keeps artifacts in the public repository.", name))
            if suffix in CODE_OR_ARTIFACT_SUFFIXES and not (in_ancillary and allow_ancillary):
                findings.append(Finding("BLOCKER", "ARCHIVE_CODE_OR_ARTIFACT", "Code, data, certificates, logs, or proof-assistant files do not belong in the strict-default arXiv upload.", name))
            if suffix in NESTED_ARCHIVE_SUFFIXES:
                findings.append(Finding("BLOCKER", "ARCHIVE_NESTED_ARCHIVE", "Nested or older archives do not belong in the arXiv upload.", name))
            if ADMINISTRATIVE_NAMES.search(basename):
                findings.append(Finding("BLOCKER", "ARCHIVE_ADMIN_FILE", "Audit, metadata, checksum, manifest, or checklist files belong in the author handoff, not the arXiv upload.", name))
            if not in_ancillary and basename != "00README" and suffix not in UPLOAD_ALLOWED_SUFFIXES:
                findings.append(Finding("BLOCKER", "ARCHIVE_UNEXPECTED_FILE", "File is outside the strict compilation allowlist.", name))
            safe_members.append(info)

        for name, count in seen_names.items():
            if count > 1:
                findings.append(Finding("BLOCKER", "ARCHIVE_DUPLICATE_MEMBER", f"ZIP contains {count} entries with the same path.", name))
        if total_size > 1_000_000_000:
            findings.append(Finding("BLOCKER", "ARCHIVE_SIZE", f"Uncompressed ZIP size is {total_size} bytes; review as an oversized or accidental bundle.", source.name))
        else:
            try:
                bad_member = archive.testzip()
            except (RuntimeError, zipfile.BadZipFile, OSError) as exc:
                findings.append(Finding("BLOCKER", "ARCHIVE_CORRUPT", f"ZIP integrity test failed: {exc}", source.name))
            else:
                if bad_member:
                    findings.append(Finding("BLOCKER", "ARCHIVE_CORRUPT", f"ZIP integrity test failed at member: {bad_member}", source.name))

        for info in safe_members:
            pure = PurePosixPath(info.filename)
            destination = root.joinpath(*pure.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                with archive.open(info) as source_stream, destination.open("wb") as destination_stream:
                    while chunk := source_stream.read(1024 * 1024):
                        destination_stream.write(chunk)
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                findings.append(Finding("BLOCKER", "ARCHIVE_CORRUPT", f"Cannot extract member: {exc}", info.filename))

    archive_report = {
        "input": str(source),
        "member_count": len(members),
        "uncompressed_bytes": total_size,
        "ancillary_opt_in": allow_ancillary,
        "members": members,
    }
    return root, temporary, archive_report, findings


def parse_metadata_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^([^:]+):\s*(.*)$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def verify_checksum_manifest(path: Path) -> tuple[dict[str, object], list[Finding]]:
    findings: list[Finding] = []
    report: dict[str, object] = {"file": str(path), "entries": 0, "verified": 0, "matches": False}
    if not path.is_file():
        findings.append(Finding("BLOCKER", "CHECKSUM_MANIFEST", "Requested checksum manifest does not exist.", str(path)))
        return report, findings
    base = path.parent.resolve()
    entries = 0
    verified = 0
    for line_number_in_manifest, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([0-9A-Fa-f]{64})\s+[ *]?(.+)$", line)
        if not match:
            findings.append(Finding("BLOCKER", "CHECKSUM_MANIFEST", "Malformed SHA-256 manifest line.", f"{path}:{line_number_in_manifest}"))
            continue
        entries += 1
        expected_hash, raw_name = match.group(1).lower(), match.group(2).strip()
        target = (base / raw_name).resolve()
        if base not in (target, *target.parents):
            findings.append(Finding("BLOCKER", "CHECKSUM_PATH", "Checksum entry escapes the manifest directory.", raw_name))
            continue
        if not target.is_file():
            findings.append(Finding("BLOCKER", "CHECKSUM_MISSING_FILE", "Checksummed file is missing.", raw_name))
            continue
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        if digest.hexdigest() != expected_hash:
            findings.append(Finding("BLOCKER", "CHECKSUM_MISMATCH", "SHA-256 checksum does not match.", raw_name))
            continue
        verified += 1
    report.update({"entries": entries, "verified": verified, "matches": entries > 0 and entries == verified})
    if entries == 0:
        findings.append(Finding("BLOCKER", "CHECKSUM_MANIFEST", "Checksum manifest has no entries.", str(path)))
    return report, findings


def run_shipping_build(root: Path, main_tex: Path, engine: str, comments: str) -> tuple[dict[str, object], list[Finding]]:
    findings: list[Finding] = []
    report: dict[str, object] = {
        "performed": True,
        "engine": engine,
        "runs": [],
        "bibtex_or_biber_invoked": False,
        "pdf": None,
        "pages": None,
        "selectable_text_characters": None,
        "fonts_embedded": None,
    }
    executable = shutil.which(engine)
    if not executable:
        findings.append(Finding("BLOCKER", "SHIPPING_BUILD_TOOL", f"Requested TeX engine is unavailable: {engine}"))
        return report, findings

    relative_main = main_tex.relative_to(root)
    command = [
        executable,
        "-no-shell-escape",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        str(relative_main),
    ]
    for run_number in range(1, 4):
        try:
            completed = subprocess.run(command, cwd=root, capture_output=True, text=True, errors="replace", timeout=180)
        except subprocess.TimeoutExpired:
            findings.append(Finding("BLOCKER", "SHIPPING_BUILD_TIMEOUT", f"Extracted final ZIP exceeded 180 seconds on LaTeX-only run {run_number}.", str(relative_main)))
            break
        report["runs"].append({
            "run": run_number,
            "returncode": completed.returncode,
            "tail": (completed.stdout + "\n" + completed.stderr)[-4000:],
        })
        if completed.returncode != 0:
            findings.append(Finding("BLOCKER", "SHIPPING_BUILD", f"Extracted final ZIP failed LaTeX-only run {run_number}; BibTeX/Biber was not invoked.", str(relative_main)))
            break

    job_stem = main_tex.stem
    log_path = root / f"{job_stem}.log"
    pdf_path = root / f"{job_stem}.pdf"
    if log_path.is_file():
        log_text = read_text(log_path)
        if re.search(r"undefined (?:citations?|references?)|Citation .+ undefined|Reference .+ undefined", log_text, re.IGNORECASE):
            findings.append(Finding("BLOCKER", "SHIPPING_UNDEFINED_REFERENCE", "Shipping-build log contains undefined citations or references.", log_path.name))
        overfull_count = len(re.findall(r"Overfull \\[hv]box", log_text))
        underfull_count = len(re.findall(r"Underfull \\[hv]box", log_text))
        report["overfull_boxes"] = overfull_count
        report["underfull_boxes"] = underfull_count
        if overfull_count:
            findings.append(Finding("BLOCKER", "PDF_OVERFULL_BOX", f"Shipping build contains {overfull_count} overfull box warning(s).", log_path.name))
        if underfull_count:
            findings.append(Finding("WARNING", "PDF_UNDERFULL_BOX", f"Shipping build contains {underfull_count} underfull box warning(s); classify each as cosmetic or substantive.", log_path.name))
    else:
        findings.append(Finding("BLOCKER", "SHIPPING_BUILD_LOG", "Shipping build produced no TeX log.", log_path.name))

    if not pdf_path.is_file():
        findings.append(Finding("BLOCKER", "SHIPPING_BUILD_PDF", "Shipping build produced no PDF.", pdf_path.name))
        return report, findings
    report["pdf"] = pdf_path.name

    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        completed = subprocess.run([pdfinfo, str(pdf_path)], capture_output=True, text=True, errors="replace", timeout=60)
        report["pdfinfo"] = completed.stdout
        for label, permitted in (("JavaScript", "no"), ("Form", "none"), ("Encrypted", "no"), ("Suspects", "no")):
            value_match = re.search(rf"^{label}:\s+(.+?)\s*$", completed.stdout, re.MULTILINE | re.IGNORECASE)
            if value_match and value_match.group(1).strip().lower() != permitted:
                findings.append(Finding("BLOCKER", "PDF_SUSPICIOUS_OBJECT", f"Shipping PDF reports `{label}: {value_match.group(1).strip()}`; expected `{permitted}`."))
        pages_match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
        if pages_match:
            pages = int(pages_match.group(1))
            report["pages"] = pages
            stated_pages = re.search(r"\b(\d+)\s+pages?\b", comments, re.IGNORECASE)
            if stated_pages and int(stated_pages.group(1)) != pages:
                findings.append(Finding("BLOCKER", "COMMENTS_PAGE_COUNT", f"Comments states {stated_pages.group(1)} page(s), but the extracted final ZIP builds {pages} page(s)."))

    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        completed = subprocess.run([pdftotext, str(pdf_path), "-"], capture_output=True, text=True, errors="replace", timeout=60)
        selectable_characters = len(completed.stdout.strip())
        report["selectable_text_characters"] = selectable_characters
        if selectable_characters == 0:
            findings.append(Finding("BLOCKER", "PDF_NOT_SELECTABLE", "Shipping PDF has no extractable/selectable text."))

    pdffonts = shutil.which("pdffonts")
    if pdffonts:
        completed = subprocess.run([pdffonts, str(pdf_path)], capture_output=True, text=True, errors="replace", timeout=60)
        report["pdffonts"] = completed.stdout
        unembedded = [
            line for line in completed.stdout.splitlines()
            if re.search(r"\sno\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$", line)
        ]
        report["fonts_embedded"] = not unembedded
        if unembedded:
            findings.append(Finding("BLOCKER", "PDF_FONT_NOT_EMBEDDED", f"Shipping PDF contains {len(unembedded)} unembedded font(s)."))
    return report, findings


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def strip_tex_comments(text: str) -> str:
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        cut = None
        for index, char in enumerate(line):
            if char != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                cut = index
                break
        if cut is None:
            output.append(line)
        else:
            ending = "\n" if line.endswith("\n") else ""
            output.append(line[:cut] + ending)
    return "".join(output)


def remove_metadata_block(text: str) -> str:
    """Remove the canonical false-conditional block while preserving line count."""
    pattern = re.compile(
        r"\\iffalse[^\S\r\n]*\r?\n[^\S\r\n]*ARXIV-METADATA-BEGIN[^\S\r\n]*\r?\n"
        r"[\s\S]*?"
        r"\r?\n[^\S\r\n]*ARXIV-METADATA-END[^\S\r\n]*\r?\n[^\S\r\n]*\\fi\b"
    )
    return pattern.sub(lambda match: "\n" * match.group(0).count("\n"), text)


def abstract_copy_paste_issues(abstract: str, source: str) -> list[str]:
    issues: list[str] = []
    value = normalize_space(abstract)
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        issues.append("contains non-ASCII characters")
    if len(value) > 1920:
        issues.append(f"has {len(value)} characters (limit 1920)")
    if value.lower().startswith("abstract"):
        issues.append("begins with the word Abstract")
    prohibited = re.compile(
        r"\\(?:cite\w*|ref|eqref|label|footnote|thanks|emph|textbf|textit|texttt|url|href|mbox|vspace|hspace|quad)\b|~|\\[,!;:]"
    )
    if prohibited.search(abstract):
        issues.append("contains citation, cross-reference, formatting, URL, or TeX spacing commands")
    custom_names = set(
        re.findall(
            r"\\(?:newcommand|renewcommand|providecommand|DeclareMathOperator)\*?\s*(?:\{\s*)?\\([A-Za-z@]+)",
            source,
        )
    )
    used_custom = sorted(name for name in custom_names if re.search(r"\\" + re.escape(name) + r"\b", abstract))
    if used_custom:
        issues.append("uses local macro(s): " + ", ".join("\\" + name for name in used_custom))
    if any(line.startswith((" ", "\t")) for line in abstract.strip().splitlines()[1:]):
        issues.append("contains continuation lines with leading whitespace")
    return issues


def braced_argument(text: str, opening_brace: int) -> tuple[str, int] | None:
    if opening_brace >= len(text) or text[opening_brace] != "{":
        return None
    depth = 0
    escaped = False
    for index in range(opening_brace, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[opening_brace + 1:index], index + 1
    return None


def command_arguments(text: str, pattern: re.Pattern[str]) -> Iterable[tuple[str, int]]:
    for match in pattern.finditer(text):
        parsed = braced_argument(text, match.end() - 1)
        if parsed:
            value, _ = parsed
            yield value, match.start()


def first_command_argument(text: str, command: str) -> str | None:
    pattern = re.compile(r"\\" + re.escape(command) + r"\s*\{")
    return next((value for value, _ in command_arguments(text, pattern)), None)


def find_main(root: Path, explicit: str | None, tex_files: Sequence[Path]) -> tuple[Path | None, list[Finding]]:
    findings: list[Finding] = []
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        if not candidate.is_file() or root.resolve() not in (candidate, *candidate.parents):
            findings.append(Finding("BLOCKER", "MAIN_NOT_FOUND", f"Explicit main TeX file not found under source root: {explicit}"))
            return None, findings
        return candidate, findings

    candidates = []
    for path in tex_files:
        text = strip_tex_comments(read_text(path))
        if "\\documentclass" in text and "\\begin{document}" in text:
            candidates.append(path)
    if len(candidates) == 1:
        return candidates[0], findings
    if not candidates:
        findings.append(Finding("BLOCKER", "MAIN_MISSING", "No TeX file contains both \\documentclass and \\begin{document}."))
    else:
        names = ", ".join(str(path.relative_to(root)) for path in candidates)
        findings.append(Finding("BLOCKER", "MAIN_AMBIGUOUS", f"Multiple possible main TeX files: {names}"))
    return None, findings


def exact_or_case_mismatch(base: Path, raw: str, suffixes: Sequence[str]) -> tuple[Path | None, Path | None]:
    candidates: list[Path] = []
    raw_path = Path(raw)
    if raw_path.suffix:
        candidates.append(base / raw_path)
    else:
        candidates.extend(base / (raw + suffix) for suffix in suffixes)
    for candidate in candidates:
        if candidate.exists():
            return candidate, None
    for candidate in candidates:
        parent = candidate.parent
        if not parent.is_dir():
            continue
        lowered = candidate.name.casefold()
        for entry in parent.iterdir():
            if entry.name.casefold() == lowered:
                return None, entry
    return None, None


def dependency_findings(root: Path, tex_files: Sequence[Path], matching_bbl_available: bool = False) -> tuple[list[Finding], list[dict[str, object]]]:
    findings: list[Finding] = []
    inventory: list[dict[str, object]] = []
    suffixes = {
        "tex": ["", ".tex"],
        "graphic": ["", ".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps"],
        "bib": ["", ".bib"],
        "bibresource": ["", ".bib"],
    }
    for tex in tex_files:
        text = strip_tex_comments(read_text(tex))
        for kind, pattern in DEPENDENCY_PATTERNS.items():
            for value, offset in command_arguments(text, pattern):
                raw_values = [part.strip() for part in value.split(",")] if kind == "bib" else [value.strip()]
                for raw in raw_values:
                    location = f"{tex.relative_to(root)}:{line_number(text, offset)}"
                    item = {"kind": kind, "source": str(tex.relative_to(root)), "line": line_number(text, offset), "raw": raw}
                    inventory.append(item)
                    if not raw or any(token in raw for token in ("\\", "#", "$")):
                        findings.append(Finding("WARNING", "DYNAMIC_DEPENDENCY", f"Cannot statically resolve {kind} dependency `{raw}`.", location))
                        continue
                    raw_path = Path(raw)
                    if raw_path.is_absolute() or re.match(r"^[A-Za-z]:[\\/]", raw):
                        findings.append(Finding("BLOCKER", "ABSOLUTE_PATH", f"Absolute {kind} dependency: {raw}", location))
                        continue
                    exact, mismatch = exact_or_case_mismatch(tex.parent, raw, suffixes[kind])
                    if exact is None:
                        exact, mismatch_at_root = exact_or_case_mismatch(root, raw, suffixes[kind])
                        mismatch = mismatch or mismatch_at_root
                    if exact is None and mismatch is not None:
                        findings.append(Finding("BLOCKER", "CASE_MISMATCH", f"Dependency `{raw}` differs in case from `{mismatch.name}`.", location))
                    elif exact is None:
                        if kind in {"bib", "bibresource"} and matching_bbl_available:
                            item["satisfied_by_matching_bbl_under_arxiv_policy"] = True
                        else:
                            findings.append(Finding("BLOCKER", "MISSING_DEPENDENCY", f"Missing {kind} dependency: {raw}", location))
                    else:
                        item["resolved"] = str(exact.relative_to(root)) if root in exact.parents else str(exact)
    return findings, inventory


def parse_metadata_block(text: str) -> tuple[dict[str, str], list[Finding]]:
    findings: list[Finding] = []
    start_count = text.count("ARXIV-METADATA-BEGIN")
    end_count = text.count("ARXIV-METADATA-END")
    if start_count != 1 or end_count != 1:
        findings.append(Finding("BLOCKER", "METADATA_BLOCK", f"Expected exactly one metadata block; found {start_count} begin marker(s) and {end_count} end marker(s)."))
        return {}, findings
    block_match = re.search(
        r"\\iffalse[^\S\r\n]*\r?\n[^\S\r\n]*ARXIV-METADATA-BEGIN[^\S\r\n]*\r?\n"
        r"([\s\S]*?)"
        r"\r?\n[^\S\r\n]*ARXIV-METADATA-END[^\S\r\n]*\r?\n[^\S\r\n]*\\fi\b",
        text,
    )
    if not block_match:
        findings.append(Finding("BLOCKER", "METADATA_BLOCK_FORMAT", "Metadata markers must be inside exactly one raw \\iffalse / \\fi region."))
        return {}, findings
    if any(line.lstrip().startswith("%") for line in block_match.group(1).splitlines()):
        findings.append(Finding("BLOCKER", "METADATA_PERCENT_COMMENTS", "Do not prefix metadata-region lines with `%`; the false conditional already hides them."))
    if re.search(r"\\(?:if\w*|fi)\b", block_match.group(1)):
        findings.append(Finding("BLOCKER", "METADATA_NESTED_CONDITIONAL", "Metadata-region content contains a TeX conditional token that may terminate or unbalance \\iffalse."))
    metadata: dict[str, str] = {}
    seen_fields: Counter[str] = Counter()
    allowed_fields = set(METADATA_FIELDS) | {"Abstract", "Abstract source"}
    for line_number_in_block, line in enumerate(block_match.group(1).splitlines(), start=1):
        if not line.strip():
            continue
        match = re.match(r"^([^:]+):\s*(.*)$", line)
        if not match:
            findings.append(Finding("BLOCKER", "METADATA_MALFORMED_LINE", f"Metadata line {line_number_in_block} is not `Field: value`: {line.strip()}"))
            continue
        field = match.group(1).strip()
        value = match.group(2).strip()
        seen_fields[field] += 1
        if seen_fields[field] > 1:
            findings.append(Finding("BLOCKER", "METADATA_DUPLICATE_FIELD", f"Metadata field appears more than once: {field}"))
        if field not in allowed_fields:
            findings.append(Finding("BLOCKER", "METADATA_UNKNOWN_FIELD", f"Unknown metadata field: {field}"))
        metadata[field] = value
    for field in METADATA_FIELDS:
        if field in OPTIONAL_METADATA_FIELDS:
            continue
        if field not in metadata or not metadata[field]:
            findings.append(Finding("BLOCKER", "METADATA_FIELD", f"Missing or empty metadata field: {field}"))
    for field, value in metadata.items():
        try:
            value.encode("ascii")
        except UnicodeEncodeError:
            findings.append(Finding("BLOCKER", "METADATA_NON_ASCII", f"Metadata field `{field}` contains non-ASCII characters."))
    has_abstract = bool(metadata.get("Abstract"))
    has_source = bool(metadata.get("Abstract source"))
    if has_abstract == has_source:
        findings.append(Finding("BLOCKER", "ABSTRACT_METADATA_MODE", "Use exactly one of `Abstract:` or `Abstract source:` in the metadata region."))
    abstract = metadata.get("Abstract", "")
    if abstract:
        if len(abstract) > 1920:
            findings.append(Finding("BLOCKER", "ABSTRACT_LENGTH", f"Metadata abstract has {len(abstract)} characters; live baseline limit is 1920."))
        if abstract.lower().startswith("abstract"):
            findings.append(Finding("BLOCKER", "ABSTRACT_HEADING", "Metadata abstract begins with the word `Abstract`."))
    if has_source and metadata["Abstract source"] != "copy abstract environment verbatim":
        findings.append(Finding("BLOCKER", "ABSTRACT_SOURCE_VALUE", "Use exactly `Abstract source: copy abstract environment verbatim`."))
    comments = metadata.get("Comments", "")
    if comments and not re.search(r"\b\d+\s+pages?\b", comments, re.IGNORECASE):
        findings.append(Finding("BLOCKER", "COMMENTS_PAGE_COUNT", "Comments must include the final page count."))
    subjects = metadata.get("Subjects", "")
    subject_item = r"[^;]+\s+\([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\)"
    if subjects and not re.fullmatch(subject_item + r"(?:; " + subject_item + r")*", subjects):
        findings.append(Finding("BLOCKER", "SUBJECTS_FORMAT", "Subjects must use exact labels and codes, primary first, with cross-lists separated by semicolon-space."))
    acm = metadata.get("ACM classes", "")
    if acm and not acm.startswith("N/A") and not re.fullmatch(r"[A-Z]\.\d+(?:\.\d+)?(?:; [A-Z]\.\d+(?:\.\d+)?)*", acm):
        findings.append(Finding("BLOCKER", "ACM_CLASS_FORMAT", "ACM classes must use legacy-style codes separated by semicolon-space, e.g. `F.2.2; D.3.4; F.3.2`."))
    msc = metadata.get("MSC classes", "")
    if msc and not msc.startswith("N/A") and "(Primary)" not in msc:
        findings.append(Finding("BLOCKER", "MSC_CLASS_FORMAT", "MSC classes must identify the primary code with `(Primary)` and secondary codes with `(Secondary)` when present."))
    return metadata, findings


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Static arXiv source/final-ZIP preflight")
    parser.add_argument("source", type=Path, help="Staged source directory, main .tex file, or final upload .zip")
    parser.add_argument("--main", help="Main .tex path relative to source root")
    parser.add_argument("--json", dest="json_path", type=Path, help="Also write the full JSON report here")
    parser.add_argument("--metadata-file", type=Path, help="Compare this derived ARXIV_METADATA.txt with the canonical TeX block")
    parser.add_argument("--regenerated-bbl", type=Path, help="Byte-compare a cleanly regenerated .bbl with the shipped main-stem .bbl")
    parser.add_argument("--allowlist", type=Path, help="Text file listing exactly one permitted final-ZIP member per line")
    parser.add_argument("--checksums", type=Path, help="Verify a recursive SHA-256 manifest for the completed handoff")
    parser.add_argument("--allow-ancillary", action="store_true", help="Record explicit author opt-in to arXiv anc/ files")
    parser.add_argument("--shipping-build", action="store_true", help="Compile the extracted final ZIP three times without BibTeX/Biber")
    parser.add_argument("--shipping-pdf", type=Path, help="Persist the PDF built from the extracted final ZIP for visual inspection")
    parser.add_argument("--engine", choices=("pdflatex", "xelatex"), default="pdflatex", help="Engine for --shipping-build")
    args = parser.parse_args()
    if args.shipping_pdf and not args.shipping_build:
        parser.error("--shipping-pdf requires --shipping-build")

    source = args.source.expanduser().resolve()
    if not source.exists():
        parser.error(f"source does not exist: {source}")
    findings: list[Finding] = []
    checksum_report: dict[str, object] | None = None
    if args.checksums:
        checksum_report, checksum_findings = verify_checksum_manifest(args.checksums.expanduser().resolve())
        findings.extend(checksum_findings)
    archive_report: dict[str, object] | None = None
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if source.is_file() and source.suffix.lower() == ".zip":
        root, temporary, archive_report, archive_findings = inspect_and_extract_zip(source, args.allow_ancillary)
        findings.extend(archive_findings)
        explicit_main = args.main
        if args.allowlist:
            allowlist_path = args.allowlist.expanduser().resolve()
            if not allowlist_path.is_file():
                findings.append(Finding("BLOCKER", "ARCHIVE_ALLOWLIST_MISSING", "Requested explicit upload allowlist does not exist.", str(allowlist_path)))
            else:
                expected_members = {
                    line.strip()
                    for line in read_text(allowlist_path).splitlines()
                    if line.strip() and not line.lstrip().startswith("#")
                }
                actual_members = {str(item["path"]) for item in archive_report.get("members", [])}
                for name in sorted(actual_members - expected_members):
                    findings.append(Finding("BLOCKER", "ARCHIVE_NOT_ALLOWLISTED", "ZIP member was not explicitly allowlisted.", name))
                for name in sorted(expected_members - actual_members):
                    findings.append(Finding("BLOCKER", "ARCHIVE_ALLOWLIST_MISSING_MEMBER", "Allowlisted dependency is absent from the final ZIP.", name))
                archive_report["allowlist"] = str(allowlist_path)
                archive_report["allowlist_matches"] = actual_members == expected_members
        else:
            findings.append(Finding("BLOCKER", "ARCHIVE_ALLOWLIST_MISSING", "Final ZIP audit requires an explicit member allowlist; never infer approval from a directory listing."))
    else:
        root = source.parent if source.is_file() else source
        explicit_main = source.name if source.is_file() else args.main

    files = sorted(path for path in root.rglob("*") if path.is_file())
    tex_files = [path for path in files if path.suffix.lower() == ".tex"]
    bib_files = [path for path in files if path.suffix.lower() == ".bib"]
    bbl_files = [path for path in files if path.suffix.lower() == ".bbl"]
    for path in files:
        relative = path.relative_to(root)
        for component in relative.parts:
            if not ALLOWED_COMPONENT.fullmatch(component):
                findings.append(Finding("BLOCKER", "FILENAME", f"Disallowed filename/path component `{component}`.", str(relative)))
        if any(component.startswith(".") for component in relative.parts):
            findings.append(Finding("BLOCKER", "HIDDEN_FILE", "Hidden files/directories are deleted upon announcement and do not belong in the upload.", str(relative)))
        lower_name = relative.as_posix().lower()
        if SECRET_NAMES.search(lower_name):
            findings.append(Finding("BLOCKER", "SECRET_FILE", "Possible credential/private-key file in source tree.", str(relative)))
        suffix = "".join(path.suffixes[-2:]).lower() if len(path.suffixes) >= 2 else path.suffix.lower()
        if path.suffix.lower() in GENERATED_SUFFIXES or suffix in GENERATED_SUFFIXES:
            findings.append(Finding("BLOCKER", "GENERATED_FILE", "Generated build file should not be in the upload source.", str(relative)))

    main_tex, main_findings = find_main(root, explicit_main, tex_files)
    findings.extend(main_findings)
    if main_tex and main_tex.with_suffix(".pdf").exists():
        findings.append(Finding("BLOCKER", "GENERATED_MAIN_PDF", "A PDF matching the main TeX stem is present and is normally removed/rebuilt by arXiv.", f"{main_tex.stem}.pdf"))

    matching_bbl_available = bool(main_tex and main_tex.with_suffix(".bbl").is_file())
    dep_findings, dependencies = dependency_findings(root, tex_files, matching_bbl_available)
    findings.extend(dep_findings)

    raw_tex_texts: dict[Path, str] = {path: read_text(path) for path in tex_files}
    tex_texts: dict[Path, str] = {
        path: strip_tex_comments(remove_metadata_block(text)) for path, text in raw_tex_texts.items()
    }
    joined = "\n".join(tex_texts.values())
    raw_joined = "\n".join(remove_metadata_block(text) for text in raw_tex_texts.values())

    for description, pattern in HARD_SOURCE_HYGIENE.items():
        for path, text_value in tex_texts.items():
            for match in pattern.finditer(text_value):
                code = "SHELL_ESCAPE" if description == "shell-escape command" else "SOURCE_HYGIENE"
                findings.append(Finding("BLOCKER", code, description, f"{path.relative_to(root)}:{line_number(text_value, match.start())}"))

    citation_occurrences: list[dict[str, object]] = []
    cited_keys: list[str] = []
    nocite_all = False
    for path, text in tex_texts.items():
        for value, offset in command_arguments(text, CITE_START):
            keys = [key.strip() for key in value.split(",") if key.strip()]
            if keys == ["*"]:
                nocite_all = True
                continue
            cited_keys.extend(keys)
            line = line_number(text, offset)
            source_line = text.splitlines()[line - 1].strip() if text.splitlines() else ""
            citation_occurrences.append({
                "file": str(path.relative_to(root)),
                "line": line,
                "keys": keys,
                "context": source_line[:500],
            })

    bib_source_keys: list[str] = []
    for path in bib_files:
        bib_source_keys.extend(BIB_KEY.findall(read_text(path)))
    bbl_file_keys: list[str] = []
    for path in bbl_files:
        bbl_text = read_text(path)
        bbl_file_keys.extend(BIBITEM.findall(bbl_text))
        bbl_file_keys.extend(BIBLATEX_ENTRY.findall(bbl_text))
    inline_bib_keys = BIBITEM.findall(joined)
    bib_key_set = set(bib_source_keys)
    bbl_key_set = set(bbl_file_keys)
    inline_key_set = set(inline_bib_keys)
    defined_key_set = bib_key_set | bbl_key_set | inline_key_set
    duplicates = sorted(
        set(key for key, count in Counter(bib_source_keys).items() if count > 1)
        | set(key for key, count in Counter(bbl_file_keys).items() if count > 1)
        | set(key for key, count in Counter(inline_bib_keys).items() if count > 1)
    )
    cited_key_set = set(cited_keys)
    missing_cites = sorted(cited_key_set - defined_key_set)
    uncited = [] if nocite_all else sorted(defined_key_set - cited_key_set)
    for key in duplicates:
        findings.append(Finding("BLOCKER", "DUPLICATE_BIB_KEY", f"Bibliography key is defined more than once: {key}"))
    for key in missing_cites:
        findings.append(Finding("BLOCKER", "MISSING_CITATION", f"Cited key has no bibliography entry: {key}"))
    for key in uncited:
        findings.append(Finding("BLOCKER", "UNCITED_BIB_ENTRY", f"Bibliography entry is not cited: {key}"))
    if cited_keys and not defined_key_set:
        findings.append(Finding("BLOCKER", "BIBLIOGRAPHY_MISSING", "Citations exist but no .bib entries or \\bibitem entries were found."))
    if bib_files:
        for key in sorted(cited_key_set - bib_key_set):
            findings.append(Finding("BLOCKER", "CITATION_MISSING_FROM_BIB", f"Cited key is absent from the audited .bib source: {key}"))
    if bbl_files:
        for key in sorted(cited_key_set - bbl_key_set):
            findings.append(Finding("BLOCKER", "CITATION_MISSING_FROM_BBL", f"Cited key is absent from the shipped .bbl: {key}"))
    if bib_files and bbl_files:
        for key in sorted(bib_key_set - bbl_key_set):
            findings.append(Finding("BLOCKER", "BIB_BBL_KEY_MISMATCH", f"Key is present in .bib but absent from .bbl: {key}"))
        for key in sorted(bbl_key_set - bib_key_set):
            findings.append(Finding("BLOCKER", "BIB_BBL_KEY_MISMATCH", f"Key is present in .bbl but absent from .bib: {key}"))
    referenced_bibs = {
        str(item["resolved"])
        for item in dependencies
        if item.get("kind") in {"bib", "bibresource"} and item.get("resolved")
    }
    for path in bib_files:
        relative = str(path.relative_to(root))
        if relative not in referenced_bibs:
            findings.append(Finding("WARNING", "UNREFERENCED_BIB_FILE", "Bibliography file is not referenced by a detected bibliography command.", relative))

    biblatex_match = re.search(r"\\usepackage(?:\s*\[([^]]*)\])?\s*\{biblatex\}", joined)
    biblatex_options = biblatex_match.group(1) if biblatex_match and biblatex_match.group(1) else ""
    backend_match = re.search(r"(?:^|,)\s*backend\s*=\s*([A-Za-z0-9_-]+)", biblatex_options, re.IGNORECASE)
    style_match = re.search(r"(?:^|,)\s*style\s*=\s*([A-Za-z0-9_-]+)", biblatex_options, re.IGNORECASE)
    bibliography_command_used = any(item.get("kind") in {"bib", "bibresource"} for item in dependencies)
    inline_bibliography = bool(re.search(r"\\begin\s*\{thebibliography\}", joined))
    if biblatex_match:
        bibliography_package = "biblatex"
        bibliography_backend = backend_match.group(1) if backend_match else "biber (default)"
        bibliography_style = style_match.group(1) if style_match else "biblatex default/declared elsewhere"
    elif bibliography_command_used:
        bibliography_package = "natbib" if re.search(r"\\usepackage(?:\s*\[[^]]*\])?\s*\{natbib\}", joined) else "classic BibTeX"
        bibliography_backend = "bibtex"
        bibliography_style = first_command_argument(joined, "bibliographystyle") or "unspecified"
    elif inline_bibliography:
        bibliography_package = "thebibliography"
        bibliography_backend = "manual"
        bibliography_style = "inline"
    else:
        bibliography_package = "none detected"
        bibliography_backend = "none detected"
        bibliography_style = "none detected"

    expected_bbl: Path | None = main_tex.with_suffix(".bbl") if main_tex else None
    bbl_byte_comparison: dict[str, object] = {
        "performed": False,
        "regenerated_file": str(args.regenerated_bbl.expanduser().resolve()) if args.regenerated_bbl else None,
        "matches_shipped_bbl": None,
    }
    if bibliography_command_used:
        if not bib_files:
            findings.append(Finding("BLOCKER", "BIB_SOURCE_MISSING_STRICT", "Strict publication default requires the audited .bib source in addition to the rendered .bbl."))
        if expected_bbl and not expected_bbl.is_file():
            findings.append(Finding("BLOCKER", "BBL_MISSING_STRICT", f"Strict publication default requires a freshly generated `{expected_bbl.name}` matching the main TeX stem."))
        if expected_bbl and expected_bbl.is_file():
            if args.regenerated_bbl:
                regenerated_path = args.regenerated_bbl.expanduser().resolve()
                if not regenerated_path.is_file():
                    findings.append(Finding("BLOCKER", "BBL_REGEN_COMPARE", "Requested regenerated .bbl does not exist.", str(regenerated_path)))
                else:
                    matches = expected_bbl.read_bytes() == regenerated_path.read_bytes()
                    bbl_byte_comparison = {
                        "performed": True,
                        "regenerated_file": str(regenerated_path),
                        "matches_shipped_bbl": matches,
                    }
                    if not matches:
                        findings.append(Finding("BLOCKER", "BBL_REGEN_COMPARE", "Regenerated .bbl is not byte-identical to the shipped main-stem .bbl.", str(expected_bbl.relative_to(root))))
            else:
                findings.append(Finding("NOTE", "BBL_REGEN_COMPARE_REQUIRED", "Regenerate the bibliography in a clean full-source build and byte-compare it with the shipped .bbl.", str(expected_bbl.relative_to(root))))
    if inline_bibliography and not bibliography_command_used:
        findings.append(Finding("WARNING", "MANUAL_BIBLIOGRAPHY", "Manual thebibliography is valid, but the strict default prefers an audited .bib plus matching .bbl unless a technical reason is documented."))
    if main_tex and bbl_files and expected_bbl not in bbl_files:
        names = ", ".join(str(path.relative_to(root)) for path in bbl_files)
        findings.append(Finding("BLOCKER", "BBL_NAME", f"No .bbl matches the main TeX filename; found: {names}"))
    if expected_bbl and expected_bbl in bbl_files and len(bbl_files) > 1:
        extras = ", ".join(str(path.relative_to(root)) for path in bbl_files if path != expected_bbl)
        findings.append(Finding("BLOCKER", "EXTRA_BBL", f"Unexpected extra .bbl file(s) in source/upload: {extras}"))
    if biblatex_match and expected_bbl and expected_bbl.is_file():
        findings.append(Finding("WARNING", "BIBLATEX_BBL_COMPAT", "Record local BibLaTeX/Biber versions, selected arXiv TeX Live tree, and .bbl format compatibility."))

    labels = [value.strip() for value, _ in command_arguments(joined, LABEL_START)]
    refs = [value.strip() for value, _ in command_arguments(joined, REF_START)]
    for key in sorted(set(refs) - set(labels)):
        findings.append(Finding("BLOCKER", "MISSING_LABEL", f"Reference target has no label: {key}"))
    for key, count in Counter(labels).items():
        if count > 1:
            findings.append(Finding("BLOCKER", "DUPLICATE_LABEL", f"Label is defined more than once: {key}"))

    for description, pattern in PLACEHOLDERS.items():
        for path, text in tex_texts.items():
            for match in pattern.finditer(text):
                policy_markup = description in {
                    "line-number command", "margin-note command", "highlight/edit markup", "draft/referee mode"
                }
                findings.append(Finding("BLOCKER" if policy_markup else "WARNING", "MANUSCRIPT_POLICY" if policy_markup else "MANUSCRIPT_MARKUP", description, f"{path.relative_to(root)}:{line_number(text, match.start())}"))

    metadata: dict[str, str] = {}
    metadata_comparison: dict[str, object] = {"file": None, "matches_canonical_block": None, "differences": []}
    abstract_report: dict[str, object] = {"found": False}
    if main_tex:
        main_raw = read_text(main_tex)
        metadata, metadata_findings = parse_metadata_block(main_raw)
        findings.extend(Finding(item.severity, item.code, item.message, str(main_tex.relative_to(root))) for item in metadata_findings)
        if first_command_argument(joined, "title") is None:
            findings.append(Finding("BLOCKER", "TITLE_MISSING", "No \\title{...} found in the TeX source.", str(main_tex.relative_to(root))))
        if first_command_argument(joined, "author") is None:
            findings.append(Finding("BLOCKER", "AUTHOR_MISSING", "No \\author{...} found in the TeX source.", str(main_tex.relative_to(root))))
        if first_command_argument(joined, "date") is None:
            findings.append(Finding("BLOCKER", "SOURCE_HYGIENE", "No explicit \\date{...} was found; standard LaTeX classes may silently render the rebuild date via \\today. Use an intentional fixed date or \\date{}.", str(main_tex.relative_to(root))))
        abstract_match = re.search(r"\\begin\s*\{abstract\}([\s\S]*?)\\end\s*\{abstract\}", joined)
        if not abstract_match:
            findings.append(Finding("BLOCKER", "ABSTRACT_MISSING", "No abstract environment found."))
        else:
            abstract_body = abstract_match.group(1)
            paper_abstract = normalize_space(abstract_body)
            abstract_issues = abstract_copy_paste_issues(abstract_body, raw_joined)
            abstract_report = {
                "found": True,
                "normalized_characters": len(paper_abstract),
                "ascii": paper_abstract.isascii(),
                "citation_present": bool(CITE_START.search(abstract_body)),
                "copy_paste_issues": abstract_issues,
                "copy_paste_safe": not abstract_issues,
                "metadata_mode": "expanded Abstract" if metadata.get("Abstract") else "copy abstract environment verbatim" if metadata.get("Abstract source") else "missing",
            }
        if abstract_match and metadata.get("Abstract"):
            metadata_abstract = normalize_space(metadata["Abstract"])
            if paper_abstract != metadata_abstract:
                findings.append(Finding("WARNING", "ABSTRACT_TRANSFORM_VERIFY", "The expanded metadata abstract differs textually from the visible abstract; verify scientific identity and document each macro/formatting expansion."))
        elif abstract_match and metadata.get("Abstract source"):
            for issue in abstract_report.get("copy_paste_issues", []):
                findings.append(Finding("BLOCKER", "ABSTRACT_NOT_COPY_PASTE", f"Abstract source cannot be copied verbatim: {issue}."))

        metadata_path = args.metadata_file.expanduser().resolve() if args.metadata_file else root / "ARXIV_METADATA.txt"
        if metadata_path.is_file():
            derived_metadata = parse_metadata_text(read_text(metadata_path))
            all_fields = sorted(set(metadata) | set(derived_metadata))
            differences = [
                {"field": field, "tex": metadata.get(field), "metadata_file": derived_metadata.get(field)}
                for field in all_fields
                if metadata.get(field) != derived_metadata.get(field)
            ]
            metadata_comparison = {
                "file": str(metadata_path),
                "matches_canonical_block": not differences,
                "differences": differences,
            }
            if differences:
                findings.append(Finding("BLOCKER", "METADATA_SYNC", "ARXIV_METADATA.txt differs from the canonical TeX metadata block field-by-field.", str(metadata_path)))
        elif args.metadata_file:
            findings.append(Finding("BLOCKER", "METADATA_SYNC", "Requested metadata convenience file does not exist.", str(metadata_path)))

    comments = metadata.get("Comments", "")
    object_patterns = {
        "figures": re.compile(r"\\begin\s*\{figure\*?\}"),
        "tables": re.compile(r"\\begin\s*\{(?:table\*?|longtable)\}"),
        "algorithms": re.compile(r"\\begin\s*\{algorithm\*?\}"),
    }
    for plural, pattern in object_patterns.items():
        actual = len(pattern.findall(joined))
        if not actual:
            continue
        singular = plural[:-1]
        stated_match = re.search(rf"\b(\d+)\s+{singular}s?\b", comments, re.IGNORECASE)
        if not stated_match:
            findings.append(Finding("BLOCKER", "COMMENTS_OBJECT_COUNT", f"Comments must state the final {plural} count ({actual})."))
        elif int(stated_match.group(1)) != actual:
            findings.append(Finding("BLOCKER", "COMMENTS_OBJECT_COUNT", f"Comments states {stated_match.group(1)} {plural}, but the TeX source contains {actual} detected environment(s)."))

    artifact_mentions: list[dict[str, object]] = []
    for path, text in tex_texts.items():
        lines = text.splitlines()
        for number, source_line in enumerate(lines, start=1):
            if ARTIFACT_TERM.search(source_line):
                artifact_mentions.append({
                    "file": str(path.relative_to(root)),
                    "line": number,
                    "context": source_line.strip()[:500],
                    "external_cue": bool(EXTERNAL_ARTIFACT_CUE.search(source_line)),
                })
    visible_github = sorted(set(GITHUB_URL.findall(joined)))
    external_value = metadata.get("External artifacts", "")
    external_none = external_value.startswith(("N/A", "None"))
    external_claimed = bool(visible_github) or any(bool(item["external_cue"]) for item in artifact_mentions) or (bool(external_value) and not external_none)
    if external_claimed:
        if external_none:
            findings.append(Finding("BLOCKER", "ARTIFACT_METADATA_MISMATCH", "The paper mentions an external artifact but `External artifacts` says none."))
        if not visible_github:
            findings.append(Finding("BLOCKER", "ARTIFACT_GITHUB_IN_PAPER", "Every external artifact requires an exact public GitHub repository URL in the visible manuscript."))
        if not GITHUB_URL.search(metadata.get("Comments", "")):
            findings.append(Finding("BLOCKER", "ARTIFACT_GITHUB_IN_COMMENTS", "A material external artifact requires its public GitHub repository URL in arXiv Comments."))
        if not GITHUB_URL.search(external_value):
            findings.append(Finding("BLOCKER", "ARTIFACT_GITHUB_METADATA", "`External artifacts` must record the exact public GitHub repository URL."))
        if not re.search(r"\b(?:release|tag)\b", external_value, re.IGNORECASE) or not re.search(r"\bcommit\b", external_value, re.IGNORECASE):
            findings.append(Finding("BLOCKER", "ARTIFACT_PIN", "`External artifacts` must record a release/tag and commit hash matching the paper."))
        if not ARTIFACT_ROLE.search(joined):
            findings.append(Finding("BLOCKER", "ARTIFACT_ROLE_MISSING", "The visible manuscript must classify the artifact as logically required, supporting, or regression-only and distinguish verification code from proof premises."))
        if not re.search(r"\b(?:release|tag)\b", joined, re.IGNORECASE):
            findings.append(Finding("BLOCKER", "ARTIFACT_RELEASE_IN_PAPER", "The visible manuscript must identify the exact repository release/tag associated with the paper."))
        findings.append(Finding("WARNING", "ARTIFACT_LIVE_VERIFY", "Static checks cannot prove the GitHub repository is public, pinned, complete, or reproducible; perform the live artifact ledger audit."))
    elif artifact_mentions:
        findings.append(Finding("WARNING", "ARTIFACT_MENTION_REVIEW", "Artifact-related terms were found; confirm none refers to external code, certificates, formal proofs, data, or supplements."))

    ai_value = metadata.get("AI disclosure", "")
    ai_metadata_present = bool(ai_value)
    ai_none = ai_metadata_present and ai_value.startswith(("N/A", "None"))
    visible_ai = bool(AI_DISCLOSURE.search(joined))
    if visible_ai:
        model_matches = list(AI_EXACT_MODEL.finditer(joined))
        mode_matches = list(AI_MODE.finditer(joined))
        if not model_matches:
            findings.append(Finding("BLOCKER", "AI_MODEL_GENERIC", "Visible AI disclosure must name each provider and exact model/product, not only a vendor or generic AI tool."))
        if model_matches and len(mode_matches) < len(model_matches):
            findings.append(Finding("BLOCKER", "AI_MODE_MISSING", "Visible AI disclosure must give the thinking/reasoning mode for every named model."))
        if not AI_ROLE.search(joined):
            findings.append(Finding("BLOCKER", "AI_ROLE_MISSING", "Visible AI disclosure must state the role of each model in research, drafting, checking, code, or referee work."))
        if not ai_metadata_present:
            findings.append(Finding("BLOCKER", "AI_METADATA_MISSING", "The visible manuscript discloses AI use, but the canonical metadata region has no AI disclosure field."))
        elif ai_none:
            findings.append(Finding("BLOCKER", "AI_METADATA_MISMATCH", "The visible manuscript discloses AI use but the metadata region says none."))
    elif ai_metadata_present and not ai_none:
        findings.append(Finding("BLOCKER", "AI_DISCLOSURE_HIDDEN_ONLY", "The metadata region records AI use, but the exact disclosure is absent from the visible manuscript."))
    else:
        findings.append(Finding("WARNING", "AI_DISCLOSURE_CONFIRM", "No visible AI disclosure was detected. Obtain an explicit model/mode/role inventory; absence is not proof that disclosure is unnecessary."))
    if ai_value and not ai_none and " -- " in ai_value:
        exact_ai_text = normalize_space(ai_value.split(" -- ", 1)[1])
        if exact_ai_text and exact_ai_text not in normalize_space(joined):
            findings.append(Finding("BLOCKER", "AI_DISCLOSURE_DIVERGENCE", "The exact AI disclosure recorded in metadata does not match visible manuscript text."))

    urls = sorted(set(match.group(0).rstrip(".,;:)") for match in URL.finditer(raw_joined)))
    arxiv_ids = sorted(set(ARXIV_ID.findall(raw_joined)))
    doi_ids = sorted(set(match.group(0).rstrip(".,;:)") for match in DOI.finditer(raw_joined)))
    arxiv_tokens = list(re.finditer(r"arxiv\s*:", raw_joined, re.IGNORECASE))
    for token in arxiv_tokens:
        if not ARXIV_ID.match(raw_joined, token.start()):
            findings.append(Finding("WARNING", "ARXIV_ID_FORMAT", "Possible malformed or non-canonical arXiv identifier."))

    novelty_claims: list[dict[str, object]] = []
    for path, text_value in tex_texts.items():
        lines = text_value.splitlines()
        for match in NOVELTY_CLAIM.finditer(text_value):
            claim_line = line_number(text_value, match.start())
            novelty_claims.append({
                "file": str(path.relative_to(root)),
                "line": claim_line,
                "term": match.group(0),
                "context": lines[claim_line - 1].strip()[:500] if lines else "",
            })
    if novelty_claims:
        findings.append(Finding("WARNING", "NOVELTY_AUDIT_REQUIRED", f"Detected {len(novelty_claims)} novelty/open/frontier claim occurrence(s); complete the dedicated primary-source and model-distinction ledger."))

    shipping_build_report: dict[str, object] = {"performed": False}
    if args.shipping_build:
        if archive_report is None:
            findings.append(Finding("BLOCKER", "SHIPPING_BUILD_INPUT", "Shipping build must run on the extracted final ZIP, not a working source directory."))
        elif main_tex is None:
            findings.append(Finding("BLOCKER", "SHIPPING_BUILD_INPUT", "Shipping build cannot run without an unambiguous main TeX file."))
        else:
            shipping_build_report, shipping_findings = run_shipping_build(root, main_tex, args.engine, comments)
            findings.extend(shipping_findings)
            if args.shipping_pdf:
                built_pdf = root / f"{main_tex.stem}.pdf"
                shipping_pdf_path = args.shipping_pdf.expanduser().resolve()
                if built_pdf.is_file():
                    shipping_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(built_pdf, shipping_pdf_path)
                    shipping_build_report["persisted_pdf"] = str(shipping_pdf_path)
                else:
                    findings.append(Finding("BLOCKER", "SHIPPING_BUILD_PDF", "Cannot persist shipping PDF because the extracted-archive build produced none.", str(shipping_pdf_path)))
            archive_report["shipping_build"] = shipping_build_report

    counts = Counter(item.severity for item in findings)
    limitations = [
        "No external citation identity, novelty/open-status, claim-support, correction/retraction, GitHub availability/content, URL-access, or rights verification was performed.",
        "Static TeX parsing is conservative and may require manual resolution for macros or generated paths.",
    ]
    if bibliography_command_used and not bbl_byte_comparison.get("performed"):
        limitations.append("No regenerated-.bbl byte comparison was performed.")
    if not shipping_build_report.get("performed"):
        limitations.append("No extracted-final-ZIP LaTeX-only shipping build or PDF inspection was performed.")

    result = {
        "input": str(source),
        "source_root": str(root),
        "main_tex": str(main_tex.relative_to(root)) if main_tex else None,
        "summary": {
            "blockers": counts.get("BLOCKER", 0),
            "warnings": counts.get("WARNING", 0),
            "notes": counts.get("NOTE", 0),
            "tex_files": len(tex_files),
            "bib_files": len(bib_files),
            "bbl_files": len(bbl_files),
            "citation_keys": len(set(cited_keys)),
            "citation_occurrences": len(citation_occurrences),
            "archive_members": archive_report.get("member_count", 0) if archive_report else None,
        },
        "findings": [finding_dict(item) for item in findings],
        "metadata": metadata,
        "metadata_file_comparison": metadata_comparison,
        "abstract": abstract_report,
        "dependencies": dependencies,
        "bibliography": {
            "package": bibliography_package,
            "style": bibliography_style,
            "backend": bibliography_backend,
            "expected_bbl": str(expected_bbl.relative_to(root)) if expected_bbl else None,
            "bib_keys": sorted(bib_key_set),
            "bbl_keys": sorted(bbl_key_set),
            "inline_keys": sorted(inline_key_set),
            "bbl_byte_comparison": bbl_byte_comparison,
        },
        "citations": {
            "keys": sorted(set(cited_keys)),
            "occurrences": citation_occurrences,
            "defined_keys": sorted(defined_key_set),
            "missing_keys": missing_cites,
            "duplicate_keys": duplicates,
            "uncited_keys": uncited,
            "nocite_all": nocite_all,
        },
        "artifacts": {
            "mentions": artifact_mentions,
            "visible_github_urls": visible_github,
            "metadata_value": external_value,
            "live_verification_required": external_claimed,
            "visible_role_classification_detected": bool(ARTIFACT_ROLE.search(joined)),
            "visible_release_or_tag_detected": bool(re.search(r"\b(?:release|tag)\b", joined, re.IGNORECASE)),
        },
        "ai_disclosure": {
            "visible_disclosure_detected": visible_ai,
            "metadata_value": ai_value,
            "exact_models_detected": [match.group(0) for match in AI_EXACT_MODEL.finditer(joined)],
            "modes_detected": [match.group(0) for match in AI_MODE.finditer(joined)],
        },
        "archive": archive_report,
        "shipping_build": shipping_build_report,
        "novelty": {
            "claim_occurrences": novelty_claims,
            "external_verification_performed": False,
        },
        "checksums": checksum_report,
        "identifiers": {"arxiv": arxiv_ids, "doi": doi_ids, "urls": urls},
        "limitations": limitations,
    }

    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(payload + "\n", encoding="utf-8")

    print(f"Main TeX: {result['main_tex'] or 'UNRESOLVED'}")
    print(f"Blockers: {counts.get('BLOCKER', 0)}  Warnings: {counts.get('WARNING', 0)}")
    for finding in findings:
        location = f" [{finding.location}]" if finding.location else ""
        print(f"{finding.severity} [{requirement_basis(finding.code)}]: {finding.code}{location}: {finding.message}")
    print("Machine-readable report:")
    print(payload)

    if counts.get("BLOCKER", 0):
        return 2
    if counts.get("WARNING", 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
