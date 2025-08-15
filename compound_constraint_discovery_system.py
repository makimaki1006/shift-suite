#!/usr/bin/env python3
"""
複合制約発見システム - 複数ファイルから統合的制約発見を実行
高度意図発見と制約昇華を複数ファイルで統合実行
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter
from dataclasses import dataclass, asdict
from enum import Enum

# 既存システムをインポート
try:
    from advanced_constraint_discovery_engine import (
        AdvancedIntentionDiscovery,
        ConstraintElevationEngine,
        ConstraintRule, ConstraintType, ConstraintAxis
    )
    from direct_excel_reader import DirectExcelReader, ShiftPatternAnalyzer
except ImportError as e:
    print(f"必要なモジュールがインポートできません: {e}")
    sys.exit(1)

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class CompoundConstraintDiscoverySystem:
    """複合制約発見システム - 複数ファイル統合分析"""
    
    def __init__(self):
        self.system_name = "複合制約発見システム"
        self.version = "3.0.0"
        
        # コンポーネント初期化
        self.reader = DirectExcelReader()
        self.analyzer = ShiftPatternAnalyzer()
        self.intention_engine = AdvancedIntentionDiscovery()
        self.constraint_engine = ConstraintElevationEngine()
        
        # 結果格納
        self.all_constraint_rules = []
        self.all_patterns = {}
        self.processed_files = []
        self.file_analysis_stats = {}
    
    def discover_compound_constraints(self, excel_directory: str = ".") -> Dict[str, Any]:
        """複合制約発見のメインエントリーポイント"""
        print("=" * 80)
        print(f"{self.system_name} v{self.version} - 複数ファイル統合制約発見")
        print("=" * 80)
        
        # Phase 1: ファイル検索と前処理
        excel_files = self._discover_excel_files(excel_directory)
        if not excel_files:
            print("[ERROR] 分析対象のExcelファイルが見つかりません")
            return {}
        
        print(f"発見されたExcelファイル: {len(excel_files)}個")
        for i, f in enumerate(excel_files, 1):
            print(f"  {i}. {f.name} ({f.stat().st_size:,}バイト)")
        
        # Phase 2: 各ファイルの制約発見
        print(f"\n{'='*60}")
        print("Phase 2: 個別ファイル制約発見")
        print(f"{'='*60}")
        
        for excel_file in excel_files:
            self._process_single_file(excel_file)
        
        # Phase 3: 複合パターン分析
        print(f"\n{'='*60}")
        print(f"Phase 3: 複合パターン分析")
        print(f"{'='*60}")
        
        compound_patterns = self._analyze_compound_patterns()
        
        # Phase 4: 統合制約生成
        print(f"\n{'='*60}")
        print("Phase 4: 統合制約生成")
        print(f"{'='*60}")
        
        integrated_constraints = self._generate_integrated_constraints(compound_patterns)
        
        # Phase 5: 結果統合とレポート生成
        final_report = self._generate_comprehensive_report(integrated_constraints)
        
        return final_report
    
    def _discover_excel_files(self, directory: str) -> List[Path]:
        """Excelファイル発見"""
        path = Path(directory)
        excel_files = list(path.glob("*.xlsx"))
        
        # 一時ファイルやバックアップファイルを除外
        filtered_files = []
        for f in excel_files:
            if not f.name.startswith('~') and not f.name.endswith('.tmp'):
                filtered_files.append(f)
        
        # ファイルサイズでソート（大きいファイルから）
        return sorted(filtered_files, key=lambda x: x.stat().st_size, reverse=True)
    
    def _process_single_file(self, excel_file: Path) -> bool:
        """単一ファイルの制約発見処理"""
        print(f"\n--- 分析中: {excel_file.name} ---")
        
        try:
            # Excel読み込み
            data = self.reader.read_xlsx_as_zip(str(excel_file))
            if not data:
                print(f"[SKIP] データ読み込み失敗: {excel_file.name}")
                return False
            
            # パターン分析
            patterns = self.analyzer.analyze_raw_data(data)
            if not patterns.get("staff_shifts"):
                print(f"[SKIP] スタッフデータなし: {excel_file.name}")
                return False
            
            # 深層パターン発見
            deep_patterns = self.intention_engine.discover_deep_patterns(data)
            
            # 制約昇華
            constraint_rules = self.constraint_engine.elevate_to_constraints(deep_patterns)
            
            # 結果蓄積
            self.all_constraint_rules.extend(constraint_rules)
            self.all_patterns[str(excel_file)] = patterns
            self.processed_files.append(excel_file.name)
            
            # ファイル統計記録
            self.file_analysis_stats[excel_file.name] = {
                "staff_count": len(patterns.get("staff_shifts", {})),
                "shift_codes": len(patterns.get("shift_codes", set())),
                "constraint_rules": len(constraint_rules),
                "implicit_rules": len(patterns.get("implicit_rules", [])),
                "file_size": excel_file.stat().st_size
            }
            
            print(f"[OK] {excel_file.name}: {len(constraint_rules)}個の制約発見")
            print(f"     スタッフ: {len(patterns.get('staff_shifts', {}))}名")
            print(f"     シフトコード: {len(patterns.get('shift_codes', set()))}種類")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] {excel_file.name}: {e}")
            return False
    
    def _analyze_compound_patterns(self) -> Dict[str, Any]:
        """複合パターン分析 - ファイル間共通性の発見"""
        if not self.processed_files:
            return {}
        
        print(f"複合パターン分析開始: {len(self.processed_files)}ファイル")
        
        compound_patterns = {
            "cross_file_staff_patterns": {},
            "universal_shift_codes": {},
            "constraint_consistency": {},
            "organizational_constants": {}
        }
        
        # ファイル間スタッフ分析
        staff_appearances = {}
        for file_path, patterns in self.all_patterns.items():
            for staff_name in patterns.get("staff_shifts", {}):
                if staff_name not in staff_appearances:
                    staff_appearances[staff_name] = []
                staff_appearances[staff_name].append(file_path)
        
        # 複数ファイル登場スタッフ
        cross_file_staff = {
            name: files for name, files in staff_appearances.items() 
            if len(files) > 1
        }
        compound_patterns["cross_file_staff_patterns"] = cross_file_staff
        
        # 共通シフトコード分析
        shift_code_frequency = {}
        for patterns in self.all_patterns.values():
            for code in patterns.get("shift_codes", set()):
                shift_code_frequency[code] = shift_code_frequency.get(code, 0) + 1
        
        universal_codes = {
            code: freq for code, freq in shift_code_frequency.items() 
            if freq >= len(self.processed_files) * 0.5  # 50%以上のファイルに登場
        }
        compound_patterns["universal_shift_codes"] = universal_codes
        
        # 制約一貫性分析
        constraint_rule_patterns = {}
        for rule in self.all_constraint_rules:
            pattern_key = f"{rule.constraint_type.value}_{rule.axis.value}"
            if pattern_key not in constraint_rule_patterns:
                constraint_rule_patterns[pattern_key] = []
            constraint_rule_patterns[pattern_key].append(rule)
        
        compound_patterns["constraint_consistency"] = {
            pattern: len(rules) for pattern, rules in constraint_rule_patterns.items()
        }
        
        print(f"複合パターン発見:")
        print(f"  - 複数ファイル登場スタッフ: {len(cross_file_staff)}名")
        print(f"  - 共通シフトコード: {len(universal_codes)}種類")
        print(f"  - 制約パターン: {len(constraint_rule_patterns)}種類")
        
        return compound_patterns
    
    def _generate_integrated_constraints(self, compound_patterns: Dict[str, Any]) -> List[ConstraintRule]:
        """統合制約生成 - 複数ファイル情報から強化制約を生成"""
        print("統合制約生成開始")
        
        integrated_constraints = []
        
        # 既存制約の強化（複数ファイルで同様パターンが見つかった場合）
        staff_constraint_strengthening = {}
        
        # スタッフごとの制約強化分析
        for rule in self.all_constraint_rules:
            if rule.axis == ConstraintAxis.STAFF_AXIS:
                # ルールからスタッフ名を抽出
                staff_match = rule.condition.split("==")[1].strip(" '")
                
                if staff_match not in staff_constraint_strengthening:
                    staff_constraint_strengthening[staff_match] = []
                staff_constraint_strengthening[staff_match].append(rule)
        
        # 複数ファイルで一貫性のあるスタッフ制約を強化
        for staff_name, rules in staff_constraint_strengthening.items():
            if len(rules) > 1:  # 複数制約が存在
                # 制約の一貫性チェック
                consistent_rules = self._find_consistent_rules(rules)
                
                if consistent_rules:
                    # 強化制約生成
                    enhanced_rule = self._create_enhanced_constraint(
                        staff_name, consistent_rules, compound_patterns
                    )
                    if enhanced_rule:
                        integrated_constraints.append(enhanced_rule)
        
        # 組織レベル制約生成
        organizational_constraints = self._generate_organizational_constraints(compound_patterns)
        integrated_constraints.extend(organizational_constraints)
        
        print(f"統合制約生成完了: {len(integrated_constraints)}個の強化制約")
        
        return integrated_constraints
    
    def _find_consistent_rules(self, rules: List[ConstraintRule]) -> List[ConstraintRule]:
        """一貫性のある制約ルールを発見"""
        # アクションパターンでグループ化
        action_groups = {}
        for rule in rules:
            action_key = rule.action.split("(")[0].strip()  # 括弧前の部分でグループ化
            if action_key not in action_groups:
                action_groups[action_key] = []
            action_groups[action_key].append(rule)
        
        # 最も多いアクションパターンを採用
        if action_groups:
            most_common_action = max(action_groups, key=lambda k: len(action_groups[k]))
            return action_groups[most_common_action]
        
        return []
    
    def _create_enhanced_constraint(self, staff_name: str, rules: List[ConstraintRule], 
                                  compound_patterns: Dict[str, Any]) -> Optional[ConstraintRule]:
        """強化制約作成"""
        if not rules:
            return None
        
        # 確信度平均値計算
        avg_confidence = sum(r.confidence for r in rules) / len(rules)
        avg_measurement = sum(r.measurement for r in rules) / len(rules)
        
        # 複数ファイルでの一貫性により制約タイプを強化
        if len(rules) >= 3:  # 3ファイル以上で同じパターン
            constraint_type = ConstraintType.STATIC_HARD
            violation_penalty = "ERROR: 複数ファイル一貫性違反"
        elif len(rules) >= 2:
            constraint_type = ConstraintType.STATIC_SOFT
            violation_penalty = "WARNING: ファイル間不整合"
        else:
            constraint_type = ConstraintType.DYNAMIC_SOFT
            violation_penalty = "INFO: 一般的制約"
        
        # 共通アクション決定
        base_rule = rules[0]
        enhanced_action = f"{base_rule.action} [複数ファイル確認済み: {len(rules)}ファイル]"
        
        enhanced_rule = ConstraintRule(
            rule_id=f"ENHANCED_{staff_name}_{len(rules)}FILES",
            constraint_type=constraint_type,
            axis=ConstraintAxis.STAFF_AXIS,
            condition=f"スタッフ == '{staff_name}'",
            action=enhanced_action,
            confidence=avg_confidence,
            evidence={
                "file_consistency_count": len(rules),
                "evidence_rules": [r.rule_id for r in rules],
                "avg_measurement": avg_measurement,
                "consistency_strength": "HIGH" if len(rules) >= 3 else "MEDIUM"
            },
            measurement=avg_measurement,
            violation_penalty=violation_penalty
        )
        
        return enhanced_rule
    
    def _generate_organizational_constraints(self, compound_patterns: Dict[str, Any]) -> List[ConstraintRule]:
        """組織レベル制約生成"""
        org_constraints = []
        
        # 共通シフトコード制約
        for shift_code, frequency in compound_patterns.get("universal_shift_codes", {}).items():
            if frequency >= len(self.processed_files):  # 全ファイルに登場
                rule = ConstraintRule(
                    rule_id=f"ORG_UNIVERSAL_{shift_code}",
                    constraint_type=ConstraintType.STATIC_SOFT,
                    axis=ConstraintAxis.TASK_AXIS,
                    condition=f"組織運用 == '全体'",
                    action=f"'{shift_code}'シフトを標準運用として維持",
                    confidence=1.0,
                    evidence={
                        "file_coverage": frequency,
                        "universality": "COMPLETE"
                    },
                    measurement=100.0,
                    violation_penalty="WARNING: 標準運用逸脱"
                )
                org_constraints.append(rule)
        
        return org_constraints
    
    def _generate_comprehensive_report(self, integrated_constraints: List[ConstraintRule]) -> Dict[str, Any]:
        """包括的レポート生成"""
        print(f"\n{'='*80}")
        print("【複合制約発見システム最終結果】")
        print(f"{'='*80}")
        
        total_constraints = len(self.all_constraint_rules) + len(integrated_constraints)
        
        print(f"\n◆ 処理サマリー")
        print(f"  - 分析ファイル数: {len(self.processed_files)}")
        print(f"  - 基本制約ルール: {len(self.all_constraint_rules)}個")
        print(f"  - 強化制約ルール: {len(integrated_constraints)}個")
        print(f"  - 総制約ルール数: {total_constraints}個")
        
        # 制約タイプ統計
        all_constraints = self.all_constraint_rules + integrated_constraints
        type_stats = Counter(r.constraint_type.value for r in all_constraints)
        axis_stats = Counter(r.axis.value for r in all_constraints)
        
        print(f"\n◆ 制約タイプ分布:")
        for ctype, count in sorted(type_stats.items()):
            print(f"  - {ctype}: {count}個")
        
        print(f"\n◆ 制約軸分布:")
        for axis, count in sorted(axis_stats.items()):
            print(f"  - {axis}: {count}個")
        
        # 高確信度制約表示
        high_confidence = [r for r in all_constraints if r.confidence > 0.8]
        print(f"\n◆ 高確信度制約 (>80%): {len(high_confidence)}個")
        
        for rule in sorted(high_confidence, key=lambda x: x.confidence, reverse=True)[:10]:
            print(f"\n[{rule.rule_id}] 確信度: {rule.confidence:.1%}")
            print(f"  条件: {rule.condition}")
            print(f"  アクション: {rule.action}")
            print(f"  測定値: {rule.measurement:.1f}")
        
        # 最終レポート作成
        final_report = {
            "system_metadata": {
                "system_name": self.system_name,
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
                "analyzed_files": self.processed_files,
                "total_files": len(self.processed_files)
            },
            "constraint_discovery_summary": {
                "basic_constraints": len(self.all_constraint_rules),
                "enhanced_constraints": len(integrated_constraints),
                "total_constraints": total_constraints,
                "high_confidence_count": len(high_confidence),
                "constraint_type_distribution": dict(type_stats),
                "constraint_axis_distribution": dict(axis_stats)
            },
            "file_analysis_stats": self.file_analysis_stats,
            "all_constraint_rules": [
                {
                    "rule_id": rule.rule_id,
                    "constraint_type": rule.constraint_type.value,
                    "axis": rule.axis.value,
                    "condition": rule.condition,
                    "action": rule.action,
                    "confidence": rule.confidence,
                    "measurement": rule.measurement,
                    "violation_penalty": rule.violation_penalty,
                    "evidence": rule.evidence,
                    "rule_category": "enhanced" if rule in integrated_constraints else "basic"
                }
                for rule in sorted(all_constraints, key=lambda x: x.confidence, reverse=True)
            ],
            "compound_analysis_insights": {
                "cross_file_consistency": len([r for r in integrated_constraints if "複数ファイル" in r.action]),
                "organizational_constraints": len([r for r in integrated_constraints if r.rule_id.startswith("ORG_")]),
                "constraint_strengthening_success": len(integrated_constraints) > 0,
                "analysis_depth_improvement": "significant" if total_constraints > 50 else "moderate"
            }
        }
        
        # レポート保存
        report_filename = f"compound_constraint_discovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, "w", encoding="utf-8") as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n[完了] 複合制約発見システム実行完了")
        print(f"レポート保存: {report_filename}")
        print(f"🎯 制約発見成果: {total_constraints}個の制約ルール生成")
        
        return final_report

def main():
    """メイン実行関数"""
    system = CompoundConstraintDiscoverySystem()
    
    try:
        report = system.discover_compound_constraints(".")
        
        if report and report.get("constraint_discovery_summary", {}).get("total_constraints", 0) > 0:
            print(f"\n✅ 成功: 複合制約発見システム正常完了")
            return 0
        else:
            print(f"\n❌ 制約発見に失敗")
            return 1
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())