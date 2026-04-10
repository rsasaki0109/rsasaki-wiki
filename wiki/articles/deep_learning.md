---
title: "深層学習"
type: "llm_article"
concept: "deep_learning"
generated_at: "2026-04-05"
source_count: 21
---

# ロボティクスにおける深層学習

ロボティクスにおける深層学習の応用。[[slam]]、[[computer_vision]]、[[point_cloud_processing]] において、従来の幾何ベース手法を補完・置換する方向で急速に進展している。

## ニューラル SLAM

### NeRF / 3D Gaussian Splatting
Photo-SLAM (2023) はリアルタイムのフォトリアリスティック地図構築を実現する。MBA-SLAM (2024) はモーションブラーに対応した Gaussian Splatting SLAM。LiDAR-NeRF (2023) は [[lidar]] 点群から NeRF を学習する手法で、`gs-sim2real` は複数データセットでの 3DGS 再構成環境を提供する。

### トランスフォーマーベース
SLAM-Former (2025) は SLAM 全体を 1 つのトランスフォーマーに統合する試み。ACE-SLAM (2024) は Scene Coordinate Regression によるニューラルな implicit 表現を利用する。

### MLP ベース
MLP-SLAM (2024) は多層パーセプトロンベースの SLAM。従来手法と比較して軽量なニューラル表現を提案する。

## セマンティック理解

`pointcloud2ifc` は点群のセマンティックセグメンテーションから BIM モデルを生成。`forest-panoptic-nav` はパノプティックセグメンテーションによる森林ナビゲーション。`bim-quality-checker` は DL ベースの品質評価を含む。

## 技術系譜

`robotics-technology-genealogy` と `company-technology-genealogy` はロボティクス・AI 技術の系譜をインタラクティブに可視化。深層学習の各分野での発展を時系列で追える。

## 従来手法との関係

rsasaki0109 の実装は現状ほぼ幾何ベース（ICP, NDT, Particle Filter など）。DL ベースの手法は論文フェーズのものが多く、rsasaki-hub での実ベンチマーク比較はまだ先の課題。

## 関連コンセプト

[[computer_vision]] | [[slam]] | [[point_cloud_processing]] | [[datasets]] | [[lidar]]
