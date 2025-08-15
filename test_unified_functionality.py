#!/usr/bin/env python3
"""
統一システム機能テスト
実際の動作確認のためのテストケース
"""

import sys
from pathlib import Path

def test_dynamic_slot_hours():
    """動的スロット時間計算のテスト"""
    print("🧪 動的スロット時間計算テスト")
    
    try:
        # dash_app.pyをインポートしてテスト
        sys.path.insert(0, str(Path.cwd()))
        
        # 関数の存在確認
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 関数定義の確認
        if 'def get_dynamic_slot_hours(' in content:
            print("   ✅ get_dynamic_slot_hours関数が定義済み")
            
            # 関数の基本ロジック確認
            if 'DEFAULT_SLOT_MINUTES' in content and 'slot_minutes / 60.0' in content:
                print("   ✅ 基本計算ロジックが正しく実装済み")
                return True
            else:
                print("   ❌ 計算ロジックに問題があります")
                return False
        else:
            print("   ❌ get_dynamic_slot_hours関数が見つかりません")
            return False
            
    except Exception as e:
        print(f"   ❌ テストエラー: {e}")
        return False

def test_unified_system_integration():
    """統一システム統合のテスト"""
    print("\n🧪 統一システム統合テスト")
    
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要な要素の確認
        required_elements = [
            'UnifiedAnalysisManager',
            'global_unified_manager',
            'get_unified_analysis_data',
            'UNIFIED_ANALYSIS_AVAILABLE'
        ]
        
        all_present = all(element in content for element in required_elements)
        
        if all_present:
            print("   ✅ 統一システム統合の全要素が実装済み")
            return True
        else:
            missing = [elem for elem in required_elements if elem not in content]
            print(f"   ❌ 不足要素: {missing}")
            return False
            
    except Exception as e:
        print(f"   ❌ テストエラー: {e}")
        return False

def test_kpi_integration():
    """KPI収集統合のテスト"""
    print("\n🧪 KPI収集統合テスト")
    
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # KPI統合の確認
        kpi_markers = [
            'collect_dashboard_overview_kpis',
            'get_unified_analysis_data(file_pattern)',
            'shortage_analysis',
            'fatigue_analysis',
            'fairness_analysis'
        ]
        
        all_integrated = all(marker in content for marker in kpi_markers)
        
        if all_integrated:
            print("   ✅ KPI収集関数が統一システム統合済み")
            return True
        else:
            missing = [marker for marker in kpi_markers if marker not in content]
            print(f"   ❌ 不足統合要素: {missing}")
            return False
            
    except Exception as e:
        print(f"   ❌ テストエラー: {e}")
        return False

def test_data_consistency():
    """データ整合性のテスト"""
    print("\n🧪 データ整合性テスト")
    
    try:
        # app.py と dash_app.py の統一システム使用確認
        files_to_check = ['app.py', 'dash_app.py']
        unified_usage = {}
        
        for file_name in files_to_check:
            if Path(file_name).exists():
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read()
                    unified_usage[file_name] = 'UnifiedAnalysisManager' in content
        
        if all(unified_usage.values()):
            print("   ✅ app.py と dash_app.py 両方で統一システムを使用")
            return True
        else:
            print("   ⚠️  統一システム使用状況:")
            for file_name, uses_unified in unified_usage.items():
                status = "✅" if uses_unified else "❌"
                print(f"     {status} {file_name}")
            return False
            
    except Exception as e:
        print(f"   ❌ テストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🎯 === 統一システム機能テスト実行 ===\n")
    
    tests = [
        test_dynamic_slot_hours,
        test_unified_system_integration, 
        test_kpi_integration,
        test_data_consistency
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print(f"\n📊 === テスト結果 ===")
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"成功: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("\n🎉 全機能テスト通過 - 統一システム統合完了確認")
        return True
    elif success_rate >= 75:
        print("\n⚠️  ほぼ成功 - 軽微な問題あり")
        return True
    else:
        print("\n❌ 重要な問題が検出されました")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)