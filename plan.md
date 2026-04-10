# Claude 引き継ぎメモ

## 1. このリポジトリの位置づけ

`rsasaki-hub` は `rsasaki0109` 配下の公開リポジトリ群を横断して、

- 何が同じ問題を解いているか
- どの実装差分が重要か
- どの I/O だけを最小契約として残すべきか
- 現時点でどの実装を暫定採用し、何を保留にするべきか

を管理するための「探索ハブ」です。

このリポジトリは正解を保存する場所ではありません。

- 共通ライブラリ化が目的ではない
- きれいな抽象設計が目的ではない
- 失敗実装の削除が目的ではない
- 比較を加速し、意思決定を更新し続けることが目的

開発原則は以下で固定しています。

1. 抽象を先に作らない
2. 複数実装を前提にする
3. 比較可能性を最優先にする
4. すべての実装を破棄可能とみなす
5. 設計書ではなく探索ログを残す

## 2. 現在の状態

2026-04-03 時点で、最初の探索ファミリとして `lidar_stack_exploration` を作成済みです。

対象トラックは 3 つです。

- `lidar_localization`
- `lidar_slam`
- `lidar_imu_slam`

CLI は実装済みで、以下が通ります。

```bash
python3 cli/expctl.py sync
python3 cli/expctl.py extract
python3 cli/expctl.py eval
python3 cli/expctl.py synthesize
```

現時点では `sync -> extract -> eval -> synthesize` を 1 回実行済みで、生成物も出ています。

## 3. 主要ファイル

- `README.md`
  - リポジトリの目的と使い方
- `registry/repos.yaml`
  - GitHub API から取得した `rsasaki0109` の公開リポジトリ一覧
  - 2026-04-03 時点で 75 repo
- `registry/experiments.yaml`
  - 実験ファミリ、抽出済み実装、評価結果、ランキング、インターフェース候補
- `ingestors/github_loader.py`
  - GitHub API 経由のリポジトリ取得
  - `.cache/repos/` への浅い clone / pull
- `evaluator/benchmark.py`
  - ベンチマーク記述やメトリクス記述の代理抽出
- `evaluator/readability.py`
  - LOC、分岐数、最大関数サイズなどの可読性ヒューリスティック
- `evaluator/extensibility.py`
  - モジュール分割、設定ファイル、公開 API などの拡張性ヒューリスティック
- `synthesizer/abstraction.py`
  - 複数実装から最小 I/O 契約候補を合成
- `synthesizer/diff.py`
  - 実装間差分を生成
- `docs/experiments.md`
  - 比較一覧
- `docs/decisions.md`
  - 暫定採用と却下理由
- `docs/interfaces.md`
  - 最小インターフェース候補

## 4. 実装方針

### 4.1 `repos.yaml` と `experiments.yaml` は JSON 互換 YAML

依存を増やさないため、`.yaml` という名前ですが実体は JSON 文字列です。YAML 1.2 的には有効ですが、人間向けの可読性は弱めです。

この判断は「まずはローカルで標準ライブラリだけで動くこと」を優先した結果です。

次に触る場合の選択肢は次の 2 つです。

1. 現状維持する
2. `PyYAML` などを導入して本物の YAML に寄せる

ただし現段階では 1 のままで十分です。フォーマット整備は実ベンチマーク導入より優先度が低いです。

### 4.2 `extract` はヒューリスティックベース

抽出では以下の信号を組み合わせています。

- repo 名
- description
- topics
- ソース内のメッセージ型
- ROS topic 文字列
- 関数名
- アルゴリズム語彙

メッセージ型の簡易抽出対象は以下です。

- `PointCloud2`
- `Imu`
- `Odometry`
- `LaserScan`
- `PoseStamped`
- `PoseWithCovarianceStamped`
- `Path`
- `MapArray`
- `NavSatFix`

アルゴリズム語彙は以下のような文字列を拾っています。

- `ndt`
- `gicp`
- `vgicp`
- `icp`
- `amcl`
- `lio`
- `imu_preintegration`
- `graph_based_slam`
- `g2o`
- `scan_context`
- `deskew`
- `submap`
- `odometry`

トラック分類はヒューリスティックスコア制です。repo 名に `slam`, `localization`, `lio`, `imu` が入っているかを強いシグナルとして使っています。

### 4.3 `eval` は「実行評価」ではなく「比較の下地」

ここは重要です。今の `eval` は本当の意味でのベンチマークではありません。

現時点の評価は以下のような代理指標です。

- ベンチマーク準備度
  - README や docs に benchmark / rmse / 実行時間 / hz / accuracy が書かれているか
  - benchmark 用 artifacts が repo 内にあるか
- 可読性
  - source files
  - non-empty LOC
  - branch count
  - import count
  - largest function span
  - comment ratio
- 拡張性
  - module dirs
  - config files
  - helper units
  - public surface markers
  - hard-coded topics

重みは以下です。

- benchmark: 0.50
- readability: 0.25
- extensibility: 0.25

つまり現在のランキングは「実運用で最強の実装」ではなく、「比較と検証を進めやすい実装」を強めに評価していると理解してください。

## 5. 現在の抽出結果

抽出済みの主な候補は以下です。

### 5.1 `lidar_localization`

- `amcl_3d`
- `lidar_localization_ros2`

### 5.2 `lidar_slam`

- `lidarslam_ros2`
- `li_slam_ros2`
- `glim`
- `littleslam_ros2`

### 5.3 `lidar_imu_slam`

- `FAST_LIO`
- `localization_zoo`

除外された repo も `registry/experiments.yaml` に残しています。理由の例は以下です。

- `no_lidar_input_signal`
- `supporting_component_only`
- `missing_pose_output`
- `missing_imu_input`
- `out_of_scope_domain`

この「除外理由を残す」こと自体が探索ログの一部です。

## 6. 現在の暫定ランキング

2026-04-03 の `eval` 時点では以下です。

### 6.1 `lidar_localization`

1. `amcl_3d` : 90.22
2. `lidar_localization_ros2` : 36.72

### 6.2 `lidar_slam`

1. `lidarslam_ros2` : 83.97
2. `glim` : 45.78
3. `littleslam_ros2` : 42.74
4. `li_slam_ros2` : 36.48

### 6.3 `lidar_imu_slam`

1. `localization_zoo` : 84.33
2. `FAST_LIO` : 52.26

## 7. 現時点の暫定採用

`docs/decisions.md` と `docs/interfaces.md` に反映済みの暫定採用は以下です。

- localization: `amcl_3d`
- slam: `lidarslam_ros2`
- lidar+imu slam: `localization_zoo`

これは永久採用ではありません。あくまで「今この repo を基準に比較を深めると進みやすい」という意味です。

## 8. 最小 I/O 契約の現状

### 8.1 localization

- 入力: `Imu, Odometry, PointCloud2, Pose`
- 任意入力: `Path`
- 出力: `Path, PointCloud2, Pose`

### 8.2 slam

- 入力: `PointCloud2`
- 任意入力: `Imu, Odometry, MapArray, NavSatFix, Pose`
- 出力: `Pose`
- 任意出力: `Path, PointCloud2, MapArray`

### 8.3 lidar+imu slam

- 入力: `Imu, Odometry, PointCloud2`
- 任意入力: `Path`
- 出力: `Odometry, Path`
- 任意出力: `PointCloud2, Pose`

ここにもヒューリスティックの粗さがあります。特に `slam` トラックの `Pose` 単独出力は最小化しすぎで、実際の mapping / submap / graph らしさが薄いです。次に改善するなら優先度は高いです。

## 9. 明確に弱いところ

### 9.1 ベンチマークが代理評価のまま

最大の弱点です。今は「実行できるベンチマーク基盤」ではなく、「ベンチマークを持っていそうか」を見ている状態に近いです。

このため、

- `lidarslam_ros2`
- `amcl_3d`
- `localization_zoo`

のように docs や tests が整っている repo が強く出ます。

これは初期探索には有効ですが、最終的な比較軸としては不十分です。

### 9.2 I/O 抽出が行ベースのヒューリスティック

`Subscription` や `Publisher` を含む行からメッセージ型を読んでいるだけなので、

- 入力 / 出力の取り違え
- 内部中間メッセージを出力と誤認
- `Path` を入力側に入れてしまう

といったノイズがあります。

### 9.3 `lidar_slam` と `lidar_imu_slam` の境界が曖昧

`li_slam_ros2` は実質 LiDAR + IMU 系の性格もありますが、現状のヒューリスティックでは `lidar_slam` 側に分類されました。

この判断自体は完全に誤りではありませんが、

- フロントエンドを見るか
- システム全体を見るか
- グラフバックエンドを含むか

で結論が変わります。

### 9.4 `localization_zoo` は比較軸として特殊

`localization_zoo` は実験場として非常に良い一方で、単一アルゴリズム実装ではなく「比較を収める場」でもあります。

そのため、

- repo 自体を 1 実装とみなすのか
- repo 内部のバリアント群を別実装として分解するのか

は次の大きな分岐です。

個人的には後者のほうがこの hub の思想に合っています。

## 10. 次に最優先でやること

優先度順に書きます。

### 優先度 A: 実ベンチマーク導入

目的は `eval` を代理評価から実測へ近づけることです。

最低限やるべきこと:

1. トラックごとにベンチマーク契約を決める
2. 実行可能なデータセット / bag / サンプル入力の場所を決める
3. repo ごとのランナーを作る
4. 実行時間 / 成否 / artifact 出力 / 品質指標を収集する

想定契約:

- localization
  - 入力: point cloud map + live cloud + initial pose
  - 出力: pose trajectory または final pose
  - 指標: localization error, 実行時間, failure count
- slam
  - 入力: point cloud stream
  - 出力: trajectory + map-like artifact
  - 指標: 実行時間, trajectory metric, map export success
- lidar+imu slam
  - 入力: point cloud + imu
  - 出力: odometry / trajectory
  - 指標: 実行時間, drift / ATE 代理, failure count

まだ大きいので、まずは 1 トラックだけやるべきです。最初は `lidar_localization` が一番狭くて進めやすいです。

### 優先度 A: `localization_zoo` の扱いを再設計

今は repo 単位で比較していますが、`localization_zoo` の価値は内部でバリアントを持てることです。

次のどちらにするかを決めてください。

1. repo 単位比較を維持する
2. repo 内バリアントを hub 側で分解して実装扱いする

この repo の思想からすると 2 がかなり自然です。

### 優先度 A: `extract` の I/O 推定精度改善

最低限ほしい改善:

- subscriber / publisher を AST か、もう少し厳密な正規表現で解析
- C++ の `create_subscription<...>` と `create_publisher<...>` を明示的に拾う
- ROS2 launch / param / rviz から topic を補完
- `Path` や `PointCloud2` の入力 / 出力誤判定を減らす

### 優先度 B: `lidar_slam` トラックを 2 層に割るか再検討

候補:

- `lidar_odometry`
- `lidar_mapping`
- `lidar_pose_graph_slam`

ただし今すぐ増やしすぎないでください。トラックを増やすなら、比較対象 repo が最低 2 つ以上あることを確認してからです。

### 優先度 B: docs をもう少し探索ログに寄せる

現在の docs は要約としては十分ですが、探索ログとしてはまだ薄いです。

足すとよい項目:

- なぜこの repo を比較対象に入れたか
- 何が似ていて、何が違ったか
- 次に比較し直す条件
- 誤抽出のメモ

## 11. やらないほうがいいこと

### 11.1 共通 Python ライブラリ化

この repo の中心は orchestration であって、汎用ライブラリ化ではありません。`core/` を作って大きな抽象化を始めるのはまだ早いです。

### 11.2 いきなり全 domain を取り込む

今の対象範囲は `lidar localization / slam / lidar+imu slam` に絞られています。GNSS、視覚 SLAM、追跡、3D 除去などへいきなり広げないでください。

### 11.3 ベンチマークを巨大基盤化する

まず 1 トラックで小さく回る実ベンチマークを作るべきです。いきなり全 repo 共通の巨大 executor を作ると失敗しやすいです。

### 11.4 docs だけ整えて満足する

この repo はドキュメント専用 repo ではありません。docs の価値は、実際の比較 pipeline が動いているときにだけ上がります。

## 12. 次の具体タスク案

### タスク 1

`cli/expctl.py extract` の I/O 抽出を改善する。

達成条件:

- `create_subscription<sensor_msgs::msg::PointCloud2>` を入力として認識
- `create_publisher<nav_msgs::msg::Path>` を出力として認識
- `Path` が入力に誤混入しにくくなる

### タスク 2

`lidar_localization` 専用の簡易ベンチマークランナーを追加する。

達成条件:

- `amcl_3d` と `lidar_localization_ros2` の 2 実装で同一フォーマットの結果を出す
- 実行時間
- success / failure
- final pose または trajectory artifact path

を最低限比較できるようにする。

### タスク 3

`registry/experiments.yaml` の実装単位を repo 単位からバリアント単位へ拡張できる形にする。

例えば次のようなフィールドを持てる構造です。

- `repo`
- `variant`
- `track`
- `runner`
- `dataset`
- `input_contract`
- `output_contract`

ただしこのタスクは、ベンチマークランナーの方向性が見えてからで十分です。

## 13. いまのコードで注意する箇所

### `cli/expctl.py`

ここにかなりロジックが集まっています。特に以下の関数が中核です。

- `pick_relevant_files`
- `extract_io`
- `extract_algorithm_markers`
- `classify_track`
- `candidate_status`
- `eval_command`
- `synthesize_command`

次に改善するなら、まずはここを読むべきです。

### `.cache/repos/`

ここには浅い clone をした公開 repo が入っています。比較対象の現物確認に使えます。

この cache は生成物なので破棄可能ですが、引き継ぎ時点では残しておくほうが探索速度は速いです。

## 14. 再現手順

作業を引き継いだら、まず以下を確認してください。

```bash
python3 -m compileall cli ingestors evaluator synthesizer
python3 cli/expctl.py sync
python3 cli/expctl.py extract
python3 cli/expctl.py eval
python3 cli/expctl.py synthesize
git status --short
```

GitHub rate limit が気になる場合は `GITHUB_TOKEN` か `GH_TOKEN` を環境変数で渡してください。

## 15. 最後に

この repo は「きれいな抽象」を作ると弱くなります。まずやるべきは、比較単位をもっと実物に寄せることです。

いまの状態は悪くありません。少なくとも以下はできています。

- repo 群を自動で集める
- LiDAR 系の候補 repo を絞る
- 比較表を生成する
- 暫定採用を出す
- docs に同期する

次の本丸は以下の 3 つです。

- 実ベンチマークを 1 本通す
- バリアント単位に分解する
- I/O 抽出を少し賢くする

この順番を崩さないほうが、探索ハブとして強く育ちます。
