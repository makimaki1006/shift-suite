#!/usr/bin/env python3
"""
app.py統合インターフェースモジュール作成
按分廃止・職種別分析システムとStreamlitアプリの統合
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, datetime, timedelta
import json
import sys
import re
sys.path.append('.')

def create_app_interface_integration_module():
    """app.py統合インターフェースモジュール作成実行"""
    
    print('=' * 80)
    print('app.py統合インターフェースモジュール作成')
    print('目的: 按分廃止・職種別分析システムとStreamlitアプリの統合')
    print('機能: 動的パラメータ取得、結果表示、ダッシュボード統合')
    print('=' * 80)
    
    try:
        # 1. app.pyからのパラメータ抽出機能作成
        print('\n【Phase 1: app.pyパラメータ抽出機能作成】')
        param_extractor = create_app_parameter_extractor()
        print_parameter_extractor_status(param_extractor)
        
        # 2. 動的Need算出統合クラス作成
        print('\n【Phase 2: 動的Need算出統合クラス作成】')
        integration_class = create_dynamic_need_integration_class()
        print_integration_class_status(integration_class)
        
        # 3. Streamlit表示コンポーネント作成
        print('\n【Phase 3: Streamlit表示コンポーネント作成】')
        display_components = create_streamlit_display_components()
        print_display_components_status(display_components)
        
        # 4. 統合テスト関数作成
        print('\n【Phase 4: 統合テスト関数作成】')
        test_functions = create_integration_test_functions()
        print_test_functions_status(test_functions)
        
        # 5. メインインターフェースモジュール保存
        print('\n【Phase 5: メインインターフェースモジュール保存】')
        module_files = save_app_interface_module(
            param_extractor, integration_class, display_components, test_functions
        )
        print_module_save_status(module_files)
        
        return {
            'success': True,
            'param_extractor': param_extractor,
            'integration_class': integration_class,
            'display_components': display_components,
            'test_functions': test_functions,
            'module_files': module_files
        }
        
    except Exception as e:
        print(f'[ERROR] app.py統合インターフェースモジュール作成失敗: {e}')
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def create_app_parameter_extractor():
    """app.pyパラメータ抽出機能作成"""
    
    print('app.pyパラメータ抽出機能作成中...')
    
    extractor_code = '''
class AppParameterExtractor:
    """app.pyからの動的パラメータ抽出クラス"""
    
    def __init__(self, app_file_path='app.py'):
        self.app_file_path = Path(app_file_path)
        
    def extract_period_parameters(self):
        """期間パラメータ抽出"""
        
        try:
            with open(self.app_file_path, 'r', encoding='utf-8') as f:
                app_content = f.read()
            
            # need_ref_start_date_widget と need_ref_end_date_widget の検索
            period_params = {}
            
            # 開始日パターン検索
            start_date_patterns = [
                r'need_ref_start_date_widget.*?=.*?([\'"].*?[\'"])',
                r'need_ref_start_date.*?=.*?([\'"].*?[\'"])',
                r'start.*?date.*?=.*?([\'"].*?[\'"])',
            ]
            
            # 終了日パターン検索
            end_date_patterns = [
                r'need_ref_end_date_widget.*?=.*?([\'"].*?[\'"])',
                r'need_ref_end_date.*?=.*?([\'"].*?[\'"])',
                r'end.*?date.*?=.*?([\'"].*?[\'"])',
            ]
            
            # デフォルト値設定
            period_params = {
                'start_date': None,
                'end_date': None,
                'period_days': 30,  # デフォルト
                'extraction_method': 'DEFAULT'
            }
            
            # パターンマッチング実行
            for pattern in start_date_patterns:
                match = re.search(pattern, app_content, re.IGNORECASE | re.DOTALL)
                if match:
                    period_params['start_date'] = match.group(1).strip('\'"')
                    period_params['extraction_method'] = 'REGEX_EXTRACTED'
                    break
            
            for pattern in end_date_patterns:
                match = re.search(pattern, app_content, re.IGNORECASE | re.DOTALL)
                if match:
                    period_params['end_date'] = match.group(1).strip('\'"')
                    period_params['extraction_method'] = 'REGEX_EXTRACTED'
                    break
            
            # 期間日数計算
            if period_params['start_date'] and period_params['end_date']:
                try:
                    start_dt = pd.to_datetime(period_params['start_date'])
                    end_dt = pd.to_datetime(period_params['end_date'])
                    period_params['period_days'] = (end_dt - start_dt).days + 1
                except Exception as e:
                    print(f'[WARNING] 日付解析失敗: {e}')
                    period_params['period_days'] = 30
            
            return period_params
            
        except Exception as e:
            print(f'[WARNING] app.pyパラメータ抽出失敗: {e}')
            return {
                'start_date': None,
                'end_date': None,
                'period_days': 30,
                'extraction_method': 'ERROR_FALLBACK'
            }
    
    def extract_scenario_directory(self):
        """シナリオディレクトリ抽出"""
        
        try:
            with open(self.app_file_path, 'r', encoding='utf-8') as f:
                app_content = f.read()
            
            # シナリオディレクトリパターン検索
            directory_patterns = [
                r'extracted_results[/\\\\]([^/\\\\\'\"\\s]+)',
                r'scenario.*?dir.*?=.*?[\'"]([^\'\"]+)[\'"]',
                r'out_[a-zA-Z0-9_]+',
            ]
            
            scenario_info = {
                'directory': 'extracted_results/out_p25_based',  # デフォルト
                'extraction_method': 'DEFAULT'
            }
            
            for pattern in directory_patterns:
                matches = re.findall(pattern, app_content, re.IGNORECASE)
                if matches:
                    scenario_info['directory'] = f'extracted_results/{matches[-1]}'
                    scenario_info['extraction_method'] = 'REGEX_EXTRACTED'
                    break
            
            return scenario_info
            
        except Exception as e:
            print(f'[WARNING] シナリオディレクトリ抽出失敗: {e}')
            return {
                'directory': 'extracted_results/out_p25_based',
                'extraction_method': 'ERROR_FALLBACK'
            }
    
    def extract_all_parameters(self):
        """全パラメータ統合抽出"""
        
        period_params = self.extract_period_parameters()
        scenario_info = self.extract_scenario_directory()
        
        return {
            'period': period_params,
            'scenario': scenario_info,
            'extraction_timestamp': datetime.now().isoformat(),
            'app_file_path': str(self.app_file_path)
        }
'''
    
    return {
        'extractor_class': extractor_code,
        'functions_count': 4,
        'capabilities': [
            'period_parameters_extraction',
            'scenario_directory_extraction',
            'regex_pattern_matching',
            'fallback_default_handling'
        ]
    }

def create_dynamic_need_integration_class():
    """動的Need算出統合クラス作成"""
    
    print('動的Need算出統合クラス作成中...')
    
    integration_code = '''
class DynamicNeedCalculationIntegration:
    """動的Need算出統合クラス - app.py統合専用"""
    
    def __init__(self, app_file_path='app.py'):
        self.param_extractor = AppParameterExtractor(app_file_path)
        self.calculation_results = {}
        
    def execute_integrated_calculation(self):
        """統合計算実行"""
        
        print('app.py統合Need算出実行中...')
        
        # 1. app.pyからパラメータ抽出
        app_params = self.param_extractor.extract_all_parameters()
        print(f'抽出パラメータ: 期間{app_params["period"]["period_days"]}日')
        
        # 2. シナリオディレクトリ設定
        scenario_dir = Path(app_params['scenario']['directory'])
        if not scenario_dir.exists():
            raise FileNotFoundError(f'シナリオディレクトリが存在しません: {scenario_dir}')
        
        # 3. データ読み込み
        data_package = self.load_dynamic_data(scenario_dir, app_params['period']['period_days'])
        
        # 4. Need算出実行
        calculation_results = self.execute_proportional_abolition_calculation(
            data_package, app_params['period']['period_days']
        )
        
        # 5. 結果統合
        integrated_results = {
            'app_parameters': app_params,
            'data_metadata': data_package['metadata'],
            'calculation_results': calculation_results,
            'integration_timestamp': datetime.now().isoformat()
        }
        
        self.calculation_results = integrated_results
        return integrated_results
    
    def load_dynamic_data(self, scenario_dir, period_days):
        """動的データ読み込み"""
        
        # intermediate_data読み込み
        intermediate_data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        operating_data = intermediate_data[intermediate_data['role'] != 'NIGHT_SLOT']
        
        # Need値動的読み込み（複数パターン対応）
        need_files_patterns = [
            'need_per_date_slot_role_*.parquet',
            'need_*_role_*.parquet',
            'need_*.parquet'
        ]
        
        need_files = []
        for pattern in need_files_patterns:
            found_files = list(scenario_dir.glob(pattern))
            if found_files:
                need_files = found_files
                break
        
        if not need_files:
            raise FileNotFoundError(f'Needファイルが見つかりません: {scenario_dir}')
        
        # Need値処理
        need_data = {}
        for need_file in need_files:
            role_name = self.extract_role_name_from_filename(need_file.name)
            df = pd.read_parquet(need_file)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            total_need = df[numeric_cols].sum().sum()
            
            need_data[role_name] = {
                'file_path': need_file,
                'total_need_value': total_need,
                'need_hours_total': total_need * 0.5,  # UNIFIED_SLOT_HOURS
                'need_hours_daily': (total_need * 0.5) / period_days  # 動的期間対応
            }
        
        return {
            'intermediate_data': intermediate_data,
            'operating_data': operating_data,
            'need_data': need_data,
            'metadata': {
                'total_records': len(operating_data),
                'period_days': period_days,  # 動的期間
                'unique_roles': operating_data['role'].nunique(),
                'unique_staff': operating_data['staff'].nunique(),
                'need_files_count': len(need_files),
                'total_need_hours': sum(data['need_hours_total'] for data in need_data.values())
            }
        }
    
    def extract_role_name_from_filename(self, filename):
        """ファイル名から職種名抽出"""
        
        # パターン1: need_per_date_slot_role_職種名.parquet
        if 'need_per_date_slot_role_' in filename:
            return filename.replace('need_per_date_slot_role_', '').replace('.parquet', '')
        
        # パターン2: need_職種名_role_*.parquet
        match = re.search(r'need_([^_]+)_role', filename)
        if match:
            return match.group(1)
        
        # パターン3: need_職種名.parquet
        if filename.startswith('need_'):
            return filename.replace('need_', '').replace('.parquet', '')
        
        # フォールバック
        return filename.replace('.parquet', '')
    
    def execute_proportional_abolition_calculation(self, data_package, period_days):
        """按分廃止計算実行"""
        
        operating_data = data_package['operating_data']
        need_data = data_package['need_data']
        
        # 職種別実配置時間計算
        role_actual_allocation = {}
        for role in operating_data['role'].unique():
            role_data = operating_data[operating_data['role'] == role]
            role_records = len(role_data)
            role_hours_total = role_records * 0.5
            role_hours_daily = role_hours_total / period_days  # 動的期間対応
            
            role_actual_allocation[role] = {
                'records': role_records,
                'hours_total': role_hours_total,
                'hours_daily': role_hours_daily,
                'staff_count': role_data['staff'].nunique()
            }
        
        # 職種別過不足算出
        role_shortages = {}
        for role_name, need_info in need_data.items():
            need_hours_daily = need_info['need_hours_daily']
            actual_info = role_actual_allocation.get(role_name, {
                'hours_daily': 0, 'staff_count': 0
            })
            actual_hours_daily = actual_info['hours_daily']
            shortage_daily = need_hours_daily - actual_hours_daily
            
            role_shortages[role_name] = {
                'role': role_name,
                'need_hours_daily': need_hours_daily,
                'actual_hours_daily': actual_hours_daily,
                'shortage_daily': shortage_daily,
                'shortage_status': 'SHORTAGE' if shortage_daily > 0 else 'SURPLUS' if shortage_daily < 0 else 'BALANCED',
                'staff_count_current': actual_info['staff_count']
            }
        
        # 組織全体過不足算出
        total_need_daily = sum(need_info['need_hours_daily'] for need_info in need_data.values())
        total_actual_daily = sum(actual_info['hours_daily'] for actual_info in role_actual_allocation.values())
        total_shortage_daily = total_need_daily - total_actual_daily
        
        return {
            'role_based_results': {
                'role_shortages': role_shortages,
                'shortage_ranking': sorted(role_shortages.values(), key=lambda x: x['shortage_daily'], reverse=True)
            },
            'organization_wide_results': {
                'total_need_daily': total_need_daily,
                'total_actual_daily': total_actual_daily,
                'total_shortage_daily': total_shortage_daily,
                'organization_status': 'SHORTAGE' if total_shortage_daily > 0 else 'SURPLUS' if total_shortage_daily < 0 else 'BALANCED'
            }
        }
    
    def get_streamlit_display_data(self):
        """Streamlit表示用データ取得"""
        
        if not self.calculation_results:
            raise ValueError('計算結果がありません。execute_integrated_calculation()を先に実行してください。')
        
        results = self.calculation_results['calculation_results']
        
        # 職種別データフレーム作成
        role_df = pd.DataFrame([
            {
                '職種': info['role'],
                'Need時間/日': round(info['need_hours_daily'], 1),
                '実配置時間/日': round(info['actual_hours_daily'], 1),
                '過不足時間/日': round(info['shortage_daily'], 1),
                '現在スタッフ数': info['staff_count_current'],
                '状態': info['shortage_status']
            }
            for info in results['role_based_results']['role_shortages'].values()
        ])
        
        # 組織全体データ
        org_data = results['organization_wide_results']
        
        return {
            'role_breakdown_df': role_df,
            'organization_summary': {
                'total_need': round(org_data['total_need_daily'], 1),
                'total_actual': round(org_data['total_actual_daily'], 1),
                'total_shortage': round(org_data['total_shortage_daily'], 1),
                'status': org_data['organization_status']
            },
            'app_parameters': self.calculation_results['app_parameters']
        }
'''
    
    return {
        'integration_class': integration_code,
        'methods_count': 8,
        'capabilities': [
            'app_parameter_integration',
            'dynamic_data_loading',
            'proportional_abolition_calculation',
            'streamlit_data_formatting'
        ]
    }

def create_streamlit_display_components():
    """Streamlit表示コンポーネント作成"""
    
    print('Streamlit表示コンポーネント作成中...')
    
    display_code = '''
def create_proportional_abolition_dashboard(integration_results):
    """按分廃止分析ダッシュボード作成"""
    
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # ページ設定
    st.markdown("## 按分廃止・職種別分析結果")
    
    display_data = integration_results
    org_summary = display_data['organization_summary']
    role_df = display_data['role_breakdown_df']
    app_params = display_data['app_parameters']
    
    # 分析パラメータ表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("分析期間", f"{app_params['period']['period_days']}日")
    with col2:
        st.metric("抽出方法", app_params['period']['extraction_method'])
    with col3:
        st.metric("職種数", len(role_df))
    
    # 組織全体サマリー
    st.markdown("### 組織全体過不足")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Need時間/日", f"{org_summary['total_need']}h")
    with col2:
        st.metric("実配置時間/日", f"{org_summary['total_actual']}h")
    with col3:
        color = "normal" if abs(org_summary['total_shortage']) < 5 else "inverse"
        st.metric("過不足時間/日", f"{org_summary['total_shortage']:+.1f}h", delta_color=color)
    with col4:
        status_color = "🔴" if org_summary['status'] == 'SHORTAGE' else "🟢" if org_summary['status'] == 'SURPLUS' else "🟡"
        st.metric("組織状態", f"{status_color} {org_summary['status']}")
    
    # 職種別詳細
    st.markdown("### 職種別過不足詳細")
    
    # データフレーム表示
    st.dataframe(
        role_df.style.format({
            'Need時間/日': '{:.1f}',
            '実配置時間/日': '{:.1f}',
            '過不足時間/日': '{:+.1f}'
        }).applymap(
            lambda x: 'background-color: #ffebee' if isinstance(x, str) and 'SHORTAGE' in x 
                     else 'background-color: #e8f5e8' if isinstance(x, str) and 'SURPLUS' in x 
                     else '', subset=['状態']
        ),
        use_container_width=True
    )
    
    # 職種別過不足グラフ
    st.markdown("### 職種別過不足視覚化")
    
    # 横棒グラフ
    fig = px.bar(
        role_df.sort_values('過不足時間/日', ascending=True),
        x='過不足時間/日',
        y='職種',
        orientation='h',
        color='過不足時間/日',
        color_continuous_scale=['red', 'white', 'green'],
        color_continuous_midpoint=0,
        title='職種別過不足時間/日',
        labels={'過不足時間/日': '過不足時間 (時間/日)', '職種': '職種'}
    )
    
    fig.update_layout(
        height=max(400, len(role_df) * 30),
        xaxis_title="過不足時間 (時間/日)",
        yaxis_title="職種"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 散布図: Need vs 実配置
    fig_scatter = px.scatter(
        role_df,
        x='Need時間/日',
        y='実配置時間/日',
        size='現在スタッフ数',
        color='状態',
        hover_name='職種',
        title='Need時間 vs 実配置時間',
        labels={
            'Need時間/日': 'Need時間 (時間/日)',
            '実配置時間/日': '実配置時間 (時間/日)'
        }
    )
    
    # 理想線（Need = 実配置）を追加
    max_val = max(role_df['Need時間/日'].max(), role_df['実配置時間/日'].max())
    fig_scatter.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='理想線 (Need = 実配置)'
    ))
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    return {
        'dashboard_created': True,
        'components_count': 4,
        'visualizations': ['metrics', 'dataframe', 'horizontal_bar', 'scatter_plot']
    }

def create_shortage_priority_matrix(role_df):
    """不足優先度マトリックス作成"""
    
    import streamlit as st
    import plotly.express as px
    import numpy as np
    
    st.markdown("### 改善優先度マトリックス")
    
    # 優先度計算
    role_df_copy = role_df.copy()
    role_df_copy['不足時間絶対値'] = role_df_copy['過不足時間/日'].abs()
    role_df_copy['優先度スコア'] = (
        role_df_copy['不足時間絶対値'] * 2 +  # 不足時間の重み
        (role_df_copy['現在スタッフ数'] == 0) * 10  # 未配置の場合の重み
    )
    
    # 優先度分類
    def get_priority_level(row):
        if row['現在スタッフ数'] == 0 and row['過不足時間/日'] > 0:
            return 'IMMEDIATE'
        elif row['過不足時間/日'] > 5:
            return 'HIGH'
        elif row['過不足時間/日'] > 2:
            return 'MEDIUM'
        elif row['過不足時間/日'] > 0:
            return 'LOW'
        else:
            return 'NONE'
    
    role_df_copy['優先度レベル'] = role_df_copy.apply(get_priority_level, axis=1)
    
    # 優先度マトリックス表示
    priority_colors = {
        'IMMEDIATE': '#d32f2f',
        'HIGH': '#f57c00',
        'MEDIUM': '#fbc02d',
        'LOW': '#689f38',
        'NONE': '#455a64'
    }
    
    fig_matrix = px.scatter(
        role_df_copy[role_df_copy['過不足時間/日'] > 0],  # 不足職種のみ
        x='現在スタッフ数',
        y='過不足時間/日',
        color='優先度レベル',
        size='優先度スコア',
        hover_name='職種',
        color_discrete_map=priority_colors,
        title='改善優先度マトリックス (不足職種のみ)',
        labels={
            '現在スタッフ数': '現在スタッフ数 (人)',
            '過不足時間/日': '不足時間 (時間/日)'
        }
    )
    
    st.plotly_chart(fig_matrix, use_container_width=True)
    
    # 優先度別集計
    priority_summary = role_df_copy[role_df_copy['優先度レベル'] != 'NONE'].groupby('優先度レベル').agg({
        '職種': 'count',
        '過不足時間/日': 'sum',
        '現在スタッフ数': 'sum'
    }).rename(columns={'職種': '職種数', '過不足時間/日': '合計不足時間', '現在スタッフ数': '合計スタッフ数'})
    
    st.markdown("#### 優先度別集計")
    st.dataframe(priority_summary, use_container_width=True)
    
    return role_df_copy[['職種', '優先度レベル', '優先度スコア']].sort_values('優先度スコア', ascending=False)
'''
    
    return {
        'display_components': display_code,
        'components_count': 2,
        'features': [
            'dashboard_creation',
            'metrics_display',
            'interactive_charts',
            'priority_matrix',
            'data_formatting'
        ]
    }

def create_integration_test_functions():
    """統合テスト関数作成"""
    
    print('統合テスト関数作成中...')
    
    test_code = '''
def test_app_integration_complete():
    """完全app統合テスト実行"""
    
    print('=' * 60)
    print('完全app統合テスト実行')
    print('=' * 60)
    
    try:
        # 1. パラメータ抽出テスト
        print('\\n【Test 1: パラメータ抽出テスト】')
        param_extractor = AppParameterExtractor('app.py')
        app_params = param_extractor.extract_all_parameters()
        
        print(f'期間抽出: {app_params["period"]["period_days"]}日')
        print(f'抽出方法: {app_params["period"]["extraction_method"]}')
        print(f'シナリオディレクトリ: {app_params["scenario"]["directory"]}')
        
        # 2. 統合計算テスト
        print('\\n【Test 2: 統合計算テスト】')
        integration = DynamicNeedCalculationIntegration('app.py')
        calculation_results = integration.execute_integrated_calculation()
        
        print(f'計算完了: 職種数{len(calculation_results["calculation_results"]["role_based_results"]["role_shortages"])}')
        print(f'組織全体状態: {calculation_results["calculation_results"]["organization_wide_results"]["organization_status"]}')
        
        # 3. Streamlit表示データテスト
        print('\\n【Test 3: Streamlit表示データテスト】')
        display_data = integration.get_streamlit_display_data()
        
        print(f'表示データ準備完了: {len(display_data["role_breakdown_df"])}職種')
        print(f'組織全体不足: {display_data["organization_summary"]["total_shortage"]:+.1f}時間/日')
        
        # 4. 統合成功確認
        print('\\n【Test 4: 統合成功確認】')
        success_checks = [
            len(calculation_results) > 0,
            'calculation_results' in calculation_results,
            len(display_data['role_breakdown_df']) > 0,
            display_data['organization_summary']['status'] in ['SHORTAGE', 'SURPLUS', 'BALANCED']
        ]
        
        all_success = all(success_checks)
        print(f'統合テスト結果: {"SUCCESS" if all_success else "FAILED"}')
        
        return {
            'test_success': all_success,
            'app_params': app_params,
            'calculation_results': calculation_results,
            'display_data': display_data,
            'test_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f'[ERROR] 統合テスト失敗: {e}')
        return {'test_success': False, 'error': str(e)}

def test_dynamic_parameter_extraction():
    """動的パラメータ抽出テスト"""
    
    print('\\n動的パラメータ抽出テスト実行中...')
    
    try:
        extractor = AppParameterExtractor('app.py')
        
        # 期間パラメータテスト
        period_params = extractor.extract_period_parameters()
        print(f'期間パラメータ: {period_params}')
        
        # シナリオディレクトリテスト
        scenario_info = extractor.extract_scenario_directory()
        print(f'シナリオ情報: {scenario_info}')
        
        # 統合パラメータテスト
        all_params = extractor.extract_all_parameters()
        print(f'統合パラメータ抽出成功: {len(all_params)}項目')
        
        return {
            'extraction_success': True,
            'period_params': period_params,
            'scenario_info': scenario_info,
            'all_params': all_params
        }
        
    except Exception as e:
        print(f'[ERROR] パラメータ抽出テスト失敗: {e}')
        return {'extraction_success': False, 'error': str(e)}

def test_streamlit_dashboard_integration():
    """Streamlitダッシュボード統合テスト"""
    
    print('\\nStreamlitダッシュボード統合テスト実行中...')
    
    try:
        # 統合計算実行
        integration = DynamicNeedCalculationIntegration('app.py')
        calculation_results = integration.execute_integrated_calculation()
        display_data = integration.get_streamlit_display_data()
        
        # ダッシュボードコンポーネント準備
        dashboard_ready = True
        components_ready = [
            'role_breakdown_df' in display_data,
            'organization_summary' in display_data,
            len(display_data['role_breakdown_df']) > 0
        ]
        
        dashboard_ready = all(components_ready)
        
        print(f'ダッシュボード準備: {"Ready" if dashboard_ready else "Not Ready"}')
        print(f'表示可能職種数: {len(display_data["role_breakdown_df"])}')
        print(f'組織状態: {display_data["organization_summary"]["status"]}')
        
        return {
            'dashboard_ready': dashboard_ready,
            'display_data': display_data,
            'components_ready': components_ready
        }
        
    except Exception as e:
        print(f'[ERROR] ダッシュボード統合テスト失敗: {e}')
        return {'dashboard_ready': False, 'error': str(e)}
'''
    
    return {
        'test_functions': test_code,
        'functions_count': 3,
        'test_categories': [
            'complete_integration_test',
            'parameter_extraction_test',
            'dashboard_integration_test'
        ]
    }

def save_app_interface_module(param_extractor, integration_class, display_components, test_functions):
    """app統合インターフェースモジュール保存"""
    
    print('app統合インターフェースモジュール保存中...')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # メインモジュールファイル作成
    main_module_content = f'''#!/usr/bin/env python3
"""
app.py統合インターフェースモジュール
按分廃止・職種別分析システム - Streamlitアプリ統合版
Created: {datetime.now().isoformat()}
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, datetime, timedelta
import json
import sys
import re

# 基本クラス定義
{param_extractor['extractor_class']}

{integration_class['integration_class']}

# Streamlit表示コンポーネント
{display_components['display_components']}

# 統合テスト関数
{test_functions['test_functions']}

# メイン実行関数
def execute_app_integration():
    """メインapp統合実行"""
    
    print('=' * 80)
    print('app.py統合Need算出システム実行')
    print('按分廃止・職種別分析 - Streamlit統合版')
    print('=' * 80)
    
    try:
        # 統合テスト実行
        test_result = test_app_integration_complete()
        
        if test_result['test_success']:
            print('\\n[SUCCESS] app統合テスト完了')
            print('システムはStreamlitダッシュボードで使用可能です')
            
            # 結果保存
            result_file = f'app統合結果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(test_result, f, ensure_ascii=False, indent=2, default=str)
            print(f'統合結果保存: {{result_file}}')
            
            return test_result
        else:
            print('\\n[ERROR] app統合テスト失敗')
            return test_result
            
    except Exception as e:
        print(f'[ERROR] app統合実行失敗: {{e}}')
        return {{'success': False, 'error': str(e)}}

if __name__ == "__main__":
    execute_app_integration()
'''
    
    # ファイル保存
    main_module_file = f'app_interface_integration_module_{timestamp}.py'
    with open(main_module_file, 'w', encoding='utf-8') as f:
        f.write(main_module_content)
    
    # 簡易版モジュール作成（import用）
    simple_module_content = f'''#!/usr/bin/env python3
"""
Simple app.py Integration Module for Import
簡易app統合モジュール - インポート用
"""

import sys
sys.path.append('.')

# メインモジュールからインポート
from {main_module_file[:-3]} import (
    AppParameterExtractor,
    DynamicNeedCalculationIntegration,
    create_proportional_abolition_dashboard,
    test_app_integration_complete
)

# 簡易実行関数
def quick_app_integration():
    """クイックapp統合実行"""
    integration = DynamicNeedCalculationIntegration('app.py')
    results = integration.execute_integrated_calculation()
    display_data = integration.get_streamlit_display_data()
    return display_data

# Streamlit統合用関数
def get_dashboard_data():
    """ダッシュボード用データ取得"""
    return quick_app_integration()
'''
    
    simple_module_file = 'app_integration_simple.py'
    with open(simple_module_file, 'w', encoding='utf-8') as f:
        f.write(simple_module_content)
    
    return {
        'main_module_file': main_module_file,
        'simple_module_file': simple_module_file,
        'files_created': [main_module_file, simple_module_file],
        'creation_timestamp': timestamp
    }

def print_parameter_extractor_status(extractor):
    """パラメータ抽出機能状態表示"""
    print(f'パラメータ抽出機能作成完了: {extractor["functions_count"]}関数')
    for capability in extractor['capabilities']:
        print(f'  - {capability}')

def print_integration_class_status(integration):
    """統合クラス状態表示"""
    print(f'統合クラス作成完了: {integration["methods_count"]}メソッド')
    for capability in integration['capabilities']:
        print(f'  - {capability}')

def print_display_components_status(display):
    """表示コンポーネント状態表示"""
    print(f'表示コンポーネント作成完了: {display["components_count"]}コンポーネント')
    for feature in display['features']:
        print(f'  - {feature}')

def print_test_functions_status(test):
    """テスト関数状態表示"""
    print(f'テスト関数作成完了: {test["functions_count"]}関数')
    for category in test['test_categories']:
        print(f'  - {category}')

def print_module_save_status(modules):
    """モジュール保存状態表示"""
    print(f'統合モジュール保存完了: {len(modules["files_created"])}ファイル')
    for file_path in modules['files_created']:
        print(f'  - {file_path}')

if __name__ == "__main__":
    result = create_app_interface_integration_module()
    
    if result and result.get('success', False):
        print('\n' + '=' * 80)
        print('[SUCCESS] app.py統合インターフェースモジュール作成完了')
        print('[READY] Streamlitダッシュボード統合準備完了')
        print('[NEXT] 統合テスト実行またはapp.py組み込み')
        print('=' * 80)
        
        # 使用方法表示
        print('\n使用方法:')
        print('1. 統合テスト実行: python app_interface_integration_module_XXXXXXXX_XXXXXX.py')
        print('2. Streamlitダッシュボード: from app_integration_simple import get_dashboard_data')
        print('3. app.py組み込み: from app_integration_simple import create_proportional_abolition_dashboard')
        
    else:
        print('\napp.py統合インターフェースモジュール作成に問題が発生しました')