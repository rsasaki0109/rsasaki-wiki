# Decisions

Generated at: 2026-04-03T04:52:49+00:00

## lidar_stack_exploration

### lidar_localization

- Temporary reference: `amcl_3d`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 90.22, interface Imu, Odometry, PointCloud2, Pose -> Path, PointCloud2, Pose, algorithms AMCL, NDT, Odometry, LoopClosure.
- Kept experimental: `lidar_localization_ros2` because they preserve alternative algorithmic choices.
- Not adopted now: `NormalDistributionTransform2D` because no_lidar_input_signal.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### lidar_slam

- Temporary reference: `lidarslam_ros2`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 83.97, interface PointCloud2 -> Pose, algorithms Submap, LoopClosure, PoseGraph, VoxelGrid.
- Kept experimental: `glim`, `littleslam_ros2` because they preserve alternative algorithmic choices.
- Not adopted now: `CloudAnalyzer` because no_lidar_input_signal.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### lidar_imu_slam

- Temporary reference: `localization_zoo`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 84.33, interface Imu, Odometry, PointCloud2 -> Odometry, Path, algorithms ICP, LIO, GICP, VoxelGrid.
- Kept experimental: `FAST_LIO` because they preserve alternative algorithmic choices.
- Not adopted now: `imu_estimator` because out_of_scope_domain.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.
