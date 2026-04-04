---
title: "Point Cloud Processing"
type: "llm_article"
concept: "point_cloud_processing"
generated_at: "2026-04-05"
source_count: 14
---

# Point Cloud Processing (点群処理)

3D 点群データの取得・変換・解析を行う技術群。[[lidar]] スキャンの前処理から、BIM モデル変換、動的物体除去まで幅広い応用を持つ。

## 処理パイプライン

### フォーマット変換
`npy2pointcloud` は NumPy (.npy) 形式から PLY/PCD/LAS への変換ツール。Rohbau3D (建設現場) 点群を標準フォーマットに変換する用途。

### ダウンサンプリング・フィルタリング
VoxelGrid フィルタが標準手法。ほぼ全ての [[slam]] 実装が前処理で使用。`CloudAnalyzer` は点群の統計分析・品質評価を CLI で行うツール。

### スキャンマッチング
2 つの点群の位置合わせ。ICP (Iterative Closest Point)、NDT (Normal Distribution Transform)、GICP が代表的。`NormalDistributionTransform2D` は NDT の教材実装。`ndt_omp_ros2` は OpenMP 並列版。

### セグメンテーション
地面除去、物体分類、パノプティックセグメンテーション。`forest-panoptic-nav` は森林環境でのパノプティックセグメンテーションによるナビゲーション。

### 動的物体除去
`dynamic-3d-object-removal` は NumPy のみで動的物体を除去する軽量実装。3D バウンディングボックスと時系列フィルタで動的点を識別・除去。

### 差分検出
`construction-diff` は建設進捗を点群スキャンの比較で検出。時点間の形状変化を定量化する。

## BIM / IFC 連携

`pointcloud2ifc` は点群からセマンティックセグメンテーションを経て IFC (BIM) モデルを自動生成。`bim-quality-checker` は BIM モデルと点群の整合性を評価。`rohbau-annotator` はパノラマ画像経由で点群にアノテーションを付与。[[bim_construction]] 参照。

## rsasaki-hub での位置づけ

pointcloud_processing_exploration で 3 track に分類:
- **pointcloud_analysis**: `CloudAnalyzer` (暫定採用, score: 79.22)
- **pointcloud_transformation**: `construction-diff` (暫定採用, score: 83.92)
- **pointcloud_to_model**: `pointcloud2ifc` (暫定採用, score: 59.48)

## 関連コンセプト

[[lidar]] | [[slam]] | [[bim_construction]] | [[ros]] | [[deep_learning]]
