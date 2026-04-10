---
title: "IMU"
type: "llm_article"
concept: "imu"
generated_at: "2026-04-05"
source_count: 25
---

# IMU（Inertial Measurement Unit）

加速度計とジャイロスコープを組み合わせた慣性センサ。ロボティクスでは [[slam]]、[[localization]]、[[state_estimation]] において、高頻度 (100〜1000Hz) の動き情報を提供する補助センサとして不可欠。

## 役割

### SLAM / Odometry における IMU
LiDAR-Inertial SLAM では、IMU で scan 間の初期姿勢推定とデスキュー (歪み補正) を行う。`FAST_LIO` は iterated Kalman Filter で IMU と LiDAR を 密結合 に融合し、高速な LIO を実現。`li_slam_ros2` も NDT/GICP + IMU の 密結合 構成。

### Preintegration
連続する IMU 測定を事前積分し、最適化変数を減らす手法。`localization_zoo` や `mathematical_robotics` で実装されている。グラフベース [[slam]] の IMU ファクターとして使われる。

### 姿勢推定
`imu_estimator` はジャイロバイアス補正付きの姿勢推定器。`quaternion-based_kalman_filter` は四元数表現での Kalman Filter 実装。いずれも IMU 単体での姿勢推定を扱う。

## rsasaki0109 の IMU 関連実装

| リポジトリ | 用途 |
|---|---|
| `FAST_LIO` | LiDAR-Inertial Odometry (iterated Kalman) |
| `localization_zoo` | 複数 LIO variant の比較環境 |
| `li_slam_ros2` | LiDAR-Inertial SLAM |
| `imu_estimator` | 姿勢推定 (ジャイロバイアス補正) |
| `kalman_filter_localization_ros2` | GNSS+IMU Kalman 測位 |
| `gnss_imu_wheel_localizer` | GNSS+IMU+Wheel 複合測位 |
| `mathematical_robotics` | IMU preintegration の C++ 実装 |
| `lidar_undistortion` | IMU を使った LiDAR 歪み補正 |

## IMU ノイズモデル

IMU の誤差はバイアス（ゆっくりドリフト）とホワイトノイズに分解される。アラン分散で特性評価し、フィルタのプロセスノイズに反映する。SLAM Handbook (`slam-handbook-python`, `slam-handbook-public-release`) でこの理論を学べる。

## 関連論文

- An Enhanced LiDAR-Inertial SLAM System (2022): ロボット自己位置推定向け改良型 LIO
- OKVIS2-X (2025): 視覚慣性 SLAM に LiDAR と GNSS を統合

## 関連コンセプト

[[slam]] | [[lidar]] | [[localization]] | [[state_estimation]] | [[gnss]] | [[control]]
