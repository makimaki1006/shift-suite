#!/usr/bin/env python3
"""
Fix for fatigue analysis execution issues in app.py
"""

# 修正箇所1: 2629-2635行目を修正
# 現在のコード:
"""
result_df = train_fatigue(
    long_df, scenario_out_dir, weights=fatigue_weights
)
if result_df is not None and not getattr(result_df, "empty", True):
    result_df.to_parquet(
        scenario_out_dir / "fatigue_score.parquet"
    )
"""

# 修正後のコード:
"""
# train_fatigueはモデルを返すが、内部でファイルを生成する
model = train_fatigue(
    long_df, scenario_out_dir, weights=fatigue_weights
)
# ファイルは既にtrain_fatigue内で生成されているので追加処理は不要
"""

# 修正箇所2: base_out_dirを適切な場所に変更する必要があるか確認
# 現在は work_root_path_str / "out" に保存している
# これをシナリオディレクトリに変更する必要があるかもしれない

print("修正案:")
print("1. app.pyの2629-2635行目で、train_fatigueの戻り値を正しく扱う")
print("2. train_fatigueは既に内部でファイルを生成するので、追加のto_parquet呼び出しは削除")
print("3. base_out_dirの場所を確認し、必要に応じて修正")