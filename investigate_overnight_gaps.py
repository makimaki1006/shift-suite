#!/usr/bin/env python3
"""
明け番シフトの連続勤務が途切れている問題を調査
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import sys
sys.path.append('.')

def investigate_overnight_gaps():
    """明け番シフトの時間的連続性を調査"""
    try:
        # 最新の分析結果から中間データを読み込み
        intermediate_path = "analysis_results_20/out_p25_based/intermediate_data.parquet"
        df = pd.read_parquet(intermediate_path)
        
        print(f"Intermediate data shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # 明シフトのデータのみを抽出
        ake_data = df[df['code'] == '明'].copy()
        print(f"\n明シフトレコード数: {len(ake_data)}")
        
        if len(ake_data) > 0:
            # 時刻情報を抽出
            ake_data['hour'] = ake_data['ds'].dt.hour
            ake_data['minute'] = ake_data['ds'].dt.minute
            ake_data['time_slot'] = ake_data['hour'].astype(str).str.zfill(2) + ':' + ake_data['minute'].astype(str).str.zfill(2)
            
            print(f"\n明シフトの時間分布:")
            time_dist = ake_data['time_slot'].value_counts().sort_index()
            print(time_dist)
            
            # 連続性の確認
            print(f"\n時間スロットの連続性チェック:")
            unique_times = sorted(ake_data['time_slot'].unique())
            print(f"明シフトに含まれる時間スロット: {unique_times}")
            
            # 期待される明シフトの時間スロット（00:00-10:00、30分間隔）
            expected_slots = []
            for hour in range(0, 10):  # 0時から9時まで
                expected_slots.append(f"{hour:02d}:00")
                expected_slots.append(f"{hour:02d}:30")
            
            print(f"\n期待される明シフト時間スロット: {expected_slots}")
            
            # 欠けている時間スロットを特定
            missing_slots = [slot for slot in expected_slots if slot not in unique_times]
            if missing_slots:
                print(f"\n警告: 欠けている時間スロット: {missing_slots}")
            else:
                print(f"\nOK: すべての期待される時間スロットが存在します")
            
            # 特定の日付での明シフトの連続性を確認
            print(f"\n日別の明シフト連続性チェック:")
            ake_data['date'] = ake_data['ds'].dt.date
            
            for date in sorted(ake_data['date'].unique())[:5]:  # 最初の5日をチェック
                date_data = ake_data[ake_data['date'] == date]
                date_times = sorted(date_data['time_slot'].unique())
                
                # 連続していない時間スロットを検出
                gaps = []
                for i in range(len(date_times) - 1):
                    current_time = datetime.strptime(date_times[i], '%H:%M').time()
                    next_time = datetime.strptime(date_times[i + 1], '%H:%M').time()
                    
                    # 30分後の時刻を計算
                    current_minutes = current_time.hour * 60 + current_time.minute
                    next_minutes = next_time.hour * 60 + next_time.minute
                    
                    if next_minutes - current_minutes > 30:
                        gaps.append(f"{date_times[i]} -> {date_times[i + 1]}")
                
                if gaps:
                    print(f"  {date}: ギャップ検出 - {gaps}")
                else:
                    print(f"  {date}: 連続性OK - {date_times}")
            
            # 職員別の明シフト実施状況
            print(f"\n職員別の明シフト実施状況:")
            staff_ake = ake_data.groupby('staff').agg({
                'time_slot': 'nunique',
                'ds': 'count'
            }).rename(columns={'time_slot': 'unique_time_slots', 'ds': 'total_records'})
            
            print(staff_ake.head(10))
            
        else:
            print("明シフトのデータが見つかりません")
            
        # 勤務パターンデータも確認
        print(f"\n勤務パターンデータの確認:")
        work_patterns_path = "analysis_results_20/out_p25_based/work_patterns.parquet"
        wp_df = pd.read_parquet(work_patterns_path)
        
        ake_pattern = wp_df[wp_df['code'] == '明']
        if len(ake_pattern) > 0:
            print(f"明パターン定義:")
            print(ake_pattern.to_string())
        else:
            print("勤務パターンに明が見つかりません")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_overnight_gaps()