#!/usr/bin/env python3
"""
客観的一貫性チェック
プロの観点で全システムの動的一貫性を検証
"""

import pandas as pd
from pathlib import Path
import sys
import os
import numpy as np
from datetime import datetime, timedelta
import traceback

# パスを追加
sys.path.insert(0, os.getcwd())

def objective_consistency_check():
    """客観的な一貫性チェック"""
    print("=== 客観的一貫性チェック（プロ観点） ===")
    
    # 1. システム環境と基本構成の確認
    print("\n【1. システム環境確認】")
    current_dir = Path.cwd()
    print(f"作業ディレクトリ: {current_dir}")
    
    # 重要ファイルの存在確認
    critical_files = {
        "Excel入力": "ショート_テスト用データ.xlsx",
        "ダッシュボード": "dash_app.py", 
        "データ処理": "shift_suite/tasks/io_excel.py",
        "設定": "shift_suite/tasks/utils.py"
    }
    
    file_status = {}
    for name, filepath in critical_files.items():
        path = Path(filepath)
        exists = path.exists()
        file_status[name] = {
            "exists": exists,
            "path": str(path),
            "size": path.stat().st_size if exists else 0
        }
        status = "✅" if exists else "❌"
        print(f"  {status} {name}: {filepath}")
    
    # 2. データ整合性の動的検証
    print("\n【2. データ整合性動的検証】")
    
    try:
        # shift_suiteが正常にインポートできるか
        from shift_suite.tasks.io_excel import ingest_excel
        print("✅ shift_suite.tasks.io_excel インポート成功")
        
        excel_path = Path("ショート_テスト用データ.xlsx")
        if not excel_path.exists():
            print("❌ 入力Excelファイルが見つかりません")
            return
        
        # 実際のデータ処理を実行
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        sheet_names = excel_file.sheet_names
        shift_sheets = [s for s in sheet_names if "勤務" not in s]
        
        print(f"✅ Excelファイル読み込み成功: {len(sheet_names)}シート")
        print(f"  - 実績シート: {shift_sheets}")
        
        # データ処理実行
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=30,
            year_month_cell_location="D1"
        )
        
        print(f"✅ データ処理成功:")
        print(f"  - 生成レコード数: {len(long_df):,}")
        print(f"  - 勤務パターン数: {len(wt_df)}")
        print(f"  - 未知コード数: {len(unknown_codes)}")
        
    except Exception as e:
        print(f"❌ データ処理エラー: {e}")
        traceback.print_exc()
        return
    
    # 3. データ品質の客観的評価
    print("\n【3. データ品質客観的評価】")
    
    # 基本統計
    total_records = len(long_df)
    working_records = len(long_df[long_df['holiday_type'] == '通常勤務'])
    leave_records = total_records - working_records
    
    print(f"基本統計:")
    print(f"  - 総レコード数: {total_records:,}")
    print(f"  - 勤務レコード: {working_records:,} ({working_records/total_records*100:.1f}%)")
    print(f"  - 休暇レコード: {leave_records:,} ({leave_records/total_records*100:.1f}%)")
    
    # データの完整性チェック
    working_data = long_df[long_df['holiday_type'] == '通常勤務'].copy()
    
    # 日付範囲の一貫性
    dates = pd.to_datetime(working_data['ds']).dt.date.unique()
    date_range = pd.date_range(start=dates.min(), end=dates.max(), freq='D')
    expected_days = len(date_range)
    actual_days = len(dates)
    
    print(f"\n日付整合性:")
    print(f"  - 期待日数: {expected_days}日")
    print(f"  - 実際日数: {actual_days}日")
    print(f"  - 整合性: {'✅' if actual_days == expected_days else '❌'}")
    
    # 時間スロットの一貫性
    working_data['time_slot'] = pd.to_datetime(working_data['ds']).dt.strftime('%H:%M')
    unique_slots = sorted(working_data['time_slot'].unique())
    expected_slots = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]
    
    print(f"\n時間スロット整合性:")
    print(f"  - 期待スロット数: {len(expected_slots)}")
    print(f"  - 実際スロット数: {len(unique_slots)}")
    print(f"  - 整合性: {'✅' if len(unique_slots) <= len(expected_slots) else '❌'}")
    
    # 4. 夜勤・明番の整合性確認
    print("\n【4. 夜勤・明番整合性確認】")
    
    # 明番コードの存在確認
    dawn_data = working_data[working_data['code'] == '明']
    print(f"明番「明」レコード数: {len(dawn_data)}")
    
    if len(dawn_data) > 0:
        dawn_data['hour'] = pd.to_datetime(dawn_data['ds']).dt.hour
        dawn_hours = dawn_data['hour'].value_counts().sort_index()
        print("明番時間分布:")
        for hour, count in dawn_hours.items():
            print(f"  - {hour:02d}時台: {count}レコード")
        
        # 夜勤時間帯（0-5時）での明番カバー率
        night_hours = [0, 1, 2, 3, 4, 5]
        night_dawn = dawn_data[dawn_data['hour'].isin(night_hours)]
        total_night_slots = len(night_hours) * actual_days  # 6時間 × 日数
        dawn_coverage = len(night_dawn) / total_night_slots * 100 if total_night_slots > 0 else 0
        
        print(f"夜勤時間帯明番カバー率: {dawn_coverage:.1f}%")
        print(f"整合性: {'✅' if dawn_coverage > 0 else '❌'}")
    else:
        print("❌ 明番データが存在しません")
    
    # 5. 職種・雇用形態の一貫性
    print("\n【5. 職種・雇用形態一貫性】")
    
    # 職種分析
    roles = working_data['role'].value_counts()
    print(f"職種数: {len(roles)}")
    print("職種分布:")
    for role, count in roles.items():
        percentage = count / len(working_data) * 100
        print(f"  - {role}: {count:,}レコード ({percentage:.1f}%)")
    
    # 雇用形態分析
    employments = working_data['employment'].value_counts()
    print(f"\n雇用形態数: {len(employments)}")
    print("雇用形態分布:")
    for emp, count in employments.items():
        percentage = count / len(working_data) * 100
        print(f"  - {emp}: {count:,}レコード ({percentage:.1f}%)")
    
    # クロス集計による整合性確認
    cross_table = pd.crosstab(working_data['role'], working_data['employment'], margins=True)
    print(f"\n職種×雇用形態クロス集計:")
    print(cross_table)
    
    # 6. 計算ロジックの一貫性検証
    print("\n【6. 計算ロジック一貫性検証】")
    
    # シナリオ計算の一貫性
    working_data['date'] = pd.to_datetime(working_data['ds']).dt.date
    daily_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
    
    # 各シナリオでの一貫性確認
    scenarios = ['median', 'mean', '25th_percentile']
    scenario_results = {}
    
    for scenario in scenarios:
        if scenario == 'median':
            scenario_values = daily_counts.groupby('time_slot')['count'].median()
        elif scenario == 'mean':
            scenario_values = daily_counts.groupby('time_slot')['count'].mean()
        else:  # 25th_percentile
            scenario_values = daily_counts.groupby('time_slot')['count'].quantile(0.25)
        
        total_demand = scenario_values.sum() * 0.5  # 30分スロット = 0.5時間
        scenario_results[scenario] = total_demand
        
        print(f"{scenario}シナリオ総需要: {total_demand:.1f}時間")
    
    # 7. dash_app.py の整合性確認
    print("\n【7. ダッシュボード整合性確認】")
    
    dash_path = Path("dash_app.py")
    if dash_path.exists():
        print("✅ dash_app.py 存在確認")
        
        try:
            with open(dash_path, 'r', encoding='utf-8') as f:
                dash_content = f.read()
            
            # 重要な関数・変数の存在確認
            critical_elements = [
                'create_shortage_from_heat_all',
                'shortage',
                'excess', 
                'scenario',
                '@app.callback'
            ]
            
            element_status = {}
            for element in critical_elements:
                exists = element in dash_content
                element_status[element] = exists
                status = "✅" if exists else "❌"
                print(f"  {status} {element}")
            
            # コールバック数の確認
            callback_count = dash_content.count('@app.callback')
            print(f"  - コールバック関数数: {callback_count}")
            
        except Exception as e:
            print(f"❌ dash_app.py 読み込みエラー: {e}")
    else:
        print("❌ dash_app.py が見つかりません")
    
    # 8. システム全体の整合性評価
    print("\n【8. システム全体整合性評価】")
    
    consistency_checks = {
        "ファイル存在": all(fs["exists"] for fs in file_status.values()),
        "データ処理": total_records > 0,
        "日付整合性": actual_days == expected_days,
        "時間整合性": len(unique_slots) <= len(expected_slots),
        "明番データ": len(dawn_data) > 0,
        "職種データ": len(roles) > 0,
        "雇用形態データ": len(employments) > 0,
        "ダッシュボード": dash_path.exists()
    }
    
    print("整合性チェック結果:")
    passed_checks = 0
    total_checks = len(consistency_checks)
    
    for check_name, result in consistency_checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {check_name}")
        if result:
            passed_checks += 1
    
    overall_score = passed_checks / total_checks * 100
    print(f"\n総合整合性スコア: {passed_checks}/{total_checks} ({overall_score:.1f}%)")
    
    # 9. 潜在的問題の特定
    print("\n【9. 潜在的問題特定】")
    
    potential_issues = []
    
    # データ量の妥当性チェック
    if total_records < 1000:
        potential_issues.append(f"データ量が少ない可能性 ({total_records:,}レコード)")
    
    # 勤務・休暇比率の妥当性
    work_ratio = working_records / total_records * 100
    if work_ratio < 80:
        potential_issues.append(f"勤務比率が低い可能性 ({work_ratio:.1f}%)")
    
    # 職種の偏りチェック
    max_role_ratio = roles.max() / len(working_data) * 100
    if max_role_ratio > 50:
        potential_issues.append(f"特定職種への集中 (最大{max_role_ratio:.1f}%)")
    
    # シナリオ間の差異チェック
    scenario_range = max(scenario_results.values()) - min(scenario_results.values())
    if scenario_range > 100:  # 100時間以上の差
        potential_issues.append(f"シナリオ間の差異が大きい ({scenario_range:.1f}時間)")
    
    if potential_issues:
        print("検出された潜在的問題:")
        for issue in potential_issues:
            print(f"  ⚠️ {issue}")
    else:
        print("✅ 重大な潜在的問題は検出されませんでした")
    
    # 10. 推奨アクション
    print("\n【10. 推奨アクション】")
    
    if overall_score >= 90:
        print("🟢 システムは概ね健全です")
        print("推奨アクション:")
        print("  - 定期的な監視継続")
        print("  - パフォーマンス最適化の検討")
    elif overall_score >= 70:
        print("🟡 軽微な問題があります")
        print("推奨アクション:")
        print("  - 失敗項目の個別調査")
        print("  - データ品質向上の検討")
    else:
        print("🔴 重大な問題があります")
        print("推奨アクション:")
        print("  - 緊急対応が必要")
        print("  - システム全体の見直し")
    
    print("\n=== 客観的一貫性チェック完了 ===")
    return {
        "overall_score": overall_score,
        "total_records": total_records,
        "working_records": working_records,
        "consistency_checks": consistency_checks,
        "potential_issues": potential_issues
    }

if __name__ == "__main__":
    result = objective_consistency_check()