---
title: "GNSS"
type: "llm_article"
concept: "gnss"
generated_at: "2026-04-05"
source_count: 17
---

# GNSS（Global Navigation Satellite System）

衛星信号を利用した測位システムの総称。GPS (米), GLONASS (露), Galileo (欧), QZSS (日) などを含む。ロボティクスでは屋外 [[localization]] の基盤であり、[[imu]] やホイールオドメトリとの融合で精度を高める。

## 測位手法

### 単独測位 (SPP)
疑似距離のみで位置を計算。精度は数メートル級。`gnssplusplus-library` が C++ でフル実装しており、rsasaki-hub の `gnss_processing` トラックで暫定採用 (スコア: 75.16)。

### RTK (Real-Time Kinematic)
搬送波位相を利用し、基準局からの補正でセンチメートル級精度を実現。`gnssplusplus-library` が RTK をサポート。論文では RTK on 30,000 km of North American Highways (2019) が大規模実証。5G-Aided RTK (2023) は GNSS 不通環境での補完を提案。

### PPP (Precise Point Positioning)
精密暦と精密時計を使い、単独局でセンチメートル級を目指す。`gnssplusplus-library` が PPP と CLAS (みちびき補強) に対応。

### NLOS 対策
都市部ではマルチパスや NLOS (Non-Line-of-Sight) が精度を劣化させる。3D LiDAR Aided GNSS NLOS Mitigation (2022) は [[lidar]] 点群で衛星可視性を判定し、NLOS 衛星を除外する手法。

## rsasaki0109 の GNSS 実装

| リポジトリ | 手法 | 特徴 |
|---|---|---|
| `gnssplusplus-library` | RTK/PPP/CLAS | モダン C++ ツールキット、RINEX/RTCM 対応 |
| `gnss_gpu` | GPU 信号処理 | CUDA による GNSS 信号処理ライブラリ |
| `RTKLIB` | 全方式 | 定番 OSS のフォーク |
| `gnss_imu_wheel_localizer` | GNSS+IMU+Wheel | Autoware 向け複合測位 |
| `kalman_filter_localization_ros2` | GNSS+IMU Kalman | ROS2 Kalman Filter 測位 |
| `GNSS-Radar` | 可視化 | 衛星配置の Web 可視化ツール |

## SLAM との融合

Time-Relative RTK-GNSS (2023) は GNSS 測定をポーズグラフのループ閉合として組み込む。`lidarslam_ros2` は NavSatFix を入力に持ち、GNSS 情報を地図構築に利用可能。

## 関連コンセプト

[[localization]] | [[imu]] | [[state_estimation]] | [[slam]] | [[datasets]]
