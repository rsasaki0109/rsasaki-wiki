#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluator.benchmark import evaluate as evaluate_benchmark
from evaluator.extensibility import evaluate as evaluate_extensibility
from evaluator.readability import evaluate as evaluate_readability
from ingestors.github_loader import github_token_from_env, sync_owner, sync_repo_checkout
from synthesizer.abstraction import synthesize_track_interface
from synthesizer.diff import build_pairwise_diffs


REPO_REGISTRY_PATH = ROOT / "registry" / "repos.yaml"
EXPERIMENT_REGISTRY_PATH = ROOT / "registry" / "experiments.yaml"
CACHE_ROOT = ROOT / ".cache" / "repos"

SOURCE_SUFFIXES = {".py", ".c", ".cc", ".cpp", ".h", ".hpp", ".rs"}
TEXT_SUFFIXES = SOURCE_SUFFIXES | {".md", ".yaml", ".yml", ".json", ".toml", ".xml", ".txt", ".sh"}
MESSAGE_TOKENS = {
    "PointCloud2": "PointCloud2",
    "Imu": "Imu",
    "Odometry": "Odometry",
    "LaserScan": "LaserScan",
    "PoseStamped": "Pose",
    "PoseWithCovarianceStamped": "Pose",
    "PoseWithCovariance": "Pose",
    "Pose": "Pose",
    "Path": "Path",
    "MapArray": "MapArray",
    "NavSatFix": "NavSatFix",
}
INPUT_HINTS = ("Subscription", "create_subscription", "Received", "receive", "input", "sub_")
OUTPUT_HINTS = ("Publisher", "create_publisher", "publish", "pub_", "output")
ALGORITHM_MARKERS = {
    "ndt": "NDT",
    "gicp": "GICP",
    "vgicp": "VGICP",
    "fast_gicp": "FAST_GICP",
    "small_gicp": "SMALL_GICP",
    "icp": "ICP",
    "particle_filter": "ParticleFilter",
    "amcl": "AMCL",
    "kalman": "Kalman",
    "imu_preintegration": "IMUPreintegration",
    "preintegration": "IMUPreintegration",
    "lio": "LIO",
    "inertial": "Inertial",
    "loop": "LoopClosure",
    "graph_based_slam": "PoseGraph",
    "pose graph": "PoseGraph",
    "g2o": "PoseGraph",
    "scan_context": "ScanContext",
    "deskew": "Deskew",
    "voxel": "VoxelGrid",
    "submap": "Submap",
    "odometry": "Odometry",
}
PY_FUNCTION_PATTERN = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
CXX_FUNCTION_PATTERN = re.compile(
    r"^\s*(?:template\s*<[^>]+>\s*)?(?:[A-Za-z_:<>~*&]+\s+)+([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:const)?\s*(?:\{|$)",
    re.MULTILINE,
)
TOPIC_PATTERN = re.compile(r"['\"](/[A-Za-z0-9_/\-]+)['\"]")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_yaml_like(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def load_yaml_like(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_yaml_like(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml_like(payload), encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def list_files(repo_root: Path) -> list[Path]:
    return [
        path
        for path in repo_root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    ]


def list_text_files(repo_root: Path) -> list[Path]:
    return [path for path in list_files(repo_root) if path.suffix.lower() in TEXT_SUFFIXES]


def list_source_files(repo_root: Path) -> list[Path]:
    return [path for path in list_files(repo_root) if path.suffix.lower() in SOURCE_SUFFIXES]


def repo_text_blob(repo: dict[str, Any]) -> str:
    fields = [repo.get("name", ""), repo.get("description", ""), " ".join(repo.get("topics", []))]
    return " ".join(fields).lower()


def keyword_score(text: str, keywords: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lowered)


def extract_function_names(files: list[Path]) -> list[str]:
    names: Counter[str] = Counter()
    for path in files:
        text = read_text(path)
        matches = PY_FUNCTION_PATTERN.findall(text) if path.suffix == ".py" else CXX_FUNCTION_PATTERN.findall(text)
        for name in matches:
            if name not in {"if", "for", "while", "switch", "return"}:
                names[name] += 1
    return [name for name, _count in names.most_common(12)]


def extract_ros_topics(files: list[Path]) -> list[str]:
    topics: Counter[str] = Counter()
    for path in files:
        for topic in TOPIC_PATTERN.findall(read_text(path)):
            topics[topic] += 1
    return [topic for topic, _count in topics.most_common(12)]


def extract_io(files: list[Path]) -> dict[str, list[str]]:
    inputs: set[str] = set()
    outputs: set[str] = set()
    mentions: set[str] = set()

    for path in files:
        for line in read_text(path).splitlines():
            for token, simplified in MESSAGE_TOKENS.items():
                if token not in line:
                    continue
                mentions.add(simplified)
                if any(hint in line for hint in INPUT_HINTS):
                    inputs.add(simplified)
                elif any(hint in line for hint in OUTPUT_HINTS):
                    outputs.add(simplified)

    if "PointCloud2" in mentions:
        inputs.add("PointCloud2")
    if "Imu" in mentions:
        inputs.add("Imu")
    if "Odometry" in mentions:
        inputs.add("Odometry")
    if "LaserScan" in mentions:
        inputs.add("LaserScan")
    if "Pose" in mentions and not outputs:
        outputs.add("Pose")
    if "Path" in mentions:
        outputs.add("Path")
    if "MapArray" in mentions:
        outputs.add("MapArray")

    return {
        "inputs": sorted(inputs),
        "outputs": sorted(outputs),
    }


def extract_algorithm_markers(files: list[Path], repo: dict[str, Any]) -> list[str]:
    markers: Counter[str] = Counter()
    texts = [repo_text_blob(repo)]
    texts.extend(read_text(path).lower() for path in files if path.suffix.lower() in TEXT_SUFFIXES)
    joined = "\n".join(texts)
    for needle, label in ALGORITHM_MARKERS.items():
        count = joined.count(needle.lower())
        if count:
            markers[label] += count
    return [label for label, _count in markers.most_common(10)]


def pick_relevant_files(repo_root: Path, experiment: dict[str, Any]) -> list[Path]:
    keywords = [item.lower() for item in experiment.get("family_keywords", [])]
    signals = keywords + [token.lower() for token in MESSAGE_TOKENS] + [key.lower() for key in ALGORITHM_MARKERS]
    relevant: list[Path] = []
    for path in list_text_files(repo_root):
        lowered_path = path.as_posix().lower()
        if any(signal in lowered_path for signal in signals):
            relevant.append(path)
            continue
        if path.suffix.lower() in SOURCE_SUFFIXES:
            text = read_text(path).lower()
            if any(signal in text for signal in signals):
                relevant.append(path)
    source_files = list_source_files(repo_root)
    if not any(path.suffix.lower() in SOURCE_SUFFIXES for path in relevant):
        relevant.extend(source_files[:12])
    if relevant:
        return sorted(set(relevant))[:40]
    return source_files[:20]


def classify_track(experiment: dict[str, Any], repo: dict[str, Any], files: list[Path], io: dict[str, list[str]], algorithms: list[str]) -> tuple[str, int]:
    repo_text = repo_text_blob(repo)
    repo_name = repo.get("name", "").lower()
    file_text = "\n".join(path.as_posix().lower() for path in files)
    algorithm_text = " ".join(algorithms).lower()
    io_text = " ".join(io.get("inputs", []) + io.get("outputs", [])).lower()

    best_track = "unclassified"
    best_score = -1
    for track in experiment.get("tracks", []):
        keywords = track.get("keywords", [])
        score = keyword_score(repo_text, keywords) * 2
        score += keyword_score(file_text, keywords)
        score += keyword_score(algorithm_text, keywords)
        score += keyword_score(io_text, keywords)
        if track["name"] == "lidar_localization":
            if "localization" in repo_name or "localizer" in repo_name or "amcl" in repo_name:
                score += 5
            if "localization" in repo_text or "localizer" in repo_text or "amcl" in repo_text:
                score += 3
            if "Pose" in io.get("outputs", []):
                score += 2
            if "PointCloud2" in io.get("inputs", []) and "Pose" in io.get("inputs", []):
                score += 2
        elif track["name"] == "lidar_slam":
            if "slam" in repo_name or "mapping" in repo_name:
                score += 5
            if "slam" in repo_text or "mapping" in repo_text:
                score += 3
            if {"PointCloud2", "Path"} & set(io.get("outputs", [])):
                score += 2
            if "PoseGraph" in algorithms or "LoopClosure" in algorithms:
                score += 2
        elif track["name"] == "lidar_imu_slam":
            if "lio" in repo_name or "imu" in repo_name:
                score += 5
            if "lio" in repo_text or "inertial" in repo_text:
                score += 3
            if "Imu" in io.get("inputs", []):
                score += 3
            if "LIO" in algorithms or "IMUPreintegration" in algorithms:
                score += 3
        if score > best_score:
            best_track = track["name"]
            best_score = score
    return best_track, best_score


def candidate_status(repo: dict[str, Any], track: str, files: list[Path], io: dict[str, list[str]], algorithms: list[str], best_score: int) -> tuple[bool, str | None]:
    core_problem_words = ("localization", "localizer", "slam", "lio", "odometry", "amcl")
    repo_text = repo_text_blob(repo)
    if not files:
        return False, "no_source_files"
    if best_score < 3:
        return False, "weak_problem_match"
    if not any(word in repo_text for word in core_problem_words):
        return False, "out_of_scope_domain"
    if "PointCloud2" not in io.get("inputs", []) and "LaserScan" not in io.get("inputs", []):
        return False, "no_lidar_input_signal"
    if track == "lidar_localization" and "Pose" not in io.get("outputs", []):
        return False, "missing_pose_output"
    if track == "lidar_slam" and not {"Pose", "Odometry", "MapArray"} & set(io.get("outputs", [])):
        return False, "supporting_component_only"
    if track == "lidar_imu_slam" and "Imu" not in io.get("inputs", []):
        return False, "missing_imu_input"
    if not io.get("outputs"):
        return False, "supporting_component_only"
    if repo["name"] in {"imu_estimator", "laser_deskew", "ndt_omp_ros2"}:
        return False, "supporting_component_only"
    if "Deskew" in algorithms and "LIO" not in algorithms and "PoseGraph" not in algorithms:
        return False, "preprocessing_only"
    return True, None


def summarize_repo(repo: dict[str, Any], track: str, algorithms: list[str], io: dict[str, list[str]]) -> str:
    input_summary = ", ".join(io.get("inputs", [])[:3]) or "unknown input"
    output_summary = ", ".join(io.get("outputs", [])[:3]) or "unknown output"
    algo_summary = ", ".join(algorithms[:3]) or "generic pipeline"
    return f"{track}: {input_summary} -> {output_summary} via {algo_summary}"


def sync_command(args: argparse.Namespace) -> None:
    owner = args.owner
    token = args.token or github_token_from_env()
    payload = sync_owner(owner=owner, registry_path=REPO_REGISTRY_PATH, token=token)
    print(f"synced {len(payload['repos'])} public repos for {owner}")


def extract_command(_args: argparse.Namespace) -> None:
    repo_registry = load_yaml_like(REPO_REGISTRY_PATH)
    experiment_registry = load_yaml_like(EXPERIMENT_REGISTRY_PATH)

    repos = repo_registry.get("repos", [])
    for experiment in experiment_registry.get("experiments", []):
        family_keywords = experiment.get("family_keywords", [])
        included: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []

        for repo in repos:
            prefilter_score = keyword_score(repo_text_blob(repo), family_keywords)
            if prefilter_score == 0:
                continue

            local_path = sync_repo_checkout(repo, CACHE_ROOT)
            relevant_files = pick_relevant_files(local_path, experiment)
            source_files = [path for path in relevant_files if path.suffix.lower() in SOURCE_SUFFIXES]
            io = extract_io(relevant_files)
            algorithms = extract_algorithm_markers(relevant_files, repo)
            track, score = classify_track(experiment, repo, relevant_files, io, algorithms)
            include, reason = candidate_status(repo, track, source_files, io, algorithms, score)
            record = {
                "repo": repo["name"],
                "description": repo.get("description", ""),
                "language": repo.get("language"),
                "track": track,
                "local_path": str(local_path),
                "match_score": score,
                "summary": summarize_repo(repo, track, algorithms, io),
                "functions": extract_function_names(source_files),
                "ros_topics": extract_ros_topics(relevant_files),
                "io": io,
                "algorithms": algorithms,
                "relevant_files": [str(path.relative_to(local_path)) for path in relevant_files[:20]],
            }
            if include:
                included.append(record)
            else:
                rejected.append({**record, "reason": reason})

        experiment["status"] = "extracted"
        experiment["generated_at"] = utc_now()
        experiment["implementations"] = sorted(included, key=lambda item: (item["track"], -item["match_score"], item["repo"]))
        experiment["rejected_candidates"] = sorted(
            rejected, key=lambda item: (item["reason"] or "", item["repo"])
        )

    experiment_registry["generated_at"] = utc_now()
    write_yaml_like(EXPERIMENT_REGISTRY_PATH, experiment_registry)
    print("extracted experiment candidates")


def eval_command(_args: argparse.Namespace) -> None:
    experiment_registry = load_yaml_like(EXPERIMENT_REGISTRY_PATH)
    for experiment in experiment_registry.get("experiments", []):
        rankings: dict[str, list[dict[str, Any]]] = {}
        for implementation in experiment.get("implementations", []):
            repo_root = Path(implementation["local_path"])
            relevant_files = [repo_root / relative_path for relative_path in implementation.get("relevant_files", [])]
            benchmark = evaluate_benchmark(relevant_files)
            readability = evaluate_readability(relevant_files)
            extensibility = evaluate_extensibility(relevant_files, repo_root=repo_root)
            overall = round(
                benchmark["score"] * 0.5 + readability["score"] * 0.25 + extensibility["score"] * 0.25,
                2,
            )
            implementation["evaluation"] = {
                "benchmark": benchmark,
                "readability": readability,
                "extensibility": extensibility,
                "overall_score": overall,
                "ranking_policy": "overall = 0.50 benchmark_readiness_or_quality + 0.25 readability + 0.25 extensibility",
            }
            rankings.setdefault(implementation["track"], []).append(
                {"repo": implementation["repo"], "overall_score": overall}
            )

        experiment["status"] = "evaluated"
        experiment["track_rankings"] = {
            track: sorted(values, key=lambda item: item["overall_score"], reverse=True)
            for track, values in rankings.items()
        }

    experiment_registry["generated_at"] = utc_now()
    write_yaml_like(EXPERIMENT_REGISTRY_PATH, experiment_registry)
    print("evaluated extracted implementations")


def format_markdown_list(values: list[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def render_experiments_doc(registry: dict[str, Any]) -> str:
    lines = [
        "# Experiments",
        "",
        f"Generated at: {registry.get('generated_at')}",
        "",
    ]
    for experiment in registry.get("experiments", []):
        lines.extend(
            [
                f"## {experiment['name']}",
                "",
                experiment["problem_statement"],
                "",
            ]
        )
        for track in experiment.get("tracks", []):
            track_name = track["name"]
            implementations = [
                item
                for item in experiment.get("implementations", [])
                if item.get("track") == track_name
            ]
            lines.extend(
                [
                    f"### {track_name}",
                    "",
                    f"- Description: {track['description']}",
                    f"- Implementations: {len(implementations)}",
                ]
            )
            if implementations:
                lines.extend(
                    [
                        "",
                        "| Repo | Score | I/O | Algorithms |",
                        "| --- | ---: | --- | --- |",
                    ]
                )
                for implementation in implementations:
                    score = implementation.get("evaluation", {}).get("overall_score", "-")
                    io_shape = f"{format_markdown_list(implementation['io']['inputs'])} -> {format_markdown_list(implementation['io']['outputs'])}"
                    algorithms = format_markdown_list(implementation.get("algorithms", [])[:4])
                    lines.append(f"| {implementation['repo']} | {score} | {io_shape} | {algorithms} |")
            diffs = build_pairwise_diffs(implementations)
            if diffs:
                lines.extend(["", "- Key diffs:"])
                for diff in diffs[:3]:
                    pair = " vs ".join(diff["pair"])
                    common_inputs = format_markdown_list(diff["common_inputs"])
                    left_only = format_markdown_list(diff["left_only_algorithms"][:3])
                    right_only = format_markdown_list(diff["right_only_algorithms"][:3])
                    lines.append(
                        f"  - {pair}: common input {common_inputs}; algorithm split {left_only} / {right_only}"
                    )
            lines.append("")

        rejected = experiment.get("rejected_candidates", [])
        if rejected:
            lines.extend(["### Rejected Candidates", ""])
            for item in rejected[:10]:
                lines.append(f"- {item['repo']}: {item['reason']}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_decisions_doc(registry: dict[str, Any]) -> str:
    lines = [
        "# Decisions",
        "",
        f"Generated at: {registry.get('generated_at')}",
        "",
    ]
    for experiment in registry.get("experiments", []):
        lines.append(f"## {experiment['name']}")
        lines.append("")
        rankings = experiment.get("track_rankings", {})
        interfaces = experiment.get("interfaces", {})
        for track in experiment.get("tracks", []):
            track_name = track["name"]
            ranked = rankings.get(track_name, [])
            lines.append(f"### {track_name}")
            lines.append("")
            if not ranked:
                lines.append("- No implementation is adopted yet because the track has no extracted candidates.")
                lines.append("")
                continue
            winner = ranked[0]["repo"]
            winner_impl = next(item for item in experiment["implementations"] if item["repo"] == winner)
            interface = interfaces.get(track_name, {})
            lines.append(
                f"- Temporary reference: `{winner}`. This is the current working reference, not a permanent standard."
            )
            lines.append(
                f"- Why it wins now: overall score {winner_impl['evaluation']['overall_score']}, interface {format_markdown_list(interface.get('input', []))} -> {format_markdown_list(interface.get('output', []))}, algorithms {format_markdown_list(winner_impl.get('algorithms', [])[:4])}."
            )
            others = [item["repo"] for item in ranked[1:3]]
            if others:
                lines.append(
                    f"- Kept experimental: {', '.join(f'`{name}`' for name in others)} because they preserve alternative algorithmic choices."
                )
            rejected = [item for item in experiment.get("rejected_candidates", []) if item.get("track") == track_name]
            if rejected:
                sample = rejected[0]
                lines.append(f"- Not adopted now: `{sample['repo']}` because {sample['reason']}.")
            lines.append("- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_interfaces_doc(registry: dict[str, Any]) -> str:
    lines = [
        "# Interfaces",
        "",
        "This repo stabilizes the smallest shared I/O contract that survived comparison.",
        "",
        f"Generated at: {registry.get('generated_at')}",
        "",
    ]
    for experiment in registry.get("experiments", []):
        lines.append(f"## {experiment['name']}")
        lines.append("")
        for track in experiment.get("tracks", []):
            track_name = track["name"]
            interface = experiment.get("interfaces", {}).get(track_name)
            if not interface:
                continue
            lines.append(f"### {track_name}")
            lines.append("")
            lines.append(f"- Input: {format_markdown_list(interface.get('input', []))}")
            lines.append(f"- Optional input: {format_markdown_list(interface.get('optional_input', []))}")
            lines.append(f"- Output: {format_markdown_list(interface.get('output', []))}")
            lines.append(f"- Optional output: {format_markdown_list(interface.get('optional_output', []))}")
            lines.append(f"- Common algorithm markers: {format_markdown_list(interface.get('algorithm_markers', []))}")
            rankings = experiment.get("track_rankings", {}).get(track_name, [])
            if rankings:
                lines.append(f"- Current lineage: {rankings[0]['repo']} is the temporary stabilized reference.")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def synthesize_command(_args: argparse.Namespace) -> None:
    experiment_registry = load_yaml_like(EXPERIMENT_REGISTRY_PATH)
    for experiment in experiment_registry.get("experiments", []):
        interfaces: dict[str, Any] = {}
        for track in experiment.get("tracks", []):
            track_name = track["name"]
            implementations = [
                item
                for item in experiment.get("implementations", [])
                if item.get("track") == track_name
            ]
            if implementations:
                interfaces[track_name] = synthesize_track_interface(track_name, implementations)
        experiment["interfaces"] = interfaces
        experiment["status"] = "synthesized"

    experiment_registry["generated_at"] = utc_now()
    write_yaml_like(EXPERIMENT_REGISTRY_PATH, experiment_registry)
    (ROOT / "docs" / "experiments.md").write_text(render_experiments_doc(experiment_registry), encoding="utf-8")
    (ROOT / "docs" / "decisions.md").write_text(render_decisions_doc(experiment_registry), encoding="utf-8")
    (ROOT / "docs" / "interfaces.md").write_text(render_interfaces_doc(experiment_registry), encoding="utf-8")
    print("synthesized docs and interfaces")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exploration control CLI for rsasaki-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch public repos into registry/repos.yaml")
    sync_parser.add_argument("--owner", default="rsasaki0109")
    sync_parser.add_argument("--token")
    sync_parser.set_defaults(func=sync_command)

    extract_parser = subparsers.add_parser("extract", help="Extract experiment candidates and heuristics")
    extract_parser.set_defaults(func=extract_command)

    eval_parser = subparsers.add_parser("eval", help="Evaluate extracted candidates")
    eval_parser.set_defaults(func=eval_command)

    synth_parser = subparsers.add_parser("synthesize", help="Generate interfaces and docs")
    synth_parser.set_defaults(func=synthesize_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
