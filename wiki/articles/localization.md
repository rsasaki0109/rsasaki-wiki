---
title: "自己位置推定"
type: "llm_article"
concept: "localization"
generated_at: "2026-04-05"
source_count: 24
---

# 自己位置推定

事前に構築された地図上で、ロボットの現在位置と姿勢を推定する技術。[[slam]] が「地図構築 + 位置推定」を同時に行うのに対し、自己位置推定は既知地図を前提に位置推定へ特化する。

## 主要手法

### AMCL (Adaptive Monte Carlo Localization)
パーティクルフィルタベースの確率的位置推定。2D LiDAR + 占有格子地図で広く使われる標準手法。`amcl_3d` はこれを 3D 点群地図に拡張した実装で、rsasaki-hub の `lidar_localization` トラックで暫定採用 (スコア: 90.22)。

### NDT / GICP マッチング
現在のスキャンを地図に直接マッチングして位置を推定する。`lidar_localization_ros2` は NDT と GICP の両方をサポートし、VoxelGrid 前処理を含む。Autoware AI の `lidar_localizer` も同様のアプローチ。

### Kalman Filter ベース
[[gnss]] + [[imu]] + Wheel の複合測位。`kalman_filter_localization_ros2` は GNSS/IMU を Kalman Filter で融合。`gnss_imu_wheel_localizer` は Autoware 向けの 3 センサ融合実装。

### 視覚的位置推定
カメラ画像ベースの位置推定。`forest-place-recognition` は森林環境での季節不変な視覚的場所認識を扱う。ACE-SLAM (2024) は Scene Coordinate Regression によるニューラル implicit 表現を利用する。

## I/O 契約（`lidar_localization` トラック）

- **入力**: Imu, Odometry, PointCloud2, Pose
- **任意入力**: Path
- **出力**: Path, PointCloud2, Pose

## 比較軸

| 手法 | 入力 | 精度 | 計算量 | 代表実装 |
|---|---|---|---|---|
| AMCL | 点群 + 地図 + 初期位置 | 中〜高 | 低 | `amcl_3d` |
| NDT/GICP | 点群 + 地図 | 高 | 中 | `lidar_localization_ros2` |
| Kalman (GNSS+IMU) | 衛星 + 慣性 | 環境依存 | 低 | `kalman_filter_localization_ros2` |
| 視覚 | カメラ画像 | 環境依存 | 高 | `forest-place-recognition` |

## 関連コンセプト

[[slam]] | [[lidar]] | [[gnss]] | [[imu]] | [[state_estimation]] | [[point_cloud_processing]]
