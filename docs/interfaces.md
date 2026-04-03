# Interfaces

This repo stabilizes the smallest shared I/O contract that survived comparison.

Generated at: 2026-04-03T04:52:49+00:00

## lidar_stack_exploration

### lidar_localization

- Input: Imu, Odometry, PointCloud2, Pose
- Optional input: Path
- Output: Path, PointCloud2, Pose
- Optional output: none
- Common algorithm markers: NDT, Odometry, ICP, AMCL, LoopClosure
- Current lineage: amcl_3d is the temporary stabilized reference.

### lidar_slam

- Input: PointCloud2
- Optional input: Imu, Odometry, MapArray, NavSatFix, Pose
- Output: Pose
- Optional output: Path, PointCloud2, MapArray
- Common algorithm markers: Submap, LoopClosure, PoseGraph, VoxelGrid, Deskew
- Current lineage: lidarslam_ros2 is the temporary stabilized reference.

### lidar_imu_slam

- Input: Imu, Odometry, PointCloud2
- Optional input: Path
- Output: Odometry, Path
- Optional output: PointCloud2, Pose
- Common algorithm markers: LIO, Odometry, Inertial, ICP, LoopClosure
- Current lineage: localization_zoo is the temporary stabilized reference.
