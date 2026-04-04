---
title: "State Estimation"
type: "llm_article"
concept: "state_estimation"
generated_at: "2026-04-05"
source_count: 11
---

# State Estimation (状態推定)

ノイズを含むセンサ観測から、システムの隠れた状態 (位置、速度、姿勢など) を推定する理論体系。[[localization]]、[[slam]]、[[control]] の基盤であり、ベイズ推定の枠組みで定式化される。

## 主要フィルタ

### Kalman Filter (KF)
線形ガウスシステムの最適推定器。Wikipedia 記事が 24,000 語超の詳細な解説を提供。`kalman_filter_localization_ros2` は GNSS+[[imu]] の測位に KF を適用。

### Extended Kalman Filter (EKF)
非線形システムへの KF 拡張。ヤコビアンで線形化する。`FAST_LIO` は iterated EKF で LiDAR-IMU 融合を実現。`mathematical_robotics` に C++ 実装あり。

### Unscented Kalman Filter (UKF)
シグマ点を用いた非線形フィルタ。線形化不要で EKF より精度が良い場合がある。`CudaRobotics` に CUDA 実装あり。

### Particle Filter (PF)
非線形・非ガウスに対応可能な Monte Carlo 法ベース。`gaussian_particle_filter` は Gaussian PF の Python 実装。`amcl_3d` ��� AMCL (Adaptive MCL) を 3D に拡張。`particle_filtering_model_predictive_control` は PF と [[control]] (MPC) の統合。

### 四元数 Kalman Filter
姿勢推定に特化。`quaternion-based_kalman_filter` が Python 実装。`imu_estimator` はジャイロバイアス補正付き。

## rsasaki0109 の実装マップ

| フィルタ | 実装 | 言語 |
|---|---|---|
| EKF | `mathematical_robotics`, `FAST_LIO` | C++ |
| EKF (CUDA) | `CudaRobotics` | CUDA/C++ |
| EKF (Rust) | `rust_robotics` | Rust |
| Particle Filter | `gaussian_particle_filter` | Python |
| AMCL (3D PF) | `amcl_3d` | C++ |
| PF + MPC | `particle_filtering_model_predictive_control` | Python |
| Quaternion KF | `quaternion-based_kalman_filter` | Python |
| IMU 姿勢 | `imu_estimator` | C++ |

## 関連コンセプト

[[localization]] | [[slam]] | [[imu]] | [[gnss]] | [[control]]
