#!/usr/bin/env python3
"""
包括的アウトプット検証スクリプト - 実際のanalysis_results.zipの詳細分析
Windows環境で実行し、実際のアウトプット品質を徹底検証
"""

import os
import sys
import zipfile
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import tempfile
import shutil

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class ComprehensiveOutputVerifier:
    """包括的アウトプット検証エンジン"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.verification_results = {
            "zip_file_analysis": {},
            "content_quality_assessment": {},
            "business_value_evaluation": {},
            "data_integrity_check": {},
            "user_experience_assessment": {},
            "performance_analysis": {}
        }
        
    def verify_output_quality(self) -> Dict[str, Any]:
        """アウトプット品質の包括的検証"""
        log.info("🔍 実際のアウトプット品質検証を開始...")
        
        try:
            # 1. ZIPファイルの詳細分析
            self._analyze_zip_files()
            
            # 2. コンテンツ品質評価
            self._assess_content_quality()
            
            # 3. ビジネス価値評価
            self._evaluate_business_value()
            
            # 4. データ整合性チェック
            self._check_data_integrity()
            
            # 5. ユーザーエクスペリエンス評価
            self._assess_user_experience()
            
            # 6. パフォーマンス分析
            self._analyze_performance()
            
            # 最終評価サマリー
            summary = self._generate_final_assessment()
            
            log.info("✅ アウトプット品質検証完了")
            return {
                "status": "completed",
                "summary": summary,
                "detailed_results": self.verification_results,
                "recommendations": self._generate_improvement_recommendations()
            }
            
        except Exception as e:
            log.error(f"❌ 検証中にエラーが発生: {e}")
            return {
                "status": "error",
                "error": str(e),
                "partial_results": self.verification_results
            }
    
    def _analyze_zip_files(self):
        """ZIPファイルの詳細分析"""
        log.info("📦 ZIPファイル分析...")
        
        zip_analysis = {}
        
        # 利用可能なZIPファイルを検索
        zip_files = list(self.project_root.glob("analysis_results*.zip"))
        
        for zip_path in zip_files:
            log.info(f"分析中: {zip_path.name}")
            
            try:
                file_stats = {
                    "file_size": zip_path.stat().st_size,
                    "file_size_mb": round(zip_path.stat().st_size / 1024 / 1024, 2),
                    "created": zip_path.stat().st_ctime,
                    "contents": []
                }
                
                # ZIPファイル内容の分析
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    files = zip_ref.namelist()
                    file_stats["total_files"] = len(files)
                    
                    # ファイルタイプ別統計
                    file_types = {}
                    total_uncompressed_size = 0
                    
                    for file_name in files:
                        info = zip_ref.getinfo(file_name)
                        total_uncompressed_size += info.file_size
                        
                        # 拡張子別分類
                        ext = Path(file_name).suffix.lower()
                        if ext not in file_types:
                            file_types[ext] = {"count": 0, "size": 0}
                        file_types[ext]["count"] += 1
                        file_types[ext]["size"] += info.file_size
                        
                        # 主要ファイルの詳細情報
                        if any(keyword in file_name.lower() for keyword in 
                               ['summary', 'stats', 'heat_all', 'forecast', 'hire_plan']):
                            file_stats["contents"].append({
                                "name": file_name,
                                "size": info.file_size,
                                "compressed_size": info.compress_size,
                                "compression_ratio": round(info.compress_size / info.file_size * 100, 1) if info.file_size > 0 else 0
                            })
                    
                    file_stats["total_uncompressed_size"] = total_uncompressed_size
                    file_stats["total_uncompressed_mb"] = round(total_uncompressed_size / 1024 / 1024, 2)
                    file_stats["compression_ratio"] = round(zip_path.stat().st_size / total_uncompressed_size * 100, 1) if total_uncompressed_size > 0 else 0
                    file_stats["file_types"] = file_types
                
                zip_analysis[zip_path.name] = file_stats
                
            except Exception as e:
                log.error(f"ZIPファイル分析エラー ({zip_path.name}): {e}")
                zip_analysis[zip_path.name] = {"error": str(e)}
        
        self.verification_results["zip_file_analysis"] = zip_analysis
        log.info(f"📦 ZIPファイル分析完了: {len(zip_files)}ファイル")
    
    def _assess_content_quality(self):
        """コンテンツ品質評価"""
        log.info("📊 コンテンツ品質評価...")
        
        quality_assessment = {
            "data_completeness": {},
            "data_accuracy": {},
            "output_usefulness": {},
            "format_accessibility": {}
        }
        
        # extracted_resultsディレクトリの分析
        extracted_dir = self.project_root / "extracted_results"
        if extracted_dir.exists():
            # ファイル形式の分析
            formats = {}
            total_files = 0
            accessible_files = 0  # Excel, CSV, TXT形式
            
            for file_path in extracted_dir.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    ext = file_path.suffix.lower()
                    
                    if ext not in formats:
                        formats[ext] = 0
                    formats[ext] += 1
                    
                    # アクセシブルな形式かチェック
                    if ext in ['.csv', '.xlsx', '.txt', '.json']:
                        accessible_files += 1
                    
                    # 主要ファイルの内容確認
                    if file_path.name in ['stats_summary.txt', 'hire_plan.txt']:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                quality_assessment["data_completeness"][file_path.name] = {
                                    "size": len(content),
                                    "lines": len(content.split('\n')) if content else 0,
                                    "empty": len(content) == 0
                                }
                        except Exception as e:
                            quality_assessment["data_completeness"][file_path.name] = {"error": str(e)}
            
            quality_assessment["format_accessibility"] = {
                "total_files": total_files,
                "accessible_files": accessible_files,
                "accessibility_ratio": accessible_files / total_files if total_files > 0 else 0,
                "formats": formats
            }
        
        self.verification_results["content_quality_assessment"] = quality_assessment
        log.info("📊 コンテンツ品質評価完了")
    
    def _evaluate_business_value(self):
        """ビジネス価値評価"""
        log.info("💼 ビジネス価値評価...")
        
        business_value = {
            "actionable_insights": [],
            "redundant_outputs": [],
            "missing_critical_info": [],
            "value_density_analysis": {}
        }
        
        # extracted_resultsの分析から実用的情報を抽出
        extracted_dir = self.project_root / "extracted_results"
        if extracted_dir.exists():
            total_data_size = 0
            actionable_data_size = 0
            
            # 各シナリオディレクトリの分析
            scenarios = ["out_mean_based", "out_median_based", "out_p25_based"]
            scenario_analysis = {}
            
            for scenario in scenarios:
                scenario_dir = extracted_dir / scenario
                if scenario_dir.exists():
                    scenario_files = list(scenario_dir.iterdir())
                    scenario_size = sum(f.stat().st_size for f in scenario_files if f.is_file())
                    total_data_size += scenario_size
                    
                    # stats_summary.txtの分析
                    stats_file = scenario_dir / "stats_summary.txt"
                    if stats_file.exists():
                        try:
                            with open(stats_file, 'r', encoding='utf-8') as f:
                                stats_content = f.read()
                                if "lack_hours_total" in stats_content and "excess_hours_total" in stats_content:
                                    actionable_data_size += stats_file.stat().st_size
                                    business_value["actionable_insights"].append({
                                        "type": "shortage_analysis",
                                        "file": str(stats_file),
                                        "value": "直接的なシフト調整指針",
                                        "content": stats_content.strip()
                                    })
                        except Exception as e:
                            log.warning(f"stats_summary.txt読み込みエラー: {e}")
                    
                    scenario_analysis[scenario] = {
                        "files": len(scenario_files),
                        "size_bytes": scenario_size,
                        "size_mb": round(scenario_size / 1024 / 1024, 2)
                    }
            
            # 重複データの検出
            if len(scenario_analysis) > 1:
                business_value["redundant_outputs"].append({
                    "type": "duplicate_scenarios",
                    "count": len(scenario_analysis),
                    "scenarios": list(scenario_analysis.keys()),
                    "total_redundant_mb": round(sum(s["size_bytes"] for s in scenario_analysis.values()) * 0.67 / 1024 / 1024, 2)
                })
            
            # 価値密度分析
            business_value["value_density_analysis"] = {
                "total_output_size_mb": round(total_data_size / 1024 / 1024, 2),
                "actionable_size_bytes": actionable_data_size,
                "value_density_ratio": actionable_data_size / total_data_size if total_data_size > 0 else 0,
                "scenario_breakdown": scenario_analysis
            }
        
        self.verification_results["business_value_evaluation"] = business_value
        log.info("💼 ビジネス価値評価完了")
    
    def _check_data_integrity(self):
        """データ整合性チェック"""
        log.info("🔍 データ整合性チェック...")
        
        integrity_check = {
            "consistency_across_scenarios": {},
            "data_validation_results": {},
            "calculation_verification": {}
        }
        
        # シナリオ間の一貫性チェック
        extracted_dir = self.project_root / "extracted_results"
        if extracted_dir.exists():
            scenarios = ["out_mean_based", "out_median_based", "out_p25_based"]
            stats_data = {}
            
            # 各シナリオのstats_summary.txtを比較
            for scenario in scenarios:
                stats_file = extracted_dir / scenario / "stats_summary.txt"
                if stats_file.exists():
                    try:
                        with open(stats_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            stats_data[scenario] = {}
                            for line in content.strip().split('\n'):
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    try:
                                        stats_data[scenario][key.strip()] = float(value.strip())
                                    except ValueError:
                                        stats_data[scenario][key.strip()] = value.strip()
                    except Exception as e:
                        log.warning(f"stats読み込みエラー ({scenario}): {e}")
            
            # 一貫性分析
            if len(stats_data) > 1:
                keys = set()
                for data in stats_data.values():
                    keys.update(data.keys())
                
                for key in keys:
                    values = []
                    for scenario, data in stats_data.items():
                        if key in data:
                            values.append((scenario, data[key]))
                    
                    if len(values) > 1:
                        numeric_values = [(s, v) for s, v in values if isinstance(v, (int, float))]
                        if numeric_values:
                            min_val = min(v for s, v in numeric_values)
                            max_val = max(v for s, v in numeric_values)
                            variance = max_val - min_val
                            
                            integrity_check["consistency_across_scenarios"][key] = {
                                "scenarios": dict(numeric_values),
                                "variance": variance,
                                "consistent": variance == 0
                            }
        
        self.verification_results["data_integrity_check"] = integrity_check
        log.info("🔍 データ整合性チェック完了")
    
    def _assess_user_experience(self):
        """ユーザーエクスペリエンス評価"""
        log.info("👤 ユーザーエクスペリエンス評価...")
        
        ux_assessment = {
            "file_findability": {},
            "content_readability": {},
            "technical_barriers": {},
            "workflow_efficiency": {}
        }
        
        # ファイル発見しやすさ
        extracted_dir = self.project_root / "extracted_results"
        if extracted_dir.exists():
            all_files = list(extracted_dir.rglob("*"))
            file_count = len([f for f in all_files if f.is_file()])
            
            # 重要ファイルの発見しやすさ
            key_files = ['stats_summary.txt', 'hire_plan.txt', 'leave_analysis.csv']
            found_key_files = []
            
            for key_file in key_files:
                found = list(extracted_dir.rglob(key_file))
                if found:
                    found_key_files.extend(found)
            
            ux_assessment["file_findability"] = {
                "total_files": file_count,
                "key_files_found": len(found_key_files),
                "key_files_ratio": len(found_key_files) / (len(key_files) * 3),  # 3シナリオ想定
                "directory_depth": max(len(f.parts) - len(extracted_dir.parts) for f in all_files if f.is_file()) if file_count > 0 else 0
            }
            
            # 技術的障壁の評価
            parquet_files = len(list(extracted_dir.rglob("*.parquet")))
            excel_files = len(list(extracted_dir.rglob("*.xlsx")))
            csv_files = len(list(extracted_dir.rglob("*.csv")))
            txt_files = len(list(extracted_dir.rglob("*.txt")))
            
            ux_assessment["technical_barriers"] = {
                "parquet_files": parquet_files,
                "excel_files": excel_files,
                "csv_files": csv_files,
                "txt_files": txt_files,
                "user_friendly_ratio": (excel_files + csv_files + txt_files) / file_count if file_count > 0 else 0,
                "technical_barrier_ratio": parquet_files / file_count if file_count > 0 else 0
            }
        
        self.verification_results["user_experience_assessment"] = ux_assessment
        log.info("👤 ユーザーエクスペリエンス評価完了")
    
    def _analyze_performance(self):
        """パフォーマンス分析"""
        log.info("⚡ パフォーマンス分析...")
        
        performance_analysis = {
            "storage_efficiency": {},
            "compression_efficiency": {},
            "processing_overhead": {}
        }
        
        # ストレージ効率分析
        total_project_size = sum(f.stat().st_size for f in self.project_root.rglob("*") if f.is_file())
        
        zip_files = list(self.project_root.glob("analysis_results*.zip"))
        total_zip_size = sum(f.stat().st_size for f in zip_files)
        
        extracted_dir = self.project_root / "extracted_results"
        extracted_size = 0
        if extracted_dir.exists():
            extracted_size = sum(f.stat().st_size for f in extracted_dir.rglob("*") if f.is_file())
        
        performance_analysis["storage_efficiency"] = {
            "total_project_size_mb": round(total_project_size / 1024 / 1024, 2),
            "zip_output_size_mb": round(total_zip_size / 1024 / 1024, 2),
            "extracted_output_size_mb": round(extracted_size / 1024 / 1024, 2),
            "output_ratio": round(total_zip_size / total_project_size, 4) if total_project_size > 0 else 0
        }
        
        self.verification_results["performance_analysis"] = performance_analysis
        log.info("⚡ パフォーマンス分析完了")
    
    def _generate_final_assessment(self) -> Dict[str, Any]:
        """最終評価サマリーの生成"""
        results = self.verification_results
        
        # 総合スコア計算
        scores = {
            "data_completeness": 0,
            "business_value": 0,
            "user_experience": 0,
            "efficiency": 0
        }
        
        # データ完全性スコア
        if "content_quality_assessment" in results:
            accessibility = results["content_quality_assessment"].get("format_accessibility", {})
            if accessibility.get("accessibility_ratio", 0) > 0.7:
                scores["data_completeness"] = 8
            elif accessibility.get("accessibility_ratio", 0) > 0.5:
                scores["data_completeness"] = 6
            else:
                scores["data_completeness"] = 4
        
        # ビジネス価値スコア
        if "business_value_evaluation" in results:
            actionable = len(results["business_value_evaluation"].get("actionable_insights", []))
            if actionable > 3:
                scores["business_value"] = 8
            elif actionable > 1:
                scores["business_value"] = 6
            else:
                scores["business_value"] = 3
        
        # ユーザーエクスペリエンススコア
        if "user_experience_assessment" in results:
            ux = results["user_experience_assessment"]
            friendly_ratio = ux.get("technical_barriers", {}).get("user_friendly_ratio", 0)
            if friendly_ratio > 0.8:
                scores["user_experience"] = 8
            elif friendly_ratio > 0.5:
                scores["user_experience"] = 6
            else:
                scores["user_experience"] = 3
        
        # 効率性スコア
        if "performance_analysis" in results:
            output_ratio = results["performance_analysis"].get("storage_efficiency", {}).get("output_ratio", 0)
            if output_ratio > 0.1:
                scores["efficiency"] = 2
            elif output_ratio > 0.01:
                scores["efficiency"] = 4
            else:
                scores["efficiency"] = 1
        
        overall_score = sum(scores.values()) / len(scores)
        
        return {
            "individual_scores": scores,
            "overall_score": round(overall_score, 1),
            "grade": self._get_grade(overall_score),
            "key_findings": self._extract_key_findings()
        }
    
    def _get_grade(self, score: float) -> str:
        """スコアから評価グレードを取得"""
        if score >= 8:
            return "A"
        elif score >= 6:
            return "B"
        elif score >= 4:
            return "C"
        else:
            return "D"
    
    def _extract_key_findings(self) -> List[str]:
        """主要な発見事項を抽出"""
        findings = []
        
        # ZIPファイル分析から
        if "zip_file_analysis" in self.verification_results:
            for zip_name, analysis in self.verification_results["zip_file_analysis"].items():
                if "total_files" in analysis:
                    findings.append(f"{zip_name}: {analysis['total_files']}ファイル, {analysis.get('file_size_mb', 0)}MB")
        
        # ビジネス価値から
        if "business_value_evaluation" in self.verification_results:
            insights = self.verification_results["business_value_evaluation"].get("actionable_insights", [])
            if insights:
                findings.append(f"実用的な分析結果: {len(insights)}件")
        
        return findings
    
    def _generate_improvement_recommendations(self) -> List[str]:
        """改善推奨事項の生成"""
        recommendations = []
        
        # ユーザーエクスペリエンス改善
        if "user_experience_assessment" in self.verification_results:
            barriers = self.verification_results["user_experience_assessment"].get("technical_barriers", {})
            if barriers.get("technical_barrier_ratio", 0) > 0.3:
                recommendations.append("Parquetファイルを一般的なExcel/CSV形式に変換")
        
        # 効率性改善
        if "performance_analysis" in self.verification_results:
            efficiency = self.verification_results["performance_analysis"].get("storage_efficiency", {})
            if efficiency.get("output_ratio", 0) < 0.01:
                recommendations.append("出力サイズ対プロジェクトサイズ比率の改善")
        
        # 重複削減
        if "business_value_evaluation" in self.verification_results:
            redundant = self.verification_results["business_value_evaluation"].get("redundant_outputs", [])
            if redundant:
                recommendations.append("重複シナリオ出力の統合")
        
        return recommendations

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent
    verifier = ComprehensiveOutputVerifier(project_root)
    
    log.info("🔍 包括的アウトプット品質検証を開始...")
    results = verifier.verify_output_quality()
    
    # 結果をJSONファイルに保存
    output_file = project_root / "comprehensive_output_verification_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # 結果をコンソールに表示
    print("\n" + "="*80)
    print("🔍 包括的アウトプット品質検証結果")
    print("="*80)
    
    if results['status'] == 'completed':
        summary = results['summary']
        print(f"📊 総合評価: {summary['grade']} ({summary['overall_score']}/10)")
        print(f"🎯 個別スコア:")
        for category, score in summary['individual_scores'].items():
            print(f"  • {category}: {score}/10")
        
        print(f"\n🔍 主要発見事項:")
        for finding in summary['key_findings']:
            print(f"  • {finding}")
        
        print(f"\n📝 改善推奨事項:")
        for rec in results['recommendations']:
            print(f"  • {rec}")
    else:
        print(f"❌ 検証エラー: {results['error']}")
    
    print(f"\n📄 詳細結果: {output_file}")
    print("="*80)
    
    return results

if __name__ == "__main__":
    main()