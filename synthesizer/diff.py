from __future__ import annotations

from itertools import combinations


def build_pairwise_diffs(implementations: list[dict]) -> list[dict]:
    diffs: list[dict] = []
    for left, right in combinations(sorted(implementations, key=lambda item: item["repo"]), 2):
        left_inputs = set(left.get("io", {}).get("inputs", []))
        right_inputs = set(right.get("io", {}).get("inputs", []))
        left_outputs = set(left.get("io", {}).get("outputs", []))
        right_outputs = set(right.get("io", {}).get("outputs", []))
        left_algorithms = set(left.get("algorithms", []))
        right_algorithms = set(right.get("algorithms", []))
        diffs.append(
            {
                "pair": [left["repo"], right["repo"]],
                "common_inputs": sorted(left_inputs & right_inputs),
                "common_outputs": sorted(left_outputs & right_outputs),
                "left_only_algorithms": sorted(left_algorithms - right_algorithms),
                "right_only_algorithms": sorted(right_algorithms - left_algorithms),
            }
        )
    return diffs

