#!/usr/bin/env python3
"""
実配置データの慎重な分析（簡潔版）
Step2-T1: データ理解から安全なアルゴリズム設計へ
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

def analyze_actual_data_safely():
    """実配置データの安全な分析"""
    
    print('=' * 60)
    print('Step2-T1: 実配置データ慎重分析')
    print('=' * 60)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    try:
        # 1. データ読み込みと基本確認
        print('\n[Phase 1: データ読み込み]')
        data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        
        print(f'総レコード数: {len(data):,}')
        print(f'期間: {data["ds"].dt.date.nunique()}日間')
        print(f'時間スロット: {data["ds"].dt.time.nunique()}個')
        print(f'スタッフ数: {data["staff"].nunique()}名')
        print(f'職種数: {data["role"].nunique()}職種')
        print(f'雇用形態数: {data["employment"].nunique()}形態')
        
        # 2. 職種別分析
        print('\n[Phase 2: 職種別配置分析]')
        role_stats = {}
        role_dist = data['role'].value_counts()
        
        for role, count in role_dist.items():
            role_data = data[data['role'] == role]
            staff_count = role_data['staff'].nunique()
            avg_records_per_staff = count / staff_count
            
            role_stats[role] = {
                'total_records': count,
                'unique_staff': staff_count,
                'avg_records_per_staff': avg_records_per_staff,
                'percentage': count / len(data) * 100
            }
            
            print(f'  {role}: {count}レコード, {staff_count}名, 平均{avg_records_per_staff:.1f}レコード/人')
        
        # 3. 雇用形態別分析
        print('\n[Phase 3: 雇用形態別分析]')
        emp_stats = {}
        emp_dist = data['employment'].value_counts()
        
        for emp, count in emp_dist.items():
            emp_data = data[data['employment'] == emp]
            staff_count = emp_data['staff'].nunique()
            
            emp_stats[emp] = {
                'total_records': count,
                'unique_staff': staff_count,
                'percentage': count / len(data) * 100
            }
            
            print(f'  {emp}: {count}レコード ({count/len(data)*100:.1f}%), {staff_count}名')
        
        # 4. 時間軸分析
        print('\n[Phase 4: 時間軸分析]')
        
        # 日別変動
        daily_counts = data.groupby(data['ds'].dt.date).size()
        daily_cv = daily_counts.std() / daily_counts.mean()
        
        # 時間帯分析
        time_slots = data['ds'].dt.time.unique()
        start_time = min(time_slots)
        end_time = max(time_slots)
        
        # スロット間隔計算
        sorted_times = sorted(time_slots)
        intervals = []
        for i in range(1, len(sorted_times)):
            prev_min = sorted_times[i-1].hour * 60 + sorted_times[i-1].minute
            curr_min = sorted_times[i].hour * 60 + sorted_times[i].minute
            intervals.append(curr_min - prev_min)
        
        typical_interval = np.mean(intervals) if intervals else 0
        
        print(f'  日別変動係数: {daily_cv:.3f}')
        print(f'  時間範囲: {start_time} - {end_time}')
        print(f'  スロット数: {len(time_slots)}個')
        print(f'  典型的間隔: {typical_interval:.0f}分')
        
        # 5. データ品質評価
        print('\n[Phase 5: データ品質評価]')
        
        # 欠損値チェック
        missing_counts = data.isnull().sum()
        total_missing = missing_counts.sum()
        
        # 重複チェック
        duplicates = data.duplicated().sum()
        
        # 品質スコア算出
        quality_score = 1.0
        if total_missing > 0:
            quality_score -= 0.1
        if duplicates > 0:
            quality_score -= 0.1
        if daily_cv > 0.5:
            quality_score -= 0.2
        
        print(f'  欠損値: {total_missing}個')
        print(f'  重複レコード: {duplicates}個')
        print(f'  品質スコア: {quality_score:.2f}/1.0')
        
        # 6. Need算出設計のための推奨事項
        print('\n[Phase 6: 設計推奨事項]')
        
        recommendations = []
        
        # データ品質ベースの推奨
        if quality_score >= 0.8:
            recommendations.append('高品質データ: 精密な実配置ベース算出が適用可能')
        else:
            recommendations.append('品質注意: 保守的な係数適用を推奨')
        
        # 職種数ベースの推奨
        if len(role_dist) >= 10:
            recommendations.append('多職種環境: 職種別個別調整が必要')
        
        # 時間構造ベースの推奨
        if len(time_slots) < 48:
            recommendations.append('部分時間カバレッジ: 時間補正係数を検討')
        
        # 変動性ベースの推奨
        if daily_cv > 0.3:
            recommendations.append('日別変動大: 外れ値処理が必要')
        
        for i, rec in enumerate(recommendations, 1):
            print(f'  {i}. {rec}')
        
        # 7. 結果まとめ
        analysis_result = {
            'analysis_timestamp': datetime.now().isoformat(),
            'basic_stats': {
                'total_records': len(data),
                'period_days': data['ds'].dt.date.nunique(),
                'time_slots': len(time_slots),
                'staff_count': data['staff'].nunique(),
                'role_count': len(role_dist),
                'employment_count': len(emp_dist)
            },
            'role_analysis': role_stats,
            'employment_analysis': emp_stats,
            'temporal_analysis': {
                'daily_variation_coefficient': daily_cv,
                'start_time': str(start_time),
                'end_time': str(end_time),
                'typical_interval_minutes': typical_interval
            },
            'data_quality': {
                'missing_values': total_missing,
                'duplicate_records': duplicates,
                'quality_score': quality_score
            },
            'design_recommendations': recommendations,
            'ready_for_algorithm_design': quality_score >= 0.7
        }
        
        # JSON保存
        with open('actual_data_analysis_result.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print('\n' + '=' * 60)
        print('S2-T1 完了サマリー')
        print('=' * 60)
        print(f'分析対象: {len(data):,}レコード ({data["ds"].dt.date.nunique()}日間)')
        print(f'職種数: {len(role_dist)}, 雇用形態数: {len(emp_dist)}')
        print(f'データ品質: {quality_score:.2f}/1.0')
        print(f'設計準備: {"[OK] 準備完了" if analysis_result["ready_for_algorithm_design"] else "[WARNING] 要注意"}')
        
        return analysis_result
        
    except Exception as e:
        print(f'[ERROR] 分析失敗: {e}')
        return None

if __name__ == "__main__":
    result = analyze_actual_data_safely()
    if result:
        print('\n分析結果保存: actual_data_analysis_result.json')
        print('S2-T2: アルゴリズム設計への準備完了')
    else:
        print('分析に失敗しました')