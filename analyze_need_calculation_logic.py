#!/usr/bin/env python3
"""
問題1: 需要計算の科学的根拠確立 - 現在のneed値生成ロジック詳細分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys

def analyze_need_calculation_logic():
    """現在のneed値生成ロジックを科学的に分析"""
    
    print("=" * 80)
    print("問題1: 需要計算の科学的根拠確立 - 詳細ロジック分析")
    print("=" * 80)
    
    # 1. need_per_date_slot.parquet の実データ分析
    print("\n【STEP 1: need_per_date_slot.parquet 実データ分析】")
    
    need_file = Path("extracted_results/out_p25_based/need_per_date_slot.parquet")
    if need_file.exists():
        try:
            need_df = pd.read_parquet(need_file)
            print(f"ファイル: {need_file}")
            print(f"データ形状: {need_df.shape}")
            print(f"インデックス: {need_df.index[:5].tolist()}")  # 時間帯
            print(f"列名: {need_df.columns[:5].tolist()}")  # 日付
            print("\n実際のneed値サンプル:")
            print(need_df.iloc[:10, :5])  # 最初の10時間帯×5日分
            
            # need値の統計分析
            print("\n【need値の統計分析】")
            all_need_values = need_df.values.flatten()
            print(f"総need値数: {len(all_need_values):,}")
            print(f"ユニークneed値: {sorted(set(all_need_values))}")
            print(f"最小値: {all_need_values.min()}")
            print(f"最大値: {all_need_values.max()}")
            print(f"平均値: {all_need_values.mean():.2f}")
            print(f"中央値: {np.median(all_need_values):.2f}")
            print(f"ゼロ値の割合: {(all_need_values == 0).sum() / len(all_need_values) * 100:.1f}%")
            
            # 時間帯別パターン分析
            print("\n【時間帯別need値パターン】")
            hourly_avg = need_df.mean(axis=1)  # 各時間帯の平均need
            non_zero_times = hourly_avg[hourly_avg > 0]
            print(f"勤務時間帯: {len(non_zero_times)}時間帯")
            print("主要勤務時間帯:")
            for time_slot, avg_need in non_zero_times.head(10).items():
                print(f"  {time_slot}: 平均{avg_need:.1f}人")
                
            # 曜日別パターン分析
            print("\n【曜日別need値パターン】")
            if hasattr(need_df.columns, 'to_pydatetime'):
                dates = pd.to_datetime(need_df.columns)
                weekday_patterns = {}
                for col_idx, date in enumerate(dates):
                    weekday = date.strftime('%A')
                    if weekday not in weekday_patterns:
                        weekday_patterns[weekday] = []
                    weekday_patterns[weekday].append(need_df.iloc[:, col_idx].sum())
                
                for weekday, daily_totals in weekday_patterns.items():
                    avg_daily = np.mean(daily_totals)
                    print(f"  {weekday}: 平均 {avg_daily:.1f}人・時間/日")
        
        except Exception as e:
            print(f"分析エラー: {e}")
    else:
        print("need_per_date_slot.parquet が見つかりません")
    
    # 2. heatmap.meta.json の需要計算パラメータ分析
    print("\n【STEP 2: need計算パラメータ分析】")
    
    meta_file = Path("extracted_results/out_p25_based/heatmap.meta.json")
    if meta_file.exists():
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            print("need計算パラメータ:")
            params = meta_data.get('need_calculation_params', {})
            for key, value in params.items():
                print(f"  {key}: {value}")
            
            print("\ndow_need_pattern (曜日パターン) 分析:")
            dow_pattern = meta_data.get('dow_need_pattern', [])
            if dow_pattern:
                # 曜日別統計
                weekday_totals = {}
                for entry in dow_pattern:
                    time_slot = entry.get('time')
                    if time_slot:
                        for day_idx in range(7):  # 0=月曜 ～ 6=日曜
                            day_need = entry.get(str(day_idx), 0)
                            if day_idx not in weekday_totals:
                                weekday_totals[day_idx] = 0
                            weekday_totals[day_idx] += day_need
                
                weekdays = ['月', '火', '水', '木', '金', '土', '日']
                print("曜日別1日総需要:")
                for day_idx, total_need in weekday_totals.items():
                    print(f"  {weekdays[day_idx]}曜日: {total_need}人・時間")
                    
                # 時間帯別統計
                peak_times = []
                for entry in dow_pattern:
                    time_slot = entry.get('time')
                    weekday_avg = np.mean([entry.get(str(i), 0) for i in range(6)])  # 土日除く平均
                    if weekday_avg > 0:
                        peak_times.append((time_slot, weekday_avg))
                
                peak_times.sort(key=lambda x: x[1], reverse=True)
                print("\n需要ピーク時間帯 TOP10:")
                for time_slot, avg_need in peak_times[:10]:
                    print(f"  {time_slot}: 平均{avg_need:.1f}人")
                    
        except Exception as e:
            print(f"メタデータ分析エラー: {e}")
    else:
        print("heatmap.meta.json が見つかりません")
    
    # 3. 科学的根拠の問題点特定
    print("\n【STEP 3: 科学的根拠の問題点分析】")
    
    problems = [
        "NG 問題A: need値の生成根拠が不透明",
        "   - 1, 11, 12, 13, 14 という具体的な数値がどのような分析から導出されたか不明",
        "   - 25パーセンタイル という統計手法の選択理由が不明",
        "",
        "NG 問題B: 業界標準・ベンチマークとの比較なし", 
        "   - 介護業界の標準的な人員配置基準との比較データなし",
        "   - 他施設との需要パターン比較なし",
        "",
        "NG 問題C: 需要予測の検証プロセスなし",
        "   - 予測したneed値と実際の必要人員の乖離を測定する仕組みなし",
        "   - 過去のneed予測の精度評価なし",
        "",
        "NG 問題D: 外部要因の考慮不足",
        "   - 季節変動、イベント、利用者数変動などの考慮が不十分",
        "   - 緊急時・繁忙期の需要増加への対応策なし",
        "",
        "NG 問題E: 統計的有意性の確認不足",
        "   - IQR乗数1.5という外れ値除去基準の根拠不明",
        "   - 信頼区間、有意水準などの統計的検定なし"
    ]
    
    for problem in problems:
        print(problem)
    
    # 4. 改善提案の方向性
    print("\n【STEP 4: 科学的根拠確立の改善方向性】")
    
    improvements = [
        "OK 改善A: 業界標準ベンチマーク導入",
        "   - 厚労省の人員配置基準をベースライン設定",
        "   - 同規模施設との需要パターン比較分析",
        "",
        "OK 改善B: 予測精度検証システム",
        "   - need予測値 vs 実績値の定期的な乖離分析",
        "   - 予測精度向上のためのフィードバックループ",
        "",
        "OK 改善C: 多変量予測モデル", 
        "   - 利用者数、重症度、季節変動を考慮した需要予測",
        "   - 機械学習による予測精度向上",
        "",
        "OK 改善D: 統計的検定の導入",
        "   - 需要パターンの有意差検定",
        "   - 信頼区間付きの需要予測値",
        "",
        "OK 改善E: リアルタイム調整機能",
        "   - 実績データによる需要パターンの動的更新",
        "   - 異常検知による緊急時対応"
    ]
    
    for improvement in improvements:
        print(improvement)
    
    print("\n" + "=" * 80)
    print("分析完了: 問題1 - 需要計算の科学的根拠確立")
    print("次段階: 具体的改善案の実装設計")
    print("=" * 80)

if __name__ == "__main__":
    analyze_need_calculation_logic()