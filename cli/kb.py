#!/usr/bin/env python3
"""rsasaki-hub 用ナレッジベース CLI。

生ソース（URL、ローカルファイル）を取り込み、.md ベースの wiki にコンパイルし、
検索と lint を行う。外部依存は不要。
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

# 自動分類に使うロボティクス領域タクソノミ
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

CONCEPT_LABELS: dict[str, str] = {
    "localization": "自己位置推定",
    "slam": "SLAM",
    "lidar": "LiDAR",
    "imu": "IMU",
    "gnss": "GNSS",
    "path_planning": "経路計画",
    "state_estimation": "状態推定",
    "point_cloud_processing": "点群処理",
    "ros": "ROS",
    "deep_learning": "深層学習",
    "computer_vision": "コンピュータビジョン",
    "control": "制御",
    "simulation": "シミュレーション",
    "datasets": "データセット",
    "bim_construction": "BIM / 建設",
}

TYPE_LABELS: dict[str, str] = {
    "arxiv_paper": "arXiv 論文",
    "experiment_data": "実験データ",
    "local_file": "ローカルファイル",
    "llm_article": "LLM 記事",
    "repo_readme": "リポジトリ README",
    "unknown": "不明",
    "web_article": "Web 記事",
}


def concept_label(concept: str) -> str:
    return CONCEPT_LABELS.get(concept, concept.replace("_", " ").title())


def concept_link(concept: str) -> str:
    return f"[[{concept}|{concept_label(concept)}]]"


def type_label(article_type: str) -> str:
    return TYPE_LABELS.get(article_type, article_type)


def display_title(title: str) -> str:
    if title.startswith("Repo: "):
        return f"リポジトリ: {title[6:]}"
    if title.startswith("Experiment: "):
        return f"実験: {title[12:]}"
    return title


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str) -> str:
    """テキストをファイルシステム安全な slug に変換する。"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:80].strip("-")


def extract_title_from_html(html_text: str) -> str:
    """HTML から <title> を抽出する。"""
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if match:
        return html.unescape(match.group(1)).strip()
    return ""


def html_to_markdown(html_text: str) -> str:
    """最小限の HTML -> Markdown 変換。記事用途として十分な精度。"""
    text = html_text
    # script / style / nav / header / footer などを除去
    for tag in ("script", "style", "nav", "header", "footer", "aside"):
        text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # 見出し
    for level in range(1, 7):
        text = re.sub(rf"<h{level}[^>]*>(.*?)</h{level}>", rf"\n{'#' * level} \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    # 段落と div
    text = re.sub(r"<(?:p|div)[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(?:p|div)>", "\n", text, flags=re.IGNORECASE)
    # 改行
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # 太字と斜体
    text = re.sub(r"<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<(?:em|i)[^>]*>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    # リンク
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.IGNORECASE | re.DOTALL)
    # コード
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<pre[^>]*>(.*?)</pre>", r"\n```\n\1\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
    # 箇条書き
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", text, flags=re.IGNORECASE | re.DOTALL)
    # 画像
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?>',  r"![\2](\1)", text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?>',  r"![](\1)", text, flags=re.IGNORECASE)
    # 残ったタグを除去
    text = re.sub(r"<[^>]+>", "", text)
    # HTML エンティティをデコード
    text = html.unescape(text)
    # 余分な空白を整理
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def classify_content(text: str) -> list[str]:
    """テキストに一致するコンセプトタグを返す。"""
    lowered = text.lower()
    matched: list[tuple[str, int]] = []
    for concept, keywords in CONCEPT_KEYWORDS.items():
        score = sum(lowered.count(kw) for kw in keywords)
        if score >= 2:
            matched.append((concept, score))
    matched.sort(key=lambda x: x[1], reverse=True)
    return [concept for concept, _ in matched[:5]]


def read_frontmatter(path: Path) -> dict[str, Any]:
    """.md ファイルから YAML 風 frontmatter を読む。"""
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
    """frontmatter を除いた Markdown 本文を返す。"""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end >= 0:
            return text[end + 3:].strip()
    return text.strip()


def word_count(text: str) -> int:
    return len(text.split())


# ---- ingest コマンド ----

def ingest_url(url: str) -> Path:
    """URL を取得して raw/ 配下に .md として保存する。"""
    print(f"{url} を取得しています ...")
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
    print(f"  -> {dest.relative_to(ROOT)} ({word_count(md_body)} 語, コンセプト: {concepts})")
    return dest


def ingest_file(file_path: Path) -> Path:
    """ローカルファイルを frontmatter 付きで raw/ へコピーする。"""
    if not file_path.exists():
        print(f"ファイルが見つかりません: {file_path}", file=sys.stderr)
        sys.exit(1)

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    # 既に frontmatter がある場合はそのままコピーする
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
    """このリポジトリ自身の実験データを raw ソースとして取り込む。"""
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
            f'title: "実験: {name}"',
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
            lines.append(f"## {impl['repo']}（トラック: {impl['track']}、スコア: {score}）")
            lines.append("")
            lines.append(f"- 説明: {impl.get('description', 'なし')}")
            lines.append(f"- 言語: {impl.get('language', '?')}")
            lines.append(f"- アルゴリズム: {algos}")
            inputs = ", ".join(impl.get("io", {}).get("inputs", []))
            outputs = ", ".join(impl.get("io", {}).get("outputs", []))
            lines.append(f"- I/O: {inputs} -> {outputs}")
            lines.append("")

        dest.write_text("\n".join(lines), encoding="utf-8")
        created.append(dest)
        print(f"  -> {dest.relative_to(ROOT)}")

    return created


def ingest_repo_readmes() -> list[Path]:
    """キャッシュ済みリポジトリすべてから README.md を取り込む。"""
    cache_dir = ROOT / ".cache" / "repos"
    if not cache_dir.exists():
        print("キャッシュ済みリポジトリが見つかりません。先に `expctl.py sync` を実行してください。")
        return []

    created: list[Path] = []
    for repo_dir in sorted(cache_dir.iterdir()):
        if not repo_dir.is_dir():
            continue
        readme = repo_dir / "README.md"
        if not readme.exists():
            # 小文字の readme.md も試す
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
        title: "リポジトリ: {repo_name}"
        source: "https://github.com/rsasaki0109/{repo_name}"
        ingested_at: "{utc_now()}"
        concepts: [{', '.join(f'"{c}"' for c in concepts)}]
        type: "repo_readme"
        ---
        """)

        dest.write_text(frontmatter + text, encoding="utf-8")
        created.append(dest)
        print(f"  -> {dest.relative_to(ROOT)} ({word_count(text)} 語, {concepts[:3]})")

    return created


def ingest_arxiv(query: str, max_results: int = 10) -> list[Path]:
    """arXiv API から論文を取り込む。"""
    import xml.etree.ElementTree as ET

    encoded_query = urllib.parse.quote(query)
    url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=relevance"
    print(f"arXiv で '{query}' を検索しています (最大 {max_results} 件) ...")

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
            f"**公開日:** {published}",
            f"**著者:** {', '.join(authors[:5])}{'...' if len(authors) > 5 else ''}",
            f"**カテゴリ:** {', '.join(categories)}",
            "",
            "## 概要",
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
        print(f"README を {len(created)} 件取り込みました")
        return

    if mode == "arxiv":
        query = " ".join(sources) if sources else "robotics SLAM localization LiDAR"
        max_results = getattr(args, "max_results", 10)
        created = ingest_arxiv(query, max_results)
        print(f"arXiv 論文を {len(created)} 件取り込みました")
        return

    if not sources:
        print("ソース指定が無いため、registry/experiments.yaml から取り込みます ...")
        created = ingest_repo_data()
        print(f"実験ファイルを {len(created)} 件取り込みました")
        return

    for source in sources:
        if source.startswith("http://") or source.startswith("https://"):
            ingest_url(source)
        else:
            ingest_file(Path(source))


# ---- compile コマンド ----

def compile_command(_args: argparse.Namespace) -> None:
    """raw/ を wiki/ へコンパイルする。index.md と concept pages を生成する。"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(RAW_DIR.glob("*.md"))
    if not raw_files:
        print("raw ファイルが見つかりません。先に `kb ingest` を実行してください。")
        return

    # メタデータ付きで全記事を収集
    articles: list[dict[str, Any]] = []
    concept_articles: dict[str, list[dict[str, Any]]] = {}

    for path in raw_files:
        fm = read_frontmatter(path)
        body = body_text(path)
        title = display_title(str(fm.get("title", path.stem)))
        concepts = fm.get("concepts", [])
        if isinstance(concepts, str):
            concepts = [concepts]
        # コンセプトが無ければ本文から再分類する
        if not concepts:
            concepts = classify_content(body)

        # 要約は、見出し以降の最初の非空行 2 行から組み立てる
        summary_lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                summary_lines.append(stripped)
                if len(summary_lines) >= 2:
                    break
        summary = " ".join(summary_lines)[:200]
        summary = summary.replace("**Published:**", "**公開日:**")
        summary = summary.replace("**Authors:**", "**著者:**")
        summary = summary.replace("**Categories:**", "**カテゴリ:**")

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

    # コンセプト共起グラフを構築
    concept_graph: dict[str, Counter[str]] = {}
    for art in articles:
        for c in art["concepts"]:
            concept_graph.setdefault(c, Counter())
            for c2 in art["concepts"]:
                if c2 != c:
                    concept_graph[c][c2] += 1

    # 記事を種別ごとに整理する
    by_type: dict[str, list[dict[str, Any]]] = {}
    for art in articles:
        by_type.setdefault(art["type"], []).append(art)

    # index.md を生成する（Obsidian 互換）
    index_lines = [
        "# ナレッジベース索引",
        "",
        f"生成日時: {utc_now()}",
        "",
        f"記事数: {len(articles)}  ",
        f"総語数: {sum(a['word_count'] for a in articles):,}  ",
        f"コンセプト数: {len(concept_articles)}  ",
        f"ソース種別: {', '.join(f'{type_label(t)} ({len(arts)})' for t, arts in sorted(by_type.items()))}",
        "",
        "## コンセプトマップ",
        "",
    ]
    for concept in sorted(concept_articles.keys()):
        count = len(concept_articles[concept])
        related = concept_graph.get(concept, Counter())
        top_related = ", ".join(concept_link(c) for c, _ in related.most_common(3))
        index_lines.append(f"- {concept_link(concept)} ({count} 記事) — 関連: {top_related}")
    index_lines.extend(["", "## 種別ごと", ""])
    for article_type in sorted(by_type.keys()):
        type_arts = by_type[article_type]
        index_lines.append(f"### {type_label(article_type)} ({len(type_arts)})")
        index_lines.append("")
        for art in sorted(type_arts, key=lambda a: a["word_count"], reverse=True):
            tags = " ".join(concept_link(c) for c in art["concepts"])
            index_lines.append(f"- **{art['title']}** — {art['word_count']} 語 — {tags}")
        index_lines.append("")

    INDEX_PATH.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"{INDEX_PATH.relative_to(ROOT)} を生成しました")

    # コンセプトページを生成する（Obsidian 互換、バックリンク対応）
    for concept, arts in concept_articles.items():
        concept_path = CONCEPTS_DIR / f"{concept}.md"
        pretty_name = concept_label(concept)
        related = concept_graph.get(concept, Counter())

        lines = [
            f"# {pretty_name}",
            "",
            f"記事数: {len(arts)}  ",
            f"総語数: {sum(a['word_count'] for a in arts):,}",
            "",
        ]

        # 関連コンセプトとバックリンクを出力する
        if related:
            lines.append("## 関連コンセプト")
            lines.append("")
            for rel_concept, overlap_count in related.most_common(8):
                lines.append(f"- {concept_link(rel_concept)} ({overlap_count} 件の共通記事)")
            lines.append("")

        # このコンセプトに属する主要 repo
        repo_arts = [a for a in arts if a["type"] == "repo_readme"]
        if repo_arts:
            lines.append("## リポジトリ")
            lines.append("")
            for art in sorted(repo_arts, key=lambda a: a["word_count"], reverse=True)[:10]:
                source = art["source"]
                lines.append(f"- [{art['title']}]({source}) — {art['word_count']} 語")
            lines.append("")

        # このコンセプトに属する arXiv 論文
        paper_arts = [a for a in arts if a["type"] == "arxiv_paper"]
        if paper_arts:
            lines.append("## 論文")
            lines.append("")
            for art in sorted(paper_arts, key=lambda a: a.get("ingested_at", ""), reverse=True)[:10]:
                source = art["source"]
                lines.append(f"- [{art['title']}]({source}) — {art['summary'][:100]}...")
            lines.append("")

        # その他のソース
        other_arts = [a for a in arts if a["type"] not in ("repo_readme", "arxiv_paper")]
        if other_arts:
            lines.append("## その他のソース")
            lines.append("")
            for art in sorted(other_arts, key=lambda a: a["word_count"], reverse=True):
                lines.append(f"- [{art['title']}]({art['source']}) — {art['word_count']} 語")
            lines.append("")

        # どのコンセプトページから参照されるか
        backlink_concepts = [c for c, _ in related.most_common()]
        if backlink_concepts:
            lines.append("## バックリンク")
            lines.append("")
            for bl in backlink_concepts[:10]:
                lines.append(f"- {concept_link(bl)}")
            lines.append("")

        concept_path.write_text("\n".join(lines), encoding="utf-8")

    # グラフ可視化データを生成する（Obsidian Graph / 手動確認向け）
    graph_path = WIKI_DIR / "graph.md"
    graph_lines = [
        "# コンセプトグラフ",
        "",
        "ノード = コンセプト、エッジ = コンセプト間で共有された記事数。",
        "",
        "```",
    ]
    for concept in sorted(concept_graph.keys()):
        related = concept_graph[concept]
        for target, weight in related.most_common(5):
            if concept < target:  # 重複辺を避ける
                graph_lines.append(f"{concept} --({weight})--> {target}")
    graph_lines.extend(["```", ""])
    graph_path.write_text("\n".join(graph_lines), encoding="utf-8")

    print(f"wiki/concepts/ にコンセプトページを {len(concept_articles)} 件生成しました")
    print("wiki/graph.md にコンセプトグラフを生成しました")
    print(f"wiki/ へ {len(articles)} 件の記事をコンパイルしました")

    # LLM による記事生成
    if getattr(_args, "llm", False):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("警告: ANTHROPIC_API_KEY が未設定のため、LLM コンパイルをスキップします。")
            return
        llm_compile(articles, concept_articles, concept_graph, api_key)


def call_claude(prompt: str, system: str, api_key: str, max_tokens: int = 2000) -> str:
    """Claude API を urllib で直接呼び出す（SDK 依存なし）。"""
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
    """各コンセプト向けに LLM 生成 wiki 記事を作る。"""
    llm_dir = WIKI_DIR / "articles"
    llm_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = textwrap.dedent("""\
    あなたはロボティクス研究向けナレッジベースの編集者です。日本語で簡潔かつ技術的な wiki 記事を書いてください。
    各記事は次を満たしてください。
    - 最初に 1 段落で概念の概要を示す
    - 主要なアルゴリズム、手法、トレードオフを扱う
    - 与えられたデータに含まれる具体的なリポジトリ名と論文名に言及する
    - 関連概念へのリンクに Obsidian 互換の [[backlinks]] を使う
    - 300〜600 語程度で、情報密度を高くし、冗長さを避ける
    - markdown の見出し (##) で構成する
    出力は markdown 本文のみとし、frontmatter は含めない。
    """)

    generated = 0
    for concept, arts in sorted(concept_articles.items(), key=lambda x: len(x[1]), reverse=True):
        if len(arts) < 2:
            continue

        dest = llm_dir / f"{concept}.md"
        pretty_name = concept_label(concept)
        related = concept_graph.get(concept, Counter())
        related_names = [c for c, _ in related.most_common(5)]

        # 記事群からプロンプト用の文脈を組み立てる
        context_parts: list[str] = []
        for art in arts[:15]:
            context_parts.append(f"- {art['title']} ({type_label(art['type'])}, {art['word_count']} 語): {art['summary'][:150]}")

        prompt = textwrap.dedent(f"""\
        ロボティクス文脈における「{pretty_name}」の wiki 記事を書いてください。

        関連コンセプト: {', '.join(concept_label(name) for name in related_names)}

        このコンセプトに属する記事:
        {chr(10).join(context_parts)}

        要件:
        - 日本語で書く
        - 関連概念へのリンクは [[{related_names[0] if related_names else 'slam'}]] 構文を使う
        - 具体的な repo 名と論文名を明示する
        - 簡潔かつ技術的にまとめる
        """)

        print(f"  LLM 生成中: {concept} ({len(arts)} 記事) ...", end=" ", flush=True)
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
            print(f"完了 ({word_count(article_text)} 語)")
        except Exception as e:
            print(f"失敗: {e}")

    print(f"wiki/articles/ に LLM 記事を {generated} 件生成しました")


# ---- search コマンド ----

def search_command(args: argparse.Namespace) -> None:
    """wiki と raw ファイルを検索する。"""
    query = " ".join(args.query).lower()
    if not query:
        print("使い方: kb search <query>")
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
                # 前後 1 行を含めて表示する
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    context = "\n".join(f"  {lines[j]}" for j in range(start, end))
                    matched_lines.append(f"  L{i + 1}:\n{context}")
            if matched_lines:
                results.append((path, len(matched_lines), matched_lines))

    if not results:
        print(f'"{query}" に一致する結果はありません')
        return

    results.sort(key=lambda x: x[1], reverse=True)
    print(f'"{query}" について {len(results)} ファイルで {sum(r[1] for r in results)} 件見つかりました:\n')

    for path, count, matches in results[:10]:
        rel = path.relative_to(ROOT)
        print(f"--- {rel} ({count} 件) ---")
        for match in matches[:3]:
            print(match)
        if len(matches) > 3:
            print(f"  ... さらに {len(matches) - 3} 件")
        print()


# ---- lint コマンド ----

def lint_command(_args: argparse.Namespace) -> None:
    """ナレッジベースの健全性を確認する。"""
    issues: list[str] = []
    suggestions: list[str] = []

    # raw/ と wiki/ の基本状態を確認する
    raw_files = list(RAW_DIR.glob("*.md")) if RAW_DIR.exists() else []
    wiki_files = list(WIKI_DIR.rglob("*.md")) if WIKI_DIR.exists() else []

    print(f"raw ファイル数: {len(raw_files)}")
    print(f"wiki ファイル数: {len(wiki_files)}")
    print()

    if not raw_files:
        issues.append("raw ファイルがありません。`kb ingest` を実行してください。")

    if raw_files and not wiki_files:
        issues.append("raw ファイルはありますが wiki が空です。`kb compile` を実行してください。")

    # frontmatter の有無を確認する
    missing_frontmatter = 0
    missing_concepts = 0
    all_concepts: Counter[str] = Counter()
    all_sources: set[str] = set()

    for path in raw_files:
        fm = read_frontmatter(path)
        if not fm:
            missing_frontmatter += 1
            issues.append(f"frontmatter がありません: {path.relative_to(ROOT)}")
        elif not fm.get("concepts"):
            missing_concepts += 1
            issues.append(f"concepts がありません: {path.relative_to(ROOT)}")
        else:
            concepts = fm["concepts"]
            if isinstance(concepts, str):
                concepts = [concepts]
            for c in concepts:
                all_concepts[c] += 1
        source = fm.get("source", "")
        if source:
            all_sources.add(source)

    # wiki 内の壊れた内部リンクを確認する
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
                issues.append(f"リンク切れ: {path.relative_to(ROOT)} -> {link_target}")

    # コンセプトの被覆率を確認する
    uncovered = [name for name in CONCEPT_KEYWORDS if name not in all_concepts]
    if uncovered:
        suggestions.append(f"未カバーのコンセプト（ソース追加候補）: {', '.join(uncovered[:8])}")

    # 短すぎる記事を確認する
    for path in raw_files:
        body = body_text(path)
        if word_count(body) < 50:
            suggestions.append(f"短すぎる記事 ({word_count(body)} 語): {path.relative_to(ROOT)}")

    # 索引の更新時刻を確認する
    if INDEX_PATH.exists():
        raw_newest = max((f.stat().st_mtime for f in raw_files), default=0)
        index_mtime = INDEX_PATH.stat().st_mtime
        if raw_newest > index_mtime:
            issues.append("索引が古い状態です。`kb compile` で更新してください。")

    # 結果を表示する
    if issues:
        print(f"問題点 ({len(issues)} 件):")
        for issue in issues:
            print(f"  - {issue}")
        print()

    if suggestions:
        print(f"提案 ({len(suggestions)} 件):")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
        print()

    if all_concepts:
        print("コンセプトのカバレッジ:")
        for concept, count in all_concepts.most_common():
            bar = "#" * min(count, 20)
            print(f"  {concept:25s} {bar} ({count})")
        print()

    if not issues and not suggestions:
        print("問題は見つかりませんでした")


# ---- stats コマンド ----

def stats_command(_args: argparse.Namespace) -> None:
    """ナレッジベースの統計を表示する。"""
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

    print(f"raw 記事数:   {len(raw_files)}")
    print(f"raw 語数:     {total_raw_words:,}")
    print(f"wiki ファイル数: {len(wiki_files)}")
    print(f"wiki 語数:     {total_wiki_words:,}")
    print(f"コンセプト数:  {len(concepts)}")
    print()
    if types:
        print("ソース種別:")
        for t, count in types.most_common():
            print(f"  {t}: {count}")
    print()
    if concepts:
        print("上位コンセプト:")
        for c, count in concepts.most_common(10):
            print(f"  {c}: {count}")


# ---- ask コマンド ----

def ask_command(args: argparse.Namespace) -> None:
    """ナレッジベースを使って質問に答える。

    関連記事を探し、重要な抜粋を集め、ソース付きで整理して表示する。
    LLM API がなくても、キーワード検索と抜粋の組み合わせで動作する。
    """
    question = " ".join(args.question)
    if not question:
        print("使い方: kb ask <question>")
        return

    # 質問文を検索語へ分解する
    stop_words = {"の", "は", "が", "を", "に", "で", "と", "から", "まで", "より",
                  "what", "is", "are", "how", "does", "do", "the", "a", "an", "in",
                  "of", "for", "to", "and", "or", "which", "between", "vs", "about"}
    terms = [t.lower() for t in re.split(r"[\s,?!。、？]+", question) if t.lower() not in stop_words and len(t) > 1]

    if not terms:
        print("質問から検索語を抽出できませんでした。")
        return

    # すべての候補ファイルに関連度を付ける
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
                    # タイトル一致には加点する
                    if term in title:
                        score += 10

            # raw より wiki 記事をやや優先する
            if "articles" in path.parts:
                score *= 1.5
            elif "concepts" in path.parts:
                score *= 1.2

            if score > 0:
                scored.append((path, score, matched_terms))

    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        print(f"関連する記事が見つかりませんでした: {question}")
        return

    # 上位結果と抜粋を表示する
    print(f"質問: {question}")
    print(f"検索語: {', '.join(terms)}")
    print(f"関連ファイル {len(scored)} 件\n")
    print("=" * 60)

    for path, score, matched in scored[:5]:
        fm = read_frontmatter(path)
        title = fm.get("title", path.stem)
        rel_path = path.relative_to(ROOT)
        article_type = fm.get("type", "unknown")
        source = fm.get("source", "")

        print(f"\n## {title}")
        print(f"   ファイル: {rel_path} ({type_label(article_type)}, 関連度: {score:.0f})")
        if source:
            print(f"   ソース: {source}")

        # 関連する抜粋を集める
        body = body_text(path)
        lines = body.splitlines()
        excerpts: list[str] = []
        for i, line in enumerate(lines):
            lowered = line.lower()
            if any(term in lowered for term in terms):
                # 前後 1 行を含めて文脈を残す
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
                # 長い抜粋は詰める
                if len(excerpt) > 300:
                    excerpt = excerpt[:300] + "..."
                print(f"   > {excerpt}")
            print()

    print("=" * 60)
    print(f"\nさらに深掘りするには全文を読むか、`kb search {terms[0]}` を実行してください")


# ---- parser ----

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="rsasaki-hub 用ナレッジベース CLI",
        prog="kb",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_p = subparsers.add_parser("ingest", help="ソースを raw/ へ取り込む")
    ingest_p.add_argument("sources", nargs="*", help="URL またはローカルファイルパス。未指定なら experiments.yaml から取り込む")
    ingest_mode = ingest_p.add_mutually_exclusive_group()
    ingest_mode.add_argument("--repos", dest="mode", action="store_const", const="repos", help="キャッシュ済み全リポジトリの README.md を取り込む")
    ingest_mode.add_argument("--arxiv", dest="mode", action="store_const", const="arxiv", help="arXiv から論文を取り込む（sources は検索クエリ）")
    ingest_p.add_argument("--max-results", type=int, default=10, help="arXiv の最大取得件数（既定値: 10）")
    ingest_p.set_defaults(func=ingest_command)

    compile_p = subparsers.add_parser("compile", help="raw/ を wiki/ にコンパイルする")
    compile_p.add_argument("--llm", action="store_true", help="LLM 生成のコンセプト記事も作成する（ANTHROPIC_API_KEY が必要）")
    compile_p.set_defaults(func=compile_command)

    search_p = subparsers.add_parser("search", help="ナレッジベースを検索する")
    search_p.add_argument("query", nargs="+", help="検索語")
    search_p.set_defaults(func=search_command)

    lint_p = subparsers.add_parser("lint", help="ナレッジベースの健全性を確認する")
    lint_p.set_defaults(func=lint_command)

    stats_p = subparsers.add_parser("stats", help="ナレッジベース統計を表示する")
    stats_p.set_defaults(func=stats_command)

    ask_p = subparsers.add_parser("ask", help="ナレッジベースに質問する")
    ask_p.add_argument("question", nargs="+", help="質問文")
    ask_p.set_defaults(func=ask_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
