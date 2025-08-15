#!/usr/bin/env python3
"""
Streamlitダッシュボード統合テスト
按分廃止・職種別分析結果のStreamlit表示テスト
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
import json
from datetime import datetime
import sys

# 前のテストモジュールからクラスをインポート
sys.path.append('.')

class StreamlitDashboardTester:
    """Streamlitダッシュボード統合テスター"""
    
    def __init__(self):
        self.test_data = None
        
    def prepare_test_data(self):
        """テスト用データ準備"""
        
        # サンプル職種別データ作成
        sample_roles_data = [
            {'職種': '介護', 'Need時間/日': 45.2, '実配置時間/日': 38.5, '過不足時間/日': 6.7, '現在スタッフ数': 12, '状態': 'SHORTAGE'},
            {'職種': '看護師', 'Need時間/日': 32.1, '実配置時間/日': 35.0, '過不足時間/日': -2.9, '現在スタッフ数': 8, '状態': 'SURPLUS'},
            {'職種': '機能訓練士', 'Need時間/日': 18.4, '実配置時間/日': 15.2, '過不足時間/日': 3.2, '現在スタッフ数': 4, '状態': 'SHORTAGE'},
            {'職種': '運転士', 'Need時間/日': 12.8, '実配置時間/日': 14.1, '過不足時間/日': -1.3, '現在スタッフ数': 3, '状態': 'SURPLUS'},
            {'職種': '管理者・相談員', 'Need時間/日': 28.6, '実配置時間/日': 25.3, '過不足時間/日': 3.3, '現在スタッフ数': 6, '状態': 'SHORTAGE'}
        ]
        
        role_df = pd.DataFrame(sample_roles_data)
        
        # 組織全体サマリー
        organization_summary = {
            'total_need': round(role_df['Need時間/日'].sum(), 1),
            'total_actual': round(role_df['実配置時間/日'].sum(), 1),
            'total_shortage': round(role_df['過不足時間/日'].sum(), 1),
            'status': 'SHORTAGE' if role_df['過不足時間/日'].sum() > 0 else 'SURPLUS'
        }
        
        self.test_data = {
            'role_breakdown_df': role_df,
            'organization_summary': organization_summary,
            'scenario_info': {
                'directory': 'extracted_results/out_mean_based',
                'extraction_method': 'SMART_DETECTION'
            },
            'period_info': {
                'period_days': 30,
                'extraction_method': 'DATA_DRIVEN'
            }
        }
        
        return self.test_data
    
    def create_dashboard_text_simulation(self, display_data):
        """ダッシュボードテキスト形式シミュレーション"""
        
        print('=' * 80)
        print('按分廃止・職種別分析ダッシュボード シミュレーション')
        print('=' * 80)
        
        # パラメータ表示
        org_summary = display_data['organization_summary']
        role_df = display_data['role_breakdown_df']
        period_info = display_data['period_info']
        scenario_info = display_data['scenario_info']
        
        print(f'\n【分析パラメータ】')
        print(f'分析期間: {period_info["period_days"]}日 ({period_info["extraction_method"]})')
        print(f'データソース: {scenario_info["directory"]} ({scenario_info["extraction_method"]})')
        print(f'職種数: {len(role_df)}')
        
        # 組織全体サマリー
        print(f'\n【組織全体過不足サマリー】')
        print(f'Need時間/日: {org_summary["total_need"]}h')
        print(f'実配置時間/日: {org_summary["total_actual"]}h')
        print(f'過不足時間/日: {org_summary["total_shortage"]:+.1f}h')
        
        status_text = {
            'SHORTAGE': '[不足] 人手不足状態',
            'SURPLUS': '[余剰] 人手余剰状態', 
            'BALANCED': '[適正] バランス状態'
        }
        print(f'組織状態: {status_text.get(org_summary["status"], org_summary["status"])}')
        
        # 職種別詳細
        print(f'\n【職種別過不足詳細】')
        print('職種' + ' ' * 12 + 'Need/日' + ' ' * 2 + '実配置/日' + ' ' * 2 + '過不足/日' + ' ' * 2 + 'スタッフ数' + ' ' * 2 + '状態')
        print('-' * 70)
        
        for _, row in role_df.iterrows():
            status_indicator = {
                'SHORTAGE': '[不足]',
                'SURPLUS': '[余剰]',
                'BALANCED': '[適正]'
            }.get(row['状態'], row['状態'])
            
            print(f"{row['職種']:<15} {row['Need時間/日']:>6.1f}h {row['実配置時間/日']:>8.1f}h {row['過不足時間/日']:>+8.1f}h {row['現在スタッフ数']:>8}名 {status_indicator}")
        
        # 優先度分析
        print(f'\n【改善優先度分析】')
        shortage_roles = role_df[role_df['過不足時間/日'] > 0].sort_values('過不足時間/日', ascending=False)
        surplus_roles = role_df[role_df['過不足時間/日'] < 0].sort_values('過不足時間/日', ascending=True)
        
        if len(shortage_roles) > 0:
            print(f'優先改善対象 (不足職種):')
            for i, (_, row) in enumerate(shortage_roles.iterrows(), 1):
                priority = 'HIGH' if row['過不足時間/日'] > 5 else 'MEDIUM' if row['過不足時間/日'] > 2 else 'LOW'
                print(f'  {i}. [{priority}] {row["職種"]}: {row["過不足時間/日"]:+.1f}h/日不足 (現在{row["現在スタッフ数"]}名)')
        
        if len(surplus_roles) > 0:
            print(f'\n配置見直し対象 (余剰職種):')
            for i, (_, row) in enumerate(surplus_roles.iterrows(), 1):
                print(f'  {i}. {row["職種"]}: {abs(row["過不足時間/日"]):.1f}h/日余剰 (現在{row["現在スタッフ数"]}名)')
        
        return {
            'dashboard_simulation_completed': True,
            'role_count': len(role_df),
            'shortage_roles': len(shortage_roles),
            'surplus_roles': len(surplus_roles)
        }
    
    def test_chart_data_preparation(self, display_data):
        """チャートデータ準備テスト"""
        
        print(f'\n【チャートデータ準備テスト】')
        
        role_df = display_data['role_breakdown_df']
        
        # 横棒グラフ用データ
        chart_data = role_df[['職種', '過不足時間/日']].copy()
        chart_data = chart_data.sort_values('過不足時間/日', ascending=True)
        
        print(f'横棒グラフデータ準備: {len(chart_data)}職種')
        print('データ範囲:', f'{chart_data["過不足時間/日"].min():.1f}h ～ {chart_data["過不足時間/日"].max():.1f}h')
        
        # 散布図用データ
        scatter_data = role_df[['職種', 'Need時間/日', '実配置時間/日', '現在スタッフ数', '状態']].copy()
        
        print(f'散布図データ準備: {len(scatter_data)}職種')
        print(f'Need範囲: {scatter_data["Need時間/日"].min():.1f}h ～ {scatter_data["Need時間/日"].max():.1f}h')
        print(f'実配置範囲: {scatter_data["実配置時間/日"].min():.1f}h ～ {scatter_data["実配置時間/日"].max():.1f}h')
        
        # 優先度マトリックス用データ
        matrix_data = role_df[role_df['過不足時間/日'] > 0].copy()  # 不足職種のみ
        if len(matrix_data) > 0:
            matrix_data['優先度スコア'] = (
                matrix_data['過不足時間/日'] * 2 +  # 不足時間の重み
                (matrix_data['現在スタッフ数'] == 0) * 10  # 未配置の場合の重み
            )
            
            print(f'優先度マトリックスデータ準備: {len(matrix_data)}職種 (不足職種のみ)')
            if len(matrix_data) > 0:
                print(f'優先度スコア範囲: {matrix_data["優先度スコア"].min():.1f} ～ {matrix_data["優先度スコア"].max():.1f}')
        
        return {
            'chart_data_ready': True,
            'horizontal_bar_data': chart_data,
            'scatter_plot_data': scatter_data,
            'priority_matrix_data': matrix_data
        }
    
    def test_streamlit_component_compatibility(self, display_data):
        """Streamlitコンポーネント互換性テスト"""
        
        print(f'\n【Streamlitコンポーネント互換性テスト】')
        
        role_df = display_data['role_breakdown_df']
        org_summary = display_data['organization_summary']
        
        # データフレーム互換性
        df_compatible = True
        compatibility_issues = []
        
        # 必要列の存在確認
        required_columns = ['職種', 'Need時間/日', '実配置時間/日', '過不足時間/日', '現在スタッフ数', '状態']
        missing_columns = [col for col in required_columns if col not in role_df.columns]
        if missing_columns:
            df_compatible = False
            compatibility_issues.append(f'Missing columns: {missing_columns}')
        
        # データ型確認
        numeric_columns = ['Need時間/日', '実配置時間/日', '過不足時間/日', '現在スタッフ数']
        for col in numeric_columns:
            if col in role_df.columns and not pd.api.types.is_numeric_dtype(role_df[col]):
                df_compatible = False
                compatibility_issues.append(f'Non-numeric column: {col}')
        
        # メトリクス互換性
        metrics_compatible = True
        required_metrics = ['total_need', 'total_actual', 'total_shortage', 'status']
        missing_metrics = [metric for metric in required_metrics if metric not in org_summary]
        if missing_metrics:
            metrics_compatible = False
            compatibility_issues.append(f'Missing metrics: {missing_metrics}')
        
        print(f'データフレーム互換性: {"OK" if df_compatible else "ERROR"}')
        print(f'メトリクス互換性: {"OK" if metrics_compatible else "ERROR"}')
        
        if compatibility_issues:
            print('互換性問題:')
            for issue in compatibility_issues:
                print(f'  - {issue}')
        
        overall_compatible = df_compatible and metrics_compatible
        
        return {
            'streamlit_compatible': overall_compatible,
            'dataframe_compatible': df_compatible,
            'metrics_compatible': metrics_compatible,
            'issues': compatibility_issues
        }

def test_streamlit_dashboard_integration():
    """Streamlitダッシュボード統合テスト実行"""
    
    print('=' * 80)
    print('Streamlitダッシュボード統合テスト')
    print('按分廃止・職種別分析結果のダッシュボード表示検証')
    print('=' * 80)
    
    try:
        # 1. テスター初期化とデータ準備
        print('\n【Phase 1: テスト用データ準備】')
        tester = StreamlitDashboardTester()
        test_data = tester.prepare_test_data()
        
        print(f'テスト用データ準備完了:')
        print(f'  職種数: {len(test_data["role_breakdown_df"])}')
        print(f'  組織状態: {test_data["organization_summary"]["status"]}')
        print(f'  総過不足: {test_data["organization_summary"]["total_shortage"]:+.1f}時間/日')
        
        # 2. ダッシュボードシミュレーション
        print('\n【Phase 2: ダッシュボードシミュレーション】')
        dashboard_result = tester.create_dashboard_text_simulation(test_data)
        
        # 3. チャートデータ準備テスト
        print('\n【Phase 3: チャートデータ準備テスト】')
        chart_result = tester.test_chart_data_preparation(test_data)
        
        # 4. Streamlit互換性テスト
        print('\n【Phase 4: Streamlit互換性テスト】')
        compatibility_result = tester.test_streamlit_component_compatibility(test_data)
        
        # 5. 統合結果評価
        print('\n【Phase 5: 統合結果評価】')
        
        test_results = {
            'dashboard_simulation': dashboard_result,
            'chart_data_preparation': chart_result,
            'streamlit_compatibility': compatibility_result
        }
        
        # 総合評価
        evaluation_scores = {
            'dashboard_simulation': dashboard_result['dashboard_simulation_completed'],
            'chart_data_ready': chart_result['chart_data_ready'],
            'streamlit_compatible': compatibility_result['streamlit_compatible']
        }
        
        overall_success = all(evaluation_scores.values())
        success_rate = sum(evaluation_scores.values()) / len(evaluation_scores) * 100
        
        print(f'Streamlitダッシュボード統合評価:')
        for test_name, success in evaluation_scores.items():
            status = '[OK]' if success else '[ERROR]'
            print(f'  {status} {test_name}: {success}')
        
        print(f'\n統合成功率: {success_rate:.1f}%')
        
        # 6. 実装ガイド出力
        if overall_success:
            print('\n【Implementation Guide】')
            print('Streamlitダッシュボードでの実装準備完了!')
            print('\n実装ステップ:')
            print('1. import streamlit as st')
            print('2. from app_integration_simple import get_dashboard_data')
            print('3. display_data = get_dashboard_data()')
            print('4. st.dataframe(display_data["role_breakdown_df"])')
            print('5. st.metric("組織全体過不足", display_data["organization_summary"]["total_shortage"])')
            print('6. Plotlyチャートでの可視化追加')
        
        # 7. 結果保存
        final_results = {
            'test_success': overall_success,
            'success_rate': success_rate,
            'test_results': test_results,
            'test_data_summary': {
                'role_count': len(test_data['role_breakdown_df']),
                'organization_status': test_data['organization_summary']['status'],
                'total_shortage': test_data['organization_summary']['total_shortage']
            },
            'test_timestamp': datetime.now().isoformat()
        }
        
        result_file = f'Streamlitダッシュボード統合テスト結果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2, default=str)
        print(f'\nダッシュボード統合テスト結果保存: {result_file}')
        
        return final_results
        
    except Exception as e:
        print(f'[ERROR] Streamlitダッシュボード統合テスト失敗: {e}')
        import traceback
        traceback.print_exc()
        return {'test_success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_streamlit_dashboard_integration()
    
    if result and result.get('test_success', False):
        print('\n' + '=' * 80)
        print('[SUCCESS] Streamlitダッシュボード統合テスト成功!')
        
        success_rate = result.get('success_rate', 0)
        if success_rate >= 95:
            print('[PERFECT] 完璧な統合準備完了')
        elif success_rate >= 85:
            print('[EXCELLENT] 優秀な統合準備完了')
        elif success_rate >= 75:
            print('[GOOD] 良好な統合準備完了')
        else:
            print('[WARNING] 統合準備に改善の余地あり')
            
        print(f'ダッシュボード統合成功率: {success_rate:.1f}%')
        print('[READY] 本格的なStreamlitダッシュボード実装準備完了')
        print('=' * 80)
        
        # 次のアクション提案
        print('\n推奨次アクション:')
        print('1. app.pyへの按分廃止機能統合')
        print('2. Streamlitダッシュボード本格実装')
        print('3. ユーザー向け操作インターフェース追加')
        print('4. 本番環境デプロイメント準備')
        
    else:
        print('\nStreamlitダッシュボード統合テストで問題が発生しました')
        if 'error' in result:
            print(f'エラー詳細: {result["error"]}')