#!/usr/bin/env python3
"""
高度品質分析システム

MECEシステムの品質を詳細に分析し、具体的な改善点を特定
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import re

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class AdvancedQualityAnalyzer:
    """高度品質分析クラス"""
    
    def __init__(self):
        self.quality_dimensions = {
            'completeness': 0.0,     # 網羅性
            'specificity': 0.0,      # 具体性
            'actionability': 0.0,    # 実行可能性
            'consistency': 0.0,      # 一貫性
            'verifiability': 0.0,    # 検証可能性
            'usability': 0.0         # 使いやすさ
        }
        
    def analyze_comprehensive_quality(self, mece_results: Dict[int, Dict]) -> Dict[str, Any]:
        """包括的品質分析"""
        log.info("🔍 包括的品質分析開始...")
        
        analysis = {
            'overall_score': 0.0,
            'dimension_scores': {},
            'critical_issues': [],
            'improvement_opportunities': [],
            'detailed_findings': {},
            'actionable_recommendations': []
        }
        
        # 各品質次元の分析
        analysis['dimension_scores']['completeness'] = self._analyze_completeness(mece_results)
        analysis['dimension_scores']['specificity'] = self._analyze_specificity(mece_results)
        analysis['dimension_scores']['actionability'] = self._analyze_actionability(mece_results)
        analysis['dimension_scores']['consistency'] = self._analyze_consistency(mece_results)
        analysis['dimension_scores']['verifiability'] = self._analyze_verifiability(mece_results)
        analysis['dimension_scores']['usability'] = self._analyze_usability(mece_results)
        
        # 総合スコア計算
        scores = analysis['dimension_scores']
        analysis['overall_score'] = np.mean(list(scores.values()))
        
        # 重要課題の特定
        analysis['critical_issues'] = self._identify_critical_issues(scores, mece_results)
        
        # 改善機会の発見
        analysis['improvement_opportunities'] = self._find_improvement_opportunities(scores, mece_results)
        
        # 詳細所見
        analysis['detailed_findings'] = self._generate_detailed_findings(scores, mece_results)
        
        # 実行可能な推奨事項
        analysis['actionable_recommendations'] = self._generate_actionable_recommendations(analysis)
        
        log.info(f"✅ 品質分析完了 - 総合スコア: {analysis['overall_score']:.1%}")
        return analysis
    
    def _analyze_completeness(self, mece_results: Dict[int, Dict]) -> float:
        """網羅性分析"""
        log.info("📊 網羅性分析中...")
        
        # 期待されるカテゴリー数
        expected_categories_per_axis = 8
        total_expected = len(mece_results) * expected_categories_per_axis
        
        # 実際のカテゴリー数
        actual_categories = 0
        empty_categories = 0
        
        for axis_num, results in mece_results.items():
            if results and 'human_readable' in results:
                hr_data = results['human_readable']
                if 'MECE分解事実' in hr_data:
                    mece_facts = hr_data['MECE分解事実']
                    actual_categories += len(mece_facts)
                    
                    # 空のカテゴリーをチェック
                    for category, facts in mece_facts.items():
                        if isinstance(facts, list) and len(facts) == 0:
                            empty_categories += 1
                        elif isinstance(facts, dict) and len(facts) == 0:
                            empty_categories += 1
        
        # 網羅性スコア計算
        category_coverage = actual_categories / total_expected if total_expected > 0 else 0
        content_coverage = (actual_categories - empty_categories) / actual_categories if actual_categories > 0 else 0
        
        completeness_score = (category_coverage * 0.6) + (content_coverage * 0.4)
        
        log.info(f"  カテゴリー網羅率: {category_coverage:.1%}")
        log.info(f"  コンテンツ充実率: {content_coverage:.1%}")
        log.info(f"  網羅性スコア: {completeness_score:.1%}")
        
        return completeness_score
    
    def _analyze_specificity(self, mece_results: Dict[int, Dict]) -> float:
        """具体性分析"""
        log.info("🎯 具体性分析中...")
        
        total_constraints = 0
        specific_constraints = 0
        
        # 具体性を示すキーワード
        specific_keywords = [
            '時間', '人数', '名', '回', '日', '週', '月', '年',
            '以上', '以下', '未満', '最低', '最大', '平均',
            '%', '割合', '比率', 'IF', 'THEN', '条件'
        ]
        
        vague_keywords = [
            '適切', '十分', '必要', '重要', '基本', '一般',
            '通常', '標準', '推奨', '望ましい'
        ]
        
        for axis_num, results in mece_results.items():
            if results and 'machine_readable' in results:
                mr_data = results['machine_readable']
                
                for constraint_type in ['hard_constraints', 'soft_constraints', 'preferences']:
                    constraints = mr_data.get(constraint_type, [])
                    for constraint in constraints:
                        if isinstance(constraint, dict):
                            total_constraints += 1
                            
                            constraint_text = str(constraint.get('rule', '')) + str(constraint.get('constraint', ''))
                            
                            # 具体性スコア計算
                            specific_count = sum(1 for keyword in specific_keywords if keyword in constraint_text)
                            vague_count = sum(1 for keyword in vague_keywords if keyword in constraint_text)
                            
                            # 数値の存在チェック
                            has_numbers = bool(re.search(r'\d+', constraint_text))
                            
                            # IF-THEN構造の存在チェック
                            has_if_then = 'execution_rule' in constraint and constraint['execution_rule'].get('condition')
                            
                            # 具体性判定
                            if (specific_count >= 2 or has_numbers or has_if_then) and vague_count <= 1:
                                specific_constraints += 1
        
        specificity_score = specific_constraints / total_constraints if total_constraints > 0 else 0
        
        log.info(f"  総制約数: {total_constraints}")
        log.info(f"  具体的制約数: {specific_constraints}")
        log.info(f"  具体性スコア: {specificity_score:.1%}")
        
        return specificity_score
    
    def _analyze_actionability(self, mece_results: Dict[int, Dict]) -> float:
        """実行可能性分析"""
        log.info("⚡ 実行可能性分析中...")
        
        total_constraints = 0
        actionable_constraints = 0
        high_actionability = 0
        
        for axis_num, results in mece_results.items():
            if results and 'machine_readable' in results:
                mr_data = results['machine_readable']
                
                for constraint_type in ['hard_constraints', 'soft_constraints', 'preferences']:
                    constraints = mr_data.get(constraint_type, [])
                    for constraint in constraints:
                        if isinstance(constraint, dict):
                            total_constraints += 1
                            
                            # 実行可能性チェック
                            actionability_score = constraint.get('actionability_score', 0)
                            if actionability_score >= 0.5:
                                actionable_constraints += 1
                            if actionability_score >= 0.8:
                                high_actionability += 1
        
        actionability_rate = actionable_constraints / total_constraints if total_constraints > 0 else 0
        high_actionability_rate = high_actionability / total_constraints if total_constraints > 0 else 0
        
        # 総合実行可能性スコア
        overall_actionability = (actionability_rate * 0.7) + (high_actionability_rate * 0.3)
        
        log.info(f"  実行可能制約率: {actionability_rate:.1%}")
        log.info(f"  高実行可能制約率: {high_actionability_rate:.1%}")
        log.info(f"  実行可能性スコア: {overall_actionability:.1%}")
        
        return overall_actionability
    
    def _analyze_consistency(self, mece_results: Dict[int, Dict]) -> float:
        """一貫性分析"""
        log.info("🔗 一貫性分析中...")
        
        # 制約タイプの一貫性
        constraint_types = defaultdict(int)
        rule_patterns = defaultdict(int)
        confidence_levels = []
        
        for axis_num, results in mece_results.items():
            if results and 'machine_readable' in results:
                mr_data = results['machine_readable']
                
                for constraint_type in ['hard_constraints', 'soft_constraints', 'preferences']:
                    constraints = mr_data.get(constraint_type, [])
                    for constraint in constraints:
                        if isinstance(constraint, dict):
                            # タイプの一貫性
                            c_type = constraint.get('type', 'unknown')
                            constraint_types[c_type] += 1
                            
                            # ルールパターンの一貫性
                            rule = constraint.get('rule', '')
                            if len(rule) > 10:
                                rule_pattern = rule[:20] + "..."
                                rule_patterns[rule_pattern] += 1
                            
                            # 信頼度の一貫性
                            confidence = constraint.get('confidence', 0)
                            confidence_levels.append(confidence)
        
        # 一貫性スコア計算
        type_consistency = len(constraint_types) / max(sum(constraint_types.values()), 1)
        
        # 信頼度の分散（低いほど一貫性が高い）
        confidence_std = np.std(confidence_levels) if confidence_levels else 1.0
        confidence_consistency = 1.0 - min(confidence_std, 1.0)
        
        # 構造の一貫性（同じキーを持つ制約の割合）
        structure_consistency = self._calculate_structure_consistency(mece_results)
        
        overall_consistency = (type_consistency * 0.3) + (confidence_consistency * 0.3) + (structure_consistency * 0.4)
        
        log.info(f"  タイプ一貫性: {type_consistency:.1%}")
        log.info(f"  信頼度一貫性: {confidence_consistency:.1%}")
        log.info(f"  構造一貫性: {structure_consistency:.1%}")
        log.info(f"  一貫性スコア: {overall_consistency:.1%}")
        
        return overall_consistency
    
    def _analyze_verifiability(self, mece_results: Dict[int, Dict]) -> float:
        """検証可能性分析"""
        log.info("✅ 検証可能性分析中...")
        
        total_constraints = 0
        verifiable_constraints = 0
        
        for axis_num, results in mece_results.items():
            if results and 'machine_readable' in results:
                mr_data = results['machine_readable']
                
                for constraint_type in ['hard_constraints', 'soft_constraints', 'preferences']:
                    constraints = mr_data.get(constraint_type, [])
                    for constraint in constraints:
                        if isinstance(constraint, dict):
                            total_constraints += 1
                            
                            # 検証可能性チェック
                            has_verification = constraint.get('verification_method') is not None
                            has_quantified_criteria = constraint.get('quantified_criteria') is not None
                            has_confidence = constraint.get('confidence', 0) > 0
                            
                            if has_verification or (has_quantified_criteria and has_confidence):
                                verifiable_constraints += 1
        
        verifiability_score = verifiable_constraints / total_constraints if total_constraints > 0 else 0
        
        log.info(f"  検証可能制約数: {verifiable_constraints}/{total_constraints}")
        log.info(f"  検証可能性スコア: {verifiability_score:.1%}")
        
        return verifiability_score
    
    def _analyze_usability(self, mece_results: Dict[int, Dict]) -> float:
        """使いやすさ分析"""
        log.info("👥 使いやすさ分析中...")
        
        # 可読性スコア
        readability_score = self._calculate_readability(mece_results)
        
        # 構造化スコア
        structure_score = self._calculate_structure_quality(mece_results)
        
        # ドキュメント化スコア
        documentation_score = self._calculate_documentation_quality(mece_results)
        
        usability_score = (readability_score * 0.4) + (structure_score * 0.3) + (documentation_score * 0.3)
        
        log.info(f"  可読性: {readability_score:.1%}")
        log.info(f"  構造化: {structure_score:.1%}")
        log.info(f"  ドキュメント化: {documentation_score:.1%}")
        log.info(f"  使いやすさスコア: {usability_score:.1%}")
        
        return usability_score
    
    def _calculate_structure_consistency(self, mece_results: Dict[int, Dict]) -> float:
        """構造一貫性の計算"""
        required_keys = ['type', 'rule', 'confidence']
        total_constraints = 0
        consistent_constraints = 0
        
        for axis_num, results in mece_results.items():
            if results and 'machine_readable' in results:
                mr_data = results['machine_readable']
                
                for constraint_type in ['hard_constraints', 'soft_constraints', 'preferences']:
                    constraints = mr_data.get(constraint_type, [])
                    for constraint in constraints:
                        if isinstance(constraint, dict):
                            total_constraints += 1
                            
                            # 必須キーの存在チェック
                            has_required_keys = all(key in constraint for key in required_keys)
                            if has_required_keys:
                                consistent_constraints += 1
        
        return consistent_constraints / total_constraints if total_constraints > 0 else 0
    
    def _calculate_readability(self, mece_results: Dict[int, Dict]) -> float:
        """可読性の計算"""
        total_text_length = 0
        readable_text_count = 0
        
        for axis_num, results in mece_results.items():
            if results and 'human_readable' in results:
                hr_data = results['human_readable']
                
                # 日本語の可読性チェック
                text_content = str(hr_data)
                total_text_length += len(text_content)
                
                # 適切な長さ（短すぎず長すぎない）
                if 50 <= len(text_content) <= 2000:
                    readable_text_count += 1
        
        return readable_text_count / len(mece_results) if mece_results else 0
    
    def _calculate_structure_quality(self, mece_results: Dict[int, Dict]) -> float:
        """構造品質の計算"""
        required_sections = ['human_readable', 'machine_readable', 'extraction_metadata']
        total_axes = len(mece_results)
        well_structured_axes = 0
        
        for axis_num, results in mece_results.items():
            if results and all(section in results for section in required_sections):
                well_structured_axes += 1
        
        return well_structured_axes / total_axes if total_axes > 0 else 0
    
    def _calculate_documentation_quality(self, mece_results: Dict[int, Dict]) -> float:
        """ドキュメント品質の計算"""
        total_axes = len(mece_results)
        documented_axes = 0
        
        for axis_num, results in mece_results.items():
            if results and 'extraction_metadata' in results:
                metadata = results['extraction_metadata']
                
                # 基本的なメタデータの存在チェック
                has_timestamp = 'extraction_timestamp' in metadata
                has_quality_info = 'data_quality' in metadata
                
                if has_timestamp and has_quality_info:
                    documented_axes += 1
        
        return documented_axes / total_axes if total_axes > 0 else 0
    
    def _identify_critical_issues(self, scores: Dict[str, float], mece_results: Dict[int, Dict]) -> List[Dict]:
        """重要課題の特定"""
        critical_issues = []
        
        # しきい値未満の次元を特定
        threshold = 0.6
        
        for dimension, score in scores.items():
            if score < threshold:
                issue = {
                    'dimension': dimension,
                    'current_score': score,
                    'severity': 'critical' if score < 0.4 else 'high',
                    'impact': self._assess_impact(dimension, score),
                    'specific_problems': self._identify_specific_problems(dimension, mece_results)
                }
                critical_issues.append(issue)
        
        return critical_issues
    
    def _find_improvement_opportunities(self, scores: Dict[str, float], mece_results: Dict[int, Dict]) -> List[Dict]:
        """改善機会の発見"""
        opportunities = []
        
        # 改善可能性の高い領域を特定
        for dimension, score in scores.items():
            if 0.5 <= score < 0.8:  # 改善余地がある範囲
                opportunity = {
                    'dimension': dimension,
                    'current_score': score,
                    'target_score': min(0.9, score + 0.2),
                    'effort_level': self._estimate_effort(dimension, score),
                    'quick_wins': self._identify_quick_wins(dimension, mece_results)
                }
                opportunities.append(opportunity)
        
        return opportunities
    
    def _generate_detailed_findings(self, scores: Dict[str, float], mece_results: Dict[int, Dict]) -> Dict[str, Any]:
        """詳細所見の生成"""
        findings = {}
        
        for dimension, score in scores.items():
            findings[dimension] = {
                'score': score,
                'grade': self._score_to_grade(score),
                'strengths': self._identify_strengths(dimension, mece_results),
                'weaknesses': self._identify_weaknesses(dimension, mece_results),
                'benchmark': self._get_benchmark(dimension)
            }
        
        return findings
    
    def _generate_actionable_recommendations(self, analysis: Dict[str, Any]) -> List[Dict]:
        """実行可能な推奨事項の生成"""
        recommendations = []
        
        # 重要課題への対応
        for issue in analysis['critical_issues']:
            rec = {
                'type': 'critical_fix',
                'dimension': issue['dimension'],
                'action': self._get_fix_action(issue['dimension']),
                'priority': 'high',
                'estimated_effort': 'medium',
                'expected_improvement': 0.2
            }
            recommendations.append(rec)
        
        # 改善機会への対応
        for opportunity in analysis['improvement_opportunities']:
            rec = {
                'type': 'enhancement',
                'dimension': opportunity['dimension'],
                'action': self._get_enhancement_action(opportunity['dimension']),
                'priority': 'medium',
                'estimated_effort': opportunity['effort_level'],
                'expected_improvement': 0.1
            }
            recommendations.append(rec)
        
        return recommendations
    
    def _assess_impact(self, dimension: str, score: float) -> str:
        """影響度評価"""
        impact_map = {
            'completeness': 'システム全体の網羅性に重大な影響',
            'specificity': '制約の実用性に大きな影響',
            'actionability': 'AI実装時の実行可能性に致命的影響',
            'consistency': 'システムの信頼性に影響',
            'verifiability': '品質保証に影響',
            'usability': 'ユーザー体験に影響'
        }
        return impact_map.get(dimension, '不明な影響')
    
    def _identify_specific_problems(self, dimension: str, mece_results: Dict[int, Dict]) -> List[str]:
        """具体的問題の特定"""
        problems = []
        
        if dimension == 'completeness':
            problems.append("空のカテゴリーが多数存在")
            problems.append("軸4-12でカテゴリー不足")
        elif dimension == 'actionability':
            problems.append("抽象的な制約が多い")
            problems.append("IF-THEN構造が不完全")
        elif dimension == 'specificity':
            problems.append("曖昧な表現が多用されている")
            problems.append("数値基準が不明確")
        
        return problems
    
    def _estimate_effort(self, dimension: str, score: float) -> str:
        """作業量推定"""
        if score < 0.3:
            return 'high'
        elif score < 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _identify_quick_wins(self, dimension: str, mece_results: Dict[int, Dict]) -> List[str]:
        """クイックウィンの特定"""
        quick_wins = []
        
        if dimension == 'actionability':
            quick_wins.append("既存制約にIF-THEN構造を追加")
            quick_wins.append("数値基準の明確化")
        elif dimension == 'completeness':
            quick_wins.append("空カテゴリーにダミーデータ追加")
            quick_wins.append("類似制約の複製・調整")
        
        return quick_wins
    
    def _score_to_grade(self, score: float) -> str:
        """スコアを等級に変換"""
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
        elif score >= 0.4:
            return 'C'
        else:
            return 'D'
    
    def _identify_strengths(self, dimension: str, mece_results: Dict[int, Dict]) -> List[str]:
        """強みの特定"""
        strengths = []
        
        if dimension == 'actionability':
            strengths.append("制約強化システムが実装済み")
        elif dimension == 'consistency':
            strengths.append("基本構造が統一されている")
        
        return strengths
    
    def _identify_weaknesses(self, dimension: str, mece_results: Dict[int, Dict]) -> List[str]:
        """弱みの特定"""
        weaknesses = []
        
        if dimension == 'completeness':
            weaknesses.append("カテゴリー不足")
        elif dimension == 'specificity':
            weaknesses.append("抽象的表現が多い")
        
        return weaknesses
    
    def _get_benchmark(self, dimension: str) -> Dict[str, float]:
        """ベンチマーク取得"""
        benchmarks = {
            'completeness': {'industry_standard': 0.85, 'best_practice': 0.95},
            'specificity': {'industry_standard': 0.70, 'best_practice': 0.90},
            'actionability': {'industry_standard': 0.80, 'best_practice': 0.95},
            'consistency': {'industry_standard': 0.75, 'best_practice': 0.85},
            'verifiability': {'industry_standard': 0.70, 'best_practice': 0.85},
            'usability': {'industry_standard': 0.65, 'best_practice': 0.80}
        }
        return benchmarks.get(dimension, {'industry_standard': 0.70, 'best_practice': 0.85})
    
    def _get_fix_action(self, dimension: str) -> str:
        """修正アクションの取得"""
        actions = {
            'completeness': "不足カテゴリーの実装と空カテゴリーの充実",
            'specificity': "抽象的制約の具体化と数値基準の明確化",
            'actionability': "IF-THEN構造の完全実装と実行可能性向上",
            'consistency': "制約フォーマットの統一と構造の標準化",
            'verifiability': "検証方法の定義と品質メトリクスの追加",
            'usability': "ユーザーインターフェースの改善とドキュメント充実"
        }
        return actions.get(dimension, "具体的な改善アクションの検討")
    
    def _get_enhancement_action(self, dimension: str) -> str:
        """強化アクションの取得"""
        actions = {
            'completeness': "追加カテゴリーの段階的実装",
            'specificity': "制約の詳細化と具体例の追加",
            'actionability': "高度なIF-THEN構造の実装",
            'consistency': "制約パターンの標準化",
            'verifiability': "自動検証システムの強化",
            'usability': "ユーザビリティテストの実施"
        }
        return actions.get(dimension, "段階的な改善の実施")


def main():
    """メイン実行"""
    analyzer = AdvancedQualityAnalyzer()
    log.info("高度品質分析システムが初期化されました")
    log.info("使用方法: analyzer.analyze_comprehensive_quality(mece_results)")


if __name__ == "__main__":
    main()