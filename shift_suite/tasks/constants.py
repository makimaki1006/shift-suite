# shift_suite/tasks/constants.py
"""
プロジェクト全体で使用する共通の定数を定義します。
"""
import datetime as dt # ★念のため dt もインポートしておく (将来的な定数追加用)

# ヒートマップや各種集計で使用される集計列のリスト
SUMMARY5 = ["need", "upper", "staff", "lack", "excess"]

# 他にも共通で使いたい定数があればここに追加できます。
# 例:
# DEFAULT_SLOT_MINUTES = 30
# NIGHT_START_TIME = dt.time(22, 0)
# NIGHT_END_TIME = dt.time(5, 59)