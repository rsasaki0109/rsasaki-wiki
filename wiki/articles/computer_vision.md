---
title: "Computer Vision"
type: "llm_article"
concept: "computer_vision"
generated_at: "2026-04-05"
source_count: 35
---

# Computer Vision

画像やビデオからシーンの理解・3D 復元・物体認識を行う技術。ロボティクスでは [[localization]]、[[slam]]、物体追跡、環境認識に幅広く使われる。

## Visual SLAM / Visual Odometry

`simple_visual_slam` は C++ による Visual SLAM 実装。特徴点検出・マッチング・バンドル調整の基本パイプラインを含む。論文では Photo-SLAM (2023), MBA-SLAM (2024) が 3D Gaussian Splatting ベースの photorealistic な地図表現を提案。SLAM-Former (2025) は Transformer アーキテクチャで SLAM 全体を統合。

## Place Recognition

`forest-place-recognition` は森林環境での季節不変な Visual Place Recognition。外観変化に頑健な特徴表現を学習し、ループ検出に利用。

## 物体検出・追跡

`crossdomain-object-tracker` はドメイン横断での物体検出・追跡の評価ツール。屋内・屋外・シミュレーション間での転移性能を比較。

## 3D 再構成

`gs-sim2real` は複数データセットでの 3D Gaussian Splatting 再構成プレイグラウンド。LiDAR-NeRF (2023) は [[lidar]] 点群から NeRF を学習する手法。`slam-handbook-python` と `slam-handbook-public-release` は SLAM の理論をハンズオン教材として提供。

## 関連技術系譜

`robotics-technology-genealogy` はロボティクス・AI 技術のインタラクティブ系譜図を提供。`company-technology-genealogy` は企業レベルの技術系譜。いずれも computer vision 関連技術の歴史的文脈を可視化。

## データセット

`robotics-datasets-hub` は自律ナビゲーション向けデータセットのハブ。`tc-datasets` は筑波チャレンジの実世界データ。これらは [[slam]] や [[localization]] のベンチマークに使われる。

## 関連コンセプト

[[slam]] | [[localization]] | [[deep_learning]] | [[datasets]] | [[lidar]]
