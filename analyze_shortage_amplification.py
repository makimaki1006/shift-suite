#!/usr/bin/env python3
"""
不足時間の異常放大（8.6時間/日）の根本原因分析
27,486.5時間問題の真の解決に向けた徹底調査スクリプト
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def analyze_shortage_calculation_amplification():
    """不足時間計算の異常放大を詳細分析"""
    
    print("=" * 80)
    print("🔍 不足時間異常放大（8.6時間/日）の根本原因分析")
    print("=" * 80)
    
    # 分析対象ディレクトリを取得
    analysis_dirs = [
        "./extracted_test/out_median_based",
        "./extracted_test/out_mean_based", 
        "./extracted_test/out_p25_based",
        "./temp_analysis_check/out_median_based"
    ]
    
    results = {}
    
    for dir_path in analysis_dirs:
        dir_path = Path(dir_path)
        if not dir_path.exists():
            continue
            
        print(f"\n📁 分析対象: {dir_path}")
        
        try:
            # 1. shortage_time.parquet の詳細分析
            shortage_file = dir_path / "shortage_time.parquet"
            need_file = dir_path / "need_per_date_slot.parquet"
            heat_all_file = dir_path / "heat_ALL.parquet"
            meta_file = dir_path / "heatmap.meta.json"
            
            analysis_result = {
                'directory': str(dir_path),
                'files_found': {},
                'shortage_analysis': {},
                'need_analysis': {},
                'amplification_factors': {},
                'root_causes': []
            }
            
            # ファイル存在確認
            for file_name, file_path in [
                ('shortage_time', shortage_file),
                ('need_per_date_slot', need_file),
                ('heat_ALL', heat_all_file),
                ('meta', meta_file)
            ]:
                analysis_result['files_found'][file_name] = file_path.exists()
                if file_path.exists():
                    print(f"  ✓ {file_name}: 存在")
                else:
                    print(f"  ✗ {file_name}: 不存在")
            
            # 2. shortage_time.parquet の詳細分析
            if shortage_file.exists():
                shortage_df = pd.read_parquet(shortage_file)
                print(f"\n  📊 Shortage Time 分析:")
                print(f"    形状: {shortage_df.shape} (時間帯 × 日付)")
                
                # 統計値計算
                total_shortage_slots = shortage_df.sum().sum()
                period_days = len(shortage_df.columns)
                time_slots = len(shortage_df.index)
                
                # スロット時間を推定（通常は30分=0.5時間）
                slot_hours = 0.5  # デフォルト
                
                total_shortage_hours = total_shortage_slots * slot_hours
                avg_shortage_per_day = total_shortage_hours / max(period_days, 1)
                
                print(f"    期間: {period_days}日")
                print(f"    時間帯数: {time_slots}")
                print(f"    総不足スロット数: {total_shortage_slots:.1f}")
                print(f"    総不足時間: {total_shortage_hours:.1f}時間")
                print(f"    1日平均不足: {avg_shortage_per_day:.2f}時間/日")
                
                # 🎯 異常値検出
                if avg_shortage_per_day > 5:
                    print(f"    ⚠️ 異常: 1日{avg_shortage_per_day:.1f}時間は過大（正常: 1-3時間/日）")
                    analysis_result['root_causes'].append(f"Daily average {avg_shortage_per_day:.1f}h exceeds normal range")
                
                # 日別・時間帯別の詳細分析
                daily_shortage = shortage_df.sum(axis=0)  # 日別合計
                hourly_shortage = shortage_df.sum(axis=1)  # 時間帯別合計
                
                print(f"    日別不足 - 最大: {daily_shortage.max():.1f}スロット, 最小: {daily_shortage.min():.1f}スロット")
                print(f"    時間帯別不足 - 最大: {hourly_shortage.max():.1f}スロット")
                
                # 最も不足の多い時間帯TOP5
                top_shortage_times = hourly_shortage.nlargest(5)
                print(f"    最大不足時間帯TOP5:")
                for time_slot, shortage_count in top_shortage_times.items():
                    print(f"      {time_slot}: {shortage_count:.1f}スロット ({shortage_count * slot_hours:.1f}時間)")
                
                analysis_result['shortage_analysis'] = {
                    'total_slots': float(total_shortage_slots),
                    'total_hours': float(total_shortage_hours),
                    'period_days': period_days,
                    'avg_per_day': float(avg_shortage_per_day),
                    'max_daily': float(daily_shortage.max()),
                    'min_daily': float(daily_shortage.min()),
                    'top_shortage_times': {str(k): float(v) for k, v in top_shortage_times.items()}
                }
            
            # 3. need_per_date_slot.parquet の詳細分析
            if need_file.exists():
                need_df = pd.read_parquet(need_file)
                print(f"\n  📈 Need Data 分析:")
                print(f"    形状: {need_df.shape}")
                
                total_need = need_df.sum().sum()
                max_need = need_df.max().max()
                mean_need = need_df.mean().mean()
                
                print(f"    総Need値: {total_need:.1f}")
                print(f"    最大Need値: {max_need:.1f}")
                print(f"    平均Need値: {mean_need:.2f}")
                
                # 🎯 Need値の異常検出
                if max_need > 10:
                    print(f"    ⚠️ 異常: 最大Need値{max_need:.1f}は過大（正常: 1-5人/スロット）")
                    analysis_result['root_causes'].append(f"Max Need value {max_need:.1f} exceeds normal range")
                
                if mean_need > 3:
                    print(f"    ⚠️ 異常: 平均Need値{mean_need:.2f}は過大（正常: 0.5-2人/スロット）")
                    analysis_result['root_causes'].append(f"Mean Need value {mean_need:.2f} exceeds normal range")
                
                analysis_result['need_analysis'] = {
                    'total_need': float(total_need),
                    'max_need': float(max_need),
                    'mean_need': float(mean_need)
                }
            
            # 4. heat_ALL.parquet との比較分析
            if heat_all_file.exists():
                heat_all_df = pd.read_parquet(heat_all_file)
                print(f"\n  🔥 Heat ALL 分析:")
                print(f"    形状: {heat_all_df.shape}")
                
                # 実績データの分析
                date_columns = [col for col in heat_all_df.columns if pd.api.types.is_datetime64_any_dtype(pd.to_datetime(col, errors='coerce', infer_datetime_format=True))]
                if not date_columns:
                    # 文字列の日付列を探す
                    date_columns = [col for col in heat_all_df.columns if isinstance(col, str) and ('2024' in col or '2025' in col)]
                
                if date_columns:
                    actual_data = heat_all_df[date_columns]
                    total_actual = actual_data.sum().sum()
                    print(f"    総実績値: {total_actual:.1f}")
                    
                    # Need vs 実績の比較
                    if need_file.exists() and total_need > 0:
                        need_vs_actual_ratio = total_need / max(total_actual, 1)
                        print(f"    Need/実績比率: {need_vs_actual_ratio:.2f}")
                        
                        if need_vs_actual_ratio > 2.0:
                            print(f"    ⚠️ 異常: Need値が実績の{need_vs_actual_ratio:.1f}倍（正常: 1.0-1.5倍）")
                            analysis_result['root_causes'].append(f"Need/Actual ratio {need_vs_actual_ratio:.2f} is excessive")
                        
                        analysis_result['amplification_factors']['need_vs_actual_ratio'] = float(need_vs_actual_ratio)
            
            # 5. meta.json からの統計手法確認
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                    
                print(f"\n  ⚙️ Meta Data 分析:")
                
                # 統計手法の確認
                statistic_method = meta_data.get('statistic_method', 'Unknown')
                print(f"    統計手法: {statistic_method}")
                
                if '75パーセンタイル' in statistic_method or '90パーセンタイル' in statistic_method:
                    print(f"    ⚠️ 高パーセンタイル検出: {statistic_method}が需要を過大評価している可能性")
                    analysis_result['root_causes'].append(f"High percentile method '{statistic_method}' may inflate demand")
                
                # 調整係数の確認
                adjustment_factor = meta_data.get('adjustment_factor', 1.0)
                if adjustment_factor > 1.2:
                    print(f"    ⚠️ 高い調整係数: {adjustment_factor}")
                    analysis_result['root_causes'].append(f"High adjustment factor {adjustment_factor}")
                
                analysis_result['amplification_factors'].update({
                    'statistic_method': statistic_method,
                    'adjustment_factor': adjustment_factor
                })
            
            results[str(dir_path)] = analysis_result
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            results[str(dir_path)] = {'error': str(e)}
    
    # 6. 全体サマリーと根本原因の特定
    print(f"\n" + "=" * 80)
    print("🎯 根本原因分析サマリー")
    print("=" * 80)
    
    all_root_causes = []
    all_avg_shortages = []
    
    for dir_name, result in results.items():
        if 'error' in result:
            continue
            
        shortage_analysis = result.get('shortage_analysis', {})
        avg_shortage = shortage_analysis.get('avg_per_day', 0)
        
        if avg_shortage > 0:
            all_avg_shortages.append(avg_shortage)
            print(f"\n📊 {Path(dir_name).name}: {avg_shortage:.2f}時間/日")
            
            for cause in result.get('root_causes', []):
                all_root_causes.append(cause)
                print(f"  🔍 {cause}")
    
    # 最終判定
    if all_avg_shortages:
        avg_of_avgs = np.mean(all_avg_shortages)
        print(f"\n🔍 全体平均不足時間: {avg_of_avgs:.2f}時間/日")
        
        if avg_of_avgs > 5:
            print(f"❌ 結論: {avg_of_avgs:.1f}時間/日は依然として異常に高い")
            print("🎯 残存する主な問題:")
            
            # 根本原因の分類
            cause_categories = {
                'statistical_amplification': [],
                'need_overestimation': [],
                'period_dependency': [],
                'calculation_error': []
            }
            
            for cause in set(all_root_causes):
                if 'percentile' in cause.lower() or 'adjustment' in cause.lower():
                    cause_categories['statistical_amplification'].append(cause)
                elif 'need' in cause.lower() and 'exceeds' in cause.lower():
                    cause_categories['need_overestimation'].append(cause)
                elif 'ratio' in cause.lower() and 'excessive' in cause.lower():
                    cause_categories['calculation_error'].append(cause)
                else:
                    cause_categories['period_dependency'].append(cause)
            
            for category, causes in cause_categories.items():
                if causes:
                    print(f"\n  📋 {category.replace('_', ' ').title()}:")
                    for cause in causes:
                        print(f"    • {cause}")
        else:
            print(f"✅ 結論: {avg_of_avgs:.1f}時間/日は許容範囲内")
    
    # 結果をJSONファイルに保存
    output_file = Path("shortage_amplification_analysis_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 詳細結果を保存: {output_file}")
    
    return results

if __name__ == "__main__":
    analyze_shortage_calculation_amplification()