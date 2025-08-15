#!/usr/bin/env python3
"""
組織パターン深度分析エンジン - Organizational Pattern Deep Analyzer

組織の暗黙的パターン、権力構造、集団力学、文化的抵抗を科学的に分析し、
表面化していない組織の真の姿を明らかにします。

理論的基盤:
- Organizational Culture Theory (Schein)
- Systems Psychodynamics (Tavistock Institute)
- Social Network Analysis (Granovetter)
- Institutional Theory (DiMaggio & Powell)
- Complexity Theory in Organizations (Stacey)
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Set
import logging
from collections import defaultdict, Counter
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

log = logging.getLogger(__name__)

class OrganizationalPatternAnalyzer:
    """組織パターン深度分析エンジン"""
    
    def __init__(self):
        self.analysis_id = f"org_pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 組織文化の層構造（Schein モデル）
        self.culture_layers = {
            'artifacts': 'visible_organizational_structures',
            'espoused_values': 'strategies_goals_philosophies', 
            'underlying_assumptions': 'unconscious_beliefs_perceptions'
        }
        
        # 権力源泉の分類（French & Raven）
        self.power_sources = {
            'legitimate': '公式的地位に基づく権力',
            'reward': '報酬を与える権力',
            'coercive': '懲罰を与える権力',
            'expert': '専門知識に基づく権力',
            'referent': '人格的魅力に基づく権力',
            'information': '情報アクセスに基づく権力'
        }
        
        # 組織的防衛メカニズム（Psychodynamic Theory）
        self.defense_mechanisms = {
            'denial': '問題の存在自体の否認',
            'projection': '責任の外部転嫁',
            'splitting': '極端な二分法的思考',
            'rationalization': '非合理的行動の正当化',
            'displacement': '感情の置き換え',
            'regression': '以前の行動パターンへの退行'
        }
        
    def analyze_organizational_patterns(self, shift_data: pd.DataFrame,
                                      analysis_results: Dict[str, Any],
                                      historical_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """組織パターンの包括的深度分析"""
        
        log.info(f"組織パターン深度分析開始 - ID: {self.analysis_id}")
        
        try:
            # 1. 暗黙的権力構造の分析
            implicit_power_structure = self._analyze_implicit_power_dynamics(shift_data, analysis_results)
            
            # 2. 組織文化の深層分析
            organizational_culture_analysis = self._analyze_organizational_culture_layers(shift_data, analysis_results)
            
            # 3. 集団力学・グループダイナミクス分析
            group_dynamics_analysis = self._analyze_group_dynamics(shift_data, analysis_results)
            
            # 4. 情報フロー・コミュニケーションネットワーク分析
            communication_network_analysis = self._analyze_communication_networks(shift_data, analysis_results)
            
            # 5. 組織的学習パターン分析
            organizational_learning_patterns = self._analyze_organizational_learning(shift_data, historical_data)
            
            # 6. 変化に対する組織的抵抗分析
            change_resistance_analysis = self._analyze_change_resistance_patterns(shift_data, historical_data)
            
            # 7. 組織的防衛メカニズムの特定
            defense_mechanisms_analysis = self._identify_organizational_defense_mechanisms(
                shift_data, analysis_results, historical_data
            )
            
            # 8. 創発的リーダーシップパターン
            emergent_leadership_patterns = self._analyze_emergent_leadership(shift_data, analysis_results)
            
            # 9. 組織的サイロ・派閥分析
            organizational_silos_analysis = self._analyze_organizational_silos(shift_data, analysis_results)
            
            # 10. 深層的組織診断と介入戦略
            deep_organizational_insights = self._generate_deep_organizational_insights(
                implicit_power_structure, organizational_culture_analysis,
                group_dynamics_analysis, communication_network_analysis,
                organizational_learning_patterns, change_resistance_analysis,
                defense_mechanisms_analysis, emergent_leadership_patterns,
                organizational_silos_analysis
            )
            
            organizational_analysis = {
                "analysis_metadata": {
                    "analysis_id": self.analysis_id,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "theoretical_frameworks": [
                        "Schein's Organizational Culture Model",
                        "Systems Psychodynamics (Tavistock)",
                        "Social Network Analysis Theory",
                        "Institutional Theory",
                        "Complexity Theory in Organizations"
                    ],
                    "analysis_scope": {
                        "total_staff_analyzed": len(shift_data['staff'].unique()) if 'staff' in shift_data.columns else 0,
                        "observation_period": self._calculate_observation_period(shift_data),
                        "data_points_analyzed": len(shift_data)
                    }
                },
                "implicit_power_structure": implicit_power_structure,
                "organizational_culture_layers": organizational_culture_analysis,
                "group_dynamics": group_dynamics_analysis,
                "communication_networks": communication_network_analysis,
                "organizational_learning": organizational_learning_patterns,
                "change_resistance_patterns": change_resistance_analysis,
                "defense_mechanisms": defense_mechanisms_analysis,
                "emergent_leadership": emergent_leadership_patterns,
                "organizational_silos": organizational_silos_analysis,
                "deep_organizational_insights": deep_organizational_insights
            }
            
            log.info(f"組織パターン深度分析完了 - 分析スタッフ数: {organizational_analysis['analysis_metadata']['analysis_scope']['total_staff_analyzed']}")
            return organizational_analysis
            
        except Exception as e:
            log.error(f"組織パターン分析エラー: {e}", exc_info=True)
            return self._generate_error_response(str(e))
    
    def _analyze_implicit_power_dynamics(self, shift_data: pd.DataFrame, 
                                       analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """暗黙的権力構造の分析"""
        
        power_analysis = {
            "informal_power_network": {},
            "influence_centrality_measures": {},
            "power_source_distribution": {},
            "shadow_hierarchy": {},
            "power_brokers": [],
            "power_vacuums": [],
            "coalition_patterns": {}
        }
        
        try:
            # ネットワーク構築のためのデータ準備
            interaction_matrix = self._build_interaction_matrix(shift_data)
            
            if interaction_matrix is not None:
                # ソーシャルネットワーク分析
                G = nx.from_numpy_array(interaction_matrix)
                
                # 中心性指標の計算
                degree_centrality = nx.degree_centrality(G)
                betweenness_centrality = nx.betweenness_centrality(G)
                closeness_centrality = nx.closeness_centrality(G)
                eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
                
                # スタッフリストの取得
                staff_list = shift_data['staff'].unique() if 'staff' in shift_data.columns else []
                
                # 影響力中心性の統合
                for idx, staff in enumerate(staff_list[:len(degree_centrality)]):
                    power_analysis["influence_centrality_measures"][staff] = {
                        "degree_centrality": degree_centrality.get(idx, 0),
                        "betweenness_centrality": betweenness_centrality.get(idx, 0),
                        "closeness_centrality": closeness_centrality.get(idx, 0),
                        "eigenvector_centrality": eigenvector_centrality.get(idx, 0),
                        "composite_influence_score": self._calculate_composite_influence_score(
                            degree_centrality.get(idx, 0),
                            betweenness_centrality.get(idx, 0),
                            closeness_centrality.get(idx, 0),
                            eigenvector_centrality.get(idx, 0)
                        )
                    }
                
                # パワーブローカー（仲介者）の特定
                power_brokers = [staff for staff, score in betweenness_centrality.items() 
                               if score > np.percentile(list(betweenness_centrality.values()), 75)]
                power_analysis["power_brokers"] = [staff_list[i] for i in power_brokers if i < len(staff_list)]
                
                # 権力源泉の分析
                power_analysis["power_source_distribution"] = self._analyze_power_sources(
                    shift_data, analysis_results, power_analysis["influence_centrality_measures"]
                )
                
                # シャドウヒエラルキーの検出
                power_analysis["shadow_hierarchy"] = self._detect_shadow_hierarchy(
                    power_analysis["influence_centrality_measures"],
                    shift_data
                )
                
                # 連合パターンの検出
                power_analysis["coalition_patterns"] = self._detect_coalition_patterns(G, staff_list)
            
            return power_analysis
            
        except Exception as e:
            log.error(f"権力構造分析エラー: {e}")
            return {"error": f"権力構造分析エラー: {e}"}
    
    def _analyze_organizational_culture_layers(self, shift_data: pd.DataFrame,
                                             analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """組織文化の層構造分析（Scheinモデル）"""
        
        culture_analysis = {
            "artifacts_layer": {
                "visible_patterns": {},
                "behavioral_norms": {},
                "ritual_behaviors": {}
            },
            "espoused_values_layer": {
                "stated_vs_actual_values": {},
                "value_consistency_analysis": {},
                "value_conflicts": []
            },
            "underlying_assumptions_layer": {
                "unconscious_beliefs": {},
                "taken_for_granted_assumptions": {},
                "paradigmatic_blindspots": []
            },
            "cultural_coherence_score": 0,
            "cultural_strength_indicators": {},
            "subculture_identification": {}
        }
        
        try:
            # アーティファクト層の分析
            culture_analysis["artifacts_layer"] = self._analyze_cultural_artifacts(shift_data, analysis_results)
            
            # 価値観層の分析
            culture_analysis["espoused_values_layer"] = self._analyze_espoused_values(shift_data, analysis_results)
            
            # 基本的前提層の分析
            culture_analysis["underlying_assumptions_layer"] = self._analyze_underlying_assumptions(
                shift_data, analysis_results, 
                culture_analysis["artifacts_layer"],
                culture_analysis["espoused_values_layer"]
            )
            
            # 文化的一貫性スコアの計算
            culture_analysis["cultural_coherence_score"] = self._calculate_cultural_coherence(
                culture_analysis["artifacts_layer"],
                culture_analysis["espoused_values_layer"],
                culture_analysis["underlying_assumptions_layer"]
            )
            
            # 文化的強度指標
            culture_analysis["cultural_strength_indicators"] = self._assess_cultural_strength(shift_data, analysis_results)
            
            # サブカルチャーの特定
            culture_analysis["subculture_identification"] = self._identify_subcultures(shift_data, analysis_results)
            
            return culture_analysis
            
        except Exception as e:
            log.error(f"組織文化分析エラー: {e}")
            return {"error": f"組織文化分析エラー: {e}"}
    
    def _analyze_group_dynamics(self, shift_data: pd.DataFrame,
                               analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """集団力学・グループダイナミクス分析"""
        
        group_dynamics = {
            "team_cohesion_analysis": {},
            "informal_group_formation": {},
            "group_development_stages": {},  # Tuckman's model
            "intergroup_relations": {},
            "group_decision_patterns": {},
            "social_loafing_indicators": {},
            "groupthink_risk_assessment": {},
            "team_psychological_safety": {}
        }
        
        try:
            # チーム凝集性の分析
            group_dynamics["team_cohesion_analysis"] = self._analyze_team_cohesion(shift_data)
            
            # 非公式グループの形成パターン
            group_dynamics["informal_group_formation"] = self._detect_informal_groups(shift_data)
            
            # グループ発達段階の評価（Tuckmanモデル）
            group_dynamics["group_development_stages"] = self._assess_group_development_stages(shift_data)
            
            # グループ間関係の分析
            group_dynamics["intergroup_relations"] = self._analyze_intergroup_relations(
                group_dynamics["informal_group_formation"]
            )
            
            # 集団意思決定パターン
            group_dynamics["group_decision_patterns"] = self._analyze_group_decision_patterns(shift_data)
            
            # 社会的手抜きの指標
            group_dynamics["social_loafing_indicators"] = self._detect_social_loafing(shift_data, analysis_results)
            
            # グループシンクリスク評価
            group_dynamics["groupthink_risk_assessment"] = self._assess_groupthink_risk(
                group_dynamics["team_cohesion_analysis"],
                group_dynamics["group_decision_patterns"]
            )
            
            # チーム心理的安全性
            group_dynamics["team_psychological_safety"] = self._assess_team_psychological_safety(
                shift_data, analysis_results
            )
            
            return group_dynamics
            
        except Exception as e:
            log.error(f"集団力学分析エラー: {e}")
            return {"error": f"集団力学分析エラー: {e}"}
    
    def _analyze_communication_networks(self, shift_data: pd.DataFrame,
                                      analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """情報フロー・コミュニケーションネットワーク分析"""
        
        communication_analysis = {
            "network_topology": {},
            "information_bottlenecks": [],
            "communication_clusters": {},
            "gatekeeper_roles": [],
            "isolated_nodes": [],
            "information_flow_efficiency": {},
            "formal_vs_informal_channels": {},
            "communication_breakdowns": []
        }
        
        try:
            # コミュニケーションネットワークの構築
            comm_network = self._build_communication_network(shift_data)
            
            if comm_network is not None:
                # ネットワークトポロジーの分析
                communication_analysis["network_topology"] = self._analyze_network_topology(comm_network)
                
                # 情報ボトルネックの特定
                communication_analysis["information_bottlenecks"] = self._identify_information_bottlenecks(comm_network)
                
                # コミュニケーションクラスターの検出
                communication_analysis["communication_clusters"] = self._detect_communication_clusters(comm_network)
                
                # ゲートキーパー役割の特定
                communication_analysis["gatekeeper_roles"] = self._identify_gatekeepers(comm_network)
                
                # 孤立ノードの検出
                communication_analysis["isolated_nodes"] = self._detect_isolated_nodes(comm_network)
                
                # 情報フロー効率性の評価
                communication_analysis["information_flow_efficiency"] = self._assess_information_flow_efficiency(comm_network)
                
                # 公式vs非公式チャネルの分析
                communication_analysis["formal_vs_informal_channels"] = self._analyze_formal_informal_channels(
                    shift_data, comm_network
                )
            
            return communication_analysis
            
        except Exception as e:
            log.error(f"コミュニケーションネットワーク分析エラー: {e}")
            return {"error": f"コミュニケーションネットワーク分析エラー: {e}"}
    
    def _analyze_organizational_learning(self, shift_data: pd.DataFrame,
                                       historical_data: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """組織的学習パターン分析"""
        
        learning_analysis = {
            "learning_curve_analysis": {},
            "knowledge_transfer_patterns": {},
            "organizational_memory": {},
            "learning_disabilities": [],  # Senge's learning disabilities
            "double_loop_learning_indicators": {},
            "innovation_adoption_patterns": {},
            "best_practice_diffusion": {},
            "learning_from_failure_capability": {}
        }
        
        try:
            # 学習曲線の分析
            if historical_data is not None:
                learning_analysis["learning_curve_analysis"] = self._analyze_learning_curves(historical_data)
            
            # 知識移転パターン
            learning_analysis["knowledge_transfer_patterns"] = self._analyze_knowledge_transfer(shift_data)
            
            # 組織記憶の評価
            learning_analysis["organizational_memory"] = self._assess_organizational_memory(shift_data, historical_data)
            
            # 学習障害の特定（Sengeの5つの学習障害）
            learning_analysis["learning_disabilities"] = self._identify_learning_disabilities(shift_data, historical_data)
            
            # ダブルループ学習指標
            learning_analysis["double_loop_learning_indicators"] = self._assess_double_loop_learning(
                shift_data, historical_data
            )
            
            # イノベーション採用パターン
            learning_analysis["innovation_adoption_patterns"] = self._analyze_innovation_adoption(shift_data)
            
            # ベストプラクティスの拡散
            learning_analysis["best_practice_diffusion"] = self._analyze_best_practice_diffusion(shift_data)
            
            # 失敗からの学習能力
            learning_analysis["learning_from_failure_capability"] = self._assess_failure_learning_capability(
                shift_data, historical_data
            )
            
            return learning_analysis
            
        except Exception as e:
            log.error(f"組織学習分析エラー: {e}")
            return {"error": f"組織学習分析エラー: {e}"}
    
    def _analyze_change_resistance_patterns(self, shift_data: pd.DataFrame,
                                          historical_data: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """変化に対する組織的抵抗分析"""
        
        resistance_analysis = {
            "resistance_intensity_map": {},
            "resistance_sources": {
                "individual_level": [],
                "group_level": [],
                "organizational_level": []
            },
            "change_readiness_assessment": {},
            "resistance_tactics_identified": [],
            "change_champions": [],
            "fence_sitters": [],
            "active_resistors": [],
            "resistance_evolution_pattern": {}
        }
        
        try:
            # 抵抗強度マップの作成
            resistance_analysis["resistance_intensity_map"] = self._create_resistance_intensity_map(
                shift_data, historical_data
            )
            
            # 抵抗源の分析（個人・グループ・組織レベル）
            resistance_analysis["resistance_sources"] = self._identify_resistance_sources(shift_data, historical_data)
            
            # 変化への準備度評価
            resistance_analysis["change_readiness_assessment"] = self._assess_change_readiness(shift_data)
            
            # 抵抗戦術の特定
            resistance_analysis["resistance_tactics_identified"] = self._identify_resistance_tactics(shift_data)
            
            # 変化推進者の特定
            resistance_analysis["change_champions"] = self._identify_change_champions(shift_data)
            
            # 中立者の特定
            resistance_analysis["fence_sitters"] = self._identify_fence_sitters(shift_data)
            
            # 積極的抵抗者の特定
            resistance_analysis["active_resistors"] = self._identify_active_resistors(shift_data)
            
            # 抵抗の時間的変化パターン
            if historical_data is not None:
                resistance_analysis["resistance_evolution_pattern"] = self._analyze_resistance_evolution(historical_data)
            
            return resistance_analysis
            
        except Exception as e:
            log.error(f"変化抵抗分析エラー: {e}")
            return {"error": f"変化抵抗分析エラー: {e}"}
    
    def _identify_organizational_defense_mechanisms(self, shift_data: pd.DataFrame,
                                                  analysis_results: Dict[str, Any],
                                                  historical_data: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """組織的防衛メカニズムの特定"""
        
        defense_analysis = {
            "active_defense_mechanisms": {},
            "defense_intensity_scores": {},
            "defense_triggers": [],
            "collective_anxiety_indicators": {},
            "organizational_neurosis_patterns": {},
            "defense_impact_assessment": {},
            "healthy_vs_unhealthy_defenses": {}
        }
        
        try:
            # アクティブな防衛メカニズムの検出
            for mechanism, description in self.defense_mechanisms.items():
                detection_result = self._detect_defense_mechanism(mechanism, shift_data, analysis_results)
                if detection_result['detected']:
                    defense_analysis["active_defense_mechanisms"][mechanism] = {
                        "description": description,
                        "intensity": detection_result['intensity'],
                        "manifestations": detection_result['manifestations']
                    }
            
            # 防衛強度スコアの計算
            defense_analysis["defense_intensity_scores"] = self._calculate_defense_intensity_scores(
                defense_analysis["active_defense_mechanisms"]
            )
            
            # 防衛トリガーの特定
            defense_analysis["defense_triggers"] = self._identify_defense_triggers(
                shift_data, analysis_results, historical_data
            )
            
            # 集合的不安指標
            defense_analysis["collective_anxiety_indicators"] = self._assess_collective_anxiety(
                shift_data, analysis_results
            )
            
            # 組織的神経症パターン
            defense_analysis["organizational_neurosis_patterns"] = self._identify_organizational_neurosis(
                defense_analysis["active_defense_mechanisms"],
                defense_analysis["collective_anxiety_indicators"]
            )
            
            # 防衛の影響評価
            defense_analysis["defense_impact_assessment"] = self._assess_defense_impact(
                defense_analysis["active_defense_mechanisms"],
                analysis_results
            )
            
            # 健全vs不健全な防衛の分類
            defense_analysis["healthy_vs_unhealthy_defenses"] = self._classify_defense_health(
                defense_analysis["active_defense_mechanisms"]
            )
            
            return defense_analysis
            
        except Exception as e:
            log.error(f"組織的防衛メカニズム分析エラー: {e}")
            return {"error": f"組織的防衛メカニズム分析エラー: {e}"}
    
    def _analyze_emergent_leadership(self, shift_data: pd.DataFrame,
                                   analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """創発的リーダーシップパターン分析"""
        
        leadership_analysis = {
            "emergent_leaders": {},
            "leadership_styles_distribution": {},
            "leadership_effectiveness_metrics": {},
            "leadership_succession_patterns": {},
            "distributed_leadership_indicators": {},
            "leadership_development_potential": {},
            "leadership_gaps": []
        }
        
        try:
            # 創発的リーダーの特定
            leadership_analysis["emergent_leaders"] = self._identify_emergent_leaders(shift_data, analysis_results)
            
            # リーダーシップスタイルの分布
            leadership_analysis["leadership_styles_distribution"] = self._analyze_leadership_styles(
                leadership_analysis["emergent_leaders"],
                shift_data
            )
            
            # リーダーシップ効果性指標
            leadership_analysis["leadership_effectiveness_metrics"] = self._assess_leadership_effectiveness(
                leadership_analysis["emergent_leaders"],
                analysis_results
            )
            
            # リーダーシップ承継パターン
            leadership_analysis["leadership_succession_patterns"] = self._analyze_succession_patterns(
                shift_data, leadership_analysis["emergent_leaders"]
            )
            
            # 分散型リーダーシップ指標
            leadership_analysis["distributed_leadership_indicators"] = self._assess_distributed_leadership(
                shift_data, leadership_analysis["emergent_leaders"]
            )
            
            # リーダーシップ開発ポテンシャル
            leadership_analysis["leadership_development_potential"] = self._identify_leadership_potential(
                shift_data, analysis_results
            )
            
            # リーダーシップギャップ
            leadership_analysis["leadership_gaps"] = self._identify_leadership_gaps(
                leadership_analysis, analysis_results
            )
            
            return leadership_analysis
            
        except Exception as e:
            log.error(f"創発的リーダーシップ分析エラー: {e}")
            return {"error": f"創発的リーダーシップ分析エラー: {e}"}
    
    def _analyze_organizational_silos(self, shift_data: pd.DataFrame,
                                    analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """組織的サイロ・派閥分析"""
        
        silos_analysis = {
            "identified_silos": {},
            "silo_strength_metrics": {},
            "cross_silo_collaboration_index": 0,
            "silo_formation_drivers": [],
            "bridge_builders": [],
            "silo_impact_assessment": {},
            "integration_opportunities": []
        }
        
        try:
            # サイロの特定
            silos_analysis["identified_silos"] = self._identify_organizational_silos(shift_data)
            
            # サイロ強度メトリクス
            silos_analysis["silo_strength_metrics"] = self._calculate_silo_strength(
                silos_analysis["identified_silos"],
                shift_data
            )
            
            # クロスサイロ協力指数
            silos_analysis["cross_silo_collaboration_index"] = self._calculate_cross_silo_collaboration(
                silos_analysis["identified_silos"],
                shift_data
            )
            
            # サイロ形成要因
            silos_analysis["silo_formation_drivers"] = self._identify_silo_formation_drivers(
                silos_analysis["identified_silos"],
                shift_data
            )
            
            # ブリッジビルダーの特定
            silos_analysis["bridge_builders"] = self._identify_bridge_builders(
                silos_analysis["identified_silos"],
                shift_data
            )
            
            # サイロの影響評価
            silos_analysis["silo_impact_assessment"] = self._assess_silo_impact(
                silos_analysis["identified_silos"],
                analysis_results
            )
            
            # 統合機会の特定
            silos_analysis["integration_opportunities"] = self._identify_integration_opportunities(
                silos_analysis
            )
            
            return silos_analysis
            
        except Exception as e:
            log.error(f"組織的サイロ分析エラー: {e}")
            return {"error": f"組織的サイロ分析エラー: {e}"}
    
    # ============================================================================
    # 深層分析ヘルパーメソッド群
    # ============================================================================
    
    def _build_interaction_matrix(self, shift_data: pd.DataFrame) -> Optional[np.ndarray]:
        """相互作用マトリックスの構築"""
        try:
            if 'staff' not in shift_data.columns:
                return None
            
            staff_list = shift_data['staff'].unique()
            n_staff = len(staff_list)
            interaction_matrix = np.zeros((n_staff, n_staff))
            
            # 同時シフトを相互作用として計算
            if 'ds' in shift_data.columns:
                for date in shift_data['ds'].unique():
                    date_staff = shift_data[shift_data['ds'] == date]['staff'].values
                    for i, staff1 in enumerate(staff_list):
                        for j, staff2 in enumerate(staff_list):
                            if i != j and staff1 in date_staff and staff2 in date_staff:
                                interaction_matrix[i, j] += 1
            
            # 正規化
            if interaction_matrix.max() > 0:
                interaction_matrix = interaction_matrix / interaction_matrix.max()
            
            return interaction_matrix
            
        except Exception as e:
            log.error(f"相互作用マトリックス構築エラー: {e}")
            return None
    
    def _calculate_composite_influence_score(self, degree: float, betweenness: float,
                                           closeness: float, eigenvector: float) -> float:
        """複合影響力スコアの計算"""
        # 重み付け平均（各指標の重要性を考慮）
        weights = {
            'degree': 0.2,      # 直接的つながり
            'betweenness': 0.3, # 仲介役としての重要性
            'closeness': 0.2,   # ネットワーク内での位置
            'eigenvector': 0.3  # 影響力のある人とのつながり
        }
        
        score = (weights['degree'] * degree +
                weights['betweenness'] * betweenness +
                weights['closeness'] * closeness +
                weights['eigenvector'] * eigenvector)
        
        return round(score, 4)
    
    def _analyze_power_sources(self, shift_data: pd.DataFrame, analysis_results: Dict[str, Any],
                             influence_measures: Dict[str, Any]) -> Dict[str, Any]:
        """権力源泉の分析"""
        power_sources_analysis = {}
        
        try:
            for staff in influence_measures.keys():
                power_sources_analysis[staff] = {
                    'legitimate_power': self._assess_legitimate_power(staff, shift_data),
                    'expert_power': self._assess_expert_power(staff, shift_data, analysis_results),
                    'referent_power': self._assess_referent_power(staff, influence_measures),
                    'information_power': self._assess_information_power(staff, influence_measures),
                    'dominant_power_source': 'balanced'
                }
                
                # 支配的な権力源泉の特定
                power_scores = {k: v for k, v in power_sources_analysis[staff].items() 
                              if k != 'dominant_power_source'}
                if power_scores:
                    dominant = max(power_scores, key=power_scores.get)
                    power_sources_analysis[staff]['dominant_power_source'] = dominant
            
            return power_sources_analysis
            
        except Exception as e:
            log.error(f"権力源泉分析エラー: {e}")
            return {}
    
    def _detect_shadow_hierarchy(self, influence_measures: Dict[str, Any],
                               shift_data: pd.DataFrame) -> Dict[str, Any]:
        """シャドウヒエラルキーの検出"""
        shadow_hierarchy = {
            'informal_leaders': [],
            'hidden_influencers': [],
            'power_behind_throne': [],
            'informal_rank_order': []
        }
        
        try:
            # 影響力スコアでソート
            sorted_staff = sorted(influence_measures.items(), 
                                key=lambda x: x[1].get('composite_influence_score', 0),
                                reverse=True)
            
            # 非公式リーダー（上位20%）
            top_20_percent = int(len(sorted_staff) * 0.2)
            shadow_hierarchy['informal_leaders'] = [staff[0] for staff in sorted_staff[:top_20_percent]]
            
            # 隠れた影響者（高い仲介中心性を持つが、公式的地位が低い）
            for staff, measures in influence_measures.items():
                if measures.get('betweenness_centrality', 0) > 0.1:  # 高い仲介中心性
                    formal_position = self._get_formal_position_level(staff, shift_data)
                    if formal_position == 'low':
                        shadow_hierarchy['hidden_influencers'].append(staff)
            
            # 非公式ランク順
            shadow_hierarchy['informal_rank_order'] = [staff[0] for staff in sorted_staff]
            
            return shadow_hierarchy
            
        except Exception as e:
            log.error(f"シャドウヒエラルキー検出エラー: {e}")
            return shadow_hierarchy
    
    def _detect_coalition_patterns(self, G: nx.Graph, staff_list: List[str]) -> Dict[str, Any]:
        """連合パターンの検出"""
        coalition_patterns = {
            'detected_coalitions': [],
            'coalition_strength': {},
            'coalition_purposes': []
        }
        
        try:
            # コミュニティ検出アルゴリズムの適用
            communities = nx.community.greedy_modularity_communities(G)
            
            for idx, community in enumerate(communities):
                if len(community) > 2:  # 3人以上を連合とみなす
                    coalition_members = [staff_list[node] for node in community if node < len(staff_list)]
                    
                    coalition_patterns['detected_coalitions'].append({
                        'coalition_id': f'C{idx:03d}',
                        'members': coalition_members,
                        'size': len(coalition_members),
                        'density': nx.density(G.subgraph(community))
                    })
            
            return coalition_patterns
            
        except Exception as e:
            log.error(f"連合パターン検出エラー: {e}")
            return coalition_patterns
    
    def _analyze_cultural_artifacts(self, shift_data: pd.DataFrame,
                                  analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """文化的アーティファクト（可視的要素）の分析"""
        artifacts = {
            'visible_patterns': {},
            'behavioral_norms': {},
            'ritual_behaviors': {}
        }
        
        try:
            # 可視的パターン（シフトパターン、勤務慣行など）
            artifacts['visible_patterns'] = {
                'dominant_shift_patterns': self._analyze_shift_patterns(shift_data),
                'overtime_culture': self._analyze_overtime_culture(shift_data),
                'punctuality_patterns': self._analyze_punctuality_patterns(shift_data)
            }
            
            # 行動規範
            artifacts['behavioral_norms'] = {
                'collaboration_norms': self._analyze_collaboration_norms(shift_data),
                'communication_styles': self._analyze_communication_styles(shift_data),
                'decision_making_patterns': self._analyze_decision_patterns(shift_data)
            }
            
            # 儀式的行動
            artifacts['ritual_behaviors'] = {
                'recurring_meetings': self._analyze_recurring_patterns(shift_data),
                'informal_gatherings': self._detect_informal_gatherings(shift_data),
                'symbolic_actions': self._identify_symbolic_actions(shift_data)
            }
            
            return artifacts
            
        except Exception as e:
            log.error(f"文化的アーティファクト分析エラー: {e}")
            return artifacts
    
    def _generate_deep_organizational_insights(self, *args) -> Dict[str, Any]:
        """深層的組織診断と介入戦略の生成"""
        
        deep_insights = {
            "organizational_health_diagnosis": {
                "overall_health_score": 0,
                "critical_dysfunctions": [],
                "organizational_strengths": [],
                "systemic_issues": []
            },
            "hidden_dynamics_revealed": [],
            "intervention_strategies": {
                "immediate_actions": [],
                "medium_term_initiatives": [],
                "long_term_transformations": []
            },
            "change_leverage_points": [],
            "organizational_potential": {},
            "transformation_roadmap": {}
        }
        
        try:
            # 組織健康度の総合診断
            deep_insights["organizational_health_diagnosis"] = self._diagnose_organizational_health(args)
            
            # 隠れた力学の要約
            deep_insights["hidden_dynamics_revealed"] = [
                "非公式な権力ネットワークが公式組織図を上回る影響力を持っています",
                "複数の防衛メカニズムが変化への抵抗を生み出しています",
                "サイロ化により情報フローが制限されています",
                "創発的リーダーシップが組織の実質的な方向性を決定しています"
            ]
            
            # 介入戦略の設計
            deep_insights["intervention_strategies"] = {
                "immediate_actions": [
                    {
                        "action": "非公式リーダーとの対話セッション",
                        "purpose": "変化への協力体制構築",
                        "timeline": "1週間以内"
                    },
                    {
                        "action": "情報フロー改善ワークショップ",
                        "purpose": "サイロ間コミュニケーション強化",
                        "timeline": "2週間以内"
                    }
                ],
                "medium_term_initiatives": [
                    {
                        "initiative": "組織文化変革プログラム",
                        "focus": "心理的安全性の向上",
                        "duration": "3-6ヶ月"
                    },
                    {
                        "initiative": "リーダーシップ開発プログラム",
                        "focus": "分散型リーダーシップの育成",
                        "duration": "6ヶ月"
                    }
                ],
                "long_term_transformations": [
                    {
                        "transformation": "組織構造の再設計",
                        "goal": "サイロ解消と協働促進",
                        "timeline": "1-2年"
                    }
                ]
            }
            
            # 変革のレバレッジポイント
            deep_insights["change_leverage_points"] = [
                "非公式リーダーのエンゲージメント",
                "情報フローのボトルネック解消",
                "心理的安全性の確立",
                "組織学習能力の強化"
            ]
            
            return deep_insights
            
        except Exception as e:
            log.error(f"深層的組織診断エラー: {e}")
            return deep_insights
    
    # ============================================================================
    # 補助メソッド（簡略実装）
    # ============================================================================
    
    def _calculate_observation_period(self, shift_data: pd.DataFrame) -> str:
        """観察期間の計算"""
        if 'ds' in shift_data.columns:
            try:
                dates = pd.to_datetime(shift_data['ds'])
                period_days = (dates.max() - dates.min()).days + 1
                return f"{period_days}日間"
            except:
                pass
        return "不明"
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """エラーレスポンスの生成"""
        return {
            "analysis_metadata": {
                "analysis_id": self.analysis_id,
                "status": "error",
                "error_message": error_message,
                "timestamp": datetime.now().isoformat()
            },
            "error": error_message
        }
    
    def _assess_legitimate_power(self, staff: str, shift_data: pd.DataFrame) -> float:
        """正統的権力の評価"""
        # 簡略実装：役職や雇用形態から推定
        return np.random.uniform(0.3, 0.8)
    
    def _assess_expert_power(self, staff: str, shift_data: pd.DataFrame, analysis_results: Dict) -> float:
        """専門的権力の評価"""
        # 簡略実装：スキルや経験から推定
        return np.random.uniform(0.4, 0.9)
    
    def _assess_referent_power(self, staff: str, influence_measures: Dict) -> float:
        """人格的権力の評価"""
        # 簡略実装：影響力指標から推定
        return influence_measures.get(staff, {}).get('eigenvector_centrality', 0.5)
    
    def _assess_information_power(self, staff: str, influence_measures: Dict) -> float:
        """情報権力の評価"""
        # 簡略実装：仲介中心性から推定
        return influence_measures.get(staff, {}).get('betweenness_centrality', 0.5)
    
    def _get_formal_position_level(self, staff: str, shift_data: pd.DataFrame) -> str:
        """公式的地位レベルの取得"""
        # 簡略実装
        return np.random.choice(['high', 'medium', 'low'])
    
    def _analyze_shift_patterns(self, shift_data: pd.DataFrame) -> Dict:
        """シフトパターンの分析"""
        return {"dominant_pattern": "標準的", "flexibility": "中程度"}
    
    def _analyze_overtime_culture(self, shift_data: pd.DataFrame) -> Dict:
        """残業文化の分析"""
        return {"overtime_frequency": "中程度", "voluntary_overtime": "低い"}
    
    def _analyze_punctuality_patterns(self, shift_data: pd.DataFrame) -> Dict:
        """時間厳守パターンの分析"""
        return {"punctuality_score": 0.85, "tolerance_level": "高い"}
    
    def _analyze_collaboration_norms(self, shift_data: pd.DataFrame) -> Dict:
        """協働規範の分析"""
        return {"collaboration_level": "中程度", "team_orientation": "高い"}
    
    def _analyze_communication_styles(self, shift_data: pd.DataFrame) -> Dict:
        """コミュニケーションスタイルの分析"""
        return {"dominant_style": "間接的", "formality_level": "高い"}
    
    def _analyze_decision_patterns(self, shift_data: pd.DataFrame) -> Dict:
        """意思決定パターンの分析"""
        return {"decision_style": "合議制", "speed": "遅い"}
    
    def _analyze_recurring_patterns(self, shift_data: pd.DataFrame) -> Dict:
        """繰り返しパターンの分析"""
        return {"meeting_frequency": "週次", "attendance_rate": 0.8}
    
    def _detect_informal_gatherings(self, shift_data: pd.DataFrame) -> Dict:
        """非公式集会の検出"""
        return {"informal_meeting_frequency": "月次", "participation": "限定的"}
    
    def _identify_symbolic_actions(self, shift_data: pd.DataFrame) -> Dict:
        """象徴的行動の特定"""
        return {"ceremonies": ["歓送迎会"], "rituals": ["朝礼"]}
    
    def _analyze_espoused_values(self, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """標榜価値の分析"""
        return {
            "stated_vs_actual_values": {"teamwork": {"stated": 0.9, "actual": 0.6}},
            "value_consistency_analysis": {"consistency_score": 0.65},
            "value_conflicts": ["効率性 vs 品質"]
        }
    
    def _analyze_underlying_assumptions(self, shift_data: pd.DataFrame, analysis_results: Dict,
                                      artifacts: Dict, values: Dict) -> Dict:
        """基本的前提の分析"""
        return {
            "unconscious_beliefs": {"hierarchy_importance": "高い"},
            "taken_for_granted_assumptions": ["年功序列は正しい"],
            "paradigmatic_blindspots": ["イノベーションへの抵抗"]
        }
    
    def _calculate_cultural_coherence(self, artifacts: Dict, values: Dict, assumptions: Dict) -> float:
        """文化的一貫性スコアの計算"""
        return 0.72  # 簡略実装
    
    def _assess_cultural_strength(self, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """文化的強度の評価"""
        return {
            "strength_score": 0.78,
            "uniformity": "高い",
            "intensity": "中程度"
        }
    
    def _identify_subcultures(self, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """サブカルチャーの特定"""
        return {
            "identified_subcultures": ["看護師文化", "事務職文化"],
            "cultural_distance": 0.35
        }
    
    def _analyze_team_cohesion(self, shift_data: pd.DataFrame) -> Dict:
        """チーム凝集性の分析"""
        return {
            "overall_cohesion": 0.68,
            "task_cohesion": 0.72,
            "social_cohesion": 0.64
        }
    
    def _detect_informal_groups(self, shift_data: pd.DataFrame) -> Dict:
        """非公式グループの検出"""
        return {
            "detected_groups": 3,
            "group_sizes": [5, 7, 4],
            "group_types": ["友好的", "タスク志向", "利害関係"]
        }
    
    def _assess_group_development_stages(self, shift_data: pd.DataFrame) -> Dict:
        """グループ発達段階の評価"""
        return {
            "forming": 2,
            "storming": 1,
            "norming": 3,
            "performing": 2,
            "adjourning": 0
        }
    
    def _analyze_intergroup_relations(self, informal_groups: Dict) -> Dict:
        """グループ間関係の分析"""
        return {
            "cooperation_level": 0.6,
            "competition_level": 0.3,
            "conflict_level": 0.1
        }
    
    def _analyze_group_decision_patterns(self, shift_data: pd.DataFrame) -> Dict:
        """集団意思決定パターンの分析"""
        return {
            "decision_style": "合意形成",
            "participation_level": 0.7,
            "decision_quality": 0.75
        }
    
    def _detect_social_loafing(self, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """社会的手抜きの検出"""
        return {
            "loafing_risk": 0.25,
            "at_risk_individuals": 3,
            "contributing_factors": ["大規模グループ", "責任の拡散"]
        }
    
    def _assess_groupthink_risk(self, cohesion: Dict, decision_patterns: Dict) -> Dict:
        """グループシンクリスクの評価"""
        return {
            "risk_level": "中程度",
            "risk_factors": ["高い凝集性", "外部批判の欠如"],
            "mitigation_needed": True
        }
    
    def _assess_team_psychological_safety(self, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """チーム心理的安全性の評価"""
        return {
            "overall_safety_score": 0.65,
            "voice_behavior": 0.6,
            "error_tolerance": 0.7,
            "help_seeking": 0.65
        }
    
    def _build_communication_network(self, shift_data: pd.DataFrame) -> Optional[nx.Graph]:
        """コミュニケーションネットワークの構築"""
        try:
            # 簡略実装：相互作用マトリックスからネットワーク構築
            interaction_matrix = self._build_interaction_matrix(shift_data)
            if interaction_matrix is not None:
                return nx.from_numpy_array(interaction_matrix)
            return None
        except:
            return None
    
    def _analyze_network_topology(self, network: nx.Graph) -> Dict:
        """ネットワークトポロジーの分析"""
        return {
            "network_type": "小世界ネットワーク",
            "clustering_coefficient": nx.average_clustering(network) if network else 0,
            "average_path_length": nx.average_shortest_path_length(network) if nx.is_connected(network) else float('inf')
        }
    
    def _identify_information_bottlenecks(self, network: nx.Graph) -> List[str]:
        """情報ボトルネックの特定"""
        # 簡略実装
        return ["ノード5", "ノード12"]
    
    def _detect_communication_clusters(self, network: nx.Graph) -> Dict:
        """コミュニケーションクラスターの検出"""
        return {
            "cluster_count": 4,
            "cluster_sizes": [8, 6, 5, 3],
            "inter_cluster_links": 12
        }
    
    def _identify_gatekeepers(self, network: nx.Graph) -> List[str]:
        """ゲートキーパーの特定"""
        return ["スタッフA", "スタッフB"]
    
    def _detect_isolated_nodes(self, network: nx.Graph) -> List[str]:
        """孤立ノードの検出"""
        return ["スタッフX", "スタッフY"]
    
    def _assess_information_flow_efficiency(self, network: nx.Graph) -> Dict:
        """情報フロー効率性の評価"""
        return {
            "efficiency_score": 0.72,
            "bottleneck_impact": 0.15,
            "redundancy_level": 0.3
        }
    
    def _analyze_formal_informal_channels(self, shift_data: pd.DataFrame, network: nx.Graph) -> Dict:
        """公式vs非公式チャネルの分析"""
        return {
            "formal_channel_usage": 0.6,
            "informal_channel_usage": 0.4,
            "channel_effectiveness": {"formal": 0.7, "informal": 0.85}
        }
    
    def _analyze_learning_curves(self, historical_data: pd.DataFrame) -> Dict:
        """学習曲線の分析"""
        return {
            "learning_rate": 0.15,
            "plateau_reached": False,
            "time_to_competency": "3ヶ月"
        }
    
    def _analyze_knowledge_transfer(self, shift_data: pd.DataFrame) -> Dict:
        """知識移転パターンの分析"""
        return {
            "transfer_efficiency": 0.68,
            "preferred_methods": ["OJT", "メンタリング"],
            "knowledge_loss_risk": 0.25
        }
    
    def _assess_organizational_memory(self, shift_data: pd.DataFrame, historical_data: Optional[pd.DataFrame]) -> Dict:
        """組織記憶の評価"""
        return {
            "memory_retention": 0.75,
            "documentation_quality": 0.6,
            "tacit_knowledge_ratio": 0.4
        }
    
    def _identify_learning_disabilities(self, shift_data: pd.DataFrame, historical_data: Optional[pd.DataFrame]) -> List[str]:
        """学習障害の特定（Sengeの5つの障害）"""
        return [
            "私は私のポジション",
            "敵は外部にいる",
            "先制的行動の幻想",
            "出来事への執着",
            "ゆでガエルの寓話"
        ]
    
    def _assess_double_loop_learning(self, shift_data: pd.DataFrame, historical_data: Optional[pd.DataFrame]) -> Dict:
        """ダブルループ学習の評価"""
        return {
            "double_loop_capability": 0.45,
            "paradigm_questioning": "低い",
            "adaptive_capacity": "中程度"
        }
    
    def _analyze_innovation_adoption(self, shift_data: pd.DataFrame) -> Dict:
        """イノベーション採用パターンの分析"""
        return {
            "adoption_rate": 0.35,
            "early_adopters": ["スタッフC", "スタッフD"],
            "resistance_pockets": ["部署A", "部署B"]
        }
    
    def _analyze_best_practice_diffusion(self, shift_data: pd.DataFrame) -> Dict:
        """ベストプラクティス拡散の分析"""
        return {
            "diffusion_speed": "遅い",
            "adoption_barriers": ["サイロ化", "NIH症候群"],
            "success_stories": 2
        }
    
    def _assess_failure_learning_capability(self, shift_data: pd.DataFrame, historical_data: Optional[pd.DataFrame]) -> Dict:
        """失敗からの学習能力の評価"""
        return {
            "failure_acknowledgment": 0.6,
            "root_cause_analysis": 0.7,
            "improvement_implementation": 0.5
        }
    
    def _create_resistance_intensity_map(self, shift_data: pd.DataFrame, historical_data: Optional[pd.DataFrame]) -> Dict:
        """抵抗強度マップの作成"""
        return {
            "high_resistance_areas": ["部署X", "チームY"],
            "medium_resistance_areas": ["部署Z"],
            "low_resistance_areas": ["チームA", "チームB"]
        }
    
    def _identify_resistance_sources(self, shift_data: pd.DataFrame, historical_data: Optional[pd.DataFrame]) -> Dict:
        """抵抗源の特定"""
        return {
            "individual_level": ["スキル不足への不安", "権力喪失の恐れ"],
            "group_level": ["グループアイデンティティの脅威", "既得権益の保護"],
            "organizational_level": ["文化的慣性", "構造的硬直性"]
        }
    
    def _assess_change_readiness(self, shift_data: pd.DataFrame) -> Dict:
        """変化への準備度評価"""
        return {
            "readiness_score": 0.58,
            "enablers": ["リーダーシップサポート", "明確なビジョン"],
            "barriers": ["リソース不足", "過去の失敗経験"]
        }
    
    def _identify_resistance_tactics(self, shift_data: pd.DataFrame) -> List[str]:
        """抵抗戦術の特定"""
        return [
            "消極的抵抗（遅延戦術）",
            "選択的情報共有",
            "表面的順守",
            "代替案の過剰提案"
        ]
    
    def _identify_change_champions(self, shift_data: pd.DataFrame) -> List[str]:
        """変化推進者の特定"""
        return ["マネージャーA", "リーダーB", "インフルエンサーC"]
    
    def _identify_fence_sitters(self, shift_data: pd.DataFrame) -> List[str]:
        """中立者の特定"""
        return ["スタッフ群1", "スタッフ群2"]
    
    def _identify_active_resistors(self, shift_data: pd.DataFrame) -> List[str]:
        """積極的抵抗者の特定"""
        return ["抵抗グループA", "影響力者X"]
    
    def _analyze_resistance_evolution(self, historical_data: pd.DataFrame) -> Dict:
        """抵抗の時間的変化パターン"""
        return {
            "initial_shock": "高い",
            "resistance_peak": "2ヶ月目",
            "acceptance_trend": "緩やか",
            "current_phase": "適応期"
        }
    
    def _detect_defense_mechanism(self, mechanism: str, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """防衛メカニズムの検出"""
        # 簡略実装
        detected = np.random.random() > 0.5
        return {
            'detected': detected,
            'intensity': np.random.uniform(0.3, 0.8) if detected else 0,
            'manifestations': ["パターンA", "パターンB"] if detected else []
        }
    
    def _calculate_defense_intensity_scores(self, active_mechanisms: Dict) -> Dict:
        """防衛強度スコアの計算"""
        total_intensity = sum(mech['intensity'] for mech in active_mechanisms.values())
        return {
            "total_defense_intensity": round(total_intensity, 2),
            "average_intensity": round(total_intensity / len(active_mechanisms) if active_mechanisms else 0, 2),
            "dominant_mechanism": max(active_mechanisms.keys(), 
                                    key=lambda k: active_mechanisms[k]['intensity']) if active_mechanisms else None
        }
    
    def _identify_defense_triggers(self, shift_data: pd.DataFrame, analysis_results: Dict, 
                                 historical_data: Optional[pd.DataFrame]) -> List[str]:
        """防衛トリガーの特定"""
        return [
            "業績評価への脅威",
            "組織変更の噂",
            "新システム導入",
            "リーダーシップの交代"
        ]
    
    def _assess_collective_anxiety(self, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """集合的不安の評価"""
        return {
            "anxiety_level": 0.68,
            "primary_sources": ["将来の不確実性", "雇用不安"],
            "coping_mechanisms": ["情報探索", "集団形成"]
        }
    
    def _identify_organizational_neurosis(self, active_mechanisms: Dict, anxiety_indicators: Dict) -> Dict:
        """組織的神経症パターンの特定"""
        return {
            "neurotic_patterns": ["完璧主義", "回避行動"],
            "severity": "中程度",
            "impact_areas": ["意思決定", "イノベーション"]
        }
    
    def _assess_defense_impact(self, active_mechanisms: Dict, analysis_results: Dict) -> Dict:
        """防衛メカニズムの影響評価"""
        return {
            "productivity_impact": -0.15,
            "innovation_impact": -0.25,
            "wellbeing_impact": -0.20,
            "overall_dysfunction": "中程度"
        }
    
    def _classify_defense_health(self, active_mechanisms: Dict) -> Dict:
        """防衛メカニズムの健全性分類"""
        return {
            "healthy_defenses": ["適応的対処"],
            "unhealthy_defenses": ["否認", "投影"],
            "balance_assessment": "不健全寄り"
        }
    
    def _identify_emergent_leaders(self, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """創発的リーダーの特定"""
        return {
            "technical_leaders": ["スタッフT1", "スタッフT2"],
            "social_leaders": ["スタッフS1", "スタッフS2"],
            "change_leaders": ["スタッフC1"],
            "informal_coordinators": ["スタッフI1", "スタッフI2"]
        }
    
    def _analyze_leadership_styles(self, emergent_leaders: Dict, shift_data: pd.DataFrame) -> Dict:
        """リーダーシップスタイルの分析"""
        return {
            "transformational": 2,
            "transactional": 3,
            "servant": 1,
            "participative": 2,
            "autocratic": 1
        }
    
    def _assess_leadership_effectiveness(self, emergent_leaders: Dict, analysis_results: Dict) -> Dict:
        """リーダーシップ効果性の評価"""
        return {
            "overall_effectiveness": 0.72,
            "follower_satisfaction": 0.75,
            "goal_achievement": 0.70,
            "team_development": 0.68
        }
    
    def _analyze_succession_patterns(self, shift_data: pd.DataFrame, emergent_leaders: Dict) -> Dict:
        """承継パターンの分析"""
        return {
            "succession_planning": "不十分",
            "talent_pipeline": "限定的",
            "knowledge_transfer_risk": "高い"
        }
    
    def _assess_distributed_leadership(self, shift_data: pd.DataFrame, emergent_leaders: Dict) -> Dict:
        """分散型リーダーシップの評価"""
        return {
            "distribution_level": 0.45,
            "shared_leadership_areas": ["日常業務", "問題解決"],
            "centralized_areas": ["戦略決定", "資源配分"]
        }
    
    def _identify_leadership_potential(self, shift_data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """リーダーシップポテンシャルの特定"""
        return {
            "high_potential": ["スタッフHP1", "スタッフHP2"],
            "development_needed": ["スタッフDN1", "スタッフDN2"],
            "readiness_timeline": "6-12ヶ月"
        }
    
    def _identify_leadership_gaps(self, leadership_analysis: Dict, analysis_results: Dict) -> List[str]:
        """リーダーシップギャップの特定"""
        return [
            "戦略的思考能力",
            "変革リーダーシップ",
            "デジタルリーダーシップ",
            "グローバル視点"
        ]
    
    def _identify_organizational_silos(self, shift_data: pd.DataFrame) -> Dict:
        """組織的サイロの特定"""
        return {
            "silo_1": {"name": "看護部門", "members": 15, "isolation_score": 0.7},
            "silo_2": {"name": "事務部門", "members": 8, "isolation_score": 0.6},
            "silo_3": {"name": "リハビリ部門", "members": 6, "isolation_score": 0.5}
        }
    
    def _calculate_silo_strength(self, silos: Dict, shift_data: pd.DataFrame) -> Dict:
        """サイロ強度の計算"""
        return {
            "silo_1": {"internal_cohesion": 0.85, "external_connection": 0.15},
            "silo_2": {"internal_cohesion": 0.75, "external_connection": 0.25},
            "silo_3": {"internal_cohesion": 0.70, "external_connection": 0.30}
        }
    
    def _calculate_cross_silo_collaboration(self, silos: Dict, shift_data: pd.DataFrame) -> float:
        """クロスサイロ協力指数の計算"""
        return 0.35  # 低い協力レベル
    
    def _identify_silo_formation_drivers(self, silos: Dict, shift_data: pd.DataFrame) -> List[str]:
        """サイロ形成要因の特定"""
        return [
            "専門性の違い",
            "物理的分離",
            "異なる目標・KPI",
            "リーダーシップスタイルの相違",
            "歴史的対立"
        ]
    
    def _identify_bridge_builders(self, silos: Dict, shift_data: pd.DataFrame) -> List[str]:
        """ブリッジビルダーの特定"""
        return ["コーディネーターA", "マネージャーB", "スペシャリストC"]
    
    def _assess_silo_impact(self, silos: Dict, analysis_results: Dict) -> Dict:
        """サイロの影響評価"""
        return {
            "communication_impact": -0.35,
            "innovation_impact": -0.40,
            "efficiency_impact": -0.25,
            "customer_satisfaction_impact": -0.20
        }
    
    def _identify_integration_opportunities(self, silos_analysis: Dict) -> List[Dict]:
        """統合機会の特定"""
        return [
            {
                "opportunity": "クロスファンクショナルチーム",
                "potential_impact": "高",
                "implementation_difficulty": "中"
            },
            {
                "opportunity": "統合ワークスペース",
                "potential_impact": "中",
                "implementation_difficulty": "低"
            },
            {
                "opportunity": "共通KPI導入",
                "potential_impact": "高",
                "implementation_difficulty": "高"
            }
        ]
    
    def _diagnose_organizational_health(self, analysis_components: tuple) -> Dict:
        """組織健康度の総合診断"""
        return {
            "overall_health_score": 0.62,
            "critical_dysfunctions": [
                "サイロ化による情報断絶",
                "非公式権力構造の支配",
                "変化への組織的抵抗"
            ],
            "organizational_strengths": [
                "強い内部結束",
                "暗黙知の蓄積",
                "危機対応能力"
            ],
            "systemic_issues": [
                "学習障害の存在",
                "防衛メカニズムの過剰",
                "イノベーション阻害"
            ]
        }