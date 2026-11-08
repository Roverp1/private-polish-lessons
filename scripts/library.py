#!/usr/bin/env python3
"""Bounded, local-only source retrieval. Python standard library; see source-library/README.md."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "reference-materials"
DERIVED = RAW / ".derived"
CATALOG = ROOT / "source-library/catalog.json"
CACHE_VERSION = 1
MAX_PAGES = 5
MAX_OUTPUT = 20000
OCR_PROFILE = "mutool-110dpi-tesseract-pol+eng-tsv-v2"
BAD_QUALITY = {"empty", "watermark-only", "suspect-garbled", "sparse", "extraction-error"}
PACKAGES = {
    "pdfinfo": "poppler-utils", "pdftotext": "poppler-utils",
    "mutool": "mupdf", "tesseract": "tesseract", "ffprobe": "ffmpeg",
}


class LibraryError(Exception):
    pass


def tool(name):
    override = os.environ.get("LIBRARY_" + name.upper())
    if override:
        resolved = shutil.which(override)
        if not resolved:
            raise LibraryError(f"LIBRARY_{name.upper()} is not executable: {override}")
        return resolved
    resolved = shutil.which(name)
    if resolved:
        return resolved
    for candidate in sorted(Path("/nix/store").glob(f"*-{PACKAGES[name]}-*/bin/{name}"), reverse=True):
        if os.access(candidate, os.X_OK):
            return str(candidate)
    raise LibraryError(
        f"Missing {name}. Set LIBRARY_{name.upper()} or use "
        "nix-shell -p poppler_utils mupdf tesseract ffmpeg (include pol+eng language data for OCR)."
    )


def run(command, timeout=60):
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LibraryError(f"{Path(command[0]).name}: {exc}") from exc
    if result.returncode:
        raise LibraryError(f"{Path(command[0]).name}: {result.stderr.decode(errors='replace')[:800]}")
    return result.stdout.decode("utf-8", errors="replace")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def relative(path):
    return path.relative_to(ROOT).as_posix()


def stamp(path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def digest(path):
    before = stamp(path)
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    if stamp(path) != before:
        raise LibraryError(f"Source changed while hashing: {path.name}; retry index.")
    return sha.hexdigest(), before


def source_metadata(path):
    name = unicodedata.normalize("NFKD", path.stem).casefold()
    if "142944" in name:
        return "umcs-cases", "Gramatyka z kulturą. Przez przypadki", "grammar-workbook", None
    if "przez-osoby" in name:
        return "umcs-verbs", "Gramatyka z kulturą. Przez osoby", "grammar-workbook", None
    if "odkrywamy" in name:
        return "odkrywamy", "Odkrywamy język polski", "grammar-reference", None
    if "krok" in name:
        level = "A2" if " a2 " in name else "A1"
        return f"krok-{level.lower()}", f"Polski krok po kroku {level}", "student-book", level
    if "hurra" in name:
        match = re.search(r"\b([123])\b", name)
        if not match:
            raise LibraryError(f"Cannot identify HURRA volume: {path.name}")
        number = match.group(1)
        kind = "teacher-guide" if "nauczyciela" in name else "workbook" if "zeszyt" in name else "student-book"
        short = {"teacher-guide": "guide", "workbook": "workbook", "student-book": "student"}[kind]
        return f"hurra-{number}-{short}", f"HURRA!!! Po polsku {number}: {kind}", kind, {"1": "A1", "2": "A2", "3": "B1"}[number]
    # Unknown additions get filename-based IDs; preserve existing IDs on subsequent runs.
    slug = re.sub(r"[^a-z0-9]+", "-", name).strip("-")[:60] or "source"
    return slug, path.stem, "unknown", None


WATERMARK = re.compile(
    r"https?://\S+|www\.\S+|\b(?:z[ -]?lib(?:rary)?|1lib|annas?-?archive)\b[^\n]*|"
    r"\bAnna[’']?s Archive\b[^\n]*|\bDownloaded (?:from|by)\b[^\n]*|"
    r"\bTelegram\s*:\s*@\S+",
    re.IGNORECASE,
)


def quality(text):
    """Conservative triage, not linguistic validation or evidence of book review."""
    visible = "".join(text.split())
    if not visible:
        return {"status": "empty", "characters": 0, "reason": "No extracted text"}
    cleaned = WATERMARK.sub("", text)
    letters = [c for c in cleaned if c.isalpha()]
    tokens = re.findall(r"[^\W\d_]+", cleaned)
    suspicious = sum(c == "\ufffd" or unicodedata.category(c) in {"Co", "Cn"} for c in text)
    latin = sum("LATIN" in unicodedata.name(c, "") for c in letters)
    singles = sum(len(token) == 1 for token in tokens)
    if WATERMARK.search(text) and len(letters) < 30:
        status, reason = "watermark-only", "Only watermark/URL and little or no book text"
    elif suspicious > max(2, len(visible) * .01) or "(cid:" in text or (len(letters) > 50 and latin / len(letters) < .6) or (len(tokens) > 80 and singles / len(tokens) > .65):
        status, reason = "suspect-garbled", "Replacement/private glyphs, non-Latin encoding, or fragmented words"
    elif len(letters) < 60:
        status, reason = "sparse", "Too little text to establish a useful text layer"
    else:
        status, reason = "usable-unverified", "Heuristic passed; layout, Polish spelling and completeness unverified"
    return {"status": status, "characters": len(visible), "reason": reason}


def cache_root(sha):
    return DERIVED / sha


def page_path(sha, number, mode="text"):
    return cache_root(sha) / mode / f"{number:04d}.txt"


def index_pdf(path, previous):
    sha, original = digest(path)
    source_id, title, kind, level = source_metadata(path)
    if previous:
        source_id = previous["id"]
    info = run([tool("pdfinfo"), str(path)])
    match = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
    if not match:
        raise LibraryError(f"pdfinfo did not report a page count: {path.name}")
    count = int(match.group(1))
    manifest_path = cache_root(sha) / "manifest.json"
    manifest = load(manifest_path) if manifest_path.exists() else {}
    if manifest.get("cache_version") != CACHE_VERSION or manifest.get("sha256") != sha or manifest.get("pdf_pages") != count:
        manifest = {"cache_version": CACHE_VERSION, "sha256": sha, "pdf_pages": count, "pages": {}}
    extractor = tool("pdftotext")
    for number in range(1, count + 1):
        key = str(number)
        target = page_path(sha, number)
        entry = manifest["pages"].get(key, {})
        if target.exists() and entry.get("text", {}).get("status") != "extraction-error" and entry.get("text"):
            # Reclassify existing text when heuristics improve, without re-extracting PDFs.
            entry["text"] = quality(target.read_text(encoding="utf-8"))
            continue
        try:
            text = run([extractor, "-f", str(number), "-l", str(number), "-layout", str(path), "-"])
            if stamp(path) != original:
                raise LibraryError(f"Source changed while extracting PDF page {number}; retry index.")
            write_text(target, text)
            entry["text"] = quality(text)
        except LibraryError as exc:
            entry["text"] = {"status": "extraction-error", "characters": 0, "reason": str(exc)[:500]}
        manifest["pages"][key] = entry
        # Checkpoint partial extraction so interrupted indexing can resume.
        if number % 20 == 0:
            write_json(manifest_path, manifest)
    if stamp(path) != original:
        raise LibraryError(f"Source changed during extraction: {path.name}; retry index.")
    write_json(manifest_path, manifest)
    counts = Counter(entry["text"]["status"] for entry in manifest["pages"].values())
    toc = []
    opening = []
    for number in range(1, min(count, 12) + 1):
        target = page_path(sha, number)
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8")
        if number <= 6 and manifest["pages"][str(number)]["text"]["status"] == "usable-unverified":
            opening.append(number)
        ocr_target = page_path(sha, number, "ocr")
        if ocr_target.exists():
            text += "\n" + ocr_target.read_text(encoding="utf-8")
        if re.search(r"spis\s+tre[śs]ci|table\s+of\s+contents", text, re.IGNORECASE):
            toc.append(number)
    return {
        "id": source_id, "title": title, "kind": kind, "level": level,
        "level_basis": "Series/filename; not a page-level assessment" if level else "Not verified",
        "path": relative(path), "sha256": sha, "bytes": original[0], "pdf_pages": count,
        "text_layer": {"page_quality_counts": dict(sorted(counts.items())), "reviewed": False},
        "ocr": {"cached_pdf_pages": [int(n) for n, entry in manifest["pages"].items() if "ocr" in entry],
                "page_quality_counts": dict(Counter(entry["ocr"]["status"] for entry in manifest["pages"].values() if "ocr" in entry)),
                "limitations": "110 dpi pol+eng OCR; tables, diacritics and page labels require visual verification", "reviewed": False},
        "cache_manifest": relative(manifest_path),
        "frontmatter": {"usable_opening_pdf_pages": opening, "toc_candidate_pdf_pages": toc, "reviewed": False},
        "printed_page_mapping": previous.get("printed_page_mapping") if previous and previous.get("sha256") == sha else None,
    }


def index_audio(path, previous):
    sha, original = digest(path)
    cached = previous and previous.get("sha256") == sha and previous.get("duration_seconds") is not None
    duration = previous["duration_seconds"] if cached else float(run([
        tool("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], timeout=30).strip())
    if stamp(path) != original:
        raise LibraryError(f"Audio changed during indexing: {path.name}")
    level = "A2" if "Audio (A2)" in path.parts else "A1" if "Audio (A1)" in path.parts else None
    return {"id": f"krok-{level.lower()}-audio-{path.stem}" if level else f"audio-{sha[:16]}",
            "kind": "audio", "title": path.stem, "filename": path.name, "level": level,
            "source_id": f"krok-{level.lower()}" if level else None, "path": relative(path),
            "sha256": sha, "bytes": original[0], "duration_seconds": round(duration, 3)}


def index(args):
    if not RAW.is_dir():
        raise LibraryError(f"Missing private source directory: {RAW}")
    old = load(CATALOG) if CATALOG.exists() else {"sources": [], "audio": []}
    old_sources = {item["path"]: item for item in old["sources"]}
    old_audio = {item["path"]: item for item in old["audio"]}
    paths = sorted(p for p in RAW.rglob("*") if p.suffix.lower() == ".pdf" and DERIVED not in p.parents)
    identifiers = {source_metadata(p)[0] for p in paths} | {s["id"] for s in old["sources"]}
    if args.source and set(args.source) - identifiers:
        raise LibraryError("Unknown source ID: " + ", ".join(sorted(set(args.source) - identifiers)))
    selected = [p for p in paths if not args.source or old_sources.get(relative(p), {}).get("id", source_metadata(p)[0]) in args.source]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        sources = list(pool.map(lambda p: index_pdf(p, old_sources.get(relative(p))), selected))
        selected_paths = {relative(p) for p in selected}
        if args.source:
            sources += [item for item in old["sources"] if item["path"] not in selected_paths]
            audio = old["audio"]
        else:
            audio_paths = sorted(p for p in RAW.rglob("*") if p.suffix.lower() == ".mp3" and DERIVED not in p.parents)
            audio = list(pool.map(lambda p: index_audio(p, old_audio.get(relative(p))), audio_paths))
    ids = [item["id"] for item in sources + audio]
    if len(ids) != len(set(ids)):
        raise LibraryError("Duplicate IDs; resolve ambiguous filenames before indexing.")
    catalog = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
               "page_numbering": "1-based PDF pages; printed labels require individually verified mapping",
               "quality_policy": "Automated extraction/OCR heuristics only. No complete-book review claimed.",
               "inventory": {"pdf_count": len(sources), "audio_count": len(audio),
                             "pdf_pages": sum(s["pdf_pages"] for s in sources),
                             "audio_duration_seconds": round(sum(a["duration_seconds"] for a in audio), 3)},
               "sources": sorted(sources, key=lambda item: item["id"]),
               "audio": sorted(audio, key=lambda item: item["id"])}
    write_json(CATALOG, catalog)
    inspect_catalog(catalog, None)


def catalog_source(catalog, source_id):
    for source in catalog["sources"]:
        if source["id"] == source_id:
            return source
    raise LibraryError(f"Unknown source ID: {source_id}; run inspect for IDs.")


def verified_manifest(source):
    path = ROOT / source["path"]
    if not path.is_file():
        raise LibraryError(f"Source missing: {source['path']}")
    sha, original = digest(path)
    if sha != source["sha256"]:
        raise LibraryError(f"Stale catalogue for {source['id']}: source hash changed. Run index --source {source['id']}.")
    manifest_path = ROOT / source["cache_manifest"]
    if not manifest_path.exists():
        raise LibraryError(f"Missing private cache for {source['id']}; run index --source {source['id']}.")
    manifest = load(manifest_path)
    if manifest.get("sha256") != sha or manifest.get("pdf_pages") != source["pdf_pages"] or manifest.get("cache_version") != CACHE_VERSION:
        raise LibraryError(f"Stale/incompatible cache for {source['id']}; run index --source {source['id']}.")
    return path, original, manifest


def page_range(value, count):
    match = re.fullmatch(r"([1-9]\d*)(?:-([1-9]\d*))?", value)
    if not match:
        raise LibraryError("--pdf must be a 1-based page or START-END, e.g. 33-35.")
    start, end = int(match[1]), int(match[2] or match[1])
    if start > end or end > count:
        raise LibraryError(f"Page range must be ordered and within PDF pages 1-{count}.")
    if end - start + 1 > MAX_PAGES:
        raise LibraryError(f"At most {MAX_PAGES} PDF pages per request.")
    return range(start, end + 1)


def ocr_text(tsv):
    lines, words, scores = [], [], []
    last_key = None
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row["level"] != "5" or not row.get("text", "").strip():
            continue
        key = tuple(row[column] for column in ("block_num", "par_num", "line_num"))
        if last_key is not None and key != last_key:
            lines.append(" ".join(words))
            if key[:2] != last_key[:2]:
                lines.append("")
            words = []
        words.append(row["text"])
        scores.append(float(row["conf"]))
        last_key = key
    if words:
        lines.append(" ".join(words))
    text = "\n".join(lines) + "\n"
    result = quality(text)
    if scores:
        mean = sum(scores) / len(scores)
        low_fraction = sum(score < 50 for score in scores) / len(scores)
        result.update(mean_word_confidence=round(mean, 1), low_confidence_word_fraction=round(low_fraction, 3))
        if result["status"] == "usable-unverified" and (mean < 65 or low_fraction > .35):
            result.update(status="suspect-garbled", reason="Low OCR word confidence; use a bounded visual page check")
    return text, result


def ocr_page(source, path, original, number, manifest):
    target = page_path(source["sha256"], number, "ocr")
    entry = manifest["pages"][str(number)]
    if target.exists() and entry.get("ocr", {}).get("profile") == OCR_PROFILE:
        return
    # Stream exactly one rendered page to OCR; no full PDF reads or image files.
    renderer, recognizer = tool("mutool"), tool("tesseract")
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    with subprocess.Popen([renderer, "draw", "-q", "-F", "png", "-r", "110", "-o", "-", str(path), str(number)],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as render:
        assert render.stdout is not None
        try:
            result = subprocess.run([recognizer, "stdin", "stdout", "-l", "pol+eng", "tsv"], stdin=render.stdout,
                                    capture_output=True, timeout=120, env=env)
            render.stdout.close()
            render.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired) as exc:
            render.kill()
            raise LibraryError(f"OCR failed on PDF page {number}: {exc}") from exc
        if result.returncode or render.returncode:
            raise LibraryError(f"OCR failed on PDF page {number}: {result.stderr.decode(errors='replace')[:800]}")
    text, assessment = ocr_text(result.stdout.decode("utf-8", errors="replace"))
    ensure_unchanged(path, original)
    write_text(target, text)
    entry["ocr"] = dict(assessment, profile=OCR_PROFILE, reviewed=False)
    write_json(ROOT / source["cache_manifest"], manifest)


def ensure_unchanged(path, original):
    if stamp(path) != original:
        raise LibraryError("Source changed during retrieval; no output returned. Re-index and retry.")


def pages(args, catalog):
    source = catalog_source(catalog, args.source_id)
    numbers = page_range(args.pdf, source["pdf_pages"])
    path, original, manifest = verified_manifest(source)
    output = []
    for number in numbers:
        if args.ocr:
            ocr_page(source, path, original, number, manifest)
        mode = "ocr" if args.ocr else "text"
        entry = manifest["pages"][str(number)].get(mode, {})
        target = page_path(source["sha256"], number, mode)
        if not target.exists():
            raise LibraryError(f"Missing cached {mode} for PDF page {number}; run index.")
        text = target.read_text(encoding="utf-8").replace("\f", "").strip()
        clipped = text[:args.max_chars]
        output.append(f"=== {source['id']} | PDF page {number} | {mode}: {entry.get('status')} | unreviewed ===\n"
                      + clipped + ("\n[Truncated; use the cached page locally for the remainder.]" if len(text) > len(clipped) else ""))
    ensure_unchanged(path, original)
    result = "\n\n".join(output)
    if len(result) >= MAX_OUTPUT:
        notice = "\n[Total output cap reached.]"
        result = result[:MAX_OUTPUT - len(notice) - 1] + notice
    print(result)


def search(args, catalog):
    selected = [catalog_source(catalog, sid) for sid in args.source] if args.source else catalog["sources"]
    needle = args.pattern.casefold()
    if not needle.strip():
        raise LibraryError("Search pattern must not be empty.")
    matches, seen, skipped = [], 0, 0
    for source in selected:
        path, original, manifest = verified_manifest(source)
        numbers = page_range(args.pdf, source["pdf_pages"]) if args.pdf else range(1, source["pdf_pages"] + 1)
        for number in numbers:
            entry = manifest["pages"][str(number)]
            mode = "ocr" if entry.get("ocr", {}).get("status") == "usable-unverified" else "text"
            status = entry[mode]["status"]
            if status in BAD_QUALITY:
                skipped += 1
                continue
            target = page_path(source["sha256"], number, mode)
            if not target.exists():
                raise LibraryError(f"Missing cached page {source['id']}:{number}; run index.")
            for line in target.read_text(encoding="utf-8").splitlines():
                if needle in line.casefold():
                    if seen >= args.offset and len(matches) < args.limit:
                        normalized = " ".join(line.split())
                        position = normalized.casefold().find(needle)
                        start = max(0, position - 80)
                        snippet = ("…" if start else "") + normalized[start:start + 240]
                        matches.append(f"{source['id']} | PDF page {number} | {mode}, unreviewed | {snippet}")
                    seen += 1
        ensure_unchanged(path, original)
    print("\n".join(matches) if matches else "No matches in usable cached text/OCR.")
    print(f"Showing {len(matches)} of {seen} matching lines; offset {args.offset}. Skipped {skipped} low-quality pages.")
    if seen > args.offset + len(matches):
        print(f"Next: --offset {args.offset + len(matches)} --limit {args.limit}")


def inspect_catalog(catalog, source_id, pdf=None):
    if source_id:
        source = catalog_source(catalog, source_id)
        path, original, manifest = verified_manifest(source)
        if pdf:
            numbers = page_range(pdf, source["pdf_pages"])
            result = {"id": source_id, "sha256": source["sha256"], "pages": {str(n): manifest["pages"][str(n)] for n in numbers}}
        else:
            result = dict(source, current_ocr_pdf_pages=[int(n) for n, entry in manifest["pages"].items() if "ocr" in entry])
        ensure_unchanged(path, original)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    inv = catalog["inventory"]
    print(f"{inv['pdf_count']} PDFs | {inv['pdf_pages']} PDF pages | {inv['audio_count']} audio files | {inv['audio_duration_seconds']:.1f} audio seconds")
    print("Catalogue summary only; inspect SOURCEID validates its hash and cache. All extraction unreviewed.")
    for source in catalog["sources"]:
        counts = ", ".join(f"{key}={value}" for key, value in source["text_layer"]["page_quality_counts"].items())
        print(f"{source['id']}: {source['pdf_pages']} pages, {source['level'] or 'level unverified'}; {counts}")


def bounded_int(low, high):
    def parse(value):
        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return number
    return parse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    cmd = commands.add_parser("index", help="Hash sources, cache each PDF page, inventory audio; no OCR")
    cmd.add_argument("--source", action="append", help="Only refresh this PDF ID (repeatable); omit for full inventory")
    cmd.add_argument("--workers", type=bounded_int(1, 8), default=4)
    cmd = commands.add_parser("inspect", help="List catalogue or validate one source and show metadata")
    cmd.add_argument("source_id", nargs="?")
    cmd.add_argument("--pdf", help="Inspect quality metadata for at most five PDF pages")
    cmd = commands.add_parser("pages", help="Print at most five cached PDF pages (bounded output)")
    cmd.add_argument("source_id")
    cmd.add_argument("--pdf", required=True, help="1-based PDF page or START-END, at most five")
    cmd.add_argument("--ocr", action="store_true", help="OCR selected pages at 110 dpi, pol+eng; reuse cache")
    cmd.add_argument("--max-chars", type=bounded_int(1, 6000), default=4000)
    cmd = commands.add_parser("search", help="Case-insensitive literal search of usable cached pages; no extraction")
    cmd.add_argument("pattern")
    cmd.add_argument("--source", action="append", help="Restrict to PDF ID (repeatable)")
    cmd.add_argument("--pdf", help="Restrict to at most five PDF pages; requires one --source")
    cmd.add_argument("--limit", type=bounded_int(1, 50), default=10)
    cmd.add_argument("--offset", type=bounded_int(0, 1000000), default=0)
    args = parser.parse_args()
    if args.command == "inspect" and args.pdf and not args.source_id:
        parser.error("inspect --pdf requires SOURCEID")
    if args.command == "search" and args.pdf and (not args.source or len(args.source) != 1):
        parser.error("search --pdf requires exactly one --source")
    try:
        if args.command == "index":
            index(args)
        else:
            if not CATALOG.exists():
                raise LibraryError("Catalogue missing; run python3 scripts/library.py index first.")
            catalog = load(CATALOG)
            if args.command == "inspect":
                inspect_catalog(catalog, args.source_id, args.pdf)
            elif args.command == "pages":
                pages(args, catalog)
            else:
                search(args, catalog)
    except (LibraryError, OSError, ValueError, KeyError) as exc:
        print(f"library: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
