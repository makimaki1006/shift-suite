#!/usr/bin/env python3
"""
品質分析実行スクリプト

現在のMECEシステムの品質を詳細に分析し、改善計画を作成
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
import sys
import os

# モジュールパスの追加
sys.path.append('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析')

from advanced_quality_analyzer import AdvancedQualityAnalyzer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def create_sample_mece_results():
    """サンプルMECE結果の作成（分析用）"""
    log.info("サンプルMECE結果作成中...")
    
    # 軸1: 改善済み（カテゴリー補完済み）
    axis1_results = {
        'human_readable': {
            'MECE分解事実': {
                '勤務体制制約': [
                    {'制約': '日勤は8:00-17:00で設定', '確信度': 0.9}
                ],
                '設備制約': [
                    {'制約': '看護ステーション常時1名配置', '確信度': 0.8}
                ],
                '業務範囲制約': [
                    {'制約': '看護師のみ医療行為可能', '確信度': 1.0}
                ],
                '施設特性制約': [],  # 空カテゴリー
                'エリア制約': [
                    {'制約': '東館・西館同時配置必須', '確信度': 0.7}
                ]
            }
        },
        'machine_readable': {
            'hard_constraints': [
                {
                    'type': 'time_constraint',
                    'rule': '日勤時間は8:00から17:00まで',
                    'confidence': 0.9,
                    'actionability_score': 0.85,
                    'execution_rule': {
                        'condition': '日勤シフトが設定される場合',
                        'action': '8:00-17:00の時間帯に配置する'
                    },
                    'quantified_criteria': {
                        'minimum_value': 8,
                        'maximum_value': 17
                    }
                }
            ],
            'soft_constraints': [
                {
                    'type': 'staffing_constraint',
                    'rule': '看護ステーションに常時1名配置',
                    'confidence': 0.8,
                    'actionability_score': 0.7
                }
            ]
        },
        'extraction_metadata': {
            'extraction_timestamp': datetime.now().isoformat(),
            'data_quality': {'total_records': 1000}
        }
    }
    
    # 軸2: 部分的改善
    axis2_results = {
        'human_readable': {
            'MECE分解事実': {
                '個人勤務パターン': [
                    {'制約': 'ベテラン職員は夜勤多め', '確信度': 0.6}
                ],
                'スキル・配置': [],  # 空カテゴリー
                '時間選好': [
                    {'制約': 'パート職員は短時間勤務', '確信度': 0.5}
                ]
            }
        },
        'machine_readable': {
            'hard_constraints': [],
            'soft_constraints': [
                {
                    'type': 'preference_constraint',
                    'rule': 'ベテラン職員は夜勤を優先的に配置',
                    'confidence': 0.6
                    # actionability_score なし（改善前）
                }
            ]
        },
        'extraction_metadata': {
            'extraction_timestamp': datetime.now().isoformat(),
            'data_quality': {'total_records': 800}
        }
    }
    
    # 軸3: 改善前の状態
    axis3_results = {
        'human_readable': {
            'MECE分解事実': {
                '祝日・特別日': [
                    {'制約': '祝日は人員減少', '確信度': 0.4}
                ]
                # 他のカテゴリーが不足
            }
        },
        'machine_readable': {
            'hard_constraints': [
                {
                    'type': 'holiday_constraint',
                    'rule': '祝日は通常より少ない人員で運用',
                    'confidence': 0.4
                    # 具体性・実行可能性に欠ける
                }
            ]
        },
        'extraction_metadata': {
            'extraction_timestamp': datetime.now().isoformat(),
            'data_quality': {'total_records': 500}
        }
    }
    
    return {
        1: axis1_results,
        2: axis2_results,
        3: axis3_results
    }


def run_comprehensive_quality_analysis():
    """包括的品質分析の実行"""
    log.info("🎯 包括的品質分析開始")
    log.info("=" * 60)
    
    # サンプルデータで分析
    mece_results = create_sample_mece_results()
    
    # 品質分析実行
    analyzer = AdvancedQualityAnalyzer()
    analysis = analyzer.analyze_comprehensive_quality(mece_results)
    
    # 結果表示
    display_analysis_results(analysis)
    
    # 結果保存
    save_analysis_results(analysis)
    
    return analysis


def display_analysis_results(analysis: dict):
    """分析結果の表示"""
    log.info("\n" + "=" * 60)
    log.info("📊 品質分析結果")
    log.info("=" * 60)
    
    # 総合スコア
    overall_score = analysis['overall_score']
    log.info(f"🎯 総合品質スコア: {overall_score:.1%}")
    
    # 各次元のスコア
    log.info("\n📈 品質次元別スコア:")
    scores = analysis['dimension_scores']
    for dimension, score in scores.items():
        emoji = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
        log.info(f"  {emoji} {dimension}: {score:.1%}")
    
    # 重要課題
    log.info("\n🚨 重要課題:")
    for issue in analysis['critical_issues']:
        log.info(f"  ❗ {issue['dimension']}: {issue['current_score']:.1%} ({issue['severity']})")
        log.info(f"     影響: {issue['impact']}")
        for problem in issue['specific_problems']:
            log.info(f"     - {problem}")
    
    # 改善機会
    log.info("\n💡 改善機会:")
    for opportunity in analysis['improvement_opportunities']:
        log.info(f"  🔧 {opportunity['dimension']}: {opportunity['current_score']:.1%} → {opportunity['target_score']:.1%}")
        log.info(f"     作業量: {opportunity['effort_level']}")
        for quick_win in opportunity['quick_wins']:
            log.info(f"     ✅ {quick_win}")
    
    # 推奨事項
    log.info("\n📋 実行可能な推奨事項:")
    for i, rec in enumerate(analysis['actionable_recommendations'], 1):
        log.info(f"  {i}. [{rec['priority'].upper()}] {rec['action']}")
        log.info(f"     作業量: {rec['estimated_effort']}, 期待改善: +{rec['expected_improvement']:.1%}")


def save_analysis_results(analysis: dict):
    """分析結果の保存"""
    
    # 詳細結果をJSONで保存
    with open('quality_analysis_detailed.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    
    # サマリーレポートを作成
    summary_report = create_summary_report(analysis)
    
    with open('quality_analysis_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2, default=str)
    
    log.info("\n💾 分析結果を保存しました:")
    log.info("  📄 quality_analysis_detailed.json - 詳細分析結果")
    log.info("  📄 quality_analysis_summary.json - サマリーレポート")


def create_summary_report(analysis: dict) -> dict:
    """サマリーレポートの作成"""
    
    scores = analysis['dimension_scores']
    
    # 優先度付き改善計画
    improvement_plan = []
    
    # 重要課題への対応（高優先度）
    for issue in analysis['critical_issues']:
        improvement_plan.append({
            'priority': 1,
            'category': '重要課題修正',
            'dimension': issue['dimension'],
            'current_score': issue['current_score'],
            'target_score': issue['current_score'] + 0.3,
            'actions': issue['specific_problems'],
            'estimated_days': 3
        })
    
    # 改善機会への対応（中優先度）
    for opportunity in analysis['improvement_opportunities']:
        improvement_plan.append({
            'priority': 2,
            'category': '改善機会活用',
            'dimension': opportunity['dimension'],
            'current_score': opportunity['current_score'],
            'target_score': opportunity['target_score'],
            'actions': opportunity['quick_wins'],
            'estimated_days': 2
        })
    
    summary = {
        'analysis_timestamp': datetime.now().isoformat(),
        'overall_assessment': {
            'current_score': analysis['overall_score'],
            'grade': _score_to_grade(analysis['overall_score']),
            'status': _determine_status(analysis['overall_score']),
            'improvement_potential': _calculate_improvement_potential(scores)
        },
        'dimension_breakdown': {
            'strongest': max(scores.items(), key=lambda x: x[1]),
            'weakest': min(scores.items(), key=lambda x: x[1]),
            'most_critical': _find_most_critical(analysis['critical_issues']),
            'quick_wins_available': len([op for op in analysis['improvement_opportunities'] if op['effort_level'] == 'low'])
        },
        'improvement_plan': sorted(improvement_plan, key=lambda x: x['priority']),
        'next_steps': {
            'immediate': _get_immediate_actions(analysis),
            'short_term': _get_short_term_actions(analysis),
            'long_term': _get_long_term_actions(analysis)
        },
        'success_metrics': {
            'target_overall_score': min(0.9, analysis['overall_score'] + 0.15),
            'target_completion_days': sum(item['estimated_days'] for item in improvement_plan),
            'expected_roi': 'High - 品質向上による実用性の大幅改善'
        }
    }
    
    return summary


def _score_to_grade(score: float) -> str:
    """スコアから等級への変換"""
    if score >= 0.9:
        return 'A+'
    elif score >= 0.8:
        return 'A'
    elif score >= 0.7:
        return 'B+'
    elif score >= 0.6:
        return 'B'
    elif score >= 0.5:
        return 'C+'
    else:
        return 'C'


def _determine_status(score: float) -> str:
    """ステータス判定"""
    if score >= 0.8:
        return 'Ready for Production'
    elif score >= 0.7:
        return 'Good Quality - Minor Improvements Needed'
    elif score >= 0.6:
        return 'Acceptable - Improvements Required'
    else:
        return 'Needs Significant Improvement'


def _calculate_improvement_potential(scores: dict) -> float:
    """改善ポテンシャルの計算"""
    max_possible_score = 0.9  # 現実的な最大スコア
    current_average = np.mean(list(scores.values()))
    return max_possible_score - current_average


def _find_most_critical(critical_issues: list) -> str:
    """最重要課題の特定"""
    if not critical_issues:
        return 'None'
    
    most_critical = min(critical_issues, key=lambda x: x['current_score'])
    return most_critical['dimension']


def _get_immediate_actions(analysis: dict) -> list:
    """即座に実行すべきアクション"""
    actions = []
    
    for issue in analysis['critical_issues']:
        if issue['severity'] == 'critical':
            actions.append(f"{issue['dimension']}の緊急修正")
    
    return actions[:3]  # 最大3つ


def _get_short_term_actions(analysis: dict) -> list:
    """短期アクション（1-2週間）"""
    actions = []
    
    for opportunity in analysis['improvement_opportunities']:
        if opportunity['effort_level'] == 'low':
            actions.extend(opportunity['quick_wins'])
    
    return actions[:5]  # 最大5つ


def _get_long_term_actions(analysis: dict) -> list:
    """長期アクション（1ヶ月以上）"""
    return [
        "全軸の完全実装",
        "高度な検証システム構築",
        "ユーザビリティテスト実施",
        "パフォーマンス最適化",
        "本格運用環境構築"
    ]


def main():
    """メイン実行"""
    try:
        analysis = run_comprehensive_quality_analysis()
        
        log.info("\n🎉 品質分析完了!")
        log.info("次のステップ: 分析結果に基づく改善実施")
        
        return analysis
        
    except Exception as e:
        log.error(f"品質分析エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()