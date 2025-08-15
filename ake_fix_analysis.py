#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明け番可視化問題の修正案分析
"""

import pandas as pd
import datetime as dt

def analyze_ake_fix_options():
    """明け番修正案の分析"""
    print("="*80)
    print("明け番可視化問題の修正案分析")
    print("="*80)
    
    print("問題の要因:")
    print("1. 明け番（'明'）の開始時間が00:00:00と定義されている")
    print("2. io_excel.pyの日付またぎ判定で 'slot_time < shift_start_time' の条件が")
    print("   00:00 < 00:00 = False となるため、日跨ぎが発生しない")
    print("3. 結果として明け番のすべての時間スロットが同じ日付として処理される")
    print()
    
    print("修正案:")
    print()
    
    # 修正案1: 明け番の開始時間を前日の時間に変更
    print("【修正案1】明け番の開始時間を前日の時間に変更")
    print("-" * 50)
    print("テストデータの勤務区分で明け番の開始時間を前日の適切な時間に変更")
    print("例: 明け番を '00:00' → '22:00' に変更")
    print()
    
    # シミュレーション
    print("修正案1のシミュレーション:")
    simulate_fix_option1()
    print()
    
    # 修正案2: io_excel.pyの処理ロジック修正
    print("【修正案2】io_excel.pyの処理ロジック修正")
    print("-" * 50)
    print("特定のシフトコード（'明'など）に対して専用の日跨ぎ処理を実装")
    print("明け番の場合、開始時間に関係なく日跨ぎ処理を適用")
    print()
    
    simulate_fix_option2()
    print()
    
    # 修正案3: 明け番専用の時間スロット定義
    print("【修正案3】明け番専用の時間スロット定義")
    print("-" * 50)
    print("明け番の時間スロットを前日の時間から開始するように定義")
    print("例: ['22:00', '23:00', '00:00', '01:00', ..., '09:00']")
    print()
    
    simulate_fix_option3()

def simulate_fix_option1():
    """修正案1のシミュレーション: 開始時間変更"""
    print("  現在の明け番定義: 開始 00:00 → 終了 10:00")
    print("  修正後の定義: 開始 22:00 → 終了 10:00")
    
    # 修正後の処理シミュレーション
    ake_start_time = dt.time(22, 0)  # 22:00開始
    test_slots = ["22:00", "23:00", "00:00", "01:00", "08:00", "09:00", "10:00"]
    test_date = dt.date(2025, 6, 15)
    
    print(f"  基準日付: {test_date}")
    print(f"  明け番開始時間: {ake_start_time}")
    print("  時間スロット処理結果:")
    
    for slot_str in test_slots:
        slot_time = dt.datetime.strptime(slot_str, "%H:%M").time()
        
        # 日付またぎ判定
        current_date = test_date
        if slot_time < ake_start_time:
            current_date += dt.timedelta(days=1)
            cross_midnight = True
        else:
            cross_midnight = False
        
        final_datetime = dt.datetime.combine(current_date, slot_time)
        print(f"    {slot_str}: {final_datetime} (日跨ぎ: {cross_midnight})")

def simulate_fix_option2():
    """修正案2のシミュレーション: ロジック修正"""
    print("  io_excel.pyの修正案:")
    print("  ```python")
    print("  # 明け番など特殊なシフトの処理")
    print("  if code_val in ['明', 'アケ', 'ake']:  # 明け番の場合")
    print("      # 0:00-9:59は翌日として処理")
    print("      if slot_time.hour < 12:  # 午前中は翌日")
    print("          current_date += timedelta(days=1)")
    print("  else:")
    print("      # 既存の処理")
    print("      if shift_start_time and slot_time < shift_start_time:")
    print("          current_date += timedelta(days=1)")
    print("  ```")
    
    # シミュレーション
    test_slots = ["00:00", "01:00", "08:00", "09:00", "10:00", "22:00", "23:00"]
    test_date = dt.date(2025, 6, 15)
    
    print(f"\n  基準日付: {test_date}")
    print("  明け番専用ロジックでの処理結果:")
    
    for slot_str in test_slots:
        slot_time = dt.datetime.strptime(slot_str, "%H:%M").time()
        
        # 明け番専用ロジック
        current_date = test_date
        if slot_time.hour < 12:  # 午前中は翌日
            current_date += dt.timedelta(days=1)
            cross_midnight = True
        else:
            cross_midnight = False
        
        final_datetime = dt.datetime.combine(current_date, slot_time)
        print(f"    {slot_str}: {final_datetime} (日跨ぎ: {cross_midnight})")

def simulate_fix_option3():
    """修正案3のシミュレーション: 時間スロット定義変更"""
    print("  現在の時間スロット: 15分刻み、00:00-23:45")
    print("  明け番用スロット案: 前日22:00から翌日10:00まで")
    
    # 明け番用時間スロットの生成
    ake_slots = []
    
    # 前日の時間（22:00-23:45）
    for hour in [22, 23]:
        for minute in [0, 15, 30, 45]:
            ake_slots.append(f"{hour:02d}:{minute:02d}")
    
    # 当日の時間（00:00-09:45）
    for hour in range(0, 10):
        for minute in [0, 15, 30, 45]:
            ake_slots.append(f"{hour:02d}:{minute:02d}")
    
    print(f"  明け番用時間スロット数: {len(ake_slots)}スロット")
    print(f"  開始: {ake_slots[0]}, 終了: {ake_slots[-1]}")
    print(f"  例: {ake_slots[:8]} ... {ake_slots[-4:]}")

def recommend_best_fix():
    """最適な修正案の推奨"""
    print("\n" + "="*80)
    print("推奨修正案")
    print("="*80)
    
    print("【推奨】修正案2: io_excel.pyの処理ロジック修正")
    print()
    print("理由:")
    print("1. テストデータを変更する必要がない")
    print("2. 既存のシステムとの互換性を保てる")
    print("3. 他の明け番パターンにも対応可能")
    print("4. 実装が比較的簡単")
    print()
    
    print("実装手順:")
    print("1. io_excel.pyの日付またぎ判定処理を修正")
    print("2. 明け番シフトコードの特別処理を追加")
    print("3. テスト実行で動作確認")
    print("4. 15分スロット分析で明け番が可視化されることを確認")

if __name__ == "__main__":
    analyze_ake_fix_options()
    recommend_best_fix()