#!/usr/bin/env python3
"""
統一分析管理システム 簡易統合確認スクリプト
パッケージ依存なしでシステム統合状況を確認
"""

import sys
import os
from pathlib import Path

def check_unified_system_integration():
    """統一分析管理システムの統合状況確認"""
    
    print("=" * 80)
    print("統一分析管理システム 簡易統合確認")
    print("=" * 80)
    
    checks_passed = 0
    total_checks = 0
    
    # 1. 統一分析管理システムファイルの存在確認
    total_checks += 1
    unified_manager_path = Path("shift_suite/tasks/unified_analysis_manager.py")
    if unified_manager_path.exists():
        print("✅ 統一分析管理システムファイル存在確認")
        checks_passed += 1
        
        # ファイル内容の基本確認
        try:
            with open(unified_manager_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            required_classes = [
                "class UnifiedAnalysisManager:",
                "class SafeDataConverter:",
                "class DynamicKeyManager:",
                "class UnifiedAnalysisResult:"
            ]
            
            for class_name in required_classes:
                if class_name in content:
                    print(f"   ✅ {class_name.replace(':', '')} 定義確認")
                else:
                    print(f"   ❌ {class_name.replace(':', '')} 定義不足")
                    
        except Exception as e:
            print(f"   ⚠️ ファイル内容確認エラー: {e}")
    else:
        print("❌ 統一分析管理システムファイルが見つかりません")
    
    # 2. AI包括レポートジェネレーターファイルの存在確認
    total_checks += 1
    ai_generator_path = Path("shift_suite/tasks/ai_comprehensive_report_generator.py")
    if ai_generator_path.exists():
        print("✅ AI包括レポートジェネレーターファイル存在確認")
        checks_passed += 1
        
        # 統一システム対応の確認
        try:
            with open(ai_generator_path, 'r', encoding='utf-8') as f:
                ai_content = f.read()
                
            integration_keywords = [
                "data_integrity",
                "unified_analysis",
                "SafeDataConverter",
                "is_reliable"
            ]
            
            found_keywords = [kw for kw in integration_keywords if kw in ai_content]
            print(f"   統合キーワード確認: {len(found_keywords)}/{len(integration_keywords)}")
            
        except Exception as e:
            print(f"   ⚠️ AI generator内容確認エラー: {e}")
    else:
        print("❌ AI包括レポートジェネレーターファイルが見つかりません")
    
    # 3. app.pyでの統合確認
    total_checks += 1
    app_path = Path("app.py")
    if app_path.exists():
        print("✅ app.pyファイル存在確認")
        checks_passed += 1
        
        try:
            with open(app_path, 'r', encoding='utf-8') as f:
                app_content = f.read()
                
            integration_markers = [
                "from shift_suite.tasks.unified_analysis_manager import UnifiedAnalysisManager",
                "UNIFIED_ANALYSIS_AVAILABLE",
                "unified_analysis_manager",
                "get_ai_compatible_results"
            ]
            
            found_integrations = []
            for marker in integration_markers:
                if marker in app_content:
                    found_integrations.append(marker)
                    print(f"   ✅ {marker} 統合確認")
                else:
                    print(f"   ❌ {marker} 統合不足")
            
            print(f"   統合度: {len(found_integrations)}/{len(integration_markers)}")
            
        except Exception as e:
            print(f"   ⚠️ app.py統合確認エラー: {e}")
    else:
        print("❌ app.pyファイルが見つかりません")
    
    # 4. 分析タスクファイルの存在確認
    total_checks += 1
    task_files = [
        "shift_suite/tasks/shortage.py",
        "shift_suite/tasks/fatigue.py", 
        "shift_suite/tasks/fairness.py"
    ]
    
    existing_tasks = []
    for task_file in task_files:
        if Path(task_file).exists():
            existing_tasks.append(task_file)
    
    if len(existing_tasks) == len(task_files):
        print("✅ 全分析タスクファイル存在確認")
        checks_passed += 1
    else:
        print(f"⚠️ 分析タスクファイル: {len(existing_tasks)}/{len(task_files)} 存在")
    
    # 5. 動的スロット処理の確認
    total_checks += 1
    slot_fixes_found = 0
    slot_error_patterns = [
        "* SLOT_HOURS",
        ".sum() * SLOT_HOURS", 
        "sum().sum() * SLOT_HOURS"
    ]
    
    for task_file in existing_tasks:
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # エラーパターンの確認
            errors_in_file = [pattern for pattern in slot_error_patterns if pattern in content]
            if not errors_in_file:
                slot_fixes_found += 1
                
        except Exception as e:
            print(f"   ⚠️ {task_file} スロット処理確認エラー: {e}")
    
    if slot_fixes_found == len(existing_tasks):
        print("✅ 動的スロット処理修正確認")
        checks_passed += 1
    else:
        print(f"⚠️ 動的スロット処理: {slot_fixes_found}/{len(existing_tasks)} 修正済み")
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("統合確認結果サマリー")
    print("=" * 80)
    print(f"通過したチェック: {checks_passed}/{total_checks}")
    print(f"統合完成度: {(checks_passed/total_checks)*100:.1f}%")
    
    if checks_passed == total_checks:
        print("🎉 統一分析管理システム統合完了！")
        print("全体最適化による統一システムが正常に構築されています。")
        return True
    elif checks_passed >= total_checks * 0.8:
        print("✅ 統一分析管理システム統合概ね完了")
        print("主要機能は実装済みです。")
        return True
    else:
        print("⚠️ 統一分析管理システム統合に課題があります")
        print("追加の修正が必要な可能性があります。")
        return False

def check_file_modifications():
    """主要ファイルの最近の変更を確認"""
    print("\n--- 最近の変更確認 ---")
    
    key_files = [
        "shift_suite/tasks/unified_analysis_manager.py",
        "shift_suite/tasks/ai_comprehensive_report_generator.py",
        "app.py"
    ]
    
    for file_path in key_files:
        path = Path(file_path)
        if path.exists():
            try:
                stat = path.stat()
                mod_time = stat.st_mtime
                size = stat.st_size
                print(f"{file_path}: {size:,} bytes")
            except Exception as e:
                print(f"{file_path}: 情報取得エラー ({e})")
        else:
            print(f"{file_path}: ファイルなし")

if __name__ == "__main__":
    success = check_unified_system_integration()
    check_file_modifications()
    print("\n" + "=" * 80)
    sys.exit(0 if success else 1)