from __future__ import annotations

import re
from pathlib import Path


SOURCE_SUFFIXES = {".py", ".c", ".cc", ".cpp", ".h", ".hpp", ".rs"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".json", ".toml", ".xml"}
TOPIC_PATTERN = re.compile(r"['\"](/[A-Za-z0-9_/\-]+)['\"]")
PUBLIC_SURFACE_PATTERN = re.compile(r"\b(class|struct|interface|pub fn|virtual)\b")
FUNCTION_PATTERN = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def evaluate(files: list[Path], repo_root: Path) -> dict[str, float | int]:
    source_files = [path for path in files if path.suffix in SOURCE_SUFFIXES]
    config_files = [path for path in files if path.suffix in CONFIG_SUFFIXES or "launch" in path.parts]
    module_dirs = {path.parent.relative_to(repo_root).as_posix() for path in source_files if path.parent != repo_root}

    helper_units = 0
    public_surface = 0
    hard_coded_topics = 0

    for path in source_files:
        text = read_text(path)
        helper_units += sum(1 for name in FUNCTION_PATTERN.findall(text) if name not in {"if", "for", "while"})
        public_surface += len(PUBLIC_SURFACE_PATTERN.findall(text))
        hard_coded_topics += len(TOPIC_PATTERN.findall(text))

    orchestration_split = round(len(module_dirs) / max(len(source_files), 1), 3)
    score = 20.0
    score += min(len(module_dirs) * 8.0, 24.0)
    score += min(len(config_files) * 4.0, 16.0)
    score += min(helper_units * 0.8, 20.0)
    score += min(public_surface * 2.0, 20.0)
    score -= min(hard_coded_topics * 1.5, 20.0)
    score = max(0.0, min(100.0, round(score, 2)))

    return {
        "module_dirs": len(module_dirs),
        "config_files": len(config_files),
        "helper_units": helper_units,
        "public_surface_markers": public_surface,
        "hard_coded_topics": hard_coded_topics,
        "orchestration_split": orchestration_split,
        "score": score,
    }

