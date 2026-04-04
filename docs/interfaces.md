# Interfaces

This repo stabilizes the smallest shared I/O contract that survived comparison.

Generated at: 2026-04-04T21:34:41+00:00

## lidar_stack_exploration

### lidar_localization

- Input: Imu, Odometry, PointCloud2, Pose
- Optional input: Path
- Output: Path, PointCloud2, Pose
- Optional output: none
- Common algorithm markers: CLAS, NDT, Odometry, SLAM, ICP
- Current lineage: amcl_3d is the temporary stabilized reference.

### lidar_slam

- Input: PointCloud2
- Optional input: Imu, MapArray, Odometry, NavSatFix, Pose
- Output: Path, PointCloud2, Pose
- Optional output: MapArray
- Common algorithm markers: SLAM, Submap, LoopClosure, PoseGraph, VoxelGrid
- Current lineage: lidarslam_ros2 is the temporary stabilized reference.

### lidar_imu_slam

- Input: Imu, Odometry, PointCloud2
- Optional input: Path
- Output: Odometry, Path
- Optional output: PointCloud2, Pose
- Common algorithm markers: LIO, Odometry, Inertial, ICP, LoopClosure
- Current lineage: localization_zoo is the temporary stabilized reference.

## robotics_algorithms_exploration

### state_estimation

- Input: Imu, Odometry
- Optional input: none
- Output: Path, Pose
- Optional output: none
- Common algorithm markers: CLAS, ParticleFilter, Kalman, EKF, MPC
- Current lineage: imu_estimator is the temporary stabilized reference.

### path_planning

- Input: none
- Optional input: none
- Output: Path
- Optional output: none
- Common algorithm markers: LoopClosure, SLAM, DWA, CLAS, MPC
- Current lineage: simple_visual_slam is the temporary stabilized reference.

### scan_matching

- Input: none
- Optional input: none
- Output: none
- Optional output: none
- Common algorithm markers: NDT, SLAM
- Current lineage: NormalDistributionTransform2D is the temporary stabilized reference.

## gnss_positioning_exploration

### gnss_processing

- Input: NavSatFix, Path, Pose
- Optional input: PointCloud2
- Output: Path, NavSatFix
- Optional output: Pose
- Common algorithm markers: RTK, CLAS, RINEX, QZSS, PPP
- Current lineage: gnssplusplus-library is the temporary stabilized reference.

### multi_sensor_positioning

- Input: Imu, Odometry, Pose
- Optional input: NavSatFix
- Output: Pose
- Optional output: Imu, Odometry, Path
- Common algorithm markers: Kalman, EKF, Odometry, CLAS, NDT
- Current lineage: kalman_filter_localization_ros2 is the temporary stabilized reference.

## pointcloud_processing_exploration

### pointcloud_analysis

- Input: Path
- Optional input: none
- Output: Path
- Optional output: none
- Common algorithm markers: CLAS, VoxelGrid, ICP, GICP, RTK
- Current lineage: CloudAnalyzer is the temporary stabilized reference.

### pointcloud_transformation

- Input: Path, PointCloud2, LaserScan
- Optional input: Odometry
- Output: Path, PointCloud2
- Optional output: LaserScan, Pose
- Common algorithm markers: CLAS, NDT, VoxelGrid, Downsampling, RANSAC
- Current lineage: construction-diff is the temporary stabilized reference.

### pointcloud_to_model

- Input: Path, PointCloud2
- Optional input: none
- Output: Path
- Optional output: none
- Common algorithm markers: CLAS, NDT, Semantic, Segmentation, VoxelGrid
- Current lineage: pointcloud2ifc is the temporary stabilized reference.
