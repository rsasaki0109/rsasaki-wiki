# CLAS parity status on gnssplusplus-library

Updated: 2026-04-10

## 対象

- Repo: `gnssplusplus-library`
- 比較対象: `CLASLIB`
- 参照ケース: `2019-08-27` CLAS parity dataset
- 比較軸: `OSR parity`, `AR availability`, `position accuracy`

## 現状の到達点

- `30/30 fixed` は達成済み
- ただし `position accuracy` はまだ `CLASLIB` 同等ではない
- 現在の best:
  - `RMS H = 0.9466 m`
  - `RMS V = 3.5390 m`
  - `RMS 3D = 3.6634 m`

要するに、`AR の成立率` はかなり揃ったが、`fixed 後の位置精度` はまだ meter 級の差が残っている。

## ここまでで固めたもの

### 1. CLASLIB を答えにしたテスト基盤

- `CLASLIB rnx2rtkp` の実出力を compare tool で直接読めるようにした
- 実データ `2019-08-27` を使う integration test を追加した
- `OSR`, `CLAS-PHASE-ROW`, `CLAS-IF-PHASE`, `CLAS-WLNL-FIX`, `30 epoch summary` の golden test を追加した

これで「CLASLIB を答えにして regression を止める」状態にはなっている。

### 2. startup fix 率

- startup の `GPS-only DD retry`
- `NL hold`
- 前 epoch の DD constraint 保持

により、参照ケースで `30/30 fixed` を達成した。

## 今わかっていること

### 1. 主問題は OSR ではない

`iono/cbias/pbias/clk` の parity はかなり揃っている。

したがって、今の差は主に

- `fixed_state` の作り方
- `fixed_state` の最終位置への反映

にある。

### 2. 残差の主戦場は vertical

現在の best でも

- `RMS H = 0.9466 m`
- `RMS V = 3.5390 m`

で、残差はほぼ vertical 側に残っている。

### 3. 差分は衛星依存

`DD/state gap` の主犯は全衛星ではなく、主に

- `G25`
- `G29`

に集中している。

### 4. network selection や明示的な slip/continuity 崩壊は主因ではなさそう

現状の観測では

- `phase_net / bias selection` は安定
- 明示的な `reset / slip / continuity` 異常は未確認

なので、本丸はそこではない。

## 効いた変更

### 1. DD transform の分離

`LAMBDA search` 用の DD transform と、`fixed_state` 投影用の DD transform を分離した。

これで `search` の ratio を壊さずに、`fixed_state` 側だけ state 定義へ寄せられるようになった。

### 2. residual ionosphere を fixed_state 側へ反映

`fixed_state` 投影用 DD transform に residual ionosphere state を入れた。

この変更で、一部 epoch の `dd_float_gap` は

- 以前: `0.57 - 1.19 cycles`
- 改善後: 最良 `0.005 cycles`

まで下がった。

## 効かなかった変更

以下は 30 epoch 全体では best を更新しなかった。

- `dd_gap` をそのまま beta 採用 gate に使う
- `phase_rms` を強くした beta 採用 gate
- `state-consistent DD residual` をそのまま最終投影に使う

startup を良くしても late epoch を壊すパターンが多く、単純な gate tuning では詰まらなかった。

## 現在の作業仮説

`CLASLIB` に届かない理由は、もはや

- `AR success` の不足

ではなく、

- `NL float` の構成
- `fixed ambiguity` を state/position に写す式

の satellite-specific mismatch にある。

特に `G25/G29` で、観測側 NL と state 側 NL の差をまだ完全には消せていない。

## 次の一手

優先順は次の通り。

1. `G25/G29` の `NL float` 構成を項別に突き合わせる
2. `corrected carrier`, `ambiguity state`, `residual ionosphere`, `sat clock / CPC` のどれが残差源かを固定する
3. その差分を `fixed_state projection` にだけ反映し、`search` 側は壊さない

## 現時点の要約

- `CLASLIB answer` に基づく test/golden は整った
- 参照ケースで `30/30 fixed` は達成した
- しかし `accuracy parity` は未達
- best は現時点で `RMS 3D = 3.6634 m`
- 本丸は `fixed後の state/position consistency`、特に `G25/G29` 周辺
