---
title: "Path Planning"
type: "llm_article"
concept: "path_planning"
generated_at: "2026-04-05"
source_count: 13
---

# Path Planning (経路計画)

スタートからゴールまでの障害物回避経路を計算する技術。[[localization]] で自己位置が分かり、[[slam]] で地図が構築された後に、実際にロボットを動かすための計画を立てるフェーズ。

## アルゴリズム分類

### グラフ探索
- **A***: 最適経路を保証するヒューリスティック探索。`CudaRobotics` に CUDA 実装、`rust_robotics` に Rust 実装。
- **Dijkstra**: A* のヒューリスティックなし版。同じく多言語実装あり。

### サンプリングベース
- **RRT (Rapidly-exploring Random Tree)**: 高次元空間向け。`CudaRobotics`, `rust_robotics` に実装。
- **PRM (Probabilistic Roadmap)**: 事前にロードマップを構築し、クエリ時に経路探索。

### リアクティブ
- **DWA (Dynamic Window Approach)**: 速度空間で障害物回避。`rust_robotics` に実装。
- **Potential Field**: 引力 (ゴール) と斥力 (障害物) の合成力で移動。

### 曲線ベース
- **Dubins Path**: 最小旋回半径制約下の最短経路。
- **Cubic Spline**: 滑らかな経路補間。

## 多言語実装比較

rsasaki-hub の robotics_algorithms_exploration で比較:

| リポジトリ | 言語 | アルゴリズム数 | 特徴 |
|---|---|---|---|
| `CudaRobotics` | CUDA/C++ | 20+ | GPU 並列化、高速 |
| `rust_robotics` | Rust | 15+ | PythonRobotics の Rust 移植 |
| `mathematical_robotics` | C++ | 10+ | MathematicalRobotics の C++ 移植 |

## [[control]] との境界

Path Planning は「どこを通るか」、[[control]] は「どう動くか」。MPC や LQR は両者にまたがる。`particle_filtering_model_predictive_control` は Particle Filter と MPC の統合例。

## 関連コンセプト

[[control]] | [[slam]] | [[localization]] | [[datasets]] | [[ros]]
