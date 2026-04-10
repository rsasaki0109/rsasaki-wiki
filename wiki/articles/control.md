---
title: "制御"
type: "llm_article"
concept: "control"
generated_at: "2026-04-05"
source_count: 6
---

# 制御

ロボットを目標状態に追従させるための制御理論。[[path_planning]] で計画された経路を実際に走行するために、モータやアクチュエータへの指令を生成する。

## 主要手法

### PID 制御
比例・積分・微分の 3 項で制御。最も基本的で広く使われる。`CudaRobotics` と `rust_robotics` に実装。

### LQR（Linear Quadratic Regulator）
線形システムに対する最適制御。状態フィードバックゲインを Riccati 方程式で計算。`CudaRobotics`, `rust_robotics` に実装。

### MPC（Model Predictive Control）
未来の状態を予測し、有限ホライズンで最適化。制約を直接扱える。`particle_filtering_model_predictive_control` は [[state_estimation]] (Particle Filter) と MPC を統合した Python シミュレーション。

## ロボティクス実装

`roboclaw-rs` は Rust ベースのロボティクスワークスペースで、モータ制御 (Roboclaw) の [[ros]] インターフェースを提供。`bagx` は ROS2 bag の後処理で制御ログの分析に利用可能。

## [[state_estimation]] との関係

制御と推定は双対関係にある。Kalman Filter (推定) と LQR (制御) は同じ Riccati 方程式を解く。`mathematical_robotics` はこの両方を C++ で実装。

## 関連コンセプト

[[path_planning]] | [[state_estimation]] | [[ros]] | [[simulation]]
