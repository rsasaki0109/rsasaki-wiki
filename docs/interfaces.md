# インターフェース候補

このリポジトリでは、比較を経ても残った最小共有 I/O 契約を整理します。

生成日時: 2026-04-10T09:30:59+00:00

## LiDAR スタック (`lidar_stack_exploration`)

### LiDAR 自己位置推定 (`lidar_localization`)

- 入力: Imu, Odometry, PointCloud2, Pose
- 任意入力: Path
- 出力: Path, PointCloud2, Pose
- 任意出力: なし
- 共通アルゴリズム指標: CLAS, NDT, Odometry, SLAM, ICP
- 現在の基準系統: amcl_3d を暫定的な安定参照とします。

### LiDAR SLAM (`lidar_slam`)

- 入力: PointCloud2
- 任意入力: Imu, MapArray, Odometry, NavSatFix, Pose
- 出力: Path, PointCloud2, Pose
- 任意出力: MapArray
- 共通アルゴリズム指標: SLAM, Submap, LoopClosure, PoseGraph, VoxelGrid
- 現在の基準系統: lidarslam_ros2 を暫定的な安定参照とします。

### LiDAR+IMU SLAM (`lidar_imu_slam`)

- 入力: Imu, Odometry, PointCloud2
- 任意入力: なし
- 出力: Path
- 任意出力: Odometry, PointCloud2
- 共通アルゴリズム指標: LIO, Odometry, Inertial, ICP, VoxelGrid
- 現在の基準系統: localization_zoo を暫定的な安定参照とします。

## ロボティクスアルゴリズム (`robotics_algorithms_exploration`)

### 状態推定 (`state_estimation`)

- 入力: Imu, Odometry
- 任意入力: なし
- 出力: Path, Pose
- 任意出力: なし
- 共通アルゴリズム指標: CLAS, ParticleFilter, Kalman, EKF, MPC
- 現在の基準系統: imu_estimator を暫定的な安定参照とします。

### 経路計画 (`path_planning`)

- 入力: なし
- 任意入力: なし
- 出力: Path
- 任意出力: Pose
- 共通アルゴリズム指標: SLAM, MPC, AStar, LoopClosure, EKF
- 現在の基準系統: simple_visual_slam を暫定的な安定参照とします。

### スキャンマッチング (`scan_matching`)

- 入力: なし
- 任意入力: なし
- 出力: Path
- 任意出力: なし
- 共通アルゴリズム指標: NDT, SLAM, CLAS, LoopClosure, ICP
- 現在の基準系統: NormalDistributionTransform2D を暫定的な安定参照とします。

## GNSS 測位 (`gnss_positioning_exploration`)

### GNSS 処理 (`gnss_processing`)

- 入力: Path, PointCloud2
- 任意入力: なし
- 出力: Path
- 任意出力: なし
- 共通アルゴリズム指標: RTK, CLAS, RINEX, QZSS, PPP
- 現在の基準系統: gnssplusplus-library を暫定的な安定参照とします。

### 複合測位 (`multi_sensor_positioning`)

- 入力: Imu, Odometry, Pose
- 任意入力: NavSatFix
- 出力: Pose
- 任意出力: Imu, Odometry, Path
- 共通アルゴリズム指標: Kalman, EKF, Odometry, CLAS, NDT
- 現在の基準系統: kalman_filter_localization_ros2 を暫定的な安定参照とします。

## 点群処理 (`pointcloud_processing_exploration`)

### 点群分析 (`pointcloud_analysis`)

- 入力: Path
- 任意入力: なし
- 出力: Path
- 任意出力: なし
- 共通アルゴリズム指標: CLAS, VoxelGrid, ICP, GICP, RTK
- 現在の基準系統: CloudAnalyzer を暫定的な安定参照とします。

### 点群変換 (`pointcloud_transformation`)

- 入力: Path, PointCloud2, LaserScan
- 任意入力: Odometry
- 出力: Path, PointCloud2
- 任意出力: LaserScan, Pose
- 共通アルゴリズム指標: CLAS, NDT, VoxelGrid, RANSAC, Downsampling
- 現在の基準系統: construction-diff を暫定的な安定参照とします。

### 点群モデル化 (`pointcloud_to_model`)

- 入力: Path, PointCloud2
- 任意入力: なし
- 出力: Path
- 任意出力: なし
- 共通アルゴリズム指標: CLAS, NDT, Semantic, Segmentation, VoxelGrid
- 現在の基準系統: pointcloud2ifc を暫定的な安定参照とします。
