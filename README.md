# rsasaki-hub

`rsasaki0109` 配下の公開リポジトリを横断比較・評価するための探索ハブです。

共通ライブラリでも設計書置き場でもありません。複数の実装を並べて比較し、暫定採用の根拠を更新し続けることを目的にしています。

## 探索の原則

1. 抽象を先に作らない
2. 複数実装を前提にする
3. 比較可能性を最優先にする
4. すべての実装を破棄可能とみなす
5. 設計書ではなく探索ログを残す

## 現在の探索対象

最初の探索ファミリは **LiDAR スタック** です。

| トラック | 暫定採用 | 比較対象 |
| --- | --- | --- |
| `lidar_localization` | `amcl_3d` | `lidar_localization_ros2` |
| `lidar_slam` | `lidarslam_ros2` | `glim`, `littleslam_ros2`, `li_slam_ros2` |
| `lidar_imu_slam` | `localization_zoo` | `FAST_LIO` |

詳細は [探索結果](https://rsasaki0109.github.io/rsasaki-hub/) を参照してください。

## ディレクトリ構成

| パス | 内容 |
| --- | --- |
| `registry/` | リポジトリのメタデータと探索状態 |
| `ingestors/` | GitHub からのリポジトリ収集とローカル checkout |
| `evaluator/` | ベンチマーク準備度・可読性・拡張性のヒューリスティック評価 |
| `synthesizer/` | 最小インターフェース合成と実装間差分生成 |
| `docs/` | 生成された探索ログ（GitHub Pages で公開） |
| `cli/` | `expctl` と `kb` のエントリーポイント |
| `raw/` | ナレッジベースの生ソース（記事、論文、repo メモ）※ gitignore |
| `wiki/` | ナレッジベースのコンパイル済み wiki ※ gitignore |

## 探索コマンド

```bash
python3 cli/expctl.py sync        # rsasaki0109 の公開リポジトリ一覧を取得
python3 cli/expctl.py extract     # 関連 repo を clone し、I/O とアルゴリズム信号を抽出
python3 cli/expctl.py eval        # 代理指標で評価してランキング
python3 cli/expctl.py synthesize  # 最小インターフェースとドキュメントを生成
```

## ナレッジベースコマンド

ロボティクス研究の知識ベースを構築・検索するための CLI です。ソースを `raw/` に取り込み、必要に応じて LLM と組み合わせて `wiki/` にコンパイルします。

```bash
python3 cli/kb.py ingest                              # experiments.yaml から自動取り込み
python3 cli/kb.py ingest https://example.com/article  # Web 記事を取り込む
python3 cli/kb.py ingest path/to/local.md             # ローカルファイルを取り込む
python3 cli/kb.py compile                             # raw/ から wiki/ を生成（索引 + コンセプトページ）
python3 cli/kb.py search "particle filter"            # 全文検索
python3 cli/kb.py lint                                # 不整合検出とカバレッジ確認
python3 cli/kb.py stats                               # 統計表示
```

外部依存なし。Python 標準ライブラリだけで動作します。
