#!/usr/bin/env python
"""
統合型スマート過不足分析システム

動的シフトデータと予測モデルを統合した
次世代過不足分析システムの完全実装
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from dynamic_shortage_analyzer import DynamicShortageAnalyzer
from predictive_demand_engine import PredictiveDemandEngine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class IntegratedSmartShortageSystem:
    """統合型スマート過不足分析システム"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.dynamic_analyzer = DynamicShortageAnalyzer(data_dir)
        self.predictive_engine = PredictiveDemandEngine(data_dir)
        self.integrated_results = {}
        
    def run_comprehensive_analysis(self) -> Dict[str, any]:
        """包括的過不足分析の実行"""
        log.info("=== 統合型スマート過不足分析開始 ===")
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_method': 'integrated_smart_system',
            'components': {}
        }
        
        try:
            # 1. 動的過不足分析
            log.info("1. 動的リアルタイム分析実行中...")
            dynamic_results = self._run_dynamic_analysis()
            results['components']['dynamic_analysis'] = dynamic_results
            
            # 2. 予測需要分析
            log.info("2. 予測需要分析実行中...")
            predictive_results = self._run_predictive_analysis()
            results['components']['predictive_analysis'] = predictive_results
            
            # 3. 統合分析
            log.info("3. 統合分析実行中...")
            integrated_analysis = self._perform_integrated_analysis(
                dynamic_results, predictive_results
            )
            results['integrated_analysis'] = integrated_analysis
            
            # 4. 最適化推奨
            log.info("4. 最適化推奨生成中...")
            optimization_recommendations = self._generate_optimization_recommendations(
                integrated_analysis
            )
            results['optimization_recommendations'] = optimization_recommendations
            
            # 5. 実用性評価
            log.info("5. 実用性評価実行中...")
            practicality_assessment = self._assess_practicality(results)
            results['practicality_assessment'] = practicality_assessment
            
            # 結果保存
            self._save_results(results)
            
            log.info("=== 統合型スマート過不足分析完了 ===")
            return results
            
        except Exception as e:
            log.error(f"統合分析エラー: {e}")
            raise
    
    def _run_dynamic_analysis(self) -> Dict[str, any]:
        """動的過不足分析の実行"""
        try:
            # 実際のシフトデータ読み込み
            self.dynamic_analyzer.load_actual_shift_data()
            
            # 動的需要パターン分析
            demand_patterns = self.dynamic_analyzer.analyze_dynamic_demand_patterns()
            
            # リアルタイムカバレッジ分析
            coverage_analysis = self.dynamic_analyzer.calculate_real_time_coverage()
            
            # 動的過不足レポート生成
            dynamic_report = self.dynamic_analyzer.generate_dynamic_shortage_report()
            
            return {
                'method': 'real_time_dynamic',
                'results': dynamic_report,
                'success': True
            }
            
        except Exception as e:
            log.error(f"動的分析エラー: {e}")
            return {
                'method': 'real_time_dynamic',
                'error': str(e),
                'success': False
            }
    
    def _run_predictive_analysis(self) -> Dict[str, any]:
        """予測需要分析の実行"""
        try:
            # データ準備
            self.predictive_engine.load_and_prepare_data()
            
            # モデル訓練
            model_results = self.predictive_engine.train_predictive_models()
            
            # 将来需要予測（7日間）
            future_predictions = self.predictive_engine.predict_future_demand(7)
            
            return {
                'method': 'machine_learning_prediction',
                'model_performance': model_results,
                'future_predictions': future_predictions,
                'success': True
            }
            
        except Exception as e:
            log.error(f"予測分析エラー: {e}")
            return {
                'method': 'machine_learning_prediction',
                'error': str(e),
                'success': False
            }
    
    def _perform_integrated_analysis(self, dynamic_results: Dict, predictive_results: Dict) -> Dict[str, any]:
        """統合分析の実行"""
        integrated = {
            'analysis_method': 'dynamic_predictive_integration',
            'timestamp': datetime.now().isoformat()
        }
        
        # 動的分析が成功している場合
        if dynamic_results.get('success'):
            dynamic_data = dynamic_results['results']
            
            integrated['current_shortage'] = {
                'total_hours': dynamic_data.get('total_shortage_hours', 0),
                'daily_average': dynamic_data.get('daily_average_shortage', 0),
                'by_role': dynamic_data.get('shortage_by_role', {}),
                'method': 'real_time_calculation'
            }
            
            # データ品質評価
            data_quality = dynamic_data.get('validation', {}).get('data_quality', {})
            integrated['data_quality'] = data_quality
        
        # 予測分析が成功している場合
        if predictive_results.get('success'):
            future_data = predictive_results['future_predictions']
            
            integrated['predicted_demand'] = {
                'forecast_period': '7 days',
                'by_role': {},
                'total_predicted_hours': 0,
                'method': 'machine_learning_prediction'
            }
            
            total_predicted = 0
            for role, pred_data in future_data.items():
                role_hours = pred_data.get('total_predicted_hours', 0)
                integrated['predicted_demand']['by_role'][role] = {
                    'total_hours': role_hours,
                    'avg_daily': pred_data.get('avg_daily_demand', 0)
                }
                total_predicted += role_hours
            
            integrated['predicted_demand']['total_predicted_hours'] = total_predicted
        
        # 統合メトリクスの計算
        integrated['integrated_metrics'] = self._calculate_integrated_metrics(
            dynamic_results, predictive_results
        )
        
        # 信頼性評価
        integrated['reliability_assessment'] = self._assess_analysis_reliability(
            dynamic_results, predictive_results
        )
        
        return integrated
    
    def _calculate_integrated_metrics(self, dynamic_results: Dict, predictive_results: Dict) -> Dict[str, any]:
        """統合メトリクスの計算"""
        metrics = {}
        
        # 現在不足と予測需要の比較
        if (dynamic_results.get('success') and predictive_results.get('success')):
            current_shortage = dynamic_results['results'].get('daily_average_shortage', 0)
            predicted_daily = predictive_results['future_predictions']
            
            if predicted_daily:
                total_predicted_daily = sum(
                    pred.get('avg_daily_demand', 0) 
                    for pred in predicted_daily.values()
                )
                
                metrics['demand_trend'] = {
                    'current_daily_shortage': current_shortage,
                    'predicted_daily_demand': total_predicted_daily,
                    'trend_ratio': total_predicted_daily / max(current_shortage, 1),
                    'trend_direction': 'increasing' if total_predicted_daily > current_shortage else 'stable'
                }
        
        # 職種別リスク評価
        if dynamic_results.get('success'):
            shortage_by_role = dynamic_results['results'].get('shortage_by_role', {})
            
            high_risk_roles = []
            medium_risk_roles = []
            low_risk_roles = []
            
            for role, shortage_hours in shortage_by_role.items():
                daily_shortage = shortage_hours / 30  # 30日基準
                
                if daily_shortage > 2.0:
                    high_risk_roles.append({'role': role, 'daily_shortage': daily_shortage})
                elif daily_shortage > 0.5:
                    medium_risk_roles.append({'role': role, 'daily_shortage': daily_shortage})
                else:
                    low_risk_roles.append({'role': role, 'daily_shortage': daily_shortage})
            
            metrics['role_risk_assessment'] = {
                'high_risk': high_risk_roles,
                'medium_risk': medium_risk_roles,
                'low_risk': low_risk_roles,
                'total_roles_analyzed': len(shortage_by_role)
            }
        
        return metrics
    
    def _assess_analysis_reliability(self, dynamic_results: Dict, predictive_results: Dict) -> Dict[str, any]:
        """分析信頼性の評価"""
        reliability = {
            'overall_score': 0.0,
            'components': {}
        }
        
        # 動的分析の信頼性
        if dynamic_results.get('success'):
            data_quality = dynamic_results['results'].get('validation', {}).get('data_quality', {})
            reliability_score = data_quality.get('reliability_score', 0.5)
            
            reliability['components']['dynamic_analysis'] = {
                'reliability_score': reliability_score,
                'data_completeness': data_quality.get('completeness', {}),
                'assessment': 'high' if reliability_score > 0.8 else 'medium' if reliability_score > 0.6 else 'low'
            }
        
        # 予測分析の信頼性
        if predictive_results.get('success'):
            model_performance = predictive_results.get('model_performance', {})
            
            # モデル性能の平均評価
            avg_performance = 0.0
            model_count = 0
            
            for role, performance in model_performance.items():
                if 'performance' in performance:
                    # MAEベースの評価（低いほど良い）
                    for model_name, metrics in performance['performance'].items():
                        mae = metrics.get('mae', 1.0)
                        # MAE -> スコア変換（経験的変換）
                        score = max(0, 1 - mae / 2)
                        avg_performance += score
                        model_count += 1
            
            if model_count > 0:
                avg_performance /= model_count
            
            reliability['components']['predictive_analysis'] = {
                'avg_model_performance': avg_performance,
                'models_trained': len(model_performance),
                'assessment': 'high' if avg_performance > 0.7 else 'medium' if avg_performance > 0.5 else 'low'
            }
        
        # 総合信頼性スコア
        component_scores = []
        for component in reliability['components'].values():
            if 'reliability_score' in component:
                component_scores.append(component['reliability_score'])
            elif 'avg_model_performance' in component:
                component_scores.append(component['avg_model_performance'])
        
        if component_scores:
            reliability['overall_score'] = sum(component_scores) / len(component_scores)
        
        reliability['overall_assessment'] = (
            'high' if reliability['overall_score'] > 0.75 else
            'medium' if reliability['overall_score'] > 0.5 else
            'low'
        )
        
        return reliability
    
    def _generate_optimization_recommendations(self, integrated_analysis: Dict) -> Dict[str, any]:
        """最適化推奨の生成"""
        recommendations = {
            'timestamp': datetime.now().isoformat(),
            'recommendations': []
        }
        
        # 現在の不足状況に基づく推奨
        current_shortage = integrated_analysis.get('current_shortage', {})
        daily_avg = current_shortage.get('daily_average', 0)
        
        if daily_avg > 3.0:
            recommendations['recommendations'].append({
                'priority': 'high',
                'category': 'staffing',
                'title': '人員増強の緊急検討',
                'description': f'日平均{daily_avg:.1f}時間の不足が検出されています。追加採用または時間延長を検討してください。',
                'impact': 'immediate'
            })
        elif daily_avg > 1.0:
            recommendations['recommendations'].append({
                'priority': 'medium',
                'category': 'scheduling',
                'title': 'シフト配置の最適化',
                'description': f'日平均{daily_avg:.1f}時間の不足があります。シフト配置の見直しで改善可能です。',
                'impact': 'short_term'
            })
        
        # 職種別リスク対応
        metrics = integrated_analysis.get('integrated_metrics', {})
        role_risks = metrics.get('role_risk_assessment', {})
        
        high_risk_roles = role_risks.get('high_risk', [])
        if high_risk_roles:
            for role_info in high_risk_roles:
                recommendations['recommendations'].append({
                    'priority': 'high',
                    'category': 'role_specific',
                    'title': f'{role_info["role"]}の人員不足対策',
                    'description': f'日平均{role_info["daily_shortage"]:.1f}時間の不足。専門スタッフの確保が必要です。',
                    'impact': 'immediate'
                })
        
        # 予測ベースの推奨
        predicted_demand = integrated_analysis.get('predicted_demand', {})
        if predicted_demand:
            demand_trend = metrics.get('demand_trend', {})
            if demand_trend.get('trend_direction') == 'increasing':
                recommendations['recommendations'].append({
                    'priority': 'medium',
                    'category': 'planning',
                    'title': '需要増加への事前対応',
                    'description': '予測モデルによると今後需要が増加する見込みです。事前の人員計画を検討してください。',
                    'impact': 'long_term'
                })
        
        # データ品質改善推奨
        reliability = integrated_analysis.get('reliability_assessment', {})
        if reliability.get('overall_assessment') == 'low':
            recommendations['recommendations'].append({
                'priority': 'medium',
                'category': 'data_quality',
                'title': 'データ品質の向上',
                'description': '分析精度を向上させるため、シフトデータの完整性を改善してください。',
                'impact': 'long_term'
            })
        
        return recommendations
    
    def _assess_practicality(self, results: Dict) -> Dict[str, any]:
        """実用性評価"""
        assessment = {
            'practicality_score': 0.0,
            'business_impact': {},
            'implementation_feasibility': {},
            'roi_estimation': {}
        }
        
        # 分析結果の実用性評価
        integrated = results.get('integrated_analysis', {})
        current_shortage = integrated.get('current_shortage', {})
        daily_avg = current_shortage.get('daily_average', 0)
        
        # 現実性チェック
        realistic_range = 0 <= daily_avg <= 8  # 8時間/日以下が現実的
        
        assessment['business_impact'] = {
            'daily_shortage_realistic': realistic_range,
            'actionable_insights': len(results.get('optimization_recommendations', {}).get('recommendations', [])),
            'role_coverage': len(current_shortage.get('by_role', {}))
        }
        
        # 実装可能性
        reliability = integrated.get('reliability_assessment', {})
        assessment['implementation_feasibility'] = {
            'data_reliability': reliability.get('overall_assessment', 'unknown'),
            'analysis_complexity': 'moderate',
            'system_integration': 'compatible'
        }
        
        # ROI推定
        if daily_avg > 0:
            # 仮定：1時間不足 = 人件費損失2,000円/時間
            daily_cost_impact = daily_avg * 2000
            monthly_cost_impact = daily_cost_impact * 30
            
            assessment['roi_estimation'] = {
                'daily_cost_impact': daily_cost_impact,
                'monthly_cost_impact': monthly_cost_impact,
                'potential_savings': monthly_cost_impact * 0.3,  # 30%改善想定
                'payback_period': '3-6 months'
            }
        
        # 総合実用性スコア
        practicality_factors = [
            1.0 if realistic_range else 0.3,
            reliability.get('overall_score', 0.5),
            min(1.0, len(results.get('optimization_recommendations', {}).get('recommendations', [])) / 5)
        ]
        
        assessment['practicality_score'] = sum(practicality_factors) / len(practicality_factors)
        assessment['overall_assessment'] = (
            'high' if assessment['practicality_score'] > 0.75 else
            'medium' if assessment['practicality_score'] > 0.5 else
            'low'
        )
        
        return assessment
    
    def _save_results(self, results: Dict) -> None:
        """結果の保存"""
        output_file = self.data_dir / "integrated_smart_shortage_analysis.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # サマリーレポートの生成
        self._generate_summary_report(results)
        
        log.info(f"統合分析結果保存: {output_file}")
    
    def _generate_summary_report(self, results: Dict) -> None:
        """サマリーレポートの生成"""
        report_file = self.data_dir / "smart_shortage_summary_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== 統合型スマート過不足分析レポート ===\n")
            f.write(f"分析日時: {results['analysis_timestamp']}\n")
            f.write(f"分析手法: 動的リアルタイム分析 + 機械学習予測\n\n")
            
            # 現在の過不足状況
            integrated = results.get('integrated_analysis', {})
            current = integrated.get('current_shortage', {})
            
            f.write("【現在の過不足状況】\n")
            f.write(f"総不足時間: {current.get('total_hours', 0):.1f}時間\n")
            f.write(f"日平均不足: {current.get('daily_average', 0):.1f}時間/日\n")
            
            by_role = current.get('by_role', {})
            if by_role:
                f.write("\n職種別不足時間:\n")
                for role, hours in by_role.items():
                    f.write(f"  {role}: {hours:.1f}時間\n")
            
            # 推奨事項
            recommendations = results.get('optimization_recommendations', {}).get('recommendations', [])
            if recommendations:
                f.write("\n【最適化推奨事項】\n")
                for i, rec in enumerate(recommendations, 1):
                    f.write(f"{i}. [{rec['priority'].upper()}] {rec['title']}\n")
                    f.write(f"   {rec['description']}\n")
            
            # 実用性評価
            practicality = results.get('practicality_assessment', {})
            f.write(f"\n【実用性評価】\n")
            f.write(f"実用性スコア: {practicality.get('practicality_score', 0):.2f}\n")
            f.write(f"総合評価: {practicality.get('overall_assessment', 'unknown').upper()}\n")
            
            # ROI推定
            roi = practicality.get('roi_estimation', {})
            if roi:
                f.write(f"\n【ROI推定】\n")
                f.write(f"月次コスト影響: ¥{roi.get('monthly_cost_impact', 0):,.0f}\n")
                f.write(f"改善による削減見込み: ¥{roi.get('potential_savings', 0):,.0f}\n")
        
        log.info(f"サマリーレポート生成: {report_file}")

def run_integrated_smart_analysis(data_dir: str) -> Dict[str, any]:
    """統合型スマート過不足分析の実行"""
    system = IntegratedSmartShortageSystem(Path(data_dir))
    
    try:
        results = system.run_comprehensive_analysis()
        
        # 結果サマリー表示
        print("=== 統合型スマート過不足分析完了 ===")
        
        integrated = results.get('integrated_analysis', {})
        current = integrated.get('current_shortage', {})
        
        print(f"日平均不足: {current.get('daily_average', 0):.1f}時間/日")
        
        practicality = results.get('practicality_assessment', {})
        print(f"実用性評価: {practicality.get('overall_assessment', 'unknown').upper()}")
        
        recommendations = results.get('optimization_recommendations', {}).get('recommendations', [])
        print(f"推奨事項: {len(recommendations)}項目")
        
        return results
        
    except Exception as e:
        log.error(f"統合分析エラー: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python integrated_smart_shortage_system.py [データディレクトリ]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    result = run_integrated_smart_analysis(data_dir)
    print("\n統合型スマート過不足分析が完了しました！")