# 不足・過剰計算の例

以下の式は不足人数と過剰人数を求めるための Pandas 操作です。

```python
lack_count_overall_df = ((need_df_all - staff_actual_data_all_df).clip(lower=0).fillna(0).astype(int))
shortage_ratio_df = (((need_df_all - staff_actual_data_all_df) / need_df_all.replace(0, np.nan)).clip(lower=0).fillna(0))
excess_count_overall_df = ((staff_actual_data_all_df - upper_df_all).clip(lower=0).fillna(0).astype(int))
excess_ratio_df = (((staff_actual_data_all_df - upper_df_all) / upper_df_all.replace(0, np.nan)).clip(lower=0).fillna(0))
```

## サンプルデータ

| 時間帯 | need | upper | actual |
| ------ | ---- | ----- | ------ |
| 08:00  | 5    | 3     | 4      |
| 08:30  | 5    | 7     | 6      |
| 09:00  | 5    | 6     | 7      |

ここでは 1 日分 (2024‑06‑01) のデータのみを扱います。`need` が必要人数、`actual` が実際の勤務人数、`upper` が上限値です。

```python
import pandas as pd
import numpy as np
index = ["08:00", "08:30", "09:00"]
need_df_all = pd.DataFrame({"2024-06-01": [5, 5, 5]}, index=index)
staff_actual_data_all_df = pd.DataFrame({"2024-06-01": [4, 6, 7]}, index=index)
upper_df_all = pd.DataFrame({"2024-06-01": [3, 7, 6]}, index=index)
```

## 計算結果

```python
lack_count_overall_df
```
|        | 2024-06-01 |
| ------ | ---------- |
| 08:00  | 1          |
| 08:30  | 0          |
| 09:00  | 0          |

```python
shortage_ratio_df.round(2)
```
|        | 2024-06-01 |
| ------ | ---------- |
| 08:00  | 0.20       |
| 08:30  | 0.00       |
| 09:00  | 0.00       |

```python
excess_count_overall_df
```
|        | 2024-06-01 |
| ------ | ---------- |
| 08:00  | 1          |
| 08:30  | 0          |
| 09:00  | 1          |

```python
excess_ratio_df.round(2)
```
|        | 2024-06-01 |
| ------ | ---------- |
| 08:00  | 0.33       |
| 08:30  | 0.00       |
| 09:00  | 0.17       |

08:00 の時間帯では `need` (5) には 1 名不足していますが、`upper` (3) は超過しているため不足と過剰が同時に発生します。

## 上限値 `upper` について

`upper` はヒートマップ作成時に 75 パーセンタイルなどから求められます。`upper` が `need` より小さい場合、同じ時間帯に不足 (`need` に対して) と過剰 (`upper` に対して) の両方が計上されることがあります。これは計算ロジック上は正しく、現場の基準に合わせて上限値が設定されていないことを示唆します。運用上この状況をどう扱うかは組織のポリシー次第ですが、説明時には「必要人数には達していないが、通常の上限は超えている」という状態であることを明確に共有する必要があります。

## 可視化例

Pandas の `plot` メソッドを使って不足人数や過剰人数を棒グラフで表示できます。

```python
import matplotlib.pyplot as plt
lack_count_overall_df.plot(kind="bar")
plt.title("不足人数")
plt.show()

excess_count_overall_df.plot(kind="bar")
plt.title("過剰人数")
plt.show()
```

GUI では以下のようなアウトプットが表示されます。

- 職種別の不足・過剰時間
- 日付別・時間帯別の不足人数
- 職員単位の内訳

これらの表やグラフは `shortage_time.xlsx` や `excess_time.xlsx` をもとに自動生成されます。データを更新して再計算すれば、ダッシュボード上でも最新の不足・過剰状況を確認できます。

### GUI で確認できるグラフ

`app.py` を実行して **Shortage** タブを開くと、以下のグラフが表示されます。

- **職種別不足時間**: 各職種の不足時間を棒グラフで表示します。
- **雇用形態別不足時間**: 雇用区分ごとの不足時間を棒グラフで比較します。
- **時間帯別不足人数**: 任意の日付を選択し、各時間帯の不足人数を棒グラフで確認できます。
- **不足比率ヒートマップ**: `shortage_ratio.xlsx` から生成され、時間帯 × 日付 のマトリクスで不足比率を色分け表示します。
- **不足発生頻度**: 時間帯ごとの不足発生日数を棒グラフで示します。

これらの可視化を利用することで、日付軸・時間軸での過不足を直感的に把握できます。
