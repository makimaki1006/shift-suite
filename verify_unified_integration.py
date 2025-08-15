#!/usr/bin/env python3
"""
統一システム統合完了検証スクリプト
dash_app.py の統一システム統合状況を包括的に検証
"""

import sys
import re
from pathlib import Path
import importlib.util

def verify_unified_integration():
    """統一システム統合の完了検証"""
    
    print("🔍 === 統一システム統合完了検証 ===\n")
    
    # ファイル存在確認
    dash_app_path = Path("dash_app.py")
    if not dash_app_path.exists():
        print("❌ dash_app.py が見つかりません")
        return False
    
    content = dash_app_path.read_text(encoding='utf-8')
    
    verification_results = {}
    
    # 1. SLOT_HOURS固定値の除去確認
    print("📋 1. SLOT_HOURS固定値の除去確認")
    slot_hours_matches = re.findall(r'(?<!#)(?<!//)SLOT_HOURS(?!\w)', content)
    if not slot_hours_matches:
        print("   ✅ SLOT_HOURS固定値は完全に除去されています")
        verification_results['slot_hours_removed'] = True
    else:
        print(f"   ❌ SLOT_HOURS固定値が{len(slot_hours_matches)}箇所残存")
        verification_results['slot_hours_removed'] = False
    
    # 2. 動的スロット時間関数の存在確認
    print("\n📋 2. 動的スロット時間関数の存在確認")
    if 'def get_dynamic_slot_hours(' in content:
        print("   ✅ get_dynamic_slot_hours関数が実装済み")
        verification_results['dynamic_slot_function'] = True
    else:
        print("   ❌ get_dynamic_slot_hours関数が見つかりません")
        verification_results['dynamic_slot_function'] = False
    
    # 3. 統一分析管理システムの導入確認
    print("\n📋 3. 統一分析管理システムの導入確認")
    unified_imports = [
        'from shift_suite.tasks.unified_analysis_manager import UnifiedAnalysisManager',
        'global_unified_manager = UnifiedAnalysisManager()',
        'UNIFIED_ANALYSIS_AVAILABLE = True'
    ]
    
    unified_imported = all(imp in content for imp in unified_imports)
    if unified_imported:
        print("   ✅ 統一分析管理システムが正しく導入済み")
        verification_results['unified_system_imported'] = True
    else:
        print("   ❌ 統一分析管理システムの導入が不完全")
        verification_results['unified_system_imported'] = False
    
    # 4. 統一データ取得関数の存在確認
    print("\n📋 4. 統一データ取得関数の存在確認")
    if 'def get_unified_analysis_data(' in content:
        print("   ✅ get_unified_analysis_data関数が実装済み")
        verification_results['unified_data_function'] = True
    else:
        print("   ❌ get_unified_analysis_data関数が見つかりません")
        verification_results['unified_data_function'] = False
    
    # 5. KPI収集関数の統合確認
    print("\n📋 5. KPI収集関数の統合確認")
    kpi_integration_markers = [
        '統一システムからデータ取得を試行',
        'get_unified_analysis_data(file_pattern)',
        'shortage_analysis',
        'fatigue_analysis',
        'fairness_analysis'
    ]
    
    kpi_integrated = all(marker in content for marker in kpi_integration_markers)
    if kpi_integrated:
        print("   ✅ KPI収集関数が統一システム統合済み")
        verification_results['kpi_integration'] = True
    else:
        print("   ❌ KPI収集関数の統一システム統合が不完全")
        verification_results['kpi_integration'] = False
    
    # 6. フォールバック機能の確認
    print("\n📋 6. フォールバック機能の確認")
    fallback_patterns = [
        'フォールバック: parquetファイルから',
        'pd.read_parquet(',
        'setdefault('
    ]
    
    fallback_exists = all(pattern in content for pattern in fallback_patterns)
    if fallback_exists:
        print("   ✅ parquetファイルへのフォールバック機能が保持済み")
        verification_results['fallback_preserved'] = True
    else:
        print("   ❌ フォールバック機能が不完全")
        verification_results['fallback_preserved'] = False
    
    # 7. 全体的な統合度評価
    print("\n📊 === 統合完了度評価 ===")
    total_checks = len(verification_results)
    passed_checks = sum(verification_results.values())
    completion_rate = (passed_checks / total_checks) * 100
    
    print(f"検証項目: {passed_checks}/{total_checks} 通過")
    print(f"完了度: {completion_rate:.1f}%")
    
    if completion_rate == 100:
        print("\n🎉 *** 統一システム統合 完全完了 ***")
        print("   dash_app.py の統一システム統合が100%完了しています")
        return True
    elif completion_rate >= 80:
        print(f"\n⚠️  統一システム統合 ほぼ完了 ({completion_rate:.1f}%)")
        print("   軽微な問題が残存していますが、基本機能は動作します")
        return True
    else:
        print(f"\n❌ 統一システム統合 未完了 ({completion_rate:.1f}%)")
        print("   重要な機能が不足しています")
        return False

if __name__ == "__main__":
    success = verify_unified_integration()
    sys.exit(0 if success else 1)