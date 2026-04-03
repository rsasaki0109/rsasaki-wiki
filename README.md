# rsasaki-hub

`rsasaki-hub` is the exploration control plane for the public repositories under `rsasaki0109`.

This repository is not a shared library and not a permanent best-practice vault. It exists to speed up exploration across repositories, keep comparable experiments in one place, and leave behind evidence for why one implementation is temporarily preferred over another.

## Purpose

- Collect the current public repositories owned by `rsasaki0109`
- Extract comparable implementations for a narrow problem slice
- Evaluate them with repeatable heuristics
- Synthesize only the smallest shared interface that survives comparison
- Record experiments and decisions as exploration logs

## Relationship To Other Repositories

The public repositories are the concrete implementations. They stay disposable.

This repository tracks:

- which repositories exist
- which ones solve the same problem
- how their I/O shapes overlap
- where the algorithmic differences live
- why a temporary reference implementation is chosen

The current first experiment family is:

- lidar localization
- lidar slam
- lidar + imu slam

## Layout

- `registry/`: repo metadata and extracted experiment state
- `ingestors/`: GitHub collection and local checkout logic
- `evaluator/`: repeatable benchmark, readability, and extensibility heuristics
- `synthesizer/`: minimal interface and implementation diff generation
- `docs/`: generated exploration logs
- `cli/`: `expctl` entrypoint

`registry/*.yaml` uses JSON-compatible YAML so the repo stays dependency-free and runnable with the Python standard library.

## Usage

Run from the repository root:

```bash
python3 cli/expctl.py sync
python3 cli/expctl.py extract
python3 cli/expctl.py eval
python3 cli/expctl.py synthesize
```

What each command does:

- `expctl sync`: fetch the current public repository list for `rsasaki0109` and write `registry/repos.yaml`
- `expctl extract`: shallow-clone relevant repositories into `.cache/repos/` and extract problem, I/O, topic, and algorithm signals into `registry/experiments.yaml`
- `expctl eval`: compute repeatable proxy metrics for benchmark readiness, readability, and extensibility
- `expctl synthesize`: generate the current minimal interfaces and rewrite `docs/experiments.md`, `docs/decisions.md`, and `docs/interfaces.md`

## Process Rules

- Do not abstract first
- Always preserve multiple implementations
- Optimize for comparability before elegance
- Treat every concrete implementation as disposable
- Keep exploration logs current in the same change as the code
