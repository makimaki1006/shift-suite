# -*- coding: utf-8 -*-
"""
品質管理プロセス設計
表現チェックリスト作成・客観性評価基準設定・多重レビュー体制構築
"""

import sys
sys.path.append('.')

from pathlib import Path
import json
from datetime import datetime
import re

def analyze_current_expression_issues():
    """現在の表現品質問題を分析"""
    
    print('=== 現在の表現品質問題分析 ===')
    print('分析目的: 品質管理プロセス設計のための問題特定')
    
    # 1. 既知の表現問題パターンを分類
    expression_problems = {
        "implementation_confusion": {
            "description": "実装/確認の混同",
            "problematic_patterns": [
                "完全実装", "実装済み", "実装完了",
                "新規実装", "システム実装"
            ],
            "correct_alternatives": [
                "機能確認完了", "動作確認済み", "利用可能確認",
                "既存機能確認", "システム動作確認"
            ],
            "detection_regex": r"(完全|新規|システム)?(実装)(済み|完了|中)?",
            "severity": "高"
        },
        "scope_exaggeration": {
            "description": "範囲・規模の誇張",
            "problematic_patterns": [
                "全体最適化", "システム全体", "包括的改善",
                "完全な", "大幅な", "劇的な"
            ],
            "correct_alternatives": [
                "機能修復", "限定的改善", "部分的改善",
                "対象範囲の", "段階的な", "漸進的な"
            ],
            "detection_regex": r"(全体|システム全体|包括的|完全な|大幅な|劇的な)",
            "severity": "高"
        },
        "achievement_inflation": {
            "description": "成果の過大表現",
            "problematic_patterns": [
                "大幅向上", "飛躍的改善", "革命的変化",
                "完全達成", "100%成功", "完璧な"
            ],
            "correct_alternatives": [
                "改善", "部分的向上", "段階的変化",
                "目標達成", "要件満足", "適切な"
            ],
            "detection_regex": r"(大幅|飛躍的|革命的|完全|100%|完璧な)(向上|改善|変化|達成|成功)",
            "severity": "中"
        },
        "certainty_overstatement": {
            "description": "確実性の過剰表現",
            "problematic_patterns": [
                "確実に", "間違いなく", "必ず",
                "完全に", "絶対に"
            ],
            "correct_alternatives": [
                "想定される", "期待される", "可能性が高い",
                "適切に", "十分に"
            ],
            "detection_regex": r"(確実に|間違いなく|必ず|完全に|絶対に)",
            "severity": "低"
        }
    }
    
    print('\n【表現問題分類】')
    for category, details in expression_problems.items():
        print(f'  {category}: {details["description"]} (重要度: {details["severity"]})')
        print(f'    問題パターン例: {details["problematic_patterns"][:3]}...')
        print(f'    適正表現例: {details["correct_alternatives"][:3]}...')
    
    return expression_problems

def create_expression_checklist(expression_problems):
    """表現チェックリスト作成"""
    
    print('\n=== 表現チェックリスト作成 ===')
    
    checklist = {
        "metadata": {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "purpose": "技術文書の表現品質確保",
            "scope": "全ての技術レポート・評価書・計画書"
        },
        "check_categories": {},
        "severity_levels": {
            "高": "即座修正必要",
            "中": "レビュー時修正推奨", 
            "低": "継続監視"
        },
        "approval_criteria": {
            "高重要度問題": 0,
            "中重要度問題": "2以下",
            "低重要度問題": "5以下",
            "全体スコア": "90以上"
        }
    }
    
    # 各問題カテゴリをチェック項目に変換
    for category, details in expression_problems.items():
        checklist["check_categories"][category] = {
            "name": details["description"],
            "severity": details["severity"],
            "check_points": [
                {
                    "item": f"「{pattern}」表現の使用確認",
                    "correct_example": alt,
                    "detection_method": "正規表現スキャン",
                    "regex_pattern": details["detection_regex"]
                }
                for pattern, alt in zip(details["problematic_patterns"], details["correct_alternatives"])
            ],
            "manual_check_points": [
                "文脈における表現の適切性",
                "技術的事実との整合性",
                "業界標準表現との一致性",
                "読み手への誤解可能性"
            ]
        }
    
    print('【チェックリスト構成】')
    for category, details in checklist["check_categories"].items():
        print(f'  {details["name"]} ({details["severity"]}重要度)')
        print(f'    自動チェック項目: {len(details["check_points"])}件')
        print(f'    手動チェック項目: {len(details["manual_check_points"])}件')
    
    return checklist

def design_objectivity_assessment_criteria():
    """客観性評価基準設定"""
    
    print('\n=== 客観性評価基準設定 ===')
    
    objectivity_criteria = {
        "evaluation_dimensions": {
            "factual_accuracy": {
                "name": "事実正確性",
                "weight": 0.35,
                "measurement": "技術的事実との整合率",
                "excellent": "95%以上",
                "good": "85-94%", 
                "acceptable": "75-84%",
                "poor": "75%未満"
            },
            "expression_appropriateness": {
                "name": "表現適切性", 
                "weight": 0.25,
                "measurement": "誇張表現・不適切表現の件数",
                "excellent": "0件",
                "good": "1-2件",
                "acceptable": "3-4件", 
                "poor": "5件以上"
            },
            "scope_clarity": {
                "name": "範囲明確性",
                "weight": 0.20,
                "measurement": "作業範囲・影響範囲の明記度",
                "excellent": "完全明記",
                "good": "概ね明記",
                "acceptable": "部分的明記",
                "poor": "不明確"
            },
            "verification_coverage": {
                "name": "検証網羅性",
                "weight": 0.15,
                "measurement": "主張に対する検証率",
                "excellent": "90%以上",
                "good": "70-89%",
                "acceptable": "50-69%", 
                "poor": "50%未満"
            },
            "consistency": {
                "name": "一貫性",
                "weight": 0.05,
                "measurement": "文書内表現の統一度",
                "excellent": "完全一致",
                "good": "概ね一致",
                "acceptable": "部分的一致",
                "poor": "不一致多数"
            }
        },
        "scoring_method": {
            "excellent": 4,
            "good": 3, 
            "acceptable": 2,
            "poor": 1
        },
        "grade_thresholds": {
            "A": 3.5,
            "B+": 3.0,
            "B": 2.5,
            "B-": 2.0,
            "C+": 1.5,
            "C": 1.0
        }
    }
    
    print('【評価次元】')
    for dimension, criteria in objectivity_criteria["evaluation_dimensions"].items():
        print(f'  {criteria["name"]} (重み: {criteria["weight"]})')
        print(f'    測定方法: {criteria["measurement"]}')
        print(f'    優秀基準: {criteria["excellent"]}')
    
    return objectivity_criteria

def design_multi_review_system():
    """多重レビュー体制構築"""
    
    print('\n=== 多重レビュー体制設計 ===')
    
    review_system = {
        "review_stages": {
            "stage_1_self_check": {
                "name": "自己チェック段階", 
                "responsible": "作成者",
                "duration": "30分",
                "tools": ["表現チェックリスト", "自動検出スクリプト"],
                "deliverable": "自己チェック報告書",
                "pass_criteria": "高重要度問題0件"
            },
            "stage_2_peer_review": {
                "name": "同僚レビュー段階",
                "responsible": "同僚レビュアー", 
                "duration": "60分",
                "tools": ["客観性評価基準", "レビューチェックシート"],
                "deliverable": "同僚レビュー報告書",
                "pass_criteria": "総合スコア2.5以上"
            },
            "stage_3_expert_audit": {
                "name": "専門家監査段階",
                "responsible": "技術専門家",
                "duration": "90分", 
                "tools": ["業界標準比較", "第三者評価システム"],
                "deliverable": "専門家監査報告書",
                "pass_criteria": "全評価次元B以上"
            }
        },
        "escalation_rules": {
            "minor_issues": "Stage 1で解決",
            "moderate_issues": "Stage 2で解決",
            "major_issues": "Stage 3まで実施",
            "critical_issues": "全段階実施 + 追加レビュー"
        },
        "quality_gates": [
            "Stage 1: 基本品質確保",
            "Stage 2: 客観性確認", 
            "Stage 3: 業界標準準拠"
        ]
    }
    
    print('【レビュー段階】')
    for stage_id, stage in review_system["review_stages"].items():
        print(f'  {stage["name"]}')
        print(f'    担当: {stage["responsible"]}')
        print(f'    所要時間: {stage["duration"]}')
        print(f'    合格基準: {stage["pass_criteria"]}')
    
    return review_system

def create_implementation_timeline():
    """実装タイムライン作成"""
    
    print('\n=== 実装タイムライン ===')
    
    timeline = {
        "day_1": {
            "tasks": [
                "表現チェックリスト最終化",
                "客観性評価基準文書化", 
                "レビュー体制手順書作成"
            ],
            "deliverables": [
                "expression_checklist.json",
                "objectivity_criteria.json",
                "review_system_manual.md"
            ],
            "duration": "8時間"
        },
        "day_2": {
            "tasks": [
                "自動検出スクリプト基本版作成",
                "レビューテンプレート作成",
                "試験運用計画策定"
            ],
            "deliverables": [
                "expression_detector.py",
                "review_templates/",
                "pilot_test_plan.md"  
            ],
            "duration": "8時間"
        }
    }
    
    print('【実装計画】')
    for day, plan in timeline.items():
        print(f'  {day}: {plan["duration"]}')
        for task in plan["tasks"]:
            print(f'    - {task}')
    
    return timeline

def save_quality_management_design(checklist, objectivity_criteria, review_system, timeline):
    """品質管理設計の保存"""
    
    design_package = {
        "metadata": {
            "title": "品質管理プロセス設計書",
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "purpose": "表現品質の体系的管理",
            "scope": "全技術文書"
        },
        "expression_checklist": checklist,
        "objectivity_criteria": objectivity_criteria, 
        "review_system": review_system,
        "implementation_timeline": timeline
    }
    
    # 設計書保存
    with open('quality_management_process_design.json', 'w', encoding='utf-8') as f:
        json.dump(design_package, f, indent=2, ensure_ascii=False, default=str)
    
    print('\n品質管理プロセス設計保存: quality_management_process_design.json')
    
    return design_package

if __name__ == '__main__':
    print('B1: 品質管理プロセス設計を慎重に開始...\n')
    
    # Step 1: 現在の問題分析
    expression_problems = analyze_current_expression_issues()
    
    # Step 2: 表現チェックリスト作成
    checklist = create_expression_checklist(expression_problems)
    
    # Step 3: 客観性評価基準設定
    objectivity_criteria = design_objectivity_assessment_criteria()
    
    # Step 4: 多重レビュー体制構築
    review_system = design_multi_review_system()
    
    # Step 5: 実装タイムライン作成
    timeline = create_implementation_timeline()
    
    # Step 6: 設計保存
    design_package = save_quality_management_design(
        checklist, objectivity_criteria, review_system, timeline
    )
    
    print('\n' + '='*60)
    print('B1: 品質管理プロセス設計完了')
    print('='*60)
    print(f'チェック項目数: {sum(len(cat["check_points"]) for cat in checklist["check_categories"].values())}')
    print(f'評価次元数: {len(objectivity_criteria["evaluation_dimensions"])}')
    print(f'レビュー段階数: {len(review_system["review_stages"])}')
    print('次のステップ: Day 1実装作業の開始')