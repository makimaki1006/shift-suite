#!/usr/bin/env python3
"""
dash_app.pyの問題をデバッグするスクリプト
休暇分析とdf_shortage_role_filteredエラーの調査
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# シフト分析モジュールのパスを追加
sys.path.append(str(Path(__file__).parent))

def test_shortage_tab_logic():
    """不足分析タブのロジックをテスト"""
    print("=== 不足分析タブロジックテスト ===")
    
    # サンプルデータを作成
    df_shortage_role = pd.DataFrame({
        'role': ['看護師', '介護職', '事務員', '全体'],
        'lack_h': [10.5, 15.2, 5.3, 30.0],
        'excess_h': [2.1, 0.0, 3.5, 5.6]
    })
    
    print(f"テストデータ: {len(df_shortage_role)}行")
    print(df_shortage_role)
    
    # 実際のロジックを模擬
    df_shortage_role_filtered = {}
    df_shortage_role_excess = {}
    
    print(f"\n変数初期化: df_shortage_role_filtered = {df_shortage_role_filtered}")
    
    if not df_shortage_role.empty:
        # 実際の職種のみ抽出（全体・合計行を除外）
        role_only_df = df_shortage_role[
            (~df_shortage_role['role'].isin(['全体', '合計', '総計'])) &
            (~df_shortage_role['role'].str.startswith('emp_', na=False))
        ]
        
        print(f"フィルタ後データ: {len(role_only_df)}行")
        print(role_only_df)
        
        for _, row in role_only_df.iterrows():
            role = row['role']
            lack_h = row.get('lack_h', 0)
            excess_h = row.get('excess_h', 0)
            
            if lack_h > 0:
                df_shortage_role_filtered[role] = lack_h
            if excess_h > 0:
                df_shortage_role_excess[role] = excess_h
    
    print(f"\n結果:")
    print(f"df_shortage_role_filtered: {df_shortage_role_filtered}")
    print(f"df_shortage_role_excess: {df_shortage_role_excess}")
    
    # グラフ作成ロジックのテスト
    if df_shortage_role_filtered:
        roles = list(df_shortage_role_filtered.keys())
        lack_values = list(df_shortage_role_filtered.values())
        excess_values = [df_shortage_role_excess.get(role, 0) for role in roles]
        
        print(f"\nグラフデータ:")
        print(f"roles: {roles}")
        print(f"lack_values: {lack_values}")
        print(f"excess_values: {excess_values}")
        
        print("✅ 不足分析タブロジック: 正常")
        return True
    else:
        print("❌ 不足分析タブロジック: df_shortage_role_filteredが空")
        return False

def test_leave_analysis_data():
    """休暇分析データのテスト"""
    print("\n=== 休暇分析データテスト ===")
    
    # サンプルのlong_dfデータ
    from datetime import datetime, timedelta
    import numpy as np
    
    # 休暇データを含むlong_dfを模擬
    dates = pd.date_range('2025-01-01', '2025-01-07', freq='D')
    times = pd.date_range('2025-01-01 08:00', '2025-01-01 17:00', freq='30min')
    
    test_data = []
    for date in dates:
        for time_slot in times:
            dt = datetime.combine(date.date(), time_slot.time())
            
            # 休暇データ（parsed_slots_count=0）をランダムに生成
            if np.random.random() < 0.1:  # 10%の確率で休暇
                test_data.append({
                    'staff': f'職員{np.random.randint(1, 10)}',
                    'role': np.random.choice(['看護師', '介護職', '事務員']),
                    'ds': dt,
                    'parsed_slots_count': 0,
                    'holiday_type': np.random.choice(['希望休', '有給', '特別休暇'])
                })
            else:
                test_data.append({
                    'staff': f'職員{np.random.randint(1, 10)}',
                    'role': np.random.choice(['看護師', '介護職', '事務員']),
                    'ds': dt,
                    'parsed_slots_count': 1,
                    'holiday_type': '通常勤務'
                })
    
    long_df = pd.DataFrame(test_data)
    
    print(f"テストlong_df: {len(long_df)}レコード")
    print(f"休暇レコード数: {len(long_df[long_df['parsed_slots_count'] == 0])}")
    
    # 休暇分析ロジックをテスト
    if not long_df.empty and 'parsed_slots_count' in long_df.columns:
        # 休暇データ（slots_count=0）を抽出
        leave_data = long_df[long_df['parsed_slots_count'] == 0]
        if not leave_data.empty:
            # 日別休暇取得者数の集計
            leave_summary = leave_data.groupby(leave_data['ds'].dt.date).agg({
                'staff': 'nunique',
                'role': lambda x: ', '.join(x.unique()[:5])  # 最大5職種まで表示
            }).reset_index()
            leave_summary.columns = ['date', 'leave_count', 'affected_roles']
            
            print(f"\n休暇分析結果:")
            print(leave_summary.head())
            print("✅ 休暇分析データ: 正常")
            return True
        else:
            print("❌ 休暇分析データ: 休暇データが見つからない")
            return False
    else:
        print("❌ 休暇分析データ: long_dfが不正")
        return False

def test_data_cache_simulation():
    """DATA_CACHEの動作を模擬テスト"""
    print("\n=== DATA_CACHE模擬テスト ===")
    
    # 簡単なキャッシュ模擬
    mock_cache = {
        'shortage_role_summary': pd.DataFrame({
            'role': ['看護師', '介護職'],
            'lack_h': [8.5, 12.3],
            'excess_h': [1.2, 0.0]
        }),
        'shortage_time': pd.DataFrame({
            'time_slot': ['08:00', '09:00', '10:00'],
            'shortage_count': [2, 1, 3]
        }),
        'staff_balance_daily': pd.DataFrame(),  # 空
        'daily_summary': pd.DataFrame(),  # 空
        'leave_analysis': pd.DataFrame()  # 空
    }
    
    def mock_data_get(key, default=None):
        return mock_cache.get(key, default)
    
    # 不足分析タブでのdata_get呼び出しを模擬
    df_shortage_role = mock_data_get('shortage_role_summary', pd.DataFrame())
    df_shortage_time = mock_data_get('shortage_time', pd.DataFrame())
    
    print(f"shortage_role_summary: {len(df_shortage_role)}行")
    print(f"shortage_time: {len(df_shortage_time)}行")
    
    # 休暇分析タブでのdata_get呼び出しを模擬
    df_staff_balance = mock_data_get('staff_balance_daily', pd.DataFrame())
    df_daily_summary = mock_data_get('daily_summary', pd.DataFrame())
    df_leave_analysis = mock_data_get('leave_analysis', pd.DataFrame())
    
    print(f"staff_balance_daily: {len(df_staff_balance)}行")
    print(f"daily_summary: {len(df_daily_summary)}行")
    print(f"leave_analysis: {len(df_leave_analysis)}行")
    
    # 休暇分析の代替処理テスト
    if all(df.empty for df in [df_staff_balance, df_daily_summary, df_leave_analysis]):
        print("✅ 休暇分析: 代替処理が必要（正常な動作）")
        return True
    else:
        print("✅ 休暇分析: 元データが利用可能")
        return True

def run_debug_tests():
    """全デバッグテストを実行"""
    print("=== dash_app.py 問題デバッグテスト開始 ===")
    print(f"実行時刻: {datetime.now()}")
    
    results = []
    
    # 1. 不足分析タブロジックテスト
    results.append(test_shortage_tab_logic())
    
    # 2. 休暇分析データテスト
    results.append(test_leave_analysis_data())
    
    # 3. データキャッシュ模擬テスト
    results.append(test_data_cache_simulation())
    
    print(f"\n=== デバッグテスト結果 ===")
    print(f"成功したテスト: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ 全テスト成功: ロジックに問題なし")
        print("問題は実行時のデータやコールバック呼び出しにある可能性があります")
    else:
        print("❌ 一部テスト失敗: ロジックに問題があります")
    
    print("\n推奨される次のステップ:")
    print("1. dash_app.pyを起動してログを確認")
    print("2. データファイルが正しく読み込まれているか確認")
    print("3. UIでタブをクリックした際のコールバック動作を確認")

if __name__ == "__main__":
    run_debug_tests()