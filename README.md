# rsasaki-hub

`rsasaki0109` 配下の public リポジトリを横断的に比較・評価するための探索中枢です。

共通ライブラリでも設計書でもありません。複数の実装を並べて比較し、暫定採用の根拠を残し続けることが目的です。

## 探索の原則

1. 抽象を先に作らない
2. 複数実装を前提にする
3. 比較可能性を最優先にする
4. すべての実装を破棄可能とみなす
5. 設計書ではなく探索ログを残す

## 現在の探索対象

最初の experiment family として **LiDAR スタック** を扱っています。

| Track | 暫定採用 | 比較対象 |
| --- | --- | --- |
| lidar_localization | `amcl_3d` | `lidar_localization_ros2` |
| lidar_slam | `lidarslam_ros2` | `glim`, `littleslam_ros2`, `li_slam_ros2` |
| lidar_imu_slam | `localization_zoo` | `FAST_LIO` |

詳細は [Experiments](https://rsasaki0109.github.io/rsasaki-hub/) を参照してください。

## ディレクトリ構成

| パス | 内容 |
| --- | --- |
| `registry/` | repo メタデータと実験状態 |
| `ingestors/` | GitHub からの repo 収集・ローカル checkout |
| `evaluator/` | benchmark 準備度・可読性・拡張性の heuristic 評価 |
| `synthesizer/` | 最小インターフェース合成・実装間 diff 生成 |
| `docs/` | 生成された探索ログ (GitHub Pages で公開) |
| `cli/` | `expctl` エントリーポイント |

## 使い方

```bash
python3 cli/expctl.py sync        # rsasaki0109 の public repo 一覧を取得
python3 cli/expctl.py extract     # 関連 repo を clone し、I/O・アルゴリズム信号を抽出
python3 cli/expctl.py eval        # proxy メトリクスで評価・ランキング
python3 cli/expctl.py synthesize  # 最小インターフェースと docs を生成
```

外部依存なし。Python 標準ライブラリのみで動作します。
