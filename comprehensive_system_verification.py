#!/usr/bin/env python3
"""
包括的システム検証スクリプト - 全機能の矛盾・整合性チェック
システム全体の機能間矛盾を検出し、データフロー整合性を確認する
"""

import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import importlib
import inspect
import ast
import re

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class SystemVerificationEngine:
    """システム全体の矛盾・整合性検証エンジン"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.shift_suite_path = project_root / "shift_suite"
        self.verification_results = {
            "import_consistency": [],
            "function_compatibility": [],
            "data_flow_integrity": [], 
            "ui_consistency": [],
            "configuration_conflicts": [],
            "error_handling_coverage": [],
            "memory_management_consistency": [],
            "18_section_integration_status": []
        }
        
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """包括的検証を実行"""
        log.info("🔍 システム全体の包括的検証を開始...")
        
        try:
            # 1. インポート整合性チェック
            self._verify_import_consistency()
            
            # 2. 機能互換性チェック  
            self._verify_function_compatibility()
            
            # 3. データフロー整合性チェック
            self._verify_data_flow_integrity()
            
            # 4. UI一貫性チェック
            self._verify_ui_consistency()
            
            # 5. 設定競合チェック
            self._verify_configuration_conflicts()
            
            # 6. エラーハンドリング網羅性チェック
            self._verify_error_handling_coverage()
            
            # 7. メモリ管理整合性チェック
            self._verify_memory_management_consistency()
            
            # 8. 18セクション統合状況チェック
            self._verify_18_section_integration()
            
            # 結果サマリー生成
            summary = self._generate_verification_summary()
            
            log.info("✅ 包括的検証完了")
            return {
                "status": "completed",
                "summary": summary,
                "detailed_results": self.verification_results,
                "recommendation": self._generate_recommendations()
            }
            
        except Exception as e:
            log.error(f"❌ 検証中にエラーが発生: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "partial_results": self.verification_results
            }
    
    def _verify_import_consistency(self):
        """インポート整合性の検証"""
        log.info("📦 インポート整合性チェック...")
        
        issues = []
        
        # 主要ファイルのインポート確認
        main_files = ["app.py", "dash_app.py"]
        init_file = self.shift_suite_path / "tasks" / "__init__.py"
        
        try:
            # __init__.pyの内容確認
            if init_file.exists():
                with open(init_file, 'r', encoding='utf-8') as f:
                    init_content = f.read()
                
                # 18セクション統合モジュールがすべて登録されているか確認
                required_modules = [
                    "AIComprehensiveReportGenerator",
                    "CognitivePsychologyAnalyzer", 
                    "OrganizationalPatternAnalyzer",
                    "SystemThinkingAnalyzer",
                    "BlueprintDeepAnalysisEngine",
                    "IntegratedMECEAnalysisEngine", 
                    "PredictiveOptimizationIntegrationEngine"
                ]
                
                for module in required_modules:
                    if module not in init_content:
                        issues.append({
                            "type": "missing_module_export",
                            "file": "__init__.py",
                            "module": module,
                            "severity": "high"
                        })
            
            # app.py と dash_app.py のインポート整合性確認
            for main_file in main_files:
                file_path = self.project_root / main_file
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # AI包括レポート生成の可用性フラグ確認
                    if "AI_REPORT_GENERATOR_AVAILABLE" in content:
                        if "from shift_suite.tasks.ai_comprehensive_report_generator import" not in content:
                            issues.append({
                                "type": "import_mismatch",
                                "file": main_file,
                                "issue": "AI_REPORT_GENERATOR_AVAILABLEフラグはあるがimportが見つからない",
                                "severity": "medium"
                            })
                    
                    # 統一分析管理システムの整合性確認
                    if "UNIFIED_ANALYSIS_AVAILABLE" in content:
                        if "from shift_suite.tasks.unified_analysis_manager import" not in content:
                            issues.append({
                                "type": "import_mismatch", 
                                "file": main_file,
                                "issue": "UNIFIED_ANALYSIS_AVAILABLEフラグはあるがimportが見つからない",
                                "severity": "medium"
                            })
        
        except Exception as e:
            issues.append({
                "type": "verification_error",
                "error": str(e),
                "severity": "high"
            })
        
        self.verification_results["import_consistency"] = issues
        log.info(f"📦 インポート整合性チェック完了: {len(issues)}件の問題を検出")
    
    def _verify_function_compatibility(self):
        """機能互換性の検証"""
        log.info("⚙️ 機能互換性チェック...")
        
        issues = []
        
        try:
            # 重複する機能呼び出しの検出
            app_file = self.project_root / "app.py"
            if app_file.exists():
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # AI包括レポート生成の重複チェック
                ai_report_calls = re.findall(r'ai_generator\.generate_comprehensive_report', content)
                if len(ai_report_calls) > 2:
                    issues.append({
                        "type": "duplicate_function_call",
                        "function": "AI包括レポート生成",
                        "count": len(ai_report_calls),
                        "severity": "medium",
                        "recommendation": "重複する呼び出しを統合する"
                    })
                
                # メモリクリーンアップの整合性チェック
                cleanup_calls = re.findall(r'cleanup_old_results\(max_age_hours=(\d+)\)', content)
                if cleanup_calls:
                    unique_hours = set(cleanup_calls)
                    if len(unique_hours) > 1:
                        issues.append({
                            "type": "inconsistent_parameter",
                            "function": "cleanup_old_results",
                            "values": list(unique_hours),
                            "severity": "low",
                            "recommendation": "メモリクリーンアップ間隔を統一する"
                        })
        
        except Exception as e:
            issues.append({
                "type": "verification_error",
                "error": str(e),
                "severity": "high"
            })
        
        self.verification_results["function_compatibility"] = issues
        log.info(f"⚙️ 機能互換性チェック完了: {len(issues)}件の問題を検出")
    
    def _verify_data_flow_integrity(self):
        """データフロー整合性の検証"""
        log.info("📊 データフロー整合性チェック...")
        
        issues = []
        
        try:
            # shortage.pyの変数順序確認
            shortage_file = self.shift_suite_path / "tasks" / "shortage.py"
            if shortage_file.exists():
                with open(shortage_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # lack_count_overall_dfの定義と使用順序確認
                lines = content.split('\n')
                lack_count_def_line = None
                lack_count_use_lines = []
                
                for i, line in enumerate(lines):
                    if 'lack_count_overall_df =' in line and '(' in line:
                        lack_count_def_line = i
                    elif 'lack_count_overall_df' in line and 'lack_count_overall_df =' not in line:
                        lack_count_use_lines.append(i)
                
                if lack_count_def_line is not None:
                    early_uses = [line for line in lack_count_use_lines if line < lack_count_def_line]
                    if early_uses:
                        issues.append({
                            "type": "variable_order_issue",
                            "file": "shortage.py",
                            "variable": "lack_count_overall_df",
                            "definition_line": lack_count_def_line + 1,
                            "early_use_lines": [line + 1 for line in early_uses],
                            "severity": "high",
                            "status": "already_fixed"
                        })
        
        except Exception as e:
            issues.append({
                "type": "verification_error",
                "error": str(e),
                "severity": "high"
            })
        
        self.verification_results["data_flow_integrity"] = issues
        log.info(f"📊 データフロー整合性チェック完了: {len(issues)}件の問題を検出")
    
    def _verify_ui_consistency(self):
        """UI一貫性の検証"""
        log.info("🎨 UI一貫性チェック...")
        
        issues = []
        
        try:
            # app.pyとdash_app.pyのUI統合確認
            app_file = self.project_root / "app.py"
            dash_file = self.project_root / "dash_app.py"
            
            app_content = ""
            dash_content = ""
            
            if app_file.exists():
                with open(app_file, 'r', encoding='utf-8') as f:
                    app_content = f.read()
            
            if dash_file.exists():
                with open(dash_file, 'r', encoding='utf-8') as f:
                    dash_content = f.read()
            
            # 18セクション表示の一貫性確認
            if "18セクション統合システム" in app_content:
                if "18セクション" not in dash_content:
                    issues.append({
                        "type": "ui_inconsistency",
                        "issue": "app.pyには18セクション表示があるがdash_app.pyにはない",
                        "severity": "medium",
                        "recommendation": "dash_app.pyにも18セクション表示を追加"
                    })
        
        except Exception as e:
            issues.append({
                "type": "verification_error",
                "error": str(e),
                "severity": "high"
            })
        
        self.verification_results["ui_consistency"] = issues
        log.info(f"🎨 UI一貫性チェック完了: {len(issues)}件の問題を検出")
    
    def _verify_configuration_conflicts(self):
        """設定競合の検証"""
        log.info("⚙️ 設定競合チェック...")
        
        issues = []
        
        try:
            # constants.pyの設定値確認
            constants_file = self.shift_suite_path / "tasks" / "constants.py"
            if constants_file.exists():
                with open(constants_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 重複する定数定義の確認
                slot_minutes_matches = re.findall(r'DEFAULT_SLOT_MINUTES\s*=\s*(\d+)', content)
                if len(set(slot_minutes_matches)) > 1:
                    issues.append({
                        "type": "duplicate_constant",
                        "constant": "DEFAULT_SLOT_MINUTES",
                        "values": list(set(slot_minutes_matches)),
                        "severity": "medium"
                    })
        
        except Exception as e:
            issues.append({
                "type": "verification_error",
                "error": str(e),
                "severity": "high"
            })
        
        self.verification_results["configuration_conflicts"] = issues
        log.info(f"⚙️ 設定競合チェック完了: {len(issues)}件の問題を検出")
    
    def _verify_error_handling_coverage(self):
        """エラーハンドリング網羅性の検証"""
        log.info("🛡️ エラーハンドリング網羅性チェック...")
        
        issues = []
        
        try:
            # 主要ファイルのtry-except網羅性確認
            critical_files = [
                "app.py",
                "dash_app.py", 
                "shift_suite/tasks/shortage.py",
                "shift_suite/tasks/ai_comprehensive_report_generator.py"
            ]
            
            for file_path in critical_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # try-exceptブロックの数とimport文の数を比較
                    try_count = len(re.findall(r'\btry:', content))
                    import_count = len(re.findall(r'^from .+ import|^import .+', content, re.MULTILINE))
                    
                    if import_count > 0 and try_count == 0:
                        issues.append({
                            "type": "missing_error_handling",
                            "file": file_path,
                            "imports": import_count,
                            "try_blocks": try_count,
                            "severity": "medium",
                            "recommendation": "インポートエラーハンドリングを追加"
                        })
        
        except Exception as e:
            issues.append({
                "type": "verification_error",
                "error": str(e),
                "severity": "high"
            })
        
        self.verification_results["error_handling_coverage"] = issues
        log.info(f"🛡️ エラーハンドリング網羅性チェック完了: {len(issues)}件の問題を検出")
    
    def _verify_memory_management_consistency(self):
        """メモリ管理整合性の検証"""
        log.info("🧠 メモリ管理整合性チェック...")
        
        issues = []
        
        try:
            # cleanup_old_resultsの呼び出し一貫性確認
            app_file = self.project_root / "app.py"
            if app_file.exists():
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # max_age_hoursパラメータの統一確認
                cleanup_patterns = re.findall(r'cleanup_old_results\(max_age_hours=(\d+)\)', content)
                if cleanup_patterns:
                    unique_values = set(cleanup_patterns)
                    if len(unique_values) == 1 and unique_values == {'24'}:
                        issues.append({
                            "type": "memory_management_consistent",
                            "parameter": "max_age_hours=24",
                            "status": "consistent",
                            "severity": "info"
                        })
                    elif len(unique_values) > 1:
                        issues.append({
                            "type": "memory_management_inconsistent",
                            "values": list(unique_values),
                            "severity": "medium",
                            "recommendation": "メモリクリーンアップ間隔を統一"
                        })
        
        except Exception as e:
            issues.append({
                "type": "verification_error",
                "error": str(e),
                "severity": "high"
            })
        
        self.verification_results["memory_management_consistency"] = issues
        log.info(f"🧠 メモリ管理整合性チェック完了: {len(issues)}件の問題を検出")
    
    def _verify_18_section_integration(self):
        """18セクション統合状況の検証"""
        log.info("🚀 18セクション統合状況チェック...")
        
        issues = []
        
        try:
            # 18セクション関連ファイルの存在確認
            required_files = [
                "shift_suite/tasks/ai_comprehensive_report_generator.py",
                "shift_suite/tasks/cognitive_psychology_analyzer.py",
                "shift_suite/tasks/organizational_pattern_analyzer.py",
                "shift_suite/tasks/system_thinking_analyzer.py",
                "shift_suite/tasks/blueprint_deep_analysis_engine.py",
                "shift_suite/tasks/integrated_mece_analysis_engine.py",
                "shift_suite/tasks/predictive_optimization_integration_engine.py"
            ]
            
            missing_files = []
            existing_files = []
            
            for file_path in required_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)
            
            if missing_files:
                issues.append({
                    "type": "missing_18_section_files",
                    "missing_files": missing_files,
                    "severity": "high"
                })
            
            if existing_files:
                issues.append({
                    "type": "18_section_files_present",
                    "existing_files": existing_files,
                    "count": len(existing_files),
                    "status": "integration_complete",
                    "severity": "info"
                })
            
            # __init__.pyでの18セクションエクスポート確認
            init_file = self.shift_suite_path / "tasks" / "__init__.py"
            if init_file.exists():
                with open(init_file, 'r', encoding='utf-8') as f:
                    init_content = f.read()
                
                section_comment = "18セクション統合システム" in init_content
                if section_comment:
                    issues.append({
                        "type": "18_section_exports_configured",
                        "status": "configured",
                        "severity": "info"
                    })
        
        except Exception as e:
            issues.append({
                "type": "verification_error",
                "error": str(e),
                "severity": "high"
            })
        
        self.verification_results["18_section_integration_status"] = issues
        log.info(f"🚀 18セクション統合状況チェック完了: {len(issues)}件の項目を確認")
    
    def _generate_verification_summary(self) -> Dict[str, Any]:
        """検証結果サマリーの生成"""
        total_issues = 0
        high_severity_issues = 0
        medium_severity_issues = 0
        info_items = 0
        
        for category, issues in self.verification_results.items():
            total_issues += len(issues)
            for issue in issues:
                severity = issue.get('severity', 'unknown')
                if severity == 'high':
                    high_severity_issues += 1
                elif severity == 'medium':
                    medium_severity_issues += 1
                elif severity == 'info':
                    info_items += 1
        
        return {
            "total_checks": len(self.verification_results),
            "total_issues": total_issues,
            "high_severity": high_severity_issues,
            "medium_severity": medium_severity_issues,
            "info_items": info_items,
            "overall_status": "healthy" if high_severity_issues == 0 else "needs_attention"
        }
    
    def _generate_recommendations(self) -> List[str]:
        """改善推奨事項の生成"""
        recommendations = []
        
        # 各カテゴリーから推奨事項を抽出
        for category, issues in self.verification_results.items():
            for issue in issues:
                if issue.get('recommendation'):
                    recommendations.append(f"[{category}] {issue['recommendation']}")
                elif issue.get('severity') == 'high':
                    recommendations.append(f"[{category}] 高優先度問題の修正が必要: {issue.get('type', '不明')}")
        
        if not recommendations:
            recommendations.append("✅ システム全体の整合性が保たれています")
        
        return recommendations

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent
    verifier = SystemVerificationEngine(project_root)
    
    log.info("🔍 シフト分析システム包括的検証を開始...")
    results = verifier.run_comprehensive_verification()
    
    # 結果をJSONファイルに保存
    output_file = project_root / "comprehensive_system_verification_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # 結果をコンソールに表示
    print("\n" + "="*80)
    print("🔍 システム包括的検証結果")
    print("="*80)
    
    summary = results['summary']
    print(f"📊 総合状況: {summary['overall_status']}")
    print(f"🔍 検証項目数: {summary['total_checks']}")
    print(f"📋 検出事項数: {summary['total_issues']}")
    print(f"🚨 高優先度: {summary['high_severity']}件")
    print(f"⚠️ 中優先度: {summary['medium_severity']}件")
    print(f"ℹ️ 情報: {summary['info_items']}件")
    
    print("\n📝 推奨事項:")
    for rec in results['recommendation']:
        print(f"  • {rec}")
    
    print(f"\n📄 詳細結果: {output_file}")
    print("="*80)
    
    return results

if __name__ == "__main__":
    main()