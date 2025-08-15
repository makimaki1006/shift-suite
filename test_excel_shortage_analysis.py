#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
3つのテストExcelファイルで過不足分析ロジックの詳細検証
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from pathlib import Path
import json
import datetime as dt

# shift_suite のインポート
from shift_suite.tasks.io_excel import ingest_excel
from shift_suite.tasks.shortage import calculate_shortage_detailed, calculate_shortage_summary

def test_excel_file_shortage_analysis(excel_path: str, test_name: str):
    """個別Excelファイルの過不足分析テスト"""
    print(f"\n{'='*80}")
    print(f"【{test_name}】過不足分析テスト")
    print(f"ファイル: {excel_path}")
    print(f"{'='*80}")
    
    excel_path = Path(excel_path)
    if not excel_path.exists():
        print(f"❌ ファイルが存在しません: {excel_path}")
        return None
    
    try:
        # Excelファイルの詳細情報を取得
        excel_info = pd.ExcelFile(excel_path)
        sheets = excel_info.sheet_names
        print(f"📊 シート一覧: {sheets}")
        
        # 勤務区分シートの確認
        if "勤務区分" not in sheets:
            print("❌ '勤務区分' シートが見つかりません")
            return None
            
        # 実績シートの特定（勤務区分以外のシート）
        shift_sheets = [s for s in sheets if s != "勤務区分"]
        print(f"📋 実績シート: {shift_sheets}")
        
        if not shift_sheets:
            print("❌ 実績シートが見つかりません")
            return None
        
        # 勤務区分シートの内容確認
        pattern_df = pd.read_excel(excel_path, sheet_name="勤務区分")
        print(f"🏢 勤務区分データ: {pattern_df.shape}")
        print(f"   勤務パターン数: {len(pattern_df)}")
        
        # 各実績シートの処理
        results = {}
        for sheet_name in shift_sheets:
            print(f"\n--- {sheet_name} シート分析 ---")
            
            try:
                # データ読み込み
                long_df, wt_df, unknown_codes = ingest_excel(
                    excel_path,
                    shift_sheets=[sheet_name],
                    header_row=0,
                    slot_minutes=30
                )
                
                print(f"✅ データ読み込み成功")
                print(f"   長形式データ: {long_df.shape}")
                print(f"   期間: {long_df['ds'].min()} ～ {long_df['ds'].max()}")
                print(f"   スタッフ数: {long_df['staff'].nunique()}")
                print(f"   職種数: {long_df['role'].nunique()}")
                print(f"   未知コード: {unknown_codes}")
                
                # 日別スタッフ数の確認
                daily_staff = long_df.groupby(long_df['ds'].dt.date)['staff'].nunique()
                print(f"   日別スタッフ数統計:")
                print(f"     平均: {daily_staff.mean():.1f}人")
                print(f"     最大: {daily_staff.max()}人")
                print(f"     最小: {daily_staff.min()}人")
                
                # 勤務時間統計
                work_hours = long_df.groupby(['staff', long_df['ds'].dt.date]).size() * 0.5
                print(f"   日別勤務時間統計:")
                print(f"     平均: {work_hours.mean():.1f}時間/人・日")
                print(f"     最大: {work_hours.max():.1f}時間/人・日")
                
                # 休暇データの確認
                holiday_data = long_df[long_df['holiday_type'] != '通常勤務']
                if not holiday_data.empty:
                    holiday_stats = holiday_data['holiday_type'].value_counts()
                    print(f"   休暇データ:")
                    for holiday_type, count in holiday_stats.items():
                        print(f"     {holiday_type}: {count}件")
                
                # 過不足分析用のテストデータを作成
                # 簡単なNeedデータを生成（実際の運用では外部から提供される）
                date_range = pd.date_range(
                    start=long_df['ds'].min().date(),
                    end=long_df['ds'].max().date(),
                    freq='D'
                )
                
                # 時間帯ラベル（30分間隔）
                time_slots = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]
                
                # 簡単なNeedマトリックス（実際より少なめに設定）
                need_matrix = np.random.randint(1, 4, size=(len(time_slots), len(date_range)))
                need_df = pd.DataFrame(
                    need_matrix,
                    index=time_slots,
                    columns=[d.strftime("%Y-%m-%d") for d in date_range]
                )
                
                print(f"   生成したNeedデータ: {need_df.shape}")
                print(f"   Need総計: {need_df.sum().sum():.0f}スロット")
                
                # 実績データをマトリックス形式に変換
                actual_pivot = long_df.pivot_table(
                    index=long_df['ds'].dt.strftime('%H:%M'),
                    columns=long_df['ds'].dt.strftime('%Y-%m-%d'),
                    values='staff',
                    aggfunc='nunique',
                    fill_value=0
                )
                
                print(f"   実績マトリックス: {actual_pivot.shape}")
                print(f"   実績総計: {actual_pivot.sum().sum():.0f}スロット")
                
                # 過不足計算
                common_dates = set(need_df.columns) & set(actual_pivot.columns)
                common_times = set(need_df.index) & set(actual_pivot.index)
                
                print(f"   共通日付: {len(common_dates)}日")
                print(f"   共通時間帯: {len(common_times)}時間帯")
                
                if common_dates and common_times:
                    # 共通部分で過不足計算
                    common_dates_sorted = sorted(common_dates)
                    common_times_sorted = sorted(common_times)
                    
                    need_common = need_df.loc[common_times_sorted, common_dates_sorted]
                    actual_common = actual_pivot.loc[common_times_sorted, common_dates_sorted]
                    
                    shortage = need_common - actual_common
                    shortage = shortage.clip(lower=0)  # 負の値は0にクリップ
                    
                    total_shortage_slots = shortage.sum().sum()
                    total_shortage_hours = total_shortage_slots * 0.5
                    
                    print(f"   🎯 過不足分析結果:")
                    print(f"     総不足スロット: {total_shortage_slots:.0f}")
                    print(f"     総不足時間: {total_shortage_hours:.1f}時間")
                    print(f"     日平均不足: {total_shortage_hours / len(common_dates):.1f}時間/日")
                    
                    # 期間依存性の確認
                    period_days = len(common_dates)
                    if period_days > 30:
                        months = period_days / 30
                        monthly_shortage = total_shortage_hours / months
                        print(f"     期間: {period_days}日 ({months:.1f}ヶ月)")
                        print(f"     月平均不足: {monthly_shortage:.1f}時間/月")
                        if monthly_shortage > 3000:
                            print(f"     ⚠️ 警告: 月平均不足が3000時間を超過 - 期間依存問題の可能性")
                    
                    results[sheet_name] = {
                        'period_days': period_days,
                        'total_shortage_hours': total_shortage_hours,
                        'daily_avg_shortage': total_shortage_hours / period_days,
                        'monthly_avg_shortage': total_shortage_hours / (period_days / 30) if period_days > 0 else 0,
                        'staff_count': long_df['staff'].nunique(),
                        'data_shape': long_df.shape,
                        'date_range': f"{long_df['ds'].min()} - {long_df['ds'].max()}"
                    }
                
            except Exception as e:
                print(f"❌ {sheet_name} シートの処理エラー: {e}")
                import traceback
                traceback.print_exc()
        
        return results
        
    except Exception as e:
        print(f"❌ ファイル処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン実行関数"""
    print("🔍 Excelデータ読み込みから過不足分析の徹底検証")
    
    # テストファイルのパス
    test_files = [
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\ショート_テスト用データ.xlsx",
            'name': "ショート_テスト用データ"
        },
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\デイ_テスト用データ_休日精緻.xlsx",
            'name': "デイ_テスト用データ"
        },
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\テストデータ_2024 本木ショート（7～9月）.xlsx",
            'name': "本木ショート（3ヶ月）"
        }
    ]
    
    all_results = {}
    
    for test_file in test_files:
        result = test_excel_file_shortage_analysis(test_file['path'], test_file['name'])
        if result:
            all_results[test_file['name']] = result
    
    # 結果の比較分析
    print(f"\n{'='*80}")
    print("📊 結果比較分析")
    print(f"{'='*80}")
    
    for test_name, test_results in all_results.items():
        print(f"\n【{test_name}】")
        for sheet_name, metrics in test_results.items():
            print(f"  {sheet_name}:")
            print(f"    期間: {metrics['period_days']}日")
            print(f"    総不足時間: {metrics['total_shortage_hours']:.1f}時間")
            print(f"    日平均不足: {metrics['daily_avg_shortage']:.1f}時間/日")
            print(f"    月平均不足: {metrics['monthly_avg_shortage']:.1f}時間/月")
            print(f"    スタッフ数: {metrics['staff_count']}人")
    
    # 3ヶ月データの異常検出
    if "本木ショート（3ヶ月）" in all_results:
        print(f"\n🚨 3ヶ月データの異常検出:")
        three_month_data = all_results["本木ショート（3ヶ月）"]
        for sheet_name, metrics in three_month_data.items():
            if metrics['monthly_avg_shortage'] > 5000:
                print(f"  ❌ {sheet_name}: 月平均{metrics['monthly_avg_shortage']:.0f}時間は異常値")
                print(f"      期間依存性問題の可能性が高い")
            elif metrics['monthly_avg_shortage'] > 2000:
                print(f"  ⚠️ {sheet_name}: 月平均{metrics['monthly_avg_shortage']:.0f}時間は要注意")
            else:
                print(f"  ✅ {sheet_name}: 月平均{metrics['monthly_avg_shortage']:.0f}時間は正常範囲")
    
    # 結果をJSONファイルに保存
    output_file = Path(__file__).parent / "excel_shortage_analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 結果を保存しました: {output_file}")

if __name__ == "__main__":
    main()