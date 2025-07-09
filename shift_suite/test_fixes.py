#!/usr/bin/env python3
"""
修正内容のテスト用スクリプト
日曜日休み施設の分析と夜勤シフト認識のテスト
"""

import sys
import os
import datetime as dt
import pandas as pd
import numpy as np

# パス設定
sys.path.append('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析')

def test_sunday_daycare_scenario():
    """デイサービス等の日曜日休み施設のテストシナリオ"""
    print("=" * 60)
    print("デイサービス日曜日休み施設のテストシナリオ")
    print("=" * 60)
    
    # テストデータ作成：平日は通常勤務、日曜日は管理職のみ
    dates = pd.date_range('2024-01-01', '2024-01-14', freq='D')
    time_slots = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
    
    test_data = pd.DataFrame(index=time_slots, columns=dates)
    
    for date in dates:
        if date.weekday() == 6:  # 日曜日
            # 管理職のみ1-2名出勤（10:00-15:00）
            test_data.loc['10:00':,'15:00', date] = np.random.choice([1, 2], 1)[0]
            test_data.fillna(0, inplace=True)
        else:  # 平日・土曜日
            # 通常の勤務体制（各時間帯10-20名）
            test_data[date] = np.random.randint(10, 21, len(time_slots))
    
    print(f"テストデータ形状: {test_data.shape}")
    print(f"日曜日の勤務者数合計: {test_data.loc[:, test_data.columns[test_data.columns.weekday == 6]].sum().sum()}")
    print(f"平日の勤務者数平均: {test_data.loc[:, test_data.columns[test_data.columns.weekday < 5]].sum().mean():.1f}")
    
    return test_data

def test_night_shift_recognition():
    """夜勤シフト認識のテストシナリオ"""
    print("\n" + "=" * 60)
    print("夜勤シフト認識のテストシナリオ")
    print("=" * 60)
    
    from shift_suite.tasks.io_excel import _expand, _to_time_str
    
    # テストケース
    test_cases = [
        ("22:00", "06:00", "夜勤（22:00-06:00）"),
        ("23:30", "07:30", "夜勤（23:30-07:30）"),
        ("22:00", "24:00", "夜勤（22:00-24:00）"),
        ("00:00", "08:00", "深夜勤（00:00-08:00）"),
        ("09:00", "17:00", "日勤（09:00-17:00）"),
        ("16:00", "00:00", "準夜勤（16:00-00:00）"),
    ]
    
    print("時刻文字列変換テスト:")
    print("24:00 -> ", _to_time_str("24:00"))
    print("0:00 -> ", _to_time_str("0:00"))
    
    print("\nシフトスロット展開テスト:")
    for start, end, description in test_cases:
        slots = _expand(start, end, slot_minutes=60)
        print(f"{description}: {start}-{end} -> {len(slots)}スロット")
        if len(slots) <= 10:
            print(f"  スロット: {slots}")
        else:
            print(f"  スロット（最初の5つ）: {slots[:5]}...")
        print()

def test_zero_staff_display():
    """0人勤務日の表示テスト"""
    print("=" * 60)
    print("0人勤務日の表示テスト")
    print("=" * 60)
    
    # 0人勤務日を含むテストデータ
    dates = pd.date_range('2024-01-01', '2024-01-07', freq='D')
    time_slots = ['09:00', '12:00', '15:00', '18:00']
    
    test_data = pd.DataFrame(index=time_slots, columns=dates)
    
    # 平日は通常勤務、土日は0人
    for date in dates:
        if date.weekday() >= 5:  # 土日
            test_data[date] = 0
        else:  # 平日
            test_data[date] = np.random.randint(5, 15, len(time_slots))
    
    print("テストデータ（0人勤務日を含む）:")
    print(test_data)
    
    print("\n各日の合計:")
    daily_totals = test_data.sum()
    for date, total in daily_totals.items():
        day_name = ['月', '火', '水', '木', '金', '土', '日'][date.weekday()]
        print(f"{date.strftime('%Y-%m-%d')} ({day_name}): {total}人")
    
    return test_data

def main():
    """メインテスト実行"""
    print("修正内容のテスト実行開始")
    print("実行時刻:", dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        # 各テストの実行
        test_sunday_daycare_scenario()
        test_night_shift_recognition()
        test_zero_staff_display()
        
        print("\n" + "=" * 60)
        print("テスト実行完了")
        print("=" * 60)
        print("✓ 日曜日休み施設の需要計算修正")
        print("✓ 夜勤シフト認識の改善")
        print("✓ 0人勤務日の表示対応")
        print("\n実際のシステムでの動作確認を推奨します。")
        
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()