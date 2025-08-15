#!/usr/bin/env python3
"""
統一計算エンジン検証レポート生成

重要な発見の詳細検証とバックアップ分析
慎重なアプローチによる結果の確認
"""

from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import sys
sys.path.append('.')

from shift_suite.tasks.unified_shortage_calculator import UnifiedShortageCalculator

def create_comprehensive_validation_report():
    """包括的な検証レポートの作成"""
    
    print("=" * 80)
    print("統一計算エンジン包括検証レポート")
    print("=" * 80)
    print(f"実行日時: {datetime.now()}")
    print()
    
    # 検証用データの準備
    scenario_dir = Path("extracted_results/out_p25_based")
    
    if not scenario_dir.exists():
        print("⚠️  検証用シナリオディレクトリが見つかりません")
        return
    
    # 統一計算エンジンでの計算
    calculator = UnifiedShortageCalculator()
    result = calculator.calculate_true_shortage(scenario_dir)
    
    print("🔍 SECTION 1: 基本計算結果の検証")
    print("-" * 50)
    print(f"総需要時間: {result.total_demand_hours:,.1f} 時間")
    print(f"総供給時間: {result.total_supply_hours:,.1f} 時間")  
    print(f"バランス状況: {result.balance_status}")
    print(f"信頼度スコア: {result.reliability_score:.2f}")
    print()
    
    # 詳細データ検証
    print("🔍 SECTION 2: 入力データ詳細検証")
    print("-" * 50)
    
    # intermediate_data.parquet の詳細確認
    data_path = scenario_dir / 'intermediate_data.parquet'
    if data_path.exists():
        df = pd.read_parquet(data_path)
        
        print(f"入力データ基本情報:")
        print(f"  総レコード数: {len(df):,} 件")
        print(f"  カラム数: {len(df.columns)} 個")
        
        if 'holiday_type' in df.columns:
            holiday_breakdown = df['holiday_type'].value_counts()
            print(f"  休暇タイプ別内訳:")
            for htype, count in holiday_breakdown.items():
                print(f"    {htype}: {count:,} 件")
        
        if 'parsed_slots_count' in df.columns:
            working_data = df[df['parsed_slots_count'] > 0]
            total_slots = working_data['parsed_slots_count'].sum()
            total_hours = total_slots * 0.5  # 30分スロット
            
            print(f"  実勤務データ:")
            print(f"    勤務レコード数: {len(working_data):,} 件")
            print(f"    総スロット数: {total_slots:,}")
            print(f"    総労働時間: {total_hours:,.1f} 時間")
            print(f"    平均スロット/レコード: {total_slots/len(working_data):.1f}")
        
        if 'role' in df.columns:
            role_counts = df['role'].value_counts()
            print(f"  職種別内訳（上位5職種）:")
            for role, count in role_counts.head(5).items():
                print(f"    {role}: {count:,} 件")
        
        if 'ds' in df.columns:
            df['ds'] = pd.to_datetime(df['ds'])
            date_range = df['ds'].dt.date
            period_days = (date_range.max() - date_range.min()).days + 1
            print(f"  期間情報:")
            print(f"    開始日: {date_range.min()}")
            print(f"    終了日: {date_range.max()}")
            print(f"    分析日数: {period_days} 日")
    
    print()
    
    # 需要データ検証
    print("🔍 SECTION 3: 需要データ検証")
    print("-" * 50)
    
    need_files = list(scenario_dir.glob('need_per_date_slot_role_*.parquet'))
    print(f"需要ファイル数: {len(need_files)} 個")
    
    total_need_value = 0.0
    for i, need_file in enumerate(need_files[:5]):  # 最初の5ファイル
        try:
            need_df = pd.read_parquet(need_file)
            numeric_cols = need_df.select_dtypes(include=['number']).columns
            file_need = need_df[numeric_cols].sum().sum()
            total_need_value += file_need
            
            role_name = need_file.stem.split('_')[-1]
            print(f"  {role_name}: {file_need:.1f} 人・スロット (shape: {need_df.shape})")
            
        except Exception as e:
            print(f"  {need_file.name}: エラー - {e}")
    
    need_hours = total_need_value * 0.5  # 人数 → 時間変換
    print(f"需要合計: {total_need_value:.1f} 人・スロット = {need_hours:.1f} 時間")
    print()
    
    # 従来計算との比較
    print("🔍 SECTION 4: 従来計算手法との比較")
    print("-" * 50)
    
    # 従来の誤った計算パターン
    total_records = len(df) if 'df' in locals() else 0
    old_wrong_calculation = total_records * 0.5
    
    print(f"従来の誤った計算:")
    print(f"  len(全レコード) × 0.5 = {total_records} × 0.5 = {old_wrong_calculation:.1f} 時間")
    print()
    
    print(f"統一エンジンの正しい計算:")
    print(f"  実勤務スロット合計 × 0.5 = {result.total_supply_hours:.1f} 時間")
    print()
    
    if result.total_supply_hours > 0:
        accuracy_improvement = ((result.total_supply_hours - old_wrong_calculation) / result.total_supply_hours) * 100
        print(f"計算精度改善:")
        print(f"  改善幅: {result.total_supply_hours - old_wrong_calculation:,.1f} 時間")
        print(f"  改善率: {accuracy_improvement:.1f}%")
    print()
    
    # 現実性チェック
    print("🔍 SECTION 5: 結果の現実性検証")
    print("-" * 50)
    
    if 'period_days' in locals():
        daily_demand = result.total_demand_hours / period_days
        daily_supply = result.total_supply_hours / period_days
        daily_balance = daily_supply - daily_demand
        
        print(f"日平均換算:")
        print(f"  需要: {daily_demand:.1f} 時間/日")
        print(f"  供給: {daily_supply:.1f} 時間/日")
        print(f"  差分: {daily_balance:.1f} 時間/日")
        print()
        
        # 現実性評価
        if daily_supply > 500:
            print("⚠️  警告: 日平均供給時間が500時間を超えています")
            print("    → 大規模施設または計算要確認")
        elif daily_supply > 200:
            print("✓ 中～大規模施設の妥当な範囲")
        elif daily_supply > 50:
            print("✓ 小～中規模施設の妥当な範囲") 
        else:
            print("⚠️  注意: 日平均供給時間が少なすぎる可能性")
        
        if abs(daily_balance) > 100:
            print("⚠️  警告: 大きな需給アンバランス")
        elif abs(daily_balance) > 50:
            print("△ 中程度の需給アンバランス")
        else:
            print("✓ 妥当な需給バランス")
    
    print()
    
    # 推奨事項
    print("📋 SECTION 6: 推奨事項")
    print("-" * 50)
    
    if result.balance_status == "EXCESS":
        print("🎯 供給過剰状態の対応推奨事項:")
        print("  1. 効率化の検討（勤務時間の最適化）")
        print("  2. サービス品質向上への人員活用")
        print("  3. コスト削減の可能性調査")
        print("  4. 将来的な需要増に備えたキャパシティ確保")
    elif result.balance_status == "SHORTAGE":
        print("⚠️  人員不足状態の対応推奨事項:")
        print("  1. 追加採用の検討")
        print("  2. 既存スタッフの勤務時間調整")
        print("  3. 業務プロセスの効率化")
    else:
        print("✓ 適切な需給バランスが保たれています")
    
    print()
    print("=" * 80)
    print("検証レポート完了")
    print("=" * 80)
    
    return result

if __name__ == "__main__":
    create_comprehensive_validation_report()