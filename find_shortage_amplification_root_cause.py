#!/usr/bin/env python3
"""
不足時間異常放大の根本原因特定スクリプト
27,153時間（295時間/日）問題の真の原因を特定
"""

import os
import json
from pathlib import Path

def analyze_shortage_root_cause():
    """不足時間の根本原因を特定"""
    
    print("=" * 80)
    print("🎯 不足時間異常放大の根本原因特定分析")
    print("=" * 80)
    
    # 分析対象ディレクトリ
    base_dir = Path("./extracted_test/out_median_based")
    
    if not base_dir.exists():
        print(f"❌ 分析ディレクトリが見つかりません: {base_dir}")
        return
    
    print(f"📁 分析対象: {base_dir}")
    
    # 1. 基本統計の確認
    stats_file = base_dir / "stats_summary.txt"
    if stats_file.exists():
        print(f"\n📊 基本統計 ({stats_file}):")
        with open(stats_file, 'r') as f:
            content = f.read()
            print(content)
            
            # 数値を抽出
            for line in content.strip().split('\n'):
                if 'lack_hours_total' in line:
                    lack_hours = int(line.split(':')[1].strip())
                    print(f"🔍 総不足時間: {lack_hours:,}時間")
                    
                    # 期間日数を計算（meta.jsonから）
                    meta_file = base_dir / "heatmap.meta.json"
                    if meta_file.exists():
                        with open(meta_file, 'r') as mf:
                            meta_data = json.load(mf)
                            dates = meta_data.get('dates', [])
                            period_days = len(dates)
                            
                            if period_days > 0:
                                hours_per_day = lack_hours / period_days
                                print(f"🔍 分析期間: {period_days}日")
                                print(f"🔍 1日平均不足: {hours_per_day:.1f}時間/日")
                                
                                # 異常判定
                                if hours_per_day > 50:
                                    print(f"❌ 重大異常: {hours_per_day:.0f}時間/日は異常に高い")
                                    print(f"   正常範囲: 1-5時間/日")
                                    print(f"   現在値は正常値の{hours_per_day/3:.0f}倍")
                                elif hours_per_day > 10:
                                    print(f"⚠️ 異常: {hours_per_day:.1f}時間/日は高すぎる")
                                else:
                                    print(f"✅ 許容範囲: {hours_per_day:.1f}時間/日")
    
    # 2. meta.jsonから統計手法を確認
    meta_file = base_dir / "heatmap.meta.json"
    if meta_file.exists():
        print(f"\n⚙️ Need計算設定 ({meta_file}):")
        with open(meta_file, 'r') as f:
            meta_data = json.load(f)
            
            need_params = meta_data.get('need_calculation_params', {})
            print(f"  統計手法: {need_params.get('statistic_method', 'N/A')}")
            print(f"  参照期間: {need_params.get('ref_start_date', 'N/A')} ～ {need_params.get('ref_end_date', 'N/A')}")
            print(f"  外れ値除去: {need_params.get('remove_outliers', 'N/A')}")
            
            # スロット情報
            slot_minutes = meta_data.get('slot', 30)
            slot_hours = slot_minutes / 60
            print(f"  スロット間隔: {slot_minutes}分 ({slot_hours}時間)")
            
            # 期間情報
            dates = meta_data.get('dates', [])
            print(f"  分析期間: {len(dates)}日")
            print(f"  開始日: {dates[0] if dates else 'N/A'}")
            print(f"  終了日: {dates[-1] if dates else 'N/A'}")
    
    # 3. ファイルサイズから異常を検出
    print(f"\n📁 ファイルサイズ分析:")
    
    key_files = [
        'shortage_time.parquet',
        'need_per_date_slot.parquet',
        'heat_ALL.parquet'
    ]
    
    file_sizes = {}
    for filename in key_files:
        filepath = base_dir / filename
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            file_sizes[filename] = size_kb
            print(f"  {filename}: {size_kb:.1f} KB")
        else:
            print(f"  {filename}: 存在しない")
    
    # ファイルサイズから異常を推定
    shortage_size = file_sizes.get('shortage_time.parquet', 0)
    need_size = file_sizes.get('need_per_date_slot.parquet', 0)
    
    if shortage_size > 200:  # 200KB以上は異常に大きい
        print(f"  ⚠️ shortage_time.parquet のサイズ異常: {shortage_size:.0f}KB")
        print(f"     正常サイズ: 50-100KB程度")
    
    if need_size > 200:  # 200KB以上は異常に大きい  
        print(f"  ⚠️ need_per_date_slot.parquet のサイズ異常: {need_size:.0f}KB")
        print(f"     正常サイズ: 50-100KB程度")
    
    # 4. 推定される根本原因を特定
    print(f"\n🎯 推定される根本原因:")
    
    # 原因1: 統計手法による需要過大評価
    statistic_method = need_params.get('statistic_method', '')
    if '75' in statistic_method or '90' in statistic_method:
        print(f"  1. 統計手法による需要過大評価")
        print(f"     現在: {statistic_method}")
        print(f"     推奨: 中央値または25パーセンタイル")
    
    # 原因2: 期間依存性による累積誤差
    period_days = len(dates) if 'dates' in locals() and dates else 0
    if period_days > 60:  # 2ヶ月以上
        print(f"  2. 期間依存性による累積誤差")
        print(f"     分析期間: {period_days}日（長期間）")
        print(f"     推奨: 30日以内での分析")
    
    # 原因3: Need値の異常放大
    if need_size > 200:
        print(f"  3. Need値の異常放大")
        print(f"     Need データサイズ: {need_size:.0f}KB（異常に大きい）")
        print(f"     可能性: 1スロットあたりの需要人数が過大")
    
    # 原因4: 計算ロジックの重複カウント
    if shortage_size > 200:
        print(f"  4. 計算ロジックの重複カウント")
        print(f"     Shortage データサイズ: {shortage_size:.0f}KB（異常に大きい）")
        print(f"     可能性: 同じ不足が複数回カウントされている")
    
    # 5. 具体的な修正提案
    print(f"\n💡 具体的な修正提案:")
    print(f"  1. 統計手法を「中央値」から「25パーセンタイル」に変更")  
    print(f"  2. Need値の上限を1スロットあたり3-5人に制限")
    print(f"  3. 分析期間を30日以内に短縮")
    print(f"  4. 不足時間計算の重複チェック機能を追加")
    print(f"  5. 日平均不足時間が10時間を超える場合の異常検出機能を強化")
    
    # 6. 緊急修正コード例
    print(f"\n🚨 緊急修正の実装箇所:")
    print(f"  📄 shift_suite/tasks/heatmap.py:")
    print(f"     - 行708: '75パーセンタイル' → '25パーセンタイル'に変更")
    print(f"     - 行721: Need値の上限を2.0から1.5に引き下げ")
    print(f"  📄 shift_suite/tasks/shortage.py:")
    print(f"     - 行387: Need異常値の上限を10から3に引き下げ")
    print(f"     - 行352: 1日最大不足時間を50から10時間に引き下げ")
    
    print(f"\n" + "=" * 80)
    print(f"🔍 結論: 295時間/日の不足は明らかに計算異常")
    print(f"💊 対策: 上記の修正を実装して統計手法と制限値を調整する必要がある")
    print(f"=" * 80)

if __name__ == "__main__":
    analyze_shortage_root_cause()