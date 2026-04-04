---
title: "BIM / Construction"
type: "llm_article"
concept: "bim_construction"
generated_at: "2026-04-05"
source_count: 8
---

# BIM / Construction (建設 BIM)

Building Information Modeling (BIM) と点群処理を組み合わせた建設現場のデジタル化技術。[[point_cloud_processing]] と [[lidar]] の応用分野であり、rsasaki0109 は建設現場向けの複数ツールを開発している。

## rsasaki0109 の実装群

### pointcloud2ifc
点群から IFC (Industry Foundation Classes) モデルを自動生成。セマンティックセグメンテーションで壁・床・柱などを識別し、BIM オブジェクトに変換。rsasaki-hub の pointcloud_to_model track で暫定採用 (score: 59.48)。

### bim-quality-checker
BIM モデルと実測点群の整合性を評価。設計と施工の乖離を検出し、品質レポートを生成。

### rohbau-annotator
Rohbau3D 建設現場点群にパノラマ画像経由でアノテーションを付与。手動ラベリングを効率化。

### construction-diff
異なる時点の点群スキャンを比較し、建設進捗を検出。rsasaki-hub の pointcloud_transformation track で暫定採用 (score: 83.92)。

### npy2pointcloud
Rohbau3D の .npy 形式点群を PLY/PCD/LAS に変換。他ツールとのデータ連携に使用。

## ワークフロー

```
LiDAR スキャン → npy2pointcloud → CloudAnalyzer (品質確認)
  → construction-diff (進捗比較)
  → pointcloud2ifc (BIM 生成) → bim-quality-checker (品質評価)
  → rohbau-annotator (アノテーション)
```

## GNSS との関連

建設現場での絶対座標取得に [[gnss]] RTK を使用。Automatic Operation of an Articulated Dump Truck (2025) は QZSS CLAS + RTK で建設車両の状態推定を行う論文。

## 関連コンセプト

[[point_cloud_processing]] | [[lidar]] | [[deep_learning]] | [[gnss]] | [[datasets]]
