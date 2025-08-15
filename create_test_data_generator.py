#!/usr/bin/env python3
"""
UAT用テストデータ生成器
各種テストシナリオに対応したExcelファイルを自動生成
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import sys
import os

def create_standard_test_data():
    """標準テストデータの生成 (A1-S01用)"""
    print("標準テストデータ生成中...")
    
    # 基本設定
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # スタッフ情報
    staff_list = [
        {'name': '田中太郎', 'role': '介護士', 'employment': '正社員'},
        {'name': '佐藤花子', 'role': '看護師', 'employment': '正社員'},
        {'name': '山田次郎', 'role': '介護士', 'employment': 'パート'},
        {'name': '鈴木美子', 'role': '相談員', 'employment': '正社員'},
        {'name': '高橋一郎', 'role': '介護士', 'employment': 'パート'},
    ]
    
    # シフトコード定義
    shift_codes = {
        'D': {'start_hour': 9, 'end_hour': 17, 'duration': 8, 'name': '日勤'},
        'E': {'start_hour': 7, 'end_hour': 15, 'duration': 8, 'name': '早番'},
        'L': {'start_hour': 11, 'end_hour': 19, 'duration': 8, 'name': '遅番'},
        'N': {'start_hour': 21, 'end_hour': 5, 'duration': 8, 'name': '夜勤'},
        'H': {'start_hour': 0, 'end_hour': 0, 'duration': 0, 'name': '休日'},
    }
    
    test_data = []
    
    # データ生成
    for date in dates:
        weekday = date.weekday()  # 0=月曜日
        
        for staff in staff_list:
            # 勤務確率の設定
            work_probability = 0.75  # 基本勤務確率
            
            # 週末は勤務確率下げる
            if weekday >= 5:  # 土日
                work_probability = 0.4
            
            # パートタイムは勤務日数少なめ
            if staff['employment'] == 'パート':
                work_probability *= 0.7
            
            if np.random.random() < work_probability:
                # シフト選択
                if staff['role'] == '看護師':
                    # 看護師は夜勤多め
                    shift_choices = ['D', 'N']
                    shift_weights = [0.6, 0.4]
                elif staff['employment'] == 'パート':
                    # パートは日中のみ
                    shift_choices = ['D', 'E', 'L']  
                    shift_weights = [0.5, 0.3, 0.2]
                else:
                    # フルタイムは全シフト
                    shift_choices = ['D', 'E', 'L', 'N']
                    shift_weights = [0.4, 0.2, 0.2, 0.2]
                
                chosen_shift = np.random.choice(shift_choices, p=shift_weights)
            else:
                chosen_shift = 'H'  # 休日
            
            # 30分スロット単位でレコード生成
            if chosen_shift != 'H':
                shift_info = shift_codes[chosen_shift]
                slots_per_hour = 2  # 30分スロット
                total_slots = shift_info['duration'] * slots_per_hour
                
                for slot in range(total_slots):
                    slot_time = date + timedelta(hours=shift_info['start_hour'], minutes=slot*30)
                    
                    test_data.append({
                        'ds': slot_time,
                        'staff': staff['name'],
                        'role': staff['role'], 
                        'employment': staff['employment'],
                        'code': chosen_shift,
                        'parsed_slots_count': 1,
                        'shift_name': shift_info['name']
                    })
    
    df = pd.DataFrame(test_data)
    
    # Excel出力
    output_file = "sample_data/test_shift_data_standard.xlsx"
    df.to_excel(output_file, index=False)
    print(f"標準テストデータ生成完了: {output_file} ({len(df)} レコード)")
    
    return df

def create_large_test_data():
    """大容量テストデータの生成 (A1-S02用)"""
    print("大容量テストデータ生成中...")
    
    # より多くのスタッフ・期間で大量データ生成
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31)  # 3ヶ月間
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 15名のスタッフ
    staff_list = []
    for i in range(15):
        staff_list.append({
            'name': f'スタッフ{i+1:02d}',
            'role': np.random.choice(['介護士', '看護師', '相談員'], p=[0.7, 0.2, 0.1]),
            'employment': np.random.choice(['正社員', 'パート', '契約'], p=[0.6, 0.3, 0.1])
        })
    
    test_data = []
    shift_codes = ['D', 'E', 'L', 'N', 'H']
    
    for date in dates:
        for staff in staff_list:
            if np.random.random() < 0.8:  # 80%の勤務確率
                chosen_shift = np.random.choice(shift_codes[:-1])  # 休日以外
                
                # 8時間 × 2スロット/時間 = 16スロット
                for slot in range(16):
                    slot_time = date + timedelta(hours=9, minutes=slot*30)
                    
                    test_data.append({
                        'ds': slot_time,
                        'staff': staff['name'],
                        'role': staff['role'],
                        'employment': staff['employment'], 
                        'code': chosen_shift,
                        'parsed_slots_count': 1
                    })
    
    df = pd.DataFrame(test_data)
    
    # Excel出力
    output_file = "sample_data/test_shift_data_large.xlsx"
    df.to_excel(output_file, index=False)
    print(f"大容量テストデータ生成完了: {output_file} ({len(df)} レコード)")
    
    return df

def create_japanese_test_data():
    """日本語・特殊文字テストデータの生成 (A1-S03用)"""
    print("日本語テストデータ生成中...")
    
    # 日本語名・特殊文字を含むスタッフ
    staff_list = [
        {'name': '田中太郎', 'role': '介護士①', 'employment': '正社員'},
        {'name': '佐藤花子', 'role': '看護師★', 'employment': '正社員'},
        {'name': '鈴木美子（主任）', 'role': '相談員', 'employment': '正社員'},
        {'name': 'ヤマダ・ジロウ', 'role': '介護士②', 'employment': 'パート'},
        {'name': '高橋一郎【リーダー】', 'role': '介護士', 'employment': '正社員'},
        {'name': '中村みどり〜新人〜', 'role': '介護士', 'employment': 'パート'},
    ]
    
    # 特殊シフトコード
    shift_codes = {
        'D①': '日勤（通常）',
        'D②': '日勤（短時間）', 
        'E★': '早番（特別）',
        'L◯': '遅番（標準）',
        'N※': '夜勤（要注意）'
    }
    
    test_data = []
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    
    for date in dates:
        for staff in staff_list:
            if np.random.random() < 0.7:
                chosen_shift = np.random.choice(list(shift_codes.keys()))
                
                # 8スロット生成
                for slot in range(8):
                    slot_time = date + timedelta(hours=9, minutes=slot*30)
                    
                    test_data.append({
                        'ds': slot_time,
                        'staff': staff['name'],
                        'role': staff['role'],
                        'employment': staff['employment'],
                        'code': chosen_shift,
                        'parsed_slots_count': 1,
                        'shift_description': shift_codes[chosen_shift],
                        'notes': f"備考：{staff['name']}の{shift_codes[chosen_shift]}勤務"
                    })
    
    df = pd.DataFrame(test_data)
    
    # Excel出力（UTF-8対応）
    output_file = "sample_data/test_shift_japanese.xlsx"
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='シフトデータ')
    
    print(f"日本語テストデータ生成完了: {output_file} ({len(df)} レコード)")
    
    return df

def create_error_test_data():
    """エラーテスト用データの生成 (D1-S01用)"""
    print("エラーテスト用データ生成中...")
    
    # 1. 空ファイル
    empty_df = pd.DataFrame()
    empty_df.to_excel("sample_data/test_empty.xlsx", index=False)
    
    # 2. 必須列欠如ファイル
    incomplete_data = [
        {'date': '2024-01-01', 'name': '田中太郎'},  # 'code'列無し
        {'date': '2024-01-02', 'name': '佐藤花子'},
    ]
    incomplete_df = pd.DataFrame(incomplete_data)
    incomplete_df.to_excel("sample_data/test_missing_columns.xlsx", index=False)
    
    # 3. 異常値データ
    abnormal_data = [
        {'ds': '2024-01-01 09:00:00', 'staff': '田中太郎', 'role': '介護士', 'code': 'X', 'parsed_slots_count': -5},  # 負数
        {'ds': '無効な日付', 'staff': '佐藤花子', 'role': '看護師', 'code': 'D', 'parsed_slots_count': 'text'},  # 文字列
        {'ds': '2024-01-02 09:00:00', 'staff': '', 'role': '介護士', 'code': 'D', 'parsed_slots_count': 999999},  # 空文字・異常値
    ]
    abnormal_df = pd.DataFrame(abnormal_data)
    abnormal_df.to_excel("sample_data/test_abnormal_values.xlsx", index=False)
    
    # 4. テキストファイル (非Excel)
    with open("sample_data/test_text_file.txt", 'w', encoding='utf-8') as f:
        f.write("これはExcelファイルではありません。\n")
        f.write("システムは適切にエラーを検出するはずです。")
    
    print("エラーテスト用データ生成完了")

def create_performance_test_data():
    """パフォーマンステスト用データの生成"""
    print("パフォーマンステスト用データ生成中...")
    
    # 超大容量データ (5000レコード)
    test_data = []
    dates = pd.date_range(start='2024-01-01', end='2024-06-30', freq='D')  # 6ヶ月
    
    # 20名のスタッフ
    for i in range(20):
        staff_name = f'パフォーマンステスト用スタッフ{i+1:02d}'
        role = np.random.choice(['介護士', '看護師', '相談員'])
        employment = np.random.choice(['正社員', 'パート'])
        
        for date in dates:
            if np.random.random() < 0.8:  # 80%勤務確率
                shift_code = np.random.choice(['D', 'E', 'L', 'N'])
                
                # 各日8時間 = 16スロット
                for slot in range(16):
                    slot_time = date + timedelta(hours=9, minutes=slot*30)
                    
                    test_data.append({
                        'ds': slot_time,
                        'staff': staff_name,
                        'role': role,
                        'employment': employment,
                        'code': shift_code,
                        'parsed_slots_count': 1,
                        'performance_test_flag': True
                    })
    
    df = pd.DataFrame(test_data)
    output_file = "sample_data/test_performance_large.xlsx"
    df.to_excel(output_file, index=False)
    print(f"パフォーマンステストデータ生成完了: {output_file} ({len(df)} レコード)")
    
    return df

def main():
    """メイン実行関数"""
    print("=" * 60)
    print("UAT用テストデータ生成器")
    print("=" * 60)
    
    # サンプルデータディレクトリ作成
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    try:
        # 各種テストデータ生成
        standard_df = create_standard_test_data()
        large_df = create_large_test_data() 
        japanese_df = create_japanese_test_data()
        create_error_test_data()
        performance_df = create_performance_test_data()
        
        # 生成結果サマリー
        print("\n" + "=" * 60)
        print("テストデータ生成完了サマリー")
        print("=" * 60)
        print(f"標準テストデータ: {len(standard_df)} レコード")
        print(f"大容量テストデータ: {len(large_df)} レコード")
        print(f"日本語テストデータ: {len(japanese_df)} レコード")
        print(f"パフォーマンステストデータ: {len(performance_df)} レコード")
        print("エラーテスト用データ: 4ファイル")
        
        # ファイル一覧
        print(f"\n生成ファイル:")
        for file in sample_dir.glob("*"):
            size = file.stat().st_size / 1024  # KB
            print(f"  {file.name} ({size:.1f}KB)")
        
        print(f"\n[SUCCESS] すべてのUATテストデータ生成が完了しました")
        print(f"生成場所: {sample_dir.absolute()}")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] テストデータ生成エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())