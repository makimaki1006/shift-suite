#!/usr/bin/env python3
"""
徹底的なデータ構造調査
23.6時間/日という異常値の根本原因を完全に解明する
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

def thorough_data_investigation():
    """データ構造の徹底的な調査"""
    
    print("=" * 80)
    print("データ構造 徹底的調査")
    print("目的: 23.6時間/日不足の根本原因完全解明")
    print("=" * 80)
    
    scenario_dir = Path("extracted_results/out_p25_based")
    
    # === PHASE 1: INTERMEDIATE_DATAの完全解析 ===
    print("\n【PHASE 1: INTERMEDIATE_DATA完全解析】")
    
    intermediate_data = pd.read_parquet(scenario_dir / "intermediate_data.parquet")
    
    print(f"基本情報:")
    print(f"  総レコード数: {len(intermediate_data)}")
    print(f"  カラム: {list(intermediate_data.columns)}")
    print(f"  期間: {intermediate_data['ds'].min()} ～ {intermediate_data['ds'].max()}")
    print(f"  実際の日数: {intermediate_data['ds'].dt.date.nunique()}日")
    
    # 時間軸の詳細分析
    print(f"\n時間軸詳細:")
    unique_times = sorted(intermediate_data['ds'].dt.time.unique())
    print(f"  時間帯数: {len(unique_times)}")
    print(f"  時間帯: {unique_times[:10]}...") # 最初の10個表示
    
    # 介護データの詳細
    care_data = intermediate_data[intermediate_data['role'].str.contains('介護', na=False)]
    print(f"\n介護関連データ:")
    print(f"  介護レコード数: {len(care_data)}")
    print(f"  介護職種: {care_data['role'].unique()}")
    
    # 1日あたりのレコード分析
    daily_counts = care_data.groupby(care_data['ds'].dt.date).size()
    print(f"\n日別レコード数統計:")
    print(f"  平均: {daily_counts.mean():.1f}レコード/日")
    print(f"  最大: {daily_counts.max()}レコード/日")
    print(f"  最小: {daily_counts.min()}レコード/日")
    print(f"  標準偏差: {daily_counts.std():.1f}")
    
    # === PHASE 2: NEED_DATAの完全解析 ===
    print(f"\n【PHASE 2: NEED_DATA完全解析】")
    
    need_files = list(scenario_dir.glob("need_per_date_slot_role_*介護*.parquet"))
    
    print(f"需要ファイル数: {len(need_files)}")
    
    need_analysis = {}
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        
        print(f"\n{need_file.name}詳細分析:")
        print(f"  形状: {df.shape}")
        print(f"  インデックス: {df.index.name} = {list(df.index[:5])}")
        print(f"  カラム: {list(df.columns[:5])}...")
        
        # データの実際の内容確認
        print(f"  データサンプル:")
        print(f"    [0,0] = {df.iloc[0,0]} (型: {type(df.iloc[0,0])})")
        print(f"    [0,1] = {df.iloc[0,1]} (型: {type(df.iloc[0,1])})")
        
        # 統計情報
        total_sum = df.sum().sum()
        max_val = df.max().max()
        non_zero_count = (df > 0).sum().sum()
        
        print(f"  統計:")
        print(f"    合計: {total_sum}")
        print(f"    最大値: {max_val}")
        print(f"    非ゼロ要素数: {non_zero_count}")
        print(f"    全要素数: {df.size}")
        print(f"    非ゼロ率: {non_zero_count/df.size*100:.1f}%")
        
        need_analysis[need_file.name] = {
            'total': total_sum,
            'max': max_val,
            'non_zero_count': non_zero_count,
            'shape': df.shape
        }
    
    # === PHASE 3: データの意味解釈 ===
    print(f"\n【PHASE 3: データ意味解釈】")
    
    # 需要データの構造分析
    print("需要データ構造分析:")
    sample_need_file = need_files[1] if len(need_files) > 1 else need_files[0]  # 介護.parquetを選択
    sample_df = pd.read_parquet(sample_need_file)
    
    print(f"  サンプルファイル: {sample_need_file.name}")
    print(f"  行数(時間帯): {len(sample_df)}")
    print(f"  列数(日数): {len(sample_df.columns)}")
    print(f"  1日の時間帯数: {len(sample_df)}")  # 48 = 24時間 x 2(30分刻み)
    
    # 各セルの意味を推定
    print(f"\nデータセル意味推定:")
    if len(sample_df) == 48:
        print(f"  行: 30分刻みの時間帯 (48 = 24時間 x 2)")
    else:
        print(f"  行: 不明な時間分割 ({len(sample_df)})")
    
    print(f"  列: 日付 ({len(sample_df.columns)}日間)")
    print(f"  セルの値: 該当時間帯・日付の必要人数 (推定)")
    
    # === PHASE 4: 計算の検証 ===
    print(f"\n【PHASE 4: 計算検証】")
    
    # 現在のロジック再現
    total_need = sum(analysis['total'] for analysis in need_analysis.values())
    total_staff = len(care_data) * 0.5
    current_shortage = total_need - total_staff
    
    print(f"現在の計算:")
    print(f"  需要合計: {total_need}")
    print(f"  配置合計: {total_staff} = {len(care_data)} x 0.5")
    print(f"  不足: {current_shortage}")
    print(f"  1日不足: {current_shortage/30:.1f}")
    
    # === PHASE 5: 正しい解釈の検討 ===
    print(f"\n【PHASE 5: 正しい解釈の検討】")
    
    print("仮説1: 需要データは「人時間」ではなく「人数」")
    print("  - セル値1 = その時間帯に1人必要")
    print("  - 合計値 = 総必要人・時間帯数")
    print("  - 0.5時間をかける必要なし")
    
    hypothesis1_daily_need = total_need / 30  # 30日で割る
    hypothesis1_daily_staff = len(care_data) / 30 / 48  # 1日48時間帯で割る
    
    print(f"  仮説1結果:")
    print(f"    1日需要: {hypothesis1_daily_need:.1f}人・時間帯/日")
    print(f"    1日配置: {hypothesis1_daily_staff:.1f}人/時間帯")
    
    print(f"\n仮説2: intermediate_dataのレコードは「人・30分」")
    print("  - 1レコード = 1人が30分勤務")
    print("  - 時間換算は正しく0.5時間")
    
    hypothesis2_daily_need = total_need / 30  # セル値の合計を日数で割る
    hypothesis2_daily_staff = len(care_data) * 0.5 / 30  # 時間で計算
    
    print(f"  仮説2結果:")
    print(f"    1日需要: {hypothesis2_daily_need:.1f}人・時間帯/日") 
    print(f"    1日配置: {hypothesis2_daily_staff:.1f}時間/日")
    
    print(f"\n仮説3: 単位系の不整合")
    print("  - 需要データ: 人数単位")
    print("  - 配置データ: 時間単位") 
    print("  - 比較するために単位を揃える必要")
    
    # 仮説3: 需要を時間に換算
    hypothesis3_need_hours = total_need * 0.5 / 30  # 人数→時間換算、30日で割る
    hypothesis3_staff_hours = len(care_data) * 0.5 / 30
    
    print(f"  仮説3結果:")
    print(f"    1日需要: {hypothesis3_need_hours:.1f}時間/日")
    print(f"    1日配置: {hypothesis3_staff_hours:.1f}時間/日")
    print(f"    1日不足: {max(0, hypothesis3_need_hours - hypothesis3_staff_hours):.1f}時間/日")
    
    # === PHASE 6: 現実性チェック ===
    print(f"\n【PHASE 6: 現実性チェック】")
    
    scenarios = [
        ("現在のロジック", current_shortage/30),
        ("仮説3(単位統一)", max(0, hypothesis3_need_hours - hypothesis3_staff_hours))
    ]
    
    print("現実性評価:")
    for name, daily_shortage in scenarios:
        if 0 <= daily_shortage <= 10:
            status = "✓ 現実的"
        elif daily_shortage <= 20:
            status = "△ 要注意"
        else:
            status = "✗ 非現実的"
        
        print(f"  {name}: {daily_shortage:.1f}時間/日 - {status}")
    
    # === 結論と推奨修正 ===
    print(f"\n【結論と推奨修正】")
    
    best_hypothesis = 3  # 仮説3が最も現実的
    recommended_daily = max(0, hypothesis3_need_hours - hypothesis3_staff_hours)
    
    print(f"最適解: 仮説{best_hypothesis} (単位系統一)")
    print(f"推奨1日不足: {recommended_daily:.1f}時間/日")
    
    if recommended_daily <= 10:
        print("この値は現実的で実装可能です")
        return {
            'status': 'SUCCESS',
            'daily_shortage': recommended_daily,
            'fix_required': True,
            'recommended_logic': 'unit_normalization'
        }
    else:
        print("さらなる調査が必要です")
        return {
            'status': 'NEEDS_MORE_INVESTIGATION',
            'daily_shortage': recommended_daily,
            'fix_required': True
        }

if __name__ == "__main__":
    result = thorough_data_investigation()
    print(f"\n" + "=" * 80)
    print(f"徹底調査結果: {result['status']}")
    if result['fix_required']:
        print(f"修正が必要: 推奨1日不足 {result['daily_shortage']:.1f}時間/日")
    print("=" * 80)