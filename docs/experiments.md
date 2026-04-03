# Experiments

Generated at: 2026-04-03T04:52:49+00:00

## lidar_stack_exploration

Compare public lidar localization, lidar SLAM, and lidar+imu SLAM repositories under one exploration family.

### lidar_localization

- Description: Point-cloud-based localization against a map.
- Implementations: 2

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| amcl_3d | 90.22 | Imu, Odometry, Path, PointCloud2, Pose -> Path, PointCloud2, Pose | AMCL, NDT, Odometry, LoopClosure |
| lidar_localization_ros2 | 36.72 | Imu, Odometry, PointCloud2, Pose -> Path, PointCloud2, Pose | NDT, VoxelGrid, GICP, ICP |

- Key diffs:
  - amcl_3d vs lidar_localization_ros2: common input Imu, Odometry, PointCloud2, Pose; algorithm split AMCL, LoopClosure, ParticleFilter / GICP, VoxelGrid

### lidar_slam

- Description: LiDAR-only odometry and mapping.
- Implementations: 4

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| lidarslam_ros2 | 83.97 | Imu, MapArray, NavSatFix, Odometry, PointCloud2 -> MapArray, NavSatFix, Path, PointCloud2, Pose | Submap, LoopClosure, PoseGraph, VoxelGrid |
| li_slam_ros2 | 36.48 | Imu, MapArray, Odometry, PointCloud2, Pose -> Imu, MapArray, Odometry, Path, PointCloud2, Pose | VoxelGrid, Submap, NDT, ICP |
| glim | 45.78 | Imu, Odometry, PointCloud2 -> Pose | Submap, Odometry, VoxelGrid, ICP |
| littleslam_ros2 | 42.74 | LaserScan, PointCloud2 -> Path, PointCloud2, Pose | ICP |

- Key diffs:
  - glim vs li_slam_ros2: common input Imu, Odometry, PointCloud2; algorithm split VGICP / IMUPreintegration, NDT
  - glim vs lidarslam_ros2: common input Imu, Odometry, PointCloud2; algorithm split GICP, ICP, VGICP / IMUPreintegration, LIO, NDT
  - glim vs littleslam_ros2: common input PointCloud2; algorithm split Deskew, GICP, LoopClosure / none

### lidar_imu_slam

- Description: LiDAR-inertial odometry and mapping.
- Implementations: 2

| Repo | Score | I/O | Algorithms |
| --- | ---: | --- | --- |
| FAST_LIO | 52.26 | Imu, Odometry, PointCloud2 -> Odometry, Path, PointCloud2 | LIO, Odometry, Inertial, ICP |
| localization_zoo | 84.33 | Imu, Odometry, Path, PointCloud2 -> Odometry, Path, Pose | ICP, LIO, GICP, VoxelGrid |

- Key diffs:
  - FAST_LIO vs localization_zoo: common input Imu, Odometry, PointCloud2; algorithm split Kalman / GICP, IMUPreintegration, VGICP

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
