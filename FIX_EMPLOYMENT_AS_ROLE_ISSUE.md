# 🚨 雇用形態の職種混入問題 - 修正計画

## 問題の詳細
- **現象**: dash_app.pyで総不足時間が48,972時間という異常値を表示
- **原因**: 雇用形態（emp_パート、emp_正社員等）が職種として扱われている
- **影響**: 同じ不足時間が職種別と雇用形態別で二重カウントされている

## データの流れ
```
Excelファイル
  ↓
データ入稿（ingest）
  ↓ 
ヒートマップ生成 ← ここで「emp_」プレフィックスの職種が混入
  ↓
shortage.py（不足計算）
  ↓
shortage_role_summary.parquet ← emp_パート等が職種として保存
  ↓
dash_app.py（表示） ← 異常な合計値
```

## 修正方法

### Option 1: データ入稿時の修正（推奨）
`shift_suite/tasks/enhanced_data_ingestion.py`で、職種名から`emp_`プレフィックスを除外

### Option 2: shortage.py での修正
職種別集計時に`emp_`で始まる職種を除外

### Option 3: dash_app.py での修正（暫定対応）
表示時に`emp_`で始まる職種を除外して集計

## 暫定修正コード（dash_app.py）

```python
# collect_dashboard_overview_kpis 関数内
if shortage_role_file.exists():
    df = pd.read_parquet(shortage_role_file)
    
    # 🔧 修正: emp_で始まる職種（雇用形態）を除外
    if 'role' in df.columns:
        df_filtered = df[~df['role'].str.startswith('emp_', na=False)]
        total_shortage = df_filtered.get('lack_h', pd.Series()).sum()
        total_excess = df_filtered.get('excess_h', pd.Series()).sum()
    else:
        total_shortage = df.get('lack_h', pd.Series()).sum()
        total_excess = df.get('excess_h', pd.Series()).sum()
```

## 根本修正の推奨
データ入稿プロセスを見直し、職種と雇用形態を明確に分離する必要があります。