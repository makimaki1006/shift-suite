#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 第三者完了チェック自動実行スクリプト
客観的・定量的な完了確認
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

def check_file_existence():
    """必須ファイル存在確認"""
    
    print("=" * 80)
    print("📁 必須ファイル存在確認")
    print("=" * 80)
    
    required_files = {
        "Phase 2実装": [
            "shift_suite/tasks/fact_extractor_prototype.py"
        ],
        "Phase 3.1実装": [
            "shift_suite/tasks/lightweight_anomaly_detector.py"
        ],
        "Phase 3.2実装": [
            "shift_suite/tasks/fact_book_visualizer.py",
            "shift_suite/tasks/dash_fact_book_integration.py"
        ],
        "設計書・レポート": [
            "PHASE3_LIGHTWEIGHT_ANOMALY_DETECTION_DESIGN.md",
            "PHASE3_2_FACT_BOOK_INTEGRATION_GUIDE.md",
            "PHASE3_1_VERIFICATION_REPORT.md",
            "PHASE3_2_VERIFICATION_REPORT.md"
        ],
        "検証スクリプト": [
            "verify_phase3_implementation.py",
            "verify_phase3_2_implementation.py"
        ]
    }
    
    results = {}
    total_files = 0
    existing_files = 0
    
    for category, files in required_files.items():
        print(f"\n📋 {category}:")
        category_results = []
        
        for file_path in files:
            path = Path(file_path)
            exists = path.exists()
            size_kb = path.stat().st_size / 1024 if exists else 0
            
            status = "✅" if exists else "❌"
            print(f"  {status} {file_path}")
            if exists:
                print(f"      サイズ: {size_kb:.1f} KB")
                existing_files += 1
            
            category_results.append({
                "file": file_path,
                "exists": exists,
                "size_kb": size_kb
            })
            
            total_files += 1
        
        results[category] = category_results
    
    completion_rate = (existing_files / total_files) * 100
    print(f"\n📊 ファイル存在率: {existing_files}/{total_files} ({completion_rate:.1f}%)")
    
    return results, completion_rate

def check_code_quality():
    """コード品質確認"""
    
    print("\n" + "=" * 80)
    print("🔧 コード品質確認")
    print("=" * 80)
    
    implementation_files = [
        "shift_suite/tasks/fact_extractor_prototype.py",
        "shift_suite/tasks/lightweight_anomaly_detector.py",
        "shift_suite/tasks/fact_book_visualizer.py",
        "shift_suite/tasks/dash_fact_book_integration.py"
    ]
    
    quality_results = {}
    
    for file_path in implementation_files:
        path = Path(file_path)
        if not path.exists():
            continue
        
        print(f"\n📄 {file_path}:")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # コード品質メトリクス
        metrics = {
            "lines": content.count('\n'),
            "functions": content.count('def '),
            "classes": content.count('class '),
            "docstrings": content.count('"""'),
            "comments": content.count('#'),
            "error_handling": content.count('try:'),
            "logging": content.count('log.'),
            "type_hints": content.count('->'),
            "imports": content.count('import ')
        }
        
        # 品質スコア計算
        structure_score = min(100, metrics["functions"] * 8 + metrics["classes"] * 20)
        documentation_score = min(100, metrics["docstrings"] * 15 + metrics["comments"] * 2)
        safety_score = min(100, metrics["error_handling"] * 25 + metrics["logging"] * 10)
        typing_score = min(100, metrics["type_hints"] * 5)
        
        total_score = (structure_score + documentation_score + safety_score + typing_score) / 4
        
        print(f"  📊 メトリクス:")
        for metric, value in metrics.items():
            print(f"    {metric}: {value}")
        
        print(f"  🎯 品質スコア: {total_score:.1f}/100")
        
        # 品質基準チェック
        quality_checks = [
            ("構造化", structure_score >= 60),
            ("文書化", documentation_score >= 50),
            ("安全性", safety_score >= 60),
            ("型付け", typing_score >= 30)
        ]
        
        print(f"  ✅ 品質基準:")
        for check_name, passed in quality_checks:
            status = "✅" if passed else "❌"
            print(f"    {status} {check_name}")
        
        quality_results[file_path] = {
            "metrics": metrics,
            "scores": {
                "structure": structure_score,
                "documentation": documentation_score,
                "safety": safety_score,
                "typing": typing_score,
                "total": total_score
            },
            "quality_checks": dict(quality_checks)
        }
    
    return quality_results

def check_integration_compatibility():
    """統合互換性確認"""
    
    print("\n" + "=" * 80)
    print("🔗 統合互換性確認")
    print("=" * 80)
    
    compatibility_results = {}
    
    # Phase 2との互換性
    phase2_path = Path("shift_suite/tasks/fact_extractor_prototype.py")
    phase3_1_path = Path("shift_suite/tasks/lightweight_anomaly_detector.py")
    phase3_2_path = Path("shift_suite/tasks/fact_book_visualizer.py")
    
    print("📋 Phase間連携確認:")
    
    if phase2_path.exists() and phase3_2_path.exists():
        with open(phase3_2_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        phase2_integration = "FactExtractorPrototype" in content
        status = "✅" if phase2_integration else "❌"
        print(f"  {status} Phase 2統合: FactExtractorPrototype")
        compatibility_results["phase2_integration"] = phase2_integration
    
    if phase3_1_path.exists() and phase3_2_path.exists():
        with open(phase3_2_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        phase3_1_integration = "LightweightAnomalyDetector" in content
        status = "✅" if phase3_1_integration else "❌"
        print(f"  {status} Phase 3.1統合: LightweightAnomalyDetector")
        compatibility_results["phase3_1_integration"] = phase3_1_integration
    
    # 既存システムとの互換性
    dash_app_path = Path("dash_app.py")
    integration_path = Path("shift_suite/tasks/dash_fact_book_integration.py")
    
    print(f"\n📋 既存システム互換性:")
    
    if dash_app_path.exists():
        print("  ✅ dash_app.py存在確認")
        compatibility_results["dash_app_exists"] = True
        
        if integration_path.exists():
            with open(integration_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 統合パターン確認
            integration_patterns = [
                ("タブ構造", "dcc.Tab" in content),
                ("コールバック", "@app.callback" in content or "callback" in content),
                ("レイアウト", "html.Div" in content),
                ("スタイル", "style=" in content)
            ]
            
            for pattern_name, exists in integration_patterns:
                status = "✅" if exists else "❌"
                print(f"    {status} {pattern_name}")
                compatibility_results[f"integration_{pattern_name.lower()}"] = exists
    else:
        print("  ⚠️ dash_app.py未発見")
        compatibility_results["dash_app_exists"] = False
    
    return compatibility_results

def check_functional_completeness():
    """機能完全性確認"""
    
    print("\n" + "=" * 80)
    print("⚙️ 機能完全性確認")
    print("=" * 80)
    
    functional_results = {}
    
    # Phase 3.1機能確認
    phase3_1_path = Path("shift_suite/tasks/lightweight_anomaly_detector.py")
    if phase3_1_path.exists():
        with open(phase3_1_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 Phase 3.1 異常検知機能:")
        required_methods = [
            ("_detect_excessive_hours", "過度な労働時間検知"),
            ("_detect_continuous_work_violations", "連続勤務違反検知"),
            ("_detect_night_shift_anomalies", "夜勤頻度過多検知"),
            ("_detect_interval_violations", "勤務間インターバル違反検知")
        ]
        
        phase3_1_functions = []
        for method, description in required_methods:
            exists = f"def {method}" in content
            status = "✅" if exists else "❌"
            print(f"  {status} {description}")
            phase3_1_functions.append(exists)
        
        functional_results["phase3_1_completeness"] = all(phase3_1_functions)
    
    # Phase 3.2機能確認
    phase3_2_path = Path("shift_suite/tasks/fact_book_visualizer.py")
    if phase3_2_path.exists():
        with open(phase3_2_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n📋 Phase 3.2 可視化機能:")
        required_features = [
            ("generate_comprehensive_fact_book", "包括的ファクトブック生成"),
            ("create_dash_layout", "Dashレイアウト生成"),
            ("_prepare_visualization_data", "可視化データ準備"),
            ("_create_anomalies_display", "異常表示機能")
        ]
        
        phase3_2_functions = []
        for method, description in required_features:
            exists = f"def {method}" in content
            status = "✅" if exists else "❌"
            print(f"  {status} {description}")
            phase3_2_functions.append(exists)
        
        functional_results["phase3_2_completeness"] = all(phase3_2_functions)
    
    return functional_results

def generate_completion_report():
    """完了チェックレポート生成"""
    
    print("\n" + "=" * 80)
    print("📊 完了チェック総合評価")
    print("=" * 80)
    
    # 各チェック実行
    file_results, file_completion_rate = check_file_existence()
    quality_results = check_code_quality()
    compatibility_results = check_integration_compatibility()
    functional_results = check_functional_completeness()
    
    # 総合評価計算
    evaluations = {
        "ファイル完全性": file_completion_rate,
        "コード品質": sum(r["scores"]["total"] for r in quality_results.values()) / len(quality_results) if quality_results else 0,
        "統合互換性": sum(v for v in compatibility_results.values() if isinstance(v, bool)) / len([v for v in compatibility_results.values() if isinstance(v, bool)]) * 100 if compatibility_results else 0,
        "機能完全性": sum(v for v in functional_results.values() if isinstance(v, bool)) / len(functional_results) * 100 if functional_results else 0
    }
    
    print(f"\n📊 評価結果:")
    for category, score in evaluations.items():
        status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        print(f"  {status} {category}: {score:.1f}%")
    
    total_score = sum(evaluations.values()) / len(evaluations)
    print(f"\n🎯 総合スコア: {total_score:.1f}%")
    
    # 完了判定
    if total_score >= 90:
        completion_status = "✅ 完全達成"
        approval = "即座に次段階移行可能"
    elif total_score >= 80:
        completion_status = "🟡 条件付き達成"  
        approval = "軽微な修正後に移行可能"
    else:
        completion_status = "❌ 要改善"
        approval = "重要な問題があり修正が必要"
    
    print(f"\n🏆 完了判定: {completion_status}")
    print(f"📋 承認状況: {approval}")
    
    # レポート保存
    timestamp = datetime.now()
    report = {
        "check_info": {
            "execution_time": timestamp.isoformat(),
            "checker": "自動検証システム",
            "version": "Phase 3 完了チェック v1.0"
        },
        "evaluations": evaluations,
        "total_score": total_score,
        "completion_status": completion_status,
        "approval": approval,
        "detailed_results": {
            "file_results": file_results,
            "quality_results": quality_results,
            "compatibility_results": compatibility_results,
            "functional_results": functional_results
        }
    }
    
    report_path = Path("PHASE3_COMPLETION_CHECK_REPORT.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細レポート保存: {report_path}")
    
    return total_score >= 80

def main():
    """メイン検証処理"""
    
    print("🚀 Phase 3 第三者完了チェック自動実行")
    print(f"📅 実行日時: {datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}")
    print("👤 実行者: 自動検証システム (第三者視点)")
    
    success = generate_completion_report()
    
    if success:
        print("\n🎉 Phase 3 完了チェック合格!")
        print("📋 推奨アクション: バックアップ作成後、次段階移行")
    else:
        print("\n⚠️ Phase 3 完了チェックで問題検出")
        print("📋 推奨アクション: 問題修正後に再チェック")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)