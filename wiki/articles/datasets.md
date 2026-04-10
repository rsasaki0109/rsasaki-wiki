---
title: "データセット"
type: "llm_article"
concept: "datasets"
generated_at: "2026-04-05"
source_count: 23
---

# データセット

ロボティクスのアルゴリズム評価に不可欠なベンチマークデータ。[[slam]]、[[localization]]、[[computer_vision]] の性能比較には、共通のデータセットでの定量評価が必要。

## rsasaki0109 のデータセット関連

### robotics-datasets-hub
自律ナビゲーション向けデータセットのカタログ。LiDAR、カメラ、IMU データを含む主要データセットへのリンクと説明を集約。

### tc-datasets
筑波チャレンジの実世界データセット。`virtual-tukuba-challenge-ros2` と組み合わせてベンチマークに使用可能。

### CloudAnalyzer
点群データの分析・評価 CLI ツール。データセットの品質チェックや統計分析に利用。

## 主要な外部データセット

| データセット | センサ | 用途 |
|---|---|---|
| KITTI | LiDAR + カメラ + GPS | SLAM、物体検出 |
| nuScenes | LiDAR + カメラ + Radar | 3D 検出、追跡 |
| Ford Highway RTK | GNSS RTK | RTK 測位評価 (30,000 km) |
| Rohbau3D | LiDAR | 建設現場点群 |

## rsasaki-hub のベンチマーク課題

plan.md で指摘されている通り、現在の `eval` は代理評価（README に benchmark 記述があるか等）であり、実際のデータセットでの実行時間 / 精度評価ではない。次のステップは:

1. トラックごとにベンチマーク契約を定義
2. データセットを 1 つ選定
3. 各実装のランナーを作成
4. 実行時間 / failure / 精度メトリクスを自動収集

`lidar_localization` トラックが最も対象範囲が狭く、最初のベンチマーク対象として適切。

## 関連コンセプト

[[slam]] | [[lidar]] | [[computer_vision]] | [[gnss]] | [[ros]]
