#!/usr/bin/env python3
"""Knowledge base CLI for rsasaki-hub.

Ingest raw sources (URLs, local files), compile them into a wiki of .md files,
search, and lint the knowledge base. All without external dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import textwrap
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
WIKI_DIR = ROOT / "wiki"
CONCEPTS_DIR = WIKI_DIR / "concepts"
INDEX_PATH = WIKI_DIR / "index.md"

# Robotics domain taxonomy for auto-categorization
CONCEPT_KEYWORDS: dict[str, list[str]] = {
    "localization": ["localization", "localizer", "amcl", "particle filter", "monte carlo",
                     "pose estimation", "position estimation", "self-localization"],
    "slam": ["slam", "simultaneous localization", "mapping", "loop closure", "pose graph",
             "graph optimization", "scan matching", "submap"],
    "lidar": ["lidar", "pointcloud", "point cloud", "velodyne", "ouster", "livox",
              "range sensor", "laser scan", "3d scan"],
    "imu": ["imu", "inertial", "accelerometer", "gyroscope", "preintegration",
            "inertial measurement", "attitude estimation"],
    "gnss": ["gnss", "gps", "rtk", "ppp", "satellite", "positioning", "navsat",
             "rinex", "rtcm", "qzss"],
    "path_planning": ["path planning", "motion planning", "rrt", "a*", "dijkstra",
                       "dwa", "trajectory", "navigation", "obstacle avoidance"],
    "state_estimation": ["kalman", "ekf", "ukf", "bayesian", "filtering",
                          "state estimation", "sensor fusion", "covariance"],
    "point_cloud_processing": ["voxel", "downsampling", "segmentation", "clustering",
                                "ground removal", "registration", "icp", "ndt", "gicp"],
    "ros": ["ros", "ros2", "ament", "colcon", "launch", "node", "topic", "service",
            "action", "rclcpp", "rclpy"],
    "deep_learning": ["neural", "deep learning", "cnn", "transformer", "inference",
                       "training", "model", "pytorch", "tensorflow"],
    "computer_vision": ["camera", "image", "visual", "feature", "descriptor",
                         "stereo", "depth", "optical flow", "visual odometry"],
    "control": ["control", "pid", "mpc", "lqr", "feedback", "controller",
                "actuator", "servo", "motor"],
    "simulation": ["simulation", "simulator", "gazebo", "isaac", "virtual",
                    "synthetic", "digital twin"],
    "datasets": ["dataset", "benchmark", "evaluation", "ground truth", "sequence",
                  "kitti", "nuscenes", "waymo"],
    "bim_construction": ["bim", "ifc", "construction", "building", "architecture",
                          "renovation", "rohbau", "as-built"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:80].strip("-")


def extract_title_from_html(html_text: str) -> str:
    """Extract <title> from HTML."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if match:
        return html.unescape(match.group(1)).strip()
    return ""


def html_to_markdown(html_text: str) -> str:
    """Minimal HTML to Markdown conversion. Good enough for articles."""
    text = html_text
    # Remove script, style, nav, header, footer
    for tag in ("script", "style", "nav", "header", "footer", "aside"):
        text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Headers
    for level in range(1, 7):
        text = re.sub(rf"<h{level}[^>]*>(.*?)</h{level}>", rf"\n{'#' * level} \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    # Paragraphs and divs
    text = re.sub(r"<(?:p|div)[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(?:p|div)>", "\n", text, flags=re.IGNORECASE)
    # Line breaks
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Bold and italic
    text = re.sub(r"<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<(?:em|i)[^>]*>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    # Links
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.IGNORECASE | re.DOTALL)
    # Code
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<pre[^>]*>(.*?)</pre>", r"\n```\n\1\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
    # Lists
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", text, flags=re.IGNORECASE | re.DOTALL)
    # Images
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?>',  r"![\2](\1)", text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?>',  r"![](\1)", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def classify_content(text: str) -> list[str]:
    """Return matching concept tags for text."""
    lowered = text.lower()
    matched: list[tuple[str, int]] = []
    for concept, keywords in CONCEPT_KEYWORDS.items():
        score = sum(lowered.count(kw) for kw in keywords)
        if score >= 2:
            matched.append((concept, score))
    matched.sort(key=lambda x: x[1], reverse=True)
    return [concept for concept, _ in matched[:5]]


def read_frontmatter(path: Path) -> dict[str, Any]:
    """Read YAML-like frontmatter from a .md file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end < 0:
        return {}
    fm: dict[str, Any] = {}
    for line in text[3:end].strip().splitlines():
        if ": " in line:
            key, val = line.split(": ", 1)
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                fm[key] = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
            else:
                fm[key] = val.strip('"').strip("'")
    return fm


def body_text(path: Path) -> str:
    """Return markdown body (after frontmatter)."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end >= 0:
            return text[end + 3:].strip()
    return text.strip()


def word_count(text: str) -> int:
    return len(text.split())


# ---- ingest command ----

def ingest_url(url: str) -> Path:
    """Fetch a URL and save as .md in raw/."""
    print(f"Fetching {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 rsasaki-hub-kb/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw_html = resp.read().decode("utf-8", errors="ignore")

    title = extract_title_from_html(raw_html) or url.split("/")[-1]
    md_body = html_to_markdown(raw_html)
    concepts = classify_content(md_body)
    slug = slugify(title)
    if not slug:
        slug = hashlib.md5(url.encode()).hexdigest()[:12]

    dest = RAW_DIR / f"{slug}.md"
    counter = 1
    while dest.exists():
        dest = RAW_DIR / f"{slug}-{counter}.md"
        counter += 1

    frontmatter = textwrap.dedent(f"""\
    ---
    title: "{title}"
    source: "{url}"
    ingested_at: "{utc_now()}"
    concepts: [{', '.join(f'"{c}"' for c in concepts)}]
    type: "web_article"
    ---
    """)

    dest.write_text(frontmatter + md_body, encoding="utf-8")
    print(f"  -> {dest.relative_to(ROOT)} ({word_count(md_body)} words, concepts: {concepts})")
    return dest


def ingest_file(file_path: Path) -> Path:
    """Copy a local file into raw/ with frontmatter."""
    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    # If it already has frontmatter, just copy
    if text.startswith("---"):
        dest = RAW_DIR / file_path.name
        dest.write_text(text, encoding="utf-8")
    else:
        title = file_path.stem.replace("-", " ").replace("_", " ").title()
        concepts = classify_content(text)
        frontmatter = textwrap.dedent(f"""\
        ---
        title: "{title}"
        source: "local:{file_path}"
        ingested_at: "{utc_now()}"
        concepts: [{', '.join(f'"{c}"' for c in concepts)}]
        type: "local_file"
        ---
        """)
        dest = RAW_DIR / file_path.name
        if not dest.suffix:
            dest = dest.with_suffix(".md")
        dest.write_text(frontmatter + text, encoding="utf-8")

    print(f"  -> {dest.relative_to(ROOT)}")
    return dest


def ingest_repo_data() -> list[Path]:
    """Ingest data from this repo's own experiments as raw sources."""
    created: list[Path] = []
    exp_path = ROOT / "registry" / "experiments.yaml"
    if not exp_path.exists():
        return created

    data = json.loads(exp_path.read_text(encoding="utf-8"))
    for experiment in data.get("experiments", []):
        name = experiment["name"]
        slug = slugify(name)
        dest = RAW_DIR / f"experiment-{slug}.md"

        lines = [
            "---",
            f'title: "Experiment: {name}"',
            f'source: "registry/experiments.yaml"',
            f'ingested_at: "{utc_now()}"',
            f'concepts: ["slam", "localization", "lidar", "ros"]',
            f'type: "experiment_data"',
            "---",
            "",
            f"# {name}",
            "",
            experiment.get("problem_statement", ""),
            "",
        ]

        for impl in experiment.get("implementations", []):
            score = impl.get("evaluation", {}).get("overall_score", "?")
            algos = ", ".join(impl.get("algorithms", [])[:4])
            lines.append(f"## {impl['repo']} (track: {impl['track']}, score: {score})")
            lines.append("")
            lines.append(f"- Description: {impl.get('description', 'N/A')}")
            lines.append(f"- Language: {impl.get('language', '?')}")
            lines.append(f"- Algorithms: {algos}")
            inputs = ", ".join(impl.get("io", {}).get("inputs", []))
            outputs = ", ".join(impl.get("io", {}).get("outputs", []))
            lines.append(f"- I/O: {inputs} -> {outputs}")
            lines.append("")

        dest.write_text("\n".join(lines), encoding="utf-8")
        created.append(dest)
        print(f"  -> {dest.relative_to(ROOT)}")

    return created


def ingest_command(args: argparse.Namespace) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sources = args.sources

    if not sources:
        # Default: ingest from repo's own experiment data
        print("No sources specified. Ingesting from registry/experiments.yaml ...")
        created = ingest_repo_data()
        print(f"Ingested {len(created)} experiment files")
        return

    for source in sources:
        if source.startswith("http://") or source.startswith("https://"):
            ingest_url(source)
        else:
            ingest_file(Path(source))


# ---- compile command ----

def compile_command(_args: argparse.Namespace) -> None:
    """Compile raw/ into wiki/. Generates index.md and concept pages."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(RAW_DIR.glob("*.md"))
    if not raw_files:
        print("No raw files found. Run 'kb ingest' first.")
        return

    # Collect all articles with metadata
    articles: list[dict[str, Any]] = []
    concept_articles: dict[str, list[dict[str, Any]]] = {}

    for path in raw_files:
        fm = read_frontmatter(path)
        body = body_text(path)
        title = fm.get("title", path.stem)
        concepts = fm.get("concepts", [])
        if isinstance(concepts, str):
            concepts = [concepts]
        # Re-classify if no concepts
        if not concepts:
            concepts = classify_content(body)

        # Generate summary (first 2 non-empty lines after headers)
        summary_lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                summary_lines.append(stripped)
                if len(summary_lines) >= 2:
                    break
        summary = " ".join(summary_lines)[:200]

        article = {
            "path": path,
            "title": title,
            "source": fm.get("source", ""),
            "type": fm.get("type", "unknown"),
            "concepts": concepts,
            "summary": summary,
            "word_count": word_count(body),
            "ingested_at": fm.get("ingested_at", ""),
        }
        articles.append(article)

        for concept in concepts:
            concept_articles.setdefault(concept, []).append(article)

    # Generate index.md
    index_lines = [
        "# Knowledge Base Index",
        "",
        f"Generated at: {utc_now()}",
        "",
        f"Total articles: {len(articles)}",
        f"Total words: {sum(a['word_count'] for a in articles):,}",
        f"Concepts: {len(concept_articles)}",
        "",
        "## Concepts",
        "",
    ]
    for concept in sorted(concept_articles.keys()):
        count = len(concept_articles[concept])
        index_lines.append(f"- [{concept}](concepts/{concept}.md) ({count} articles)")
    index_lines.extend(["", "## All Articles", ""])

    for article in sorted(articles, key=lambda a: a["title"]):
        tags = " ".join(f"`{c}`" for c in article["concepts"])
        wc = article["word_count"]
        rel_path = article["path"].relative_to(ROOT)
        index_lines.append(f"- **{article['title']}** — {wc} words — {tags}")
        index_lines.append(f"  - Source: {article['source']}")
        index_lines.append(f"  - Raw: [{rel_path}](../{rel_path})")

    INDEX_PATH.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Generated {INDEX_PATH.relative_to(ROOT)}")

    # Generate concept pages
    for concept, arts in concept_articles.items():
        concept_path = CONCEPTS_DIR / f"{concept}.md"
        lines = [
            f"# {concept.replace('_', ' ').title()}",
            "",
            f"Articles: {len(arts)}",
            "",
        ]
        # Find related concepts (concepts that share articles)
        related: Counter[str] = Counter()
        for art in arts:
            for c in art["concepts"]:
                if c != concept:
                    related[c] += 1
        if related:
            related_links = ", ".join(f"[{c}]({c}.md)" for c, _ in related.most_common(5))
            lines.append(f"Related: {related_links}")
            lines.append("")

        lines.append("## Articles")
        lines.append("")
        for art in sorted(arts, key=lambda a: a["word_count"], reverse=True):
            lines.append(f"### {art['title']}")
            lines.append("")
            lines.append(f"{art['summary']}")
            lines.append("")
            rel_path = art["path"].relative_to(ROOT)
            lines.append(f"- Source: {art['source']}")
            lines.append(f"- Words: {art['word_count']}")
            lines.append(f"- Raw: [{rel_path}](../../{rel_path})")
            lines.append("")

        concept_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Generated {len(concept_articles)} concept pages in wiki/concepts/")
    print(f"Compiled {len(articles)} articles into wiki/")


# ---- search command ----

def search_command(args: argparse.Namespace) -> None:
    """Search wiki and raw files for a query."""
    query = " ".join(args.query).lower()
    if not query:
        print("Usage: kb search <query>")
        return

    results: list[tuple[Path, int, list[str]]] = []

    search_dirs = [WIKI_DIR, RAW_DIR]
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in search_dir.rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            matched_lines: list[str] = []
            for i, line in enumerate(lines):
                if query in line.lower():
                    # Show context
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    context = "\n".join(f"  {lines[j]}" for j in range(start, end))
                    matched_lines.append(f"  L{i + 1}:\n{context}")
            if matched_lines:
                results.append((path, len(matched_lines), matched_lines))

    if not results:
        print(f'No results for "{query}"')
        return

    results.sort(key=lambda x: x[1], reverse=True)
    print(f'Found {sum(r[1] for r in results)} matches in {len(results)} files for "{query}":\n')

    for path, count, matches in results[:10]:
        rel = path.relative_to(ROOT)
        print(f"--- {rel} ({count} matches) ---")
        for match in matches[:3]:
            print(match)
        if len(matches) > 3:
            print(f"  ... and {len(matches) - 3} more matches")
        print()


# ---- lint command ----

def lint_command(_args: argparse.Namespace) -> None:
    """Check knowledge base health."""
    issues: list[str] = []
    suggestions: list[str] = []

    # Check raw/ files
    raw_files = list(RAW_DIR.glob("*.md")) if RAW_DIR.exists() else []
    wiki_files = list(WIKI_DIR.rglob("*.md")) if WIKI_DIR.exists() else []

    print(f"Raw files: {len(raw_files)}")
    print(f"Wiki files: {len(wiki_files)}")
    print()

    if not raw_files:
        issues.append("No raw files found. Run 'kb ingest' to add sources.")

    if raw_files and not wiki_files:
        issues.append("Raw files exist but wiki is empty. Run 'kb compile' to generate wiki.")

    # Check frontmatter
    missing_frontmatter = 0
    missing_concepts = 0
    all_concepts: Counter[str] = Counter()
    all_sources: set[str] = set()

    for path in raw_files:
        fm = read_frontmatter(path)
        if not fm:
            missing_frontmatter += 1
            issues.append(f"Missing frontmatter: {path.relative_to(ROOT)}")
        elif not fm.get("concepts"):
            missing_concepts += 1
            issues.append(f"Missing concepts: {path.relative_to(ROOT)}")
        else:
            concepts = fm["concepts"]
            if isinstance(concepts, str):
                concepts = [concepts]
            for c in concepts:
                all_concepts[c] += 1
        source = fm.get("source", "")
        if source:
            all_sources.add(source)

    # Check for broken internal links in wiki
    broken_links = 0
    for path in wiki_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            link_target = match.group(2)
            if link_target.startswith("http"):
                continue
            resolved = (path.parent / link_target).resolve()
            if not resolved.exists():
                broken_links += 1
                issues.append(f"Broken link: {path.relative_to(ROOT)} -> {link_target}")

    # Check concept coverage
    uncovered = [name for name in CONCEPT_KEYWORDS if name not in all_concepts]
    if uncovered:
        suggestions.append(f"Uncovered concepts (consider adding sources): {', '.join(uncovered[:8])}")

    # Check for small articles
    for path in raw_files:
        body = body_text(path)
        if word_count(body) < 50:
            suggestions.append(f"Very short article ({word_count(body)} words): {path.relative_to(ROOT)}")

    # Check index freshness
    if INDEX_PATH.exists():
        raw_newest = max((f.stat().st_mtime for f in raw_files), default=0)
        index_mtime = INDEX_PATH.stat().st_mtime
        if raw_newest > index_mtime:
            issues.append("Index is stale. Run 'kb compile' to update.")

    # Report
    if issues:
        print(f"Issues ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        print()

    if suggestions:
        print(f"Suggestions ({len(suggestions)}):")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
        print()

    if all_concepts:
        print("Concept coverage:")
        for concept, count in all_concepts.most_common():
            bar = "#" * min(count, 20)
            print(f"  {concept:25s} {bar} ({count})")
        print()

    if not issues and not suggestions:
        print("All clean!")


# ---- stats command ----

def stats_command(_args: argparse.Namespace) -> None:
    """Show knowledge base statistics."""
    raw_files = list(RAW_DIR.glob("*.md")) if RAW_DIR.exists() else []
    wiki_files = list(WIKI_DIR.rglob("*.md")) if WIKI_DIR.exists() else []

    total_raw_words = 0
    total_wiki_words = 0
    concepts: Counter[str] = Counter()
    types: Counter[str] = Counter()

    for path in raw_files:
        total_raw_words += word_count(body_text(path))
        fm = read_frontmatter(path)
        fmc = fm.get("concepts", [])
        if isinstance(fmc, str):
            fmc = [fmc]
        for c in fmc:
            concepts[c] += 1
        types[fm.get("type", "unknown")] += 1

    for path in wiki_files:
        total_wiki_words += word_count(path.read_text(encoding="utf-8", errors="ignore"))

    print(f"Raw articles:  {len(raw_files)}")
    print(f"Raw words:     {total_raw_words:,}")
    print(f"Wiki files:    {len(wiki_files)}")
    print(f"Wiki words:    {total_wiki_words:,}")
    print(f"Concepts:      {len(concepts)}")
    print()
    if types:
        print("Source types:")
        for t, count in types.most_common():
            print(f"  {t}: {count}")
    print()
    if concepts:
        print("Top concepts:")
        for c, count in concepts.most_common(10):
            print(f"  {c}: {count}")


# ---- parser ----

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Knowledge base CLI for rsasaki-hub",
        prog="kb",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_p = subparsers.add_parser("ingest", help="Ingest sources into raw/")
    ingest_p.add_argument("sources", nargs="*", help="URLs or local file paths. Empty = ingest from experiments.yaml")
    ingest_p.set_defaults(func=ingest_command)

    compile_p = subparsers.add_parser("compile", help="Compile raw/ into wiki/")
    compile_p.set_defaults(func=compile_command)

    search_p = subparsers.add_parser("search", help="Search the knowledge base")
    search_p.add_argument("query", nargs="+", help="Search terms")
    search_p.set_defaults(func=search_command)

    lint_p = subparsers.add_parser("lint", help="Check knowledge base health")
    lint_p.set_defaults(func=lint_command)

    stats_p = subparsers.add_parser("stats", help="Show knowledge base statistics")
    stats_p.set_defaults(func=stats_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
