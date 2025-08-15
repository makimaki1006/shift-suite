#!/usr/bin/env python3
"""
0:00時刻の夜勤・明け番重複問題の詳細調査
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import json

print('=== 0:00重複問題の詳細調査 ===')

# 分析対象フォルダ
analysis_folder = 'temp_analysis_results/out_p25_based/'

def analyze_heat_all():
    """heat_ALL.parquetの0:00時刻分析"""
    print('\n1. heat_ALL.parquetの0:00時刻分析')
    print('=' * 50)
    
    try:
        heat_all = pd.read_parquet(f'{analysis_folder}heat_ALL.parquet')
        print(f'データ形状: {heat_all.shape}')
        print(f'列名: {heat_all.columns.tolist()}')
        
        # 時間関連の列を特定
        time_cols = [col for col in heat_all.columns if any(x in col.lower() for x in ['time', 'hour', 'slot', 'date'])]
        print(f'時間関連列: {time_cols}')
        
        # staffや人員数関連の列を特定
        staff_cols = [col for col in heat_all.columns if any(x in col.lower() for x in ['staff', 'count', 'num', 'worker'])]
        print(f'人員関連列: {staff_cols}')
        
        # データのサンプル表示
        print('\n先頭5行:')
        print(heat_all.head())
        
        # 0:00に関連するデータを探す
        if 'slot' in heat_all.columns and 'staff' in heat_all.columns:
            print('\n0:00時刻(slot=0)の分析:')
            midnight_data = heat_all[heat_all['slot'] == 0]
            print(f'0:00のデータ行数: {len(midnight_data)}')
            
            if len(midnight_data) > 0:
                print('0:00の統計:')
                print(midnight_data['staff'].describe())
                
                # 日付別の0:00人員数
                if 'date' in midnight_data.columns:
                    print('\n日付別0:00人員数:')
                    date_staff = midnight_data.groupby('date')['staff'].sum().sort_index()
                    print(date_staff.head(10))
                    
                    # 異常に多い日を特定
                    mean_staff = date_staff.mean()
                    std_staff = date_staff.std()
                    threshold = mean_staff + 2 * std_staff
                    
                    print(f'\n0:00人員数統計: 平均={mean_staff:.1f}, 標準偏差={std_staff:.1f}')
                    print(f'異常値閾値(平均+2σ): {threshold:.1f}')
                    
                    anomaly_dates = date_staff[date_staff > threshold]
                    if len(anomaly_dates) > 0:
                        print(f'\n異常に多い日({len(anomaly_dates)}日):')
                        print(anomaly_dates)
        
        # 時系列での人員推移を確認
        if 'slot' in heat_all.columns and 'staff' in heat_all.columns:
            print('\n時間帯別人員数の統計:')
            slot_stats = heat_all.groupby('slot')['staff'].agg(['mean', 'std', 'max', 'min'])
            
            # 夜間〜早朝の時間帯(slot 47, 0, 1)をピックアップ
            critical_slots = [47, 0, 1]  # 23:30, 0:00, 0:30相当
            for slot in critical_slots:
                if slot in slot_stats.index:
                    stats = slot_stats.loc[slot]
                    time_str = f'{slot//2:02d}:{(slot%2)*30:02d}'
                    print(f'  Slot {slot:2d} ({time_str}): 平均={stats["mean"]:.1f}, 最大={stats["max"]:.0f}, 最小={stats["min"]:.0f}')
            
    except Exception as e:
        print(f'heat_ALL.parquet分析エラー: {e}')

def analyze_work_patterns():
    """work_patterns.parquetの連続勤務分析"""
    print('\n2. work_patterns.parquetの連続勤務分析')
    print('=' * 50)
    
    try:
        work_patterns = pd.read_parquet(f'{analysis_folder}work_patterns.parquet')
        print(f'データ形状: {work_patterns.shape}')
        print(f'列名: {work_patterns.columns.tolist()}')
        
        print('\n先頭5行:')
        print(work_patterns.head())
        
        # 夜勤→明け番パターンの検索
        if 'shift_pattern' in work_patterns.columns or 'pattern' in work_patterns.columns:
            pattern_col = 'shift_pattern' if 'shift_pattern' in work_patterns.columns else 'pattern'
            
            # 夜勤関連パターンを探す
            night_patterns = work_patterns[work_patterns[pattern_col].str.contains('夜|明|Night|night', na=False)]
            print(f'\n夜勤関連パターン数: {len(night_patterns)}')
            
            if len(night_patterns) > 0:
                print('夜勤関連パターンの例:')
                print(night_patterns[pattern_col].value_counts().head(10))
        
        # 連続勤務の時間スロットを分析
        if 'start_slot' in work_patterns.columns and 'end_slot' in work_patterns.columns:
            print('\n0:00跨ぎ勤務パターンの分析:')
            
            # 夜間から朝にかけて跨ぐパターン (end_slot < start_slot)
            overnight_patterns = work_patterns[work_patterns['end_slot'] < work_patterns['start_slot']]
            print(f'夜間跨ぎパターン数: {len(overnight_patterns)}')
            
            if len(overnight_patterns) > 0:
                print('夜間跨ぎパターンの例:')
                for _, pattern in overnight_patterns.head(5).iterrows():
                    start_time = f'{pattern["start_slot"]//2:02d}:{(pattern["start_slot"]%2)*30:02d}'
                    end_time = f'{pattern["end_slot"]//2:02d}:{(pattern["end_slot"]%2)*30:02d}'
                    print(f'  {start_time} → {end_time}')
        
    except Exception as e:
        print(f'work_patterns.parquet分析エラー: {e}')

def analyze_intermediate_data():
    """intermediate_data.parquetの詳細分析"""
    print('\n3. intermediate_data.parquetの詳細分析')
    print('=' * 50)
    
    try:
        intermediate = pd.read_parquet(f'{analysis_folder}intermediate_data.parquet')
        print(f'データ形状: {intermediate.shape}')
        print(f'列名: {intermediate.columns.tolist()}')
        
        print('\n先頭5行:')
        print(intermediate.head())
        
        # 日付と時間スロットでの人員配置を確認
        if 'date' in intermediate.columns and 'slot' in intermediate.columns:
            print('\n6月2日〜3日の0:00前後の詳細分析:')
            
            # 特定日付での分析
            target_dates = ['2024-06-02', '2024-06-03']
            
            for date_str in target_dates:
                if intermediate['date'].astype(str).str.contains(date_str).any():
                    date_data = intermediate[intermediate['date'].astype(str).str.contains(date_str)]
                    
                    # 0:00前後のスロット (23:45, 0:00, 0:15相当)
                    critical_slots = [47, 0, 1]
                    
                    print(f'\n{date_str}の0:00前後:')
                    for slot in critical_slots:
                        slot_data = date_data[date_data['slot'] == slot]
                        if len(slot_data) > 0:
                            time_str = f'{slot//2:02d}:{(slot%2)*30:02d}'
                            staff_count = len(slot_data) if 'staff_id' in slot_data.columns else slot_data.get('staff', 0).sum()
                            print(f'  Slot {slot:2d} ({time_str}): {staff_count}人')
        
    except Exception as e:
        print(f'intermediate_data.parquet分析エラー: {e}')

def compare_time_slots():
    """23:45, 0:00, 0:15の人員推移比較"""
    print('\n4. 時間スロット別人員推移の比較分析')
    print('=' * 50)
    
    try:
        heat_all = pd.read_parquet(f'{analysis_folder}heat_ALL.parquet')
        
        if 'slot' in heat_all.columns and 'staff' in heat_all.columns:
            # 重要な時間スロット
            critical_slots = [47, 0, 1]  # 23:30, 0:00, 0:30
            slot_names = ['23:30', '0:00', '0:30']
            
            print('時間スロット別人員統計:')
            print('スロット | 時刻  | 平均人員 | 最大人員 | 最小人員 | 標準偏差')
            print('-' * 60)
            
            slot_data = {}
            for i, slot in enumerate(critical_slots):
                slot_subset = heat_all[heat_all['slot'] == slot]['staff']
                if len(slot_subset) > 0:
                    stats = {
                        'mean': slot_subset.mean(),
                        'max': slot_subset.max(),
                        'min': slot_subset.min(),
                        'std': slot_subset.std()
                    }
                    slot_data[slot] = stats
                    print(f'{slot:8d} | {slot_names[i]:5s} | {stats["mean"]:8.1f} | {stats["max"]:8.0f} | {stats["min"]:8.0f} | {stats["std"]:8.1f}')
            
            # 0:00の異常値検出
            if 0 in slot_data:
                midnight_stats = slot_data[0]
                other_slots_mean = np.mean([slot_data[s]['mean'] for s in slot_data if s != 0])
                
                print(f'\n0:00の分析:')
                print(f'  0:00平均人員: {midnight_stats["mean"]:.1f}')
                print(f'  他時間平均人員: {other_slots_mean:.1f}')
                print(f'  差分: {midnight_stats["mean"] - other_slots_mean:+.1f}')
                print(f'  比率: {midnight_stats["mean"] / other_slots_mean:.2f}倍')
                
                if midnight_stats["mean"] > other_slots_mean * 1.5:
                    print('  ⚠️ 0:00で異常に多い人員が検出されました!')
        
    except Exception as e:
        print(f'時間スロット比較分析エラー: {e}')

def quantify_overlap_problem():
    """重複問題の定量化"""
    print('\n5. 重複問題の定量化')
    print('=' * 50)
    
    try:
        # メタデータファイルの確認
        meta_files = ['heatmap.meta.json', 'shortage.meta.json']
        
        for meta_file in meta_files:
            meta_path = f'{analysis_folder}{meta_file}'
            if os.path.exists(meta_path):
                print(f'\n{meta_file}の内容:')
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                    print(json.dumps(meta_data, indent=2, ensure_ascii=False))
        
        # shortage関連データの確認
        shortage_files = [f for f in os.listdir(analysis_folder) if f.startswith('shortage_')]
        print(f'\n不足データファイル: {shortage_files}')
        
        for shortage_file in shortage_files[:3]:  # 最初の3ファイル
            try:
                shortage_df = pd.read_parquet(f'{analysis_folder}{shortage_file}')
                print(f'\n{shortage_file}:')
                print(f'  形状: {shortage_df.shape}')
                print(f'  列: {shortage_df.columns.tolist()}')
                
                # 0:00関連の不足データを確認
                if 'slot' in shortage_df.columns:
                    midnight_shortage = shortage_df[shortage_df['slot'] == 0]
                    if len(midnight_shortage) > 0:
                        print(f'  0:00の不足データ行数: {len(midnight_shortage)}')
                        if 'shortage' in shortage_df.columns:
                            print(f'  0:00平均不足: {midnight_shortage["shortage"].mean():.1f}')
            except Exception as e:
                print(f'  {shortage_file}読み込みエラー: {e}')
    
    except Exception as e:
        print(f'定量化分析エラー: {e}')

# メイン実行
if __name__ == '__main__':
    # 分析対象フォルダの確認
    if not os.path.exists(analysis_folder):
        print(f'エラー: {analysis_folder} が見つかりません')
        exit(1)
    
    print(f'分析対象: {analysis_folder}')
    
    # 各分析の実行
    analyze_heat_all()
    analyze_work_patterns()
    analyze_intermediate_data()
    compare_time_slots()
    quantify_overlap_problem()
    
    print('\n=== 調査完了 ===')