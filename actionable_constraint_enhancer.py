#!/usr/bin/env python3
"""
実行可能制約の強化システム

抽象的制約を具体的で実行可能な制約に変換
IF-THEN形式の明確な条件とアクションを定義
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any, Union
from datetime import datetime, timedelta
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class ActionableConstraintEnhancer:
    """実行可能制約への変換・強化システム"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.min_sample_size = 10
        
    def enhance_facility_constraints(self, original_results: Dict[str, Any]) -> Dict[str, Any]:
        """軸1施設制約を実行可能な形に強化"""
        log.info("軸1施設制約の実行可能性強化開始...")
        
        enhanced = {
            'human_readable': {},
            'machine_readable': {
                'hard_constraints': [],
                'soft_constraints': [],
                'preferences': []
            },
            'extraction_metadata': {}
        }
        
        # 元の制約を解析して実行可能な形に変換
        if 'machine_readable' in original_results:
            mr_data = original_results['machine_readable']
            
            # ハード制約の強化
            for constraint in mr_data.get('hard_constraints', []):
                enhanced_constraint = self._enhance_constraint_actionability(constraint, 'hard')
                if enhanced_constraint:
                    enhanced['machine_readable']['hard_constraints'].append(enhanced_constraint)
            
            # ソフト制約の強化
            for constraint in mr_data.get('soft_constraints', []):
                enhanced_constraint = self._enhance_constraint_actionability(constraint, 'soft')
                if enhanced_constraint:
                    enhanced['machine_readable']['soft_constraints'].append(enhanced_constraint)
        
        # 人間可読形式の生成
        enhanced['human_readable'] = self._generate_readable_constraints(enhanced['machine_readable'])
        
        # メタデータの更新
        enhanced['extraction_metadata'] = {
            'enhancement_applied': True,
            'actionability_improvements': self._count_improvements(original_results, enhanced),
            'enhancement_timestamp': datetime.now().isoformat()
        }
        
        return enhanced
    
    def _enhance_constraint_actionability(self, constraint: Dict[str, Any], constraint_type: str) -> Dict[str, Any]:
        """個別制約の実行可能性を向上"""
        
        # 基本的な制約構造の確認
        if not isinstance(constraint, dict) or 'type' not in constraint:
            return None
        
        enhanced = constraint.copy()
        
        # IF-THEN構造の追加
        enhanced['execution_rule'] = self._create_if_then_rule(constraint)
        
        # 数値基準の明確化
        enhanced['quantified_criteria'] = self._extract_quantified_criteria(constraint)
        
        # 実行可能性スコアの計算
        enhanced['actionability_score'] = self._calculate_actionability_score(enhanced)
        
        # 制約の優先度設定
        enhanced['priority'] = self._determine_constraint_priority(enhanced, constraint_type)
        
        # 検証可能性の追加
        enhanced['verification_method'] = self._add_verification_method(enhanced)
        
        return enhanced
    
    def _create_if_then_rule(self, constraint: Dict[str, Any]) -> Dict[str, str]:
        """IF-THEN構造のルール作成"""
        
        constraint_type = constraint.get('type', '')
        rule_content = constraint.get('rule', constraint.get('constraint', ''))
        
        if_then_rule = {
            'condition': '',
            'action': '',
            'exception': ''
        }
        
        # 制約タイプ別のIF-THEN変換
        if 'staff_count' in constraint_type.lower() or '人数' in str(rule_content):
            # 人数制約
            if_then_rule['condition'] = f"シフト時間帯に配置される職員数が基準値を下回る場合"
            if_then_rule['action'] = f"最低限必要な職員数を確保する"
            if_then_rule['exception'] = f"緊急時は一時的な基準緩和を許可"
            
        elif 'time' in constraint_type.lower() or '時間' in str(rule_content):
            # 時間制約
            if_then_rule['condition'] = f"連続勤務時間または休憩時間が規定を超過する場合"
            if_then_rule['action'] = f"シフト調整により規定時間内に収める"
            if_then_rule['exception'] = f"職員の同意がある場合は例外適用可能"
            
        elif 'role' in constraint_type.lower() or '職種' in str(rule_content):
            # 職種制約
            if_then_rule['condition'] = f"必要な職種の職員が配置されていない場合"
            if_then_rule['action'] = f"適切な職種の職員を配置する"
            if_then_rule['exception'] = f"代替可能な職種による一時対応を許可"
            
        else:
            # 汎用制約
            if_then_rule['condition'] = f"制約条件 {constraint_type} が満たされない場合"
            if_then_rule['action'] = f"制約を満たすためのシフト調整を実行"
            if_then_rule['exception'] = f"運用上必要な場合は例外処理を適用"
        
        return if_then_rule
    
    def _extract_quantified_criteria(self, constraint: Dict[str, Any]) -> Dict[str, Union[int, float]]:
        """数値基準の抽出・明確化"""
        
        criteria = {}
        rule_text = str(constraint.get('rule', constraint.get('constraint', '')))
        
        # 数値の抽出
        import re
        numbers = re.findall(r'\d+\.?\d*', rule_text)
        
        if numbers:
            # 基本的な数値基準
            if len(numbers) >= 1:
                criteria['minimum_value'] = float(numbers[0])
            if len(numbers) >= 2:
                criteria['maximum_value'] = float(numbers[1])
        
        # 制約タイプ別のデフォルト基準
        constraint_type = constraint.get('type', '').lower()
        
        if 'staff' in constraint_type and 'count' in constraint_type:
            criteria.setdefault('minimum_value', 1)
            criteria.setdefault('maximum_value', 10)
            
        elif 'time' in constraint_type:
            criteria.setdefault('minimum_value', 1)  # 最低1時間
            criteria.setdefault('maximum_value', 16)  # 最大16時間
            
        elif 'ratio' in constraint_type or '比率' in rule_text:
            criteria.setdefault('minimum_value', 0.0)
            criteria.setdefault('maximum_value', 1.0)
        
        # 信頼度に基づく調整
        confidence = constraint.get('confidence', 0.5)
        if confidence > 0.8:
            criteria['confidence_level'] = 'high'
        elif confidence > 0.5:
            criteria['confidence_level'] = 'medium'
        else:
            criteria['confidence_level'] = 'low'
        
        return criteria
    
    def _calculate_actionability_score(self, constraint: Dict[str, Any]) -> float:
        """実行可能性スコアの計算"""
        
        score = 0.0
        
        # IF-THENルールの存在 (30%)
        if constraint.get('execution_rule', {}).get('condition'):
            score += 0.3
        
        # 数値基準の明確性 (25%)
        quantified = constraint.get('quantified_criteria', {})
        if 'minimum_value' in quantified or 'maximum_value' in quantified:
            score += 0.25
        
        # 制約タイプの具体性 (20%)
        constraint_type = constraint.get('type', '')
        if any(keyword in constraint_type.lower() for keyword in ['staff', 'time', 'count', 'ratio']):
            score += 0.2
        
        # 信頼度 (15%)
        confidence = constraint.get('confidence', 0.0)
        score += confidence * 0.15
        
        # 検証可能性 (10%)
        if constraint.get('verification_method'):
            score += 0.1
        
        return min(1.0, score)
    
    def _determine_constraint_priority(self, constraint: Dict[str, Any], constraint_type: str) -> str:
        """制約優先度の決定"""
        
        # ハード制約は基本的に高優先度
        if constraint_type == 'hard':
            return 'critical'
        
        # 実行可能性スコアによる優先度決定
        actionability = constraint.get('actionability_score', 0.0)
        confidence = constraint.get('confidence', 0.0)
        
        if actionability >= 0.8 and confidence >= 0.8:
            return 'high'
        elif actionability >= 0.6 and confidence >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _add_verification_method(self, constraint: Dict[str, Any]) -> Dict[str, str]:
        """検証方法の追加"""
        
        constraint_type = constraint.get('type', '').lower()
        
        verification = {
            'method': '',
            'frequency': '',
            'metrics': ''
        }
        
        if 'staff' in constraint_type:
            verification['method'] = 'スタッフ配置数の自動カウント'
            verification['frequency'] = 'リアルタイム'
            verification['metrics'] = '配置人数, 職種別カウント'
            
        elif 'time' in constraint_type:
            verification['method'] = '勤務時間の自動計算'
            verification['frequency'] = '日次/週次'
            verification['metrics'] = '連続勤務時間, 休憩時間, 週間労働時間'
            
        else:
            verification['method'] = '制約違反の自動検出'
            verification['frequency'] = '定期チェック'
            verification['metrics'] = '制約適合率, 違反件数'
        
        return verification
    
    def _generate_readable_constraints(self, machine_readable: Dict[str, Any]) -> Dict[str, Any]:
        """人間可読形式の制約生成"""
        
        readable = {
            'MECE分解事実': {
                '実行可能制約': {},
                '数値基準制約': {},
                'IF-THEN制約': {},
                '検証可能制約': {}
            },
            '統計情報': {}
        }
        
        # 実行可能制約の分類
        all_constraints = []
        all_constraints.extend(machine_readable.get('hard_constraints', []))
        all_constraints.extend(machine_readable.get('soft_constraints', []))
        
        actionable_count = 0
        quantified_count = 0
        if_then_count = 0
        verifiable_count = 0
        
        for constraint in all_constraints:
            # 実行可能性チェック
            if constraint.get('actionability_score', 0) >= 0.7:
                actionable_count += 1
                readable['MECE分解事実']['実行可能制約'][f"制約{actionable_count}"] = {
                    'ルール': constraint.get('rule', '未定義'),
                    'スコア': constraint.get('actionability_score', 0),
                    '優先度': constraint.get('priority', 'unknown')
                }
            
            # 数値基準チェック
            if constraint.get('quantified_criteria'):
                quantified_count += 1
                readable['MECE分解事実']['数値基準制約'][f"基準{quantified_count}"] = constraint['quantified_criteria']
            
            # IF-THENルールチェック
            if constraint.get('execution_rule', {}).get('condition'):
                if_then_count += 1
                readable['MECE分解事実']['IF-THEN制約'][f"ルール{if_then_count}"] = constraint['execution_rule']
            
            # 検証可能性チェック
            if constraint.get('verification_method'):
                verifiable_count += 1
                readable['MECE分解事実']['検証可能制約'][f"検証{verifiable_count}"] = constraint['verification_method']
        
        # 統計情報
        readable['統計情報'] = {
            '総制約数': len(all_constraints),
            '実行可能制約数': actionable_count,
            '数値基準制約数': quantified_count,
            'IF-THEN制約数': if_then_count,
            '検証可能制約数': verifiable_count,
            '実行可能率': round(actionable_count / len(all_constraints) * 100, 1) if all_constraints else 0
        }
        
        return readable
    
    def _count_improvements(self, original: Dict[str, Any], enhanced: Dict[str, Any]) -> Dict[str, int]:
        """改善数のカウント"""
        
        improvements = {
            'if_then_rules_added': 0,
            'quantified_criteria_added': 0,
            'verification_methods_added': 0,
            'actionability_score_improved': 0
        }
        
        # 強化された制約の数をカウント
        enhanced_constraints = []
        enhanced_constraints.extend(enhanced.get('machine_readable', {}).get('hard_constraints', []))
        enhanced_constraints.extend(enhanced.get('machine_readable', {}).get('soft_constraints', []))
        
        for constraint in enhanced_constraints:
            if constraint.get('execution_rule'):
                improvements['if_then_rules_added'] += 1
            if constraint.get('quantified_criteria'):
                improvements['quantified_criteria_added'] += 1
            if constraint.get('verification_method'):
                improvements['verification_methods_added'] += 1
            if constraint.get('actionability_score', 0) >= 0.7:
                improvements['actionability_score_improved'] += 1
        
        return improvements
    
    def enhance_all_axes_constraints(self, all_axis_results: Dict[int, Dict]) -> Dict[int, Dict]:
        """全軸の制約を実行可能形式に強化"""
        log.info("全軸制約の実行可能性強化開始...")
        
        enhanced_results = {}
        
        for axis_num, results in all_axis_results.items():
            if results and isinstance(results, dict):
                log.info(f"軸{axis_num}の制約強化中...")
                
                if axis_num == 1:
                    enhanced_results[axis_num] = self.enhance_facility_constraints(results)
                else:
                    # 他の軸も同様の強化を適用
                    enhanced_results[axis_num] = self._enhance_generic_constraints(results, axis_num)
            else:
                enhanced_results[axis_num] = results
        
        return enhanced_results
    
    def _enhance_generic_constraints(self, original_results: Dict[str, Any], axis_num: int) -> Dict[str, Any]:
        """汎用的な制約強化（軸1以外）"""
        
        enhanced = original_results.copy()
        
        if 'machine_readable' in enhanced:
            mr_data = enhanced['machine_readable']
            
            # 各制約タイプを強化
            for constraint_type in ['hard_constraints', 'soft_constraints', 'preferences']:
                if constraint_type in mr_data and isinstance(mr_data[constraint_type], list):
                    enhanced_constraints = []
                    for constraint in mr_data[constraint_type]:
                        if isinstance(constraint, dict):
                            enhanced_constraint = self._enhance_constraint_actionability(constraint, constraint_type.split('_')[0])
                            enhanced_constraints.append(enhanced_constraint)
                        else:
                            enhanced_constraints.append(constraint)
                    mr_data[constraint_type] = enhanced_constraints
        
        return enhanced
    
    def generate_actionability_report(self, enhanced_results: Dict[int, Dict]) -> Dict[str, Any]:
        """実行可能性レポートの生成"""
        
        report = {
            'summary': {
                'total_axes': len(enhanced_results),
                'total_constraints': 0,
                'actionable_constraints': 0,
                'if_then_rules': 0,
                'quantified_constraints': 0,
                'verifiable_constraints': 0
            },
            'by_axis': {},
            'improvements': {
                'actionability_rate_before': 0.169,  # MECEテスト結果から
                'actionability_rate_after': 0.0,
                'improvement_ratio': 0.0
            }
        }
        
        total_constraints = 0
        actionable_constraints = 0
        
        for axis_num, results in enhanced_results.items():
            if results and 'machine_readable' in results:
                mr_data = results['machine_readable']
                
                axis_constraints = []
                axis_constraints.extend(mr_data.get('hard_constraints', []))
                axis_constraints.extend(mr_data.get('soft_constraints', []))
                axis_constraints.extend(mr_data.get('preferences', []))
                
                axis_actionable = sum(1 for c in axis_constraints 
                                    if isinstance(c, dict) and c.get('actionability_score', 0) >= 0.7)
                
                total_constraints += len(axis_constraints)
                actionable_constraints += axis_actionable
                
                report['by_axis'][f'axis_{axis_num}'] = {
                    'total_constraints': len(axis_constraints),
                    'actionable_constraints': axis_actionable,
                    'actionability_rate': round(axis_actionable / len(axis_constraints), 3) if axis_constraints else 0
                }
        
        # 全体統計の更新
        report['summary']['total_constraints'] = total_constraints
        report['summary']['actionable_constraints'] = actionable_constraints
        
        # 改善率の計算
        if total_constraints > 0:
            new_actionability_rate = actionable_constraints / total_constraints
            report['improvements']['actionability_rate_after'] = new_actionability_rate
            report['improvements']['improvement_ratio'] = (
                new_actionability_rate - report['improvements']['actionability_rate_before']
            ) / report['improvements']['actionability_rate_before']
        
        return report


def main():
    """実行可能制約強化のテスト実行"""
    log.info("実行可能制約強化テスト開始")
    
    enhancer = ActionableConstraintEnhancer()
    
    # 既存のMECEテスト結果を読み込み
    try:
        # ここで実際の軸結果を読み込み
        log.info("実行可能制約強化システムが正常に初期化されました")
        log.info("使用方法: enhancer.enhance_all_axes_constraints(axis_results)")
        
    except Exception as e:
        log.error(f"初期化エラー: {e}")


if __name__ == "__main__":
    main()