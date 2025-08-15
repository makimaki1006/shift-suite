#!/usr/bin/env python3
"""
27,486.5時間問題の根本原因分析
計算不整合の特定と検証
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def analyze_calculation_inconsistency():
    """計算不整合の詳細分析"""
    
    print("=== 27,486.5時間問題 根本原因分析 ===")
    print("検証日時:", pd.Timestamp.now().strftime("%Y年%m月%d日 %H時%M分"))
    print()
    
    # 3つの統計手法を比較分析
    methods = ['p25_based', 'median_based', 'mean_based']
    base_dir = Path('extracted_results')
    
    inconsistency_found = False
    
    for method in methods:
        method_dir = base_dir / f'out_{method}'
        if not method_dir.exists():
            print(f"[ERROR] {method} ディレクトリが存在しません")
            continue
            
        print(f"\n【{method.upper()} 分析】")
        print("-" * 50)
        
        # shortage_time.parquet の分析
        shortage_time_file = method_dir / 'shortage_time.parquet'
        if shortage_time_file.exists():
            df_shortage = pd.read_parquet(shortage_time_file)
            total_shortage_time = df_shortage.sum().sum() * 0.5  # スロット→時間変換
            print(f"shortage_time.parquet 総不足: {total_shortage_time:.1f}時間")
            print(f"データ形状: {df_shortage.shape}")
            print(f"負の値の割合: {(df_shortage < 0).sum().sum() / df_shortage.size * 100:.1f}%")
        
        # 分析レポートの読み込み
        report_files = list(method_dir.glob('*不足時間計算詳細分析.txt'))
        if report_files:
            report_file = report_files[0]
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # サマリー数値を抽出
            lines = content.split('\n')
            summary_shortage = None
            summary_demand = None
            summary_actual = None
            
            for line in lines:
                if '総不足時間:' in line:
                    try:
                        summary_shortage = float(line.split(':')[1].strip().replace('時間', ''))
                    except:
                        pass
                elif '総需要時間:' in line:
                    try:
                        summary_demand = float(line.split(':')[1].strip().replace('時間', ''))
                    except:
                        pass
                elif '総実績時間:' in line:
                    try:
                        summary_actual = float(line.split(':')[1].strip().replace('時間', ''))
                    except:
                        pass
            
            print(f"サマリー総不足時間: {summary_shortage}時間")
            print(f"サマリー総需要時間: {summary_demand}時間") 
            print(f"サマリー総実績時間: {summary_actual}時間")
            
            # 重大な不整合を検出
            if (total_shortage_time < 0 and summary_shortage > 0):
                print(f"[CRITICAL] 重大な計算不整合検出!")
                print(f"   shortage_time.parquet: {total_shortage_time:.1f}時間 (負値=過剰)")
                print(f"   サマリー計算: {summary_shortage:.1f}時間 (正値=不足)")
                print(f"   差異: {abs(total_shortage_time - summary_shortage):.1f}時間")
                inconsistency_found = True
                
                # 27,486.5時間との比較
                if summary_shortage and abs(summary_shortage - 27486.5) < 1000:
                    print(f"[WARNING] サマリー値が27,486.5時間問題に近似! (差異: {abs(summary_shortage - 27486.5):.1f})")
        
        print()
    
    return inconsistency_found

def analyze_need_calculation_method():
    """Need計算方式の詳細分析"""
    
    print("\n=== Need計算方式の詳細分析 ===")
    
    # heatmap.meta.json の確認
    meta_file = Path('extracted_results/out_p25_based/heatmap.meta.json')
    if meta_file.exists():
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        print("現在のNeed計算パラメータ:")
        need_params = meta.get('need_calculation_params', {})
        print(f"  統計手法: {need_params.get('statistic_method', 'N/A')}")
        print(f"  参照期間: {need_params.get('ref_start_date', 'N/A')} ～ {need_params.get('ref_end_date', 'N/A')}")
        print(f"  外れ値除去: {need_params.get('remove_outliers', 'N/A')}")
        print(f"  IQR倍数: {need_params.get('iqr_multiplier', 'N/A')}")
        
        # dow_need_pattern の分析
        dow_pattern = meta.get('dow_need_pattern', [])
        if dow_pattern:
            # 需要のピークタイムを特定
            peak_demand_slots = []
            for slot in dow_pattern:
                total_demand = sum(slot.get(str(i), 0) for i in range(7))
                if total_demand > 10:  # 閾値以上のスロット
                    peak_demand_slots.append({
                        'time': slot.get('time', ''),
                        'total_demand': total_demand
                    })
            
            print(f"\n高需要時間帯 (需要>10):")
            for slot in sorted(peak_demand_slots, key=lambda x: x['total_demand'], reverse=True)[:5]:
                print(f"  {slot['time']}: {slot['total_demand']}人")
                
            # 25パーセンタイル手法の問題点
            print(f"\n[ANALYSIS] 25パーセンタイル手法の潜在的問題:")
            print(f"  - 需要を過小評価する可能性")
            print(f"  - ピーク需要を捉えにくい") 
            print(f"  - 現実的な人員配置とのギャップ")

def investigate_time_axis_calculator():
    """時間軸計算機の実装状況を調査"""
    
    print("\n=== 時間軸計算機 実装状況 ===")
    
    # time_axis_shortage_calculator.py の確認
    calc_file = Path('shift_suite/tasks/time_axis_shortage_calculator.py')
    if calc_file.exists():
        with open(calc_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("重要な実装ポイント:")
        
        # 検証用途のみのコメントを確認
        if '検証用途のみ' in content:
            print("[OK] total_shortage_baseline は「検証用途のみ」に変更済み")
        
        # 動的需要計算の実装確認
        if '_calculate_realistic_demand' in content:
            print("[OK] 現実的需要計算メソッドが実装済み")
        
        # 循環増幅の回避確認
        if 'circular amplification' in content.lower():
            print("[OK] 循環増幅回避のコメントあり")
        else:
            print("[?] 循環増幅への言及なし")
            
        # DYNAMIC_FIX の確認
        dynamic_fix_count = content.count('DYNAMIC_FIX')
        print(f"[OK] DYNAMIC_FIX 修正箇所: {dynamic_fix_count}箇所")

def main():
    """メイン分析実行"""
    
    inconsistency = analyze_calculation_inconsistency()
    analyze_need_calculation_method()
    investigate_time_axis_calculator()
    
    print("\n" + "="*70)
    print("【分析結論】")
    print("="*70)
    
    if inconsistency:
        print("[CRITICAL] 重大な発見: 計算不整合が確認されました")
        print("   - shortage_time.parquet では負値(過剰)を示している")
        print("   - サマリー計算では正値(不足)を示している")
        print("   - この不整合が27,486.5時間問題の根本原因の可能性")
        print()
        print("[RECOMMENDATION] 推奨されるアクション:")
        print("   1. shortage_time.parquet とサマリー計算の整合性を確保")
        print("   2. Need計算の25パーセンタイル手法を見直し") 
        print("   3. 時間軸ベース計算の正式採用を検討")
        print("   4. 計算プロセス全体の検証とテスト強化")
    else:
        print("[OK] 基本的な計算整合性は確認されました")
        print("   ただし、さらなる詳細検証が必要です")

if __name__ == "__main__":
    main()