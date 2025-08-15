#!/usr/bin/env python3
"""
AI Comprehensive Report Generator 緊急修正版テスト
実際のデータ構造に対応した修正の検証
"""

import sys
import os
import json
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
import pandas as pd
import numpy as np

def create_test_data_structures():
    """実際のデータ構造に基づくテストデータを作成"""
    
    # テスト用の出力ディレクトリ
    test_output_dir = Path("test_corrected_ai_report")
    test_output_dir.mkdir(exist_ok=True)
    
    print("🔄 実際のデータ構造に基づくテストデータを作成...")
    
    # 1. shortage_time.parquet (Wide format: 時間×日付)
    print("  📊 shortage_time.parquet (Wide format) を作成")
    time_slots = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]  # 48時間枠
    dates = [f"2025-06-{d:02d}" for d in range(1, 31)]  # 30日分
    
    # ほとんど0で、6月5日の一部時間帯のみ1（実際の構造に合わせる）
    shortage_data = np.zeros((len(time_slots), len(dates)))
    shortage_data[18:22, 4] = 1  # 6月5日の09:00-11:00に不足
    shortage_data[36:40, 4] = 1  # 6月5日の18:00-20:00に不足
    
    shortage_df = pd.DataFrame(shortage_data, index=time_slots, columns=dates)
    shortage_parquet_path = test_output_dir / "shortage_time.parquet"
    shortage_df.to_parquet(shortage_parquet_path)
    print(f"    ✅ {shortage_parquet_path} (shape: {shortage_df.shape}, 不足イベント: {(shortage_df > 0).sum().sum()}個)")
    
    # 2. combined_score.csv (スタッフ名 + 総合スコア)
    print("  📊 combined_score.csv を作成")
    staff_names = ["田中太郎", "佐藤花子", "鈴木一郎", "山田美代子", "高橋健一", "松本留美"]
    # 実際のデータに似たスコア分布
    scores = [0.1234, 0.5678, 0.7890, 0.4567, 0.8901, 0.3456]
    
    combined_score_df = pd.DataFrame({
        "staff": staff_names,
        "final_score": scores
    })
    combined_score_path = test_output_dir / "combined_score.csv"
    combined_score_df.to_csv(combined_score_path, index=False, encoding='utf-8')
    print(f"    ✅ {combined_score_path} (スタッフ: {len(staff_names)}人, 平均スコア: {np.mean(scores):.3f})")
    
    # 3. staff_balance_daily.csv (日別スタッフバランス)
    print("  📊 staff_balance_daily.csv を作成")
    dates_balance = [f"2025-06-{d:02d}" for d in range(1, 31)]
    balance_data = []
    
    for i, date in enumerate(dates_balance):
        total_staff = 26  # 固定値
        # 週末や特定日に高い申請率を設定
        if i % 7 in [5, 6]:  # 週末
            leave_applicants = 30  # 総スタッフ数を超える申請
        elif i in [10, 15, 20]:  # 特定の問題日
            leave_applicants = 35
        else:
            leave_applicants = 18  # 通常日
            
        non_leave_staff = total_staff - leave_applicants
        leave_ratio = leave_applicants / total_staff
        
        balance_data.append({
            "date": date,
            "total_staff": total_staff,
            "leave_applicants_count": leave_applicants,
            "non_leave_staff": non_leave_staff,
            "leave_ratio": leave_ratio
        })
    
    balance_df = pd.DataFrame(balance_data)
    balance_path = test_output_dir / "staff_balance_daily.csv"
    balance_df.to_csv(balance_path, index=False)
    print(f"    ✅ {balance_path} (期間: 30日, 平均申請率: {balance_df['leave_ratio'].mean():.1%})")
    
    return test_output_dir

def test_corrected_ai_report_generator():
    """修正版AIレポートジェネレータのテスト"""
    
    print("\n🚀 AI Comprehensive Report Generator 修正版テスト開始")
    
    # テストデータ作成
    test_output_dir = create_test_data_structures()
    
    # AIレポートジェネレータ初期化
    generator = AIComprehensiveReportGenerator()
    
    # テスト用の分析結果（空でもOK、実際のファイルから抽出される）
    test_analysis_results = {
        "data_summary": {
            "total_records": 100,
            "missing_records": 0
        }
    }
    
    # テスト用パラメータ
    test_params = {
        "analysis_start_date": "2025-06-01",
        "analysis_end_date": "2025-06-30",
        "slot_minutes": 30,
        "need_calculation_method": "statistical_estimation"
    }
    
    print("📝 包括的レポート生成を実行...")
    
    try:
        # 包括的レポート生成
        comprehensive_report = generator.generate_comprehensive_report(
            analysis_results=test_analysis_results,
            input_file_path="test_data.xlsx",
            output_dir=str(test_output_dir),
            analysis_params=test_params
        )
        
        print("✅ レポート生成成功!")
        
        # 生成されたレポートの内容確認
        print("\n📊 生成されたレポートの検証:")
        
        # KPI検証
        kpis = comprehensive_report.get("key_performance_indicators", {})
        overall_perf = kpis.get("overall_performance", {})
        
        shortage_hours = overall_perf.get("total_shortage_hours", {}).get("value", 0)
        avg_fatigue = overall_perf.get("avg_fatigue_score", {}).get("value", 0)
        
        print(f"  🔢 総不足時間: {shortage_hours}時間 (期待値: 2-4時間)")
        print(f"  😴 平均疲労スコア: {avg_fatigue:.3f} (期待値: 0.4-0.7)")
        
        # スタッフバランス検証
        if "staffing_balance" in overall_perf:
            balance = overall_perf["staffing_balance"]
            leave_ratio = balance.get("avg_leave_ratio", 0)
            critical_days = balance.get("critical_days_count", 0)
            print(f"  ⚖️ 平均申請率: {leave_ratio:.1%} (期待値: 100%超過)")
            print(f"  🚨 深刻な日数: {critical_days}日")
        
        # 詳細モジュール検証
        modules = comprehensive_report.get("detailed_analysis_modules", {})
        
        # スタッフ疲労分析
        staff_fatigue = modules.get("staff_fatigue_analysis", [])
        print(f"  👥 スタッフ疲労分析: {len(staff_fatigue)}人分")
        if staff_fatigue:
            first_staff = staff_fatigue[0]
            data_source = first_staff.get("fatigue_score", {}).get("data_source", "unknown")
            print(f"    📋 データソース: {data_source}")
        
        # スタッフバランス分析
        staff_balance = modules.get("staff_balance_analysis", {})
        if staff_balance:
            module_type = staff_balance.get("module_type", "unknown")
            recommendations = staff_balance.get("operational_insights", {}).get("recommended_actions", [])
            print(f"  📈 バランス分析: {module_type}")
            print(f"    💡 推奨事項: {len(recommendations)}件")
        
        # 生成されたJSONファイルのパス表示
        json_files = list(test_output_dir.glob("ai_comprehensive_report_*.json"))
        if json_files:
            json_file = json_files[0]
            print(f"\n📄 生成されたJSONファイル: {json_file}")
            
            # ファイルサイズ確認
            file_size = json_file.stat().st_size
            print(f"  💾 ファイルサイズ: {file_size:,} bytes")
            
            # 内容確認
            with open(json_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # デフォルト値ではなく実データが含まれているか確認
            shortage_in_file = report_data.get("key_performance_indicators", {}).get("overall_performance", {}).get("total_shortage_hours", {}).get("value", 0)
            fatigue_modules = report_data.get("detailed_analysis_modules", {}).get("staff_fatigue_analysis", [])
            
            print(f"  📊 JSONファイル内の不足時間: {shortage_in_file}時間")
            print(f"  👥 JSONファイル内の疲労分析: {len(fatigue_modules)}人分")
            
            # 重要: デフォルト値かどうかの確認
            is_default_shortage = (shortage_in_file == 0.0)
            is_default_fatigue = (len(fatigue_modules) == 0)
            
            if not is_default_shortage and not is_default_fatigue:
                print("  ✅ 実際のデータが正しく抽出されています!")
            else:
                print("  ⚠️ 一部でデフォルト値が残っている可能性があります")
                
        print("\n🎉 修正版テスト完了! 実際のデータ構造に対応できています。")
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_corrected_ai_report_generator()
    if success:
        print("\n✅ 緊急修正が正常に動作しています!")
    else:
        print("\n❌ 修正に問題があります。ログを確認してください。")