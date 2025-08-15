# -*- coding: utf-8 -*-
"""
shortage機能修復計画策定
データフロー断絶問題の解決とシステム一貫性の確保
"""

import sys
sys.path.append('.')

from pathlib import Path
import json
from datetime import datetime

def analyze_current_issues():
    """現在の問題点を分析"""
    
    issues = {
        "critical": [],  # 重要な問題
        "major": [],     # 主要な問題
        "minor": []      # 軽微な問題
    }
    
    print('=== 現状問題分析 ===')
    
    # 1. データフロー断絶の確認
    print('\n【データフロー断絶確認】')
    scenarios = ['out_p25_based', 'out_mean_based', 'out_median_based']
    
    shortage_files_missing = []
    for scenario in scenarios:
        shortage_time_path = Path(f'extracted_results/{scenario}/shortage_time.parquet')
        if not shortage_time_path.exists():
            shortage_files_missing.append(scenario)
    
    if shortage_files_missing:
        issues["critical"].append({
            "issue": "shortage系ファイル未生成",
            "scenarios": shortage_files_missing,
            "impact": "分析→加工フロー断絶",
            "root_cause": "shortage.py実行プロセス不整合"
        })
        print(f'CRITICAL: shortage系ファイル未生成 ({len(shortage_files_missing)}シナリオ)')
    
    # 2. 動的パラメータ不整合確認
    print('\n【動的パラメータ不整合確認】')
    
    # constants.pyとutils.pyの整合性確認
    try:
        from shift_suite.tasks.constants import DEFAULT_SLOT_MINUTES, SLOT_HOURS
        from shift_suite.tasks.utils import apply_rest_exclusion_filter
        
        # スロット時間の一貫性確認
        if DEFAULT_SLOT_MINUTES == 30 and SLOT_HOURS == 0.5:
            print('OK: スロット時間設定一貫性')
        else:
            issues["major"].append({
                "issue": "スロット時間設定不整合",
                "details": f"DEFAULT_SLOT_MINUTES={DEFAULT_SLOT_MINUTES}, SLOT_HOURS={SLOT_HOURS}",
                "expected": "30分=0.5時間"
            })
            print('MAJOR: スロット時間設定不整合')
            
    except ImportError as e:
        issues["critical"].append({
            "issue": "コア モジュール インポートエラー",
            "error": str(e)
        })
        print(f'CRITICAL: モジュールインポートエラー {e}')
    
    # 3. 処理効率性問題確認
    print('\n【処理効率性問題確認】')
    
    # 重複処理の確認
    duplicate_processes = []
    
    # ヒートマップファイルの重複確認
    for scenario in scenarios:
        scenario_path = Path(f'extracted_results/{scenario}')
        if scenario_path.exists():
            parquet_files = list(scenario_path.glob('heat_*.parquet'))
            xlsx_files = list(scenario_path.glob('heat_*.xlsx'))
            
            # 同一データの重複保存確認
            if len(parquet_files) == len(xlsx_files) and len(parquet_files) > 10:
                duplicate_processes.append(f'{scenario}: parquet+xlsx重複保存')
    
    if duplicate_processes:
        issues["minor"].append({
            "issue": "ファイル重複保存による効率低下",
            "details": duplicate_processes
        })
        print(f'MINOR: ファイル重複保存 ({len(duplicate_processes)}件)')
    
    # 4. UI統合不整合確認
    print('\n【UI統合不整合確認】')
    
    app_py_exists = Path('app.py').exists()
    dash_app_py_exists = Path('dash_app.py').exists()
    
    if app_py_exists and dash_app_py_exists:
        # 両方存在する場合の機能重複確認
        issues["minor"].append({
            "issue": "UI重複実装による保守コスト増",
            "details": "app.py と dash_app.py の並行保守"
        })
        print('MINOR: UI重複実装')
    elif not (app_py_exists or dash_app_py_exists):
        issues["critical"].append({
            "issue": "UIアプリケーション未存在"
        })
        print('CRITICAL: UIアプリケーション未存在')
    
    return issues

def create_optimization_strategy(issues):
    """最適化戦略の作成"""
    
    print('\n=== shortage機能修復戦略 ===')
    
    strategy = {
        "objectives": [
            "データフロー完全一貫性の実現",
            "動的データ対応の全面強化", 
            "処理効率の最大化",
            "保守性の向上"
        ],
        "phases": [],
        "timeline": "即座実行",
        "success_criteria": []
    }
    
    # Phase 1: Critical問題の即座対応
    if issues["critical"]:
        phase1_actions = []
        for critical_issue in issues["critical"]:
            if "shortage系ファイル未生成" in critical_issue["issue"]:
                phase1_actions.extend([
                    "shortage.py実行プロセス修復",
                    "shortage_time.parquet生成機能統合",
                    "分析→加工フロー完全接続"
                ])
            elif "モジュールインポートエラー" in critical_issue["issue"]:
                phase1_actions.append("依存関係修復とモジュール再構築")
            elif "UIアプリケーション未存在" in critical_issue["issue"]:
                phase1_actions.append("UI統合アプリケーション復旧")
        
        strategy["phases"].append({
            "phase": 1,
            "name": "Critical問題即座対応",
            "actions": list(set(phase1_actions)),
            "priority": "最高",
            "estimated_time": "即座"
        })
    
    # Phase 2: Major問題の体系的解決
    if issues["major"]:
        phase2_actions = []
        for major_issue in issues["major"]:
            if "スロット時間設定不整合" in major_issue["issue"]:
                phase2_actions.extend([
                    "constants.py統一パラメータ強化",
                    "全モジュール間パラメータ一貫性確保",
                    "動的設定検証機能追加"
                ])
        
        strategy["phases"].append({
            "phase": 2, 
            "name": "動的対応全面強化",
            "actions": list(set(phase2_actions)),
            "priority": "高",
            "estimated_time": "段階的実行"
        })
    
    # Phase 3: Minor問題の効率最適化
    if issues["minor"]:
        phase3_actions = []
        for minor_issue in issues["minor"]:
            if "重複保存" in minor_issue["issue"]:
                phase3_actions.extend([
                    "ファイル出力戦略最適化",
                    "parquet優先・xlsx選択的生成",
                    "ストレージ効率向上"
                ])
            elif "UI重複実装" in minor_issue["issue"]:
                phase3_actions.extend([
                    "UI統合戦略策定",
                    "dash_app.py主体・app.py補完体制",
                    "保守コスト削減"
                ])
        
        strategy["phases"].append({
            "phase": 3,
            "name": "効率最適化・保守性向上", 
            "actions": list(set(phase3_actions)),
            "priority": "中",
            "estimated_time": "継続改善"
        })
    
    # 成功基準の設定
    strategy["success_criteria"] = [
        "データフロー一貫性: 100%達成",
        "shortage系ファイル: 全シナリオ生成確認",
        "動的パラメータ: 全モジュール統一",
        "処理効率: ファイル重複削減",
        "UI統合: 単一アクセスポイント確立"
    ]
    
    return strategy

def prioritize_actions(strategy):
    """アクション優先順位付け"""
    
    print('\n=== 実行優先順位 ===')
    
    all_actions = []
    for phase in strategy["phases"]:
        for action in phase["actions"]:
            all_actions.append({
                "action": action,
                "phase": phase["phase"],
                "priority": phase["priority"],
                "category": phase["name"]
            })
    
    # 優先度別ソート
    priority_order = {"最高": 1, "高": 2, "中": 3}
    sorted_actions = sorted(all_actions, key=lambda x: (priority_order[x["priority"]], x["phase"]))
    
    print('\n【実行順序】')
    for i, action in enumerate(sorted_actions, 1):
        print(f'{i:2d}. [{action["priority"]}] {action["action"]}')
        print(f'     Category: {action["category"]}')
    
    return sorted_actions

def generate_implementation_roadmap():
    """実装ロードマップ生成"""
    
    print('\n=== 実装ロードマップ生成 ===')
    
    # 問題分析実行
    issues = analyze_current_issues()
    
    # 戦略策定
    strategy = create_optimization_strategy(issues)
    
    # 優先順位付け
    prioritized_actions = prioritize_actions(strategy)
    
    # ロードマップ出力
    roadmap = {
        "generated_at": datetime.now().isoformat(),
        "analysis_summary": {
            "critical_issues": len(issues["critical"]),
            "major_issues": len(issues["major"]),
            "minor_issues": len(issues["minor"])
        },
        "strategy": strategy,
        "prioritized_actions": prioritized_actions,
        "next_immediate_actions": prioritized_actions[:3] if prioritized_actions else []
    }
    
    # JSON形式で保存
    roadmap_file = Path("holistic_optimization_roadmap.json")
    with open(roadmap_file, 'w', encoding='utf-8') as f:
        json.dump(roadmap, f, indent=2, ensure_ascii=False)
    
    print(f'\n実装ロードマップ保存完了: {roadmap_file}')
    
    # 即座実行項目の表示
    if roadmap["next_immediate_actions"]:
        print('\n【即座実行項目】')
        for i, action in enumerate(roadmap["next_immediate_actions"], 1):
            print(f'{i}. {action["action"]}')
    
    return roadmap

if __name__ == '__main__':
    roadmap = generate_implementation_roadmap()
    print(f'\nshortage機能修復計画策定完了')
    print(f'Critical問題: {roadmap["analysis_summary"]["critical_issues"]}件')
    print(f'Major問題: {roadmap["analysis_summary"]["major_issues"]}件') 
    print(f'Minor問題: {roadmap["analysis_summary"]["minor_issues"]}件')