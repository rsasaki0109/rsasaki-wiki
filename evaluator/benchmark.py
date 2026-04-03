from __future__ import annotations

import re
import time
from pathlib import Path


BENCHMARK_KEYWORDS = ("benchmark", "evaluation", "report", "rmse", "runtime", "latency", "fps", "hz", "accuracy")
NUMERIC_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)?)")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def metric_kind(line: str) -> str | None:
    lowered = line.lower()
    for keyword in BENCHMARK_KEYWORDS:
        if keyword in lowered:
            return keyword
    return None


def evaluate(files: list[Path]) -> dict[str, object]:
    started = time.perf_counter()
    benchmark_artifacts: list[str] = []
    metric_mentions: list[dict[str, object]] = []

    for path in files:
        lowered_path = path.as_posix().lower()
        if any(keyword in lowered_path for keyword in BENCHMARK_KEYWORDS):
            benchmark_artifacts.append(path.as_posix())

        if path.suffix not in {".md", ".py", ".sh", ".yaml", ".yml", ".cpp", ".hpp", ".h", ".txt"}:
            continue

        text = read_text(path)
        for line in text.splitlines():
            kind = metric_kind(line)
            if not kind:
                continue
            match = NUMERIC_PATTERN.search(line)
            metric_mentions.append(
                {
                    "kind": kind,
                    "value": float(match.group(1)) if match else None,
                    "line": line.strip()[:180],
                    "source": path.as_posix(),
                }
            )

    elapsed = round(time.perf_counter() - started, 4)
    artifact_count = len(set(benchmark_artifacts))
    metric_count = len(metric_mentions)
    quality_mentions = [m for m in metric_mentions if m["kind"] in {"rmse", "accuracy"} and m["value"] is not None]
    quality_signal = 0.0
    for metric in quality_mentions:
        if metric["kind"] == "rmse":
            quality_signal = max(quality_signal, max(0.0, 100.0 - float(metric["value"]) * 2.0))
        elif metric["kind"] == "accuracy":
            quality_signal = max(quality_signal, min(100.0, float(metric["value"])))

    maturity_signal = min(artifact_count * 12.0 + metric_count * 4.0, 100.0)
    score = round(min(100.0, quality_signal * 0.6 + maturity_signal * 0.4), 2)

    return {
        "analysis_runtime_seconds": elapsed,
        "benchmark_artifacts": sorted(set(benchmark_artifacts))[:10],
        "benchmark_artifact_count": artifact_count,
        "metric_mentions": metric_mentions[:10],
        "metric_count": metric_count,
        "quality_signal": round(quality_signal, 2),
        "score": score,
    }

