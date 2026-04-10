# 暫定判断

生成日時: 2026-04-10T09:30:59+00:00

## LiDAR スタック (`lidar_stack_exploration`)

### LiDAR 自己位置推定 (`lidar_localization`)

- 暫定採用: `amcl_3d`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 90.22、インターフェース Imu, Odometry, PointCloud2, Pose -> Path, PointCloud2, Pose、主要アルゴリズム AMCL, CLAS, PID, NDT。
- 比較継続: `lidar_localization_ros2`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `gaussian_particle_filter`。理由: LiDAR 入力信号が見つからない。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

### LiDAR SLAM (`lidar_slam`)

- 暫定採用: `lidarslam_ros2`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 83.97、インターフェース PointCloud2 -> Path, PointCloud2, Pose、主要アルゴリズム Submap, LoopClosure, SLAM, PoseGraph。
- 比較継続: `littleslam_ros2`, `li_slam_ros2`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `CloudAnalyzer`。理由: LiDAR 入力信号が見つからない。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

### LiDAR+IMU SLAM (`lidar_imu_slam`)

- 暫定採用: `localization_zoo`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 92.81、インターフェース Imu, Odometry, PointCloud2 -> Path、主要アルゴリズム ICP, GICP, LIO, NDT。
- 比較継続: `FAST_LIO`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `imu_estimator`。理由: 探索対象の領域外。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

## ロボティクスアルゴリズム (`robotics_algorithms_exploration`)

### 状態推定 (`state_estimation`)

- 暫定採用: `imu_estimator`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 41.5、インターフェース Imu, Odometry -> Path, Pose、主要アルゴリズム EKF, CLAS。
- 比較継続: `quaternion-based_kalman_filter`, `particle_filtering_model_predictive_control`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `kalman_filter_localization_ros2`。理由: GNSS 系探索ファミリに属する。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

### 経路計画 (`path_planning`)

- 暫定採用: `simple_visual_slam`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 78.99、インターフェース なし -> Path、主要アルゴリズム CLAS, LoopClosure, SLAM, RANSAC。
- 比較継続: `CudaRobotics`, `rust_robotics`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `company-technology-genealogy`。理由: アルゴリズム実装ではない。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

### スキャンマッチング (`scan_matching`)

- 暫定採用: `NormalDistributionTransform2D`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 36.44、インターフェース なし -> Path、主要アルゴリズム NDT, SLAM。
- 比較継続: `roboclaw-rs`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `glim`。理由: LiDAR 系探索ファミリに属する。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

## GNSS 測位 (`gnss_positioning_exploration`)

### GNSS 処理 (`gnss_processing`)

- 暫定採用: `gnssplusplus-library`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 74.36、インターフェース Path, PointCloud2 -> Path、主要アルゴリズム PPP, RTK, CLAS, RTCM。
- 比較継続: `gnss_gpu`, `q-method`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `PoseOptimizationSLAM3D`。理由: GNSS 関連の信号が見つからない。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

### 複合測位 (`multi_sensor_positioning`)

- 暫定採用: `kalman_filter_localization_ros2`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 45.77、インターフェース Imu, Odometry, Pose -> Pose、主要アルゴリズム EKF, Kalman, Odometry, NDT。
- 比較継続: `gnss_imu_wheel_localizer`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `amcl_3d`。理由: GNSS 関連の信号が見つからない。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

## 点群処理 (`pointcloud_processing_exploration`)

### 点群分析 (`pointcloud_analysis`)

- 暫定採用: `CloudAnalyzer`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 79.22、インターフェース Path -> Path、主要アルゴリズム CLAS, VoxelGrid, ICP, GICP。
- 今回は採用しない: `github-curator`。理由: 対象課題との一致が弱い。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

### 点群変換 (`pointcloud_transformation`)

- 暫定採用: `construction-diff`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 83.92、インターフェース Path, PointCloud2, LaserScan -> Path, PointCloud2、主要アルゴリズム VoxelGrid, ICP, CLAS, RANSAC。
- 比較継続: `tree-trunk-mapper`, `dynamic-3d-object-removal`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `amcl_3d`。理由: 点群処理の信号が見つからない。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。

### 点群モデル化 (`pointcloud_to_model`)

- 暫定採用: `pointcloud2ifc`。これは現時点の比較基準であり、恒久的な標準ではありません。
- 現時点の採用理由: 総合スコア 59.48、インターフェース Path, PointCloud2 -> Path、主要アルゴリズム CLAS, VoxelGrid, Segmentation, RANSAC。
- 比較継続: `bim-quality-checker`, `gs-sim2real`。異なるアルゴリズム上の選択肢を保持するためです。
- 今回は採用しない: `forest-panoptic-nav`。理由: 点群処理の信号が見つからない。
- 再評価条件: 新しい公開リポジトリが現れたとき、抽出済みリポジトリの I/O 形状が変わったとき、実ランタイムのベンチマーク基盤が追加されたとき。
