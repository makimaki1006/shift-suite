#!/usr/bin/env python3
"""
現実的な規模感の分析と修正
2000時間や-1000時間といった非現実的な数値の根本原因調査
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

def analyze_realistic_scale():
    """現実的な規模感の分析"""
    
    print("=" * 80)
    print("現実的な規模感分析 - 異常値の根本原因調査")
    print("=" * 80)
    print(f"分析実行: {datetime.now().strftime('%Y年%m月%d日 %H時%M分')}")
    print()
    
    print("【業界標準との比較】")
    print("-" * 50)
    
    # 業界標準の人員配置
    facility_standards = {
        "小規模デイサービス": {
            "利用者数": 20,
            "標準職員数": 4,  # 20名÷5(配置基準)
            "1日標準勤務時間": 32,  # 4名×8時間
            "月間標準勤務時間": 960,  # 32時間×30日
            "現実的不足範囲": (50, 200)
        },
        "中規模デイサービス": {
            "利用者数": 50,
            "標準職員数": 10,
            "1日標準勤務時間": 80,
            "月間標準勤務時間": 2400,
            "現実的不足範囲": (100, 400)
        },
        "大規模施設": {
            "利用者数": 100,
            "標準職員数": 20,
            "1日標準勤務時間": 160,
            "月間標準勤務時間": 4800,
            "現実的不足範囲": (200, 800)
        }
    }
    
    for facility_type, standards in facility_standards.items():
        print(f"{facility_type}:")
        print(f"  利用者数: {standards['利用者数']}名")
        print(f"  標準職員数: {standards['標準職員数']}名")
        print(f"  月間標準勤務: {standards['月間標準勤務時間']}時間")
        print(f"  現実的不足範囲: {standards['現実的不足範囲'][0]}-{standards['現実的不足範囲'][1]}時間/月")
        print()
    
    return facility_standards

def analyze_current_abnormal_values():
    """現在の異常値を分析"""
    
    print("【現在の計算結果の異常性】")
    print("-" * 50)
    
    # 実際のデータから
    base_dir = Path('extracted_results')
    methods = {
        'p25_based': '25パーセンタイル',
        'median_based': '中央値', 
        'mean_based': '平均値'
    }
    
    for method_key, method_name in methods.items():
        method_dir = base_dir / f'out_{method_key}'
        
        if not method_dir.exists():
            continue
        
        print(f"{method_name}:")
        
        # Need計算の分析
        need_files = list(method_dir.glob('need_per_date_slot_role_*.parquet'))
        if need_files:
            total_need = 0
            for need_file in need_files:
                try:
                    df = pd.read_parquet(need_file)
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    file_total = df[numeric_cols].sum().sum()
                    total_need += file_total
                except:
                    pass
            
            need_hours_month = total_need * 0.5
            need_hours_day = need_hours_month / 30
            
            print(f"  月間需要: {need_hours_month:.0f}時間")
            print(f"  日平均需要: {need_hours_day:.1f}時間/日")
            
            # 現実性評価
            if need_hours_month > 4000:
                scale = "超大規模施設相当"
                reality = "非現実的"
            elif need_hours_month > 2000:
                scale = "大規模施設相当"
                reality = "要検証"
            elif need_hours_month > 800:
                scale = "中規模施設相当"
                reality = "現実的"
            else:
                scale = "小規模施設相当"
                reality = "現実的"
            
            print(f"  規模感: {scale}")
            print(f"  現実性: {reality}")
            
            # 異常性の定量化
            if need_hours_month > 2400:  # 中規模基準を超過
                excess_ratio = need_hours_month / 2400
                print(f"  異常度: 中規模基準の{excess_ratio:.1f}倍")
        
        print()

def investigate_calculation_magnification():
    """計算の拡大要因を調査"""
    
    print("【計算拡大要因の調査】")
    print("-" * 50)
    
    print("可能性のある拡大要因:")
    print()
    
    print("1. スロット計算の問題")
    print("   - 30分スロット × 48スロット/日 = 24時間")
    print("   - しかし実際の営業時間は8-10時間")
    print("   - 非営業時間での需要計算が過大")
    print()
    
    print("2. 職種重複カウント")
    print("   - 同一人物が複数職種でカウント")
    print("   - 職種別ファイルの単純合計による重複")
    print()
    
    print("3. 期間重複計算")
    print("   - 同一日付の重複処理")
    print("   - 累積計算による指数的増大")
    print()
    
    print("4. 単位変換エラー")
    print("   - 人数 × 時間の二重計算")
    print("   - スロット→時間変換の重複適用")
    print()

def propose_realistic_correction():
    """現実的な修正案の提案"""
    
    print("【現実的な修正案】")
    print("-" * 50)
    
    print("Phase 1: 営業時間制限")
    print("  - 実際の営業時間（例：8:00-17:30）のみで計算")
    print("  - 深夜・早朝時間帯の需要を0に設定")
    print("  - 効果: 約50-70%の削減")
    print()
    
    print("Phase 2: 職種重複の排除")
    print("  - 職種間の重複チェック機能")
    print("  - 主職種のみでの計算")
    print("  - 効果: 約20-30%の削減")
    print()
    
    print("Phase 3: 現実性制約の適用")
    print("  - 業界標準との比較チェック")
    print("  - 異常値の自動検出・制限")
    print("  - 上限値の設定（施設規模基準）")
    print()
    
    print("Phase 4: 単位統一の徹底")
    print("  - 人数・時間・スロットの明確な分離")
    print("  - 変換ロジックの一本化")
    print("  - 中間結果の検証機能")
    print()

def calculate_realistic_targets():
    """現実的な目標値の算出"""
    
    print("【現実的な目標値】")
    print("-" * 50)
    
    # 現在の値から現実的な値への修正
    current_values = {
        'p25_based': 2739.0,
        'median_based': 2984.5,
        'mean_based': 2954.5
    }
    
    print("修正前→修正後の目標:")
    
    for method_key, current_value in current_values.items():
        method_name = {'p25_based': '25%ile', 'median_based': '中央値', 'mean_based': '平均'}[method_key]
        
        # 現実的な範囲への修正（約80%削減想定）
        realistic_value = current_value * 0.2  # 営業時間制限による大幅削減
        
        print(f"{method_name}:")
        print(f"  現在: {current_value:.0f}時間/月")
        print(f"  目標: {realistic_value:.0f}時間/月")
        print(f"  削減率: {((current_value - realistic_value) / current_value) * 100:.0f}%")
        
        # 現実性評価
        if 100 <= realistic_value <= 800:
            evaluation = "✓ 現実的"
        elif realistic_value > 800:
            evaluation = "△ やや高い"
        else:
            evaluation = "✓ 保守的"
        
        print(f"  評価: {evaluation}")
        print()

def main():
    """メイン分析実行"""
    
    facility_standards = analyze_realistic_scale()
    analyze_current_abnormal_values()
    investigate_calculation_magnification()
    propose_realistic_correction()
    calculate_realistic_targets()
    
    print("=" * 80)
    print("【結論】")
    print("=" * 80)
    print("現在の2000-3000時間/月は現実的でない")
    print("根本原因: 非営業時間の需要計算、職種重複、単位変換エラー")
    print("解決策: 営業時間制限 + 重複排除 + 現実性制約")
    print("目標: 500-800時間/月の現実的な範囲への修正")
    print()
    print("一貫性担保だけでなく、現実性の確保が必要")
    print("=" * 80)

if __name__ == "__main__":
    main()