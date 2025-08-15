#!/usr/bin/env python3
"""
MECE事実抽出システム統合テスト
新しく実装されたMECEFactExtractorとその統合の基本動作を確認
"""

import sys
import traceback
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_basic_imports():
    """基本的なインポートテスト"""
    print("=== 基本インポートテスト ===")
    
    try:
        from shift_suite.tasks.mece_fact_extractor import MECEFactExtractor
        print("✅ MECEFactExtractor インポート成功")
    except Exception as e:
        print(f"❌ MECEFactExtractor インポート失敗: {e}")
        return False
    
    try:
        from shift_suite.tasks.advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2
        print("✅ AdvancedBlueprintEngineV2 インポート成功")
    except Exception as e:
        print(f"❌ AdvancedBlueprintEngineV2 インポート失敗: {e}")
        return False
    
    return True

def test_mece_extractor_basic():
    """MECEFactExtractor基本動作テスト"""
    print("\n=== MECEFactExtractor基本動作テスト ===")
    
    try:
        from shift_suite.tasks.mece_fact_extractor import MECEFactExtractor
        
        # インスタンス作成
        extractor = MECEFactExtractor()
        print("✅ MECEFactExtractor インスタンス作成成功")
        
        # ダミーデータ作成
        dates = pd.date_range(start='2024-01-01', end='2024-01-07', freq='H')
        staff_list = ['佐藤', '田中', '鈴木', '高橋']
        role_list = ['看護師', '介護士', 'リーダー']
        
        dummy_data = []
        for i, date in enumerate(dates):
            if i % 3 == 0:  # 3時間に1回勤務
                dummy_data.append({
                    'ds': date,
                    'staff': staff_list[i % len(staff_list)],
                    'role': role_list[i % len(role_list)],
                    'code': 'D' if 6 <= date.hour <= 18 else 'N',
                    'parsed_slots_count': 1 if i % 3 == 0 else 0,
                    'holiday_type': '通常勤務'
                })
        
        long_df = pd.DataFrame(dummy_data)
        print(f"✅ ダミーlong_df作成成功 ({len(long_df)}行)")
        
        # 空データテスト
        empty_result = extractor.extract_axis1_facility_rules(pd.DataFrame())
        print("✅ 空データ処理成功")
        
        # 実データテスト
        if not long_df.empty:
            result = extractor.extract_axis1_facility_rules(long_df)
            print("✅ MECE事実抽出実行成功")
            
            # 結果構造確認
            expected_keys = ['human_readable', 'machine_readable', 'training_data', 'extraction_metadata']
            for key in expected_keys:
                if key in result:
                    print(f"✅ 結果に{key}キー存在")
                else:
                    print(f"❌ 結果に{key}キー不存在")
                    return False
            
            # human_readable構造確認
            hr = result['human_readable']
            hr_keys = ['抽出事実サマリー', 'MECE分解事実', '確信度別分類']
            for key in hr_keys:
                if key in hr:
                    print(f"✅ human_readableに{key}存在")
                else:
                    print(f"❌ human_readableに{key}不存在")
            
            # machine_readable構造確認  
            mr = result['machine_readable']
            mr_keys = ['hard_constraints', 'soft_constraints', 'preferences']
            for key in mr_keys:
                if key in mr:
                    print(f"✅ machine_readableに{key}存在")
                else:
                    print(f"❌ machine_readableに{key}不存在")
            
            # 抽出件数確認
            total_facts = hr.get('抽出事実サマリー', {}).get('総事実数', 0)
            print(f"📊 抽出された総事実数: {total_facts}")
            
            hard_count = len(mr.get('hard_constraints', []))
            soft_count = len(mr.get('soft_constraints', []))
            pref_count = len(mr.get('preferences', []))
            print(f"📊 制約数 - ハード: {hard_count}, ソフト: {soft_count}, 推奨: {pref_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ MECEFactExtractor基本動作テスト失敗: {e}")
        traceback.print_exc()
        return False

def test_blueprint_engine_integration():
    """AdvancedBlueprintEngineV2統合テスト"""
    print("\n=== AdvancedBlueprintEngineV2統合テスト ===")
    
    try:
        from shift_suite.tasks.advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2
        
        # エンジンインスタンス作成
        engine = AdvancedBlueprintEngineV2()
        print("✅ AdvancedBlueprintEngineV2 インスタンス作成成功")
        
        # MECE extractorの存在確認
        if hasattr(engine, 'mece_extractor'):
            print("✅ MECE extractor統合確認")
        else:
            print("❌ MECE extractor統合失敗")
            return False
        
        # ダミーデータでフル分析実行テスト（軽量版）
        dates = pd.date_range(start='2024-01-01', end='2024-01-02', freq='6H')  # 軽量化
        staff_list = ['スタッフA', 'スタッフB']  # 軽量化
        
        dummy_data = []
        for i, date in enumerate(dates):
            dummy_data.append({
                'ds': date,
                'staff': staff_list[i % len(staff_list)],
                'role': '職種A',
                'code': 'D',
                'parsed_slots_count': 1,
                'holiday_type': '通常勤務'
            })
        
        long_df = pd.DataFrame(dummy_data)
        
        # フル分析実行（タイムアウト対策で短時間制限）
        print("⏳ フル分析実行中...")
        result = engine.run_full_blueprint_analysis(long_df)
        print("✅ フル分析実行成功")
        
        # 結果にMECE事実が含まれているか確認
        if 'mece_facility_facts' in result:
            print("✅ MECE事実抽出結果がフル分析に統合されている")
            
            mece_facts = result['mece_facility_facts']
            if 'human_readable' in mece_facts and 'machine_readable' in mece_facts:
                print("✅ MECE事実抽出結果の構造が正常")
            else:
                print("❌ MECE事実抽出結果の構造に問題")
                return False
        else:
            print("❌ MECE事実抽出結果がフル分析に統合されていない")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ AdvancedBlueprintEngineV2統合テスト失敗: {e}")
        traceback.print_exc()
        return False

def test_json_serialization():
    """JSON出力テスト"""
    print("\n=== JSON出力テスト ===")
    
    try:
        import json
        from shift_suite.tasks.mece_fact_extractor import MECEFactExtractor
        
        extractor = MECEFactExtractor()
        
        # ダミーデータ作成
        dates = pd.date_range(start='2024-01-01', end='2024-01-02', freq='4H')
        dummy_data = []
        for i, date in enumerate(dates):
            dummy_data.append({
                'ds': date,
                'staff': f'スタッフ{i%2}',
                'role': '職種A',
                'code': 'D',
                'parsed_slots_count': 1,
                'holiday_type': '通常勤務'
            })
        
        long_df = pd.DataFrame(dummy_data)
        result = extractor.extract_axis1_facility_rules(long_df)
        
        # JSON変換テスト
        machine_readable = result['machine_readable']
        json_str = json.dumps(machine_readable, ensure_ascii=False, indent=2)
        print("✅ 機械実行用制約データのJSON変換成功")
        print(f"📊 JSONサイズ: {len(json_str)}文字")
        
        # JSONパースバックテスト
        parsed_back = json.loads(json_str)
        if parsed_back == machine_readable:
            print("✅ JSONパースバック成功")
        else:
            print("❌ JSONパースバック失敗")
            return False
        
        # レポート用JSON変換テスト
        human_readable = result['human_readable']
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "テスト用MECE施設ルール事実抽出レポート"
            },
            "summary": human_readable.get('抽出事実サマリー', {}),
            "facts": human_readable.get('MECE分解事実', {}),
        }
        
        report_json_str = json.dumps(report_data, ensure_ascii=False, indent=2)
        print("✅ 人間確認用レポートのJSON変換成功")
        print(f"📊 レポートJSONサイズ: {len(report_json_str)}文字")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON出力テスト失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("🧪 MECE事実抽出システム統合テスト開始")
    print("=" * 50)
    
    test_results = []
    
    # 各テスト実行
    test_results.append(("基本インポート", test_basic_imports()))
    test_results.append(("MECEFactExtractor基本動作", test_mece_extractor_basic()))
    test_results.append(("AdvancedBlueprintEngineV2統合", test_blueprint_engine_integration()))
    test_results.append(("JSON出力", test_json_serialization()))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("🧪 テスト結果サマリー")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        if result:
            print(f"✅ {test_name}: 成功")
            passed += 1
        else:
            print(f"❌ {test_name}: 失敗")
            failed += 1
    
    print(f"\n📊 合計: {passed + failed}テスト, 成功: {passed}, 失敗: {failed}")
    
    if failed == 0:
        print("🎉 全テスト成功！MECE事実抽出システムの統合が完了しました。")
        return True
    else:
        print("⚠️ 一部テスト失敗。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)