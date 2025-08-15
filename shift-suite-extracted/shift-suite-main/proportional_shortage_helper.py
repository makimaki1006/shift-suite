#!/usr/bin/env python3
"""
按分方式不足時間計算ヘルパー関数
dash_app.pyの全データフロー修正をサポート
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# shift_suiteインポート
import sys
import os
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel
from shift_suite.tasks.proportional_calculator import (
    calculate_total_shortage_from_data, 
    calculate_proportional_shortage,
    create_proportional_summary_df,
    create_employment_summary_df,
    validate_calculation_consistency
)

log = logging.getLogger(__name__)

def generate_proportional_shortage_data(excel_path: str, scenario: str = "median") -> Dict[str, pd.DataFrame]:
    """
    按分方式によるダッシュボード用データ生成
    
    Args:
        excel_path: Excelファイルパス
        scenario: シナリオ ('median', 'mean', '25th_percentile', '75th_percentile')
    
    Returns:
        ダッシュボード用データ辞書
    """
    log.info(f"按分方式データ生成開始: {scenario}シナリオ")
    
    try:
        # データ入稿フェーズ
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
        
        long_df, wt_df, unknown_codes = ingest_excel(
            Path(excel_path),
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=30,
            year_month_cell_location="D1"
        )
        
        # データ分解フェーズ
        working_data = long_df[long_df['holiday_type'] == '通常勤務'].copy()
        
        if working_data.empty:
            log.warning("勤務データが空です")
            return {}
        
        # データ分析フェーズ（統合需要モデル）
        total_shortage_hours = calculate_total_shortage_from_data(working_data, scenario)
        
        # 可視化加工フェーズ（按分計算）
        role_shortages, employment_shortages = calculate_proportional_shortage(working_data, total_shortage_hours)
        
        # 職種別サマリーDF作成
        df_shortage_role = create_proportional_summary_df(working_data, total_shortage_hours, scenario)
        
        # 「全体」行を追加（三つのレベル合計一致確保）
        if not df_shortage_role.empty:
            total_row = pd.DataFrame({
                'role': ['全体'],
                'shortage_hours': [total_shortage_hours],
                'proportion': [1.0],
                'record_count': [len(working_data)],
                'scenario': [scenario]
            })
            df_shortage_role = pd.concat([total_row, df_shortage_role], ignore_index=True)
        
        # 雇用形態別サマリーDF作成
        df_shortage_emp = create_employment_summary_df(working_data, total_shortage_hours, scenario)
        
        # 「全体」行を追加
        if not df_shortage_emp.empty:
            total_emp_row = pd.DataFrame({
                'employment': ['全体'],
                'shortage_hours': [total_shortage_hours],
                'proportion': [1.0],
                'record_count': [len(working_data)],
                'scenario': [scenario]
            })
            df_shortage_emp = pd.concat([total_emp_row, df_shortage_emp], ignore_index=True)
        
        # 既存フォーマットとの互換性確保
        if 'shortage_hours' in df_shortage_role.columns:
            df_shortage_role['lack_h'] = df_shortage_role['shortage_hours']
            df_shortage_role['excess_h'] = 0  # 按分方式では常に0
        
        if 'shortage_hours' in df_shortage_emp.columns:
            df_shortage_emp['lack_h'] = df_shortage_emp['shortage_hours']
            df_shortage_emp['excess_h'] = 0
        
        # 一貫性検証
        consistency = validate_calculation_consistency(
            total_shortage_hours, 
            role_shortages, 
            employment_shortages
        )
        
        if not consistency['all_consistent']:
            log.warning(f"一貫性検証失敗: {consistency}")
        
        log.info(f"按分方式データ生成完了: 総不足{total_shortage_hours:.2f}時間")
        
        return {
            'long_df': long_df,
            'working_data': working_data,
            'shortage_role_summary': df_shortage_role,
            'shortage_employment_summary': df_shortage_emp,
            'total_shortage_hours': total_shortage_hours,
            'consistency_check': consistency,
            'scenario': scenario
        }
        
    except Exception as e:
        log.error(f"按分方式データ生成エラー: {e}")
        return {}

def update_data_cache_with_proportional(data_cache_dict: Dict, excel_path: str, scenario: str = "median"):
    """
    既存のデータキャッシュを按分方式結果で更新
    
    Args:
        data_cache_dict: 既存のデータキャッシュ辞書
        excel_path: Excelファイルパス
        scenario: シナリオ
    """
    proportional_data = generate_proportional_shortage_data(excel_path, scenario)
    
    if proportional_data:
        # 按分方式データでキャッシュを更新
        data_cache_dict.update({
            'shortage_role_summary': proportional_data['shortage_role_summary'],
            'shortage_employment_summary': proportional_data['shortage_employment_summary'],
            'total_shortage_hours': proportional_data['total_shortage_hours'],
            'proportional_consistency': proportional_data['consistency_check']
        })
        
        log.info(f"データキャッシュ更新完了: {scenario}シナリオ")
    else:
        log.error("データキャッシュ更新失敗")

def create_consistent_shortage_summary(
    working_data: pd.DataFrame, 
    scenario: str = "median"
) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    一貫性のある不足時間サマリー作成
    
    Returns:
        (職種別DF, 雇用形態別DF, 全体不足時間)
    """
    if working_data.empty:
        return pd.DataFrame(), pd.DataFrame(), 0.0
    
    # 全体不足時間計算
    total_shortage = calculate_total_shortage_from_data(working_data, scenario)
    
    # 按分計算
    role_df = create_proportional_summary_df(working_data, total_shortage, scenario)
    employment_df = create_employment_summary_df(working_data, total_shortage, scenario)
    
    # 既存形式に変換
    if not role_df.empty:
        role_df['lack_h'] = role_df['shortage_hours']
        role_df['excess_h'] = 0
    
    if not employment_df.empty:
        employment_df['lack_h'] = employment_df['shortage_hours']
        employment_df['excess_h'] = 0
    
    return role_df, employment_df, total_shortage

def validate_dashboard_consistency(data_dict: Dict) -> Dict[str, any]:
    """
    ダッシュボードデータの一貫性検証
    """
    role_df = data_dict.get('shortage_role_summary', pd.DataFrame())
    emp_df = data_dict.get('shortage_employment_summary', pd.DataFrame())
    
    if role_df.empty or emp_df.empty:
        return {'status': 'insufficient_data'}
    
    # 全体行を除いて合計計算
    role_total = role_df[~role_df['role'].isin(['全体', '合計', '総計'])]['lack_h'].sum() if 'lack_h' in role_df.columns else 0
    emp_total = emp_df[~emp_df['employment'].isin(['全体', '合計', '総計'])]['lack_h'].sum() if 'lack_h' in emp_df.columns else 0
    
    # 全体行の値
    total_row_role = role_df[role_df['role'] == '全体']['lack_h'].iloc[0] if len(role_df[role_df['role'] == '全体']) > 0 else 0
    total_row_emp = emp_df[emp_df['employment'] == '全体']['lack_h'].iloc[0] if len(emp_df[emp_df['employment'] == '全体']) > 0 else 0
    
    tolerance = 0.01
    
    return {
        'status': 'validated',
        'role_sum': role_total,
        'employment_sum': emp_total,
        'total_role': total_row_role,
        'total_employment': total_row_emp,
        'role_consistent': abs(total_row_role - role_total) < tolerance,
        'employment_consistent': abs(total_row_emp - emp_total) < tolerance,
        'all_consistent': abs(total_row_role - total_row_emp) < tolerance and abs(total_row_role - role_total) < tolerance
    }

if __name__ == "__main__":
    # テスト実行
    excel_path = "ショート_テスト用データ.xlsx"
    
    if Path(excel_path).exists():
        print("=== 按分方式ヘルパー関数テスト ===")
        
        result = generate_proportional_shortage_data(excel_path, "median")
        
        if result:
            print(f"✓ データ生成成功")
            print(f"  - 総不足時間: {result['total_shortage_hours']:.2f}時間")
            print(f"  - 職種数: {len(result['shortage_role_summary'])}個")
            print(f"  - 雇用形態数: {len(result['shortage_employment_summary'])}個")
            
            validation = validate_dashboard_consistency(result)
            print(f"  - 一貫性: {'✓' if validation.get('all_consistent', False) else '✗'}")
        else:
            print("✗ データ生成失敗")
    else:
        print(f"✗ テストファイルが見つかりません: {excel_path}")