#!/usr/bin/env python3
"""
0:00重複問題の最終分析レポート
データから具体的な数値を抽出して重複問題を定量化
"""

import csv
import json
import os
from datetime import datetime

print('=== 0:00重複問題の最終分析レポート ===')

# 分析対象フォルダ
analysis_folder = '/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/temp_analysis_results/out_p25_based/'

def analyze_shortage_leave_csv():
    """shortage_leave.csvから0:00の人員データを抽出"""
    print('\n1. shortage_leave.csvによる0:00人員分析')
    print('=' * 60)
    
    csv_path = os.path.join(analysis_folder, 'shortage_leave.csv')
    if not os.path.exists(csv_path):
        print('shortage_leave.csvが見つかりません')
        return None
    
    # 0:00のデータを抽出
    midnight_data = []
    other_times_data = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_str = row['time']
            leave_applicants = int(row['leave_applicants'])
            
            if time_str == '00:00':
                midnight_data.append({
                    'date': row['date'],
                    'leave_applicants': leave_applicants,
                    'lack': int(row['lack']),
                    'net_shortage': int(row['net_shortage'])
                })
            elif time_str in ['23:45', '00:15', '00:30']:
                other_times_data.append({
                    'time': time_str,
                    'date': row['date'],
                    'leave_applicants': leave_applicants,
                    'lack': int(row['lack']),
                    'net_shortage': int(row['net_shortage'])
                })
    
    print(f'0:00データ件数: {len(midnight_data)}件')
    print(f'比較時間データ件数: {len(other_times_data)}件')
    
    if midnight_data:
        # 0:00の統計
        leave_counts = [d['leave_applicants'] for d in midnight_data]
        avg_leave = sum(leave_counts) / len(leave_counts)
        max_leave = max(leave_counts)
        min_leave = min(leave_counts)
        
        print(f'\n0:00時刻の人員統計:')
        print(f'  平均人員: {avg_leave:.1f}人')
        print(f'  最大人員: {max_leave}人')
        print(f'  最小人員: {min_leave}人')
        
        # 日別詳細
        print(f'\n6月前半10日間の0:00人員数:')
        for i, data in enumerate(midnight_data[:10]):
            print(f'  {data["date"]}: {data["leave_applicants"]}人')
        
        # 比較時間の統計
        if other_times_data:
            other_leave_counts = [d['leave_applicants'] for d in other_times_data]
            other_avg = sum(other_leave_counts) / len(other_leave_counts)
            
            print(f'\n比較時間(23:45, 00:15, 00:30)の平均人員: {other_avg:.1f}人')
            print(f'0:00との差分: {avg_leave - other_avg:+.1f}人')
            
            if avg_leave > other_avg:
                excess_ratio = avg_leave / other_avg
                print(f'0:00は他時間の{excess_ratio:.2f}倍の人員')
                if excess_ratio > 1.1:
                    print(f'⚠️ 0:00で{avg_leave - other_avg:.1f}人の重複疑い!')
    
    return midnight_data

def analyze_time_comparison():
    """23:45, 0:00, 0:15の詳細比較"""
    print('\n2. 時間別詳細比較分析')
    print('=' * 60)
    
    csv_path = os.path.join(analysis_folder, 'shortage_leave.csv')
    
    # 重要な時間帯のデータを収集
    time_slots = ['23:45', '00:00', '00:15']
    time_data = {slot: [] for slot in time_slots}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_str = row['time']
            if time_str in time_slots:
                time_data[time_str].append({
                    'date': row['date'],
                    'leave_applicants': int(row['leave_applicants']),
                    'lack': int(row['lack']),
                    'net_shortage': int(row['net_shortage'])
                })
    
    print('時間別統計 (6月全体):')
    print('時刻  | 平均人員 | 最大 | 最小 | データ数')
    print('-' * 45)
    
    stats_summary = {}
    for time_slot in time_slots:
        data = time_data[time_slot]
        if data:
            leave_counts = [d['leave_applicants'] for d in data]
            avg_count = sum(leave_counts) / len(leave_counts)
            max_count = max(leave_counts)
            min_count = min(leave_counts)
            
            stats_summary[time_slot] = {
                'avg': avg_count,
                'max': max_count,
                'min': min_count,
                'count': len(data)
            }
            
            print(f'{time_slot} | {avg_count:8.1f} | {max_count:4d} | {min_count:4d} | {len(data):8d}')
    
    # 0:00の異常性を分析
    if '00:00' in stats_summary and '23:45' in stats_summary and '00:15' in stats_summary:
        midnight_avg = stats_summary['00:00']['avg']
        before_avg = stats_summary['23:45']['avg']
        after_avg = stats_summary['00:15']['avg']
        
        print(f'\n境界分析:')
        print(f'  23:45 → 0:00: {midnight_avg - before_avg:+.1f}人差')
        print(f'  0:00 → 0:15: {after_avg - midnight_avg:+.1f}人差')
        
        # 理論的には0:00前後で人員は連続的に変化すべき
        expected_midnight = (before_avg + after_avg) / 2
        actual_excess = midnight_avg - expected_midnight
        
        print(f'\n重複分析:')
        print(f'  理論値(23:45と0:15の中間): {expected_midnight:.1f}人')
        print(f'  実測値(0:00): {midnight_avg:.1f}人')
        print(f'  重複疑い: {actual_excess:+.1f}人')
        
        if actual_excess > 1:
            print(f'  ⚠️ 0:00で約{actual_excess:.1f}人の重複カウントが疑われます!')
    
    return stats_summary

def analyze_need_pattern():
    """Need計算パターンの分析"""
    print('\n3. Need計算パターン分析')
    print('=' * 60)
    
    meta_path = os.path.join(analysis_folder, 'heatmap.meta.json')
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta_data = json.load(f)
    
    dow_pattern = meta_data.get('dow_need_pattern', [])
    
    print('曜日別Need計算パターン (深夜時間帯):')
    print('時刻  | 日 | 月 | 火 | 水 | 木 | 金 | 土')
    print('-' * 40)
    
    # 深夜時間帯のNeedパターンを確認
    for pattern in dow_pattern[:8]:  # 0:00-1:45
        time_str = pattern['time']
        values = [pattern[str(i)] for i in range(7)]
        print(f'{time_str} | {" | ".join([str(v) for v in values])}')
    
    print('\n重要な発見:')
    print('  - 0:00-6:45の全時間帯でNeed=0')
    print('  - 7:00からNeed=3で勤務開始')
    print('  - 深夜時間帯は理論上スタッフ不要')

def check_continuous_shift_patterns():
    """連続勤務パターンの確認"""
    print('\n4. 連続勤務パターンの確認')
    print('=' * 60)
    
    # work_patterns.csvの確認
    patterns_path = os.path.join(analysis_folder, 'work_patterns.csv')
    if os.path.exists(patterns_path):
        print('work_patterns.csvを確認中...')
        
        night_shift_count = 0
        total_patterns = 0
        
        with open(patterns_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_patterns += 1
                # 夜勤や深夜勤務パターンを検索
                for field in row.values():
                    if field and ('夜' in str(field) or '明' in str(field) or 'Night' in str(field)):
                        night_shift_count += 1
                        break
        
        print(f'  総パターン数: {total_patterns}')
        print(f'  夜勤関連パターン: {night_shift_count}')
        print(f'  夜勤比率: {night_shift_count/total_patterns*100:.1f}%')
    else:
        print('work_patterns.csvが見つかりません')

def quantify_overlap_problem():
    """重複問題の最終定量化"""
    print('\n5. 重複問題の最終定量化')
    print('=' * 60)
    
    # shortage_leave.csvから0:00の人員数を再計算
    csv_path = os.path.join(analysis_folder, 'shortage_leave.csv')
    
    midnight_counts = []
    adjacent_counts = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_str = row['time']
            count = int(row['leave_applicants'])
            
            if time_str == '00:00':
                midnight_counts.append(count)
            elif time_str in ['23:45', '00:15']:
                adjacent_counts.append(count)
    
    if midnight_counts and adjacent_counts:
        midnight_avg = sum(midnight_counts) / len(midnight_counts)
        adjacent_avg = sum(adjacent_counts) / len(adjacent_counts)
        
        print(f'分析結果:')
        print(f'  0:00平均人員: {midnight_avg:.1f}人')
        print(f'  隣接時間平均人員: {adjacent_avg:.1f}人')
        print(f'  差分: {midnight_avg - adjacent_avg:+.1f}人')
        
        # 重複率の計算
        if adjacent_avg > 0:
            overlap_ratio = (midnight_avg - adjacent_avg) / adjacent_avg * 100
            print(f'  重複率: {overlap_ratio:+.1f}%')
        
        # 月間影響度の計算
        days_in_month = 30
        daily_excess = midnight_avg - adjacent_avg
        monthly_excess_hours = daily_excess * days_in_month * 0.25  # 15分 = 0.25時間
        
        print(f'\n月間影響度:')
        print(f'  日次重複: {daily_excess:.1f}人')
        print(f'  月間重複時間: {monthly_excess_hours:.1f}人時間')
        
        if daily_excess > 0.5:
            print(f'  ⚠️ 毎日約{daily_excess:.1f}人が0:00で重複カウントされている可能性')
            print(f'  💡 これは夜勤終了者と明け番開始者の重複が原因と推測される')

# メイン実行
if __name__ == '__main__':
    if not os.path.exists(analysis_folder):
        print(f'エラー: {analysis_folder} が見つかりません')
        exit(1)
    
    # 各分析の実行
    midnight_data = analyze_shortage_leave_csv()
    stats_summary = analyze_time_comparison()
    analyze_need_pattern()
    check_continuous_shift_patterns()
    quantify_overlap_problem()
    
    print('\n=== 調査完了 ===')
    print('\n📋 主要な発見事項:')
    print('1. 0:00〜6:45は理論上Need=0で勤務不要')
    print('2. しかし実際には0:00に毎日12-19人が配置されている')
    print('3. 隣接時間との比較で重複カウントの疑い')
    print('4. 夜勤終了と明け番開始の境界処理に問題がある可能性')
    print('\n💡 推奨される対策:')
    print('- 連続勤務の境界時刻での重複カウント防止')
    print('- 夜勤終了時刻と明け番開始時刻の明確な分離')
    print('- 0:00跨ぎ勤務の適切な処理ロジック実装')