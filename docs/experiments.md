# Experiments

Generated at: 2026-04-04T21:34:41+00:00

## lidar_stack_exploration

Compare public lidar localization, lidar SLAM, and lidar+imu SLAM repositories under one exploration family.

### lidar_localization

- Description: Point-cloud-based localization against a map.
- Implementations: 2

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| amcl_3d | 90.22 | Imu, Odometry, Path, PointCloud2, Pose -> Path, PointCloud2, Pose | AMCL, CLAS, PID, NDT |
| lidar_localization_ros2 | 36.72 | Imu, Odometry, PointCloud2, Pose -> Path, PointCloud2, Pose | NDT, VoxelGrid, GICP, ICP |

- Key diffs:
  - amcl_3d vs lidar_localization_ros2: common input Imu, Odometry, PointCloud2, Pose; algorithm split AMCL, LoopClosure, PID / GICP, VoxelGrid

### lidar_slam

- Description: LiDAR-only odometry and mapping.
- Implementations: 3

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| lidarslam_ros2 | 83.97 | Imu, MapArray, NavSatFix, Odometry, PointCloud2 -> MapArray, NavSatFix, Path, PointCloud2, Pose | Submap, LoopClosure, SLAM, PoseGraph |
| li_slam_ros2 | 36.48 | Imu, MapArray, Odometry, PointCloud2, Pose -> Imu, MapArray, Odometry, Path, PointCloud2, Pose | VoxelGrid, Submap, SLAM, NDT |
| littleslam_ros2 | 42.74 | LaserScan, PointCloud2 -> Path, PointCloud2, Pose | SLAM, CLAS, ICP |

- Key diffs:
  - li_slam_ros2 vs lidarslam_ros2: common input Imu, MapArray, Odometry, PointCloud2; algorithm split GICP, ICP, IMUPreintegration / CLAS, LIO, RTK
  - li_slam_ros2 vs littleslam_ros2: common input PointCloud2; algorithm split GICP, IMUPreintegration, LoopClosure / CLAS
  - lidarslam_ros2 vs littleslam_ros2: common input PointCloud2; algorithm split LIO, LoopClosure, NDT / ICP

### lidar_imu_slam

- Description: LiDAR-inertial odometry and mapping.
- Implementations: 2

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| FAST_LIO | 52.26 | Imu, Odometry, PointCloud2 -> Odometry, Path, PointCloud2 | CLAS, LIO, EKF, Odometry |
| localization_zoo | 84.33 | Imu, Odometry, Path, PointCloud2 -> Odometry, Path, Pose | ICP, LIO, GICP, VoxelGrid |

- Key diffs:
  - FAST_LIO vs localization_zoo: common input Imu, Odometry, PointCloud2; algorithm split CLAS, EKF, Kalman / GICP, IMUPreintegration, NDT

### Rejected Candidates

- CloudAnalyzer: no_lidar_input_signal
- CudaRobotics: no_lidar_input_signal
- NormalDistributionTransform2D: no_lidar_input_signal
- PoseOptimizationSLAM3D: no_lidar_input_signal
- gaussian_particle_filter: no_lidar_input_signal
- gnss_imu_wheel_localizer: no_lidar_input_signal
- gnssplusplus-library: no_lidar_input_signal
- kalman_filter_localization_ros2: no_lidar_input_signal
- mathematical_robotics: no_lidar_input_signal
- ndt_omp_ros2: no_lidar_input_signal

## robotics_algorithms_exploration

Compare cross-language implementations of core robotics algorithms (filtering, path planning, SLAM basics).

### state_estimation

- Description: Filtering and state estimation algorithms (EKF, UKF, Particle Filter, etc.).
- Implementations: 5

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| gaussian_particle_filter | 33.64 | none -> none | ParticleFilter, Kalman |
| particle_filtering_model_predictive_control | 35.44 | none -> Path | MPC, ParticleFilter, CLAS |
| quaternion-based_kalman_filter | 38.64 | none -> none | Kalman, CLAS |
| mathematical_robotics | 32.91 | Imu, Odometry -> Path, Pose | IMUPreintegration, EKF, PoseGraph, CLAS |
| imu_estimator | 41.5 | Imu -> none | EKF, CLAS |

- Key diffs:
  - gaussian_particle_filter vs imu_estimator: common input none; algorithm split Kalman, ParticleFilter / CLAS, EKF
  - gaussian_particle_filter vs mathematical_robotics: common input none; algorithm split none / CLAS, EKF, ICP
  - gaussian_particle_filter vs particle_filtering_model_predictive_control: common input none; algorithm split Kalman / CLAS, MPC

### path_planning

- Description: Path and motion planning algorithms (RRT, A*, DWA, etc.).
- Implementations: 4

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| rust_robotics | 41.34 | none -> Path | MPC, LQR, AStar, LoopClosure |
| CudaRobotics | 63.29 | none -> Path | CLAS, LIO, RRT, AStar |
| roboclaw-rs | 27.62 | none -> Path | CLAS, LoopClosure, ICP, DWA |
| simple_visual_slam | 78.19 | none -> Path | CLAS, LoopClosure, SLAM, NDT |

- Key diffs:
  - CudaRobotics vs roboclaw-rs: common input none; algorithm split AMCL, AStar, Dijkstra / LoopClosure
  - CudaRobotics vs rust_robotics: common input none; algorithm split AMCL, CLAS, Dijkstra / EKF, Kalman, LQR
  - CudaRobotics vs simple_visual_slam: common input none; algorithm split AMCL, AStar, DWA / EKF, LoopClosure, MPC

### scan_matching

- Description: Point cloud registration and scan matching (ICP, NDT, etc.).
- Implementations: 1

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| NormalDistributionTransform2D | 36.44 | none -> none | NDT, SLAM |

### Rejected Candidates

- kalman_filter_localization_ros2: belongs_to_gnss_family
- amcl_3d: belongs_to_lidar_family
- glim: belongs_to_lidar_family
- li_slam_ros2: belongs_to_lidar_family
- lidar_localization_ros2: belongs_to_lidar_family
- lidarslam_ros2: belongs_to_lidar_family
- littleslam_ros2: belongs_to_lidar_family
- localization_zoo: belongs_to_lidar_family
- ndt_omp_ros2: belongs_to_lidar_family
- CloudAnalyzer: belongs_to_pointcloud_family

## gnss_positioning_exploration

Compare GNSS and multi-sensor positioning implementations.

### gnss_processing

- Description: Raw GNSS signal processing and positioning (RTK, PPP, code/carrier).
- Implementations: 4

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| gnssplusplus-library | 75.16 | NavSatFix, Path, Pose -> NavSatFix, Path, Pose | PPP, RTK, CLAS, RTCM |
| gnss_gpu | 53.86 | PointCloud2 -> Path | EKF, Pseudorange, RTK, RINEX |
| RTKLIB | 31.51 | none -> Path | RTK, RTCM, RINEX, CLAS |
| q-method | 35.98 | none -> none | none |

- Key diffs:
  - RTKLIB vs gnss_gpu: common input none; algorithm split AStar, AmbiguityResolution, NDT / EKF, LIO, LoopClosure
  - RTKLIB vs gnssplusplus-library: common input none; algorithm split AStar, AmbiguityResolution, NDT / Ionosphere, PID, Pseudorange
  - RTKLIB vs q-method: common input none; algorithm split AStar, AmbiguityResolution, CLAS / none

### multi_sensor_positioning

- Description: GNSS fused with IMU, wheel odometry, or other sensors.
- Implementations: 2

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| gnss_imu_wheel_localizer | 37.33 | Imu, NavSatFix, Odometry, Pose -> Imu, Odometry, Path, Pose | Kalman, EKF, Odometry, LoopClosure |
| kalman_filter_localization_ros2 | 45.77 | Imu, Odometry, Pose -> Pose | EKF, Kalman, Odometry, NDT |

- Key diffs:
  - gnss_imu_wheel_localizer vs kalman_filter_localization_ros2: common input Imu, Odometry, Pose; algorithm split LoopClosure / none

### Rejected Candidates

- CudaRobotics: no_gnss_signal
- PoseOptimizationSLAM3D: no_gnss_signal
- amcl_3d: no_gnss_signal
- gaussian_particle_filter: no_gnss_signal
- glim: no_gnss_signal
- imu_estimator: no_gnss_signal
- lidar_localization_ros2: no_gnss_signal
- lidar_localizer: no_gnss_signal
- lidar_undistortion: no_gnss_signal
- littleslam_ros2: no_gnss_signal

## pointcloud_processing_exploration

Compare point cloud analysis, transformation, and processing tools.

### pointcloud_analysis

- Description: Point cloud inspection, evaluation, and visualization.
- Implementations: 1

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| CloudAnalyzer | 79.22 | Path -> Path | CLAS, VoxelGrid, ICP, GICP |

### pointcloud_transformation

- Description: Point cloud filtering, object removal, diff, and format conversion.
- Implementations: 5

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| npy2pointcloud | 40.05 | Path -> Path | CLAS, NDT |
| dynamic-3d-object-removal | 51.26 | Path, PointCloud2 -> Path, PointCloud2 | VoxelGrid, CLAS, NDT, SLAM |
| construction-diff | 83.92 | none -> Path | VoxelGrid, ICP, CLAS, RANSAC |
| laser_deskew | 39.11 | LaserScan, Odometry -> LaserScan | Deskew, NDT, Odometry, CLAS |
| tree-trunk-mapper | 80.03 | Path, PointCloud2 -> Path, Pose | CLAS, RANSAC, NDT, Clustering |

- Key diffs:
  - construction-diff vs dynamic-3d-object-removal: common input none; algorithm split ICP, RANSAC / EKF, LoopClosure, NDT
  - construction-diff vs laser_deskew: common input none; algorithm split Downsampling, ICP, RANSAC / Deskew, NDT, Odometry
  - construction-diff vs npy2pointcloud: common input none; algorithm split Downsampling, ICP, RANSAC / NDT

### pointcloud_to_model

- Description: Point cloud to BIM/IFC or semantic model conversion.
- Implementations: 4

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| pointcloud2ifc | 59.48 | Path, PointCloud2 -> Path | CLAS, VoxelGrid, Segmentation, RANSAC |
| rohbau-annotator | 36.59 | none -> Path | CLAS, Semantic, Segmentation, NDT |
| bim-quality-checker | 58.59 | none -> Path | CLAS, NDT |
| gs-sim2real | 48.67 | Path -> Path | CLAS, NDT, LoopClosure, SLAM |

- Key diffs:
  - bim-quality-checker vs gs-sim2real: common input none; algorithm split none / LoopClosure, SLAM, Semantic
  - bim-quality-checker vs pointcloud2ifc: common input none; algorithm split none / Clustering, Downsampling, RANSAC
  - bim-quality-checker vs rohbau-annotator: common input none; algorithm split none / Segmentation, Semantic

### Rejected Candidates

- amcl_3d: no_pointcloud_signal
- bagx: no_pointcloud_signal
- forest-panoptic-nav: no_pointcloud_signal
- glim: no_pointcloud_signal
- transfrom_velocity: no_pointcloud_signal
- rsasaki0109-tweet-summaries: no_source_files
- gnssplusplus-library: primarily_other_domain
- lidarslam_ros2: primarily_other_domain
- localization_zoo: primarily_other_domain
- PoseOptimizationSLAM3D: weak_problem_match
