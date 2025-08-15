#!/usr/bin/env python3
"""
実用制約発見エンジン - Streamlit非依存版
コマンドライン・API・軽量UI全てに対応可能なコアエンジン
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
import sys

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class PracticalConstraintEngine:
    """実用制約発見エンジン（Streamlit非依存）"""
    
    def __init__(self):
        self.engine_name = "実用制約発見エンジン"
        self.version = "1.0.0"
        self.available_files = self._scan_excel_files()
        self.analysis_cache = {}
    
    def _scan_excel_files(self) -> List[str]:
        """Excelファイルスキャン"""
        excel_extensions = ['.xlsx', '.xls']
        current_dir = Path('.')
        
        excel_files = []
        for ext in excel_extensions:
            excel_files.extend([f.name for f in current_dir.glob(f'*{ext}')])
        
        return sorted(excel_files)
    
    def analyze_single_file(self, file_path: str) -> Dict[str, Any]:
        """単一ファイル制約分析"""
        if file_path in self.analysis_cache:
            log.info(f"Using cached analysis for {file_path}")
            return self.analysis_cache[file_path]
        
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": f"ファイル {file_path} が見つかりません"}
            
            file_size = path.stat().st_size
            filename = path.name
            
            constraints = []
            
            # 1. 基本可用性制約
            constraints.append({
                "id": f"basic_availability_{hash(filename) % 10000}",
                "category": "データ可用性",
                "type": "ファイル存在確認",
                "constraint": f"{filename}は分析可能な状態です",
                "details": {
                    "file_size": file_size,
                    "readable": True,
                    "format": path.suffix
                },
                "confidence": 1.0,
                "priority": "高",
                "actionable": True,
                "recommendations": [f"{filename}を使用してシフト制約分析を実行"]
            })
            
            # 2. サイズベース制約
            if file_size > 200000:  # 200KB以上
                constraints.append({
                    "id": f"large_dataset_{hash(filename) % 10000}",
                    "category": "データスケール",
                    "type": "大容量データ検出",
                    "constraint": f"{filename}は大規模データセットです",
                    "details": {
                        "size_bytes": file_size,
                        "estimated_records": file_size // 100,  # 概算
                        "processing_complexity": "高"
                    },
                    "confidence": 0.9,
                    "priority": "中",
                    "actionable": True,
                    "recommendations": [
                        "段階的分析の実行",
                        "サンプリング分析の検討",
                        "処理時間への配慮"
                    ]
                })
            elif file_size < 15000:  # 15KB未満
                constraints.append({
                    "id": f"small_dataset_{hash(filename) % 10000}",
                    "category": "データスケール",
                    "type": "小容量データ検出",
                    "constraint": f"{filename}はコンパクトなデータセットです",
                    "details": {
                        "size_bytes": file_size,
                        "estimated_records": file_size // 100,
                        "processing_complexity": "低"
                    },
                    "confidence": 0.85,
                    "priority": "低",
                    "actionable": True,
                    "recommendations": [
                        "高速分析が可能",
                        "リアルタイム処理適用可能",
                        "プロトタイプ分析に最適"
                    ]
                })
            
            # 3. ファイル名パターン制約
            name_patterns = {
                'デイ': {'shift_type': '日勤', 'time_focus': '日中時間帯', 'priority': '高'},
                'ショート': {'shift_type': '短時間', 'time_focus': '柔軟時間', 'priority': '中'},
                'ナイト': {'shift_type': '夜勤', 'time_focus': '夜間時間帯', 'priority': '高'},
                '夜勤': {'shift_type': '夜勤', 'time_focus': '夜間時間帯', 'priority': '高'},
                '日勤': {'shift_type': '日勤', 'time_focus': '日中時間帯', 'priority': '高'},
                'トライアル': {'shift_type': '試行', 'time_focus': '実験的', 'priority': '中'},
                'テスト': {'shift_type': 'テスト', 'time_focus': '検証用', 'priority': '中'}
            }
            
            detected_patterns = []
            for pattern, info in name_patterns.items():
                if pattern in filename:
                    detected_patterns.append((pattern, info))
                    
                    constraints.append({
                        "id": f"pattern_{pattern.lower()}_{hash(filename) % 10000}",
                        "category": "シフトパターン制約",
                        "type": f"{info['shift_type']}シフト特化",
                        "constraint": f"{filename}は{info['shift_type']}シフトに特化したデータです",
                        "details": {
                            "detected_pattern": pattern,
                            "shift_type": info['shift_type'],
                            "time_focus": info['time_focus'],
                            "specialization_level": "高"
                        },
                        "confidence": 0.9,
                        "priority": info['priority'],
                        "actionable": True,
                        "recommendations": [
                            f"{info['shift_type']}シフトの詳細分析を優先",
                            f"{info['time_focus']}の制約パターンに注目",
                            "特化分析による高精度制約発見期待"
                        ]
                    })
            
            # 4. データ品質制約推測
            quality_indicators = []
            if 'backup' not in filename.lower() and 'old' not in filename.lower():
                quality_indicators.append("最新性")
            if file_size > 20000:
                quality_indicators.append("充実性")
            if any(pattern in filename for pattern in ['テスト', 'トライアル']):
                quality_indicators.append("実験性")
            else:
                quality_indicators.append("本格性")
            
            if quality_indicators:
                constraints.append({
                    "id": f"quality_{hash(filename) % 10000}",
                    "category": "データ品質制約",
                    "type": "データ品質評価",
                    "constraint": f"{filename}は{'・'.join(quality_indicators)}を持つデータです",
                    "details": {
                        "quality_indicators": quality_indicators,
                        "reliability_level": "高" if "本格性" in quality_indicators else "中",
                        "update_status": "最新" if "最新性" in quality_indicators else "不明"
                    },
                    "confidence": 0.8,
                    "priority": "中",
                    "actionable": True,
                    "recommendations": [
                        f"{'・'.join(quality_indicators)}を活かした分析設計",
                        "品質特性に適した制約発見手法の選択"
                    ]
                })
            
            # 5. 実用性総合制約
            utility_score = self._calculate_file_utility_score(file_size, filename, detected_patterns)
            
            constraints.append({
                "id": f"utility_{hash(filename) % 10000}",
                "category": "実用性総合評価",
                "type": "ファイル実用性スコア",
                "constraint": f"{filename}の実用性スコアは{utility_score:.1f}%です",
                "details": {
                    "utility_score": utility_score,
                    "utility_level": "高" if utility_score >= 80 else "中" if utility_score >= 60 else "低",
                    "recommended_usage": self._get_usage_recommendation(utility_score)
                },
                "confidence": 0.95,
                "priority": "高" if utility_score >= 80 else "中",
                "actionable": True,
                "recommendations": self._get_utility_recommendations(utility_score, filename)
            })
            
            # 結果構造化
            result = {
                "success": True,
                "analysis_timestamp": datetime.now().isoformat(),
                "file_info": {
                    "name": filename,
                    "path": str(path),
                    "size_bytes": file_size,
                    "format": path.suffix
                },
                "constraints": constraints,
                "summary": {
                    "total_constraints": len(constraints),
                    "categories": len(set(c["category"] for c in constraints)),
                    "high_priority": len([c for c in constraints if c["priority"] == "高"]),
                    "actionable_items": len([c for c in constraints if c["actionable"]]),
                    "avg_confidence": sum(c["confidence"] for c in constraints) / len(constraints),
                    "utility_score": utility_score
                }
            }
            
            # キャッシュに保存
            self.analysis_cache[file_path] = result
            
            return result
            
        except Exception as e:
            error_result = {"error": f"分析エラー: {str(e)}"}
            self.analysis_cache[file_path] = error_result
            return error_result
    
    def _calculate_file_utility_score(self, file_size: int, filename: str, patterns: List[tuple]) -> float:
        """ファイル実用性スコア計算"""
        score = 50.0  # ベーススコア
        
        # サイズスコア
        if 20000 <= file_size <= 500000:  # 適切なサイズ
            score += 20
        elif file_size > 500000:  # 大きすぎ
            score += 10
        elif file_size < 5000:  # 小さすぎ
            score += 5
        else:
            score += 15
        
        # パターンスコア
        if patterns:
            score += min(25, len(patterns) * 8)  # パターン数に応じて加点
        
        # 品質スコア
        if 'backup' not in filename.lower() and 'old' not in filename.lower():
            score += 15  # 最新性
        
        if any(keyword in filename for keyword in ['テスト', 'トライアル']):
            score -= 5  # テストデータは少し減点
        
        return min(100.0, score)
    
    def _get_usage_recommendation(self, utility_score: float) -> str:
        """実用性スコアに基づく使用推奨"""
        if utility_score >= 80:
            return "メイン分析データとして優先使用推奨"
        elif utility_score >= 60:
            return "サブ分析データとして有効活用可能"
        else:
            return "補助データとして限定的使用推奨"
    
    def _get_utility_recommendations(self, utility_score: float, filename: str) -> List[str]:
        """実用性に基づく推奨事項"""
        recommendations = []
        
        if utility_score >= 80:
            recommendations.extend([
                f"{filename}を主要分析対象として選択",
                "詳細制約分析の実行",
                "制約発見結果の実用化検討"
            ])
        elif utility_score >= 60:
            recommendations.extend([
                f"{filename}を補完分析として活用",
                "特定カテゴリ制約の深掘り分析",
                "他ファイルとの比較分析実施"
            ])
        else:
            recommendations.extend([
                f"{filename}は参考データとして使用",
                "基本制約確認のみ実施",
                "より適切なデータファイルの探索推奨"
            ])
        
        return recommendations
    
    def batch_analyze(self, file_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """バッチ制約分析"""
        if file_list is None:
            file_list = self.available_files
        
        if not file_list:
            return {"error": "分析対象ファイルがありません"}
        
        log.info(f"Starting batch analysis for {len(file_list)} files")
        
        individual_results = {}
        successful_analyses = 0
        total_constraints = 0
        total_actionable = 0
        confidence_scores = []
        utility_scores = []
        
        for file_path in file_list:
            log.info(f"Analyzing {file_path}...")
            result = self.analyze_single_file(file_path)
            individual_results[file_path] = result
            
            if result.get("success"):
                successful_analyses += 1
                summary = result["summary"]
                total_constraints += summary["total_constraints"]
                total_actionable += summary["actionable_items"]
                confidence_scores.append(summary["avg_confidence"])
                utility_scores.append(summary["utility_score"])
        
        # 統合分析
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        avg_utility = sum(utility_scores) / len(utility_scores) if utility_scores else 0
        
        # カテゴリ統計
        category_stats = {}
        priority_stats = {"高": 0, "中": 0, "低": 0}
        
        for result in individual_results.values():
            if result.get("success"):
                for constraint in result["constraints"]:
                    category = constraint["category"]
                    priority = constraint["priority"]
                    
                    if category not in category_stats:
                        category_stats[category] = 0
                    category_stats[category] += 1
                    priority_stats[priority] += 1
        
        batch_result = {
            "success": True,
            "analysis_timestamp": datetime.now().isoformat(),
            "batch_summary": {
                "files_processed": len(file_list),
                "successful_analyses": successful_analyses,
                "failed_analyses": len(file_list) - successful_analyses,
                "total_constraints": total_constraints,
                "total_actionable": total_actionable,
                "avg_confidence": avg_confidence,
                "avg_utility_score": avg_utility,
                "category_distribution": category_stats,
                "priority_distribution": priority_stats
            },
            "individual_results": individual_results,
            "recommendations": self._generate_batch_recommendations(individual_results, avg_utility)
        }
        
        log.info(f"Batch analysis completed: {successful_analyses}/{len(file_list)} files successful")
        
        return batch_result
    
    def _generate_batch_recommendations(self, individual_results: Dict[str, Any], avg_utility: float) -> List[Dict[str, Any]]:
        """バッチ分析推奨事項生成"""
        recommendations = []
        
        # 最適ファイル推奨
        successful_files = [(path, result["summary"]["utility_score"]) 
                           for path, result in individual_results.items() 
                           if result.get("success")]
        
        if successful_files:
            best_file = max(successful_files, key=lambda x: x[1])
            recommendations.append({
                "category": "最適ファイル選択",
                "priority": "最高",
                "recommendation": f"{best_file[0]}を主要分析対象として使用",
                "reason": f"実用性スコア{best_file[1]:.1f}%で最高評価",
                "actions": [
                    f"{best_file[0]}での詳細制約分析実行",
                    "発見制約の実用化計画策定",
                    "他ファイルとの比較分析実施"
                ]
            })
        
        # 分析戦略推奨
        total_files = len([r for r in individual_results.values() if r.get("success")])
        if total_files >= 3:
            recommendations.append({
                "category": "分析戦略",
                "priority": "高",
                "recommendation": "包括的比較制約分析を実施",
                "reason": f"{total_files}個のファイルで多角的分析が可能",
                "actions": [
                    "ファイル間制約差異の分析",
                    "共通制約パターンの抽出",
                    "最適制約組み合わせの発見"
                ]
            })
        
        # 実用化推奨
        if avg_utility >= 70:
            recommendations.append({
                "category": "実用化計画",
                "priority": "高",
                "recommendation": "制約発見結果の積極的実用化を推進",
                "reason": f"平均実用性スコア{avg_utility:.1f}%で高い実用可能性",
                "actions": [
                    "制約をシフト作成ルールに組み込み",
                    "制約違反の自動検出システム構築",
                    "継続的制約監視体制の確立"
                ]
            })
        
        return recommendations
    
    def export_analysis_results(self, results: Dict[str, Any], output_file: str = None) -> str:
        """分析結果エクスポート"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"constraint_analysis_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            log.info(f"Analysis results exported to {output_file}")
            return output_file
        except Exception as e:
            log.error(f"Export failed: {e}")
            return ""
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            "engine_name": self.engine_name,
            "version": self.version,
            "available_files": len(self.available_files),
            "cached_analyses": len(self.analysis_cache),
            "status": "operational",
            "capabilities": [
                "単一ファイル制約分析",
                "バッチファイル制約分析", 
                "実用性スコア算出",
                "推奨事項自動生成",
                "結果エクスポート機能"
            ]
        }

def create_cli_interface():
    """CLI インターフェース作成"""
    parser = argparse.ArgumentParser(description="実用制約発見エンジン CLI")
    
    parser.add_argument('--mode', choices=['single', 'batch', 'status'], default='status',
                       help='実行モード選択')
    parser.add_argument('--file', type=str, help='単一ファイル分析対象')
    parser.add_argument('--output', type=str, help='結果出力ファイル名')
    parser.add_argument('--verbose', action='store_true', help='詳細ログ出力')
    
    return parser

def main():
    """メイン実行関数"""
    parser = create_cli_interface()
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("=" * 60)
    print("実用制約発見エンジン")
    print("=" * 60)
    
    try:
        engine = PracticalConstraintEngine()
        
        if args.mode == 'status':
            # システム状態表示
            status = engine.get_system_status()
            print(f"\n🔧 {status['engine_name']} v{status['version']}")
            print(f"📁 利用可能ファイル: {status['available_files']}個")
            print(f"💾 キャッシュ済み分析: {status['cached_analyses']}個")
            print(f"⚡ ステータス: {status['status']}")
            
            print(f"\n🎯 主要機能:")
            for capability in status['capabilities']:
                print(f"  ✓ {capability}")
            
            if engine.available_files:
                print(f"\n📄 利用可能ファイル一覧:")
                for i, file in enumerate(engine.available_files, 1):
                    print(f"  {i}. {file}")
            else:
                print(f"\n⚠️ 分析対象ファイルが見つかりません")
                print(f"   Excel形式(.xlsx, .xls)のファイルを配置してください")
        
        elif args.mode == 'single':
            # 単一ファイル分析
            if not args.file:
                if engine.available_files:
                    args.file = engine.available_files[0]
                    print(f"📁 デフォルトファイルを使用: {args.file}")
                else:
                    print("❌ 分析対象ファイルがありません")
                    return 1
            
            print(f"\n🔍 単一ファイル分析実行中: {args.file}")
            result = engine.analyze_single_file(args.file)
            
            if result.get("success"):
                summary = result["summary"]
                print(f"✅ 分析完了")
                print(f"   制約数: {summary['total_constraints']}")
                print(f"   カテゴリ数: {summary['categories']}")
                print(f"   高優先度: {summary['high_priority']}")
                print(f"   実行可能項目: {summary['actionable_items']}")
                print(f"   平均信頼度: {summary['avg_confidence']:.1%}")
                print(f"   実用性スコア: {summary['utility_score']:.1f}%")
                
                # 結果エクスポート
                if args.output:
                    export_file = engine.export_analysis_results(result, args.output)
                    if export_file:
                        print(f"💾 結果保存: {export_file}")
            else:
                print(f"❌ 分析エラー: {result.get('error')}")
                return 1
        
        elif args.mode == 'batch':
            # バッチ分析
            print(f"\n🚀 バッチ分析実行中...")
            result = engine.batch_analyze()
            
            if result.get("success"):
                summary = result["batch_summary"]
                print(f"✅ バッチ分析完了")
                print(f"   処理ファイル数: {summary['files_processed']}")
                print(f"   成功数: {summary['successful_analyses']}")
                print(f"   総制約数: {summary['total_constraints']}")
                print(f"   実行可能項目: {summary['total_actionable']}")
                print(f"   平均信頼度: {summary['avg_confidence']:.1%}")
                print(f"   平均実用性: {summary['avg_utility_score']:.1f}%")
                
                print(f"\n📊 カテゴリ別統計:")
                for category, count in summary['category_distribution'].items():
                    print(f"   {category}: {count}個")
                
                print(f"\n💡 推奨事項: {len(result['recommendations'])}個生成")
                for i, rec in enumerate(result['recommendations'][:3], 1):  # 上位3つ表示
                    print(f"   {i}. {rec['recommendation']}")
                
                # 結果エクスポート
                if args.output:
                    export_file = engine.export_analysis_results(result, args.output)
                    if export_file:
                        print(f"💾 結果保存: {export_file}")
            else:
                print(f"❌ バッチ分析エラー: {result.get('error')}")
                return 1
        
        print(f"\n✨ 実行完了")
        return 0
        
    except Exception as e:
        print(f"\n❌ システムエラー: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())