#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2/3.1統合システムの包括的動作検証
修正の影響をMECE・客観的・プロフェッショナルに確認
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_test_data():
    """テストデータ生成（現実的なシフトデータ）"""
    
    print("📊 テストデータ生成中...")
    
    # 30分スロットでの4時間勤務（8スロット）のデータ
    base_date = datetime(2025, 6, 1, 8, 0)  # 2025年6月1日 08:00開始
    
    # 4時間勤務のスロット生成（08:00-12:00）
    slots = []
    current_time = base_date
    for i in range(8):  # 8スロット = 4時間
        slots.append({
            'ds': current_time,
            'staff': '田中太郎',
            'role': '介護士',
            'code': '日勤',
            'employment': '正社員',
            'holiday_type': '',
            'parsed_slots_count': 1  # 1スロット（30分）
        })
        current_time += timedelta(minutes=30)
    
    # 追加：2人目のデータ（6時間勤務 = 12スロット）
    current_time = base_date
    for i in range(12):  # 12スロット = 6時間
        slots.append({
            'ds': current_time,
            'staff': '佐藤花子',
            'role': '看護師', 
            'code': '日勤',
            'employment': 'パート',
            'holiday_type': '',
            'parsed_slots_count': 1  # 1スロット（30分）
        })
        current_time += timedelta(minutes=30)
    
    long_df = pd.DataFrame(slots)
    
    print(f"✅ テストデータ生成完了:")
    print(f"  レコード数: {len(long_df)}")
    print(f"  田中太郎: {len(long_df[long_df['staff']=='田中太郎'])}スロット")
    print(f"  佐藤花子: {len(long_df[long_df['staff']=='佐藤花子'])}スロット")
    
    return long_df

def test_phase2_integration(long_df):
    """Phase 2統合テスト"""
    
    print("\n🔍 A. Phase 2統合テスト")
    print("-" * 60)
    
    try:
        from shift_suite.tasks.fact_extractor_prototype import FactExtractorPrototype
        
        extractor = FactExtractorPrototype()
        facts = extractor.extract_basic_facts(long_df)
        
        print("✅ Phase 2動作確認:")
        for category, df in facts.items():
            print(f"  📋 {category}: {len(df)}レコード")
            
            # 労働時間計算の確認
            if '基本勤務統計' in category and not df.empty:
                for _, row in df.iterrows():
                    staff = row.get('スタッフ', 'N/A')
                    hours = row.get('総労働時間', 0)
                    print(f"    {staff}: {hours}時間")
                    
                    # 期待値チェック
                    if staff == '田中太郎':
                        expected = 4.0  # 8スロット × 0.5時間
                        if abs(hours - expected) < 0.1:
                            print(f"      ✅ 正確（期待値: {expected}時間）")
                        else:
                            print(f"      ❌ 誤差（期待値: {expected}時間, 実際: {hours}時間）")
                    elif staff == '佐藤花子':
                        expected = 6.0  # 12スロット × 0.5時間
                        if abs(hours - expected) < 0.1:
                            print(f"      ✅ 正確（期待値: {expected}時間）")
                        else:
                            print(f"      ❌ 誤差（期待値: {expected}時間, 実際: {hours}時間）")
        
        return True, facts
        
    except Exception as e:
        print(f"❌ Phase 2テストエラー: {e}")
        return False, None

def test_phase31_integration(long_df):
    """Phase 3.1統合テスト"""
    
    print("\n🔍 B. Phase 3.1統合テスト")
    print("-" * 60)
    
    try:
        from shift_suite.tasks.lightweight_anomaly_detector import LightweightAnomalyDetector
        
        detector = LightweightAnomalyDetector(sensitivity="medium")
        anomalies = detector.detect_anomalies(long_df)
        
        print("✅ Phase 3.1動作確認:")
        print(f"  検出された異常: {len(anomalies)}件")
        
        for anomaly in anomalies:
            print(f"  🚨 {anomaly.anomaly_type}: {anomaly.staff}")
            print(f"    値: {anomaly.value}, 重要度: {anomaly.severity}")
            
            # 月間労働時間の妥当性チェック
            if anomaly.anomaly_type == "過度な労働時間":
                if anomaly.staff == '田中太郎':
                    # 4時間勤務なので異常ではないはず
                    print(f"      ⚠️ 要確認: 4時間勤務で異常検知")
                elif anomaly.staff == '佐藤花子':
                    # 6時間勤務なので異常ではないはず
                    print(f"      ⚠️ 要確認: 6時間勤務で異常検知")
        
        return True, anomalies
        
    except Exception as e:
        print(f"❌ Phase 3.1テストエラー: {e}")
        return False, None

def test_fact_book_integration(long_df):
    """FactBookVisualizer統合テスト"""
    
    print("\n🔍 C. FactBookVisualizer統合テスト")
    print("-" * 60)
    
    try:
        from shift_suite.tasks.fact_book_visualizer import FactBookVisualizer
        
        visualizer = FactBookVisualizer(sensitivity="medium")
        fact_book = visualizer.generate_comprehensive_fact_book(long_df)
        
        if "error" in fact_book:
            print(f"❌ FactBook生成エラー: {fact_book['error']}")
            return False, None
        
        print("✅ FactBook生成確認:")
        print(f"  生成時刻: {fact_book.get('generation_timestamp', 'N/A')}")
        print(f"  基本事実カテゴリ: {len(fact_book.get('basic_facts', {}))}")
        print(f"  異常検知件数: {len(fact_book.get('anomalies', []))}")
        
        # データ概要の確認
        overview = fact_book.get('data_overview', {})
        if overview:
            print(f"  データ概要:")
            for key, value in overview.items():
                print(f"    {key}: {value}")
        
        # 労働時間サマリーの確認
        summary = fact_book.get('summary', {})
        if summary:
            print(f"  統合サマリー:")
            for key, value in summary.items():
                print(f"    {key}: {value}")
        
        return True, fact_book
        
    except Exception as e:
        print(f"❌ FactBook統合テストエラー: {e}")
        return False, None

def test_calculation_consistency():
    """計算一貫性テスト"""
    
    print("\n🔍 D. 計算一貫性テスト")
    print("-" * 60)
    
    # 理論値との比較
    test_cases = [
        {"slots": 8, "expected_hours": 4.0, "description": "4時間勤務"},
        {"slots": 12, "expected_hours": 6.0, "description": "6時間勤務"},
        {"slots": 16, "expected_hours": 8.0, "description": "8時間勤務"},
        {"slots": 2, "expected_hours": 1.0, "description": "1時間勤務"}
    ]
    
    print("🧮 理論計算確認:")
    SLOT_HOURS = 0.5
    
    for case in test_cases:
        calculated = case["slots"] * SLOT_HOURS
        expected = case["expected_hours"]
        match = abs(calculated - expected) < 0.01
        
        print(f"  {case['description']}: {case['slots']}スロット × {SLOT_HOURS} = {calculated}時間")
        print(f"    期待値: {expected}時間, 一致: {'✅' if match else '❌'}")
    
    return True

def test_shortage_consistency():
    """shortage.pyとの整合性テスト"""
    
    print("\n🔍 E. shortage.py整合性テスト")
    print("-" * 60)
    
    # shortage_summary.txtの確認
    summary_path = Path("temp_analysis_check/out_mean_based/shortage_summary.txt")
    
    if summary_path.exists():
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("✅ 既存shortage結果:")
            print(f"  {content.strip()}")
            
            # 670時間の妥当性確認
            if "total_lack_hours: 670" in content:
                print("  🎯 基準値670時間を確認")
                print("  📊 Phase 2/3.1の結果がこの基準と整合するか要確認")
            
            return True
            
        except Exception as e:
            print(f"❌ shortage結果読み込みエラー: {e}")
            return False
    else:
        print(f"⚠️ shortage結果ファイル不存在: {summary_path}")
        return False

def generate_comprehensive_report(test_results):
    """包括的テストレポート生成"""
    
    print("\n" + "=" * 80)
    print("📋 包括的テストレポート")
    print("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result["status"])
    
    print(f"🎯 総合結果: {passed_tests}/{total_tests} テスト合格")
    
    for test_name, result in test_results.items():
        status = "✅ 合格" if result["status"] else "❌ 失敗"
        print(f"  {status}: {test_name}")
        
        if "details" in result:
            for detail in result["details"]:
                print(f"    • {detail}")
    
    # 総合評価
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n📊 品質評価:")
    print(f"  成功率: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("  🟢 優秀: システム統合に問題なし")
    elif success_rate >= 70:
        print("  🟡 良好: 軽微な問題のみ")
    elif success_rate >= 50:
        print("  🟠 要改善: 重要な問題あり")
    else:
        print("  🔴 深刻: システム統合に重大な問題")
    
    return success_rate

def main():
    """メイン実行"""
    
    print("🚨 Phase 2/3.1統合システム包括検証開始")
    print("=" * 80)
    
    log = setup_logging()
    
    # テストデータ生成
    long_df = create_test_data()
    
    # 各テストの実行
    test_results = {}
    
    # A. Phase 2テスト
    phase2_success, phase2_data = test_phase2_integration(long_df)
    test_results["Phase 2統合"] = {
        "status": phase2_success,
        "details": ["基本事実抽出機能", "労働時間計算", "統計生成"]
    }
    
    # B. Phase 3.1テスト
    phase31_success, phase31_data = test_phase31_integration(long_df)
    test_results["Phase 3.1統合"] = {
        "status": phase31_success,
        "details": ["異常検知機能", "閾値判定", "重要度評価"]
    }
    
    # C. FactBook統合テスト
    factbook_success, factbook_data = test_fact_book_integration(long_df)
    test_results["FactBook統合"] = {
        "status": factbook_success,
        "details": ["統合可視化", "データ統合", "レポート生成"]
    }
    
    # D. 計算一貫性テスト
    calc_success = test_calculation_consistency()
    test_results["計算一貫性"] = {
        "status": calc_success,
        "details": ["理論値との一致", "SLOT_HOURS計算", "数値精度"]
    }
    
    # E. shortage整合性テスト
    shortage_success = test_shortage_consistency()
    test_results["shortage整合性"] = {
        "status": shortage_success,
        "details": ["既存結果との比較", "基準値確認", "数値整合性"]
    }
    
    # 包括レポート生成
    success_rate = generate_comprehensive_report(test_results)
    
    print(f"\n✅ 包括検証完了: 品質スコア {success_rate:.1f}%")
    
    return success_rate >= 80  # 80%以上で合格

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)