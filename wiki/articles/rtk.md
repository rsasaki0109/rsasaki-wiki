---
title: "RTK"
type: "llm_article"
concept: "rtk"
generated_at: "2026-04-10"
source_count: 6
---

# RTK (Real-Time Kinematic)

搬送波位相を用いて相対測位を高精度化する GNSS 手法。理想的にはセンチメートル級を狙えるが、実装上は ambiguity resolution、cycle slip、hold、都市部マルチパス、post-filter の扱いで性能差が大きく出る。

## 現在の実装対象

`rsasaki0109` の主対象は `gnssplusplus-library`。RTK / PPP / CLAS を同一コードベースで扱えるため、現状の GNSS track では暫定採用になっている。

## 2026-04-10 時点の主要知見

### 1. `--arfilter` は効かせる価値がある

subset AR fix 採択に `--arfilter` と `--arfilter-margin` を実際に配線すると、newly eligible な衛星対が混ざったときの誤固定を減らせる。特に `low-cost + arfilter` は PPC Tokyo run3 late-window で強く効いた。

### 2. Doppler slip は mean-removed 判定が有効

単独衛星だけを見る Doppler slip 判定より、共通バイアスを差し引いた residual 判定の方が demo5 に近く、都市走行データで安定した。

### 3. Odaiba では solver 本体より post-filter が coverage を落としていた

Odaiba 実データでは、solver が解を出していても kinematic post-filter が epoch を落とし過ぎていた。post-filter 緩和後は matched epoch が大きく戻り、coverage 面では RTKLIB demo5 との差が縮んだ。

### 4. PPC は city / run ごとに勝ち筋が違う

- Tokyo run1 は current default が最良寄り
- Tokyo run3 late-window は `low-cost + arfilter` が有効
- Nagoya run2 は default と tuned がほぼ同値
- Nagoya run3 late-window は false-fix と float drift が未解決

## 現在の benchmark 読み

### Odaiba

post-filter 緩和後は coverage がかなり改善した。`low-cost + arfilter` は current default より fix rate と all-epoch p95 を改善できている。

### PPC Tokyo run3 late-window

`skip=13301`, `max_epochs=2000`, `--preset low-cost --arfilter` で `1957 matched`, `81.808891% fix`, `median_h=0.019441 m`, `p95_h=1.521877 m`。RTKLIB 比でも fix rate は上回っている。

### PPC Nagoya run3 late-window

ここが現在の主ボトルネック。hold ratio threshold の hardcode 修正後でも `1819 matched`, `16.272677% fix`, `median_h=7.817195 m`, `p95_h=18.312437 m`, `p95_abs_up=55.943279 m` で、RTKLIB 相当には届いていない。

## 直近で潰したバグ

hold active 時の ratio threshold が実装上 `2.0` 固定になっていて、`hold_ambiguity_ratio_threshold` が無視されていた。これを設定値に接続したことで、Tokyo run3 tuned の勝ち筋を壊さずに Nagoya run3 の悪い FIX をかなり削れた。

## まだ残っている問題

### false-fix

PPC Nagoya run3 late-window の `tow 554720.2/554720.4` では libgnss++ が FIX を出すが、実際の水平誤差は `13.463 m` 前後ある。RTKLIB は同区間を FLOAT のまま維持しているため、`validateFixedSolution()` 側がまだ甘い。

### float drift

`tow 554746.x` 付近では default / low-cost / no-hold がほぼ同じ FLOAT を出し、`horiz=18.878 m`, `up=-7.265 m` まで外れる。hold を切っても変わらないので、hold ではなく float update か measurement weighting 側の課題と見ている。

## 実務上の使い分け

- Odaiba のような coverage drop が主問題の区間では、post-filter 緩和の有無を先に疑う
- Tokyo run3 のような AR 成功率が支配的な区間では `low-cost + arfilter` が有力
- Nagoya run3 のような bad fix / bad float 混在区間では、fix rate だけで tuning を選ばない

## 次に見るべき場所

- `validateFixedSolution()` で `554720.x` の false-fix を止める条件
- long float 区間で stale ambiguity が position を引っ張っていないか
- `554746.x` で RTKLIB float と libgnss++ float の差を作っている measurement weighting / state reset 条件

## 関連コンセプト

[[gnss]] | [[localization]] | [[imu]] | [[state_estimation]] | [[datasets]]
