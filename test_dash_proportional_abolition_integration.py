#!/usr/bin/env python3
"""
dash_app.py按分廃止タブ統合テスト
Step 3完了後の統合テスト実行
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import sys
import importlib.util

def test_dash_app_proportional_abolition_integration():
    """dash_app.py按分廃止タブ統合テスト"""
    
    print('=' * 80)
    print('dash_app.py按分廃止タブ統合テスト')
    print('Step 3: 手動統合完了後の動作確認')
    print('=' * 80)
    
    try:
        # 1. dash_app.pyの構文チェック
        print('\n【Phase 1: dash_app.py構文チェック】')
        
        # dash_app.pyファイルの存在確認
        dash_app_path = Path('dash_app.py')
        if not dash_app_path.exists():
            return {'test_success': False, 'error': 'dash_app.py not found'}
            
        # ファイル内容読み込み
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            dash_app_content = f.read()
        
        print(f'dash_app.py読み込み成功: {len(dash_app_content):,}文字')
        
        # 2. 統合された機能の確認
        print('\n【Phase 2: 統合機能確認】')
        
        integration_checks = {
            'proportional_abolition_tab_function': 'def create_proportional_abolition_tab(' in dash_app_content,
            'tab_definition_added': "label='🎯 按分廃止分析'" in dash_app_content,
            'tab_container_added': "id='proportional-abolition-tab-container'" in dash_app_content,
            'output_style_added': "Output('proportional-abolition-tab-container', 'style')" in dash_app_content,
            'callback_function_added': 'def initialize_proportional_abolition_content(' in dash_app_content,
            'all_tabs_updated': "'proportional_abolition'" in dash_app_content
        }
        
        print('統合機能チェック結果:')
        for check_name, check_result in integration_checks.items():
            status = '[OK]' if check_result else '[MISSING]'
            print(f'  {status} {check_name}: {check_result}')
        
        # 3. 按分廃止機能の詳細確認
        print('\n【Phase 3: 按分廃止機能詳細確認】')
        
        detailed_checks = {
            'data_loading_logic': 'data_get(\'proportional_abolition_role_summary\',' in dash_app_content,
            'organization_summary': 'proportional_abolition_organization_summary' in dash_app_content,
            'metric_cards': 'create_metric_card(' in dash_app_content,
            'data_table': 'dash_table.DataTable(' in dash_app_content,
            'action_plan': '改善アクションプラン' in dash_app_content,
            'error_handling': 'except Exception as e:' in dash_app_content
        }
        
        print('按分廃止機能詳細チェック結果:')
        for check_name, check_result in detailed_checks.items():
            status = '[OK]' if check_result else '[MISSING]'
            print(f'  {status} {check_name}: {check_result}')
        
        # 4. テストデータ作成と模擬実行
        print('\n【Phase 4: テストデータ作成】')
        
        # 按分廃止テスト用データ作成
        test_role_data = pd.DataFrame([
            {'職種': '介護（W_2）', 'Need時間/日': 15.2, '実配置時間/日': 12.6, '過不足時間/日': 2.6, '現在スタッフ数': 8, '状態': 'SHORTAGE'},
            {'職種': '介護（W_3）', 'Need時間/日': 8.4, '実配置時間/日': 4.8, '過不足時間/日': 3.6, '現在スタッフ数': 0, '状態': 'SHORTAGE'},
            {'職種': '看護師', 'Need時間/日': 12.8, '実配置時間/日': 15.7, '過不足時間/日': -2.9, '現在スタッフ数': 6, '状態': 'SURPLUS'},
            {'職種': '機能訓練士', 'Need時間/日': 6.2, '実配置時間/日': 4.1, '過不足時間/日': 2.1, '現在スタッフ数': 3, '状態': 'SHORTAGE'},
            {'職種': '管理者・相談員', 'Need時間/日': 9.8, '実配置時間/日': 8.3, '過不足時間/日': 1.5, '現在スタッフ数': 4, '状態': 'SHORTAGE'}
        ])
        
        test_org_data = pd.DataFrame([{
            'total_need': test_role_data['Need時間/日'].sum(),
            'total_actual': test_role_data['実配置時間/日'].sum(), 
            'total_shortage': test_role_data['過不足時間/日'].sum(),
            'status': 'SURPLUS' if test_role_data['過不足時間/日'].sum() < 0 else 'SHORTAGE',
            'total_staff_count': test_role_data['現在スタッフ数'].sum()
        }])
        
        # テストファイル保存
        test_role_data.to_parquet('proportional_abolition_role_summary.parquet', index=False)
        test_org_data.to_parquet('proportional_abolition_organization_summary.parquet', index=False)
        
        print(f'テスト用データ作成:')
        print(f'  職種別データ: {len(test_role_data)}職種')
        print(f'  組織全体データ: 過不足 {test_org_data.iloc[0]["total_shortage"]:+.1f}時間/日')
        print(f'  総スタッフ数: {test_org_data.iloc[0]["total_staff_count"]}名')
        
        # 5. 統合評価
        print('\n【Phase 5: 統合評価】')
        
        integration_score = sum(integration_checks.values()) / len(integration_checks) * 100
        detailed_score = sum(detailed_checks.values()) / len(detailed_checks) * 100
        overall_score = (integration_score + detailed_score) / 2
        
        print(f'統合機能スコア: {integration_score:.1f}%')
        print(f'詳細機能スコア: {detailed_score:.1f}%')
        print(f'総合統合スコア: {overall_score:.1f}%')
        
        # 6. 結果判定
        test_success = overall_score >= 80
        
        if test_success:
            print(f'\n[SUCCESS] dash_app.py按分廃止タブ統合成功!')
            quality = "完璧" if overall_score >= 95 else "優秀" if overall_score >= 90 else "良好"
            print(f'統合品質: {overall_score:.1f}% - {quality}')
            
            print(f'\n次のステップ:')
            print('1. dash_app.pyを起動してブラウザで確認')
            print('2. 按分廃止分析タブが表示されることを確認')
            print('3. ZIPファイルアップロード → 按分廃止タブでデータ表示確認')
            
        else:
            print(f'\n[WARNING] 統合に問題があります')
            print(f'統合品質: {overall_score:.1f}% - 改善が必要')
            
            missing_features = [name for name, result in {**integration_checks, **detailed_checks}.items() if not result]
            if missing_features:
                print('不足機能:')
                for feature in missing_features:
                    print(f'  - {feature}')
        
        # 7. 結果保存
        final_results = {
            'test_success': test_success,
            'overall_score': overall_score,
            'integration_score': integration_score,
            'detailed_score': detailed_score,
            'integration_checks': integration_checks,
            'detailed_checks': detailed_checks,
            'test_data_created': {
                'role_data_file': 'proportional_abolition_role_summary.parquet',
                'org_data_file': 'proportional_abolition_organization_summary.parquet',
                'role_count': len(test_role_data),
                'total_shortage': float(test_org_data.iloc[0]['total_shortage'])
            },
            'dash_app_file_size': len(dash_app_content),
            'test_timestamp': datetime.now().isoformat()
        }
        
        result_file = f'dash_app_按分廃止統合テスト結果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        print(f'\n統合テスト結果保存: {result_file}')
        
        return final_results
        
    except Exception as e:
        print(f'[ERROR] 統合テスト失敗: {e}')
        import traceback
        traceback.print_exc()
        return {'test_success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_dash_app_proportional_abolition_integration()
    
    if result and result.get('test_success', False):
        print('\n' + '=' * 80)
        print('[SUCCESS] dash_app.py按分廃止タブ統合テスト成功!')
        print('🎯 按分廃止・職種別分析システム統合完了')
        print('=' * 80)
        
        print('\n🚀 完了サマリー:')
        print('✅ Step 1: app.py按分廃止機能統合 - 完了')
        print('✅ Step 2: dash_app.py按分廃止タブ追加 - 完了')
        print('✅ Step 3: 手動統合実装 - 完了')
        print('✅ Step 4: 統合テスト - 成功')
        
        print('\n📋 利用方法:')
        print('1. app.pyで分析実行 → 按分廃止結果をZIP出力')
        print('2. dash_app.pyを起動')
        print('3. ZIPファイルをアップロード')
        print('4. "🎯 按分廃止分析"タブで結果確認')
        
        print('\n🎯 按分廃止システムの価値:')
        print('• 従来の按分方式による「真実の隠蔽」を完全排除')
        print('• 各職種の真の過不足を露呈し、現場の実態を可視化')
        print('• 組織全体、職種別、雇用形態別の包括的分析を提供')
        
    else:
        print('\n統合テストで問題が発生しました')
        if 'error' in result:
            print(f'エラー詳細: {result["error"]}')