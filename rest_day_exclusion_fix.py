#!/usr/bin/env python3
"""
休日除外修正強化版
==================

シフトデータの「×」(休み)を完全に除外する修正
1. データ読み込み段階での除外
2. 集計段階での除外
3. 表示段階での除外
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def create_enhanced_rest_exclusion_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    強化版休日除外フィルター
    シフトデータの「×」やその他の休み表現を完全除外
    """
    if df.empty:
        return df
    
    original_count = len(df)
    log.info(f"[RestExclusion] 開始: {original_count}レコード")
    
    # 1. スタッフ名による除外（最も重要）
    if 'staff' in df.columns:
        # 休み関連パターンの完全リスト
        rest_patterns = [
            '×', 'X', 'x',           # 基本的な休み記号
            '休', '休み', '休暇',      # 日本語の休み
            '欠', '欠勤',             # 欠勤
            'OFF', 'off', 'Off',     # オフ
            '-', '−', '―',           # ハイフン類
            '', ' ', '　',           # 空文字・空白
            'nan', 'NaN', 'null',    # NULL値系
            '有', '有休',             # 有給
            '特', '特休',             # 特休
            '代', '代休',             # 代休
            '振', '振休'              # 振替休日
        ]
        
        # 除外カウンター
        excluded_by_pattern = {}
        
        for pattern in rest_patterns:
            if pattern.strip():  # 空文字以外
                # 完全一致 または 含む
                pattern_mask = (
                    (df['staff'].str.strip() == pattern) |
                    (df['staff'].str.contains(pattern, na=False, regex=False))
                )
                excluded_count = pattern_mask.sum()
                if excluded_count > 0:
                    excluded_by_pattern[pattern] = excluded_count
                    df = df[~pattern_mask]
            else:  # 空文字系
                empty_mask = (
                    df['staff'].isna() |
                    (df['staff'].str.strip() == '') |
                    (df['staff'].str.strip() == ' ') |
                    (df['staff'].str.strip() == '　')
                )
                excluded_count = empty_mask.sum()
                if excluded_count > 0:
                    excluded_by_pattern['empty'] = excluded_count
                    df = df[~empty_mask]
        
        if excluded_by_pattern:
            log.info(f"[RestExclusion] スタッフ名による除外: {excluded_by_pattern}")
    
    # 2. parsed_slots_count による除外
    if 'parsed_slots_count' in df.columns:
        zero_slots_mask = df['parsed_slots_count'] <= 0
        zero_slots_count = zero_slots_mask.sum()
        if zero_slots_count > 0:
            df = df[~zero_slots_mask]
            log.info(f"[RestExclusion] 0スロット除外: {zero_slots_count}件")
    
    # 3. staff_count による除外
    if 'staff_count' in df.columns:
        zero_staff_mask = df['staff_count'] <= 0
        zero_staff_count = zero_staff_mask.sum()
        if zero_staff_count > 0:
            df = df[~zero_staff_mask]
            log.info(f"[RestExclusion] 0人数除外: {zero_staff_count}件")
    
    # 4. work_hours系による除外
    work_hour_cols = [col for col in df.columns if 'work' in col.lower() and ('hour' in col.lower() or 'time' in col.lower())]
    for col in work_hour_cols:
        zero_work_mask = df[col] <= 0
        zero_work_count = zero_work_mask.sum()
        if zero_work_count > 0:
            df = df[~zero_work_mask]
            log.info(f"[RestExclusion] {col}=0除外: {zero_work_count}件")
    
    # 5. role（職種）による除外
    if 'role' in df.columns:
        rest_role_patterns = ['×', '休', '-', '', 'OFF', 'off']
        for pattern in rest_role_patterns:
            if pattern:
                role_mask = (
                    (df['role'].str.strip() == pattern) |
                    (df['role'].str.contains(pattern, na=False, regex=False))
                )
                excluded_count = role_mask.sum()
                if excluded_count > 0:
                    df = df[~role_mask]
                    log.info(f"[RestExclusion] 職種'{pattern}'除外: {excluded_count}件")
    
    final_count = len(df)
    total_excluded = original_count - final_count
    exclusion_rate = total_excluded / original_count if original_count > 0 else 0
    
    log.info(f"[RestExclusion] 完了: {original_count} -> {final_count} (除外: {total_excluded}件, {exclusion_rate:.1%})")
    
    return df

def create_test_data_with_rest_days():
    """休日データを含むテストデータ生成"""
    
    test_data = pd.DataFrame({
        'staff': [
            '田中', '佐藤', '×', '鈴木', '休',
            '田中', '佐藤', 'OFF', '鈴木', '有',
            '田中', '佐藤', '-', '鈴木', '',
            '田中', '佐藤', '欠', '鈴木', '×'
        ],
        'role': [
            '看護師', '介護士', '×', '事務', '休',
            '看護師', '介護士', '×', '事務', '休',
            '看護師', '介護士', '-', '事務', '',
            '看護師', '介護士', '×', '事務', 'OFF'
        ],
        'time': ['08:00'] * 20,
        'date_lbl': ['2025-01-01'] * 20,
        'staff_count': [1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0],
        'parsed_slots_count': [1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]
    })
    
    return test_data

def test_rest_exclusion():
    """休日除外テスト"""
    print("=" * 50)
    print("休日除外強化テスト")
    print("=" * 50)
    
    # テストデータ生成
    test_data = create_test_data_with_rest_days()
    print(f"テストデータ生成: {len(test_data)}レコード")
    print("スタッフ名分布:")
    print(test_data['staff'].value_counts())
    
    # フィルター適用
    filtered_data = create_enhanced_rest_exclusion_filter(test_data)
    print(f"\nフィルター後: {len(filtered_data)}レコード")
    print("スタッフ名分布:")
    if not filtered_data.empty:
        print(filtered_data['staff'].value_counts())
    else:
        print("データなし")
    
    # 結果検証
    excluded_count = len(test_data) - len(filtered_data)
    exclusion_rate = excluded_count / len(test_data)
    
    print(f"\n結果:")
    print(f"除外件数: {excluded_count}")
    print(f"除外率: {exclusion_rate:.1%}")
    print(f"残存データに休み記号が含まれるか: {'あり' if any('×' in str(v) or '休' in str(v) for v in filtered_data['staff'].values) else 'なし'}")

if __name__ == "__main__":
    test_rest_exclusion()