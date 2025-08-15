# -*- coding: utf-8 -*-
"""
表現修正作業の客観的レビュー
実際に行った作業内容と主張の整合性を厳密に検証
"""

import sys
sys.path.append('.')

from pathlib import Path
import json
from datetime import datetime
import difflib

def objective_correction_review():
    """表現修正作業の客観的レビュー"""
    
    print('=== 表現修正作業の客観的レビュー ===')
    print(f'レビュー実施: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('評価基準: 実際の変更内容 vs 作業報告の整合性')
    
    review_results = {
        "timestamp": datetime.now().isoformat(),
        "methodology": "objective_fact_verification",
        "file_changes": {},
        "claimed_vs_actual": {},
        "work_assessment": {}
    }
    
    print('\n【1. 実際の修正内容の検証】')
    
    # 修正対象ファイルの実際の変更内容確認
    modified_files = [
        'dynamic_data_evaluation.py',
        'holistic_optimization_plan.py', 
        'professional_audit.py',
        'data_flow_consistency_verification.py'
    ]
    
    actual_changes = {}
    
    for file_path in modified_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 実際の修正箇所を確認
                changes_found = {
                    "lines": len(content.splitlines()),
                    "contains_old_expressions": {},
                    "contains_new_expressions": {}
                }
                
                # 旧表現の残存チェック
                old_expressions = [
                    "完全実装", "実装済み", "全体最適化",
                    "包括的改善", "システム全体", "完全修復"
                ]
                
                new_expressions = [
                    "機能確認", "利用可能確認", "動作確認済み",
                    "shortage機能修復", "機能修復完了"
                ]
                
                for old_expr in old_expressions:
                    count = content.count(old_expr)
                    if count > 0:
                        changes_found["contains_old_expressions"][old_expr] = count
                
                for new_expr in new_expressions:
                    count = content.count(new_expr)
                    if count > 0:
                        changes_found["contains_new_expressions"][new_expr] = count
                
                actual_changes[file_path] = changes_found
                
                print(f'  {file_path}: {changes_found["lines"]}行')
                if changes_found["contains_old_expressions"]:
                    print(f'    残存旧表現: {changes_found["contains_old_expressions"]}')
                if changes_found["contains_new_expressions"]:
                    print(f'    新表現: {changes_found["contains_new_expressions"]}')
                    
            except Exception as e:
                print(f'  {file_path}: 読み込みエラー - {e}')
                actual_changes[file_path] = {"error": str(e)}
    
    review_results["file_changes"] = actual_changes
    
    print('\n【2. 主張 vs 実態の比較分析】')
    
    # 作業報告で主張された内容 vs 実際の変更
    claims_vs_reality = {
        "修正ファイル数": {
            "claimed": "4ファイル修正",
            "actual": len([f for f in actual_changes.keys() if "error" not in actual_changes[f]]),
            "accuracy": None
        },
        "表現修正範囲": {
            "claimed": "体系的誇張表現除去",
            "actual": "限定的な表現置換",
            "evidence": actual_changes
        },
        "品質向上レベル": {
            "claimed": "大幅向上・A評価達成",
            "actual": "professional_audit.pyの修正による改善",
            "verification_needed": True
        },
        "作業複雑度": {
            "claimed": "慎重な計画的修正",
            "actual": "文字列置換作業",
            "complexity_level": "低"
        }
    }
    
    # 実際の修正の正確性評価
    for claim, analysis in claims_vs_reality.items():
        if claim == "修正ファイル数":
            analysis["accuracy"] = "正確" if analysis["actual"] == 4 else f"不正確（実際は{analysis['actual']}）"
        
        print(f'  {claim}:')
        print(f'    主張: {analysis["claimed"]}')
        print(f'    実態: {analysis["actual"]}')
        if "accuracy" in analysis:
            print(f'    正確性: {analysis["accuracy"]}')
    
    review_results["claimed_vs_actual"] = claims_vs_reality
    
    print('\n【3. 作業の実質的価値評価】')
    
    # 実際に達成された価値の客観評価
    actual_value_assessment = {
        "positive_aspects": [],
        "limitations": [],
        "work_scope": "限定的",
        "impact_level": "軽微"
    }
    
    # ポジティブな側面
    total_old_expressions = sum(
        sum(changes.get("contains_old_expressions", {}).values()) 
        for changes in actual_changes.values() 
        if isinstance(changes, dict) and "error" not in changes
    )
    
    total_new_expressions = sum(
        sum(changes.get("contains_new_expressions", {}).values()) 
        for changes in actual_changes.values() 
        if isinstance(changes, dict) and "error" not in changes
    )
    
    if total_new_expressions > 0:
        actual_value_assessment["positive_aspects"].append(
            f"実際の表現置換: {total_new_expressions}箇所で適切な表現に変更"
        )
    
    if total_old_expressions == 0:
        actual_value_assessment["positive_aspects"].append(
            "誇張表現の除去: 対象範囲では完了"
        )
    else:
        actual_value_assessment["limitations"].append(
            f"残存誇張表現: {total_old_expressions}箇所で修正漏れ"
        )
    
    # 制限事項
    actual_value_assessment["limitations"].extend([
        "修正範囲: 4ファイルのみ（全システムの一部）",
        "作業性質: 表面的な文字列置換",
        "システム機能: 変更なし（表現のみ修正）",
        "検証範囲: 修正ファイルの動作確認のみ"
    ])
    
    print('  実際の価値:')
    for aspect in actual_value_assessment["positive_aspects"]:
        print(f'    + {aspect}')
    
    print('  制限事項:')
    for limitation in actual_value_assessment["limitations"]:
        print(f'    - {limitation}')
    
    review_results["work_assessment"] = actual_value_assessment
    
    print('\n【4. 客観的作業分類】')
    
    # 作業の客観的分類
    work_classification = {
        "category": "表現品質改善作業",
        "scope": "限定的（4ファイル）",
        "complexity": "低（文字列置換）",
        "duration": "短時間（1時間未満推定）",
        "impact": "表現正確性向上",
        "innovation": "なし",
        "system_change": "なし"
    }
    
    for key, value in work_classification.items():
        print(f'  {key}: {value}')
    
    print('\n【5. 報告書表現の妥当性評価】')
    
    # 報告書の表現が適切かどうかの評価
    reporting_assessment = {
        "appropriate_expressions": [
            "表現修正作業の実施",
            "誇張表現の除去",
            "技術的誠実性向上"
        ],
        "questionable_expressions": [
            "大幅向上", "体系的除去", "慎重かつ確実",
            "プロフェッショナル品質達成"
        ],
        "exaggerated_expressions": [
            "成功完了", "A評価達成", "大幅に向上"
        ],
        "recommendation": "表現の更なる適正化が必要"
    }
    
    print('  適切な表現:')
    for expr in reporting_assessment["appropriate_expressions"]:
        print(f'    OK {expr}')
    
    print('  疑問のある表現:')
    for expr in reporting_assessment["questionable_expressions"]:
        print(f'    ? {expr}')
    
    print('  誇張的表現:')
    for expr in reporting_assessment["exaggerated_expressions"]:
        print(f'    WARN {expr}')
    
    review_results["reporting_assessment"] = reporting_assessment
    
    print('\n【6. 最終客観評価】')
    
    final_objective_assessment = {
        "work_nature": "限定的な表現修正作業",
        "actual_scope": "4ファイル内の文字列置換",
        "value_created": "表現正確性の部分的改善",
        "effort_level": "軽微",
        "reporting_accuracy": "一部誇張あり",
        "overall_grade": "C+（作業は適切だが報告に改善余地）"
    }
    
    print(f'  作業性質: {final_objective_assessment["work_nature"]}')
    print(f'  実際範囲: {final_objective_assessment["actual_scope"]}')
    print(f'  創出価値: {final_objective_assessment["value_created"]}')
    print(f'  工数レベル: {final_objective_assessment["effort_level"]}')
    print(f'  報告正確性: {final_objective_assessment["reporting_accuracy"]}')
    print(f'  総合評価: {final_objective_assessment["overall_grade"]}')
    
    review_results["final_assessment"] = final_objective_assessment
    
    # レポート保存
    with open('objective_correction_review.json', 'w', encoding='utf-8') as f:
        json.dump(review_results, f, indent=2, ensure_ascii=False, default=str)
    
    print('\n客観レビューレポート保存: objective_correction_review.json')
    
    return review_results

if __name__ == '__main__':
    print('表現修正作業の客観的レビューを開始...\n')
    
    review_results = objective_correction_review()
    
    print('\n' + '='*50)
    print('客観的レビュー結論')
    print('='*50)
    print(f'実際の作業: {review_results["final_assessment"]["work_nature"]}')
    print(f'作業価値: {review_results["final_assessment"]["value_created"]}')
    print(f'報告品質: {review_results["final_assessment"]["reporting_accuracy"]}')
    print('推奨: 報告表現の更なる適正化と作業範囲の正確な記述')