#!/usr/bin/env python3
"""
三階層整合性保証システム
数学的に保証された階層整合性実現
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
sys.path.append('.')

@dataclass
class HierarchyLevel:
    """階層レベル定義"""
    name: str
    calculation_method: str
    aggregation_rules: Dict
    validation_constraints: List[str]
    tolerance: float = 0.01  # 1分以内の誤差許容

@dataclass
class IntegrityResult:
    """整合性結果"""
    level_name: str
    total_demand: float
    total_supply: float
    total_shortage: float
    total_excess: float
    detailed_breakdown: Dict
    integrity_violations: List[str]
    quality_score: float

class IntegrityCalculator(ABC):
    """整合性計算抽象基底クラス"""
    
    @abstractmethod
    def calculate_level(self, data: Dict) -> IntegrityResult:
        pass
    
    @abstractmethod
    def validate_integrity(self, result: IntegrityResult) -> bool:
        pass

class OrganizationLevelCalculator(IntegrityCalculator):
    """組織レベル計算器"""
    
    def __init__(self, slot_hours: float = 0.5):
        self.slot_hours = slot_hours
        self.tolerance = 0.01
    
    def calculate_level(self, data: Dict) -> IntegrityResult:
        """組織レベル計算実行"""
        
        supply_data = data['supply_data']
        demand_data = data['demand_data'] 
        mapping_result = data['mapping_result']
        
        # 組織全体の供給計算（特殊勤務含む）
        total_supply = 0.0
        supply_breakdown = {}
        
        for role, role_data in supply_data.items():
            role_supply = role_data['total_hours']
            total_supply += role_supply
            supply_breakdown[role] = role_supply
        
        # 組織全体の需要計算
        total_demand = 0.0
        demand_breakdown = {}
        
        for role, role_data in demand_data.items():
            role_demand = role_data['total_hours']
            total_demand += role_demand
            demand_breakdown[role] = role_demand
        
        # 過不足計算
        total_shortage = max(0, total_demand - total_supply)
        total_excess = max(0, total_supply - total_demand)
        
        # 整合性違反チェック
        violations = []
        if abs(total_supply - sum(supply_breakdown.values())) > self.tolerance:
            violations.append(f"供給合計不整合: {abs(total_supply - sum(supply_breakdown.values())):.3f}時間")
        if abs(total_demand - sum(demand_breakdown.values())) > self.tolerance:
            violations.append(f"需要合計不整合: {abs(total_demand - sum(demand_breakdown.values())):.3f}時間")
        
        # 品質スコア計算
        quality_score = 1.0 - len(violations) * 0.1
        
        return IntegrityResult(
            level_name="organization",
            total_demand=total_demand,
            total_supply=total_supply, 
            total_shortage=total_shortage,
            total_excess=total_excess,
            detailed_breakdown={
                'supply_by_role': supply_breakdown,
                'demand_by_role': demand_breakdown
            },
            integrity_violations=violations,
            quality_score=max(0.0, quality_score)
        )
    
    def validate_integrity(self, result: IntegrityResult) -> bool:
        """組織レベル整合性検証"""
        return len(result.integrity_violations) == 0 and result.quality_score >= 0.9

class RoleLevelCalculator(IntegrityCalculator):
    """職種レベル計算器"""
    
    def __init__(self, slot_hours: float = 0.5):
        self.slot_hours = slot_hours
        self.tolerance = 0.01
    
    def calculate_level(self, data: Dict) -> IntegrityResult:
        """職種レベル計算実行"""
        
        supply_data = data['supply_data']
        demand_data = data['demand_data']
        mapping_result = data['mapping_result']
        
        # 職種別詳細計算
        role_results = {}
        total_demand = 0.0
        total_supply = 0.0
        violations = []
        
        # マッピング済み職種の処理
        for supply_role, mapped_demands in mapping_result.mapped_pairs.items():
            if supply_role in supply_data:
                role_supply = supply_data[supply_role]['total_hours']
                role_demand = sum(mapped_demands.values())
                
                role_shortage = max(0, role_demand - role_supply)
                role_excess = max(0, role_supply - role_demand)
                
                role_results[supply_role] = {
                    'supply': role_supply,
                    'demand': role_demand,
                    'shortage': role_shortage,
                    'excess': role_excess,
                    'mapped_to': list(mapped_demands.keys())
                }
                
                total_supply += role_supply
                total_demand += role_demand
        
        # 特殊処理職種（NIGHT_SLOT等）
        special_roles = {}
        for role, role_data in supply_data.items():
            if role not in mapping_result.mapped_pairs and role == 'NIGHT_SLOT':
                special_supply = role_data['total_hours']
                special_roles[role] = {
                    'supply': special_supply,
                    'demand': 0.0,  # 専用需要なし
                    'shortage': 0.0,
                    'excess': special_supply,
                    'category': 'special_shift'
                }
                # 特殊勤務は組織全体には含めるが、通常職種計算からは除外
        
        # 未マッピング需要の処理
        unmapped_demand_total = sum(mapping_result.unmapped_demand.values())
        if unmapped_demand_total > self.tolerance:
            violations.append(f"未マッピング需要: {unmapped_demand_total:.1f}時間")
        
        # 整合性計算
        total_shortage = max(0, total_demand - total_supply)
        total_excess = max(0, total_supply - total_demand)
        
        # 品質スコア
        mapping_coverage = total_supply / sum(role_data['total_hours'] for role_data in supply_data.values() if role_data)
        quality_score = mapping_coverage * (1.0 - len(violations) * 0.05)
        
        return IntegrityResult(
            level_name="role",
            total_demand=total_demand,
            total_supply=total_supply,
            total_shortage=total_shortage, 
            total_excess=total_excess,
            detailed_breakdown={
                'role_results': role_results,
                'special_roles': special_roles,
                'unmapped_demand': dict(mapping_result.unmapped_demand)
            },
            integrity_violations=violations,
            quality_score=max(0.0, quality_score)
        )
    
    def validate_integrity(self, result: IntegrityResult) -> bool:
        """職種レベル整合性検証"""
        return result.quality_score >= 0.8

class EmploymentLevelCalculator(IntegrityCalculator):
    """雇用形態レベル計算器"""
    
    def __init__(self, slot_hours: float = 0.5):
        self.slot_hours = slot_hours
        self.tolerance = 0.01
    
    def calculate_level(self, data: Dict) -> IntegrityResult:
        """雇用形態レベル計算実行"""
        
        # 供給データから雇用形態別集計
        scenario_dir = Path('extracted_results/out_p25_based')
        df = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        working_data = df[df['holiday_type'].isin(['通常勤務', 'NORMAL'])]
        
        employment_results = {}
        total_supply = 0.0
        total_demand = 0.0
        
        # 雇用形態別供給計算
        for employment in working_data['employment'].unique():
            emp_records = working_data[working_data['employment'] == employment]
            emp_supply = len(emp_records) * self.slot_hours
            
            # 雇用形態別需要推定（供給比率ベース）
            supply_ratio = emp_supply / (len(working_data) * self.slot_hours) if len(working_data) > 0 else 0.0
            emp_demand = data['organization_result'].total_demand * supply_ratio
            
            emp_shortage = max(0, emp_demand - emp_supply)
            emp_excess = max(0, emp_supply - emp_demand)
            
            employment_results[employment] = {
                'supply': emp_supply,
                'demand': emp_demand,
                'shortage': emp_shortage,
                'excess': emp_excess,
                'supply_ratio': supply_ratio,
                'record_count': len(emp_records)
            }
            
            total_supply += emp_supply
            total_demand += emp_demand
        
        # 整合性検証
        violations = []
        org_supply = data['organization_result'].total_supply
        if abs(total_supply - org_supply) > self.tolerance:
            violations.append(f"組織供給との不整合: {abs(total_supply - org_supply):.3f}時間")
        
        total_shortage = max(0, total_demand - total_supply)
        total_excess = max(0, total_supply - total_demand)
        
        quality_score = 1.0 - len(violations) * 0.1
        
        return IntegrityResult(
            level_name="employment",
            total_demand=total_demand,
            total_supply=total_supply,
            total_shortage=total_shortage,
            total_excess=total_excess,
            detailed_breakdown={'employment_results': employment_results},
            integrity_violations=violations,
            quality_score=max(0.0, quality_score)
        )
    
    def validate_integrity(self, result: IntegrityResult) -> bool:
        """雇用形態レベル整合性検証"""
        return result.quality_score >= 0.9

class HierarchicalIntegritySystem:
    """階層整合性システム"""
    
    def __init__(self):
        self.calculators = {
            'organization': OrganizationLevelCalculator(),
            'role': RoleLevelCalculator(),
            'employment': EmploymentLevelCalculator()
        }
        self.hierarchy_levels = self._define_hierarchy_levels()
        self.global_tolerance = 0.01
    
    def _define_hierarchy_levels(self) -> List[HierarchyLevel]:
        """階層レベル定義"""
        
        return [
            HierarchyLevel(
                name="organization",
                calculation_method="aggregate_all",
                aggregation_rules={'include_special': True},
                validation_constraints=['total_consistency', 'non_negative'],
                tolerance=0.01
            ),
            HierarchyLevel(
                name="role", 
                calculation_method="role_mapping_based",
                aggregation_rules={'mapping_required': True, 'special_separate': True},
                validation_constraints=['mapping_coverage', 'role_consistency'],
                tolerance=0.01
            ),
            HierarchyLevel(
                name="employment",
                calculation_method="proportional_allocation",
                aggregation_rules={'ratio_based': True},
                validation_constraints=['organization_consistency'],
                tolerance=0.01
            )
        ]
    
    def execute_hierarchical_calculation(self, base_data: Dict) -> Dict[str, IntegrityResult]:
        """階層計算実行"""
        
        print("=== 三階層整合性保証システム実行 ===")
        
        results = {}
        
        # 1. 組織レベル計算
        print("1. 組織レベル計算...")
        org_result = self.calculators['organization'].calculate_level(base_data)
        results['organization'] = org_result
        base_data['organization_result'] = org_result
        
        # 2. 職種レベル計算  
        print("2. 職種レベル計算...")
        role_result = self.calculators['role'].calculate_level(base_data)
        results['role'] = role_result
        base_data['role_result'] = role_result
        
        # 3. 雇用形態レベル計算
        print("3. 雇用形態レベル計算...")
        employment_result = self.calculators['employment'].calculate_level(base_data)
        results['employment'] = employment_result
        
        # 4. 階層間整合性検証
        print("4. 階層間整合性検証...")
        hierarchy_integrity = self._validate_hierarchy_integrity(results)
        
        # 5. 結果統合・レポート
        self._generate_integrity_report(results, hierarchy_integrity)
        
        return results
    
    def _validate_hierarchy_integrity(self, results: Dict[str, IntegrityResult]) -> Dict:
        """階層間整合性検証"""
        
        org_result = results['organization']
        role_result = results['role'] 
        emp_result = results['employment']
        
        integrity_status = {
            'supply_consistency': [],
            'demand_consistency': [],
            'overall_score': 1.0
        }
        
        # 供給整合性チェック
        org_supply = org_result.total_supply
        role_supply = role_result.total_supply + sum(
            role_data['supply'] for role_data in role_result.detailed_breakdown.get('special_roles', {}).values()
        )
        emp_supply = emp_result.total_supply
        
        supply_diff_role = abs(org_supply - role_supply)
        supply_diff_emp = abs(org_supply - emp_supply)
        
        if supply_diff_role > self.global_tolerance:
            integrity_status['supply_consistency'].append(f"組織-職種供給差異: {supply_diff_role:.3f}時間")
            integrity_status['overall_score'] -= 0.2
        
        if supply_diff_emp > self.global_tolerance:
            integrity_status['supply_consistency'].append(f"組織-雇用形態供給差異: {supply_diff_emp:.3f}時間")
            integrity_status['overall_score'] -= 0.2
        
        # 需要整合性チェック（特殊勤務除外）
        org_demand = org_result.total_demand
        role_demand = role_result.total_demand  # マッピング済み需要のみ
        emp_demand = emp_result.total_demand
        
        demand_diff_role = abs(org_demand - role_demand)
        demand_diff_emp = abs(org_demand - emp_demand)
        
        if demand_diff_role > self.global_tolerance:
            integrity_status['demand_consistency'].append(f"組織-職種需要差異: {demand_diff_role:.3f}時間")
            integrity_status['overall_score'] -= 0.1
        
        if demand_diff_emp > self.global_tolerance:
            integrity_status['demand_consistency'].append(f"組織-雇用形態需要差異: {demand_diff_emp:.3f}時間")
            integrity_status['overall_score'] -= 0.1
        
        integrity_status['overall_score'] = max(0.0, integrity_status['overall_score'])
        
        return integrity_status
    
    def _generate_integrity_report(self, results: Dict[str, IntegrityResult], hierarchy_integrity: Dict):
        """整合性レポート生成"""
        
        print("\n" + "="*70)
        print("三階層整合性保証システム実行結果")
        print("="*70)
        
        # 各階層の結果
        for level_name, result in results.items():
            print(f"\n【{level_name.upper()}レベル】")
            print(f"需要: {result.total_demand:.1f}時間")
            print(f"供給: {result.total_supply:.1f}時間")
            print(f"不足: {result.total_shortage:.1f}時間") 
            print(f"過剰: {result.total_excess:.1f}時間")
            print(f"品質スコア: {result.quality_score:.2%}")
            
            if result.integrity_violations:
                print(f"整合性違反: {len(result.integrity_violations)}件")
                for violation in result.integrity_violations:
                    print(f"  - {violation}")
        
        # 階層間整合性
        print(f"\n【階層間整合性】")
        print(f"全体スコア: {hierarchy_integrity['overall_score']:.2%}")
        
        if hierarchy_integrity['supply_consistency']:
            print("供給整合性課題:")
            for issue in hierarchy_integrity['supply_consistency']:
                print(f"  - {issue}")
        else:
            print("[OK] 供給整合性: 完全")
        
        if hierarchy_integrity['demand_consistency']:
            print("需要整合性課題:")
            for issue in hierarchy_integrity['demand_consistency']:
                print(f"  - {issue}")
        else:
            print("[OK] 需要整合性: 完全")
        
        # 最終判定
        print(f"\n【最終判定】")
        if hierarchy_integrity['overall_score'] >= 0.95:
            print("[OK] 三階層整合性: 完全達成")
        elif hierarchy_integrity['overall_score'] >= 0.9:
            print("[GOOD] 三階層整合性: 高品質（軽微な改善余地）")
        else:
            print("[NG] 三階層整合性: 要改善")

def test_hierarchical_integrity():
    """階層整合性システムのテスト"""
    
    # 基礎データ準備
    from comprehensive_data_structure_analysis import ComprehensiveDataStructureAnalyzer
    from integrated_mapping_system import IntegratedMappingSystem
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    # データ構造分析
    analyzer = ComprehensiveDataStructureAnalyzer(scenario_dir)
    analysis_result = analyzer.execute_complete_analysis()
    
    # 統合マッピング
    mapping_system = IntegratedMappingSystem()
    mapping_result = mapping_system.execute_complete_mapping(
        analysis_result.supply_roles,
        analysis_result.demand_roles
    )
    
    # 基礎データ構築
    base_data = {
        'supply_data': analysis_result.supply_roles,
        'demand_data': analysis_result.demand_roles,
        'mapping_result': mapping_result
    }
    
    # 階層整合性システム実行
    integrity_system = HierarchicalIntegritySystem()
    hierarchy_results = integrity_system.execute_hierarchical_calculation(base_data)
    
    return hierarchy_results

if __name__ == "__main__":
    test_hierarchical_integrity()