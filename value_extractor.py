#!/usr/bin/env python3
"""
価値抽出ツール - Value Extractor
========================================
既存システムに一切影響を与えずに、出力された結果から価値のみを抽出する

特徴:
- 既存システムのファイルを読み取り専用でアクセス
- 軽量依存関係（pandas, pathloibのみ）
- リスクゼロ設計

作成日: 2025年8月5日
"""

from pathlib import Path
import pandas as pd
import json
from typing import Dict, Any, Optional, List
import datetime as dt


class ValueExtractor:
    """既存システムから価値のみを抽出する軽量ツール"""
    
    def __init__(self, results_dir: str = "extracted_results"):
        """
        初期化
        
        Args:
            results_dir: 既存システムの出力ディレクトリ
        """
        self.results_dir = Path(results_dir)
        self.extracted_values = {}
        
        # 依存関係を最小限に抑制
        self.dependencies = ["pandas", "pathlib", "json"]  # 軽量
        
    def extract_all_values(self) -> Dict[str, Any]:
        """
        すべての価値データを抽出
        
        Returns:
            抽出された価値データの辞書
        """
        print("価値抽出開始...")
        
        # 1. 基本統計データの抽出
        shortage_data = self._extract_shortage_data()
        
        # 2. 予測精度データの抽出
        forecast_data = self._extract_forecast_data()
        
        # 3. その他の実用データ抽出
        additional_data = self._extract_additional_insights()
        
        extracted = {
            "extraction_timestamp": dt.datetime.now().isoformat(),
            "source_directory": str(self.results_dir),
            "shortage_analysis": shortage_data,
            "forecast_analysis": forecast_data,
            "additional_insights": additional_data,
            "summary": self._generate_executive_summary(
                shortage_data, forecast_data, additional_data
            )
        }
        
        print("価値抽出完了")
        return extracted
    
    def _extract_shortage_data(self) -> Dict[str, Any]:
        """不足・過剰分析データの抽出"""
        shortage_data = {}
        
        # stats_summary.txt から基本データを抽出
        scenarios = ["out_mean_based", "out_median_based", "out_p25_based"]
        
        for scenario in scenarios:
            summary_file = self.results_dir / scenario / "stats_summary.txt"
            if summary_file.exists():
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    scenario_data = {}
                    for line in lines:
                        if ':' in line:
                            key, value = line.strip().split(':', 1)
                            try:
                                scenario_data[key.strip()] = float(value.strip())
                            except ValueError:
                                scenario_data[key.strip()] = value.strip()
                    
                    shortage_data[scenario] = scenario_data
                    print(f"  {scenario}: 不足{scenario_data.get('lack_hours_total', 'N/A')}h, 過剰{scenario_data.get('excess_hours_total', 'N/A')}h")
                    
                except Exception as e:
                    print(f"  WARNING {scenario}: {e}")
        
        return shortage_data
    
    def _extract_forecast_data(self) -> Dict[str, Any]:
        """予測分析データの抽出"""
        forecast_data = {}
        
        scenarios = ["out_mean_based", "out_median_based", "out_p25_based"]
        
        for scenario in scenarios:
            forecast_file = self.results_dir / scenario / "forecast.summary.txt"
            if forecast_file.exists():
                try:
                    with open(forecast_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    scenario_data = {}
                    for line in lines:
                        if ':' in line:
                            key, value = line.strip().split(':', 1)
                            scenario_data[key.strip()] = value.strip()
                    
                    forecast_data[scenario] = scenario_data
                    mape = scenario_data.get('mape', 'N/A')
                    print(f"  {scenario}: 予測精度 MAPE {mape}")
                    
                except Exception as e:
                    print(f"  WARNING {scenario}: {e}")
        
        return forecast_data
    
    def _extract_additional_insights(self) -> Dict[str, Any]:
        """その他の洞察データを抽出"""
        additional = {}
        
        # 休暇分析データ
        leave_file = self.results_dir / "leave_analysis.csv"
        if leave_file.exists():
            try:
                leave_df = pd.read_csv(leave_file)
                additional["leave_analysis"] = {
                    "total_records": len(leave_df),
                    "columns": list(leave_df.columns)
                }
                print(f"  休暇分析: {len(leave_df)}件のデータ")
            except Exception as e:
                print(f"  WARNING 休暇分析: {e}")
        
        # 日次コストデータ
        cost_file = self.results_dir / "daily_cost.xlsx"
        if cost_file.exists():
            try:
                # Excelファイルのサイズのみ確認（読み込まない）
                file_size = cost_file.stat().st_size / 1024  # KB
                additional["daily_cost"] = {
                    "file_exists": True,
                    "file_size_kb": file_size
                }
                print(f"  日次コスト: {file_size:.1f}KB")
            except Exception as e:
                print(f"  WARNING 日次コスト: {e}")
        
        return additional
    
    def _generate_executive_summary(self, shortage_data: Dict, 
                                  forecast_data: Dict, 
                                  additional_data: Dict) -> Dict[str, Any]:
        """経営層向けエグゼクティブサマリーを生成"""
        
        # 最も信頼性の高いシナリオ（median_based）を使用
        primary_scenario = "out_median_based"
        
        shortage_info = shortage_data.get(primary_scenario, {})
        forecast_info = forecast_data.get(primary_scenario, {})
        
        summary = {
            "key_metrics": {
                "shortage_hours": shortage_info.get("lack_hours_total", "データなし"),
                "excess_hours": shortage_info.get("excess_hours_total", "データなし"),
                "forecast_accuracy": forecast_info.get("mape", "データなし"),
                "net_shortage": shortage_info.get("lack_hours_total", 0) - shortage_info.get("excess_hours_total", 0)
            },
            "status": self._assess_status(shortage_info),
            "recommendations": self._generate_recommendations(shortage_info, forecast_info)
        }
        
        return summary
    
    def _assess_status(self, shortage_info: Dict) -> str:
        """状況評価"""
        lack_hours = shortage_info.get("lack_hours_total", 0)
        
        if isinstance(lack_hours, (int, float)):
            if lack_hours <= 100:
                return "良好"
            elif lack_hours <= 300:
                return "注意"
            else:
                return "要改善"
        
        return "データ不足"
    
    def _generate_recommendations(self, shortage_info: Dict, forecast_info: Dict) -> List[str]:
        """推奨事項の生成"""
        recommendations = []
        
        lack_hours = shortage_info.get("lack_hours_total", 0)
        excess_hours = shortage_info.get("excess_hours_total", 0)
        
        if isinstance(lack_hours, (int, float)) and lack_hours > 200:
            recommendations.append(f"人員不足対策: {lack_hours}時間の不足を解消する採用計画の検討")
        
        if isinstance(excess_hours, (int, float)) and excess_hours > 50:
            recommendations.append(f"効率化対策: {excess_hours}時間の過剰配置の最適化")
        
        mape = forecast_info.get("mape", "N/A")
        if mape != "N/A":
            try:
                mape_float = float(mape)
                if mape_float < 0.1:
                    recommendations.append(f"予測精度良好: MAPE {mape} - 予測モデルが有効活用可能")
            except ValueError:
                pass
        
        if not recommendations:
            recommendations.append("現状維持: 大きな問題は検出されていません")
        
        return recommendations
    
    def save_extracted_values(self, output_file: str = "extracted_values.json") -> Path:
        """抽出した価値をJSONファイルに保存"""
        values = self.extract_all_values()
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(values, f, ensure_ascii=False, indent=2)
        
        print(f"抽出結果を保存: {output_path}")
        return output_path
    
    def generate_lightweight_report(self, output_file: str = "lightweight_report.txt") -> Path:
        """軽量テキストレポートの生成"""
        values = self.extract_all_values()
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("シフト分析 価値抽出レポート\n")
            f.write("=" * 60 + "\n")
            f.write(f"生成日時: {values['extraction_timestamp']}\n")
            f.write(f"データソース: {values['source_directory']}\n")
            f.write("\n")
            
            # エグゼクティブサマリー
            summary = values.get('summary', {})
            key_metrics = summary.get('key_metrics', {})
            
            f.write("【主要指標】\n")
            f.write(f"• 人員不足: {key_metrics.get('shortage_hours', 'N/A')} 時間\n")
            f.write(f"• 人員過剰: {key_metrics.get('excess_hours', 'N/A')} 時間\n") 
            f.write(f"• 予測精度: MAPE {key_metrics.get('forecast_accuracy', 'N/A')}\n")
            f.write(f"• 純不足: {key_metrics.get('net_shortage', 'N/A')} 時間\n")
            f.write(f"• 状況評価: {summary.get('status', 'N/A')}\n")
            f.write("\n")
            
            # 推奨事項
            recommendations = summary.get('recommendations', [])
            f.write("【推奨事項】\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")
            
            f.write("\n")
            f.write("=" * 60 + "\n")
            f.write("※ このレポートは既存システムから価値のみを抽出したものです\n")
            f.write("※ 既存システムには一切の変更を加えていません\n")
        
        print(f"軽量レポートを生成: {output_path}")
        return output_path


def main():
    """メイン実行関数"""
    print("価値抽出ツール開始")
    print("リスクゼロ設計: 既存システムには一切影響しません")
    print()
    
    # 価値抽出の実行
    extractor = ValueExtractor()
    
    # JSON形式で詳細データを保存
    json_path = extractor.save_extracted_values()
    
    # 軽量テキストレポートを生成
    report_path = extractor.generate_lightweight_report()
    
    print()
    print("価値抽出完了")
    print(f"詳細データ: {json_path}")
    print(f"レポート: {report_path}")
    print()
    print("次回からは、軽量レポートで十分な価値を得られます（990MB → 数KB）")


if __name__ == "__main__":
    main()