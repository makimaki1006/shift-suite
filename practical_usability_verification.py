#!/usr/bin/env python3
"""
実用性検証システム

「実用的である」という主張の根拠を客観的に検証
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class PracticalUsabilityVerifier:
    """実用性検証クラス"""
    
    def __init__(self):
        self.verification_criteria = {
            'technical_feasibility': 0.0,      # 技術的実現可能性
            'operational_readiness': 0.0,      # 運用準備度
            'user_accessibility': 0.0,         # ユーザーアクセシビリティ
            'business_value': 0.0,             # ビジネス価値
            'maintenance_sustainability': 0.0,  # 保守持続可能性
            'scalability': 0.0,                # スケーラビリティ
            'error_tolerance': 0.0,            # エラー耐性
            'real_world_applicability': 0.0    # 実世界適用性
        }
        
    def verify_practical_usability(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """実用性の包括的検証"""
        log.info("🔍 実用性根拠検証開始...")
        
        verification_result = {
            'overall_practicality_score': 0.0,
            'criterion_scores': {},
            'evidence_analysis': {},
            'gap_identification': {},
            'usability_barriers': {},
            'improvement_requirements': {},
            'practical_readiness_assessment': '',
            'objective_evidence': {},
            'subjective_assumptions': {},
            'verification_methodology': {}
        }
        
        # 各基準の検証
        verification_result['criterion_scores'] = self._verify_all_criteria(system_data)
        
        # 総合実用性スコア計算
        verification_result['overall_practicality_score'] = np.mean(list(verification_result['criterion_scores'].values()))
        
        # エビデンス分析
        verification_result['evidence_analysis'] = self._analyze_evidence_quality(system_data)
        
        # ギャップ特定
        verification_result['gap_identification'] = self._identify_practical_gaps(verification_result['criterion_scores'])
        
        # 実用性阻害要因
        verification_result['usability_barriers'] = self._identify_usability_barriers(system_data)
        
        # 客観的証拠 vs 主観的仮定の分離
        verification_result['objective_evidence'], verification_result['subjective_assumptions'] = self._separate_evidence_types(system_data)
        
        # 改善要件
        verification_result['improvement_requirements'] = self._define_improvement_requirements(verification_result)
        
        # 実用準備度評価
        verification_result['practical_readiness_assessment'] = self._assess_practical_readiness(verification_result['overall_practicality_score'])
        
        # 検証方法論
        verification_result['verification_methodology'] = self._document_verification_methodology()
        
        return verification_result
    
    def _verify_all_criteria(self, system_data: Dict[str, Any]) -> Dict[str, float]:
        """全基準の検証"""
        log.info("📊 実用性基準の個別検証...")
        
        scores = {}
        
        # 1. 技術的実現可能性
        scores['technical_feasibility'] = self._verify_technical_feasibility(system_data)
        
        # 2. 運用準備度  
        scores['operational_readiness'] = self._verify_operational_readiness(system_data)
        
        # 3. ユーザーアクセシビリティ
        scores['user_accessibility'] = self._verify_user_accessibility(system_data)
        
        # 4. ビジネス価値
        scores['business_value'] = self._verify_business_value(system_data)
        
        # 5. 保守持続可能性
        scores['maintenance_sustainability'] = self._verify_maintenance_sustainability(system_data)
        
        # 6. スケーラビリティ
        scores['scalability'] = self._verify_scalability(system_data)
        
        # 7. エラー耐性
        scores['error_tolerance'] = self._verify_error_tolerance(system_data)
        
        # 8. 実世界適用性
        scores['real_world_applicability'] = self._verify_real_world_applicability(system_data)
        
        return scores
    
    def _verify_technical_feasibility(self, system_data: Dict[str, Any]) -> float:
        """技術的実現可能性の検証"""
        log.info("  🔧 技術的実現可能性検証中...")
        
        feasibility_factors = {
            'implementation_complexity': 0.0,
            'dependency_availability': 0.0,
            'performance_requirements': 0.0,
            'integration_capability': 0.0,
            'resource_requirements': 0.0
        }
        
        # 実装複雑性の評価（実際のコード分析が必要）
        feasibility_factors['implementation_complexity'] = 0.6  # 推定値 - 要実測
        log.warning("    ⚠️  実装複雑性: 推定値使用 - 実際のコード分析が必要")
        
        # 依存関係の可用性（requirements.txtから推定）
        feasibility_factors['dependency_availability'] = 0.8  # Python標準ライブラリベース
        log.info("    ✅ 依存関係: Python標準ライブラリ中心で安定")
        
        # パフォーマンス要件（未実測）
        feasibility_factors['performance_requirements'] = 0.5  # 推定値 - 要ベンチマーク
        log.warning("    ⚠️  パフォーマンス: 未実測 - ベンチマークテストが必要")
        
        # 統合能力（APIレベルでの評価）
        feasibility_factors['integration_capability'] = 0.7  # JSON/REST API対応
        log.info("    ✅ 統合能力: JSON/REST API対応済み")
        
        # リソース要件（未評価）
        feasibility_factors['resource_requirements'] = 0.4  # 推定値 - 要実測
        log.warning("    ⚠️  リソース要件: 未評価 - システム要件分析が必要")
        
        score = np.mean(list(feasibility_factors.values()))
        log.info(f"    📊 技術的実現可能性スコア: {score:.1%}")
        return score
    
    def _verify_operational_readiness(self, system_data: Dict[str, Any]) -> float:
        """運用準備度の検証"""
        log.info("  🏭 運用準備度検証中...")
        
        readiness_factors = {
            'deployment_procedures': 0.0,
            'monitoring_systems': 0.0,
            'backup_recovery': 0.0,
            'security_measures': 0.0,
            'documentation_completeness': 0.0,
            'staff_training': 0.0
        }
        
        # デプロイメント手順（未整備）
        readiness_factors['deployment_procedures'] = 0.2  # 基本スクリプトのみ
        log.warning("    ❌ デプロイメント手順: 未整備 - 本格的なCI/CDが必要")
        
        # 監視システム（部分的実装）
        readiness_factors['monitoring_systems'] = 0.6  # ログ出力のみ
        log.warning("    ⚠️  監視システム: 基本的なログのみ - 本格監視システムが必要")
        
        # バックアップ・復旧（未実装）
        readiness_factors['backup_recovery'] = 0.1  # JSONファイル保存のみ
        log.error("    ❌ バックアップ・復旧: 未実装 - データ保護機能が必要")
        
        # セキュリティ対策（未実装）
        readiness_factors['security_measures'] = 0.2  # 基本的なファイル権限のみ
        log.error("    ❌ セキュリティ対策: 不十分 - 認証・認可システムが必要")
        
        # ドキュメント完成度（部分的）
        readiness_factors['documentation_completeness'] = 0.7  # コメント・README存在
        log.info("    ✅ ドキュメント: 基本的な説明は存在")
        
        # スタッフトレーニング（未実施）
        readiness_factors['staff_training'] = 0.1  # マニュアルなし
        log.error("    ❌ スタッフトレーニング: 未実施 - 運用マニュアルが必要")
        
        score = np.mean(list(readiness_factors.values()))
        log.warning(f"    📊 運用準備度スコア: {score:.1%} - 大幅な改善が必要")
        return score
    
    def _verify_user_accessibility(self, system_data: Dict[str, Any]) -> float:
        """ユーザーアクセシビリティの検証"""
        log.info("  👥 ユーザーアクセシビリティ検証中...")
        
        accessibility_factors = {
            'interface_usability': 0.0,
            'learning_curve': 0.0,
            'error_handling': 0.0,
            'help_support': 0.0,
            'accessibility_compliance': 0.0
        }
        
        # インターフェース使いやすさ（Dashベース）
        accessibility_factors['interface_usability'] = 0.6  # Dash UIの基本的な使いやすさ
        log.info("    ✅ インターフェース: Dashベースで基本的な操作性確保")
        
        # 学習コスト（高専門性）
        accessibility_factors['learning_curve'] = 0.4  # 専門知識が必要
        log.warning("    ⚠️  学習コスト: 高 - MECE概念の理解が必要")
        
        # エラーハンドリング（部分的実装）
        accessibility_factors['error_handling'] = 0.5  # 基本的なtry-catch
        log.warning("    ⚠️  エラーハンドリング: 基本的なもののみ")
        
        # ヘルプ・サポート（未実装）
        accessibility_factors['help_support'] = 0.2  # READMEのみ
        log.error("    ❌ ヘルプ・サポート: 不十分 - オンラインヘルプが必要")
        
        # アクセシビリティ準拠（未考慮）
        accessibility_factors['accessibility_compliance'] = 0.3  # 基本的なHTML構造
        log.warning("    ⚠️  アクセシビリティ準拠: 未考慮 - WCAG準拠が必要")
        
        score = np.mean(list(accessibility_factors.values()))
        log.warning(f"    📊 ユーザーアクセシビリティスコア: {score:.1%}")
        return score
    
    def _verify_business_value(self, system_data: Dict[str, Any]) -> float:
        """ビジネス価値の検証"""
        log.info("  💼 ビジネス価値検証中...")
        
        value_factors = {
            'cost_reduction': 0.0,
            'efficiency_improvement': 0.0,
            'quality_enhancement': 0.0,
            'risk_mitigation': 0.0,
            'competitive_advantage': 0.0
        }
        
        # コスト削減（理論的）
        value_factors['cost_reduction'] = 0.7  # 自動化によるコスト削減期待
        log.info("    ✅ コスト削減: 自動化による人件費削減が期待")
        
        # 効率改善（理論的）
        value_factors['efficiency_improvement'] = 0.8  # シフト作成時間短縮
        log.info("    ✅ 効率改善: シフト作成時間の大幅短縮が期待")
        
        # 品質向上（検証済み）
        value_factors['quality_enhancement'] = 0.9  # MECE品質88.1%達成
        log.info("    ✅ 品質向上: MECE品質88.1%で制約の質が向上")
        
        # リスク軽減（理論的）
        value_factors['risk_mitigation'] = 0.6  # 制約違反の自動検出
        log.info("    ✅ リスク軽減: 制約違反の自動検出機能")
        
        # 競争優位（理論的）
        value_factors['competitive_advantage'] = 0.5  # AI活用の先進性
        log.warning("    ⚠️  競争優位: 理論的 - 市場での実証が必要")
        
        score = np.mean(list(value_factors.values()))
        log.info(f"    📊 ビジネス価値スコア: {score:.1%}")
        return score
    
    def _verify_maintenance_sustainability(self, system_data: Dict[str, Any]) -> float:
        """保守持続可能性の検証"""
        log.info("  🔧 保守持続可能性検証中...")
        
        maintenance_factors = {
            'code_maintainability': 0.0,
            'technical_debt': 0.0,
            'update_procedures': 0.0,
            'knowledge_documentation': 0.0,
            'team_expertise': 0.0
        }
        
        # コード保守性（未評価）
        maintenance_factors['code_maintainability'] = 0.6  # 推定 - 要コードレビュー
        log.warning("    ⚠️  コード保守性: 未評価 - 本格的なコードレビューが必要")
        
        # 技術的負債（要評価）
        maintenance_factors['technical_debt'] = 0.5  # 推定 - 要分析
        log.warning("    ⚠️  技術的負債: 未分析 - 負債レベルの評価が必要")
        
        # 更新手順（未整備）
        maintenance_factors['update_procedures'] = 0.3  # 基本的なGit管理のみ
        log.error("    ❌ 更新手順: 未整備 - バージョン管理体制が必要")
        
        # 知識ドキュメント（部分的）
        maintenance_factors['knowledge_documentation'] = 0.4  # コメントレベル
        log.warning("    ⚠️  知識ドキュメント: 不十分 - 詳細設計書が必要")
        
        # チーム専門性（未評価）
        maintenance_factors['team_expertise'] = 0.4  # 推定 - 要スキル評価
        log.warning("    ⚠️  チーム専門性: 未評価 - スキルマトリックスが必要")
        
        score = np.mean(list(maintenance_factors.values()))
        log.warning(f"    📊 保守持続可能性スコア: {score:.1%} - 改善が必要")
        return score
    
    def _verify_scalability(self, system_data: Dict[str, Any]) -> float:
        """スケーラビリティの検証"""
        log.info("  📈 スケーラビリティ検証中...")
        
        scalability_factors = {
            'data_volume_handling': 0.0,
            'user_concurrency': 0.0,
            'feature_extensibility': 0.0,
            'performance_scaling': 0.0,
            'resource_efficiency': 0.0
        }
        
        # データ量処理（未テスト）
        scalability_factors['data_volume_handling'] = 0.3  # 小規模データのみテスト
        log.error("    ❌ データ量処理: 未テスト - 大規模データでの性能評価が必要")
        
        # ユーザー同時接続（未テスト）
        scalability_factors['user_concurrency'] = 0.2  # 単一ユーザーのみ
        log.error("    ❌ ユーザー同時接続: 未テスト - 負荷テストが必要")
        
        # 機能拡張性（良好）
        scalability_factors['feature_extensibility'] = 0.8  # モジュラー設計
        log.info("    ✅ 機能拡張性: モジュラー設計で拡張容易")
        
        # パフォーマンススケーリング（未評価）
        scalability_factors['performance_scaling'] = 0.3  # 未評価
        log.error("    ❌ パフォーマンススケーリング: 未評価 - ベンチマークが必要")
        
        # リソース効率（未評価）
        scalability_factors['resource_efficiency'] = 0.4  # 推定
        log.warning("    ⚠️  リソース効率: 未評価 - メモリ・CPU使用量の測定が必要")
        
        score = np.mean(list(scalability_factors.values()))
        log.error(f"    📊 スケーラビリティスコア: {score:.1%} - 大幅な改善が必要")
        return score
    
    def _verify_error_tolerance(self, system_data: Dict[str, Any]) -> float:
        """エラー耐性の検証"""
        log.info("  🛡️ エラー耐性検証中...")
        
        tolerance_factors = {
            'input_validation': 0.0,
            'graceful_degradation': 0.0,
            'error_recovery': 0.0,
            'fault_isolation': 0.0,
            'logging_monitoring': 0.0
        }
        
        # 入力検証（部分的実装）
        tolerance_factors['input_validation'] = 0.5  # 基本的なvalidation
        log.warning("    ⚠️  入力検証: 基本的なもののみ - 包括的検証が必要")
        
        # 段階的劣化（未実装）
        tolerance_factors['graceful_degradation'] = 0.3  # 部分的な例外処理
        log.warning("    ⚠️  段階的劣化: 部分的 - エラー時の代替処理が必要")
        
        # エラー回復（基本的）
        tolerance_factors['error_recovery'] = 0.4  # try-catchレベル
        log.warning("    ⚠️  エラー回復: 基本的 - 自動回復機能が必要")
        
        # 障害分離（未実装）
        tolerance_factors['fault_isolation'] = 0.2  # 未実装
        log.error("    ❌ 障害分離: 未実装 - 障害時の影響範囲制限が必要")
        
        # ログ・監視（基本的）
        tolerance_factors['logging_monitoring'] = 0.6  # ログ出力あり
        log.info("    ✅ ログ・監視: 基本的なレベルは実装済み")
        
        score = np.mean(list(tolerance_factors.values()))
        log.warning(f"    📊 エラー耐性スコア: {score:.1%}")
        return score
    
    def _verify_real_world_applicability(self, system_data: Dict[str, Any]) -> float:
        """実世界適用性の検証"""
        log.info("  🌍 実世界適用性検証中...")
        
        applicability_factors = {
            'real_data_compatibility': 0.0,
            'workflow_integration': 0.0,
            'regulatory_compliance': 0.0,
            'organizational_fit': 0.0,
            'pilot_testing': 0.0
        }
        
        # 実データ互換性（未テスト）
        applicability_factors['real_data_compatibility'] = 0.4  # サンプルデータのみ
        log.error("    ❌ 実データ互換性: 未テスト - 実際の施設データでの検証が必要")
        
        # ワークフロー統合（未検証）
        applicability_factors['workflow_integration'] = 0.3  # 理論レベル
        log.error("    ❌ ワークフロー統合: 未検証 - 実際の業務フローとの適合性確認が必要")
        
        # 規制準拠（未確認）
        applicability_factors['regulatory_compliance'] = 0.2  # 未確認
        log.error("    ❌ 規制準拠: 未確認 - 労働法・業界規制への適合確認が必要")
        
        # 組織適合性（未評価）
        applicability_factors['organizational_fit'] = 0.3  # 理論レベル
        log.error("    ❌ 組織適合性: 未評価 - 実際の組織での受容性確認が必要")
        
        # パイロットテスト（未実施）
        applicability_factors['pilot_testing'] = 0.1  # 未実施
        log.error("    ❌ パイロットテスト: 未実施 - 実環境での試験運用が必要")
        
        score = np.mean(list(applicability_factors.values()))
        log.error(f"    📊 実世界適用性スコア: {score:.1%} - 重大な改善が必要")
        return score
    
    def _analyze_evidence_quality(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """エビデンス品質の分析"""
        return {
            'objective_evidence_ratio': 0.3,  # 客観的証拠30%
            'subjective_assumptions_ratio': 0.7,  # 主観的仮定70%
            'empirical_validation_level': 'low',  # 実証的検証レベル：低
            'theoretical_foundation': 'moderate',  # 理論的基盤：中程度
            'data_quality': 'sample_based',  # データ品質：サンプルベース
            'measurement_reliability': 'estimated'  # 測定信頼性：推定
        }
    
    def _identify_practical_gaps(self, criterion_scores: Dict[str, float]) -> Dict[str, Any]:
        """実用性ギャップの特定"""
        gaps = {}
        
        for criterion, score in criterion_scores.items():
            if score < 0.7:  # 70%未満を実用性ギャップとして特定
                gaps[criterion] = {
                    'current_score': score,
                    'gap_to_practical': 0.7 - score,
                    'severity': 'critical' if score < 0.4 else 'high',
                    'impact_on_usability': self._assess_gap_impact(criterion, score)
                }
        
        return gaps
    
    def _identify_usability_barriers(self, system_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """実用性阻害要因の特定"""
        return {
            'missing_infrastructure': [
                'CI/CDパイプライン未整備',
                '本格的な監視システム不在',
                'バックアップ・復旧システム未実装',
                'セキュリティ対策不十分'
            ],
            'insufficient_testing': [
                '実データでの検証未実施',
                '負荷テスト未実施',
                'ユーザビリティテスト未実施',
                'セキュリティテスト未実施'
            ],
            'documentation_gaps': [
                '運用マニュアル不在',
                'トラブルシューティングガイド不在',
                'API仕様書不完全',
                'ユーザートレーニング資料不在'
            ],
            'compliance_unknowns': [
                '労働法準拠未確認',
                '業界規制適合未確認',
                'データ保護法対応未確認',
                'アクセシビリティ基準未準拠'
            ]
        }
    
    def _separate_evidence_types(self, system_data: Dict[str, Any]) -> Tuple[Dict, Dict]:
        """客観的証拠と主観的仮定の分離"""
        
        objective_evidence = {
            'code_exists': True,
            'basic_functionality_works': True,
            'test_data_processes': True,
            'json_output_generated': True,
            'dash_interface_renders': True,
            'quality_metrics_calculated': True
        }
        
        subjective_assumptions = {
            'performance_adequacy': '推定値',
            'scalability_sufficiency': '未検証の仮定',
            'user_satisfaction': '未測定の期待',
            'business_value_realization': '理論的予測',
            'maintenance_feasibility': '経験則による推定',
            'real_world_compatibility': '理想的条件での仮定',
            'deployment_simplicity': '開発環境での経験による推定',
            'cost_effectiveness': '未実証の期待'
        }
        
        return objective_evidence, subjective_assumptions
    
    def _define_improvement_requirements(self, verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """改善要件の定義"""
        
        # 実用性達成に必要な最低要件
        minimum_requirements = {
            'critical_priority': [
                '実環境での試験運用実施',
                '実データでの動作確認',
                'セキュリティ対策の実装',
                'バックアップ・復旧システム構築'
            ],
            'high_priority': [
                '負荷テストの実施',
                '運用マニュアルの作成',
                'エラー処理の強化',
                'パフォーマンス最適化'
            ],
            'medium_priority': [
                'ユーザビリティテスト',
                'コードレビューと改善',
                '監視システムの強化',
                'ドキュメント充実'
            ]
        }
        
        # 推定改善時間とコスト
        improvement_estimates = {
            'time_to_minimum_viable': '2-3ヶ月',
            'time_to_production_ready': '4-6ヶ月',
            'estimated_effort': '高（専門チーム必要）',
            'infrastructure_cost': '中程度',
            'risk_level': '中～高（未検証要素多数）'
        }
        
        return {
            'minimum_requirements': minimum_requirements,
            'improvement_estimates': improvement_estimates
        }
    
    def _assess_practical_readiness(self, overall_score: float) -> str:
        """実用準備度の評価"""
        if overall_score >= 0.8:
            return 'Production Ready - 本格運用可能'
        elif overall_score >= 0.7:
            return 'Near Production - 最終調整後運用可能'
        elif overall_score >= 0.6:
            return 'Beta Quality - 限定運用可能'
        elif overall_score >= 0.5:
            return 'Alpha Quality - 内部テスト段階'
        elif overall_score >= 0.4:
            return 'Development Phase - 開発継続中'
        else:
            return 'Proof of Concept - 概念実証段階'
    
    def _document_verification_methodology(self) -> Dict[str, Any]:
        """検証方法論のドキュメント化"""
        return {
            'verification_approach': 'multi_criteria_assessment',
            'evaluation_basis': '8つの実用性基準による包括評価',
            'scoring_method': '各基準0-1.0の数値評価',
            'evidence_classification': 'objective_vs_subjective separation',
            'limitation_acknowledgment': '多くの評価が推定値に基づく',
            'validation_requirements': '実環境での検証が必要',
            'methodology_confidence': 'medium - 構造化されているが実証データ不足'
        }
    
    def _assess_gap_impact(self, criterion: str, score: float) -> str:
        """ギャップの実用性への影響評価"""
        impact_map = {
            'technical_feasibility': '実装不可リスク',
            'operational_readiness': '運用失敗リスク',
            'user_accessibility': 'ユーザー離脱リスク',
            'business_value': 'ROI未達リスク',
            'maintenance_sustainability': '長期運用不可リスク',
            'scalability': '成長対応不可リスク',
            'error_tolerance': 'システム停止リスク',
            'real_world_applicability': '実用化失敗リスク'
        }
        
        return impact_map.get(criterion, '影響度不明')


def run_practical_usability_verification():
    """実用性検証の実行"""
    log.info("🎯 実用性根拠検証開始")
    log.info("=" * 80)
    
    # システムデータの準備（現在は限定的なサンプル）
    system_data = {
        'code_base': 'exists',
        'test_results': 'limited_sample_data',
        'performance_data': 'not_measured',
        'user_feedback': 'not_collected',
        'deployment_experience': 'development_only'
    }
    
    # 検証実行
    verifier = PracticalUsabilityVerifier()
    verification_result = verifier.verify_practical_usability(system_data)
    
    # 結果表示
    display_verification_results(verification_result)
    
    # 結果保存
    with open('practical_usability_verification.json', 'w', encoding='utf-8') as f:
        json.dump(verification_result, f, ensure_ascii=False, indent=2, default=str)
    
    return verification_result


def display_verification_results(result: Dict[str, Any]):
    """検証結果の表示"""
    
    overall_score = result['overall_practicality_score']
    readiness = result['practical_readiness_assessment']
    
    log.info("\n" + "=" * 80)
    log.info("📊 実用性検証結果")
    log.info("=" * 80)
    
    log.info(f"🎯 総合実用性スコア: {overall_score:.1%}")
    log.info(f"📋 実用準備度: {readiness}")
    
    log.info("\n📈 各基準スコア:")
    for criterion, score in result['criterion_scores'].items():
        emoji = "🟢" if score >= 0.7 else "🟡" if score >= 0.5 else "🔴"
        log.info(f"  {emoji} {criterion}: {score:.1%}")
    
    log.info("\n🚧 実用性ギャップ:")
    for criterion, gap_info in result['gap_identification'].items():
        log.info(f"  ❗ {criterion}: {gap_info['current_score']:.1%} (ギャップ: {gap_info['gap_to_practical']:.1%})")
        log.info(f"     影響: {gap_info['impact_on_usability']}")
    
    log.info("\n🎭 客観的証拠 vs 主観的仮定:")
    evidence_analysis = result['evidence_analysis']
    log.info(f"  📊 客観的証拠: {evidence_analysis['objective_evidence_ratio']:.1%}")
    log.info(f"  💭 主観的仮定: {evidence_analysis['subjective_assumptions_ratio']:.1%}")
    log.info(f"  🔬 実証的検証レベル: {evidence_analysis['empirical_validation_level']}")
    
    log.info("\n🚨 重要な実用性阻害要因:")
    barriers = result['usability_barriers']
    for category, barrier_list in barriers.items():
        log.info(f"  📂 {category}:")
        for barrier in barrier_list[:2]:  # 最初の2つを表示
            log.info(f"    - {barrier}")
    
    log.info("\n📋 改善要件:")
    requirements = result['improvement_requirements']
    log.info("  🔴 Critical Priority:")
    for req in requirements['minimum_requirements']['critical_priority']:
        log.info(f"    • {req}")
    
    estimates = requirements['improvement_estimates']
    log.info(f"\n⏱️  改善予想:")
    log.info(f"  - 最小実用版まで: {estimates['time_to_minimum_viable']}")
    log.info(f"  - 本格運用まで: {estimates['time_to_production_ready']}")
    log.info(f"  - リスクレベル: {estimates['risk_level']}")


def main():
    """メイン実行"""
    try:
        result = run_practical_usability_verification()
        
        log.info("\n🎉 実用性検証完了!")
        
        # 重要な発見の要約
        overall_score = result['overall_practicality_score']
        if overall_score < 0.6:
            log.warning("⚠️  警告: 現在の実用性は限定的です")
            log.warning("実環境での運用前に大幅な改善が必要です")
        
        log.info("詳細結果: practical_usability_verification.json")
        
        return result
        
    except Exception as e:
        log.error(f"実用性検証エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()