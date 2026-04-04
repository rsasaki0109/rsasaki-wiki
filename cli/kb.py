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
import os
import re
import sys
import textwrap
import urllib.parse
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


def ingest_repo_readmes() -> list[Path]:
    """Ingest README.md files from all cached repos."""
    cache_dir = ROOT / ".cache" / "repos"
    if not cache_dir.exists():
        print("No cached repos found. Run 'expctl.py sync' first.")
        return []

    created: list[Path] = []
    for repo_dir in sorted(cache_dir.iterdir()):
        if not repo_dir.is_dir():
            continue
        readme = repo_dir / "README.md"
        if not readme.exists():
            # Try lowercase
            readme = repo_dir / "readme.md"
        if not readme.exists():
            continue

        text = readme.read_text(encoding="utf-8", errors="ignore")
        if len(text.strip()) < 50:
            continue

        repo_name = repo_dir.name
        concepts = classify_content(text)
        slug = slugify(repo_name)
        dest = RAW_DIR / f"repo-{slug}.md"

        frontmatter = textwrap.dedent(f"""\
        ---
        title: "Repo: {repo_name}"
        source: "https://github.com/rsasaki0109/{repo_name}"
        ingested_at: "{utc_now()}"
        concepts: [{', '.join(f'"{c}"' for c in concepts)}]
        type: "repo_readme"
        ---
        """)

        dest.write_text(frontmatter + text, encoding="utf-8")
        created.append(dest)
        print(f"  -> {dest.relative_to(ROOT)} ({word_count(text)} words, {concepts[:3]})")

    return created


def ingest_arxiv(query: str, max_results: int = 10) -> list[Path]:
    """Ingest papers from arXiv API."""
    import xml.etree.ElementTree as ET

    encoded_query = urllib.parse.quote(query)
    url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=relevance"
    print(f"Querying arXiv for '{query}' (max {max_results}) ...")

    req = urllib.request.Request(url, headers={"User-Agent": "rsasaki-hub-kb/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml_text = resp.read().decode("utf-8")

    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    created: list[Path] = []
    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        id_el = entry.find("atom:id", ns)
        published_el = entry.find("atom:published", ns)

        if title_el is None or summary_el is None or id_el is None:
            continue

        title = " ".join(title_el.text.strip().split())
        abstract = " ".join(summary_el.text.strip().split())
        arxiv_url = id_el.text.strip()
        arxiv_id = arxiv_url.split("/abs/")[-1]
        published = published_el.text.strip()[:10] if published_el is not None else ""

        authors = []
        for author in entry.findall("atom:author", ns):
            name_el = author.find("atom:name", ns)
            if name_el is not None:
                authors.append(name_el.text.strip())

        categories = []
        for cat in entry.findall("atom:category", ns):
            term = cat.get("term", "")
            if term:
                categories.append(term)

        full_text = f"{title}\n{abstract}"
        concepts = classify_content(full_text)
        slug = slugify(f"arxiv-{arxiv_id}")
        dest = RAW_DIR / f"{slug}.md"

        body_lines = [
            f"# {title}",
            "",
            f"**arXiv:** [{arxiv_id}]({arxiv_url})",
            f"**Published:** {published}",
            f"**Authors:** {', '.join(authors[:5])}{'...' if len(authors) > 5 else ''}",
            f"**Categories:** {', '.join(categories)}",
            "",
            "## Abstract",
            "",
            abstract,
            "",
        ]

        frontmatter = textwrap.dedent(f"""\
        ---
        title: "{title.replace('"', "'")}"
        source: "{arxiv_url}"
        ingested_at: "{utc_now()}"
        concepts: [{', '.join(f'"{c}"' for c in concepts)}]
        type: "arxiv_paper"
        arxiv_id: "{arxiv_id}"
        published: "{published}"
        ---
        """)

        dest.write_text(frontmatter + "\n".join(body_lines), encoding="utf-8")
        created.append(dest)
        print(f"  -> {dest.relative_to(ROOT)} [{arxiv_id}] {title[:60]}...")

    return created


def ingest_command(args: argparse.Namespace) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sources = args.sources
    mode = getattr(args, "mode", None)

    if mode == "repos":
        created = ingest_repo_readmes()
        print(f"Ingested {len(created)} repo READMEs")
        return

    if mode == "arxiv":
        query = " ".join(sources) if sources else "robotics SLAM localization LiDAR"
        max_results = getattr(args, "max_results", 10)
        created = ingest_arxiv(query, max_results)
        print(f"Ingested {len(created)} arXiv papers")
        return

    if not sources:
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

    # Build concept graph (which concepts co-occur)
    concept_graph: dict[str, Counter[str]] = {}
    for art in articles:
        for c in art["concepts"]:
            concept_graph.setdefault(c, Counter())
            for c2 in art["concepts"]:
                if c2 != c:
                    concept_graph[c][c2] += 1

    # Group articles by type
    by_type: dict[str, list[dict[str, Any]]] = {}
    for art in articles:
        by_type.setdefault(art["type"], []).append(art)

    # Generate index.md (Obsidian compatible)
    index_lines = [
        "# Knowledge Base Index",
        "",
        f"Generated at: {utc_now()}",
        "",
        f"Total articles: {len(articles)}  ",
        f"Total words: {sum(a['word_count'] for a in articles):,}  ",
        f"Concepts: {len(concept_articles)}  ",
        f"Sources: {', '.join(f'{t} ({len(arts)})' for t, arts in sorted(by_type.items()))}",
        "",
        "## Concept Map",
        "",
    ]
    for concept in sorted(concept_articles.keys()):
        count = len(concept_articles[concept])
        related = concept_graph.get(concept, Counter())
        top_related = ", ".join(f"[[{c}]]" for c, _ in related.most_common(3))
        index_lines.append(f"- [[{concept}]] ({count} articles) — related: {top_related}")
    index_lines.extend(["", "## By Type", ""])
    for article_type in sorted(by_type.keys()):
        type_arts = by_type[article_type]
        index_lines.append(f"### {article_type} ({len(type_arts)})")
        index_lines.append("")
        for art in sorted(type_arts, key=lambda a: a["word_count"], reverse=True):
            tags = " ".join(f"[[{c}]]" for c in art["concepts"])
            index_lines.append(f"- **{art['title']}** — {art['word_count']} words — {tags}")
        index_lines.append("")

    INDEX_PATH.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Generated {INDEX_PATH.relative_to(ROOT)}")

    # Generate concept pages (Obsidian compatible with backlinks)
    for concept, arts in concept_articles.items():
        concept_path = CONCEPTS_DIR / f"{concept}.md"
        pretty_name = concept.replace("_", " ").title()
        related = concept_graph.get(concept, Counter())

        lines = [
            f"# {pretty_name}",
            "",
            f"Articles: {len(arts)}  ",
            f"Total words: {sum(a['word_count'] for a in arts):,}",
            "",
        ]

        # Related concepts with backlinks
        if related:
            lines.append("## Related Concepts")
            lines.append("")
            for rel_concept, overlap_count in related.most_common(8):
                rel_pretty = rel_concept.replace("_", " ").title()
                lines.append(f"- [[{rel_concept}|{rel_pretty}]] ({overlap_count} shared articles)")
            lines.append("")

        # Key repos in this concept
        repo_arts = [a for a in arts if a["type"] == "repo_readme"]
        if repo_arts:
            lines.append("## Repositories")
            lines.append("")
            for art in sorted(repo_arts, key=lambda a: a["word_count"], reverse=True)[:10]:
                source = art["source"]
                lines.append(f"- [{art['title']}]({source}) — {art['word_count']} words")
            lines.append("")

        # arXiv papers in this concept
        paper_arts = [a for a in arts if a["type"] == "arxiv_paper"]
        if paper_arts:
            lines.append("## Papers")
            lines.append("")
            for art in sorted(paper_arts, key=lambda a: a.get("ingested_at", ""), reverse=True)[:10]:
                source = art["source"]
                lines.append(f"- [{art['title']}]({source}) — {art['summary'][:100]}...")
            lines.append("")

        # Other articles
        other_arts = [a for a in arts if a["type"] not in ("repo_readme", "arxiv_paper")]
        if other_arts:
            lines.append("## Other Sources")
            lines.append("")
            for art in sorted(other_arts, key=lambda a: a["word_count"], reverse=True):
                lines.append(f"- [{art['title']}]({art['source']}) — {art['word_count']} words")
            lines.append("")

        # Backlinks section (which other concept pages link here)
        backlink_concepts = [c for c, _ in related.most_common()]
        if backlink_concepts:
            lines.append("## Backlinks")
            lines.append("")
            for bl in backlink_concepts[:10]:
                lines.append(f"- [[{bl}]]")
            lines.append("")

        concept_path.write_text("\n".join(lines), encoding="utf-8")

    # Generate graph visualization data (for Obsidian Graph or manual inspection)
    graph_path = WIKI_DIR / "graph.md"
    graph_lines = [
        "# Concept Graph",
        "",
        "Nodes = concepts, edges = shared articles between concepts.",
        "",
        "```",
    ]
    for concept in sorted(concept_graph.keys()):
        related = concept_graph[concept]
        for target, weight in related.most_common(5):
            if concept < target:  # avoid duplicates
                graph_lines.append(f"{concept} --({weight})--> {target}")
    graph_lines.extend(["```", ""])
    graph_path.write_text("\n".join(graph_lines), encoding="utf-8")

    print(f"Generated {len(concept_articles)} concept pages in wiki/concepts/")
    print(f"Generated concept graph in wiki/graph.md")
    print(f"Compiled {len(articles)} articles into wiki/")

    # LLM-powered article generation
    if getattr(_args, "llm", False):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not set. Skipping LLM compilation.")
            return
        llm_compile(articles, concept_articles, concept_graph, api_key)


def call_claude(prompt: str, system: str, api_key: str, max_tokens: int = 2000) -> str:
    """Call Claude API directly via urllib (no SDK dependency)."""
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    for block in result.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    return ""


def llm_compile(
    articles: list[dict[str, Any]],
    concept_articles: dict[str, list[dict[str, Any]]],
    concept_graph: dict[str, Counter[str]],
    api_key: str,
) -> None:
    """Generate LLM-written wiki articles for each concept."""
    llm_dir = WIKI_DIR / "articles"
    llm_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = textwrap.dedent("""\
    You are a robotics research knowledge base compiler. You write concise, technical wiki articles in Japanese.
    Each article should:
    - Start with a one-paragraph overview of the concept
    - Cover key algorithms, methods, and their trade-offs
    - Reference specific repositories and papers from the provided data
    - Use Obsidian-compatible [[backlinks]] to link to related concepts
    - Be 300-600 words, information-dense, no filler
    - Use markdown headers (##) to organize sections
    Output only the markdown article body (no frontmatter).
    """)

    generated = 0
    for concept, arts in sorted(concept_articles.items(), key=lambda x: len(x[1]), reverse=True):
        if len(arts) < 2:
            continue

        dest = llm_dir / f"{concept}.md"
        pretty_name = concept.replace("_", " ").title()
        related = concept_graph.get(concept, Counter())
        related_names = [c for c, _ in related.most_common(5)]

        # Build context from articles
        context_parts: list[str] = []
        for art in arts[:15]:
            context_parts.append(f"- {art['title']} ({art['type']}, {art['word_count']} words): {art['summary'][:150]}")

        prompt = textwrap.dedent(f"""\
        Write a wiki article about "{pretty_name}" in the context of robotics.

        Related concepts: {', '.join(related_names)}

        Articles in this concept:
        {chr(10).join(context_parts)}

        Requirements:
        - Write in Japanese
        - Link related concepts with [[{related_names[0] if related_names else 'slam'}]] syntax
        - Mention specific repos and papers by name
        - Be concise and technical
        """)

        print(f"  LLM generating: {concept} ({len(arts)} articles) ...", end=" ", flush=True)
        try:
            article_text = call_claude(prompt, system_prompt, api_key)
            frontmatter = textwrap.dedent(f"""\
            ---
            title: "{pretty_name}"
            type: "llm_article"
            concept: "{concept}"
            generated_at: "{utc_now()}"
            source_count: {len(arts)}
            ---
            """)
            dest.write_text(frontmatter + article_text + "\n", encoding="utf-8")
            generated += 1
            print(f"done ({word_count(article_text)} words)")
        except Exception as e:
            print(f"failed: {e}")

    print(f"LLM generated {generated} concept articles in wiki/articles/")


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


# ---- ask command ----

def ask_command(args: argparse.Namespace) -> None:
    """Answer a question using the knowledge base.

    Finds relevant articles, extracts key passages, and presents
    a structured answer with sources. Works without an LLM API
    by doing keyword-based retrieval and excerpt assembly.
    """
    question = " ".join(args.question)
    if not question:
        print("Usage: kb ask <question>")
        return

    # Tokenize question into search terms
    stop_words = {"の", "は", "が", "を", "に", "で", "と", "から", "まで", "より",
                  "what", "is", "are", "how", "does", "do", "the", "a", "an", "in",
                  "of", "for", "to", "and", "or", "which", "between", "vs", "about"}
    terms = [t.lower() for t in re.split(r"[\s,?!。、？]+", question) if t.lower() not in stop_words and len(t) > 1]

    if not terms:
        print("Could not extract search terms from question.")
        return

    # Score all files by relevance
    search_dirs = [WIKI_DIR / "articles", CONCEPTS_DIR, RAW_DIR]
    scored: list[tuple[Path, float, list[str]]] = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in search_dir.rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            fm = read_frontmatter(path)
            title = fm.get("title", path.stem).lower()

            score = 0.0
            matched_terms: list[str] = []
            for term in terms:
                count = text.count(term)
                if count > 0:
                    matched_terms.append(term)
                    score += min(count, 20)
                    # Boost for title match
                    if term in title:
                        score += 10

            # Boost wiki articles over raw
            if "articles" in path.parts:
                score *= 1.5
            elif "concepts" in path.parts:
                score *= 1.2

            if score > 0:
                scored.append((path, score, matched_terms))

    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        print(f"No relevant articles found for: {question}")
        return

    # Present top results with excerpts
    print(f"Question: {question}")
    print(f"Search terms: {', '.join(terms)}")
    print(f"Found {len(scored)} relevant files\n")
    print("=" * 60)

    for path, score, matched in scored[:5]:
        fm = read_frontmatter(path)
        title = fm.get("title", path.stem)
        rel_path = path.relative_to(ROOT)
        article_type = fm.get("type", "unknown")
        source = fm.get("source", "")

        print(f"\n## {title}")
        print(f"   File: {rel_path} ({article_type}, relevance: {score:.0f})")
        if source:
            print(f"   Source: {source}")

        # Extract relevant excerpts
        body = body_text(path)
        lines = body.splitlines()
        excerpts: list[str] = []
        for i, line in enumerate(lines):
            lowered = line.lower()
            if any(term in lowered for term in terms):
                # Get surrounding context
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                excerpt = "\n".join(lines[start:end]).strip()
                if excerpt and excerpt not in excerpts:
                    excerpts.append(excerpt)
                if len(excerpts) >= 3:
                    break

        if excerpts:
            print()
            for excerpt in excerpts:
                # Truncate long excerpts
                if len(excerpt) > 300:
                    excerpt = excerpt[:300] + "..."
                print(f"   > {excerpt}")
            print()

    print("=" * 60)
    print(f"\nTo dive deeper, read the full articles or run: kb search {terms[0]}")


# ---- parser ----

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Knowledge base CLI for rsasaki-hub",
        prog="kb",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_p = subparsers.add_parser("ingest", help="Ingest sources into raw/")
    ingest_p.add_argument("sources", nargs="*", help="URLs or local file paths. Empty = ingest from experiments.yaml")
    ingest_mode = ingest_p.add_mutually_exclusive_group()
    ingest_mode.add_argument("--repos", dest="mode", action="store_const", const="repos", help="Ingest README.md from all cached repos")
    ingest_mode.add_argument("--arxiv", dest="mode", action="store_const", const="arxiv", help="Ingest papers from arXiv (sources = search query)")
    ingest_p.add_argument("--max-results", type=int, default=10, help="Max arXiv results (default: 10)")
    ingest_p.set_defaults(func=ingest_command)

    compile_p = subparsers.add_parser("compile", help="Compile raw/ into wiki/")
    compile_p.add_argument("--llm", action="store_true", help="Also generate LLM-written concept articles (requires ANTHROPIC_API_KEY)")
    compile_p.set_defaults(func=compile_command)

    search_p = subparsers.add_parser("search", help="Search the knowledge base")
    search_p.add_argument("query", nargs="+", help="Search terms")
    search_p.set_defaults(func=search_command)

    lint_p = subparsers.add_parser("lint", help="Check knowledge base health")
    lint_p.set_defaults(func=lint_command)

    stats_p = subparsers.add_parser("stats", help="Show knowledge base statistics")
    stats_p.set_defaults(func=stats_command)

    ask_p = subparsers.add_parser("ask", help="Ask a question against the knowledge base")
    ask_p.add_argument("question", nargs="+", help="Your question")
    ask_p.set_defaults(func=ask_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
