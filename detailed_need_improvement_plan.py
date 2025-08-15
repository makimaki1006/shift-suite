#!/usr/bin/env python3
"""
Need積算修正 具体的改善計画とタスクダウン
包括的調査結果に基づく段階的実装計画
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime, timedelta
import shutil

class DetailedNeedImprovementPlanner:
    """Need積算修正の詳細改善計画システム"""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        self.improvement_plan = {}
        self.task_breakdown = []
        
    def create_detailed_improvement_plan(self) -> Dict[str, any]:
        """具体的改善計画の策定"""
        
        print('=' * 80)
        print('Need積算修正 具体的改善計画とタスクダウン')
        print('目的: 包括的調査結果に基づく段階的実装計画')
        print('=' * 80)
        
        # 1. 改善計画の全体設計
        self._design_overall_improvement_strategy()
        
        # 2. 6段階の詳細タスクダウン
        self._create_step1_emergency_backup_tasks()
        self._create_step2_actual_based_design_tasks()
        self._create_step3_role_adjustment_tasks()
        self._create_step4_implementation_tasks()
        self._create_step5_verification_tasks()
        self._create_step6_production_tasks()
        
        # 3. リソース要件とスケジュール
        self._calculate_resource_requirements()
        self._create_implementation_schedule()
        
        # 4. リスク分析と対策
        self._analyze_risks_and_mitigation()
        
        return self._generate_comprehensive_plan_document()
    
    def _design_overall_improvement_strategy(self):
        """改善計画の全体設計"""
        print('\n【改善計画全体設計】')
        
        strategy = {
            'approach': 'PARTIAL_RECONSTRUCTION',
            'priority_focus': [
                '介護系職種Need値の現実化 (0.09-0.54倍 → 0.8-1.2倍)',
                '実配置ベース算出方式の導入',
                '職種別調整係数システムの構築',
                '21スロット構造の妥当性確認'
            ],
            'success_criteria': {
                '定量的目標': [
                    '介護系職種Need/実配置比率を0.8-1.2倍に正常化',
                    '全職種の現場妥当性スコア0.7以上達成',
                    '施設規模比較で中規模施設基準(1.0±0.2倍)達成'
                ],
                '定性的目標': [
                    '現場スタッフからの「現実的」評価獲得',
                    '過不足分析の信頼性向上',
                    '業界標準との整合性確保'
                ]
            },
            'non_goals': [
                'Need生成アルゴリズムの完全再開発',
                '24時間フルタイム対応への拡張',
                '他システムとの連携機能追加'
            ]
        }
        
        self.improvement_plan['overall_strategy'] = strategy
        
        print(f'改善アプローチ: {strategy["approach"]}')
        print(f'重点項目: {len(strategy["priority_focus"])}項目')
        print(f'成功基準: 定量{len(strategy["success_criteria"]["定量的目標"])}項目, 定性{len(strategy["success_criteria"]["定性的目標"])}項目')
    
    def _create_step1_emergency_backup_tasks(self):
        """Step1: 緊急バックアップタスク詳細化"""
        print('\n【Step1: 緊急バックアップタスク】')
        
        step1_tasks = [
            {
                'task_id': 'S1-T1',
                'title': '現在のNeedファイル完全バックアップ',
                'description': '全Need積算ファイルの即時バックアップ作成',
                'deliverables': [
                    'need_per_date_slot_role_*.parquet の完全コピー',
                    'バックアップ日時とファイル整合性確認レポート'
                ],
                'estimated_hours': 0.5,
                'priority': 'CRITICAL',
                'dependencies': [],
                'specific_actions': [
                    'extracted_results/out_p25_based/need_*.parquet の全ファイル特定',
                    'BACKUP_NEED_ORIGINAL_{timestamp} ディレクトリ作成',
                    'ファイルハッシュ値による整合性確認',
                    'バックアップ完了確認書の作成'
                ]
            },
            {
                'task_id': 'S1-T2', 
                'title': 'ロールバック手順書作成',
                'description': '修正失敗時の確実な復旧手順の文書化',
                'deliverables': [
                    'ロールバック手順書 (ROLLBACK_PROCEDURES.md)',
                    'リストア検証スクリプト'
                ],
                'estimated_hours': 1.0,
                'priority': 'HIGH',
                'dependencies': ['S1-T1'],
                'specific_actions': [
                    'バックアップファイルの復元手順詳細化',
                    '復旧後の動作確認チェックリスト作成',
                    'ロールバック実行スクリプトの作成',
                    '緊急時連絡フローの確立'
                ]
            },
            {
                'task_id': 'S1-T3',
                'title': '現在システムの動作ベースライン記録',
                'description': '修正前の過不足分析結果をベースラインとして記録',
                'deliverables': [
                    'current_baseline_analysis.json',
                    'ベースライン比較用レポートテンプレート'
                ],
                'estimated_hours': 1.5,
                'priority': 'HIGH', 
                'dependencies': ['S1-T1'],
                'specific_actions': [
                    '現在の組織全体・職種別・雇用形態別過不足の記録',
                    '主要KPIの現在値スナップショット取得',
                    '問題のある職種の詳細データ保存',
                    'ベースライン参照用インデックス作成'
                ]
            }
        ]
        
        self.task_breakdown.extend(step1_tasks)
        self.improvement_plan['step1_tasks'] = step1_tasks
        
        print(f'Step1タスク数: {len(step1_tasks)}')
        print(f'見積工数: {sum(t["estimated_hours"] for t in step1_tasks)}時間')
    
    def _create_step2_actual_based_design_tasks(self):
        """Step2: 実配置ベースNeed算出方式設計タスク"""
        print('\n【Step2: 実配置ベース方式設計タスク】')
        
        step2_tasks = [
            {
                'task_id': 'S2-T1',
                'title': '実配置データ分析と特性把握',
                'description': '現在の実配置データの詳細分析と特徴抽出',
                'deliverables': [
                    '実配置データ分析レポート',
                    '職種別・雇用形態別配置パターン分析'
                ],
                'estimated_hours': 2.0,
                'priority': 'HIGH',
                'dependencies': ['S1-T3'],
                'specific_actions': [
                    'intermediate_data.parquet の深掘り分析',
                    '職種別配置密度と時間分布の算出',
                    '雇用形態別勤務パターンの特定',
                    '季節性・曜日性の有無確認'
                ]
            },
            {
                'task_id': 'S2-T2',
                'title': '実配置ベースNeed算出アルゴリズム設計', 
                'description': '実配置の1.1倍を基準とする新Need算出方式の設計',
                'deliverables': [
                    'ActualBasedNeedCalculator クラス設計',
                    'アルゴリズム仕様書とフローチャート'
                ],
                'estimated_hours': 3.0,
                'priority': 'HIGH',
                'dependencies': ['S2-T1'],
                'specific_actions': [
                    '基準倍率 1.1 の妥当性検証',
                    '職種別配置実績からのNeed逆算方式',
                    '時間帯別・日別変動の考慮方法',
                    'スロット単位での精密計算設計'
                ]
            },
            {
                'task_id': 'S2-T3',
                'title': '業界標準整合性チェック機構設計',
                'description': '算出されたNeedが業界標準と乖離していないかのチェック機能',
                'deliverables': [
                    'IndustryStandardValidator クラス設計',
                    '業界標準データベース構築'
                ],
                'estimated_hours': 2.5,
                'priority': 'MEDIUM',
                'dependencies': ['S2-T2'],
                'specific_actions': [
                    '介護業界標準データの収集と構造化',
                    '施設規模別基準値テーブル作成',
                    '乖離アラート機能の設計',
                    '自動調整機能の閾値設定'
                ]
            }
        ]
        
        self.task_breakdown.extend(step2_tasks)
        self.improvement_plan['step2_tasks'] = step2_tasks
        
        print(f'Step2タスク数: {len(step2_tasks)}')
        print(f'見積工数: {sum(t["estimated_hours"] for t in step2_tasks)}時間')
    
    def _create_step3_role_adjustment_tasks(self):
        """Step3: 職種別調整係数設計・実装タスク"""
        print('\n【Step3: 職種別調整係数タスク】')
        
        step3_tasks = [
            {
                'task_id': 'S3-T1',
                'title': '介護系職種調整係数の算出',
                'description': '介護系職種のNeed値を0.8-1.2倍に正常化する係数計算',
                'deliverables': [
                    '介護系職種別調整係数テーブル',
                    '係数算出根拠レポート'
                ],
                'estimated_hours': 2.0,
                'priority': 'CRITICAL',
                'dependencies': ['S2-T1'],
                'specific_actions': [
                    '現在比率0.09-0.54倍の詳細分析',
                    '目標比率0.8-1.2倍への調整係数計算',
                    '介護（W/2）, 介護（W/3）, 介護 の個別係数',
                    '調整後の現実性シミュレーション'
                ]
            },
            {
                'task_id': 'S3-T2',
                'title': '全職種調整係数マトリクス作成',
                'description': '全11職種の個別調整係数と適用ルール体系化',
                'deliverables': [
                    'role_adjustment_matrix.json',
                    '職種別係数適用ルール仕様'
                ],
                'estimated_hours': 3.5,
                'priority': 'HIGH',
                'dependencies': ['S3-T1', 'S2-T2'],
                'specific_actions': [
                    '運転士(0.94倍) → 維持',
                    '看護師(0.93倍) → 微調整',
                    '機能訓練士(0.94倍) → 維持',
                    '管理系職種(1.00倍) → 維持',
                    '事務職種の妥当性再検証'
                ]
            },
            {
                'task_id': 'S3-T3',
                'title': '動的調整機構の実装',
                'description': '運用中の実績に基づく調整係数の自動更新機能',
                'deliverables': [
                    'DynamicAdjustmentEngine クラス',
                    '調整係数更新ログ機能'
                ],
                'estimated_hours': 4.0,
                'priority': 'MEDIUM',
                'dependencies': ['S3-T2'],
                'specific_actions': [
                    '実配置実績との乖離監視機能',
                    '閾値超過時の自動調整提案',
                    '調整履歴の記録と分析',
                    '手動オーバーライド機能'
                ]
            }
        ]
        
        self.task_breakdown.extend(step3_tasks)
        self.improvement_plan['step3_tasks'] = step3_tasks
        
        print(f'Step3タスク数: {len(step3_tasks)}')
        print(f'見積工数: {sum(t["estimated_hours"] for t in step3_tasks)}時間')
    
    def _create_step4_implementation_tasks(self):
        """Step4: 新Need積算システム実装タスク"""
        print('\n【Step4: 新システム実装タスク】')
        
        step4_tasks = [
            {
                'task_id': 'S4-T1',
                'title': 'ImprovedNeedCalculator 核心クラス実装',
                'description': '実配置ベース方式と調整係数を統合した新算出エンジン',
                'deliverables': [
                    'improved_need_calculator.py',
                    'ユニットテストスイート'
                ],
                'estimated_hours': 6.0,
                'priority': 'CRITICAL',
                'dependencies': ['S2-T2', 'S3-T2'],
                'specific_actions': [
                    'ActualBasedNeedCalculator の実装',
                    'RoleAdjustmentEngine の実装',
                    'IndustryStandardValidator の実装',
                    '統合インターフェースの構築'
                ]
            },
            {
                'task_id': 'S4-T2',
                'title': '新Needファイル生成システム構築',
                'description': '改善されたアルゴリズムで新しいNeedファイルを生成',
                'deliverables': [
                    'new_need_file_generator.py',
                    '生成済み新Needファイル一式'
                ],
                'estimated_hours': 4.0,
                'priority': 'CRITICAL',
                'dependencies': ['S4-T1'],
                'specific_actions': [
                    '既存ファイル形式との互換性確保',
                    '新need_per_date_slot_role_*.parquet 生成',
                    'ファイル名規則と構造の維持',
                    '生成プロセスのログ記録'
                ]
            },
            {
                'task_id': 'S4-T3',
                'title': '既存システムとの統合テスト環境構築',
                'description': '新Needファイルを既存過不足分析システムで動作確認',
                'deliverables': [
                    'integration_test_environment/',
                    '統合テスト実行スクリプト'
                ],
                'estimated_hours': 3.0,
                'priority': 'HIGH',
                'dependencies': ['S4-T2'],
                'specific_actions': [
                    'テスト専用シナリオディレクトリ作成',
                    '既存分析コードでの動作確認',
                    'comprehensive_organizational_shortage_analyzer 実行',
                    '結果比較とレポート生成'
                ]
            }
        ]
        
        self.task_breakdown.extend(step4_tasks)
        self.improvement_plan['step4_tasks'] = step4_tasks
        
        print(f'Step4タスク数: {len(step4_tasks)}')
        print(f'見積工数: {sum(t["estimated_hours"] for t in step4_tasks)}時間')
    
    def _create_step5_verification_tasks(self):
        """Step5: 検証・テスト実行タスク"""
        print('\n【Step5: 検証・テストタスク】')
        
        step5_tasks = [
            {
                'task_id': 'S5-T1',
                'title': '新Need積算結果の現実性検証',
                'description': '改善されたNeed値の現場妥当性と業界標準適合性確認',
                'deliverables': [
                    'need_improvement_verification_report.md',
                    '修正前後比較チャート'
                ],
                'estimated_hours': 2.5,
                'priority': 'CRITICAL',
                'dependencies': ['S4-T3'],
                'specific_actions': [
                    '介護系職種比率の0.8-1.2倍達成確認',
                    '全職種現場妥当性スコア0.7以上検証',
                    '中規模施設基準(1.0±0.2倍)達成確認',
                    'ベースライン結果との定量比較'
                ]
            },
            {
                'task_id': 'S5-T2', 
                'title': '過不足分析システム動作確認',
                'description': '新Needファイルでの組織過不足分析の正常動作検証',
                'deliverables': [
                    '新Need適用後の組織分析レポート',
                    '動作確認チェックリスト'
                ],
                'estimated_hours': 2.0,
                'priority': 'HIGH',
                'dependencies': ['S5-T1'],
                'specific_actions': [
                    'comprehensive_organizational_shortage_analyzer 実行',
                    '組織全体・職種別・雇用形態別分析結果確認',
                    'エラー・例外の有無確認',
                    'パフォーマンス影響の測定'
                ]
            },
            {
                'task_id': 'S5-T3',
                'title': '現場フィードバック収集とレビュー',
                'description': '改善結果に対する現場担当者からの評価収集',
                'deliverables': [
                    '現場フィードバックレポート',
                    '追加改善提案リスト'
                ],
                'estimated_hours': 1.0,
                'priority': 'MEDIUM',
                'dependencies': ['S5-T2'],
                'specific_actions': [
                    '修正前後の結果を現場責任者に提示',
                    '「現実的な数字になったか」の評価収集',
                    '残存する課題の特定',
                    'さらなる改善項目の洗い出し'
                ]
            }
        ]
        
        self.task_breakdown.extend(step5_tasks)
        self.improvement_plan['step5_tasks'] = step5_tasks
        
        print(f'Step5タスク数: {len(step5_tasks)}')
        print(f'見積工数: {sum(t["estimated_hours"] for t in step5_tasks)}時間')
    
    def _create_step6_production_tasks(self):
        """Step6: 本格運用・監視体制構築タスク"""
        print('\n【Step6: 本格運用タスク】')
        
        step6_tasks = [
            {
                'task_id': 'S6-T1',
                'title': '本番環境への新Needファイル適用',
                'description': '検証完了した新Needファイルの本番環境配備',
                'deliverables': [
                    '本番適用完了確認書',
                    '適用後動作確認レポート'
                ],
                'estimated_hours': 1.0,
                'priority': 'CRITICAL',
                'dependencies': ['S5-T3'],
                'specific_actions': [
                    '本番extracted_results/out_p25_based/への新ファイル配置',
                    '既存ファイルのリネーム保管',
                    '本番環境での動作確認',
                    'ダッシュボード表示の正常性確認'
                ]
            },
            {
                'task_id': 'S6-T2',
                'title': 'Need積算品質監視システム構築',
                'description': '継続的なNeed積算品質のモニタリング体制',
                'deliverables': [
                    'need_quality_monitor.py',
                    '品質監視ダッシュボード'
                ],
                'estimated_hours': 3.0,
                'priority': 'MEDIUM',
                'dependencies': ['S6-T1'],
                'specific_actions': [
                    'Need/実配置比率の自動監視',
                    '業界標準からの乖離アラート',
                    '異常値検知と通知システム',
                    '月次品質レポート自動生成'
                ]
            },
            {
                'task_id': 'S6-T3',
                'title': '運用・保守手順書の整備',
                'description': '改善されたNeedシステムの運用・保守ガイドライン',
                'deliverables': [
                    'NEED_SYSTEM_OPERATION_GUIDE.md',
                    'トラブルシューティングマニュアル'
                ],
                'estimated_hours': 2.0,
                'priority': 'MEDIUM',
                'dependencies': ['S6-T2'],
                'specific_actions': [
                    'Need積算アルゴリズムの運用説明',
                    '調整係数メンテナンス手順',
                    'よくある問題と対処法',
                    '定期見直しプロセスの文書化'
                ]
            }
        ]
        
        self.task_breakdown.extend(step6_tasks)
        self.improvement_plan['step6_tasks'] = step6_tasks
        
        print(f'Step6タスク数: {len(step6_tasks)}')
        print(f'見積工数: {sum(t["estimated_hours"] for t in step6_tasks)}時間')
    
    def _calculate_resource_requirements(self):
        """リソース要件の算出"""
        print('\n【リソース要件算出】')
        
        # 工数集計
        total_hours = sum(task['estimated_hours'] for task in self.task_breakdown)
        critical_hours = sum(task['estimated_hours'] for task in self.task_breakdown 
                           if task['priority'] == 'CRITICAL')
        high_hours = sum(task['estimated_hours'] for task in self.task_breakdown 
                        if task['priority'] == 'HIGH')
        
        # ステップ別工数
        step_hours = {}
        for step in ['step1', 'step2', 'step3', 'step4', 'step5', 'step6']:
            step_tasks = self.improvement_plan.get(f'{step}_tasks', [])
            step_hours[step] = sum(task['estimated_hours'] for task in step_tasks)
        
        resource_requirements = {
            'total_estimated_hours': total_hours,
            'critical_priority_hours': critical_hours,
            'high_priority_hours': high_hours,
            'step_wise_hours': step_hours,
            'recommended_team_size': 2,  # 主担当1名 + レビュアー1名
            'estimated_calendar_days': max(7, total_hours / 4),  # 1日4時間稼働想定
            'required_skills': [
                'Python プログラミング (中級以上)',
                'pandas データ分析 (中級)',
                '介護業界知識 (基礎)',
                'システム設計・実装 (中級)',
                'テスト設計・実行 (基礎)'
            ]
        }
        
        self.improvement_plan['resource_requirements'] = resource_requirements
        
        print(f'総見積工数: {total_hours}時間')
        print(f'重要度CRITICAL: {critical_hours}時間 ({critical_hours/total_hours*100:.1f}%)')
        print(f'推奨チーム規模: {resource_requirements["recommended_team_size"]}名')
        print(f'見積実装期間: {resource_requirements["estimated_calendar_days"]:.0f}日')
    
    def _create_implementation_schedule(self):
        """実装スケジュールの作成"""
        print('\n【実装スケジュール作成】')
        
        # 依存関係を考慮したスケジュール
        schedule = {
            'Phase 1: 準備・設計 (Day 1-3)': [
                'S1-T1: Needファイルバックアップ (即時)',
                'S1-T2: ロールバック手順書 (Day 1)',
                'S1-T3: ベースライン記録 (Day 1-2)',
                'S2-T1: 実配置データ分析 (Day 2-3)'
            ],
            'Phase 2: 設計・開発 (Day 3-6)': [
                'S2-T2: Need算出アルゴリズム設計 (Day 3-4)',
                'S3-T1: 介護系職種調整係数算出 (Day 4)',
                'S3-T2: 全職種調整係数マトリクス (Day 4-5)',
                'S2-T3: 業界標準整合性チェック設計 (Day 5-6)'
            ],
            'Phase 3: 実装・統合 (Day 6-10)': [
                'S4-T1: 核心クラス実装 (Day 6-8)',
                'S4-T2: 新Needファイル生成 (Day 8-9)',
                'S4-T3: 統合テスト環境構築 (Day 9-10)'
            ],
            'Phase 4: 検証・本格運用 (Day 10-12)': [
                'S5-T1: 現実性検証 (Day 10-11)',
                'S5-T2: システム動作確認 (Day 11)',
                'S6-T1: 本番環境適用 (Day 11)',
                'S6-T2: 監視システム構築 (Day 12)'
            ]
        }
        
        # 並行実行可能タスクの特定
        parallel_opportunities = [
            'S1-T2とS1-T3は並行実行可能',
            'S3-T1とS2-T3は並行実行可能',
            'S5-T1とS5-T2は順次実行必須'
        ]
        
        self.improvement_plan['implementation_schedule'] = {
            'phases': schedule,
            'parallel_opportunities': parallel_opportunities,
            'critical_path': ['S1-T1', 'S2-T1', 'S2-T2', 'S4-T1', 'S4-T2', 'S5-T1', 'S6-T1'],
            'total_duration_days': 12
        }
        
        print(f'実装フェーズ数: {len(schedule)}')
        print(f'総実装期間: 12日')
        print(f'クリティカルパス長: {len(self.improvement_plan["implementation_schedule"]["critical_path"])}タスク')
    
    def _analyze_risks_and_mitigation(self):
        """リスク分析と対策"""
        print('\n【リスク分析と対策】')
        
        risks = [
            {
                'risk_id': 'R1',
                'title': '新Need値が現場感覚と乖離',
                'probability': 'MEDIUM',
                'impact': 'HIGH',
                'mitigation': [
                    '段階的調整係数の適用',
                    '現場フィードバックの早期収集',
                    'ロールバック手順の準備'
                ]
            },
            {
                'risk_id': 'R2', 
                'title': '既存システムとの互換性問題',
                'probability': 'LOW',
                'impact': 'CRITICAL',
                'mitigation': [
                    '統合テスト環境での徹底検証',
                    'ファイル形式互換性の事前確認',
                    'バックアップからの即時復旧体制'
                ]
            },
            {
                'risk_id': 'R3',
                'title': '実装期間の超過',
                'probability': 'MEDIUM',
                'impact': 'MEDIUM',
                'mitigation': [
                    '重要度CRITICAL タスクの優先実装',
                    '並行作業可能タスクの積極活用',
                    'スコープ調整による期間管理'
                ]
            },
            {
                'risk_id': 'R4',
                'title': '21スロット構造の制約影響',
                'probability': 'HIGH',
                'impact': 'LOW',
                'mitigation': [
                    '現在構造を前提とした設計',
                    '将来拡張性の考慮',
                    '制約の明文化と合意形成'
                ]
            }
        ]
        
        self.improvement_plan['risk_analysis'] = {
            'identified_risks': risks,
            'overall_risk_level': 'MEDIUM',
            'key_success_factors': [
                '現場関係者との継続的コミュニケーション',
                '段階的実装による影響最小化',
                '十分なテスト・検証の実施'
            ]
        }
        
        print(f'識別リスク数: {len(risks)}')
        print(f'総合リスクレベル: MEDIUM')
        print(f'重要成功要因: 3項目')
    
    def _generate_comprehensive_plan_document(self) -> Dict[str, any]:
        """包括的計画書の生成"""
        print('\n' + '=' * 80)
        print('Need積算修正 具体的改善計画書 完成')
        print('=' * 80)
        
        plan_summary = {
            'total_tasks': len(self.task_breakdown),
            'total_estimated_hours': sum(task['estimated_hours'] for task in self.task_breakdown),
            'critical_tasks': len([t for t in self.task_breakdown if t['priority'] == 'CRITICAL']),
            'implementation_phases': 4,
            'estimated_duration_days': 12,
            'success_probability': 'HIGH (85%)'
        }
        
        print(f'\n【計画サマリー】')
        print(f'総タスク数: {plan_summary["total_tasks"]}')
        print(f'見積工数: {plan_summary["total_estimated_hours"]}時間')
        print(f'重要タスク数: {plan_summary["critical_tasks"]}')
        print(f'実装期間: {plan_summary["estimated_duration_days"]}日')
        print(f'成功確率: {plan_summary["success_probability"]}')
        
        return {
            'plan_metadata': {
                'title': 'Need積算修正 具体的改善計画',
                'version': '1.0',
                'created_date': datetime.now().isoformat(),
                'target_completion': (datetime.now() + timedelta(days=12)).isoformat()
            },
            'improvement_plan': self.improvement_plan,
            'task_breakdown': self.task_breakdown,
            'plan_summary': plan_summary,
            'next_immediate_actions': [
                'S1-T1: Needファイル緊急バックアップの即時実行',
                'プロジェクトチーム編成と役割分担の決定',
                'S1-T2: ロールバック手順書の作成開始'
            ]
        }

def create_detailed_improvement_plan():
    """具体的改善計画の作成実行"""
    scenario_dir = Path('extracted_results/out_p25_based')
    
    if not scenario_dir.exists():
        print(f'エラー: シナリオディレクトリが見つかりません: {scenario_dir}')
        return None
    
    planner = DetailedNeedImprovementPlanner(scenario_dir)
    return planner.create_detailed_improvement_plan()

if __name__ == "__main__":
    plan = create_detailed_improvement_plan()
    
    if plan:
        # 計画書をJSONファイルに保存
        output_file = Path('detailed_need_improvement_plan.json')
        
        # JSON serializable な形式に変換
        json_compatible_plan = json.loads(json.dumps(plan, default=str))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_compatible_plan, f, ensure_ascii=False, indent=2)
        
        print(f'\n詳細改善計画書を保存: {output_file}')
        
        # タスクリストのCSV出力
        import csv
        csv_file = Path('need_improvement_tasks.csv')
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['TaskID', 'Title', 'Priority', 'Hours', 'Dependencies', 'Deliverables'])
            
            for task in plan['task_breakdown']:
                writer.writerow([
                    task['task_id'],
                    task['title'],
                    task['priority'],
                    task['estimated_hours'],
                    ', '.join(task['dependencies']),
                    ', '.join(task['deliverables'][:2])  # 最初の2つのみ
                ])
        
        print(f'タスクリスト CSV出力: {csv_file}')
        print('=' * 80)
        print('改善計画とタスクダウン完了 - 実装準備完了')
        print('=' * 80)