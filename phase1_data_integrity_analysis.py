#!/usr/bin/env python3
"""
Phase1: データ整合性改善分析
慎重なアプローチによる問題特定と段階的修正
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
sys.path.append('.')

@dataclass
class DataIntegrityIssue:
    """データ整合性問題"""
    issue_type: str
    severity: str  # low, medium, high, critical
    description: str
    affected_data: str
    impact_hours: float
    suggested_fix: str
    
@dataclass
class IntegrityAnalysisResult:
    """整合性分析結果"""
    current_score: float
    target_score: float
    identified_issues: List[DataIntegrityIssue]
    fix_priority: List[str]
    estimated_improvement: float

class Phase1DataIntegrityAnalyzer:
    """Phase1 データ整合性分析器"""
    
    def __init__(self):
        self.scenario_dir = Path('extracted_results/out_p25_based')
        self.data_path = self.scenario_dir / 'intermediate_data.parquet'
        self.slot_hours = 0.5
        
    def execute_phase1_analysis(self) -> IntegrityAnalysisResult:
        """Phase1 データ整合性分析実行"""
        
        print("=== Phase1: データ整合性改善分析開始 ===")
        
        # 1. 現在のデータ状態詳細分析
        current_issues = self._identify_current_issues()
        
        # 2. 各問題の影響度評価
        prioritized_issues = self._prioritize_issues(current_issues)
        
        # 3. 修正優先順位決定
        fix_priority = self._determine_fix_priority(prioritized_issues)
        
        # 4. 改善見込み評価
        improvement_estimate = self._estimate_improvement(prioritized_issues)
        
        return IntegrityAnalysisResult(
            current_score=0.8,  # 現在80%
            target_score=0.95,  # 目標95%
            identified_issues=prioritized_issues,
            fix_priority=fix_priority,
            estimated_improvement=improvement_estimate
        )
    
    def _identify_current_issues(self) -> List[DataIntegrityIssue]:
        """現在のデータ整合性問題特定"""
        
        print("1. 現在のデータ整合性問題特定中...")
        
        issues = []
        df = pd.read_parquet(self.data_path)
        
        # 問題1: 負の値チェック (parsed_slots_count)
        negative_count_data = df[df['parsed_slots_count'] < 0]
        if len(negative_count_data) > 0:
            issues.append(DataIntegrityIssue(
                issue_type="negative_values",
                severity="high",
                description=f"{len(negative_count_data)}件の負のスロット数データ",
                affected_data="intermediate_data.parquet",
                impact_hours=abs(negative_count_data['parsed_slots_count'].sum()) * self.slot_hours,
                suggested_fix="負値データの0への正規化またはデータ源修正"
            ))
        
        # 問題2: 欠損データチェック
        missing_role_data = df[df['role'].isna()]
        if len(missing_role_data) > 0:
            issues.append(DataIntegrityIssue(
                issue_type="missing_role_data",
                severity="critical",
                description=f"{len(missing_role_data)}件の職種欠損データ",
                affected_data="intermediate_data.parquet",
                impact_hours=len(missing_role_data) * self.slot_hours,
                suggested_fix="職種データの補完または除外"
            ))
        
        # 問題3: 不正な日付データ
        try:
            invalid_dates = df[pd.to_datetime(df['ds'], errors='coerce').isna()]
            if len(invalid_dates) > 0:
                issues.append(DataIntegrityIssue(
                    issue_type="invalid_date_data",
                    severity="medium",
                    description=f"{len(invalid_dates)}件の不正日付データ",
                    affected_data="intermediate_data.parquet",
                    impact_hours=len(invalid_dates) * self.slot_hours,
                    suggested_fix="日付フォーマットの統一・修正"
                ))
        except Exception as e:
            print(f"   日付チェックでエラー: {e}")
        
        # 問題4: 重複データチェック
        duplicate_records = df.duplicated(subset=['staff', 'ds', 'code'])
        duplicate_count = duplicate_records.sum()
        if duplicate_count > 0:
            issues.append(DataIntegrityIssue(
                issue_type="duplicate_records",
                severity="medium", 
                description=f"{duplicate_count}件の重複レコード",
                affected_data="intermediate_data.parquet",
                impact_hours=duplicate_count * self.slot_hours,
                suggested_fix="重複データの除去・統合"
            ))
        
        # 問題5: 異常値チェック（実働データのみで1日12時間超のスタッフ）
        working_data = df[df['holiday_type'].isin(['通常勤務', 'NORMAL'])]
        if len(working_data) > 0:
            daily_slots = working_data.groupby(['staff', 'ds']).size()
            daily_hours = daily_slots * self.slot_hours
            excessive_hours = daily_hours[daily_hours > 12]  # 1日12時間超
            if len(excessive_hours) > 0:
                issues.append(DataIntegrityIssue(
                    issue_type="excessive_daily_hours",
                    severity="high",
                    description=f"{len(excessive_hours)}件の異常勤務時間（12時間超/日）",
                    affected_data="intermediate_data.parquet", 
                    impact_hours=excessive_hours.sum() - (len(excessive_hours) * 8),  # 8時間超過分
                    suggested_fix="労働基準法準拠の勤務時間制限適用"
                ))
        
        print(f"   特定された問題: {len(issues)}個")
        return issues
    
    def _prioritize_issues(self, issues: List[DataIntegrityIssue]) -> List[DataIntegrityIssue]:
        """問題の優先順位付け"""
        
        print("2. 問題の優先順位付け...")
        
        # 重要度スコア計算
        severity_weights = {
            'critical': 4.0,
            'high': 3.0, 
            'medium': 2.0,
            'low': 1.0
        }
        
        for issue in issues:
            # 重要度 × 影響時間での優先度計算
            priority_score = severity_weights.get(issue.severity, 1.0) * max(1, issue.impact_hours / 10)
            issue.priority_score = priority_score
        
        # 優先度順にソート
        prioritized = sorted(issues, key=lambda x: getattr(x, 'priority_score', 0), reverse=True)
        
        for i, issue in enumerate(prioritized, 1):
            print(f"   {i}. {issue.issue_type} - {issue.severity} ({issue.impact_hours:.1f}時間影響)")
        
        return prioritized
    
    def _determine_fix_priority(self, issues: List[DataIntegrityIssue]) -> List[str]:
        """修正優先順位決定"""
        
        print("3. 修正優先順位決定...")
        
        # 実装難易度を考慮した優先順位
        fix_complexity = {
            'missing_role_data': 1,      # 最優先（critical）
            'negative_values': 2,        # 簡単に修正可能
            'duplicate_records': 3,      # データクリーニング
            'excessive_daily_hours': 4,  # ビジネスルール適用
            'invalid_date_data': 5       # フォーマット修正
        }
        
        priority_order = []
        for issue in issues:
            if issue.issue_type not in priority_order:
                priority_order.append(issue.issue_type)
        
        # 複雑性を考慮して並び替え
        sorted_priority = sorted(priority_order, key=lambda x: fix_complexity.get(x, 10))
        
        print("   修正優先順位:")
        for i, issue_type in enumerate(sorted_priority, 1):
            print(f"   {i}. {issue_type}")
        
        return sorted_priority
    
    def _estimate_improvement(self, issues: List[DataIntegrityIssue]) -> float:
        """改善見込み評価"""
        
        print("4. 改善見込み評価...")
        
        # 各問題修正による改善見込み
        total_impact = sum(issue.impact_hours for issue in issues)
        current_total_hours = 3288.5  # 総供給時間
        
        # 修正による改善率推定
        if current_total_hours > 0:
            improvement_ratio = min(0.15, total_impact / current_total_hours)  # 最大15%改善
        else:
            improvement_ratio = 0.05
        
        current_score = 0.8
        estimated_new_score = min(0.95, current_score + improvement_ratio)
        
        print(f"   現在スコア: {current_score:.1%}")
        print(f"   推定改善後: {estimated_new_score:.1%}")
        print(f"   改善度: +{improvement_ratio:.1%}")
        
        return estimated_new_score
    
    def generate_phase1_report(self, result: IntegrityAnalysisResult):
        """Phase1分析レポート生成"""
        
        print("\n" + "="*60)
        print("Phase1: データ整合性改善分析レポート")
        print("="*60)
        
        print(f"\n【現状評価】")
        print(f"現在スコア: {result.current_score:.1%}")
        print(f"目標スコア: {result.target_score:.1%}")
        print(f"改善必要幅: {result.target_score - result.current_score:.1%}")
        
        print(f"\n【特定された問題】")
        print(f"総問題数: {len(result.identified_issues)}個")
        
        for issue in result.identified_issues:
            print(f"\n- {issue.issue_type}")
            print(f"  重要度: {issue.severity}")
            print(f"  内容: {issue.description}")
            print(f"  影響: {issue.impact_hours:.1f}時間")
            print(f"  推奨修正: {issue.suggested_fix}")
        
        print(f"\n【修正計画】")
        print("推奨実施順序:")
        for i, fix_type in enumerate(result.fix_priority, 1):
            print(f"{i}. {fix_type}")
        
        print(f"\n【改善見込み】")
        improvement = result.estimated_improvement - result.current_score
        print(f"推定改善後スコア: {result.estimated_improvement:.1%}")
        print(f"改善度: +{improvement:.1%}")
        
        if result.estimated_improvement >= result.target_score:
            print("\n[OK] 目標達成見込み: 高")
        else:
            print(f"\n[CAUTION] 追加改善が必要: {result.target_score - result.estimated_improvement:.1%}")

def main():
    """Phase1メイン実行"""
    
    analyzer = Phase1DataIntegrityAnalyzer()
    result = analyzer.execute_phase1_analysis()
    analyzer.generate_phase1_report(result)
    
    return result

if __name__ == "__main__":
    main()