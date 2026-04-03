from __future__ import annotations

from collections import Counter


def most_common(values: list[str], limit: int = 3) -> list[str]:
    counter = Counter(values)
    return [item for item, _count in counter.most_common(limit)]


def synthesize_track_interface(track_name: str, implementations: list[dict]) -> dict:
    inputs: list[str] = []
    outputs: list[str] = []
    algorithms: list[str] = []
    for implementation in implementations:
        inputs.extend(implementation.get("io", {}).get("inputs", []))
        outputs.extend(implementation.get("io", {}).get("outputs", []))
        algorithms.extend(implementation.get("algorithms", []))

    common_inputs = set(implementations[0].get("io", {}).get("inputs", [])) if implementations else set()
    common_outputs = set(implementations[0].get("io", {}).get("outputs", [])) if implementations else set()
    for implementation in implementations[1:]:
        common_inputs &= set(implementation.get("io", {}).get("inputs", []))
        common_outputs &= set(implementation.get("io", {}).get("outputs", []))

    minimal_inputs = sorted(common_inputs) or most_common(inputs)
    minimal_outputs = sorted(common_outputs) or most_common(outputs, limit=2)
    optional_inputs = [item for item in most_common(inputs, limit=6) if item not in minimal_inputs]
    optional_outputs = [item for item in most_common(outputs, limit=4) if item not in minimal_outputs]

    return {
        "track": track_name,
        "input": minimal_inputs,
        "optional_input": optional_inputs,
        "output": minimal_outputs,
        "optional_output": optional_outputs,
        "algorithm_markers": most_common(algorithms, limit=5),
    }

