#!/usr/bin/env python3
"""
制約可視化システム - 46個の制約を具体的に理解できる形で表示
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class ConstraintVisualizer:
    """制約可視化器"""
    
    def __init__(self):
        self.visualizer_name = "制約可視化システム"
        self.version = "1.0.0"
    
    def load_and_parse_constraints(self) -> Dict[str, Any]:
        """制約データの読み込みと解析"""
        try:
            with open("batch_analysis_results.json", "r", encoding="utf-8") as f:
                batch_results = json.load(f)
            
            all_constraints = []
            file_constraint_map = {}
            
            for file_path, result in batch_results["individual_results"].items():
                if result.get("success"):
                    file_constraints = []
                    for constraint in result["constraints"]:
                        # 制約を理解しやすい形に変換
                        parsed_constraint = {
                            "file": file_path,
                            "id": constraint["id"], 
                            "category": constraint["category"],
                            "type": constraint["type"],
                            "constraint_text": constraint["constraint"],
                            "confidence": constraint["confidence"],
                            "priority": constraint["priority"],
                            "actionable": constraint["actionable"],
                            "recommendations": constraint["recommendations"],
                            "details": constraint.get("details", {})
                        }
                        all_constraints.append(parsed_constraint)
                        file_constraints.append(parsed_constraint)
                    
                    file_constraint_map[file_path] = file_constraints
            
            return {
                "all_constraints": all_constraints,
                "file_constraint_map": file_constraint_map,
                "total_constraints": len(all_constraints),
                "batch_summary": batch_results["batch_summary"]
            }
            
        except FileNotFoundError:
            return {"error": "batch_analysis_results.json が見つかりません"}
    
    def categorize_constraints_by_type(self, constraints_data: Dict[str, Any]) -> Dict[str, Any]:
        """制約をタイプ別に分類"""
        print("=== 制約のタイプ別分類 ===")
        
        if "error" in constraints_data:
            return constraints_data
        
        all_constraints = constraints_data["all_constraints"]
        
        # カテゴリ別分類
        categorized = {}
        for constraint in all_constraints:
            category = constraint["category"]
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(constraint)
        
        # 各カテゴリの詳細分析
        category_analysis = {}
        for category, constraints in categorized.items():
            category_analysis[category] = {
                "count": len(constraints),
                "avg_confidence": sum(c["confidence"] for c in constraints) / len(constraints),
                "priority_distribution": {
                    "高": len([c for c in constraints if c["priority"] == "高"]),
                    "中": len([c for c in constraints if c["priority"] == "中"]),
                    "低": len([c for c in constraints if c["priority"] == "低"])
                },
                "unique_types": list(set(c["type"] for c in constraints)),
                "examples": constraints[:3]  # 最初の3つを例として
            }
        
        # 表示
        for category, analysis in category_analysis.items():
            print(f"\n📂 {category} ({analysis['count']}個)")
            print(f"   平均信頼度: {analysis['avg_confidence']:.1%}")
            print(f"   優先度分布: 高{analysis['priority_distribution']['高']} 中{analysis['priority_distribution']['中']} 低{analysis['priority_distribution']['低']}")
            print(f"   制約タイプ: {', '.join(analysis['unique_types'])}")
        
        return {
            "categorized_constraints": categorized,
            "category_analysis": category_analysis
        }
    
    def show_concrete_constraint_examples(self, constraints_data: Dict[str, Any]) -> None:
        """具体的な制約例の表示"""
        print("\n=== 具体的な制約例 ===")
        
        if "error" in constraints_data:
            print("データ読み込みエラー")
            return
        
        all_constraints = constraints_data["all_constraints"]
        
        # カテゴリ別に代表例を表示
        categories = {}
        for constraint in all_constraints:
            category = constraint["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(constraint)
        
        for i, (category, constraints) in enumerate(categories.items(), 1):
            print(f"\n{i}. 【{category}】の例:")
            
            # 各カテゴリから異なるファイルの例を3つまで表示
            shown_files = set()
            example_count = 0
            
            for constraint in constraints:
                if constraint["file"] not in shown_files and example_count < 3:
                    print(f"   📄 {constraint['file']}:")
                    print(f"      制約: {constraint['constraint_text']}")
                    print(f"      優先度: {constraint['priority']} | 信頼度: {constraint['confidence']:.1%}")
                    
                    if constraint["recommendations"]:
                        print(f"      推奨: {constraint['recommendations'][0]}")
                    
                    # 詳細情報があれば表示
                    if constraint["details"]:
                        key_details = []
                        for key, value in constraint["details"].items():
                            if key in ["file_size", "utility_score", "shift_type", "processing_complexity"]:
                                key_details.append(f"{key}: {value}")
                        if key_details:
                            print(f"      詳細: {', '.join(key_details)}")
                    
                    print()
                    shown_files.add(constraint["file"])
                    example_count += 1
            
            if example_count < len(constraints):
                remaining = len(constraints) - example_count
                print(f"   ... 他{remaining}個の同様制約")
    
    def analyze_constraint_patterns(self, constraints_data: Dict[str, Any]) -> Dict[str, Any]:
        """制約パターンの分析"""
        print("\n=== 制約パターンの分析 ===")
        
        if "error" in constraints_data:
            return {"error": "データなし"}
        
        all_constraints = constraints_data["all_constraints"]
        
        # パターン分析
        patterns = {
            "repetitive_patterns": {},  # 繰り返しパターン
            "file_specific_patterns": {},  # ファイル固有パターン
            "universal_patterns": [],  # 全ファイル共通パターン
            "confidence_patterns": {"high": 0, "medium": 0, "low": 0}
        }
        
        # 繰り返しパターンの検出
        constraint_texts = {}
        for constraint in all_constraints:
            # 制約文の基本パターンを抽出（ファイル名を除外）
            pattern = constraint["constraint_text"]
            for file_name in constraints_data["file_constraint_map"].keys():
                pattern = pattern.replace(file_name.replace('.xlsx', ''), '[ファイル名]')
            
            if pattern not in constraint_texts:
                constraint_texts[pattern] = []
            constraint_texts[pattern].append(constraint)
        
        # 繰り返しの多いパターンを特定
        for pattern, constraints in constraint_texts.items():
            if len(constraints) > 1:
                patterns["repetitive_patterns"][pattern] = {
                    "count": len(constraints),
                    "files": list(set(c["file"] for c in constraints)),
                    "category": constraints[0]["category"]
                }
        
        # 全ファイル共通パターンの検出
        file_count = len(constraints_data["file_constraint_map"])
        for pattern, info in patterns["repetitive_patterns"].items():
            if info["count"] == file_count:
                patterns["universal_patterns"].append({
                    "pattern": pattern,
                    "category": info["category"]
                })
        
        # 信頼度パターン
        for constraint in all_constraints:
            if constraint["confidence"] >= 0.9:
                patterns["confidence_patterns"]["high"] += 1
            elif constraint["confidence"] >= 0.7:
                patterns["confidence_patterns"]["medium"] += 1
            else:
                patterns["confidence_patterns"]["low"] += 1
        
        # 結果表示
        print(f"繰り返しパターン数: {len(patterns['repetitive_patterns'])}")
        print(f"全ファイル共通パターン: {len(patterns['universal_patterns'])}")
        print(f"信頼度分布: 高{patterns['confidence_patterns']['high']} 中{patterns['confidence_patterns']['medium']} 低{patterns['confidence_patterns']['low']}")
        
        # 最も一般的なパターンを表示
        print(f"\n最も一般的なパターン:")
        sorted_patterns = sorted(patterns['repetitive_patterns'].items(), 
                               key=lambda x: x[1]['count'], reverse=True)
        
        for i, (pattern, info) in enumerate(sorted_patterns[:5], 1):
            print(f"  {i}. 「{pattern}」")
            print(f"     出現回数: {info['count']}回 | カテゴリ: {info['category']}")
        
        return patterns
    
    def generate_constraint_reality_check(self, constraints_data: Dict[str, Any]) -> Dict[str, Any]:
        """制約の現実性チェック"""
        print("\n=== 制約の現実性チェック ===")
        
        if "error" in constraints_data:
            return {"error": "データなし"}
        
        all_constraints = constraints_data["all_constraints"]
        
        reality_analysis = {
            "truly_useful_constraints": [],
            "obvious_constraints": [],
            "questionable_constraints": [],
            "file_management_constraints": [],
            "shift_analysis_constraints": []
        }
        
        for constraint in all_constraints:
            constraint_text = constraint["constraint_text"]
            category = constraint["category"]
            recommendations = constraint["recommendations"]
            
            # 分類基準
            if "分析可能な状態" in constraint_text or "存在" in constraint_text:
                reality_analysis["obvious_constraints"].append({
                    "constraint": constraint_text,
                    "reason": "ファイル存在は当然の前提条件"
                })
            
            elif "実用性スコア" in constraint_text:
                reality_analysis["questionable_constraints"].append({
                    "constraint": constraint_text,
                    "reason": "スコア自体が計算結果で、制約ではない"
                })
            
            elif any("分析" in rec or "ファイル" in rec for rec in recommendations):  
                reality_analysis["file_management_constraints"].append({
                    "constraint": constraint_text,
                    "benefit": "ファイル選択・管理の改善"
                })
            
            elif "シフト" in constraint_text and "特化" in constraint_text:
                reality_analysis["shift_analysis_constraints"].append({
                    "constraint": constraint_text,
                    "potential": "シフト分析の方向性示唆"
                })
            
            elif ("高速分析" in str(recommendations) or 
                  "詳細分析" in str(recommendations) or
                  "比較分析" in str(recommendations)):
                reality_analysis["truly_useful_constraints"].append({
                    "constraint": constraint_text,
                    "value": "具体的な分析戦略の提示"
                })
        
        # 結果表示
        print(f"実用的制約: {len(reality_analysis['truly_useful_constraints'])}個")
        print(f"当然の制約: {len(reality_analysis['obvious_constraints'])}個")
        print(f"疑問な制約: {len(reality_analysis['questionable_constraints'])}個")
        print(f"ファイル管理制約: {len(reality_analysis['file_management_constraints'])}個")
        print(f"シフト分析制約: {len(reality_analysis['shift_analysis_constraints'])}個")
        
        # 実用的制約の例を表示
        if reality_analysis["truly_useful_constraints"]:
            print(f"\n実用的制約の例:")
            for i, constraint in enumerate(reality_analysis["truly_useful_constraints"][:3], 1):
                print(f"  {i}. {constraint['constraint']}")
                print(f"     価値: {constraint['value']}")
        
        return reality_analysis

def main():
    """メイン実行関数"""
    print("=" * 80)
    print("制約可視化システム - 46個の制約を具体的に理解")
    print("=" * 80)
    
    try:
        visualizer = ConstraintVisualizer()
        
        # Phase 1: 制約データの読み込み
        constraints_data = visualizer.load_and_parse_constraints()
        
        if "error" in constraints_data:
            print(f"エラー: {constraints_data['error']}")
            return 1
        
        print(f"読み込み完了: {constraints_data['total_constraints']}個の制約")
        
        # Phase 2: タイプ別分類
        categorized_data = visualizer.categorize_constraints_by_type(constraints_data)
        
        # Phase 3: 具体的な制約例の表示
        visualizer.show_concrete_constraint_examples(constraints_data)
        
        # Phase 4: 制約パターンの分析
        patterns = visualizer.analyze_constraint_patterns(constraints_data)
        
        # Phase 5: 制約の現実性チェック
        reality_check = visualizer.generate_constraint_reality_check(constraints_data)
        
        # 総合レポート
        visualization_report = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_constraints_analyzed": constraints_data['total_constraints'],
                "visualizer": visualizer.visualizer_name
            },
            "constraint_breakdown": constraints_data['batch_summary']['category_distribution'],
            "categorized_analysis": categorized_data.get('category_analysis', {}),
            "pattern_analysis": patterns,
            "reality_check": reality_check
        }
        
        # レポート保存
        try:
            with open("constraint_visualization_report.json", "w", encoding="utf-8") as f:
                json.dump(visualization_report, f, ensure_ascii=False, indent=2)
            print(f"\n   [OK] 制約可視化レポート保存完了: constraint_visualization_report.json")
        except Exception as e:
            print(f"   [WARNING] レポート保存エラー: {e}")
        
        # 最終サマリー
        print("\n" + "=" * 80)
        print("[CONSTRAINT SUMMARY] 46個の制約の実態")
        print("=" * 80)
        
        print(f"[BREAKDOWN] カテゴリ別内訳:")
        for category, count in constraints_data['batch_summary']['category_distribution'].items():
            print(f"  {category}: {count}個")
        
        print(f"\n[REALITY CHECK] 制約の価値評価:")
        print(f"  実用的: {len(reality_check.get('truly_useful_constraints', []))}個")
        print(f"  当然: {len(reality_check.get('obvious_constraints', []))}個")
        print(f"  疑問: {len(reality_check.get('questionable_constraints', []))}個")
        print(f"  ファイル管理: {len(reality_check.get('file_management_constraints', []))}個")
        print(f"  シフト分析: {len(reality_check.get('shift_analysis_constraints', []))}個")
        
        print(f"\n[PATTERN] 繰り返しパターン: {len(patterns.get('repetitive_patterns', {}))}種類")
        print(f"[UNIVERSAL] 全ファイル共通: {len(patterns.get('universal_patterns', []))}個")
        
        print(f"\n[CONCLUSION] 46個の制約の正体:")
        print(f"  - 多くは「ファイルが存在する」「サイズがXX」等の基本情報")
        print(f"  - シフト制約は主にファイル名からの推測")
        print(f"  - 実際のシフトデータ内容に基づく制約は0個")
        print(f"  - ファイル選択・管理の改善には有効")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] 制約可視化エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())