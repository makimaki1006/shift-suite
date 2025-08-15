# -*- coding: utf-8 -*-
"""
ROI定量分析システム
品質管理システム導入の投資対効果分析
"""

import json
from datetime import datetime
from pathlib import Path

class ROIAnalyzer:
    """ROI定量分析エンジン"""
    
    def __init__(self):
        self.analysis_date = datetime.now().isoformat()
        self.hourly_cost = 5000  # 円/時間 (技術者単価)
        self.roi_results = {
            "analysis_metadata": {
                "analysis_date": self.analysis_date,
                "hourly_cost_assumption": f"{self.hourly_cost}円/時間",
                "analysis_period": "24ヶ月",
                "discount_rate": "5%"
            }
        }
    
    def calculate_investment_costs(self):
        """投資コスト計算"""
        print("=== 投資コスト分析 ===")
        
        # 既投資済みコスト
        sunk_costs = {
            "system_development": {
                "hours": 40,
                "description": "品質管理システム開発完了",
                "cost": 40 * self.hourly_cost,
                "status": "完了"
            },
            "pilot_testing": {
                "hours": 8,
                "description": "パイロットテスト実施",
                "cost": 8 * self.hourly_cost, 
                "status": "完了"
            }
        }
        
        # 追加必要投資 (3つのシナリオ)
        additional_investments = {
            "scenario_minimal": {
                "description": "最小限実装 (Phase 1のみ)",
                "development_hours": 16,
                "implementation_hours": 162,
                "training_hours": 8,
                "total_hours": 186,
                "total_cost": 186 * self.hourly_cost,
                "success_probability": 0.85
            },
            "scenario_standard": {
                "description": "標準実装 (Phase 1-2)",
                "development_hours": 32,
                "implementation_hours": 216,
                "training_hours": 16,
                "total_hours": 264,
                "total_cost": 264 * self.hourly_cost,
                "success_probability": 0.70
            },
            "scenario_comprehensive": {
                "description": "包括実装 (Phase 1-3)",
                "development_hours": 48,
                "implementation_hours": 324,
                "training_hours": 24,
                "total_hours": 396,
                "total_cost": 396 * self.hourly_cost,
                "success_probability": 0.50
            }
        }
        
        # 継続運用コスト
        ongoing_costs_annual = {
            "system_maintenance": {
                "hours": 24,
                "cost": 24 * self.hourly_cost,
                "description": "システム保守・更新"
            },
            "quality_monitoring": {
                "hours": 36,
                "cost": 36 * self.hourly_cost,
                "description": "品質監視・改善活動"
            },
            "training_updates": {
                "hours": 12,
                "cost": 12 * self.hourly_cost,
                "description": "トレーニング・スキルアップ"
            }
        }
        
        total_sunk_cost = sum(item["cost"] for item in sunk_costs.values())
        total_annual_ongoing = sum(item["cost"] for item in ongoing_costs_annual.values())
        
        investment_analysis = {
            "sunk_costs": sunk_costs,
            "additional_investments": additional_investments,
            "ongoing_costs_annual": ongoing_costs_annual,
            "total_sunk_cost": total_sunk_cost,
            "total_annual_ongoing": total_annual_ongoing
        }
        
        self.roi_results["investment_costs"] = investment_analysis
        
        print(f"既投資コスト: {total_sunk_cost:,}円")
        print(f"最小追加投資: {additional_investments['scenario_minimal']['total_cost']:,}円")
        print(f"標準追加投資: {additional_investments['scenario_standard']['total_cost']:,}円")
        print(f"年間運用コスト: {total_annual_ongoing:,}円")
        
        return investment_analysis
    
    def calculate_expected_benefits(self):
        """期待効果計算"""
        print("\n=== 期待効果分析 ===")
        
        # 現状の非効率性コスト (年間)
        current_inefficiency_costs = {
            "document_review_time": {
                "current_hours_per_document": 2.0,
                "documents_per_month": 15,
                "annual_hours": 2.0 * 15 * 12,
                "annual_cost": 2.0 * 15 * 12 * self.hourly_cost,
                "description": "文書レビュー時間"
            },
            "quality_issues_rework": {
                "rework_hours_per_month": 20,
                "annual_hours": 20 * 12,
                "annual_cost": 20 * 12 * self.hourly_cost,
                "description": "品質問題による手戻り"
            },
            "stakeholder_confusion": {
                "confusion_resolution_hours_per_month": 8,
                "annual_hours": 8 * 12,
                "annual_cost": 8 * 12 * self.hourly_cost,
                "description": "文書理解不足による問い合わせ対応"
            },
            "reputation_risk": {
                "estimated_annual_cost": 200000,
                "description": "技術文書品質による信頼性リスク"
            }
        }
        
        # 品質向上による効果 (3シナリオ)
        quality_improvement_benefits = {
            "scenario_minimal": {
                "review_time_reduction": 0.25,  # 25%削減
                "rework_reduction": 0.30,       # 30%削減  
                "confusion_reduction": 0.20,    # 20%削減
                "reputation_improvement": 0.10  # 10%改善
            },
            "scenario_standard": {
                "review_time_reduction": 0.40,  # 40%削減
                "rework_reduction": 0.50,       # 50%削減
                "confusion_reduction": 0.35,    # 35%削減
                "reputation_improvement": 0.25  # 25%改善
            },
            "scenario_comprehensive": {
                "review_time_reduction": 0.55,  # 55%削減
                "rework_reduction": 0.70,       # 70%削減
                "confusion_reduction": 0.50,    # 50%削減
                "reputation_improvement": 0.40  # 40%改善
            }
        }
        
        # 各シナリオの年間効果計算
        annual_benefits = {}
        for scenario, improvements in quality_improvement_benefits.items():
            scenario_benefits = {
                "review_time_savings": current_inefficiency_costs["document_review_time"]["annual_cost"] * improvements["review_time_reduction"],
                "rework_savings": current_inefficiency_costs["quality_issues_rework"]["annual_cost"] * improvements["rework_reduction"],
                "confusion_savings": current_inefficiency_costs["stakeholder_confusion"]["annual_cost"] * improvements["confusion_reduction"],
                "reputation_value": current_inefficiency_costs["reputation_risk"]["estimated_annual_cost"] * improvements["reputation_improvement"]
            }
            scenario_benefits["total_annual_benefit"] = sum(scenario_benefits.values())
            annual_benefits[scenario] = scenario_benefits
        
        benefit_analysis = {
            "current_inefficiency_costs": current_inefficiency_costs,
            "quality_improvement_benefits": quality_improvement_benefits,
            "annual_benefits": annual_benefits,
            "total_current_annual_cost": sum(
                cost["annual_cost"] if "annual_cost" in cost 
                else cost["estimated_annual_cost"]
                for cost in current_inefficiency_costs.values()
            )
        }
        
        self.roi_results["expected_benefits"] = benefit_analysis
        
        print(f"現状年間非効率コスト: {benefit_analysis['total_current_annual_cost']:,}円")
        print(f"最小シナリオ年間効果: {annual_benefits['scenario_minimal']['total_annual_benefit']:,}円")
        print(f"標準シナリオ年間効果: {annual_benefits['scenario_standard']['total_annual_benefit']:,}円")
        print(f"包括シナリオ年間効果: {annual_benefits['scenario_comprehensive']['total_annual_benefit']:,}円")
        
        return benefit_analysis
    
    def calculate_roi_scenarios(self):
        """ROI シナリオ計算"""
        print("\n=== ROI シナリオ分析 ===")
        
        investment_data = self.roi_results["investment_costs"]
        benefit_data = self.roi_results["expected_benefits"]
        
        scenarios = ["scenario_minimal", "scenario_standard", "scenario_comprehensive"]
        roi_scenarios = {}
        
        for scenario in scenarios:
            # 投資コスト
            initial_investment = investment_data["additional_investments"][scenario]["total_cost"]
            annual_ongoing_cost = investment_data["total_annual_ongoing"]
            
            # 期待効果
            annual_benefit = benefit_data["annual_benefits"][scenario]["total_annual_benefit"]
            success_probability = investment_data["additional_investments"][scenario]["success_probability"]
            
            # 期待値調整
            expected_annual_benefit = annual_benefit * success_probability
            
            # ROI計算 (2年間)
            year1_net_benefit = expected_annual_benefit - annual_ongoing_cost
            year2_net_benefit = expected_annual_benefit - annual_ongoing_cost
            total_2year_benefit = year1_net_benefit + year2_net_benefit
            
            roi_2year = ((total_2year_benefit - initial_investment) / initial_investment) * 100 if initial_investment > 0 else 0
            
            # 損益分岐点
            if expected_annual_benefit > annual_ongoing_cost:
                payback_months = (initial_investment / (expected_annual_benefit - annual_ongoing_cost)) * 12
            else:
                payback_months = float('inf')
            
            # NPV計算 (簡易版、割引率5%)
            discount_rate = 0.05
            npv = -initial_investment
            for year in range(1, 3):
                npv += (expected_annual_benefit - annual_ongoing_cost) / ((1 + discount_rate) ** year)
            
            roi_scenarios[scenario] = {
                "initial_investment": initial_investment,
                "annual_benefit": annual_benefit,
                "expected_annual_benefit": expected_annual_benefit,
                "annual_ongoing_cost": annual_ongoing_cost,
                "roi_2year_percent": roi_2year,
                "payback_months": payback_months if payback_months != float('inf') else "N/A",
                "npv": npv,
                "success_probability": success_probability,
                "risk_adjusted_recommendation": self._get_risk_assessment(roi_2year, payback_months, success_probability)
            }
        
        self.roi_results["roi_scenarios"] = roi_scenarios
        
        # 結果表示
        for scenario, data in roi_scenarios.items():
            scenario_name = scenario.replace("scenario_", "")
            print(f"\n{scenario_name.upper()}シナリオ:")
            print(f"  投資額: {data['initial_investment']:,}円")
            print(f"  年間効果期待値: {data['expected_annual_benefit']:,}円")
            print(f"  2年間ROI: {data['roi_2year_percent']:.1f}%")
            print(f"  回収期間: {data['payback_months']}")
            print(f"  NPV: {data['npv']:,}円")
            print(f"  推奨度: {data['risk_adjusted_recommendation']}")
        
        return roi_scenarios
    
    def _get_risk_assessment(self, roi, payback_months, success_probability):
        """リスク評価"""
        if roi > 50 and payback_months != "N/A" and payback_months < 18 and success_probability > 0.7:
            return "強く推奨"
        elif roi > 25 and payback_months != "N/A" and payback_months < 24 and success_probability > 0.6:
            return "推奨"
        elif roi > 0 and payback_months != "N/A" and payback_months < 36:
            return "条件付推奨"
        else:
            return "推奨しない"
    
    def compare_with_alternatives(self):
        """代替案との比較"""
        print("\n=== 代替案比較分析 ===")
        
        alternatives = {
            "status_quo": {
                "investment": 0,
                "annual_benefit": 0,
                "annual_cost": 0,
                "roi_2year": 0,
                "description": "現状維持"
            },
            "external_audit": {
                "investment": 80000,  # 外部監査導入
                "annual_benefit": 800000,
                "annual_cost": 200000,
                "roi_2year": 650,  # ((800-200)*2 - 80) / 80 * 100
                "description": "外部品質監査"
            },
            "manual_checklist": {
                "investment": 40000,  # 手動チェックリスト強化
                "annual_benefit": 400000,
                "annual_cost": 100000, 
                "roi_2year": 1400,  # ((400-100)*2 - 40) / 40 * 100
                "description": "手動品質管理強化"
            }
        }
        
        # 自社システムの最適シナリオ選択
        roi_scenarios = self.roi_results["roi_scenarios"]
        best_internal_scenario = max(roi_scenarios.keys(), 
                                   key=lambda x: roi_scenarios[x]["roi_2year_percent"])
        best_internal_data = roi_scenarios[best_internal_scenario]
        
        alternatives["our_system_best"] = {
            "investment": best_internal_data["initial_investment"],
            "annual_benefit": best_internal_data["expected_annual_benefit"],
            "annual_cost": best_internal_data["annual_ongoing_cost"],
            "roi_2year": best_internal_data["roi_2year_percent"],
            "description": f"自社システム({best_internal_scenario.replace('scenario_', '')})"
        }
        
        # 比較分析
        comparison_analysis = {
            "alternatives": alternatives,
            "ranking": sorted(alternatives.items(), 
                            key=lambda x: x[1]["roi_2year"], reverse=True),
            "recommendation": self._get_alternative_recommendation(alternatives)
        }
        
        self.roi_results["alternative_comparison"] = comparison_analysis
        
        print("代替案ROI比較:")
        for name, data in sorted(alternatives.items(), key=lambda x: x[1]["roi_2year"], reverse=True):
            print(f"  {data['description']}: {data['roi_2year']:.1f}%")
        
        return comparison_analysis
    
    def _get_alternative_recommendation(self, alternatives):
        """代替案推奨判定"""
        sorted_alternatives = sorted(alternatives.items(), key=lambda x: x[1]["roi_2year"], reverse=True)
        
        top_alternative = sorted_alternatives[0]
        our_system_rank = next(i for i, (name, _) in enumerate(sorted_alternatives) if name == "our_system_best")
        
        if our_system_rank == 0:
            return "自社システムが最適"
        elif our_system_rank <= 1:
            return "自社システムは有力候補"
        else:
            return f"{top_alternative[1]['description']}が最適、自社システムは{our_system_rank + 1}位"
    
    def generate_executive_summary(self):
        """エグゼクティブサマリー生成"""
        print("\n=== エグゼクティブサマリー ===")
        
        roi_scenarios = self.roi_results["roi_scenarios"]
        comparison = self.roi_results["alternative_comparison"]
        
        # 最適シナリオ選定
        recommended_scenario = max(roi_scenarios.keys(), 
                                 key=lambda x: roi_scenarios[x]["roi_2year_percent"] 
                                 * roi_scenarios[x]["success_probability"])
        recommended_data = roi_scenarios[recommended_scenario]
        
        executive_summary = {
            "recommendation": {
                "decision": "条件付き実行推奨",
                "recommended_scenario": recommended_scenario.replace("scenario_", ""),
                "key_metrics": {
                    "initial_investment": f"{recommended_data['initial_investment']:,}円",
                    "roi_2year": f"{recommended_data['roi_2year_percent']:.1f}%",
                    "payback_period": f"{recommended_data['payback_months']}ヶ月",
                    "success_probability": f"{recommended_data['success_probability']*100:.0f}%"
                }
            },
            "critical_success_factors": [
                "自動修正機能の16時間での開発完了",
                "段階的品質基準による現実的目標設定", 
                "継続運用体制(年間72時間)の確保",
                "効果測定による継続改善"
            ],
            "major_risks": [
                "修正工数が想定の2倍に拡大するリスク",
                "組織的受容性が想定を下回るリスク",
                "技術的複雑性による運用負荷増大リスク"
            ],
            "decision_timeline": {
                "immediate_action": "48時間以内に最終GO/NO-GO判定", 
                "pilot_expansion": "4週間で限定実装・効果測定",
                "full_deployment": "12週間で本格運用移行"
            }
        }
        
        self.roi_results["executive_summary"] = executive_summary
        
        print(f"推奨判定: {executive_summary['recommendation']['decision']}")
        print(f"推奨シナリオ: {executive_summary['recommendation']['recommended_scenario']}")
        print(f"投資額: {executive_summary['recommendation']['key_metrics']['initial_investment']}")
        print(f"2年間ROI: {executive_summary['recommendation']['key_metrics']['roi_2year']}")
        print(f"回収期間: {executive_summary['recommendation']['key_metrics']['payback_period']}")
        
        return executive_summary
    
    def save_comprehensive_report(self):
        """包括レポート保存"""
        report_file = Path("roi_comprehensive_analysis.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.roi_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n包括的ROI分析レポート保存: {report_file}")
        return self.roi_results

def main():
    """メイン実行関数"""
    print("ROI定量分析システム実行開始")
    print("=" * 60)
    
    analyzer = ROIAnalyzer()
    
    # 段階的分析実行
    analyzer.calculate_investment_costs()
    analyzer.calculate_expected_benefits()
    analyzer.calculate_roi_scenarios()
    analyzer.compare_with_alternatives()
    analyzer.generate_executive_summary()
    
    # レポート保存
    final_results = analyzer.save_comprehensive_report()
    
    print("=" * 60)
    print("ROI定量分析完了")
    
    return final_results

if __name__ == "__main__":
    main()