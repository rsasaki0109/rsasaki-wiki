---
title: "ROS"
type: "llm_article"
concept: "ros"
generated_at: "2026-04-05"
source_count: 40
---

# ROS (Robot Operating System)

ロボットソフトウェア開発のためのミドルウェアフレームワーク。rsasaki0109 の実装の大半は ROS2 (主に Humble / Iron) をベースにしており、rsasaki-hub の探索パイプラインも ROS2 のメッセージ型 (PointCloud2, Imu, Odometry 等) を I/O 契約の基本単位として使っている。

## rsasaki-hub における ROS の役割

rsasaki-hub の `expctl.py extract` は ROS2 のメッセージ型パターンを手がかりに実装の I/O を抽出する。具体的には:
- `create_subscription<sensor_msgs::msg::PointCloud2>` → Input: PointCloud2
- `create_publisher<nav_msgs::msg::Path>` → Output: Path
- Topic 名 (`/scan`, `/imu`, `/odom`) からもセンサ入力を推定

## ROS2 ベースの主要実装

### [[slam]] / [[localization]]
`lidarslam_ros2`, `li_slam_ros2`, `amcl_3d`, `lidar_localization_ros2`, `glim`, `littleslam_ros2` — いずれも ROS2 ノードとして実装。

### [[gnss]] / [[imu]]
`gnss_imu_wheel_localizer`, `kalman_filter_localization_ros2` — Autoware 連携を想定した ROS2 測位ノード。

### ツール
`bagx` は ROS2 rosbag の後処理分析エンジン。eval、比較、可視化を CLI で行う。`ndt_omp_ros2` は NDT の ROS2 ラッパー。

### シミュレーション
`virtual-tukuba-challenge-ros2` は筑波チャレンジの ROS2 シミュレーションワークスペース。`roboclaw-rs` は Rust + ROS2 のロボティクスワークスペース。

## ROS に依存しない実装

`CudaRobotics`, `rust_robotics`, `mathematical_robotics` は ROS 非依存のアルゴリズム実装。`gnssplusplus-library` も standalone。rsasaki-hub の robotics_algorithms_exploration はこれらを比較対象としている。

## 関連コンセプト

[[slam]] | [[lidar]] | [[localization]] | [[imu]] | [[gnss]]
