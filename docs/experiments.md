# 探索結果

生成日時: 2026-04-10T09:30:59+00:00

## LiDAR スタック (`lidar_stack_exploration`)

公開 LiDAR 自己位置推定・LiDAR SLAM・LiDAR+IMU SLAM 実装を 1 つの探索ファミリとして比較する。

### LiDAR 自己位置推定 (`lidar_localization`)

- 説明: 点群マップに対する自己位置推定
- 実装数: 2

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| amcl_3d | 90.22 | Imu, Odometry, Path, PointCloud2, Pose -> Path, PointCloud2, Pose | AMCL, CLAS, PID, NDT |
| lidar_localization_ros2 | 36.72 | Imu, Odometry, PointCloud2, Pose -> Path, PointCloud2, Pose | NDT, VoxelGrid, GICP, ICP |

- 主要差分:
  - amcl_3d vs lidar_localization_ros2: 共通入力 Imu, Odometry, PointCloud2, Pose; アルゴリズム差分 AMCL, LoopClosure, PID / GICP, VoxelGrid

### LiDAR SLAM (`lidar_slam`)

- 説明: LiDAR 単独によるオドメトリと地図構築
- 実装数: 3

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| lidarslam_ros2 | 83.97 | Imu, MapArray, NavSatFix, Odometry, PointCloud2 -> MapArray, NavSatFix, Path, PointCloud2, Pose | Submap, LoopClosure, SLAM, PoseGraph |
| li_slam_ros2 | 36.48 | Imu, MapArray, Odometry, PointCloud2, Pose -> Imu, MapArray, Odometry, Path, PointCloud2, Pose | VoxelGrid, Submap, SLAM, NDT |
| littleslam_ros2 | 42.74 | LaserScan, PointCloud2 -> Path, PointCloud2, Pose | SLAM, CLAS, ICP |

- 主要差分:
  - li_slam_ros2 vs lidarslam_ros2: 共通入力 Imu, MapArray, Odometry, PointCloud2; アルゴリズム差分 GICP, ICP, IMUPreintegration / CLAS, LIO, RTK
  - li_slam_ros2 vs littleslam_ros2: 共通入力 PointCloud2; アルゴリズム差分 GICP, IMUPreintegration, LoopClosure / CLAS
  - lidarslam_ros2 vs littleslam_ros2: 共通入力 PointCloud2; アルゴリズム差分 LIO, LoopClosure, NDT / ICP

### LiDAR+IMU SLAM (`lidar_imu_slam`)

- 説明: LiDAR と IMU を使う慣性融合オドメトリと地図構築
- 実装数: 2

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| FAST_LIO | 52.26 | Imu, Odometry, PointCloud2 -> Odometry, Path, PointCloud2 | CLAS, LIO, EKF, Odometry |
| localization_zoo | 92.81 | Imu, Odometry, PointCloud2 -> Path | ICP, GICP, LIO, NDT |

- 主要差分:
  - FAST_LIO vs localization_zoo: 共通入力 Imu, Odometry, PointCloud2; アルゴリズム差分 CLAS, EKF, Kalman / GICP, NDT, SMALL_GICP

### 除外候補

- CloudAnalyzer: LiDAR 入力信号が見つからない
- CudaRobotics: LiDAR 入力信号が見つからない
- NormalDistributionTransform2D: LiDAR 入力信号が見つからない
- PoseOptimizationSLAM3D: LiDAR 入力信号が見つからない
- gaussian_particle_filter: LiDAR 入力信号が見つからない
- gnss_imu_wheel_localizer: LiDAR 入力信号が見つからない
- gnssplusplus-library: LiDAR 入力信号が見つからない
- kalman_filter_localization_ros2: LiDAR 入力信号が見つからない
- mathematical_robotics: LiDAR 入力信号が見つからない
- ndt_omp_ros2: LiDAR 入力信号が見つからない

## ロボティクスアルゴリズム (`robotics_algorithms_exploration`)

ロボティクス基盤アルゴリズムの多言語実装を比較する（フィルタ、経路計画、SLAM 基礎）。

### 状態推定 (`state_estimation`)

- 説明: フィルタリング・状態推定 (EKF, UKF, Particle Filter 等)
- 実装数: 5

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| gaussian_particle_filter | 33.64 | なし -> なし | ParticleFilter, Kalman |
| particle_filtering_model_predictive_control | 35.44 | なし -> Path | MPC, ParticleFilter, CLAS |
| quaternion-based_kalman_filter | 38.64 | なし -> なし | Kalman, CLAS |
| mathematical_robotics | 32.91 | Imu, Odometry -> Path, Pose | IMUPreintegration, EKF, PoseGraph, CLAS |
| imu_estimator | 41.5 | Imu -> なし | EKF, CLAS |

- 主要差分:
  - gaussian_particle_filter vs imu_estimator: 共通入力 なし; アルゴリズム差分 Kalman, ParticleFilter / CLAS, EKF
  - gaussian_particle_filter vs mathematical_robotics: 共通入力 なし; アルゴリズム差分 なし / CLAS, EKF, ICP
  - gaussian_particle_filter vs particle_filtering_model_predictive_control: 共通入力 なし; アルゴリズム差分 Kalman / CLAS, MPC

### 経路計画 (`path_planning`)

- 説明: 経路・動作計画 (RRT, A*, DWA 等)
- 実装数: 3

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| rust_robotics | 48.75 | なし -> Path, Pose | MPC, AStar, LQR, SLAM |
| CudaRobotics | 63.29 | なし -> Path | CLAS, LIO, RRT, AStar |
| simple_visual_slam | 78.99 | なし -> Path | CLAS, LoopClosure, SLAM, RANSAC |

- 主要差分:
  - CudaRobotics vs rust_robotics: 共通入力 なし; アルゴリズム差分 AMCL, CLAS, Dijkstra / EKF, Kalman, LQR
  - CudaRobotics vs simple_visual_slam: 共通入力 なし; アルゴリズム差分 AMCL, AStar, DWA / EKF, LoopClosure, MPC
  - rust_robotics vs simple_visual_slam: 共通入力 なし; アルゴリズム差分 AStar, DWA, Kalman / CLAS, NDT, PID

### スキャンマッチング (`scan_matching`)

- 説明: 点群レジストレーション・スキャンマッチング (ICP, NDT 等)
- 実装数: 2

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| NormalDistributionTransform2D | 36.44 | なし -> なし | NDT, SLAM |
| roboclaw-rs | 27.62 | なし -> Path | CLAS, LoopClosure, ICP |

- 主要差分:
  - NormalDistributionTransform2D vs roboclaw-rs: 共通入力 なし; アルゴリズム差分 NDT, SLAM / CLAS, ICP, LoopClosure

### 除外候補

- kalman_filter_localization_ros2: GNSS 系探索ファミリに属する
- amcl_3d: LiDAR 系探索ファミリに属する
- glim: LiDAR 系探索ファミリに属する
- li_slam_ros2: LiDAR 系探索ファミリに属する
- lidar_localization_ros2: LiDAR 系探索ファミリに属する
- lidarslam_ros2: LiDAR 系探索ファミリに属する
- littleslam_ros2: LiDAR 系探索ファミリに属する
- localization_zoo: LiDAR 系探索ファミリに属する
- ndt_omp_ros2: LiDAR 系探索ファミリに属する
- CloudAnalyzer: 点群処理系探索ファミリに属する

## GNSS 測位 (`gnss_positioning_exploration`)

GNSS および複合センサ測位の実装を比較する。

### GNSS 処理 (`gnss_processing`)

- 説明: GNSS 信号処理・測位 (RTK, PPP 等)
- 実装数: 4

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| gnssplusplus-library | 74.36 | Path -> Path | PPP, RTK, CLAS, RTCM |
| gnss_gpu | 53.86 | PointCloud2 -> Path | EKF, Pseudorange, RTK, RINEX |
| RTKLIB | 31.51 | なし -> Path | RTK, RTCM, RINEX, CLAS |
| q-method | 35.98 | なし -> なし | なし |

- 主要差分:
  - RTKLIB vs gnss_gpu: 共通入力 なし; アルゴリズム差分 AStar, AmbiguityResolution, NDT / EKF, LIO, LoopClosure
  - RTKLIB vs gnssplusplus-library: 共通入力 なし; アルゴリズム差分 AStar, NDT / Ionosphere, PID, Pseudorange
  - RTKLIB vs q-method: 共通入力 なし; アルゴリズム差分 AStar, AmbiguityResolution, CLAS / なし

### 複合測位 (`multi_sensor_positioning`)

- 説明: GNSS + IMU/Wheel 複合測位
- 実装数: 2

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| gnss_imu_wheel_localizer | 37.33 | Imu, NavSatFix, Odometry, Pose -> Imu, Odometry, Path, Pose | Kalman, EKF, Odometry, LoopClosure |
| kalman_filter_localization_ros2 | 45.77 | Imu, Odometry, Pose -> Pose | EKF, Kalman, Odometry, NDT |

- 主要差分:
  - gnss_imu_wheel_localizer vs kalman_filter_localization_ros2: 共通入力 Imu, Odometry, Pose; アルゴリズム差分 LoopClosure / なし

### 除外候補

- PoseOptimizationSLAM3D: GNSS 関連の信号が見つからない
- amcl_3d: GNSS 関連の信号が見つからない
- gaussian_particle_filter: GNSS 関連の信号が見つからない
- glim: GNSS 関連の信号が見つからない
- imu_estimator: GNSS 関連の信号が見つからない
- lidar_localization_ros2: GNSS 関連の信号が見つからない
- lidar_localizer: GNSS 関連の信号が見つからない
- lidar_undistortion: GNSS 関連の信号が見つからない
- littleslam_ros2: GNSS 関連の信号が見つからない
- localization_zoo: GNSS 関連の信号が見つからない

## 点群処理 (`pointcloud_processing_exploration`)

点群の分析・変換・処理ツールを比較する。

### 点群分析 (`pointcloud_analysis`)

- 説明: 点群の分析・評価・可視化
- 実装数: 1

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| CloudAnalyzer | 79.22 | Path -> Path | CLAS, VoxelGrid, ICP, GICP |

### 点群変換 (`pointcloud_transformation`)

- 説明: 点群のフィルタリング・変換・差分検出
- 実装数: 5

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| npy2pointcloud | 40.05 | Path -> Path | CLAS, NDT |
| construction-diff | 83.92 | なし -> Path | VoxelGrid, ICP, CLAS, RANSAC |
| dynamic-3d-object-removal | 52.86 | Path, PointCloud2 -> Path, PointCloud2 | VoxelGrid, CLAS, NDT, SLAM |
| laser_deskew | 39.11 | LaserScan, Odometry -> LaserScan | Deskew, NDT, Odometry, CLAS |
| tree-trunk-mapper | 80.03 | Path, PointCloud2 -> Path, Pose | CLAS, RANSAC, NDT, Clustering |

- 主要差分:
  - construction-diff vs dynamic-3d-object-removal: 共通入力 なし; アルゴリズム差分 ICP, RANSAC / EKF, LoopClosure, NDT
  - construction-diff vs laser_deskew: 共通入力 なし; アルゴリズム差分 Downsampling, ICP, RANSAC / Deskew, NDT, Odometry
  - construction-diff vs npy2pointcloud: 共通入力 なし; アルゴリズム差分 Downsampling, ICP, RANSAC / NDT

### 点群モデル化 (`pointcloud_to_model`)

- 説明: 点群から BIM/IFC・セマンティックモデルへの変換
- 実装数: 4

| リポジトリ | スコア | I/O | アルゴリズム |
| --- | ---: | --- | --- |
| pointcloud2ifc | 59.48 | Path, PointCloud2 -> Path | CLAS, VoxelGrid, Segmentation, RANSAC |
| rohbau-annotator | 36.59 | なし -> Path | CLAS, Semantic, Segmentation, NDT |
| bim-quality-checker | 58.59 | なし -> Path | CLAS, NDT |
| gs-sim2real | 48.67 | Path -> Path | CLAS, NDT, LoopClosure, SLAM |

- 主要差分:
  - bim-quality-checker vs gs-sim2real: 共通入力 なし; アルゴリズム差分 なし / LoopClosure, SLAM, Semantic
  - bim-quality-checker vs pointcloud2ifc: 共通入力 なし; アルゴリズム差分 なし / Clustering, Downsampling, RANSAC
  - bim-quality-checker vs rohbau-annotator: 共通入力 なし; アルゴリズム差分 なし / Segmentation, Semantic

### 除外候補

- amcl_3d: 点群処理の信号が見つからない
- bagx: 点群処理の信号が見つからない
- forest-panoptic-nav: 点群処理の信号が見つからない
- glim: 点群処理の信号が見つからない
- transfrom_velocity: 点群処理の信号が見つからない
- rsasaki0109-tweet-summaries: ソースファイルが見つからない
- gnssplusplus-library: 主用途が別領域
- lidarslam_ros2: 主用途が別領域
- PoseOptimizationSLAM3D: 対象課題との一致が弱い
- github-curator: 対象課題との一致が弱い
