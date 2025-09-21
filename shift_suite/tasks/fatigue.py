"""shift_suite.fatigue – 疲労リスクスコアリング (包括的分析)"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from .utils import save_df_xlsx, save_df_parquet, log
from .constants import FATIGUE_PARAMETERS
from .analyzers.rest_time import RestTimeAnalyzer

# PyTorch LSTM疲労予測モデルのインポート（利用可能な場合）
try:
    from .pytorch_fatigue_predictor import PyTorchFatiguePredictor
    _HAS_PYTORCH = True
    log.info("[fatigue] PyTorch LSTM model available for advanced fatigue prediction")
except ImportError:
    _HAS_PYTORCH = False
    log.info("[fatigue] Using statistical fatigue model (PyTorch not available)")


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
        basic[["night_ratio_adj", "total_days"]],  # total_daysも含める
    ], axis=1).fillna(0)
    
    return feats


def train_fatigue(long_df: pd.DataFrame, out_dir: Path, weights: dict = None, slot_minutes: int = 30, use_pytorch: bool = None):
    """疲労分析を実行し、結果を保存
    
    Parameters
    ----------
    long_df : pd.DataFrame
        分析対象データ
    out_dir : Path
        出力ディレクトリ
    weights : dict, optional
        重み設定（統計モデル用）
    slot_minutes : int
        時間スロット（分）
    use_pytorch : bool, optional
        PyTorchモデルを使用するか（None = 自動判定）
    """
    
    # PyTorchモデルの使用判定
    if use_pytorch is None:
        use_pytorch = _HAS_PYTORCH and len(long_df) >= 100  # 100件以上のデータがあればPyTorch使用
    
    if use_pytorch and _HAS_PYTORCH:
        log.info("[fatigue] Using PyTorch LSTM model for advanced fatigue prediction")
        return _train_fatigue_pytorch(long_df, out_dir)
    else:
        log.info("[fatigue] Using statistical model for fatigue analysis")
        return _train_fatigue_statistical(long_df, out_dir, weights, slot_minutes)


def _train_fatigue_pytorch(long_df: pd.DataFrame, out_dir: Path):
    """PyTorch LSTMモデルによる疲労分析"""
    
    # データ準備
    df = long_df.copy()
    df['date'] = pd.to_datetime(df['ds'])
    df['work_hours'] = df.get('work_hours', 8)  # デフォルト8時間
    df['is_night_shift'] = df['code'].apply(lambda x: 1 if _get_time_category(x) == 'night' else 0)
    df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6]).astype(int)
    
    # PyTorchモデル初期化と訓練
    predictor = PyTorchFatiguePredictor(sequence_length=7)  # 7日間の履歴使用
    
    # モデル訓練
    training_results = predictor.train_model(df, epochs=50, batch_size=16)
    
    # 予測実行
    predicted_df = predictor.predict_fatigue(df)
    
    # スタッフごとの最新疲労度を集計
    staff_fatigue = predicted_df.groupby('staff').agg({
        'fatigue_score': 'last',
        'risk_level': 'last',
        'consecutive_days': 'max',
        'weekly_total_hours': 'last'
    }).reset_index()
    
    # 出力形式の整形
    output_df = pd.DataFrame(index=staff_fatigue['staff'])
    output_df['fatigue_score'] = (staff_fatigue.set_index('staff')['fatigue_score'] * 100).round(2)
    output_df['risk_level'] = staff_fatigue.set_index('staff')['risk_level']
    output_df['consecutive_work_days'] = staff_fatigue.set_index('staff')['consecutive_days']
    output_df['weekly_hours'] = staff_fatigue.set_index('staff')['weekly_total_hours']
    
    # モデル性能メトリクスも保存
    output_df['model_mse'] = training_results.get('final_mse', 0)
    output_df['model_correlation'] = training_results.get('correlation', 0)
    
    # 保存
    save_df_xlsx(output_df, out_dir / "fatigue_score.xlsx", "fatigue", index=True)
    result_path = out_dir / "fatigue_score.parquet"
    save_df_parquet(output_df, result_path, index=True)
    
    log.info(f"[fatigue] PyTorch LSTM analysis completed - MSE: {training_results.get('final_mse', 0):.4f}, Correlation: {training_results.get('correlation', 0):.4f}")
    return result_path


def _normalize_robust(series: pd.Series, use_iqr_clipping: bool = True) -> pd.Series:
    """ロバストな正規化（外れ値耐性付き）
    
    Parameters:
    -----------
    series : pd.Series
        正規化対象のデータ
    use_iqr_clipping : bool
        IQRベースの外れ値クリッピングを使用するか
    """
    if len(series) == 0 or series.isna().all():
        return pd.Series(0, index=series.index)
    
    if use_iqr_clipping and len(series) > 3:
        # IQRベースの外れ値クリッピング
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        if iqr > 0:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            series = series.clip(lower, upper)
    
    # Min-Max正規化
    min_val = series.min()
    max_val = series.max()
    if max_val > min_val:
        return (series - min_val) / (max_val - min_val)
    return pd.Series(0, index=series.index)


def _train_fatigue_statistical(long_df: pd.DataFrame, out_dir: Path, weights: dict = None, slot_minutes: int = 30):
    """従来の統計的疲労分析（後方互換性）"""
    
    X = _features(long_df, slot_minutes)
    
    # デフォルト重み（夜勤の重みを強化）
    weights_default = {
        "start_var": 1.0,
        "diversity": 1.0,
        "worktime_var": 1.0,
        "short_rest": 1.2,  # 短い休息の重みを強化
        "consecutive": 1.3,  # 連続勤務の重みを強化
        "night_ratio": 2.0,  # 夜勤の重みを1.5→2.0にさらに強化
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
    
    # ロバストな正規化（特徴量ごとに適切な方法を選択）
    norm_df = pd.DataFrame(index=X.index)
    
    # 相対的評価が適切な特徴量（IQRクリッピング付き）
    for col in ["start_std", "worktime_std"]:
        if col in X.columns:
            norm_df[col] = _normalize_robust(X[col], use_iqr_clipping=True)
        else:
            norm_df[col] = 0
    
    # 絶対値に意味がある特徴量（既に制約済み）
    for col in ["code_diversity", "rest_penalty", "night_ratio_adj"]:
        if col in X.columns:
            norm_df[col] = _normalize_robust(X[col], use_iqr_clipping=False)
        else:
            norm_df[col] = 0
    
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
    
    # 勤務頻度による調整（月間想定勤務日数を20日として計算）
    # total_daysは_features()から取得済み
    expected_monthly_days = 20  # 月間標準勤務日数
    
    # 頻度調整係数を計算（シグモイド関数で滑らかな調整）
    # - 連続的な減衰で不連続性を回避
    # - 極端に少ない勤務（3日未満）のみ強く減衰
    import numpy as np
    
    def smooth_frequency_factor(days):
        """滑らかな頻度調整係数を計算（最終調整版）"""
        if days >= expected_monthly_days:
            return 1.0
        elif days >= 15:
            # 15-19日: ほぼ正社員レベル（0.85-1.0）
            return 0.85 + 0.15 * (days - 15) / 5
        elif days >= 10:
            # 10-14日: 中間層（0.65-0.85）
            return 0.65 + 0.20 * (days - 10) / 5
        elif days >= 5:
            # 5-9日: パートレベル（0.35-0.65）
            return 0.35 + 0.30 * (days - 5) / 5
        elif days >= 3:
            # 3-4日: 低頻度（0.2-0.35）
            return 0.2 + 0.15 * (days - 3) / 2
        else:
            # 3日未満: 超低頻度（0.05-0.2）
            return 0.05 + 0.15 * days / 3
    
    frequency_factor = X["total_days"].apply(smooth_frequency_factor)
    
    # 頻度調整を適用
    X["fatigue_score_raw"] = X["fatigue_score"]  # 調整前の値を保存
    X["fatigue_score"] = X["fatigue_score"] * frequency_factor
    
    # 最小スコア保証（正社員レベルの勤務者）
    for idx in X.index:
        total_days = X.loc[idx, "total_days"]
        # night_ratio_adjが正しい列名（0-1に正規化済み）
        night_ratio = X.loc[idx, "night_ratio_adj"] if "night_ratio_adj" in X.columns else 0
        
        # 18日以上勤務かつ夜勤がある場合、最小30点を保証（閾値を緩和）
        if total_days >= 18 and night_ratio >= 0.15:
            X.loc[idx, "fatigue_score"] = max(X.loc[idx, "fatigue_score"], 30)
        
        # 23日以上勤務かつ夜勤率40%以上の場合、最小70点を保証（閾値を緩和）
        if total_days >= 23 and night_ratio >= 0.4:
            X.loc[idx, "fatigue_score"] = max(X.loc[idx, "fatigue_score"], 70)
        
        # 25日以上勤務の場合、夜勤率に関わらず最小60点を保証
        if total_days >= 25:
            X.loc[idx, "fatigue_score"] = max(X.loc[idx, "fatigue_score"], 60)
    
    # 100点を超える場合は警告フラグを立てる（クリップはしない）
    X["is_extreme_fatigue"] = X["fatigue_score"] > 100
    X["fatigue_category"] = pd.cut(
        X["fatigue_score"],
        bins=[0, 30, 60, 80, 100, float('inf')],
        labels=["低", "中", "高", "非常に高", "危険"],
        include_lowest=True
    )
    
    # 表示用スコア（100点を超えても保持）
    X["fatigue_score_display"] = X["fatigue_score"].round(2)
    
    # 互換性のため、fatigue_scoreは100でクリップ（警告付き）
    if (X["fatigue_score"] > 100).any():
        extreme_staff = X[X["fatigue_score"] > 100].index.tolist()
        log.warning(f"⚠️ 疲労度が100を超えるスタッフ: {extreme_staff}")
        log.warning(f"  実際の値: {X.loc[extreme_staff, 'fatigue_score_display'].to_dict()}")
    
    X["fatigue_score"] = X["fatigue_score"].clip(0, 100).round(2)
    
    # デバッグ用：頻度係数も保存
    X["frequency_factor"] = frequency_factor.round(3)
    
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