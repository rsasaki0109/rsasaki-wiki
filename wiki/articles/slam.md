---
title: "SLAM"
type: "llm_article"
concept: "slam"
generated_at: "2026-04-05"
source_count: 35
---

# SLAM (Simultaneous Localization and Mapping)

SLAM は、未知環境の地図構築と自己位置推定を同時に行う技術である。ロボティクスにおける最も基本的かつ困難な問題の一つであり、[[lidar]]、[[computer_vision]]、[[imu]] など多様なセンサを入力として用いる。

## アルゴリズムの系譜

### フィルタベース
初期の SLAM は [[state_estimation]] の延長線上にあり、EKF-SLAM や FastSLAM (Particle Filter ベース) が代表的。計算量が状態次元の二乗に比例するため、大規模環境では実用的でない。

### グラフベース
現在の主流。ポーズグラフ最適化 (g2o, GTSAM) でループ閉合を含む全軌跡を一括最適化する。`lidarslam_ros2` はサブマップ + ループ検出 + PoseGraph の典型実装。`li_slam_ros2` は NDT/GICP を front-end に使う LiDAR-Inertial 構成。

### ニューラル SLAM
近年の研究では NeRF や 3D Gaussian Splatting を地図表現に用いる手法が登場。Photo-SLAM (2023)、MBA-SLAM (2024)、SLAM-Former (2025) が代表例。`simple_visual_slam` は従来型の Visual SLAM 実装だが、将来的にニューラル表現との比較対象となる。

## rsasaki0109 の実装群

| リポジトリ | 方式 | 特徴 |
|---|---|---|
| `lidarslam_ros2` | LiDAR Graph SLAM | サブマップ、ループ閉合、ベンチマーク付�� |
| `li_slam_ros2` | LiDAR-Inertial SLAM | NDT/GICP front-end + IMU tightly-coupled |
| `glim` | 汎用 Range-based SLAM | 拡張性重視、VoxelGrid + ICP |
| `littleslam_ros2` | 2D LiDAR SLAM | LittleSLAM の ROS2 ラッパー、ICP のみ |
| `FAST_LIO` | LiDAR-Inertial Odometry | iterated Kalman Filter、高速 |
| `localization_zoo` | 複数手法比較環境 | ICP/GICP/LIO の variant を内包 |

## 最小 I/O 契約

rsasaki-hub の探索結果から導出された最小契約:
- **Input**: PointCloud2
- **Optional Input**: Imu, Odometry, MapArray, NavSatFix, Pose
- **Output**: Pose
- **Optional Output**: Path, PointCloud2, MapArray

## 関連論文

- RTAB-Map: 大規模長時間運用向け LiDAR + Visual SLAM ライブラリ
- Swarm-SLAM: マルチロボット分散協調 SLAM
- Evolution of SLAM (2023): SLAM 手法の包括的サーベイ
- An Enhanced LiDAR-Inertial SLAM System (2022): ロボット自己位置推定向け改良型

## 関連コンセプト

[[lidar]] | [[localization]] | [[imu]] | [[point_cloud_processing]] | [[computer_vision]] | [[state_estimation]]
