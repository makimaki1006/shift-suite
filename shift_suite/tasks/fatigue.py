"""shift_suite.fatigue – 疲労リスクスコアリング (包括的分析)"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from .utils import save_df_xlsx, save_df_parquet, log
from .constants import FATIGUE_PARAMETERS
from .analyzers.rest_time import RestTimeAnalyzer


def _get_time_category(code_str: str) -> str:
    """勤務コードから時間帯カテゴリを判定"""
    if pd.isna(code_str):
        return "other"
    code_str = str(code_str).lower()
    
    # 夜勤の判定
    night_keywords = ["夜", "夜勤", "night", "準夜", "深夜"]
    if any(keyword in code_str for keyword in night_keywords):
        return "night"
    
    # 日勤の判定
    day_keywords = ["日", "日勤", "day", "早番", "朝"]
    if any(keyword in code_str for keyword in day_keywords):
        return "day"
    
    # 遅番の判定
    late_keywords = ["遅", "遅番", "late", "夕"]
    if any(keyword in code_str for keyword in late_keywords):
        return "late"
    
    return "other"


def _analyze_consecutive_days(long_df: pd.DataFrame) -> list:
    """連続勤務日数の分析"""
    consecutive_metrics = []
    
    # スタッフごとの連続勤務を分析
    for staff in long_df["staff"].unique():
        staff_df = long_df[long_df["staff"] == staff].copy()
        staff_df["date"] = pd.to_datetime(staff_df["ds"]).dt.date
        work_dates = sorted(staff_df["date"].unique())
        
        if len(work_dates) < 2:
            consecutive_metrics.append({
                "staff": staff,
                "consec3_ratio": 0,
                "consec4_ratio": 0,
                "consec5_ratio": 0
            })
            continue
        
        # 連続勤務パターンの検出
        consecutive_groups = []
        current_group = [work_dates[0]]
        
        for i in range(1, len(work_dates)):
            prev_date = work_dates[i-1]
            curr_date = work_dates[i]
            
            # 1日の差があるかチェック
            if (curr_date - prev_date).days == 1:
                current_group.append(curr_date)
            else:
                if len(current_group) >= 3:  # 3日以上の連勤のみ記録
                    consecutive_groups.append(len(current_group))
                current_group = [curr_date]
        
        # 最後のグループもチェック
        if len(current_group) >= 3:
            consecutive_groups.append(len(current_group))
        
        # 連勤パターンの比率計算
        total_work_days = len(work_dates)
        consec3_days = sum(1 for x in consecutive_groups if x >= 3)
        consec4_days = sum(1 for x in consecutive_groups if x >= 4)
        consec5_days = sum(1 for x in consecutive_groups if x >= 5)
        
        consecutive_metrics.append({
            "staff": staff,
            "consec3_ratio": consec3_days / max(total_work_days, 1),
            "consec4_ratio": consec4_days / max(total_work_days, 1),
            "consec5_ratio": consec5_days / max(total_work_days, 1)
        })
    
    return consecutive_metrics


def _features(long_df: pd.DataFrame, slot_minutes: int = 30) -> pd.DataFrame:
    """疲労分析用の特徴量を生成"""
    
    # Check if 'name' column exists, fallback to 'staff' if not
    groupby_col = "name" if "name" in long_df.columns else "staff"
    
    # データのコピーと前処理
    work_df = long_df[long_df["parsed_slots_count"] > 0].copy()
    work_df["staff"] = work_df[groupby_col]
    
    # 日付と時間の処理
    work_df["date"] = pd.to_datetime(work_df["ds"]).dt.date
    
    # start_time列のチェック
    if "start_time" in work_df.columns:
        work_df["start_hour"] = pd.to_datetime(work_df["start_time"]).dt.hour
    else:
        log.warning("start_time列が見つかりません。デフォルト値（9時）を使用します")
        work_df["start_hour"] = 9  # デフォルト値
    
    work_df["slots"] = work_df["parsed_slots_count"]
    work_df["time_category"] = work_df["code"].apply(_get_time_category)
    
    # 日次データの生成
    daily = (
        work_df.groupby(["staff", "date"])
        .agg({
            "start_hour": "mean",
            "slots": "sum",
            "time_category": lambda x: x.mode().iloc[0] if not x.empty else "other"
        })
        .reset_index()
    )
    
    # 基本メトリクス
    basic = (
        daily.groupby("staff")
        .agg({
            "date": "count",  # total_days
            "time_category": lambda x: sum(1 for cat in x if cat == "night")  # night_days
        })
        .rename(columns={"date": "total_days", "time_category": "night_days"})
    )
    
    # ① 勤務開始時刻のばらつき
    start_std = daily.groupby("staff")["start_hour"].std(ddof=0).fillna(0)
    
    # ② 業務コードの多様性
    code_diversity = work_df.groupby("staff")["code"].nunique()
    
    # ③ 労働時間のばらつき
    daily["work_hours"] = daily["slots"] * slot_minutes / 60.0
    worktime_std = daily.groupby("staff")["work_hours"].std(ddof=0).fillna(0)
    
    # ④ 休息時間ペナルティ
    try:
        rest_df = RestTimeAnalyzer().analyze(long_df, slot_minutes=slot_minutes)
        min_rest_hours = FATIGUE_PARAMETERS.get("min_rest_hours", 11)
        rest_df["penalty"] = (min_rest_hours - rest_df["rest_hours"]).clip(lower=0)
        rest_penalty = rest_df.groupby("staff")["penalty"].mean() / min_rest_hours
    except Exception as e:
        log.warning(f"Rest time analysis failed: {e}")
        # フォールバック: 全スタッフに0を設定
        all_staff = work_df["staff"].unique()
        rest_penalty = pd.Series(index=all_staff, data=0.0)
        rest_penalty.index.name = "staff"
    
    # ⑤ 連続勤務日数
    consec_metrics = _analyze_consecutive_days(work_df)
    consec_df = pd.DataFrame(consec_metrics).set_index("staff")
    
    # ⑥ 夜勤比率（調整済み）
    basic["night_ratio"] = (basic["night_days"] / basic["total_days"].replace(0, pd.NA)).fillna(0)
    basic["night_ratio_adj"] = np.clip(basic["night_ratio"], 0, 0.8) / 0.8
    
    # 特徴量を結合
    feats = pd.concat([
        start_std.rename("start_std"),
        code_diversity.rename("code_diversity"),
        worktime_std.rename("worktime_std"),
        rest_penalty.rename("rest_penalty"),
        consec_df,
        basic[["night_ratio_adj"]],
    ], axis=1).fillna(0)
    
    return feats


def train_fatigue(long_df: pd.DataFrame, out_dir: Path, weights: dict = None, slot_minutes: int = 30):
    """疲労分析を実行し、結果を保存"""
    
    X = _features(long_df, slot_minutes)
    
    # デフォルト重み
    weights_default = {
        "start_var": 1.0,
        "diversity": 1.0,
        "worktime_var": 1.0,
        "short_rest": 1.0,
        "consecutive": 1.0,
        "night_ratio": 1.0,
    }
    if weights:
        weights_default.update(weights)
    w = weights_default
    
    # 連続勤務スコアの計算
    consec_score = (
        FATIGUE_PARAMETERS.get("consecutive_3_days_weight", 1.0) * X.get("consec3_ratio", 0)
        + FATIGUE_PARAMETERS.get("consecutive_4_days_weight", 2.0) * X.get("consec4_ratio", 0)
        + FATIGUE_PARAMETERS.get("consecutive_5_days_weight", 3.0) * X.get("consec5_ratio", 0)
    )
    
    # パーセンタイル正規化
    norm_df = X.rank(pct=True).fillna(0)
    
    # 重み付き疲労スコア計算
    X["fatigue_score"] = (
        w["start_var"] * norm_df.get("start_std", 0)
        + w["diversity"] * norm_df.get("code_diversity", 0)
        + w["worktime_var"] * norm_df.get("worktime_std", 0)
        + w["short_rest"] * norm_df.get("rest_penalty", 0)
        + w["consecutive"] * consec_score
        + w["night_ratio"] * norm_df.get("night_ratio_adj", 0)
    )
    
    # 正規化と最終調整
    total_w = sum(w.values())
    if total_w > 0:
        X["fatigue_score"] = X["fatigue_score"] / total_w * 100
    X["fatigue_score"] = X["fatigue_score"].clip(0, 100).round(2)
    
    # ダッシュボード用の列名に変換
    output_df = X.copy()
    output_df.rename(columns={
        "start_std": "work_start_variance",
        "code_diversity": "work_diversity", 
        "worktime_std": "work_duration_variance",
        "rest_penalty": "short_rest_frequency",
        "night_ratio_adj": "night_shift_ratio"
    }, inplace=True)
    
    # 連続勤務の合成スコア
    output_df["consecutive_work_days"] = consec_score
    
    # 必要な列のみを保存
    cols_to_save = [
        "fatigue_score", "work_start_variance", "work_diversity",
        "work_duration_variance", "short_rest_frequency", 
        "consecutive_work_days", "night_shift_ratio"
    ]
    available_cols = [col for col in cols_to_save if col in output_df.columns]
    final_df = output_df[available_cols]
    
    # 両形式で保存（互換性確保）
    save_df_xlsx(final_df, out_dir / "fatigue_score.xlsx", "fatigue", index=True)
    result_path = out_dir / "fatigue_score.parquet"
    save_df_parquet(final_df, result_path, index=True)
    
    log.info(f"fatigue: comprehensive analysis completed, saved {len(available_cols)} features for {len(final_df)} staff")
    return result_path