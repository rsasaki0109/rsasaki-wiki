from __future__ import annotations

import re
from pathlib import Path


SOURCE_SUFFIXES = {".py", ".c", ".cc", ".cpp", ".h", ".hpp", ".rs"}
BRANCH_PATTERN = re.compile(r"\b(if|else|elif|switch|case|for|while|catch)\b")
IMPORT_PATTERN = re.compile(r"^\s*(import |from |#include )", re.MULTILINE)
PY_FUNCTION_PATTERN = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
CXX_FUNCTION_PATTERN = re.compile(
    r"^\s*(?:template\s*<[^>]+>\s*)?(?:[A-Za-z_:<>~*&]+\s+)+([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:const)?\s*(?:\{|$)",
    re.MULTILINE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def function_names(text: str, suffix: str) -> list[str]:
    if suffix == ".py":
        return PY_FUNCTION_PATTERN.findall(text)
    return [
        name
        for name in CXX_FUNCTION_PATTERN.findall(text)
        if name not in {"if", "for", "while", "switch", "return"}
    ]


def largest_function_span(text: str, suffix: str) -> int:
    lines = text.splitlines()
    if suffix == ".py":
        indices = [idx for idx, line in enumerate(lines) if PY_FUNCTION_PATTERN.search(line)]
    else:
        indices = [idx for idx, line in enumerate(lines) if CXX_FUNCTION_PATTERN.search(line)]

    if not indices:
        return 0

    spans: list[int] = []
    for current, nxt in zip(indices, indices[1:] + [len(lines)]):
        spans.append(nxt - current)
    return max(spans, default=0)


def evaluate(files: list[Path]) -> dict[str, float | int]:
    source_files = [path for path in files if path.suffix in SOURCE_SUFFIXES]
    nonempty_loc = 0
    comment_lines = 0
    branch_keywords = 0
    import_count = 0
    function_count = 0
    max_function_size = 0
    largest_file_loc = 0

    for path in source_files:
        text = read_text(path)
        lines = text.splitlines()
        stripped = [line.strip() for line in lines]
        nonempty = [line for line in stripped if line]
        nonempty_loc += len(nonempty)
        comment_lines += sum(
            1 for line in stripped if line.startswith("#") or line.startswith("//") or line.startswith("/*")
        )
        branch_keywords += len(BRANCH_PATTERN.findall(text))
        import_count += len(IMPORT_PATTERN.findall(text))
        function_count += len(function_names(text, path.suffix))
        max_function_size = max(max_function_size, largest_function_span(text, path.suffix))
        largest_file_loc = max(largest_file_loc, len(nonempty))

    comment_ratio = round(comment_lines / max(nonempty_loc, 1), 3)
    score = 100.0
    score -= min(nonempty_loc / 80.0, 25.0)
    score -= min(branch_keywords / 10.0, 20.0)
    score -= min(import_count / 15.0, 15.0)
    score -= min(max_function_size / 20.0, 20.0)
    score += min(comment_ratio * 20.0, 10.0)
    score = max(0.0, min(100.0, round(score, 2)))

    return {
        "source_files": len(source_files),
        "nonempty_loc": nonempty_loc,
        "comment_ratio": comment_ratio,
        "branch_keywords": branch_keywords,
        "import_count": import_count,
        "function_count": function_count,
        "largest_file_loc": largest_file_loc,
        "largest_function_span": max_function_size,
        "score": score,
    }

