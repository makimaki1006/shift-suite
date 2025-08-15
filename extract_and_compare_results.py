#!/usr/bin/env python3
"""
ZIPファイルから分析結果を抽出して比較
"""

import zipfile
import tempfile
import os
from pathlib import Path

def extract_summary_from_zip(zip_path):
    """ZIPファイルからサマリー情報を抽出"""
    results = {}
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 一時ディレクトリに展開
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_ref.extractall(temp_dir)
                
                # アウトプット.txtファイルを探す
                temp_path = Path(temp_dir)
                output_files = list(temp_path.rglob("*アウトプット.txt"))
                
                if output_files:
                    output_file = output_files[0]
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 総不足時間を抽出
                    lines = content.split('\n')
                    for line in lines:
                        if '総不足時間:' in line:
                            shortage_str = line.split('総不足時間:')[1].strip()
                            shortage_hours = float(shortage_str.replace('時間', ''))
                            results['total_shortage_hours'] = shortage_hours
                            break
                
                # シナリオ別結果を確認
                scenario_dirs = ['out_median_based', 'out_mean_based', 'out_p25_based']
                for scenario in scenario_dirs:
                    scenario_path = temp_path / scenario
                    if scenario_path.exists():
                        # アウトプット.txtを確認
                        scenario_output = scenario_path / "*アウトプット.txt"
                        scenario_files = list(scenario_path.glob("*アウトプット.txt"))
                        if scenario_files:
                            with open(scenario_files[0], 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # シナリオ別の総不足時間を抽出
                            for line in content.split('\n'):
                                if '総不足時間:' in line:
                                    shortage_str = line.split('総不足時間:')[1].strip()
                                    shortage_hours = float(shortage_str.replace('時間', ''))
                                    results[f'{scenario}_shortage_hours'] = shortage_hours
                                    break
                
    except Exception as e:
        print(f"エラー: {zip_path} - {e}")
        
    return results

def compare_all_results():
    """全ZIPファイルの結果を比較"""
    
    zip_files = {
        '3ヶ月一気': '3か月一気に.zip',
        '7月分': '7月分.zip',
        '8月分': '8月分.zip', 
        '9月分': '9月分.zip'
    }
    
    all_results = {}
    
    print("🔍 === ZIPファイル分析結果の抽出 ===\n")
    
    for name, zip_file in zip_files.items():
        if Path(zip_file).exists():
            print(f"📁 {name} ({zip_file}) を分析中...")
            results = extract_summary_from_zip(zip_file)
            all_results[name] = results
            
            if results:
                print(f"  ✅ 結果抽出成功")
                for key, value in results.items():
                    print(f"    {key}: {value:.1f}時間")
            else:
                print(f"  ❌ 結果抽出失敗")
            print()
        else:
            print(f"❌ {zip_file} が見つかりません\n")
    
    # 比較分析
    if len(all_results) >= 2:
        print("📊 === 比較分析 ===\n")
        
        # 月別合計の計算
        monthly_total = 0
        monthly_count = 0
        
        for name in ['7月分', '8月分', '9月分']:
            if name in all_results and 'total_shortage_hours' in all_results[name]:
                monthly_total += all_results[name]['total_shortage_hours']
                monthly_count += 1
        
        if '3ヶ月一気' in all_results and 'total_shortage_hours' in all_results['3ヶ月一気']:
            cumulative_total = all_results['3ヶ月一気']['total_shortage_hours']
            
            print(f"🔢 数値比較:")
            print(f"  月別合計: {monthly_total:.1f}時間 ({monthly_count}ヶ月分)")
            print(f"  3ヶ月一気: {cumulative_total:.1f}時間")
            print(f"  差異: {abs(cumulative_total - monthly_total):.1f}時間")
            print(f"  差異率: {abs(cumulative_total - monthly_total) / monthly_total * 100:.1f}%")
            
            if abs(cumulative_total - monthly_total) / monthly_total > 0.1:  # 10%以上の差
                print(f"\n⚠️ 重大な差異検出！")
                print(f"   → 分析ロジックに期間依存性があります")
            else:
                print(f"\n✅ 妥当な範囲内の差異")

if __name__ == "__main__":
    compare_all_results()