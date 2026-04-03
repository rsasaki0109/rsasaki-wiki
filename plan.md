# Claude Handoff Plan

## 1. このリポジトリの位置づけ

`rsasaki-hub` は `rsasaki0109` 配下の public repository 群を横断して、

- 何が同じ問題を解いているか
- どの実装差分が重要か
- どの I/O だけを最小契約として残すべきか
- 今どの実装を暫定採用し、何を保留にするべきか

を管理するための「探索中枢」です。

重要なのは、この repo は正解を保存する場所ではないことです。

- 共通ライブラリ化が目的ではない
- 綺麗な抽象設計が目的ではない
- 失敗実装の削除が目的ではない
- 比較を加速し、意思決定を更新し続けることが目的

開発原則は以下で固定しています。

1. 抽象を先に作らない
2. 複数実装を前提にする
3. 比較可能性を最優先にする
4. すべての実装を破棄可能とみなす
5. 設計書ではなく探索ログを残す

## 2. 現在の状態

2026-04-03 時点で、最初の探索 family として `lidar_stack_exploration` を作成済みです。

対象トラックは 3 つです。

- `lidar_localization`
- `lidar_slam`
- `lidar_imu_slam`

CLI はすでに実装済みで、以下が通っています。

```bash
python3 cli/expctl.py sync
python3 cli/expctl.py extract
python3 cli/expctl.py eval
python3 cli/expctl.py synthesize
```

現時点では `sync -> extract -> eval -> synthesize` を 1 回実行済みで、生成物も出ています。

## 3. いま存在する主要ファイル

- `README.md`
  - repo の目的と使い方の説明
- `registry/repos.yaml`
  - GitHub API から取得した `rsasaki0109` の public repo 一覧
  - 2026-04-03 時点で 75 repo
- `registry/experiments.yaml`
  - 実験 family、抽出された実装、評価結果、ランキング、インターフェース候補
- `ingestors/github_loader.py`
  - GitHub API 経由の repo 取得
  - `.cache/repos/` への shallow clone / pull
- `evaluator/benchmark.py`
  - benchmark 記述やメトリクス記述の proxy 抽出
- `evaluator/readability.py`
  - LOC、分岐数、最大関数サイズなどの可読性 heuristic
- `evaluator/extensibility.py`
  - モジュール分割、設定ファイル、public surface などの拡張性 heuristic
- `synthesizer/abstraction.py`
  - 複数実装から最小 I/O 契約候補を合成
- `synthesizer/diff.py`
  - pairwise diff 生成
- `docs/experiments.md`
  - 比較一覧
- `docs/decisions.md`
  - 暫定採用と却下理由
- `docs/interfaces.md`
  - 最小インターフェース候補

## 4. 実装の考え方

### 4.1 `repos.yaml` と `experiments.yaml` は JSON 互換 YAML

依存を増やさないため、`.yaml` という名前ですが実体は JSON 文字列です。
YAML 1.2 的には有効ですが、人間向け可読性は弱いです。

この判断は「まずはローカルで標準ライブラリだけで動くこと」を優先した結果です。

もし Claude が次に触るなら、以下のどちらかを選ぶのが良いです。

1. 現状維持する
2. `PyYAML` などを導入して本物の YAML に寄せる

ただし今の段階では 1 のままで十分です。
フォーマット整備は benchmark 実装より優先度が低いです。

### 4.2 `extract` は heuristic ベース

抽出は以下の信号を組み合わせています。

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

track 分類は heuristic スコア制です。
repo 名に `slam`, `localization`, `lio`, `imu` が入っているかをかなり強いシグナルとして使っています。

### 4.3 `eval` は「実行評価」ではなく「比較の下地」

ここはかなり重要です。
今の `eval` は本当の意味での benchmark ではありません。

現時点の評価は以下のような proxy 指標です。

- benchmark
  - README や docs に benchmark / rmse / runtime / hz / accuracy が書かれているか
  - benchmark artifacts が repo 内にあるか
- readability
  - source files
  - non-empty LOC
  - branch count
  - import count
  - largest function span
  - comment ratio
- extensibility
  - module dirs
  - config files
  - helper units
  - public surface markers
  - hard-coded topics

重みは現状以下です。

- benchmark: 0.50
- readability: 0.25
- extensibility: 0.25

つまり、現在のランキングは「実運用で本当に最強な実装」ではなく、
「比較・検証を前に進めやすい実装」を強めに評価していると理解してください。

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

除外された repo も `registry/experiments.yaml` に残しています。
理由は例えば以下です。

- `no_lidar_input_signal`
- `supporting_component_only`
- `missing_pose_output`
- `missing_imu_input`
- `out_of_scope_domain`

この「除外理由を残す」こと自体が探索ログの一部です。

## 6. 現時点の暫定ランキング

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

これは永久採用ではありません。
あくまで「今この repo を基準に比較を深めると進みやすい」という意味です。

## 8. 最小 I/O 契約の現状

### 8.1 localization

- Input: `Imu, Odometry, PointCloud2, Pose`
- Optional input: `Path`
- Output: `Path, PointCloud2, Pose`

### 8.2 slam

- Input: `PointCloud2`
- Optional input: `Imu, Odometry, MapArray, NavSatFix, Pose`
- Output: `Pose`
- Optional output: `Path, PointCloud2, MapArray`

### 8.3 lidar+imu slam

- Input: `Imu, Odometry, PointCloud2`
- Optional input: `Path`
- Output: `Odometry, Path`
- Optional output: `PointCloud2, Pose`

ここにも heuristic の粗さがあります。
特に `slam` track の `Output: Pose` は最小すぎて、実際の mapping / submap / graph らしさが薄いです。
Claude が次に改善するなら、ここはかなり優先度が高いです。

## 9. 明確に弱いところ

### 9.1 benchmark が proxy のまま

最大の弱点です。
今は「実行できる benchmark 基盤」ではなく、
「benchmark を持っていそうか」を見ているに近いです。

これにより、

- `lidarslam_ros2`
- `amcl_3d`
- `localization_zoo`

のように docs や tests が整っている repo が強く出ます。

これは初期探索には有効ですが、最終的な比較軸としては不十分です。

### 9.2 I/O 抽出が line-based heuristic

`Subscription` や `Publisher` を含む行からメッセージ型を読んでいるだけなので、

- input / output の取り違え
- internal intermediate message を output と誤認
- Path を input 側に入れてしまう

といったノイズがあります。

### 9.3 `lidar_slam` と `lidar_imu_slam` の境界が曖昧

`li_slam_ros2` は実質 LiDAR + IMU 系の性格もありますが、
現状 heuristic では `lidar_slam` 側に分類されました。

この判断自体は完全に間違いではないですが、

- front-end を見るか
- system 全体を見るか
- graph backend を含むか

で答えが変わります。

ここは Claude が整理し直す価値があります。

### 9.4 `localization_zoo` が強く出るが、比較軸としては特殊

`localization_zoo` は実験場として非常に良い一方で、
単一アルゴリズム実装ではなく「比較を収める場」でもあります。

そのため、

- その repo 自体を 1 implementation と見なすのか
- repo 内部の variant 群を implementation として再分解するのか

は次の大きな分岐です。

個人的には後者のほうがこの hub の思想に合っています。

## 10. Claude に最優先でやってほしいこと

優先度順に書きます。

### 優先度 A: 実 benchmark 導入

目的は `eval` を proxy から実測へ近づけることです。

最低限やるべきこと:

1. track ごとに benchmark contract を決める
2. 実行可能な dataset / bag / sample input の場所を決める
3. repo ごとの runner を作る
4. runtime / failure / artifact 出力 / quality metric を収集する

想定 contract:

- localization
  - input: point cloud map + live cloud + initial pose
  - output: pose trajectory or final pose
  - metric: localization error, runtime, failure count
- slam
  - input: point cloud stream
  - output: trajectory + map-like artifact
  - metric: runtime, trajectory metric, map export success
- lidar+imu slam
  - input: point cloud + imu
  - output: odometry / trajectory
  - metric: runtime, drift / ATE proxy, failure count

まだ大きいので、まずは 1 track だけやるべきです。
最初は `lidar_localization` が一番狭くて進めやすいです。

### 優先度 A: `localization_zoo` の扱いを再設計

今は repo 単位で比較していますが、
`localization_zoo` の価値は「内部で variant を持てること」です。

次のどちらにするかを決めてください。

1. repo 単位比較を維持する
2. repo 内 variant を hub 側で分解して implementation 扱いする

この repo の思想からすると、2 がかなり自然です。

### 優先度 A: `extract` の I/O 推定精度改善

最低限ほしい改善:

- subscriber / publisher の AST か正規表現をもう少し真面目に解析
- C++ の `create_subscription<...>` と `create_publisher<...>` を明示的に拾う
- ROS2 launch / param / rviz から topic 補完
- `Path` や `PointCloud2` の input / output 誤判定を減らす

### 優先度 B: `lidar_slam` track を 2 層に割るか再検討

候補:

- `lidar_odometry`
- `lidar_mapping`
- `lidar_pose_graph_slam`

ただし、今すぐ増やしすぎないでください。
track を増やすなら、比較対象 repo が最低 2 つ以上あることを確認してからです。

### 優先度 B: docs をもう少し「探索ログ」に寄せる

現在の docs は要約としては十分ですが、探索ログとしてはまだ薄いです。

足すとよい項目:

- なぜこの repo を比較対象に入れたか
- 何が似ていて、何が違ったか
- 次に比較し直す条件
- 誤抽出のメモ

## 11. やらないほうがいいこと

Claude に明確に避けてほしいことを先に書いておきます。

### 11.1 共通 Python ライブラリ化

この repo の中心は orchestration であって、汎用ライブラリ化ではありません。
`core/` を作って壮大な抽象化を始めるのはまだ早いです。

### 11.2 いきなり全 domain を取り込む

今の scope は `lidar localization / slam / lidar+imu slam` に絞られています。
GNSS、visual SLAM、tracking、3D removal などへいきなり広げないでください。

### 11.3 benchmark を巨大基盤化する

まず 1 track で小さく回る実 benchmark を作るべきです。
いきなり全 repo 共通の巨大 executor を作ると失敗しやすいです。

### 11.4 docs だけ綺麗にして満足する

この repo は docs repo ではないです。
docs の価値は、実際の比較 pipeline が動くときにだけ上がります。

## 12. 次の具体タスク案

Claude が着手しやすいように、実作業単位で書きます。

### Task 1

`cli/expctl.py extract` の I/O 抽出を改善する。

達成条件:

- `create_subscription<sensor_msgs::msg::PointCloud2>` を input と認識
- `create_publisher<nav_msgs::msg::Path>` を output と認識
- `Path` が input に誤混入しにくくなる

### Task 2

`lidar_localization` 専用の簡易 benchmark runner を追加する。

達成条件:

- `amcl_3d` と `lidar_localization_ros2` の 2 実装で同一フォーマットの結果を吐く
- runtime
- success / failure
- final pose or trajectory artifact path

を最低限比較可能にする。

### Task 3

`registry/experiments.yaml` の implementation 単位を repo 単位から variant 単位へ拡張できる形にする。

例えば:

- `repo`
- `variant`
- `track`
- `runner`
- `dataset`
- `input_contract`
- `output_contract`

のようなフィールドを持てる形です。

ただし、この task は benchmark runner の方向性が見えてからで十分です。

## 13. いまのコードで注意する箇所

### `cli/expctl.py`

ここにかなりロジックが集まっています。
特に以下の関数が中核です。

- `pick_relevant_files`
- `extract_io`
- `extract_algorithm_markers`
- `classify_track`
- `candidate_status`
- `eval_command`
- `synthesize_command`

次に改善するなら、まずはここを読むべきです。

### `.cache/repos/`

ここには shallow clone された public repos が入っています。
比較対象の現物確認に使えます。

この cache は作業上かなり重要ですが、生成物なので破棄可能です。
ただし引き継ぎ時点では残しておくほうが探索速度は速いです。

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

もし GitHub rate limit が気になるなら `GITHUB_TOKEN` か `GH_TOKEN` を環境変数で渡してください。

## 15. 最後に

この repo は「綺麗な抽象」を作ると弱くなります。
まずやるべきは、比較単位をもっと実物に寄せることです。

いまの状態は悪くありません。
少なくとも以下はできています。

- repo 群を自動で集める
- LiDAR 系の候補 repo を絞る
- 比較表を生成する
- 暫定採用を出す
- docs に同期する

次の本丸は、

- 実 benchmark を 1 本通す
- variant 単位に分解する
- I/O 抽出を少し賢くする

の 3 つです。

この順番を崩さないほうが、探索ハブとして強く育ちます。
