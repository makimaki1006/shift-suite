#!/usr/bin/env python3
"""
統合職種マッピングシステム
完全対応関係構築による整合性保証
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
sys.path.append('.')

class MappingStrategy(Enum):
    EXACT_MATCH = "exact_match"
    SEMANTIC_MATCH = "semantic_match" 
    COMPOSITE_MATCH = "composite_match"
    SPECIAL_HANDLING = "special_handling"

@dataclass
class MappingRule:
    """高度マッピングルール"""
    supply_roles: List[str]
    demand_roles: List[str]
    mapping_strategy: MappingStrategy
    allocation_matrix: np.ndarray
    confidence_score: float
    business_rationale: str
    validation_method: str

@dataclass
class MappingResult:
    """マッピング結果"""
    mapped_pairs: Dict[str, Dict[str, float]]
    unmapped_supply: Dict[str, float]
    unmapped_demand: Dict[str, float]
    total_mapped_supply: float
    total_mapped_demand: float
    mapping_accuracy: float
    integrity_score: float

class IntegratedMappingSystem:
    """統合マッピングシステム"""
    
    def __init__(self):
        self.mapping_rules = self._define_comprehensive_mapping_rules()
        self.special_handling_rules = self._define_special_handling_rules()
        self.validation_threshold = 0.95
        
    def execute_complete_mapping(self, supply_data: Dict, demand_data: Dict) -> MappingResult:
        """完全マッピング実行"""
        
        print("=== 統合マッピングシステム実行 ===")
        
        # 1. 初期マッピング実行
        initial_mapping = self._execute_initial_mapping(supply_data, demand_data)
        
        # 2. 高度マッピング適用
        advanced_mapping = self._apply_advanced_mapping(initial_mapping, supply_data, demand_data)
        
        # 3. 特殊処理適用
        final_mapping = self._apply_special_handling(advanced_mapping, supply_data, demand_data)
        
        # 4. 整合性検証
        validated_mapping = self._validate_mapping_integrity(final_mapping, supply_data, demand_data)
        
        return validated_mapping
    
    def _define_comprehensive_mapping_rules(self) -> List[MappingRule]:
        """包括的マッピングルール定義"""
        
        rules = []
        
        # 1. 完全一致マッピング
        exact_matches = [
            (["介護"], ["介護"], "職種完全一致"),
            (["看護師"], ["看護師"], "職種完全一致"),  
            (["機能訓練士"], ["機能訓練士"], "職種完全一致"),
            (["管理者・相談員"], ["管理者・相談員"], "職種完全一致")
        ]
        
        for supply_roles, demand_roles, rationale in exact_matches:
            allocation_matrix = np.array([[1.0]])
            rules.append(MappingRule(
                supply_roles=supply_roles,
                demand_roles=demand_roles,
                mapping_strategy=MappingStrategy.EXACT_MATCH,
                allocation_matrix=allocation_matrix,
                confidence_score=1.0,
                business_rationale=rationale,
                validation_method="完全一致検証"
            ))
        
        # 2. 複合マッピング（相談員系）
        composite_mapping = MappingRule(
            supply_roles=["管理者・相談員"],
            demand_roles=["管理者・相談員", "2名", "3名"],
            mapping_strategy=MappingStrategy.COMPOSITE_MATCH,
            allocation_matrix=np.array([[0.7], [0.15], [0.15]]), # 時間帯配分
            confidence_score=0.85,
            business_rationale="相談員の時間帯別配分",
            validation_method="時間帯配分検証"
        )
        rules.append(composite_mapping)
        
        # 3. 意味的マッピング（介護系統合）
        semantic_mapping = MappingRule(
            supply_roles=["介護", "介護福祉士"],
            demand_roles=["介護"],
            mapping_strategy=MappingStrategy.SEMANTIC_MATCH,
            allocation_matrix=np.array([[1.0], [1.0]]),
            confidence_score=0.9,
            business_rationale="介護系職種統合",
            validation_method="職種統合検証"
        )
        rules.append(semantic_mapping)
        
        return rules
    
    def _define_special_handling_rules(self) -> Dict[str, Dict]:
        """特殊処理ルール定義"""
        
        return {
            "NIGHT_SLOT": {
                "handling_type": "separate_analysis",
                "reason": "夜間専用勤務区分",
                "calculation_method": "independent",
                "reporting_category": "special_shifts"
            },
            "相談員/2名": {
                "handling_type": "time_based_allocation", 
                "reason": "時間帯別配分",
                "allocation_target": "2名",
                "allocation_ratio": 1.0
            },
            "相談員/3名": {
                "handling_type": "time_based_allocation",
                "reason": "時間帯別配分", 
                "allocation_target": "3名",
                "allocation_ratio": 1.0
            }
        }
    
    def _execute_initial_mapping(self, supply_data: Dict, demand_data: Dict) -> Dict:
        """初期マッピング実行"""
        
        print("1. 初期マッピング実行...")
        
        mapping_matrix = {}
        
        for rule in self.mapping_rules:
            if rule.mapping_strategy == MappingStrategy.EXACT_MATCH:
                for i, supply_role in enumerate(rule.supply_roles):
                    if supply_role in supply_data:
                        for j, demand_role in enumerate(rule.demand_roles):
                            if demand_role in demand_data:
                                if supply_role not in mapping_matrix:
                                    mapping_matrix[supply_role] = {}
                                mapping_matrix[supply_role][demand_role] = rule.allocation_matrix[j, i] if rule.allocation_matrix.shape[0] > j and rule.allocation_matrix.shape[1] > i else 1.0
                                
                                print(f"   マッピング確立: {supply_role} → {demand_role}")
        
        return mapping_matrix
    
    def _apply_advanced_mapping(self, initial_mapping: Dict, supply_data: Dict, demand_data: Dict) -> Dict:
        """高度マッピング適用"""
        
        print("2. 高度マッピング適用...")
        
        advanced_mapping = initial_mapping.copy()
        
        # 複合マッピングの適用
        for rule in self.mapping_rules:
            if rule.mapping_strategy == MappingStrategy.COMPOSITE_MATCH:
                self._apply_composite_mapping(advanced_mapping, rule, supply_data, demand_data)
            elif rule.mapping_strategy == MappingStrategy.SEMANTIC_MATCH:
                self._apply_semantic_mapping(advanced_mapping, rule, supply_data, demand_data)
        
        return advanced_mapping
    
    def _apply_composite_mapping(self, mapping: Dict, rule: MappingRule, supply_data: Dict, demand_data: Dict):
        """複合マッピング適用"""
        
        for supply_role in rule.supply_roles:
            if supply_role in supply_data:
                if supply_role not in mapping:
                    mapping[supply_role] = {}
                
                for i, demand_role in enumerate(rule.demand_roles):
                    if demand_role in demand_data:
                        allocation_ratio = rule.allocation_matrix[i, 0] if i < rule.allocation_matrix.shape[0] else 0.0
                        mapping[supply_role][demand_role] = allocation_ratio
                        
                        print(f"   複合マッピング: {supply_role} → {demand_role} (比率: {allocation_ratio:.2f})")
    
    def _apply_semantic_mapping(self, mapping: Dict, rule: MappingRule, supply_data: Dict, demand_data: Dict):
        """意味的マッピング適用"""
        
        for i, supply_role in enumerate(rule.supply_roles):
            if supply_role in supply_data:
                if supply_role not in mapping:
                    mapping[supply_role] = {}
                
                for j, demand_role in enumerate(rule.demand_roles):
                    if demand_role in demand_data:
                        allocation_ratio = rule.allocation_matrix[i, 0] if i < rule.allocation_matrix.shape[0] else 1.0
                        mapping[supply_role][demand_role] = allocation_ratio
                        
                        print(f"   意味的マッピング: {supply_role} → {demand_role} (統合)")
    
    def _apply_special_handling(self, mapping: Dict, supply_data: Dict, demand_data: Dict) -> Dict:
        """特殊処理適用"""
        
        print("3. 特殊処理適用...")
        
        special_mapping = mapping.copy()
        special_categories = {}
        
        for role, rule in self.special_handling_rules.items():
            if role in supply_data:
                if rule["handling_type"] == "separate_analysis":
                    # 特殊勤務として分離
                    special_categories[role] = {
                        "supply_hours": supply_data[role]['total_hours'],
                        "demand_hours": 0.0,  # 専用需要なし
                        "category": rule["reporting_category"],
                        "analysis_method": rule["calculation_method"]
                    }
                    print(f"   特殊処理: {role} → 分離分析 ({rule['reason']})")
                
                elif rule["handling_type"] == "time_based_allocation":
                    # 時間帯別配分
                    target_demand = rule["allocation_target"]
                    if target_demand in demand_data and role in supply_data:
                        if role not in special_mapping:
                            special_mapping[role] = {}
                        special_mapping[role][target_demand] = rule["allocation_ratio"]
                        print(f"   時間帯配分: {role} → {target_demand}")
        
        return special_mapping
    
    def _validate_mapping_integrity(self, mapping: Dict, supply_data: Dict, demand_data: Dict) -> MappingResult:
        """マッピング整合性検証"""
        
        print("4. マッピング整合性検証...")
        
        # マッピング済み供給・需要の計算
        total_mapped_supply = 0.0
        total_mapped_demand = 0.0
        mapped_pairs = {}
        
        for supply_role, demand_mappings in mapping.items():
            if supply_role in supply_data:
                supply_hours = supply_data[supply_role]['total_hours']
                mapped_pairs[supply_role] = {}
                
                for demand_role, allocation_ratio in demand_mappings.items():
                    if demand_role in demand_data:
                        allocated_demand = demand_data[demand_role]['total_hours'] * allocation_ratio
                        mapped_pairs[supply_role][demand_role] = allocated_demand
                        total_mapped_demand += allocated_demand
                
                total_mapped_supply += supply_hours
        
        # 未マッピングの特定
        unmapped_supply = {}
        unmapped_demand = {}
        
        for role, data in supply_data.items():
            if role not in mapping and role != 'NIGHT_SLOT':  # 特殊処理除外
                unmapped_supply[role] = data['total_hours']
        
        for role, data in demand_data.items():
            is_mapped = any(role in demand_mappings for demand_mappings in mapping.values())
            if not is_mapped:
                unmapped_demand[role] = data['total_hours']
        
        # 精度計算
        total_supply = sum(data['total_hours'] for data in supply_data.values())
        total_demand = sum(data['total_hours'] for data in demand_data.values())
        
        mapping_accuracy = (total_mapped_supply + total_mapped_demand) / (total_supply + total_demand) if (total_supply + total_demand) > 0 else 0.0
        integrity_score = 1.0 - abs(total_mapped_supply - total_mapped_demand) / max(total_mapped_supply, total_mapped_demand) if max(total_mapped_supply, total_mapped_demand) > 0 else 0.0
        
        result = MappingResult(
            mapped_pairs=mapped_pairs,
            unmapped_supply=unmapped_supply,
            unmapped_demand=unmapped_demand,
            total_mapped_supply=total_mapped_supply,
            total_mapped_demand=total_mapped_demand,
            mapping_accuracy=mapping_accuracy,
            integrity_score=integrity_score
        )
        
        # 検証結果出力
        print(f"   マッピング精度: {mapping_accuracy:.2%}")
        print(f"   整合性スコア: {integrity_score:.2%}")
        print(f"   マッピング済み供給: {total_mapped_supply:.1f}時間")
        print(f"   マッピング済み需要: {total_mapped_demand:.1f}時間")
        print(f"   差分: {abs(total_mapped_supply - total_mapped_demand):.1f}時間")
        
        return result

def test_integrated_mapping():
    """統合マッピングシステムのテスト"""
    
    # データ構造分析結果の読み込み
    sys.path.append('.')
    from comprehensive_data_structure_analysis import ComprehensiveDataStructureAnalyzer
    
    scenario_dir = Path('extracted_results/out_p25_based')
    analyzer = ComprehensiveDataStructureAnalyzer(scenario_dir)
    analysis_result = analyzer.execute_complete_analysis()
    
    # 統合マッピング実行
    mapping_system = IntegratedMappingSystem()
    mapping_result = mapping_system.execute_complete_mapping(
        analysis_result.supply_roles, 
        analysis_result.demand_roles
    )
    
    # 結果レポート
    print("\n" + "="*60)
    print("統合マッピングシステム実行結果")
    print("="*60)
    
    print(f"マッピング精度: {mapping_result.mapping_accuracy:.1%}")
    print(f"整合性スコア: {mapping_result.integrity_score:.1%}")
    print(f"残存未マッピング供給: {sum(mapping_result.unmapped_supply.values()):.1f}時間")
    print(f"残存未マッピング需要: {sum(mapping_result.unmapped_demand.values()):.1f}時間")
    
    return mapping_result

if __name__ == "__main__":
    test_integrated_mapping()