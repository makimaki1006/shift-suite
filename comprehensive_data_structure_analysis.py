#!/usr/bin/env python3
"""
データ構造不整合の完全分析システム
専門的アプローチによる根本原因特定
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
sys.path.append('.')

@dataclass
class DataStructureAnalysis:
    """データ構造分析結果"""
    supply_roles: Dict[str, float]
    demand_roles: Dict[str, float] 
    mapping_matrix: pd.DataFrame
    unmapped_supply: Dict[str, float]
    unmapped_demand: Dict[str, float]
    integrity_gaps: List[Dict]

@dataclass
class MappingRule:
    """職種マッピングルール"""
    supply_role: str
    demand_role: str
    mapping_confidence: float
    mapping_rationale: str

class ComprehensiveDataStructureAnalyzer:
    """包括的データ構造分析器"""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        self.data_path = scenario_dir / 'intermediate_data.parquet'
        self.slot_hours = 0.5
        
    def execute_complete_analysis(self) -> DataStructureAnalysis:
        """完全データ構造分析実行"""
        
        print("=== 包括的データ構造分析開始 ===")
        
        # 1. 供給データの完全解析
        supply_analysis = self._analyze_supply_structure()
        
        # 2. 需要データの完全解析  
        demand_analysis = self._analyze_demand_structure()
        
        # 3. マッピング行列の構築
        mapping_matrix = self._build_mapping_matrix(supply_analysis, demand_analysis)
        
        # 4. 整合性ギャップの特定
        integrity_gaps = self._identify_integrity_gaps(supply_analysis, demand_analysis, mapping_matrix)
        
        # 5. 結果統合
        return DataStructureAnalysis(
            supply_roles=supply_analysis,
            demand_roles=demand_analysis,
            mapping_matrix=mapping_matrix,
            unmapped_supply=self._find_unmapped_supply(supply_analysis, mapping_matrix),
            unmapped_demand=self._find_unmapped_demand(demand_analysis, mapping_matrix),
            integrity_gaps=integrity_gaps
        )
    
    def _analyze_supply_structure(self) -> Dict[str, float]:
        """供給データ構造の完全解析"""
        
        print("1. 供給データ構造解析...")
        
        df = pd.read_parquet(self.data_path)
        working_data = df[df['holiday_type'].isin(['通常勤務', 'NORMAL'])]
        
        supply_roles = {}
        
        for role in working_data['role'].unique():
            role_records = working_data[working_data['role'] == role]
            role_hours = len(role_records) * self.slot_hours
            
            # 詳細分析
            role_analysis = {
                'total_hours': role_hours,
                'record_count': len(role_records),
                'staff_count': role_records['staff'].nunique(),
                'employment_types': role_records['employment'].unique().tolist(),
                'date_range': (role_records['ds'].min(), role_records['ds'].max()),
                'avg_hours_per_staff': role_hours / role_records['staff'].nunique() if role_records['staff'].nunique() > 0 else 0
            }
            
            supply_roles[role] = role_analysis
            
            print(f"   {role}: {role_hours:.1f}時間 ({len(role_records)}件, {role_records['staff'].nunique()}人)")
        
        return supply_roles
    
    def _analyze_demand_structure(self) -> Dict[str, float]:
        """需要データ構造の完全解析"""
        
        print("\n2. 需要データ構造解析...")
        
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        demand_roles = {}
        
        for need_file in need_files:
            try:
                need_df = pd.read_parquet(need_file)
                role_name = need_file.stem.split('_')[-1]
                
                # 需要値の詳細計算
                numeric_columns = need_df.select_dtypes(include=[np.number]).columns
                total_demand_slots = need_df[numeric_columns].sum().sum()
                total_demand_hours = total_demand_slots * self.slot_hours
                
                # 需要データの構造分析
                demand_analysis = {
                    'total_hours': total_demand_hours,
                    'total_slots': total_demand_slots,
                    'data_shape': need_df.shape,
                    'date_columns': [col for col in numeric_columns if self._is_date_column(col)],
                    'time_slots': len(numeric_columns),
                    'demand_density': total_demand_slots / (need_df.shape[0] * need_df.shape[1]) if need_df.shape[0] * need_df.shape[1] > 0 else 0
                }
                
                demand_roles[role_name] = demand_analysis
                
                print(f"   {role_name}: {total_demand_hours:.1f}時間 ({total_demand_slots:.0f}スロット, shape{need_df.shape})")
                
            except Exception as e:
                print(f"   {need_file.name}: 解析エラー - {e}")
                
        return demand_roles
    
    def _build_mapping_matrix(self, supply_analysis: Dict, demand_analysis: Dict) -> pd.DataFrame:
        """マッピング行列の構築"""
        
        print("\n3. マッピング行列構築...")
        
        supply_roles = list(supply_analysis.keys())
        demand_roles = list(demand_analysis.keys())
        
        # マッピング行列初期化
        mapping_matrix = pd.DataFrame(0.0, index=supply_roles, columns=demand_roles)
        
        # マッピングルールの適用
        mapping_rules = self._define_mapping_rules()
        
        for rule in mapping_rules:
            if rule.supply_role in supply_roles and rule.demand_role in demand_roles:
                mapping_matrix.loc[rule.supply_role, rule.demand_role] = rule.mapping_confidence
                print(f"   マッピング: {rule.supply_role} → {rule.demand_role} (信頼度: {rule.mapping_confidence:.2f})")
        
        return mapping_matrix
    
    def _define_mapping_rules(self) -> List[MappingRule]:
        """職種マッピングルールの定義"""
        
        return [
            # 完全一致マッピング
            MappingRule("介護", "介護", 1.0, "完全一致"),
            MappingRule("看護師", "看護師", 1.0, "完全一致"),
            MappingRule("機能訓練士", "機能訓練士", 1.0, "完全一致"),
            MappingRule("管理者・相談員", "管理者・相談員", 1.0, "完全一致"),
            
            # 部分一致マッピング
            MappingRule("介護福祉士", "介護", 0.9, "職種統合"),
            MappingRule("准看護師", "看護師", 0.8, "職種統合"),
            MappingRule("相談員/2名", "管理者・相談員", 0.7, "役割統合"),
            MappingRule("相談員/3名", "管理者・相談員", 0.7, "役割統合"),
            
            # 時間帯マッピング
            MappingRule("相談員/2名", "2名", 0.9, "時間帯対応"),
            MappingRule("相談員/3名", "3名", 0.9, "時間帯対応"),
            
            # 特殊勤務マッピング (NIGHT_SLOTは除外)
        ]
    
    def _identify_integrity_gaps(self, supply_analysis: Dict, demand_analysis: Dict, mapping_matrix: pd.DataFrame) -> List[Dict]:
        """整合性ギャップの特定"""
        
        print("\n4. 整合性ギャップ特定...")
        
        gaps = []
        
        # マッピング済みの計算
        mapped_supply_total = 0.0
        mapped_demand_total = 0.0
        
        for supply_role, supply_data in supply_analysis.items():
            if supply_role in mapping_matrix.index:
                mapped_demands = mapping_matrix.loc[supply_role]
                role_mapped_demand = 0.0
                
                for demand_role, confidence in mapped_demands.items():
                    if confidence > 0 and demand_role in demand_analysis:
                        role_mapped_demand += demand_analysis[demand_role]['total_hours'] * confidence
                
                mapped_supply_total += supply_data['total_hours']
                mapped_demand_total += role_mapped_demand
                
                # 職種レベルのギャップ
                role_gap = supply_data['total_hours'] - role_mapped_demand
                if abs(role_gap) > 0.1:
                    gaps.append({
                        'type': 'role_level_gap',
                        'role': supply_role,
                        'supply_hours': supply_data['total_hours'],
                        'demand_hours': role_mapped_demand,
                        'gap_hours': role_gap
                    })
        
        # 全体レベルのギャップ
        total_gap = mapped_supply_total - mapped_demand_total
        if abs(total_gap) > 0.1:
            gaps.append({
                'type': 'total_level_gap',
                'supply_total': mapped_supply_total,
                'demand_total': mapped_demand_total,
                'gap_hours': total_gap
            })
        
        print(f"   特定されたギャップ: {len(gaps)}個")
        
        return gaps
    
    def _find_unmapped_supply(self, supply_analysis: Dict, mapping_matrix: pd.DataFrame) -> Dict[str, float]:
        """未マッピング供給の特定"""
        
        unmapped = {}
        
        for role, data in supply_analysis.items():
            if role not in mapping_matrix.index:
                unmapped[role] = data['total_hours']
            elif mapping_matrix.loc[role].sum() == 0:
                unmapped[role] = data['total_hours']
        
        return unmapped
    
    def _find_unmapped_demand(self, demand_analysis: Dict, mapping_matrix: pd.DataFrame) -> Dict[str, float]:
        """未マッピング需要の特定"""
        
        unmapped = {}
        
        for role, data in demand_analysis.items():
            if role not in mapping_matrix.columns:
                unmapped[role] = data['total_hours']
            elif mapping_matrix[role].sum() == 0:
                unmapped[role] = data['total_hours']
        
        return unmapped
    
    def _is_date_column(self, column_name: str) -> bool:
        """日付カラム判定"""
        return '-' in str(column_name) or str(column_name).isdigit()
    
    def print_analysis_report(self, analysis: DataStructureAnalysis):
        """分析レポート出力"""
        
        print("\n" + "="*60)
        print("包括的データ構造分析レポート")
        print("="*60)
        
        # 供給データサマリー
        total_supply = sum([data['total_hours'] for data in analysis.supply_roles.values()])
        print(f"\n【供給データ】")
        print(f"総職種数: {len(analysis.supply_roles)}")
        print(f"総供給時間: {total_supply:.1f}時間")
        
        # 需要データサマリー
        total_demand = sum([data['total_hours'] for data in analysis.demand_roles.values()])
        print(f"\n【需要データ】")
        print(f"総職種数: {len(analysis.demand_roles)}")
        print(f"総需要時間: {total_demand:.1f}時間")
        
        # 未マッピングデータ
        unmapped_supply_total = sum(analysis.unmapped_supply.values())
        unmapped_demand_total = sum(analysis.unmapped_demand.values())
        
        print(f"\n【未マッピングデータ】")
        print(f"未マッピング供給: {unmapped_supply_total:.1f}時間")
        print(f"未マッピング需要: {unmapped_demand_total:.1f}時間")
        
        if analysis.unmapped_supply:
            print("未マッピング供給職種:")
            for role, hours in analysis.unmapped_supply.items():
                print(f"  - {role}: {hours:.1f}時間")
        
        if analysis.unmapped_demand:
            print("未マッピング需要職種:")
            for role, hours in analysis.unmapped_demand.items():
                print(f"  - {role}: {hours:.1f}時間")
        
        # 整合性ギャップ
        print(f"\n【整合性ギャップ】")
        print(f"特定されたギャップ: {len(analysis.integrity_gaps)}個")
        
        for gap in analysis.integrity_gaps:
            if gap['type'] == 'total_level_gap':
                print(f"全体レベル: {gap['gap_hours']:.1f}時間の差異")
            elif gap['type'] == 'role_level_gap':
                print(f"{gap['role']}: {gap['gap_hours']:.1f}時間の差異")
        
        # 修正必要性評価
        total_gap_hours = unmapped_supply_total - unmapped_demand_total
        print(f"\n【修正必要性評価】")
        print(f"推定総ギャップ: {total_gap_hours:.1f}時間")
        
        if abs(total_gap_hours) < 1:
            print("評価: 軽微な調整で解決可能")
        elif abs(total_gap_hours) < 10:
            print("評価: 中程度の修正が必要")
        else:
            print("評価: 重大な構造修正が必要")

def main():
    """メイン実行"""
    scenario_dir = Path('extracted_results/out_p25_based')
    
    analyzer = ComprehensiveDataStructureAnalyzer(scenario_dir)
    analysis_result = analyzer.execute_complete_analysis()
    analyzer.print_analysis_report(analysis_result)
    
    return analysis_result

if __name__ == "__main__":
    main()