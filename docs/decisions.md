# Decisions

Generated at: 2026-04-04T21:34:41+00:00

## lidar_stack_exploration

### lidar_localization

- Temporary reference: `amcl_3d`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 90.22, interface Imu, Odometry, PointCloud2, Pose -> Path, PointCloud2, Pose, algorithms AMCL, CLAS, PID, NDT.
- Kept experimental: `lidar_localization_ros2` because they preserve alternative algorithmic choices.
- Not adopted now: `gaussian_particle_filter` because no_lidar_input_signal.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### lidar_slam

- Temporary reference: `lidarslam_ros2`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 83.97, interface PointCloud2 -> Path, PointCloud2, Pose, algorithms Submap, LoopClosure, SLAM, PoseGraph.
- Kept experimental: `littleslam_ros2`, `li_slam_ros2` because they preserve alternative algorithmic choices.
- Not adopted now: `CloudAnalyzer` because no_lidar_input_signal.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### lidar_imu_slam

- Temporary reference: `localization_zoo`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 84.33, interface Imu, Odometry, PointCloud2 -> Odometry, Path, algorithms ICP, LIO, GICP, VoxelGrid.
- Kept experimental: `FAST_LIO` because they preserve alternative algorithmic choices.
- Not adopted now: `imu_estimator` because out_of_scope_domain.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

## robotics_algorithms_exploration

### state_estimation

- Temporary reference: `imu_estimator`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 41.5, interface Imu, Odometry -> Path, Pose, algorithms EKF, CLAS.
- Kept experimental: `quaternion-based_kalman_filter`, `particle_filtering_model_predictive_control` because they preserve alternative algorithmic choices.
- Not adopted now: `kalman_filter_localization_ros2` because belongs_to_gnss_family.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### path_planning

- Temporary reference: `simple_visual_slam`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 78.19, interface none -> Path, algorithms CLAS, LoopClosure, SLAM, NDT.
- Kept experimental: `CudaRobotics`, `rust_robotics` because they preserve alternative algorithmic choices.
- Not adopted now: `company-technology-genealogy` because not_algorithm_implementation.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### scan_matching

- Temporary reference: `NormalDistributionTransform2D`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 36.44, interface none -> none, algorithms NDT, SLAM.
- Not adopted now: `glim` because belongs_to_lidar_family.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

## gnss_positioning_exploration

### gnss_processing

- Temporary reference: `gnssplusplus-library`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 75.16, interface NavSatFix, Path, Pose -> Path, NavSatFix, algorithms PPP, RTK, CLAS, RTCM.
- Kept experimental: `gnss_gpu`, `q-method` because they preserve alternative algorithmic choices.
- Not adopted now: `CudaRobotics` because no_gnss_signal.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### multi_sensor_positioning

- Temporary reference: `kalman_filter_localization_ros2`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 45.77, interface Imu, Odometry, Pose -> Pose, algorithms EKF, Kalman, Odometry, NDT.
- Kept experimental: `gnss_imu_wheel_localizer` because they preserve alternative algorithmic choices.
- Not adopted now: `amcl_3d` because no_gnss_signal.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

## pointcloud_processing_exploration

### pointcloud_analysis

- Temporary reference: `CloudAnalyzer`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 79.22, interface Path -> Path, algorithms CLAS, VoxelGrid, ICP, GICP.
- Not adopted now: `github-curator` because weak_problem_match.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### pointcloud_transformation

- Temporary reference: `construction-diff`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 83.92, interface Path, PointCloud2, LaserScan -> Path, PointCloud2, algorithms VoxelGrid, ICP, CLAS, RANSAC.
- Kept experimental: `tree-trunk-mapper`, `dynamic-3d-object-removal` because they preserve alternative algorithmic choices.
- Not adopted now: `amcl_3d` because no_pointcloud_signal.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.

### pointcloud_to_model

- Temporary reference: `pointcloud2ifc`. This is the current working reference, not a permanent standard.
- Why it wins now: overall score 59.48, interface Path, PointCloud2 -> Path, algorithms CLAS, VoxelGrid, Segmentation, RANSAC.
- Kept experimental: `bim-quality-checker`, `gs-sim2real` because they preserve alternative algorithmic choices.
- Not adopted now: `forest-panoptic-nav` because no_pointcloud_signal.
- Re-run trigger: when a new public repo appears, when an extracted repo changes its I/O shape, or when a real runtime benchmark harness is added.
