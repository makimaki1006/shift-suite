#!/usr/bin/env python
"""
動的パラメータ対応パッチ

app.pyからslot_hoursを直接受け取るための修正
既存のslot（分）も互換性のために維持
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, Iterable
import datetime as dt
import logging

log = logging.getLogger(__name__)

def shortage_and_brief_enhanced(
    out_dir: Union[Path, str],
    slot: Optional[int] = None,  # 分単位（既存互換性）
    slot_hours: Optional[float] = None,  # 時間単位（新規）
    *,
    holidays: Optional[Iterable[dt.date]] = None,
    include_zero_days: bool = True,
    wage_direct: float = 0.0,
    wage_temp: float = 0.0,
    penalty_per_lack: float = 0.0,
    auto_detect_slot: bool = True,
):
    """
    改良版過不足分析 - app.pyからslot_hoursを直接受け取り対応
    
    Parameters
    ----------
    out_dir : Path | str
        出力ディレクトリ
    slot : int, optional
        スロット時間（分単位）- 既存互換性のため
    slot_hours : float, optional  
        スロット時間（時間単位）- app.pyから直接指定
    holidays : Iterable[dt.date], optional
        休日リスト
    include_zero_days : bool
        ゼロ日を含めるか
    wage_direct : float
        直接雇用時給
    wage_temp : float
        派遣時給
    penalty_per_lack : float
        不足ペナルティ
    auto_detect_slot : bool
        自動スロット検出
        
    Returns
    -------
    tuple : (shortage_file_path, role_file_path) or None
    """
    
    # パラメータ優先順位の解決
    resolved_slot_hours = _resolve_slot_parameter(slot, slot_hours, auto_detect_slot, out_dir)
    
    log.info(f"[Enhanced] 動的パラメータ解決: slot_hours={resolved_slot_hours}")
    
    # 既存のshortage_and_brief呼び出し（内部でslot_hoursを使用）
    return _run_shortage_analysis_with_slot_hours(
        out_dir=out_dir,
        slot_hours=resolved_slot_hours,
        holidays=holidays,
        include_zero_days=include_zero_days,
        wage_direct=wage_direct,
        wage_temp=wage_temp,
        penalty_per_lack=penalty_per_lack
    )

def _resolve_slot_parameter(
    slot: Optional[int], 
    slot_hours: Optional[float], 
    auto_detect: bool,
    out_dir: Union[Path, str]
) -> float:
    """
    スロットパラメータの優先順位解決
    
    優先順位:
    1. slot_hours（app.pyから直接指定）
    2. slot（分単位から時間に変換）
    3. auto_detect（データから自動検出）
    4. デフォルト値（0.5時間）
    """
    
    # 1. slot_hours が直接指定されている場合（最優先）
    if slot_hours is not None:
        if slot_hours <= 0 or slot_hours > 24:
            raise ValueError(f"slot_hours={slot_hours} は無効です（0 < slot_hours <= 24）")
        log.info(f"[RESOLVE] app.pyから直接指定: {slot_hours}時間")
        return slot_hours
    
    # 2. slot（分）が指定されている場合
    if slot is not None:
        if slot <= 0 or slot > 1440:  # 1日=1440分
            raise ValueError(f"slot={slot}分 は無効です（0 < slot <= 1440）")
        calculated_hours = slot / 60.0
        log.info(f"[RESOLVE] 分から時間に変換: {slot}分 -> {calculated_hours}時間")
        return calculated_hours
    
    # 3. 自動検出が有効な場合
    if auto_detect:
        detected_hours = _detect_slot_from_data(out_dir)
        if detected_hours:
            log.info(f"[RESOLVE] データから自動検出: {detected_hours}時間")
            return detected_hours
    
    # 4. デフォルト値
    default_hours = 0.5
    log.warning(f"[RESOLVE] デフォルト値を使用: {default_hours}時間")
    return default_hours

def _detect_slot_from_data(out_dir: Union[Path, str]) -> Optional[float]:
    """データからスロット間隔を自動検出"""
    try:
        out_path = Path(out_dir)
        intermediate_file = out_path / "intermediate_data.parquet"
        
        if not intermediate_file.exists():
            log.warning("[AUTO_DETECT] intermediate_data.parquet が見つかりません")
            return None
        
        df = pd.read_parquet(intermediate_file)
        
        if 'ds' not in df.columns:
            log.warning("[AUTO_DETECT] 'ds'列が見つかりません")
            return None
        
        # 時刻データの分析
        df['datetime'] = pd.to_datetime(df['ds'])
        df_sorted = df.sort_values('datetime')
        
        # 連続する時刻の差分を計算
        time_diffs = df_sorted['datetime'].diff().dropna()
        
        # 最頻値を取得（最も一般的なスロット間隔）
        if len(time_diffs) > 0:
            mode_diff = time_diffs.mode()
            if len(mode_diff) > 0:
                slot_minutes = mode_diff.iloc[0].total_seconds() / 60
                slot_hours = slot_minutes / 60
                
                # 妥当性チェック
                if 0.1 <= slot_hours <= 2.0:  # 6分～2時間の範囲
                    log.info(f"[AUTO_DETECT] 検出成功: {slot_minutes}分 ({slot_hours}時間)")
                    return slot_hours
                else:
                    log.warning(f"[AUTO_DETECT] 検出値が範囲外: {slot_hours}時間")
        
        return None
        
    except Exception as e:
        log.error(f"[AUTO_DETECT] 自動検出エラー: {e}")
        return None

def _run_shortage_analysis_with_slot_hours(
    out_dir: Union[Path, str],
    slot_hours: float,
    holidays: Optional[Iterable[dt.date]],
    include_zero_days: bool,
    wage_direct: float,
    wage_temp: float,
    penalty_per_lack: float
):
    """
    slot_hoursを使った過不足分析の実行
    """
    from .unified_shortage_calculator import calculate_true_shortage
    
    out_dir_path = Path(out_dir)
    
    try:
        # ヒートマップデータの読み込み
        heat_all_df = pd.read_parquet(out_dir_path / "heat_ALL.parquet")
        log.info(f"[ANALYSIS] ヒートマップデータ読み込み: {heat_all_df.shape}")
        
        # 需要データの読み込み（統一されたNeedファイル使用）
        need_df = _load_unified_need_data(out_dir_path)
        
        # スタッフ配置データの準備  
        staff_df = _prepare_staff_allocation_data(heat_all_df)
        
        # 統一過不足計算の実行
        shortage_results = calculate_true_shortage(need_df, staff_df, slot_hours)
        
        # 結果の保存
        output_files = _save_shortage_results(out_dir_path, shortage_results, slot_hours)
        
        log.info(f"[ANALYSIS] 過不足分析完了: {slot_hours}時間ベース")
        return output_files
        
    except Exception as e:
        log.error(f"[ANALYSIS] 過不足分析エラー: {e}")
        return None

def _load_unified_need_data(out_dir_path: Path) -> pd.DataFrame:
    """統一されたNeedデータの読み込み"""
    
    # 修正済みのNeedファイルを優先
    corrected_file = out_dir_path / "need_per_date_slot_corrected.parquet"
    if corrected_file.exists():
        log.info("[NEED] 修正済みNeedファイルを使用")
        return pd.read_parquet(corrected_file)
    
    # 統合Needファイル
    combined_files = list(out_dir_path.glob("need_per_date_slot_role_*.parquet"))
    if combined_files:
        log.info(f"[NEED] 職種別Needファイルを統合: {len(combined_files)}個")
        
        combined_df = pd.DataFrame()
        for file_path in combined_files:
            role_df = pd.read_parquet(file_path)
            if combined_df.empty:
                combined_df = role_df.copy()
            else:
                combined_df = combined_df.add(role_df, fill_value=0)
        
        return combined_df
    
    # フォールバック: 従来ファイル
    fallback_file = out_dir_path / "need_per_date_slot.parquet"
    if fallback_file.exists():
        log.warning("[NEED] フォールバック: 従来ファイルを使用")
        return pd.read_parquet(fallback_file)
    
    raise FileNotFoundError("Needデータファイルが見つかりません")

def _prepare_staff_allocation_data(heat_all_df: pd.DataFrame) -> pd.DataFrame:
    """スタッフ配置データの準備"""
    # 日付列を特定（SUMMARY列以外）
    SUMMARY_COLS = ['staff', 'role', 'employment', 'total', 'percentage']
    date_columns = [col for col in heat_all_df.columns if col not in SUMMARY_COLS]
    
    # インデックス（時間帯）と日付列のデータを抽出
    staff_df = heat_all_df[date_columns].fillna(0)
    
    log.info(f"[STAFF] スタッフ配置データ準備: {staff_df.shape}")
    return staff_df

def _save_shortage_results(out_dir_path: Path, results: dict, slot_hours: float) -> tuple:
    """結果の保存"""
    
    # 時間軸別不足ファイル
    shortage_time_file = out_dir_path / "shortage_time_enhanced.parquet"
    results['shortage_only'].to_parquet(shortage_time_file)
    
    # 真の過不足ファイル
    true_balance_file = out_dir_path / "true_balance.parquet"
    results['true_balance'].to_parquet(true_balance_file)
    
    # 過剰ファイル
    excess_file = out_dir_path / "excess_only.parquet"
    results['excess_only'].to_parquet(excess_file)
    
    # 分析サマリー
    summary_file = out_dir_path / "shortage_analysis_summary.json"
    import json
    
    summary_data = {
        'analysis_method': 'enhanced_dynamic_parameter',
        'slot_hours': slot_hours,
        'net_hours': results['net_hours'],
        'shortage_hours': results['shortage_hours'],
        'excess_hours': results['excess_hours'],
        'statistics': results['statistics'],
        'validation': results['validation'],
        'generated_files': [
            str(shortage_time_file.name),
            str(true_balance_file.name),
            str(excess_file.name)
        ]
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    log.info(f"[SAVE] 結果保存完了: {len(summary_data['generated_files'])}ファイル")
    
    return (shortage_time_file, true_balance_file)

# app.py での使用例
def example_app_integration():
    """
    app.py での統合例
    """
    
    # UI設定値
    slot_minutes_from_ui = 30  # UIのスライダーから
    slot_hours_from_ui = slot_minutes_from_ui / 60.0  # 0.5
    
    output_directory = "path/to/output"
    
    # 新しい関数の呼び出し（推奨）
    results = shortage_and_brief_enhanced(
        out_dir=output_directory,
        slot_hours=slot_hours_from_ui,  # 直接時間を指定
        wage_direct=1500,
        wage_temp=2200
    )
    
    # 従来の呼び出し方法（互換性維持）
    results_compat = shortage_and_brief_enhanced(
        out_dir=output_directory,
        slot=slot_minutes_from_ui,  # 分で指定
        wage_direct=1500,
        wage_temp=2200
    )
    
    return results

if __name__ == "__main__":
    print("動的パラメータ対応パッチ")
    print("使用方法:")
    print("1. slot_hours=0.5 で直接時間指定（推奨）")
    print("2. slot=30 で分指定（既存互換性）")
    print("3. auto_detect=True でデータから自動検出")