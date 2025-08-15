#!/usr/bin/env python3
"""
按分計算の問題点と代替案の詳細分析
"""

import sys
import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_proportional_problems():
    """按分計算の根本的問題を分析"""
    
    print("=== 按分計算の問題点詳細分析 ===")
    
    # 1. 按分計算の論理的問題
    print("\n1. 按分計算の論理的問題:")
    print("   a) 職種固有のニーズを無視")
    print("      - 看護師と事務職では必要時間帯が異なる")
    print("      - 夜勤専門職種と日勤専門職種の混在")
    print("      - スキルレベルによる代替可能性の差")
    
    print("   b) 時間帯別の需要パターンを無視")
    print("      - 朝の忙しい時間帯 vs 午後の静かな時間帯")
    print("      - 夜勤時間帯の特殊性")
    print("      - 休日と平日の需要差")
    
    print("   c) 雇用形態の制約を無視")
    print("      - パートタイマーの勤務時間制限")
    print("      - 常勤職員の責任範囲")
    print("      - スポット職員の利用可能性")
    
    # 2. 現在のデータ構造確認
    print("\n2. 現在のデータ構造確認...")
    
    try:
        test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
        
        # 実際のシフトデータを確認
        df_r72 = pd.read_excel(test_file, sheet_name="R7.2", header=0, dtype=str).fillna("")
        
        print(f"   実績データ形状: {df_r72.shape}")
        print(f"   職種一覧: {df_r72.iloc[:, 1].unique()[:10]}")  # 職種列
        print(f"   雇用形態一覧: {df_r72.iloc[:, 2].unique()}")   # 雇用形態列
        
        # 日付列の確認
        date_cols = df_r72.columns[3:]
        print(f"   日付列数: {len(date_cols)}")
        
        # 勤務コードの分布確認
        all_codes = set()
        for col in date_cols[:7]:  # 最初の1週間分
            for val in df_r72[col].dropna():
                val_str = str(val).strip()
                if val_str and val_str not in ['土', '日', '月', '火', '水', '木', '金', 'nan']:
                    all_codes.add(val_str)
        
        print(f"   使用されている勤務コード: {sorted(all_codes)}")
        
    except Exception as e:
        print(f"   データ確認エラー: {e}")
    
    # 3. 真の分析が必要な要素
    print("\n3. 真の分析が必要な要素:")
    print("   a) 職種別の実際の配置状況")
    print("      - 各職種が実際にどの時間帯に勤務しているか")
    print("      - 職種別の勤務パターンの特徴")
    print("      - 職種間の連携・代替可能性")
    
    print("   b) 需要と供給の時間軸マッチング")
    print("      - 30分スロット単位での需要 vs 供給")
    print("      - 時間帯別の不足・過剰状況")
    print("      - ピーク時間とオフピーク時間の特定")
    
    print("   c) 雇用形態の制約を考慮した分析")
    print("      - 各雇用形態の勤務可能時間帯")
    print("      - コスト効率性の評価")
    print("      - 柔軟性 vs 安定性のバランス")
    
    # 4. 代替分析手法の提案
    print("\n4. 代替分析手法の提案:")
    print("   A) 時間軸ベース分析")
    print("      - 30分スロット単位での過不足計算")
    print("      - 職種別の実際の勤務時間帯分析")
    print("      - 需要ピークと供給ギャップの特定")
    
    print("   B) 職種能力マトリクス分析")
    print("      - 各職種が対応可能な業務範囲")
    print("      - 代替可能性マトリクス")
    print("      - スキルギャップ分析")
    
    print("   C) コスト効率分析")
    print("      - 雇用形態別の時間単価")
    print("      - 最適な職員配置の算出")
    print("      - ROI（投資対効果）分析")
    
    # 5. 実装優先度
    print("\n5. 実装優先度:")
    print("   【高】時間軸ベース分析 - 現在のデータで即座に実装可能")
    print("   【中】職種能力マトリクス分析 - 追加データ収集が必要")
    print("   【低】コスト効率分析 - 人事データとの統合が必要")
    
    return {
        "immediate_fix": "時間軸ベース分析の実装",
        "long_term_goal": "職種能力マトリクス分析",
        "data_needed": ["職種別業務範囲", "時間単価情報", "代替可能性データ"]
    }

if __name__ == "__main__":
    result = analyze_proportional_problems()
    print(f"\n=== 推奨アプローチ ===")
    print(f"即座の修正: {result['immediate_fix']}")
    print(f"長期目標: {result['long_term_goal']}")
    print(f"追加データ: {result['data_needed']}")