# Need計算適正化 修正内容引継ぎ書

## 📅 修正日時
2025年7月15日 15:15

## 🎯 修正の目的
職種別・雇用形態別ヒートマップでの過大な不足表示問題を解決し、適正なNeed計算を実現する。

## 🐛 発見された問題

### 問題1: ファイル命名規則の不備
- **職種別ファイル**: `need_per_date_slot_介護.parquet`
- **雇用形態別ファイル**: `need_per_date_slot_スポット.parquet`
- **問題**: 両方とも同じパターンで区別ができない

### 問題2: 整合性検証での混同
```python
# 問題のあったフィルタリング
role_need_files = [f for f in role_need_files if not ("emp_" in f.name...)]
```
- `emp_`プレフィックスがないため、雇用形態別ファイルが職種別として扱われ重複カウント発生

### 問題3: Need値の不整合
```
[NEED_VALIDATION] 全体Need総計: 6454.00
[NEED_VALIDATION] 職種別Need総計: 12908.00 (差: 6454.00)
```
- 職種別Need合計が全体Needの2倍になっていた

### 問題4: dash_app.pyでの独自ロジック
- 生成された詳細Need値ファイルを使用せず、独自の動的Need計算を実行

## ✅ 実施した修正内容

### 1. heatmap.py の修正

#### ファイル命名規則の統一化
```python
# 修正前
role_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_{role_safe_name_final_loop}.parquet"
emp_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_{emp_safe_name_final_loop}.parquet"

# 修正後
role_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_role_{role_safe_name_final_loop}.parquet"
emp_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_emp_{emp_safe_name_final_loop}.parquet"
```

#### 整合性検証の修正
```python
# 修正前
role_need_files = list(out_dir_path.glob("need_per_date_slot_*.parquet"))
role_need_files = [f for f in role_need_files if not ("emp_" in f.name or f.name == "need_per_date_slot.parquet")]

# 修正後
role_need_files = list(out_dir_path.glob("need_per_date_slot_role_*.parquet"))
emp_need_files = list(out_dir_path.glob("need_per_date_slot_emp_*.parquet"))
```

### 2. shortage.py の修正

#### ファイル検索ロジックの修正
```python
# 修正前
role_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_{role_safe_name}.parquet"
emp_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_{emp_safe_name}.parquet"

# 修正後
role_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_role_{role_safe_name}.parquet"
emp_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_emp_{emp_safe_name}.parquet"
```

### 3. dash_app.py の修正

#### データ読み込み機能の追加
```python
# 追加：職種別・雇用形態別詳細Need値ファイルの検索対応
if key.startswith("need_per_date_slot_role_") or key.startswith("need_per_date_slot_emp_"):
    filenames = [f"{key}.parquet"]
```

#### 動的Need計算の統一化
```python
# 詳細Need値ファイルを直接使用するロジックを追加
if heat_key.startswith('heat_emp_'):
    detailed_need_key = f"need_per_date_slot_emp_{emp_name}"
elif heat_key.startswith('heat_'):
    detailed_need_key = f"need_per_date_slot_role_{role_name}"

if detailed_need_key:
    detailed_need_df = data_get(detailed_need_key, pd.DataFrame())
    if not detailed_need_df.empty:
        # 詳細Need値を直接使用
```

### 4. app.py の修正

#### UnboundLocalError の修正
```python
# 修正前（問題のあった箇所）
def display_mind_reader_tab(tab_container, data_dir: Path) -> None:
    if "mind_reader_results" not in st.session_state:
        # ... 処理 ...
    else:
        results = st.session_state.mind_reader_results
    # resultsが未定義の場合がある

# 修正後
def display_mind_reader_tab(tab_container, data_dir: Path) -> None:
    results = None  # 事前初期化
    if "mind_reader_results" not in st.session_state:
        if st.button("思考プロセスを解読する"):
            # ... 処理 ...
        else:
            st.info("思考プロセスを解読するボタンをクリックしてください。")
            return
    else:
        results = st.session_state.mind_reader_results
    
    if results is None:
        return
```

## 🗂️ 生成ファイル構造

### 修正後のファイル命名規則
```
need_per_date_slot.parquet                    # 全体Need
need_per_date_slot_role_介護.parquet          # 職種別Need
need_per_date_slot_role_看護師.parquet        # 職種別Need  
need_per_date_slot_emp_正社員.parquet         # 雇用形態別Need
need_per_date_slot_emp_パート.parquet         # 雇用形態別Need
```

## 🧮 按分計算の理論

### 設計思想
- **全体Need**: 独立した全体の必要人数
- **職種別Need**: 全体Needから職種比率で按分
- **雇用形態別Need**: 全体Needから雇用形態比率で按分
- **整合性**: 全体Need = 職種別Need合計 = 雇用形態別Need合計

### 按分計算式
```python
# 職種比率の計算
role_ratio = role_staff_total / all_staff_total

# 詳細Need値の全日程に比率を適用
role_need_df = global_need_df * role_ratio

# 時間帯別の平均Need値を算出（ヒートマップ用）
need_r_series = role_need_df.mean(axis=1).round()
```

## 📊 期待される効果

1. **整合性確保**: 全体Need = 職種別Need合計 = 雇用形態別Need合計
2. **適正な不足表示**: 職種別・雇用形態別で過大な不足が解消
3. **統一されたNeed計算**: 3つのモジュール全てで同じ詳細Need値を使用
4. **ファイル管理の明確化**: 職種別と雇用形態別の明確な区別

## 🔧 バックアップファイル

以下のディレクトリに修正版ファイルをバックアップ済み：
```
backups/20250715_151529/
├── app_fixed.py          # Mind Reader UnboundLocalError修正版
├── dash_app_fixed.py     # 統一Need計算ロジック版
├── heatmap_fixed.py      # 按分計算・ファイル命名修正版
└── shortage_fixed.py     # ファイル検索ロジック修正版
```

## 🚀 動作確認方法

### 1. 新しい分析の実行
修正されたロジックで新しい分析を実行して、以下を確認：

### 2. 生成ファイルの確認
```bash
ls analysis_results/need_per_date_slot_*.parquet
```
- `need_per_date_slot_role_*.parquet` ファイルが生成されている
- `need_per_date_slot_emp_*.parquet` ファイルが生成されている

### 3. 整合性ログの確認
```
[NEED_VALIDATION] 全体Need総計: XXXX.XX
[NEED_VALIDATION] 職種別Need総計: XXXX.XX (差: 0.XX以下)
[NEED_VALIDATION] 雇用形態別Need総計: XXXX.XX (差: 0.XX以下)
[NEED_VALIDATION] ✅ Need値の整合性: OK（誤差は許容範囲内）
```

### 4. dash_app.pyでの詳細Need値使用ログ
```
[ROLE_DYNAMIC_NEED] heat_介護: Using detailed need file need_per_date_slot_role_介護
[ROLE_DYNAMIC_NEED] heat_介護: Successfully using detailed need values
```

## ⚠️ 注意事項

### 1. 既存データとの互換性
- 修正前に生成されたファイルは古い命名規則のため、新しい分析が必要
- キャッシュクリアが推奨

### 2. 按分計算の前提
- 「実績比率 = Need比率」の前提に基づく
- 職種間の業務特性差は考慮しない純粋な人数按分

### 3. メンテナンス時の注意
- ファイル命名規則の変更時は3つのモジュール全てを同期修正する必要
- 新しい職種・雇用形態追加時は命名規則に従う

## 📞 技術サポート

### 主要修正箇所
- `heatmap.py`: 1054, 1283, 1467-1487行目
- `shortage.py`: 446, 766行目  
- `dash_app.py`: 493-496, 214-238行目
- `app.py`: 4233-4252行目

### 按分計算のコアロジック
- `heatmap.py`: 1048, 1277行目の `* role_ratio`, `* emp_ratio`

このドキュメントにより、今後のメンテナンスや機能拡張が適切に実施できます。