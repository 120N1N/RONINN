#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "tmp",
    "vendor",
    "__pycache__",
}

SOURCE_EXTENSIONS = {
    ".astro",
    ".conf",
    ".config",
    ".cs",
    ".css",
    ".env",
    ".erb",
    ".go",
    ".graphql",
    ".gql",
    ".hbs",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".lua",
    ".md",
    ".php",
    ".properties",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sql",
    ".svelte",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".twig",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}

IMPORTANT_NAME_HINTS = {
    "admin",
    "api",
    "auth",
    "authn",
    "authz",
    "billing",
    "cache",
    "callback",
    "controller",
    "controllers",
    "cors",
    "csrf",
    "download",
    "export",
    "graphql",
    "handler",
    "handlers",
    "hook",
    "import",
    "invoice",
    "job",
    "jwt",
    "middleware",
    "model",
    "models",
    "oauth",
    "oidc",
    "payment",
    "permission",
    "policy",
    "queue",
    "route",
    "router",
    "routes",
    "saml",
    "schema",
    "service",
    "services",
    "session",
    "settings",
    "storage",
    "token",
    "upload",
    "webhook",
    "worker",
}

IMPORTANT_BASENAMES = {
    ".env",
    ".env.example",
    ".htaccess",
    "app.py",
    "config.json",
    "config.yaml",
    "config.yml",
    "docker-compose.yml",
    "go.mod",
    "next.config.js",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "server.js",
    "settings.py",
    "vite.config.js",
    "webpack.config.js",
}

CONTENT_HINTS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bapp\.(get|post|put|patch|delete|route)\s*\(",
        r"\brouter\.(get|post|put|patch|delete|route)\s*\(",
        r"\broute\s*[:=]",
        r"@(get|post|put|patch|delete|route)\b",
        r"\bfetch\s*\(",
        r"\baxios\.",
        r"\bgraphql\b",
        r"\bSELECT\b.+\bFROM\b",
        r"\bINSERT\b.+\bINTO\b",
        r"\bUPDATE\b.+\bSET\b",
        r"\b(auth|session|jwt|csrf|cors|permission|role|tenant|owner)\b",
        r"\b(upload|download|export|import|webhook|callback|redirect|url)\b",
    ]
]

REQUIRED_SECTIONS = [
    "RESTATE-OK",
    "FILE-PURPOSE",
    "ENTRYPOINTS",
    "TRUST-BOUNDARIES",
    "ROUTES-ENDPOINTS",
    "DATA-FLOW",
    "SINKS-SOURCES",
    "AUTHZ-AUTHN",
    "ATTACK-SURFACE",
    "MULTI-ANGLE-PLAN",
    "CHAIN-CANDIDATES",
    "EVENTS-WRITTEN",
    "OPEN-GAPS",
]

MEANINGFUL_SECTIONS = [
    "RESTATE-OK",
    "FILE-PURPOSE",
    "ENTRYPOINTS",
    "TRUST-BOUNDARIES",
    "ROUTES-ENDPOINTS",
    "DATA-FLOW",
    "SINKS-SOURCES",
    "AUTHZ-AUTHN",
    "ATTACK-SURFACE",
    "MULTI-ANGLE-PLAN",
    "EVENTS-WRITTEN",
]


@dataclass(frozen=True)
class SourceCandidate:
    file_id: str
    rel_path: str
    abs_path: Path
    language: str
    size: int
    lines: int
    sha256: str
    chunks: int
    reason: str


@dataclass
class SourceScore:
    candidate: SourceCandidate
    score: int
    grade: str
    present: list[str]
    missing: list[str]
    warnings: list[str]
    review_path: str
    runtime_relevant: bool


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def json_dump(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)


def slugify(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    clean = re.sub(r"-{2,}", "-", clean)
    return clean.strip("-") or "item"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def chunk_count(lines: int, chunk_size: int = 200) -> int:
    return max(1, (max(1, lines) + chunk_size - 1) // chunk_size)


def source_id_for(rel_path: str) -> str:
    digest = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()[:8]
    slug = slugify(rel_path.replace("/", "-"))[:72].strip("-")
    return f"src-{slug}-{digest}"


def current_engagement_id(root: Path) -> str:
    parts = root.parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}-{parts[idx + 2]}"
    return root.name


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def write_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json_dump(event) + "\n")


def build_graph(root: Path) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_graph.py"), "--root", str(root)], check=True)


def rel_to(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def norm_path(value: str) -> str:
    if not value:
        return ""
    return Path(value).as_posix().lstrip("./")


def is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\x00" in chunk


def language_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext:
        return ext.lstrip(".")
    return path.name


def line_count(path: Path, max_bytes: int) -> int:
    try:
        data = path.read_bytes()[:max_bytes]
    except OSError:
        return 0
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def content_reason(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:30000]
    except OSError:
        return ""
    for pattern in CONTENT_HINTS:
        if pattern.search(text):
            return f"content hint `{pattern.pattern}`"
    return ""


def important_reason(path: Path, rel_path: str, include_all: bool) -> str:
    name = path.name.lower()
    stem = path.stem.lower()
    parts = {part.lower() for part in Path(rel_path).parts}
    ext = path.suffix.lower()

    if include_all:
        return "all supported source-like files"
    if name in IMPORTANT_BASENAMES:
        return f"important basename `{name}`"
    for hint in IMPORTANT_NAME_HINTS:
        if hint == stem or hint in parts or hint in name:
            return f"name/path hint `{hint}`"
    if ext in {".env", ".conf", ".config", ".ini", ".toml", ".yaml", ".yml"}:
        return f"configuration file `{ext}`"
    if ext in {".graphql", ".gql", ".sql"}:
        return f"query/schema file `{ext}`"
    return content_reason(path)


def should_skip(path: Path, source_root: Path, skip_dirs: set[str]) -> bool:
    try:
        rel = path.relative_to(source_root)
    except ValueError:
        return True
    return any(part in skip_dirs for part in rel.parts[:-1])


def discover_sources(source_root: Path, include_all: bool, skip_dirs: set[str], max_bytes: int, include_ext: set[str]) -> tuple[list[SourceCandidate], list[str]]:
    if not source_root.exists() or not source_root.is_dir():
        raise SystemExit(f"source root is not a directory: {source_root}")

    candidates: list[SourceCandidate] = []
    skipped: list[str] = []
    extensions = SOURCE_EXTENSIONS | include_ext
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if should_skip(path, source_root, skip_dirs):
            continue
        rel_path = rel_to(source_root, path)
        ext = path.suffix.lower()
        if ext not in extensions and path.name.lower() not in IMPORTANT_BASENAMES:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            skipped.append(f"{rel_path}: stat failed")
            continue
        if size > max_bytes:
            skipped.append(f"{rel_path}: larger than max bytes ({size} > {max_bytes})")
            continue
        if is_binary(path):
            skipped.append(f"{rel_path}: binary-looking file")
            continue
        reason = important_reason(path, rel_path, include_all)
        if not reason:
            continue
        candidates.append(
            SourceCandidate(
                file_id=source_id_for(rel_path),
                rel_path=rel_path,
                abs_path=path,
                language=language_for(path),
                size=size,
                lines=line_count(path, max_bytes),
                sha256=file_sha256(path),
                chunks=chunk_count(line_count(path, max_bytes)),
                reason=reason,
            )
        )
    return candidates, skipped


def event_source_id(event: dict[str, Any]) -> str:
    return str(event.get("source_id") or event.get("file_id") or event.get("source_file") or event.get("path") or "")


def event_source_path(event: dict[str, Any]) -> str:
    return norm_path(str(event.get("source_file") or event.get("path") or event.get("file") or ""))


def event_matches_candidate(event: dict[str, Any], candidate: SourceCandidate, endpoint_ids: set[str] | None = None) -> bool:
    aliases = {candidate.file_id, candidate.rel_path, norm_path(candidate.rel_path)}
    sid = event_source_id(event)
    path = event_source_path(event)
    if sid in aliases or norm_path(sid) in aliases or path in aliases:
        return True
    if endpoint_ids and str(event.get("endpoint_id") or "") in endpoint_ids:
        return True
    return False


def events_for_candidate(events: list[dict[str, Any]], candidate: SourceCandidate) -> list[dict[str, Any]]:
    first_pass = [event for event in events if event_matches_candidate(event, candidate)]
    endpoint_ids = {
        str(event.get("endpoint_id") or "")
        for event in first_pass
        if event.get("type") == "source_flow_linked" and event.get("endpoint_id")
    }
    endpoint_ids.update(
        str(event.get("endpoint_id") or "")
        for event in first_pass
        if event.get("type") == "attack_surface_mapped" and event.get("endpoint_id")
    )
    if not endpoint_ids:
        return first_pass
    return [
        event
        for event in events
        if event_matches_candidate(event, candidate, endpoint_ids)
        or (event.get("type") == "endpoint_angle_planned" and str(event.get("endpoint_id") or "") in endpoint_ids)
    ]


def review_candidates(root: Path, candidate: SourceCandidate, source_events: list[dict[str, Any]]) -> list[Path]:
    paths: list[Path] = []
    for event in reversed(source_events):
        raw = str(event.get("review") or event.get("review_artifact") or event.get("review_path") or "")
        if raw:
            paths.append(root / raw)
    paths.extend(
        [
            root / "source-reviews" / f"{candidate.file_id}.md",
            root / "source-reviews" / f"{slugify(candidate.rel_path)}.md",
            root / "source-reviews" / f"{slugify(Path(candidate.rel_path).stem)}.md",
        ]
    )
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(path)
    return deduped


def existing_review_path(root: Path, candidate: SourceCandidate, source_events: list[dict[str, Any]]) -> Path | None:
    for path in review_candidates(root, candidate, source_events):
        if path.exists() and path.is_file() and path.stat().st_size > 0:
            return path
    return None


def section_map(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        title = match.group(1).strip().upper()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def normalize_section_body(body: str) -> str:
    lines: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in {"-", "|---|---|---|", "|---|---|---|---|", "|---|---|---|---|---|"}:
            continue
        if set(line) <= {"|", "-", ":", " "}:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def is_unknown_only(body: str) -> bool:
    clean = normalize_section_body(body).lower()
    clean = clean.replace("`", "").strip("-: \n\t")
    return clean in {"unknown", "n/a", "na", "none", "tidak diketahui", "belum diketahui"}


def meaningful_review_gaps(text: str, has_gap_event: bool) -> tuple[list[str], list[str]]:
    sections = section_map(text)
    missing: list[str] = []
    warnings: list[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            missing.append(f"missing required section {section}")
    for section in MEANINGFUL_SECTIONS:
        if section not in sections:
            continue
        body = sections[section]
        clean = normalize_section_body(body)
        if not clean:
            missing.append(f"section {section} is empty/placeheld")
        elif is_unknown_only(body):
            if has_gap_event:
                warnings.append(f"section {section} is unknown but backed by a gap/blocker event")
            else:
                missing.append(f"section {section} is unknown without a gap/blocker event")
    return missing, warnings


def has_runtime_irrelevant_marker(events: list[dict[str, Any]], review_text: str) -> bool:
    for event in events:
        status = str(event.get("status") or "").lower()
        if status == "not_runtime_relevant":
            return True
        reason = str(event.get("reason") or event.get("notes") or "").lower()
        if "not_runtime_relevant" in reason or "not runtime relevant" in reason:
            return True
    lower = review_text.lower()
    return "not_runtime_relevant" in lower or "not runtime relevant" in lower


def score_candidate(root: Path, candidate: SourceCandidate, events: list[dict[str, Any]]) -> SourceScore:
    source_events = events_for_candidate(events, candidate)
    event_types = {str(event.get("type") or "") for event in source_events}
    present: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []
    score = 0

    queued = "source_file_queued" in event_types
    read = "source_file_read" in event_types
    flow_linked = "source_flow_linked" in event_types
    attack_surface = "attack_surface_mapped" in event_types
    angle_planned = "endpoint_angle_planned" in event_types
    has_gap_event = any(
        event.get("type") in {"gap_found", "mapping_gap_found"}
        or str(event.get("status") or "") == "blocked"
        for event in source_events
    )

    if queued:
        score += 10
        present.append("source_file_queued")
    else:
        missing.append("source_file_queued event missing")

    if read:
        score += 20
        present.append("source_file_read")
        read_events = [event for event in source_events if event.get("type") == "source_file_read"]
        if any(str(event.get("sha256") or "") == candidate.sha256 for event in read_events):
            score += 5
            present.append("source hash matched")
        else:
            missing.append("source_file_read matching sha256 proof missing")
        range_events = [
            event
            for event in read_events
            if int(event.get("line_start") or 0) <= 1 and int(event.get("line_end") or 0) >= candidate.lines
        ]
        chunk_events = {
            int(event.get("chunk_index") or 0)
            for event in read_events
            if int(event.get("chunk_index") or 0) > 0 and int(event.get("chunks_total") or candidate.chunks) == candidate.chunks
        }
        if range_events or len(chunk_events) >= candidate.chunks:
            score += 5
            present.append("line-range or chunk coverage proof")
        else:
            missing.append(f"line-range/chunk proof missing for {candidate.chunks} chunk(s)")
    else:
        missing.append("source_file_read event missing")

    review_path = existing_review_path(root, candidate, source_events)
    review_text = ""
    review_missing: list[str] = []
    review_warnings: list[str] = []
    if review_path:
        review_text = review_path.read_text(encoding="utf-8", errors="ignore")
        score += 20
        present.append("source review artifact exists")
        review_missing, review_warnings = meaningful_review_gaps(review_text, has_gap_event)
        if not review_missing:
            score += 20
            present.append("source review required sections complete")
        else:
            section_points = max(0, 20 - min(20, len(review_missing) * 2))
            score += section_points
            missing.extend(review_missing)
        warnings.extend(review_warnings)
    else:
        missing.append("source-reviews artifact missing or empty")

    runtime_irrelevant = has_runtime_irrelevant_marker(source_events, review_text)
    if runtime_irrelevant:
        if read and review_path and not review_missing:
            score += 30
            present.append("not_runtime_relevant disposition recorded")
        else:
            score += 10
            warnings.append("not_runtime_relevant marker exists but read/review gate is incomplete")
    else:
        if flow_linked:
            score += 15
            present.append("source_flow_linked")
        else:
            missing.append("source_flow_linked event missing")
        if attack_surface:
            score += 10
            present.append("attack_surface_mapped")
        else:
            missing.append("attack_surface_mapped event missing")
        if angle_planned:
            score += 5
            present.append("endpoint_angle_planned")
        else:
            missing.append("endpoint_angle_planned event missing")

    score = min(100, score)
    critical = [
        item
        for item in missing
        if item.startswith("source_file_read")
        or item.startswith("source-reviews")
        or item.startswith("missing required section")
        or "empty/placeheld" in item
        or "unknown without" in item
        or "sha256 proof" in item
        or "chunk proof" in item
    ]
    if score >= 85 and not critical:
        grade = "source_complete"
    elif score >= 50:
        grade = "source_partial"
    else:
        grade = "source_incomplete"

    rel_review = str(review_path.relative_to(root)) if review_path and review_path.is_relative_to(root) else str(review_path or "")
    return SourceScore(
        candidate=candidate,
        score=score,
        grade=grade,
        present=present,
        missing=missing,
        warnings=warnings,
        review_path=rel_review,
        runtime_relevant=not runtime_irrelevant,
    )


def append_queue_row(root: Path, candidate: SourceCandidate) -> None:
    queue = root / "source-file-queue.md"
    if not queue.exists():
        queue.write_text("# Source File Queue\n\n", encoding="utf-8")
    row = (
        f"| 1 | {candidate.file_id} | {candidate.rel_path} | {candidate.language} | queued | "
        f"source-reviews/{candidate.file_id}.md | - | read fully |\n"
    )
    current = queue.read_text(encoding="utf-8")
    if candidate.file_id in current or candidate.rel_path in current:
        return
    marker = "\nAllowed statuses:"
    if marker in current:
        queue.write_text(current.replace(marker, row + marker, 1), encoding="utf-8")
    else:
        with queue.open("a", encoding="utf-8") as f:
            f.write(row)


def queue_missing_events(
    root: Path,
    events_path: Path,
    events: list[dict[str, Any]],
    candidates: list[SourceCandidate],
    actor: str,
) -> tuple[list[dict[str, Any]], int]:
    engagement_id = current_engagement_id(root)
    next_num = len(events) + 1
    added = 0
    updated = list(events)
    for candidate in candidates:
        source_events = events_for_candidate(updated, candidate)
        if any(event.get("type") == "source_file_queued" for event in source_events):
            continue
        event = {
            "id": f"evt-{next_num:06d}",
            "ts": now(),
            "engagement_id": engagement_id,
            "actor": actor,
            "type": "source_file_queued",
            "status": "queued",
            "source_id": candidate.file_id,
            "source_file": candidate.rel_path,
            "language": candidate.language,
            "size": candidate.size,
            "lines": candidate.lines,
            "sha256": candidate.sha256,
            "chunks_total": candidate.chunks,
            "reason": candidate.reason,
            "source": "bbf source-verify --queue-missing",
        }
        write_event(events_path, event)
        append_queue_row(root, candidate)
        updated.append(event)
        next_num += 1
        added += 1
    return updated, added


def write_report(
    root: Path,
    source_root: Path,
    scores: list[SourceScore],
    skipped: list[str],
    include_all: bool,
    queue_events_added: int,
) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    review_dir = root / "source-reviews/_completeness"
    review_dir.mkdir(parents=True, exist_ok=True)
    report_path = review_dir / f"source-completeness-{timestamp}.md"
    total = len(scores)
    complete = sum(1 for item in scores if item.grade == "source_complete")
    partial = sum(1 for item in scores if item.grade == "source_partial")
    incomplete = sum(1 for item in scores if item.grade == "source_incomplete")
    avg = round(sum(item.score for item in scores) / total, 1) if scores else 0
    mode = "all supported source-like files" if include_all else "important files only"

    def short(items: list[str]) -> str:
        if not items:
            return "-"
        return "<br>".join(items[:4])

    rows = "\n".join(
        "| {grade} | {score} | `{file_id}` | `{path}` | {reason} | {missing} | {review} |".format(
            grade=item.grade,
            score=item.score,
            file_id=item.candidate.file_id,
            path=item.candidate.rel_path,
            reason=item.candidate.reason.replace("|", "/"),
            missing=short(item.missing).replace("|", "/"),
            review=f"`{item.review_path}`" if item.review_path else "-",
        )
        for item in sorted(scores, key=lambda s: (s.grade != "source_incomplete", s.score, s.candidate.rel_path))
    )

    details = []
    for item in sorted(scores, key=lambda s: s.candidate.rel_path):
        details.append(
            f"## {item.candidate.rel_path}\n\n"
            f"- File ID: `{item.candidate.file_id}`\n"
            f"- SHA256: `{item.candidate.sha256}`\n"
            f"- Lines: `{item.candidate.lines}`\n"
            f"- Chunks: `{item.candidate.chunks}`\n"
            f"- Grade: `{item.grade}`\n"
            f"- Score: `{item.score}`\n"
            f"- Runtime relevant: `{str(item.runtime_relevant).lower()}`\n"
            f"- Reason included: {item.candidate.reason}\n"
            f"- Review: `{item.review_path or '-'}`\n\n"
            "### Present\n\n"
            + ("\n".join(f"- {entry}" for entry in item.present) if item.present else "- none")
            + "\n\n### Missing\n\n"
            + ("\n".join(f"- {entry}" for entry in item.missing) if item.missing else "- none")
            + "\n\n### Warnings\n\n"
            + ("\n".join(f"- {entry}" for entry in item.warnings) if item.warnings else "- none")
            + "\n"
        )

    report = (
        "# Source Completeness Review\n\n"
        f"- Source root: `{source_root}`\n"
        f"- Mode: `{mode}`\n"
        f"- Files evaluated: `{total}`\n"
        f"- Complete: `{complete}`\n"
        f"- Partial: `{partial}`\n"
        f"- Incomplete: `{incomplete}`\n"
        f"- Average score: `{avg}`\n"
        f"- Queue events added: `{queue_events_added}`\n\n"
        "## File Results\n\n"
        "| Grade | Score | File ID | Path | Why Included | Missing | Review |\n"
        "|---|---:|---|---|---|---|---|\n"
        f"{rows or '| - | - | - | - | No source files matched | - | - |'}\n\n"
        "## Skipped Files\n\n"
        + ("\n".join(f"- {item}" for item in skipped[:200]) if skipped else "- none")
        + "\n\n## Next Actions\n\n"
        "- Read every `source_incomplete` file one by one.\n"
        "- Write `source-reviews/<file-id>.md` using `templates/source/file-review.md`.\n"
        "- Emit `source_file_read`, then `source_flow_linked`, `attack_surface_mapped`, and `endpoint_angle_planned` when runtime-relevant.\n"
        "- If a file is not runtime-relevant, mark it with status `not_runtime_relevant` and still keep the review artifact.\n\n"
        "## Detail\n\n"
        + "\n".join(details)
    )
    report_path.write_text(report, encoding="utf-8")
    (root / "source-completeness.md").write_text(report, encoding="utf-8")
    write_source_inventory(root, source_root, scores)
    return str(report_path.relative_to(root))


def extract_route_sink_hints(path: Path) -> list[dict[str, Any]]:
    patterns = [
        ("route", re.compile(r"(route|router|app)\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]", re.I)),
        ("wp_hook", re.compile(r"add_(action|filter)\s*\(\s*['\"]([^'\"]+)['\"]", re.I)),
        ("rest_route", re.compile(r"register_rest_route\s*\(", re.I)),
        ("sink", re.compile(r"(exec|system|popen|subprocess|eval|pickle|yaml\.load|innerHTML|dangerouslySetInnerHTML|wpdb->query|requests?\.)", re.I)),
    ]
    hints: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return hints
    for index, line in enumerate(lines, 1):
        for kind, regex in patterns:
            match = regex.search(line)
            if not match:
                continue
            hints.append({"kind": kind, "line": index, "text": line.strip()[:220]})
            break
    return hints[:100]


def write_source_inventory(root: Path, source_root: Path, scores: list[SourceScore]) -> None:
    out = root / "data" / "source_inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": "1.0.0",
        "generated_at": now(),
        "source_root": str(source_root),
        "files": [
            {
                "source_id": item.candidate.file_id,
                "path": item.candidate.rel_path,
                "language": item.candidate.language,
                "size": item.candidate.size,
                "lines": item.candidate.lines,
                "sha256": item.candidate.sha256,
                "chunks_total": item.candidate.chunks,
                "grade": item.grade,
                "review_path": item.review_path,
                "route_sink_hints": extract_route_sink_hints(item.candidate.abs_path),
            }
            for item in sorted(scores, key=lambda score: score.candidate.rel_path)
        ],
    }
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_completeness_event(
    root: Path,
    events_path: Path,
    events: list[dict[str, Any]],
    scores: list[SourceScore],
    source_root: Path,
    report_path: str,
    queue_events_added: int,
    actor: str,
) -> dict[str, Any]:
    total = len(scores)
    complete = sum(1 for item in scores if item.grade == "source_complete")
    partial = sum(1 for item in scores if item.grade == "source_partial")
    incomplete = sum(1 for item in scores if item.grade == "source_incomplete")
    avg = round(sum(item.score for item in scores) / total, 1) if scores else 0
    reviews_missing = sum(1 for item in scores if not item.review_path)
    critical_missing = sum(1 for item in scores if item.grade == "source_incomplete")
    status = "source_complete" if total and incomplete == 0 and partial == 0 else "source_partial" if complete or partial else "source_incomplete"
    if total == 0:
        status = "source_incomplete"
    event = {
        "id": f"evt-{len(events) + 1:06d}",
        "ts": now(),
        "engagement_id": current_engagement_id(root),
        "actor": actor,
        "type": "source_completeness_reviewed",
        "status": status,
        "review_id": f"source-completeness-{hashlib.sha1((report_path + now()).encode('utf-8')).hexdigest()[:8]}",
        "source_root": str(source_root),
        "review_path": report_path,
        "score": avg,
        "files_total": total,
        "files_complete": complete,
        "files_partial": partial,
        "files_incomplete": incomplete,
        "reviews_missing": reviews_missing,
        "critical_missing": critical_missing,
        "queue_events_added": queue_events_added,
        "missing_files": [
            item.candidate.rel_path
            for item in scores
            if item.grade == "source_incomplete"
        ][:50],
    }
    write_event(events_path, event)
    return event


def default_source_root(root: Path) -> Path | None:
    for rel in ["source/current", "source", "artifacts/source"]:
        candidate = root / rel
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify that important source files were read one by one and linked into the workflow.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--source-root", type=Path, help="Extracted source root to verify. Defaults to source/current when present.")
    parser.add_argument("--all", action="store_true", help="Verify every supported source-like file, not only high-signal important files.")
    parser.add_argument("--include-ext", action="append", default=[], help="Additional extension to include, e.g. .tpl. Repeatable.")
    parser.add_argument("--ignore-dir", action="append", default=[], help="Additional directory basename to ignore. Repeatable.")
    parser.add_argument("--max-bytes", type=int, default=1_000_000, help="Skip individual files larger than this size.")
    parser.add_argument("--queue-missing", action="store_true", help="Append source_file_queued events and queue rows for unqueued files.")
    parser.add_argument("--no-event", action="store_true", help="Do not append source_completeness_reviewed event.")
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any evaluated file is incomplete or partial.")
    parser.add_argument("--actor", default="ai")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    source_root = args.source_root.resolve() if args.source_root else default_source_root(root)
    if source_root is None:
        raise SystemExit("missing --source-root and no source/current directory exists")
    skip_dirs = set(DEFAULT_SKIP_DIRS)
    skip_dirs.update(args.ignore_dir)
    include_ext = {ext if ext.startswith(".") else f".{ext}" for ext in args.include_ext}

    events_path = root / "data/events.jsonl"
    events = read_events(events_path)
    candidates, skipped = discover_sources(source_root, args.all, skip_dirs, args.max_bytes, include_ext)
    queue_added = 0
    if args.queue_missing:
        events, queue_added = queue_missing_events(root, events_path, events, candidates, args.actor)

    scores = [score_candidate(root, candidate, events) for candidate in candidates]
    report_path = write_report(root, source_root, scores, skipped, args.all, queue_added)
    event: dict[str, Any] | None = None
    if not args.no_event:
        event = write_completeness_event(root, events_path, events, scores, source_root, report_path, queue_added, args.actor)

    if not args.no_build:
        build_graph(root)

    total = len(scores)
    complete = sum(1 for item in scores if item.grade == "source_complete")
    partial = sum(1 for item in scores if item.grade == "source_partial")
    incomplete = sum(1 for item in scores if item.grade == "source_incomplete")
    avg = round(sum(item.score for item in scores) / total, 1) if scores else 0
    status = event.get("status") if event else ("source_complete" if total and incomplete == 0 and partial == 0 else "source_partial" if complete or partial else "source_incomplete")
    print(f"source completeness: {status} avg={avg}/100 complete={complete} partial={partial} incomplete={incomplete} total={total}")
    print(f"report: {report_path}")
    if queue_added:
        print(f"queued missing files: {queue_added}")
    for item in scores:
        if item.grade == "source_incomplete":
            print(f"- incomplete: {item.candidate.rel_path} ({'; '.join(item.missing[:3])})")
    if args.strict and (partial or incomplete or total == 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
