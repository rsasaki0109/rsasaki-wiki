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
    # LiDAR / SLAM 系
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
    # ロボティクス基盤アルゴリズム
    "extended_kalman": "EKF",
    "ekf": "EKF",
    "ukf": "UKF",
    "unscented": "UKF",
    "rrt": "RRT",
    "a_star": "AStar",
    "astar": "AStar",
    "dijkstra": "Dijkstra",
    "dwa": "DWA",
    "dynamic_window": "DWA",
    "lqr": "LQR",
    "mpc": "MPC",
    "model_predictive": "MPC",
    "pid": "PID",
    "cubic_spline": "CubicSpline",
    "dubins": "Dubins",
    "potential_field": "PotentialField",
    "voronoi": "Voronoi",
    "prm": "PRM",
    "slam": "SLAM",
    # GNSS / 測位
    "rtk": "RTK",
    "ppp": "PPP",
    "rinex": "RINEX",
    "rtcm": "RTCM",
    "pseudorange": "Pseudorange",
    "carrier_phase": "CarrierPhase",
    "troposphere": "Troposphere",
    "ionosphere": "Ionosphere",
    "ambiguity": "AmbiguityResolution",
    "qzss": "QZSS",
    "clas": "CLAS",
    # 点群処理
    "segmentation": "Segmentation",
    "clustering": "Clustering",
    "ransac": "RANSAC",
    "ground_removal": "GroundRemoval",
    "noise_removal": "NoiseRemoval",
    "downsampling": "Downsampling",
    "semantic": "Semantic",
    "panoptic": "Panoptic",
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
        # --- lidar_stack 向けの加点 ---
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
        # --- robotics_algorithms 向けの加点 ---
        elif track["name"] == "state_estimation":
            if any(w in repo_name for w in ("kalman", "filter", "ekf", "ukf", "particle", "estimation")):
                score += 5
            if any(a in algorithms for a in ("EKF", "UKF", "Kalman", "ParticleFilter")):
                score += 3
        elif track["name"] == "path_planning":
            if any(w in repo_name for w in ("planning", "planner", "rrt", "dwa", "path")):
                score += 5
            if any(a in algorithms for a in ("RRT", "AStar", "Dijkstra", "DWA", "PRM", "MPC", "LQR")):
                score += 3
        elif track["name"] == "scan_matching":
            if any(w in repo_name for w in ("ndt", "icp", "registration", "matching")):
                score += 5
            if any(a in algorithms for a in ("ICP", "NDT", "GICP", "VGICP")):
                score += 3
        # --- gnss_positioning 向けの加点 ---
        elif track["name"] == "gnss_processing":
            if any(w in repo_name for w in ("gnss", "gps", "rtk", "ppp", "rinex")):
                score += 5
            if any(a in algorithms for a in ("RTK", "PPP", "RINEX", "RTCM", "Pseudorange", "QZSS", "CLAS")):
                score += 3
        elif track["name"] == "multi_sensor_positioning":
            if any(w in repo_name for w in ("localizer", "localization", "fusion", "imu", "wheel")):
                score += 5
            if any(a in algorithms for a in ("EKF", "Kalman", "UKF")):
                score += 2
            if "imu" in repo_text or "wheel" in repo_text:
                score += 2
        # --- pointcloud_processing 向けの加点 ---
        elif track["name"] == "pointcloud_analysis":
            if any(w in repo_name for w in ("analyzer", "analysis", "cloud", "quality", "eval")):
                score += 5
            if any(a in algorithms for a in ("Segmentation", "Clustering", "RANSAC")):
                score += 2
        elif track["name"] == "pointcloud_transformation":
            if any(w in repo_name for w in ("removal", "diff", "convert", "npy", "dynamic", "construction")):
                score += 5
            if any(a in algorithms for a in ("GroundRemoval", "NoiseRemoval", "Downsampling", "RANSAC")):
                score += 2
        elif track["name"] == "pointcloud_to_model":
            if any(w in repo_name for w in ("bim", "ifc", "annotator", "semantic", "pointcloud2")):
                score += 5
            if any(a in algorithms for a in ("Semantic", "Panoptic", "Segmentation")):
                score += 3
        if score > best_score:
            best_track = track["name"]
            best_score = score
    return best_track, best_score


def candidate_status(repo: dict[str, Any], track: str, files: list[Path], io: dict[str, list[str]], algorithms: list[str], best_score: int, family_name: str = "lidar_stack_exploration") -> tuple[bool, str | None]:
    repo_text = repo_text_blob(repo)
    if not files:
        return False, "no_source_files"
    if best_score < 3:
        return False, "weak_problem_match"

    # --- lidar_stack 専用の採否条件 ---
    if family_name == "lidar_stack_exploration":
        core_problem_words = ("localization", "localizer", "slam", "lio", "odometry", "amcl")
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

    # --- robotics_algorithms: アルゴリズム実装を要求し、純粋な SLAM/LiDAR/GNSS/点群 repo を除外 ---
    elif family_name == "robotics_algorithms_exploration":
        known = {"EKF", "UKF", "Kalman", "ParticleFilter", "RRT", "AStar", "Dijkstra",
                 "DWA", "PRM", "MPC", "LQR", "PID", "ICP", "NDT", "GICP", "SLAM",
                 "CubicSpline", "Dubins", "PotentialField", "Voronoi"}
        if not known & set(algorithms):
            return False, "no_known_algorithm"
        repo_name = repo.get("name", "").lower()
        # 他ファミリに属する repo を除外する（LiDAR SLAM、GNSS、点群ツールなど）
        lidar_slam_names = {"lidarslam_ros2", "li_slam_ros2", "littleslam_ros2", "glim",
                            "FAST_LIO", "localization_zoo", "lidar_localization_ros2", "amcl_3d",
                            "ndt_omp_ros2", "laser_deskew", "lidar_localizer", "lidar_undistortion"}
        if repo["name"] in lidar_slam_names:
            return False, "belongs_to_lidar_family"
        pointcloud_names = {"CloudAnalyzer", "dynamic-3d-object-removal", "construction-diff",
                            "npy2pointcloud", "pointcloud2ifc", "bim-quality-checker", "rohbau-annotator"}
        if repo["name"] in pointcloud_names:
            return False, "belongs_to_pointcloud_family"
        gnss_names = {"gnssplusplus-library", "gnss_gpu", "gnss_imu_wheel_localizer",
                      "kalman_filter_localization_ros2", "GNSS-Radar", "RTKLIB"}
        if repo["name"] in gnss_names:
            return False, "belongs_to_gnss_family"
        non_algo_names = {"rsasaki0109.github.io", "rsasaki0109", "bagx", "crossdomain-object-tracker",
                          "gs-sim2real", "robotics-technology-genealogy", "company-technology-genealogy",
                          "kinematicPOST", "slam-handbook-python"}
        if repo["name"] in non_algo_names:
            return False, "not_algorithm_implementation"

    # --- gnss_positioning: repo 名または description に GNSS 系シグナルを要求 ---
    elif family_name == "gnss_positioning_exploration":
        gnss_words = ("gnss", "gps", "rtk", "ppp", "satellite", "navsat", "rinex", "rtcm", "qzss")
        repo_name = repo.get("name", "").lower()
        if not any(w in repo_name for w in gnss_words) and not any(w in repo_text for w in gnss_words):
            return False, "no_gnss_signal"
        # 主用途が SLAM の repo は除外する
        if any(w in repo_name for w in ("slam", "lidarslam", "littleslam")):
            return False, "primarily_slam"

    # --- pointcloud_processing: 点群処理を主対象とし、SLAM / localization 系 repo を除外 ---
    elif family_name == "pointcloud_processing_exploration":
        pc_words = ("pointcloud", "point_cloud", "point cloud", "ply", "pcd", "las",
                    "npy", "cloud", "voxel", "bim", "ifc", "construction")
        if not any(w in repo_text for w in pc_words):
            return False, "no_pointcloud_signal"
        repo_name = repo.get("name", "").lower()
        # 主用途が SLAM / localization / GNSS の repo は除外する
        if any(w in repo_name for w in ("slam", "localization", "localizer", "amcl", "gnss", "lio")):
            return False, "primarily_other_domain"

    return True, None


def summarize_repo(repo: dict[str, Any], track: str, algorithms: list[str], io: dict[str, list[str]]) -> str:
    input_summary = ", ".join(io.get("inputs", [])[:3]) or "入力不明"
    output_summary = ", ".join(io.get("outputs", [])[:3]) or "出力不明"
    algo_summary = ", ".join(algorithms[:3]) or "主要アルゴリズム不明"
    return f"{track}: {input_summary} -> {output_summary} / {algo_summary}"


def sync_command(args: argparse.Namespace) -> None:
    owner = args.owner
    token = args.token or github_token_from_env()
    payload = sync_owner(owner=owner, registry_path=REPO_REGISTRY_PATH, token=token)
    print(f"{owner} の公開リポジトリ {len(payload['repos'])} 件を同期しました")


def extract_command(_args: argparse.Namespace) -> None:
    repo_registry = load_yaml_like(REPO_REGISTRY_PATH)
    experiment_registry = load_yaml_like(EXPERIMENT_REGISTRY_PATH)

    repos = repo_registry.get("repos", [])
    synced_checkouts: dict[str, Path] = {}
    for experiment in experiment_registry.get("experiments", []):
        family_keywords = experiment.get("family_keywords", [])
        included: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []

        for repo in repos:
            prefilter_score = keyword_score(repo_text_blob(repo), family_keywords)
            if prefilter_score == 0:
                continue

            local_path = synced_checkouts.get(repo["name"])
            if local_path is None:
                local_path = sync_repo_checkout(repo, CACHE_ROOT)
                synced_checkouts[repo["name"]] = local_path
            relevant_files = pick_relevant_files(local_path, experiment)
            source_files = [path for path in relevant_files if path.suffix.lower() in SOURCE_SUFFIXES]
            io = extract_io(relevant_files)
            algorithms = extract_algorithm_markers(relevant_files, repo)
            track, score = classify_track(experiment, repo, relevant_files, io, algorithms)
            include, reason = candidate_status(repo, track, source_files, io, algorithms, score, family_name=experiment["name"])
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
    print("探索候補を抽出しました")


def eval_command(_args: argparse.Namespace) -> None:
    experiment_registry = load_yaml_like(EXPERIMENT_REGISTRY_PATH)
    for experiment in experiment_registry.get("experiments", []):
        rankings: dict[str, list[dict[str, Any]]] = {}
        for implementation in experiment.get("implementations", []):
            repo_root = Path(implementation["local_path"])
            all_relevant_files = [repo_root / relative_path for relative_path in implementation.get("relevant_files", [])]
            relevant_files = [path for path in all_relevant_files if path.exists()]
            missing_files = [path for path in all_relevant_files if not path.exists()]
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
                "ranking_policy": "総合 = 0.50 ベンチマーク準備度/品質 + 0.25 可読性 + 0.25 拡張性",
                "evaluated_file_count": len(relevant_files),
                "missing_relevant_files": [str(path.relative_to(repo_root)) for path in missing_files[:20]],
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
    print("抽出済み実装を評価しました")


def format_markdown_list(values: list[str]) -> str:
    if not values:
        return "なし"
    return ", ".join(values)


def render_experiments_doc(registry: dict[str, Any]) -> str:
    lines = [
        "# 探索結果",
        "",
        f"生成日時: {registry.get('generated_at')}",
        "",
    ]
    for experiment in registry.get("experiments", []):
        exp_name = experiment["name"]
        lines.extend(
            [
                f"## {experiment_title(exp_name)} (`{exp_name}`)",
                "",
                experiment_summary(exp_name, experiment.get("problem_statement", "")),
                "",
            ]
        )
        for track in experiment.get("tracks", []):
            track_name = track["name"]
            track_heading = f"{track_title(track_name)} (`{track_name}`)"
            desc = TRACK_DESCRIPTIONS.get(track_name, track.get("description", ""))
            implementations = [
                item
                for item in experiment.get("implementations", [])
                if item.get("track") == track_name
            ]
            lines.extend(
                [
                    f"### {track_heading}",
                    "",
                    f"- 説明: {desc}",
                    f"- 実装数: {len(implementations)}",
                ]
            )
            if implementations:
                lines.extend(
                    [
                        "",
                        "| リポジトリ | スコア | I/O | アルゴリズム |",
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
                lines.extend(["", "- 主要差分:"])
                for diff in diffs[:3]:
                    pair = " vs ".join(diff["pair"])
                    common_inputs = format_markdown_list(diff["common_inputs"])
                    left_only = format_markdown_list(diff["left_only_algorithms"][:3])
                    right_only = format_markdown_list(diff["right_only_algorithms"][:3])
                    lines.append(
                        f"  - {pair}: 共通入力 {common_inputs}; アルゴリズム差分 {left_only} / {right_only}"
                    )
            lines.append("")

        rejected = experiment.get("rejected_candidates", [])
        if rejected:
            lines.extend(["### 除外候補", ""])
            for item in rejected[:10]:
                lines.append(f"- {item['repo']}: {reason_label(item.get('reason'))}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_decisions_doc(registry: dict[str, Any]) -> str:
    lines = [
        "# 暫定判断",
        "",
        f"生成日時: {registry.get('generated_at')}",
        "",
    ]
    for experiment in registry.get("experiments", []):
        exp_name = experiment["name"]
        lines.append(f"## {experiment_title(exp_name)} (`{exp_name}`)")
        lines.append("")
        rankings = experiment.get("track_rankings", {})
        interfaces = experiment.get("interfaces", {})
        for track in experiment.get("tracks", []):
            track_name = track["name"]
            ranked = rankings.get(track_name, [])
            lines.append(f"### {track_title(track_name)} (`{track_name}`)")
            lines.append("")
            if not ranked:
                lines.append("- 抽出候補がまだ無いため、このトラックでは採用済み実装がありません。")
                lines.append("")
                continue
            winner = ranked[0]["repo"]
            winner_impl = next(
                item
                for item in experiment["implementations"]
                if item["repo"] == winner and item.get("track") == track_name
            )
            interface = interfaces.get(track_name, {})
            lines.append(
                f"- 暫定採用: `{winner}`。これは現時点の比較基準であり、恒久的な標準ではありません。"
            )
            lines.append(
                f"- 現時点の採用理由: 総合スコア {winner_impl['evaluation']['overall_score']}、インターフェース {format_markdown_list(interface.get('input', []))} -> {format_markdown_list(interface.get('output', []))}、主要アルゴリズム {format_markdown_list(winner_impl.get('algorithms', [])[:4])}。"
            )
            others = [item["repo"] for item in ranked[1:3]]
            if others:
                lines.append(
                    f"- 比較継続: {', '.join(f'`{name}`' for name in others)}。異なるアルゴリズム上の選択肢を保持するためです。"
                )
            rejected = [item for item in experiment.get("rejected_candidates", []) if item.get("track") == track_name]
            if rejected:
                sample = rejected[0]
                lines.append(f"- 今回は採用しない: `{sample['repo']}`。理由: {reason_label(sample.get('reason'))}。")
            lines.append("- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_interfaces_doc(registry: dict[str, Any]) -> str:
    lines = [
        "# インターフェース候補",
        "",
        "このリポジトリでは、比較を経ても残った最小共有 I/O 契約を整理します。",
        "",
        f"生成日時: {registry.get('generated_at')}",
        "",
    ]
    for experiment in registry.get("experiments", []):
        exp_name = experiment["name"]
        lines.append(f"## {experiment_title(exp_name)} (`{exp_name}`)")
        lines.append("")
        for track in experiment.get("tracks", []):
            track_name = track["name"]
            interface = experiment.get("interfaces", {}).get(track_name)
            if not interface:
                continue
            lines.append(f"### {track_title(track_name)} (`{track_name}`)")
            lines.append("")
            lines.append(f"- 入力: {format_markdown_list(interface.get('input', []))}")
            lines.append(f"- 任意入力: {format_markdown_list(interface.get('optional_input', []))}")
            lines.append(f"- 出力: {format_markdown_list(interface.get('output', []))}")
            lines.append(f"- 任意出力: {format_markdown_list(interface.get('optional_output', []))}")
            lines.append(f"- 共通アルゴリズム指標: {format_markdown_list(interface.get('algorithm_markers', []))}")
            rankings = experiment.get("track_rankings", {}).get(track_name, [])
            if rankings:
                lines.append(f"- 現在の基準系統: {rankings[0]['repo']} を暫定的な安定参照とします。")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


EXPERIMENT_TITLES: dict[str, str] = {
    "lidar_stack_exploration": "LiDAR スタック",
    "robotics_algorithms_exploration": "ロボティクスアルゴリズム",
    "gnss_positioning_exploration": "GNSS 測位",
    "pointcloud_processing_exploration": "点群処理",
}

EXPERIMENT_SUMMARIES: dict[str, str] = {
    "lidar_stack_exploration": "公開 LiDAR 自己位置推定・LiDAR SLAM・LiDAR+IMU SLAM 実装を 1 つの探索ファミリとして比較する。",
    "robotics_algorithms_exploration": "ロボティクス基盤アルゴリズムの多言語実装を比較する（フィルタ、経路計画、SLAM 基礎）。",
    "gnss_positioning_exploration": "GNSS および複合センサ測位の実装を比較する。",
    "pointcloud_processing_exploration": "点群の分析・変換・処理ツールを比較する。",
}

TRACK_TITLES: dict[str, str] = {
    "lidar_localization": "LiDAR 自己位置推定",
    "lidar_slam": "LiDAR SLAM",
    "lidar_imu_slam": "LiDAR+IMU SLAM",
    "state_estimation": "状態推定",
    "path_planning": "経路計画",
    "scan_matching": "スキャンマッチング",
    "gnss_processing": "GNSS 処理",
    "multi_sensor_positioning": "複合測位",
    "pointcloud_analysis": "点群分析",
    "pointcloud_transformation": "点群変換",
    "pointcloud_to_model": "点群モデル化",
}

TRACK_DESCRIPTIONS: dict[str, str] = {
    "lidar_localization": "点群マップに対する自己位置推定",
    "lidar_slam": "LiDAR 単独によるオドメトリと地図構築",
    "lidar_imu_slam": "LiDAR と IMU を使う慣性融合オドメトリと地図構築",
    "state_estimation": "フィルタリング・状態推定 (EKF, UKF, Particle Filter 等)",
    "path_planning": "経路・動作計画 (RRT, A*, DWA 等)",
    "scan_matching": "点群レジストレーション・スキャンマッチング (ICP, NDT 等)",
    "gnss_processing": "GNSS 信号処理・測位 (RTK, PPP 等)",
    "multi_sensor_positioning": "GNSS + IMU/Wheel 複合測位",
    "pointcloud_analysis": "点群の分析・評価・可視化",
    "pointcloud_transformation": "点群のフィルタリング・変換・差分検出",
    "pointcloud_to_model": "点群から BIM/IFC・セマンティックモデルへの変換",
}

REJECTION_REASON_LABELS: dict[str, str] = {
    "no_source_files": "ソースファイルが見つからない",
    "weak_problem_match": "対象課題との一致が弱い",
    "out_of_scope_domain": "探索対象の領域外",
    "no_lidar_input_signal": "LiDAR 入力信号が見つからない",
    "missing_pose_output": "Pose 出力が見つからない",
    "supporting_component_only": "補助コンポーネント寄りで単体比較に向かない",
    "missing_imu_input": "IMU 入力が見つからない",
    "preprocessing_only": "前処理専用で主処理を持たない",
    "no_known_algorithm": "既知アルゴリズムの信号が見つからない",
    "belongs_to_lidar_family": "LiDAR 系探索ファミリに属する",
    "belongs_to_pointcloud_family": "点群処理系探索ファミリに属する",
    "belongs_to_gnss_family": "GNSS 系探索ファミリに属する",
    "not_algorithm_implementation": "アルゴリズム実装ではない",
    "no_gnss_signal": "GNSS 関連の信号が見つからない",
    "primarily_slam": "主用途が SLAM 寄り",
    "no_pointcloud_signal": "点群処理の信号が見つからない",
    "primarily_other_domain": "主用途が別領域",
}


def experiment_title(name: str) -> str:
    return EXPERIMENT_TITLES.get(name, name)


def experiment_summary(name: str, fallback: str) -> str:
    return EXPERIMENT_SUMMARIES.get(name, fallback)


def track_title(name: str) -> str:
    return TRACK_TITLES.get(name, name)


def reason_label(reason: str | None) -> str:
    if not reason:
        return "理由不明"
    return REJECTION_REASON_LABELS.get(reason, reason)


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_index_html(registry: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.append("""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>rsasaki-hub</title>
<style>
:root { --bg: #0d1117; --fg: #e6edf3; --muted: #8b949e; --border: #30363d; --accent: #58a6ff; --green: #3fb950; --card: #161b22; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background: var(--bg); color: var(--fg); line-height: 1.6; padding: 2rem; max-width: 960px; margin: 0 auto; }
h1 { font-size: 1.8rem; margin-bottom: 0.3rem; }
h2 { font-size: 1.3rem; margin-top: 2rem; margin-bottom: 0.8rem; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 0.3rem; }
h3 { font-size: 1.05rem; margin-top: 1.2rem; margin-bottom: 0.5rem; }
p, li { color: var(--fg); }
.subtitle { color: var(--muted); margin-bottom: 2rem; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
table { width: 100%; border-collapse: collapse; margin: 0.8rem 0; }
th, td { padding: 0.5rem 0.8rem; border: 1px solid var(--border); text-align: left; }
th { background: var(--card); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.03em; color: var(--muted); }
td { font-size: 0.9rem; }
tr:hover td { background: var(--card); }
.score { font-weight: 700; font-variant-numeric: tabular-nums; }
.winner { color: var(--green); }
.tag { display: inline-block; padding: 0.1rem 0.45rem; margin: 0.1rem; border-radius: 3px; font-size: 0.75rem; background: var(--card); border: 1px solid var(--border); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 1rem 1.2rem; margin: 0.8rem 0; }
.diff-label { font-size: 0.8rem; color: var(--muted); }
.io { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.82rem; }
.rejected { color: var(--muted); font-size: 0.85rem; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.8rem; }
</style>
</head>
<body>

<h1>rsasaki-hub</h1>
<p class="subtitle"><code>rsasaki0109</code> の公開リポジトリを横断比較する探索ハブ</p>

<div class="card">
<div class="diff-label">スコアについて</div>
<p>各リポジトリのスコア (0〜100) は以下の 3 指標の加重平均です。実行ベンチマークではなく、ソースコードの静的解析による代理評価です。</p>
<table style="margin-top:0.5rem">
<thead><tr><th>指標</th><th>重み</th><th>内容</th></tr></thead>
<tbody>
<tr><td>ベンチマーク準備度</td><td>50%</td><td>README / docs に精度・速度の記述があるか、ベンチマーク用ファイルが存在するか</td></tr>
<tr><td>可読性</td><td>25%</td><td>ファイル数、LOC、分岐数、最大関数サイズ、コメント率などのヒューリスティック</td></tr>
<tr><td>拡張性</td><td>25%</td><td>モジュール分割、設定ファイル、公開 API、ハードコード数などのヒューリスティック</td></tr>
</tbody>
</table>
<p style="margin-top:0.4rem;color:var(--muted);font-size:0.85rem">スコアが高い = 「比較・検証を進めやすい実装」であり、「実運用で最強」ではありません。</p>
</div>
""")

    for experiment in registry.get("experiments", []):
        exp_name = experiment["name"]
        title = experiment_title(exp_name)
        parts.append(f'<h2>&#9670; {_html_escape(title)}</h2>')
        parts.append(f'<p class="subtitle"><code>{_html_escape(exp_name)}</code></p>')
        parts.append(f'<p>{_html_escape(experiment_summary(exp_name, experiment.get("problem_statement", "")))}</p>')

        rankings = experiment.get("track_rankings", {})
        interfaces = experiment.get("interfaces", {})

        for track in experiment.get("tracks", []):
            track_name = track["name"]
            desc = TRACK_DESCRIPTIONS.get(track_name, track.get("description", ""))
            implementations = [
                item for item in experiment.get("implementations", [])
                if item.get("track") == track_name
            ]
            if not implementations:
                continue

            parts.append(f'<h3>{_html_escape(track_title(track_name))} <code>{_html_escape(track_name)}</code></h3>')
            parts.append(f'<p>{_html_escape(desc)}</p>')

            # ランキング表
            ranked = rankings.get(track_name, [])
            top_repo = ranked[0]["repo"] if ranked else None
            parts.append('<table><thead><tr><th>リポジトリ</th><th>スコア</th><th>主要アルゴリズム</th></tr></thead><tbody>')
            for impl in sorted(implementations, key=lambda x: x.get("evaluation", {}).get("overall_score", 0), reverse=True):
                score = impl.get("evaluation", {}).get("overall_score", "-")
                is_winner = impl["repo"] == top_repo
                score_cls = 'score winner' if is_winner else 'score'
                algos = "".join(f'<span class="tag">{_html_escape(a)}</span>' for a in impl.get("algorithms", [])[:4])
                repo_name = _html_escape(impl["repo"])
                parts.append(f'<tr><td><a href="https://github.com/rsasaki0109/{impl["repo"]}">{repo_name}</a></td><td class="{score_cls}">{score}</td><td>{algos}</td></tr>')
            parts.append('</tbody></table>')

            # I/O 契約カード
            iface = interfaces.get(track_name)
            if iface:
                inp = ", ".join(iface.get("input", [])) or "なし"
                opt_inp = ", ".join(iface.get("optional_input", []))
                out = ", ".join(iface.get("output", [])) or "なし"
                opt_out = ", ".join(iface.get("optional_output", []))
                io_line = f'入力: {inp}'
                if opt_inp:
                    io_line += f' &nbsp;|&nbsp; 任意: {opt_inp}'
                io_line += f'<br>出力: {out}'
                if opt_out:
                    io_line += f' &nbsp;|&nbsp; 任意: {opt_out}'
                ref = ranked[0]["repo"] if ranked else "N/A"
                parts.append(f'<div class="card"><div class="diff-label">最小 I/O 契約</div><p class="io">{io_line}</p><p>暫定採用: <strong>{_html_escape(ref)}</strong></p></div>')

    parts.append(f"""
<footer>
  <p>生成日時 {registry.get('generated_at', '')} / <a href="https://github.com/rsasaki0109/rsasaki-hub">rsasaki-hub</a></p>
</footer>

</body>
</html>
""")
    return "\n".join(parts)


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
    (ROOT / "docs" / "index.html").write_text(render_index_html(experiment_registry), encoding="utf-8")
    print("docs / interfaces / index.html を再生成しました")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="rsasaki-hub の探索制御 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="公開リポジトリを registry/repos.yaml へ同期")
    sync_parser.add_argument("--owner", default="rsasaki0109")
    sync_parser.add_argument("--token")
    sync_parser.set_defaults(func=sync_command)

    extract_parser = subparsers.add_parser("extract", help="探索候補とヒューリスティック情報を抽出")
    extract_parser.set_defaults(func=extract_command)

    eval_parser = subparsers.add_parser("eval", help="抽出済み候補を評価")
    eval_parser.set_defaults(func=eval_command)

    synth_parser = subparsers.add_parser("synthesize", help="インターフェース候補とドキュメントを生成")
    synth_parser.set_defaults(func=synthesize_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
