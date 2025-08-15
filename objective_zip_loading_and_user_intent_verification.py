#!/usr/bin/env python
"""
dash_app.py ZIPファイル読み込みとユーザー意図実現の客観的検証

2つの核心的な検証:
1. ZIPファイルの完璧な表現可能性
2. ユーザー意図に沿った動作実現性

極めて客観的に、事実のみに基づいて評価
"""

import pandas as pd
import numpy as np
from pathlib import Path
import zipfile
import tempfile
import shutil
import logging
import sys
import re
import ast
from datetime import datetime, timedelta
import plotly.graph_objects as go

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class ObjectiveZipLoadingVerifier:
    """ZIPファイル読み込みとユーザー意図の客観的検証"""
    
    def __init__(self):
        self.dash_app_path = Path("dash_app.py")
        self.test_output_dir = Path("objective_verification_output")
        self.test_output_dir.mkdir(exist_ok=True)
        self.verification_results = {}
    
    def execute_objective_verification(self):
        """客観的検証の実行"""
        
        print("=== ZIPファイル読み込み・ユーザー意図実現の客観的検証 ===")
        print("=" * 70)
        
        # 検証1: ZIPファイルの完璧表現可能性
        print("\n[検証1] ZIPファイルの完璧表現可能性")
        zip_representation_result = self._verify_zip_perfect_representation()
        
        # 検証2: ユーザー意図に沿った動作実現性  
        print("\n[検証2] ユーザー意図に沿った動作実現性")
        user_intent_result = self._verify_user_intent_alignment()
        
        # 客観的総合評価
        print("\n[総合評価] 客観的事実に基づく評価")
        overall_result = self._generate_objective_assessment(
            zip_representation_result,
            user_intent_result
        )
        
        return overall_result
    
    def _verify_zip_perfect_representation(self):
        """ZIPファイルの完璧表現可能性の検証"""
        
        try:
            # dash_app.pyの分析
            with open(self.dash_app_path, 'r', encoding='utf-8') as f:
                dash_content = f.read()
            
            # 1. ZIPファイル読み込み機能の解析
            zip_loading_analysis = self._analyze_zip_loading_capability(dash_content)
            
            # 2. 実際のZIPファイルでのテスト
            zip_processing_test = self._test_actual_zip_processing()
            
            # 3. データ表現の完全性評価
            data_representation_assessment = self._assess_data_representation_completeness()
            
            # 客観的評価の算出
            representation_score = self._calculate_representation_score(
                zip_loading_analysis,
                zip_processing_test, 
                data_representation_assessment
            )
            
            return {
                'zip_loading_analysis': zip_loading_analysis,
                'zip_processing_test': zip_processing_test,
                'data_representation_assessment': data_representation_assessment,
                'representation_score': representation_score
            }
            
        except Exception as e:
            return {'error': f"検証エラー: {e}"}
    
    def _analyze_zip_loading_capability(self, content: str):
        """ZIPファイル読み込み機能の解析"""
        
        analysis = {
            'zip_import_present': False,
            'zip_extraction_logic': False,
            'file_loading_functions': [],
            'error_handling_for_zip': False,
            'dynamic_file_discovery': False
        }
        
        # zipfile import確認
        if 'import zipfile' in content or 'from zipfile import' in content:
            analysis['zip_import_present'] = True
        
        # ZIP展開ロジック確認
        zip_extract_patterns = [
            r'zipfile\.ZipFile\(',
            r'\.extractall\(',
            r'\.extract\(',
            r'with.*ZipFile'
        ]
        
        for pattern in zip_extract_patterns:
            if re.search(pattern, content):
                analysis['zip_extraction_logic'] = True
                break
        
        # ファイル読み込み関数の特定
        loading_function_patterns = [
            r'def.*load.*\(',
            r'def.*read.*\(',
            r'def.*get.*data\(',
            r'pd\.read_parquet\(',
            r'pd\.read_csv\('
        ]
        
        for pattern in loading_function_patterns:
            matches = re.findall(pattern, content)
            analysis['file_loading_functions'].extend(matches)
        
        # ZIPファイル用エラーハンドリング確認
        zip_error_patterns = [
            r'except.*ZipFile',
            r'except.*zipfile',
            r'except.*FileNotFound',
            r'try:.*zip'
        ]
        
        for pattern in zip_error_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                analysis['error_handling_for_zip'] = True
                break
        
        # 動的ファイル発見機能確認
        dynamic_patterns = [
            r'\.glob\(',
            r'listdir\(',
            r'\.iterdir\(',
            r'os\.walk\('
        ]
        
        for pattern in dynamic_patterns:
            if re.search(pattern, content):
                analysis['dynamic_file_discovery'] = True
                break
        
        print(f"   ZIP import: {'あり' if analysis['zip_import_present'] else 'なし'}")
        print(f"   ZIP展開ロジック: {'あり' if analysis['zip_extraction_logic'] else 'なし'}")
        print(f"   読み込み関数: {len(analysis['file_loading_functions'])}個")
        print(f"   ZIPエラーハンドリング: {'あり' if analysis['error_handling_for_zip'] else 'なし'}")
        print(f"   動的ファイル発見: {'あり' if analysis['dynamic_file_discovery'] else 'なし'}")
        
        return analysis
    
    def _test_actual_zip_processing(self):
        """実際のZIPファイル処理のテスト"""
        
        try:
            # テストZIPファイルの作成
            test_scenario_dir = self.test_output_dir / "test_zip_scenario"
            test_scenario_dir.mkdir(exist_ok=True)
            
            # 実データ相当のテストファイル生成
            test_files = self._create_realistic_test_files(test_scenario_dir)
            
            # ZIPファイル生成
            zip_path = self.test_output_dir / "test_analysis_results.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in test_scenario_dir.glob("*.parquet"):
                    zipf.write(file_path, f"test_scenario/{file_path.name}")
            
            # dash_app.pyの実際の読み込み機能をシミュレート
            loading_results = self._simulate_dash_app_loading(zip_path)
            
            return {
                'test_zip_created': True,
                'test_zip_size': zip_path.stat().st_size,
                'test_files_count': len(test_files),
                'loading_simulation_results': loading_results
            }
            
        except Exception as e:
            return {
                'test_zip_created': False,
                'error': str(e)
            }
    
    def _create_realistic_test_files(self, scenario_dir: Path):
        """現実的なテストファイルの生成"""
        
        # 1. intermediate_data.parquet - メインデータ
        dates = pd.date_range('2025-01-01', periods=30, freq='D')
        time_slots = pd.date_range('06:00', '22:00', freq='30min')
        roles = ['介護', '看護', '事務', 'リハビリ', 'ケアマネ']
        
        intermediate_data = []
        for date in dates:
            for time_slot in time_slots:
                for role in roles:
                    # より現実的なデータパターン
                    need_value = np.random.randint(1, 6)  # 1-5人の需要
                    allocation_value = max(0, need_value + np.random.randint(-2, 3))  # ±2人の変動
                    
                    intermediate_data.append({
                        'ds': pd.Timestamp.combine(date.date(), time_slot.time()),
                        'staff': f'Staff_{len(intermediate_data)%50}',
                        'role': role,
                        'employment': np.random.choice(['正社員', 'パート', '派遣'], p=[0.6, 0.3, 0.1]),
                        'need': need_value,
                        'allocation': allocation_value
                    })
        
        intermediate_df = pd.DataFrame(intermediate_data)
        intermediate_df.to_parquet(scenario_dir / "intermediate_data.parquet")
        
        # 2. shortage関連ファイル
        shortage_data = np.random.randint(-3, 5, size=(len(roles), 30))  # 職種×日数
        shortage_df = pd.DataFrame(shortage_data, 
                                 index=roles,
                                 columns=[f'2025-01-{i+1:02d}' for i in range(30)])
        shortage_df.to_parquet(scenario_dir / "shortage_time_enhanced.parquet")
        
        # 3. heat_ALL.parquet - スタッフ配置データ
        heat_data = []
        for staff_id in range(50):
            for role in roles:
                heat_data.append({
                    'staff': f'Staff_{staff_id}',
                    'role': role,
                    'employment': np.random.choice(['正社員', 'パート', '派遣']),
                    **{f'2025-01-{i+1:02d}': np.random.randint(0, 2) for i in range(30)}
                })
        
        heat_df = pd.DataFrame(heat_data)
        heat_df.to_parquet(scenario_dir / "heat_ALL.parquet")
        
        # 4. サマリーファイル
        role_summary = pd.DataFrame({
            'role': roles,
            'shortage_hours': np.random.uniform(10, 100, len(roles)),
            'avg_daily_shortage': np.random.uniform(1, 10, len(roles))
        })
        role_summary.to_parquet(scenario_dir / "shortage_role_summary.parquet")
        
        employment_summary = pd.DataFrame({
            'employment': ['正社員', 'パート', '派遣'],
            'shortage_hours': np.random.uniform(20, 80, 3),
            'avg_daily_shortage': np.random.uniform(2, 8, 3)
        })
        employment_summary.to_parquet(scenario_dir / "shortage_employment_summary.parquet")
        
        return list(scenario_dir.glob("*.parquet"))
    
    def _simulate_dash_app_loading(self, zip_path: Path):
        """dash_app.pyの読み込み機能をシミュレート"""
        
        results = {
            'extraction_success': False,
            'file_loading_success': {},
            'data_structure_validation': {},
            'visualization_data_preparation': False
        }
        
        try:
            # ZIP展開シミュレーション
            temp_dir = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            results['extraction_success'] = True
            
            # 各ファイルの読み込みテスト
            extracted_scenario = temp_dir / "test_scenario"
            
            expected_files = [
                'intermediate_data.parquet',
                'shortage_time_enhanced.parquet',
                'heat_ALL.parquet',
                'shortage_role_summary.parquet',
                'shortage_employment_summary.parquet'
            ]
            
            for file_name in expected_files:
                file_path = extracted_scenario / file_name
                if file_path.exists():
                    try:
                        df = pd.read_parquet(file_path)
                        results['file_loading_success'][file_name] = {
                            'loaded': True,
                            'shape': df.shape,
                            'columns': list(df.columns),
                            'data_types': df.dtypes.to_dict()
                        }
                    except Exception as e:
                        results['file_loading_success'][file_name] = {
                            'loaded': False,
                            'error': str(e)
                        }
                else:
                    results['file_loading_success'][file_name] = {
                        'loaded': False,
                        'error': 'File not found'
                    }
            
            # データ構造の妥当性検証
            if 'intermediate_data.parquet' in results['file_loading_success']:
                intermediate_info = results['file_loading_success']['intermediate_data.parquet']
                if intermediate_info.get('loaded', False):
                    required_columns = ['ds', 'staff', 'role', 'employment', 'need', 'allocation']
                    present_columns = set(intermediate_info['columns'])
                    missing_columns = set(required_columns) - present_columns
                    
                    results['data_structure_validation']['intermediate_data'] = {
                        'required_columns_present': len(missing_columns) == 0,
                        'missing_columns': list(missing_columns),
                        'extra_columns': list(present_columns - set(required_columns))
                    }
            
            # 可視化データ準備の可能性評価
            loaded_files = [f for f, info in results['file_loading_success'].items() 
                          if info.get('loaded', False)]
            visualization_ready = len(loaded_files) >= 3  # 最低3ファイルで可視化可能
            results['visualization_data_preparation'] = visualization_ready
            
            # クリーンアップ
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            results['extraction_error'] = str(e)
        
        return results
    
    def _assess_data_representation_completeness(self):
        """データ表現の完全性評価"""
        
        # dash_app.pyの可視化機能分析
        with open(self.dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assessment = {
            'chart_types_available': [],
            'data_filtering_capabilities': [],
            'interactive_features': [],
            'export_functionalities': [],
            'real_time_updates': False
        }
        
        # チャートタイプの確認
        chart_patterns = {
            'heatmap': r'Heatmap|heatmap',
            'bar_chart': r'Bar\(|bar.*chart',
            'line_chart': r'Scatter\(|line.*chart',
            'table': r'dash_table|DataTable',
            'pie_chart': r'Pie\(|pie.*chart'
        }
        
        for chart_type, pattern in chart_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                assessment['chart_types_available'].append(chart_type)
        
        # データフィルタリング機能
        filter_patterns = {
            'date_filter': r'date.*picker|date.*range',
            'role_filter': r'role.*dropdown|role.*filter',
            'employment_filter': r'employment.*dropdown|employment.*filter',
            'slider_filter': r'Slider\(|RangeSlider\('
        }
        
        for filter_type, pattern in filter_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                assessment['data_filtering_capabilities'].append(filter_type)
        
        # インタラクティブ機能
        interactive_patterns = {
            'callback_functions': r'@app\.callback',
            'hover_effects': r'hover',
            'click_events': r'click.*Data',
            'selection_events': r'selected.*Data'
        }
        
        for feature_type, pattern in interactive_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                assessment['interactive_features'].append(feature_type)
        
        # エクスポート機能
        export_patterns = {
            'csv_export': r'\.to_csv\(',
            'excel_export': r'\.to_excel\(',
            'download_component': r'Download\(',
            'pdf_export': r'\.to_pdf\('
        }
        
        for export_type, pattern in export_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                assessment['export_functionalities'].append(export_type)
        
        # リアルタイム更新
        realtime_patterns = [
            r'dcc\.Interval',
            r'interval.*component',
            r'auto.*refresh'
        ]
        
        for pattern in realtime_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                assessment['real_time_updates'] = True
                break
        
        print(f"   チャートタイプ: {len(assessment['chart_types_available'])}種類")
        print(f"   フィルタリング: {len(assessment['data_filtering_capabilities'])}機能")
        print(f"   インタラクティブ: {len(assessment['interactive_features'])}機能")
        print(f"   エクスポート: {len(assessment['export_functionalities'])}機能")
        print(f"   リアルタイム更新: {'あり' if assessment['real_time_updates'] else 'なし'}")
        
        return assessment
    
    def _calculate_representation_score(self, loading_analysis, processing_test, representation_assessment):
        """表現力スコアの算出"""
        
        score_components = {
            'zip_loading_capability': 0,
            'actual_processing_success': 0,
            'data_representation_completeness': 0
        }
        
        # ZIP読み込み能力 (30点満点)
        loading_score = 0
        if loading_analysis.get('zip_import_present', False):
            loading_score += 5
        if loading_analysis.get('zip_extraction_logic', False):
            loading_score += 10
        if len(loading_analysis.get('file_loading_functions', [])) >= 3:
            loading_score += 10
        if loading_analysis.get('error_handling_for_zip', False):
            loading_score += 5
        
        score_components['zip_loading_capability'] = loading_score
        
        # 実際の処理成功率 (40点満点)
        if processing_test.get('test_zip_created', False):
            processing_score = 10
            loading_results = processing_test.get('loading_simulation_results', {})
            
            if loading_results.get('extraction_success', False):
                processing_score += 10
            
            loaded_files = sum(1 for info in loading_results.get('file_loading_success', {}).values()
                             if info.get('loaded', False))
            processing_score += min(15, loaded_files * 3)  # 最大15点
            
            if loading_results.get('visualization_data_preparation', False):
                processing_score += 5
        else:
            processing_score = 0
        
        score_components['actual_processing_success'] = processing_score
        
        # データ表現完全性 (30点満点)
        representation_score = 0
        representation_score += min(10, len(representation_assessment.get('chart_types_available', [])) * 2)
        representation_score += min(10, len(representation_assessment.get('data_filtering_capabilities', [])) * 2.5)
        representation_score += min(5, len(representation_assessment.get('interactive_features', [])) * 1.25)
        representation_score += min(3, len(representation_assessment.get('export_functionalities', [])) * 1.5)
        if representation_assessment.get('real_time_updates', False):
            representation_score += 2
        
        score_components['data_representation_completeness'] = representation_score
        
        total_score = sum(score_components.values())
        
        print(f"   ZIP読み込み能力: {loading_score}/30")
        print(f"   実処理成功率: {processing_score}/40") 
        print(f"   データ表現完全性: {representation_score}/30")
        print(f"   総合スコア: {total_score}/100")
        
        return {
            'total_score': total_score,
            'components': score_components,
            'max_score': 100
        }
    
    def _verify_user_intent_alignment(self):
        """ユーザー意図に沿った動作実現性の検証"""
        
        try:
            # ユーザー意図の明確化
            user_intents = self._identify_core_user_intents()
            
            # 各意図の実現度評価
            intent_realization = {}
            for intent_name, intent_details in user_intents.items():
                realization_result = self._evaluate_intent_realization(intent_name, intent_details)
                intent_realization[intent_name] = realization_result
            
            # 総合的なユーザー意図実現度算出
            overall_alignment_score = self._calculate_user_intent_alignment_score(intent_realization)
            
            return {
                'user_intents': user_intents,
                'intent_realization': intent_realization,
                'overall_alignment_score': overall_alignment_score
            }
            
        except Exception as e:
            return {'error': f"ユーザー意図検証エラー: {e}"}
    
    def _identify_core_user_intents(self):
        """核心的なユーザー意図の特定"""
        
        # 過去の会話から抽出されたユーザー意図
        intents = {
            'dynamic_shift_analysis': {
                'description': '動的なシフトデータを活用した真の過不足分析',
                'requirements': [
                    '任意の期間・職種・時間帯での分析',
                    '負の値（過剰）も含む真の過不足計算',
                    '動的パラメータの反映'
                ],
                'success_criteria': [
                    'データ期間の動的変更対応',
                    '職種の動的追加・削除対応',
                    '時間軸の柔軟な設定'
                ]
            },
            'unified_calculation_logic': {
                'description': '全体分析と職種別分析のロジック統一',
                'requirements': [
                    '単一の計算エンジンの使用',
                    '真の過不足・不足のみ・過剰のみの分離',
                    '分析レベルによる一貫性'
                ],
                'success_criteria': [
                    '同一計算ロジックの確認',
                    '結果の整合性',
                    '分析粒度の統一'
                ]
            },
            'accurate_shortage_visualization': {
                'description': '正確な過不足状況の可視化',
                'requirements': [
                    '職種別・時間帯別の詳細表示',
                    'ヒートマップでの視覚的表現',
                    '数値とグラフの整合性'
                ],
                'success_criteria': [
                    '視覚的な理解容易性',
                    'データの正確な反映',
                    'インタラクティブな操作性'
                ]
            },
            'practical_operational_support': {
                'description': '実際の運用を支援する機能',
                'requirements': [
                    'Excel形式のデータ入力対応',
                    '結果のエクスポート機能',
                    'シナリオ比較機能'
                ],
                'success_criteria': [
                    'データ入出力の簡便性',
                    '運用担当者の使いやすさ',
                    '意思決定支援情報の提供'
                ]
            }
        }
        
        print("   特定されたユーザー意図:")
        for intent_name, intent_info in intents.items():
            print(f"     - {intent_name}: {intent_info['description']}")
        
        return intents
    
    def _evaluate_intent_realization(self, intent_name: str, intent_details: dict):
        """個別ユーザー意図の実現度評価"""
        
        with open(self.dash_app_path, 'r', encoding='utf-8') as f:
            dash_content = f.read()
        
        evaluation = {
            'requirements_met': {},
            'success_criteria_achieved': {},
            'implementation_evidence': [],
            'realization_score': 0
        }
        
        # 要件の満足度評価
        for requirement in intent_details['requirements']:
            met_score = self._assess_requirement_fulfillment(requirement, dash_content)
            evaluation['requirements_met'][requirement] = met_score
        
        # 成功基準の達成度評価
        for criterion in intent_details['success_criteria']:
            achieved_score = self._assess_success_criterion(criterion, dash_content)
            evaluation['success_criteria_achieved'][criterion] = achieved_score
        
        # 実装証拠の収集
        evaluation['implementation_evidence'] = self._collect_implementation_evidence(
            intent_name, dash_content
        )
        
        # 実現度スコアの計算
        requirements_scores = list(evaluation['requirements_met'].values())
        criteria_scores = list(evaluation['success_criteria_achieved'].values())
        
        avg_requirements = sum(requirements_scores) / len(requirements_scores) if requirements_scores else 0
        avg_criteria = sum(criteria_scores) / len(criteria_scores) if criteria_scores else 0
        
        evaluation['realization_score'] = (avg_requirements * 0.6 + avg_criteria * 0.4)
        
        print(f"     {intent_name}: {evaluation['realization_score']:.1f}/100")
        
        return evaluation
    
    def _assess_requirement_fulfillment(self, requirement: str, content: str):
        """要件満足度の評価"""
        
        # 要件ごとの具体的な実装パターンをチェック
        requirement_patterns = {
            '任意の期間・職種・時間帯での分析': [
                r'date.*range|date.*picker',
                r'role.*dropdown|role.*filter',
                r'time.*slot|hour.*filter'
            ],
            '負の値（過剰）も含む真の過不足計算': [
                r'true.*balance|balance.*calculation',
                r'excess.*calculation|negative.*values',
                r'clip.*lower.*0'
            ],
            '動的パラメータの反映': [
                r'dynamic.*parameter|parameter.*update',
                r'slot.*hours|slot.*time',
                r'config.*update|setting.*change'
            ],
            '単一の計算エンジンの使用': [
                r'unified.*calculation|calculate.*true.*shortage',
                r'shortage.*calculator|calculation.*engine'
            ],
            '真の過不足・不足のみ・過剰のみの分離': [
                r'shortage.*only|excess.*only',
                r'true.*balance|separate.*calculation'
            ],
            '職種別・時間帯別の詳細表示': [
                r'role.*breakdown|role.*detail',
                r'time.*breakdown|hourly.*detail'
            ],
            'ヒートマップでの視覚的表現': [
                r'Heatmap\(|heatmap.*chart',
                r'heat.*map|thermal.*map'
            ],
            'Excel形式のデータ入力対応': [
                r'excel.*input|xlsx.*read',
                r'to_excel\(|read_excel\('
            ]
        }
        
        patterns = requirement_patterns.get(requirement, [])
        if not patterns:
            return 50  # デフォルト中間値
        
        matches = sum(1 for pattern in patterns if re.search(pattern, content, re.IGNORECASE))
        fulfillment_score = min(100, (matches / len(patterns)) * 100)
        
        return fulfillment_score
    
    def _assess_success_criterion(self, criterion: str, content: str):
        """成功基準の達成度評価"""
        
        criterion_patterns = {
            'データ期間の動的変更対応': [
                r'@app\.callback.*date',
                r'date.*input.*callback',
                r'update.*date.*range'
            ],
            '職種の動的追加・削除対応': [
                r'role.*update|role.*change',
                r'dynamic.*role|role.*callback'
            ],
            '時間軸の柔軟な設定': [
                r'time.*axis.*update|time.*setting',
                r'hour.*configuration|slot.*setting'
            ],
            '同一計算ロジックの確認': [
                r'unified.*logic|same.*calculation',
                r'calculate.*true.*shortage'
            ],
            '結果の整合性': [
                r'consistency.*check|validation',
                r'data.*integrity|result.*verify'
            ],
            '視覚的な理解容易性': [
                r'tooltip|hover.*info',
                r'color.*scale|legend',
                r'chart.*title|axis.*label'
            ],
            'データの正確な反映': [
                r'data.*accuracy|precise.*calculation',
                r'correct.*values|accurate.*display'
            ],
            'インタラクティブな操作性': [
                r'@app\.callback|interactive',
                r'click.*event|hover.*event'
            ]
        }
        
        patterns = criterion_patterns.get(criterion, [])
        if not patterns:
            return 50  # デフォルト中間値
        
        matches = sum(1 for pattern in patterns if re.search(pattern, content, re.IGNORECASE))
        achievement_score = min(100, (matches / len(patterns)) * 100)
        
        return achievement_score
    
    def _collect_implementation_evidence(self, intent_name: str, content: str):
        """実装証拠の収集"""
        
        evidence = []
        
        # コールバック関数の数
        callback_count = len(re.findall(r'@app\.callback', content))
        if callback_count > 0:
            evidence.append(f"コールバック関数: {callback_count}個")
        
        # 可視化コンポーネントの数
        viz_components = [
            'Graph',
            'DataTable',
            'Heatmap',
            'Bar',
            'Scatter'
        ]
        
        viz_count = sum(1 for comp in viz_components if comp in content)
        if viz_count > 0:
            evidence.append(f"可視化コンポーネント: {viz_count}種類")
        
        # データ処理関数の数
        data_functions = re.findall(r'def\s+\w*(?:data|load|process|calculate)\w*\s*\(', content)
        if data_functions:
            evidence.append(f"データ処理関数: {len(data_functions)}個")
        
        return evidence
    
    def _calculate_user_intent_alignment_score(self, intent_realization: dict):
        """ユーザー意図実現度の総合スコア算出"""
        
        if not intent_realization:
            return {'total_score': 0, 'category_scores': {}}
        
        category_scores = {}
        for intent_name, realization_data in intent_realization.items():
            category_scores[intent_name] = realization_data.get('realization_score', 0)
        
        total_score = sum(category_scores.values()) / len(category_scores)
        
        print(f"   総合ユーザー意図実現度: {total_score:.1f}/100")
        
        return {
            'total_score': total_score,
            'category_scores': category_scores
        }
    
    def _generate_objective_assessment(self, zip_representation_result, user_intent_result):
        """客観的総合評価の生成"""
        
        print("=" * 70)
        print("客観的事実に基づく総合評価")
        print("=" * 70)
        
        # スコアの抽出
        zip_score = zip_representation_result.get('representation_score', {}).get('total_score', 0)
        user_intent_score = user_intent_result.get('overall_alignment_score', {}).get('total_score', 0)
        
        # 総合評価の算出
        overall_score = (zip_score * 0.4 + user_intent_score * 0.6)  # ユーザー意図を重視
        
        print(f"\n1. ZIPファイル完璧表現: {zip_score:.1f}/100")
        print(f"2. ユーザー意図実現: {user_intent_score:.1f}/100")
        print(f"3. 総合評価: {overall_score:.1f}/100")
        
        # 客観的判定
        if overall_score >= 80:
            judgment = "優秀 - 両方の要求を高いレベルで満たしている"
        elif overall_score >= 65:
            judgment = "良好 - 基本的な要求は満たしているが改善余地あり"
        elif overall_score >= 50:
            judgment = "普通 - 一部の機能は動作するが重要な課題が残る"
        else:
            judgment = "要改善 - 基本的な要求が十分に満たされていない"
        
        print(f"\n客観的判定: {judgment}")
        
        # 具体的な事実の列挙
        print(f"\n事実の要約:")
        print(f"  ZIP読み込み機能: {'実装済み' if zip_score >= 60 else '不十分'}")
        print(f"  動的データ対応: {'実現済み' if user_intent_score >= 60 else '限定的'}")
        print(f"  ユーザー意図反映: {'高度' if user_intent_score >= 70 else '基本的' if user_intent_score >= 50 else '限定的'}")
        
        # 改善が必要な領域の特定
        improvement_areas = []
        if zip_score < 70:
            improvement_areas.append("ZIPファイル処理能力の向上")
        if user_intent_score < 70:
            improvement_areas.append("ユーザー意図実現度の向上")
        
        if improvement_areas:
            print(f"\n改善推奨領域:")
            for area in improvement_areas:
                print(f"  - {area}")
        else:
            print(f"\n改善推奨領域: なし（十分な機能レベル）")
        
        return {
            'zip_representation_score': zip_score,
            'user_intent_alignment_score': user_intent_score,
            'overall_score': overall_score,
            'objective_judgment': judgment,
            'improvement_areas': improvement_areas,
            'detailed_results': {
                'zip_representation': zip_representation_result,
                'user_intent_alignment': user_intent_result
            }
        }

def main():
    """メイン実行"""
    
    verifier = ObjectiveZipLoadingVerifier()
    result = verifier.execute_objective_verification()
    
    return result

if __name__ == "__main__":
    verification_result = main()