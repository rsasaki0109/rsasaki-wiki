---
title: "Simulation"
type: "llm_article"
concept: "simulation"
generated_at: "2026-04-05"
source_count: 1
---

# Simulation

実ロボットを使わずにアルゴリズムの開発・検証を行うためのシミュレーション環境。[[slam]]、[[localization]]、[[control]] の開発効率を大幅に向上させる。

## rsasaki0109 の実装

### roboclaw-rs
Rust ベースのロボティクスワークスペース。シミュレーション環境と [[ros]] フックを備え、モータ制御のテストが可能。

### virtual-tukuba-challenge-ros2
筑波チャレンジの ROS2 シミュレーションワークスペース。実大会の環境を仮想空間で再現し、ナビゲーションアルゴリズムの開発に使用。

### gs-sim2real
3D Gaussian Splatting を使った Sim-to-Real 再構成プレイグラウンド。実環境の 3D モデルを構築し、シミュレーション用の環境生成に応用可能。

### particle_filtering_model_predictive_control
Particle Filter + MPC の Python シミュレーション。[[state_estimation]] と [[control]] の統合を仮想環境で検証。

## Sim-to-Real Gap

シミュレーションと実環境の差異は常に課題。`gs-sim2real` のアプローチ (実データから高品質 3D モデル生成) はこのギャップを縮める一つの方向性。[[datasets]] との組み合わせで、より現実的なベンチマークが可能になる。

## 関連コンセプト

[[ros]] | [[control]] | [[datasets]] | [[slam]] | [[deep_learning]]
