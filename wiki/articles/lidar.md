---
title: "LiDAR"
type: "llm_article"
concept: "lidar"
generated_at: "2026-04-05"
source_count: 35
---

# LiDAR

LiDAR (Light Detection and Ranging) は、レーザー光の反射を利用して周囲の 3D 形状を計測するセンサである。ロボティクスでは [[slam]]、[[localization]]、[[point_cloud_processing]] の基盤入力として広く使われる。

## センサの種類と特性

回転式 (Velodyne, Ouster)、ソリッドステート (Livox)、2D スキャナ (SICK, Hokuyo) に大別される。rsasaki0109 の実装は主に 3D 回転式を想定しており、`PointCloud2` メッセージを標準入力とする。`littleslam_ros2` のみ 2D `LaserScan` にも対応。

## 点群処理パイプライン

1. **歪み補正**: スキャン中のロボット移動による歪みを [[imu]] やオドメトリで補正。`laser_deskew`、`lidar_undistortion` が専用実装。
2. **ダウンサンプリング**: VoxelGrid フィルタで点群密度を削減。ほぼ全ての SLAM 実装で前処理として使用。
3. **スキャンマッチング**: ICP、NDT、GICP で連続スキャン間の変位を推定。`NormalDistributionTransform2D` は NDT の Python 教材実装。`ndt_omp_ros2` は OpenMP 並列化版。
4. **地図構築**: サブマップの蓄積とループ閉合による大域的整合。

## rsasaki0109 の LiDAR 関連実装

**SLAM 系**: `lidarslam_ros2` (暫定採用)、`li_slam_ros2`、`glim`、`littleslam_ros2`
**Localization 系**: `amcl_3d` (暫定採用)、`lidar_localization_ros2`、`lidar_localizer`
**LiDAR+IMU 系**: `FAST_LIO`、`localization_zoo` (暫定採用)
**ツール系**: `laser_deskew`、`lidar_undistortion`、`ndt_omp_ros2`

## NeRF / Gaussian Splatting との融合

LiDAR-NeRF (2023) は LiDAR 点群から NeRF を学習し、新視点の LiDAR スキャンを合成する。3D Gaussian Splatting ベースの手法も登場しており、`gs-sim2real` はこの方向の実験場。従来の幾何ベース [[slam]] との性能比較が今後の課題。

## 関連コンセプト

[[slam]] | [[localization]] | [[imu]] | [[point_cloud_processing]] | [[ros]]
