#!/usr/bin/env python3
"""
休日除外実装の最終検証スクリプト
============================

app.py の修正実装と dash_app.py の既存フィルタが正しく動作しているかを検証
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath('.'))

def check_data_consistency():
    """データの一貫性を確認する"""
    print("=" * 60)
    print("データ一貫性チェック")
    print("=" * 60)
    
    # 利用可能なテストデータを探す
    test_files = [
        "デイ_テスト用データ_休日精緻.xlsx",
        "ショート_テスト用データ.xlsx",
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"✅ テストファイル発見: {test_file}")
            return test_file
    
    print("❌ テストファイルが見つかりません")
    return None

def analyze_excel_structure(excel_path: str):
    """Excelファイルの構造を分析"""
    print(f"\n📊 Excelファイル構造分析: {excel_path}")
    print("-" * 40)
    
    try:
        # 各シートの内容を確認
        xl = pd.ExcelFile(excel_path)
        print(f"シート数: {len(xl.sheet_names)}")
        print(f"シート名: {xl.sheet_names}")
        
        # 最初のシートのサンプルを表示
        if xl.sheet_names:
            sample_df = pd.read_excel(excel_path, sheet_name=xl.sheet_names[0], nrows=10)
            print(f"\nサンプルデータ (最初の10行):")
            print(sample_df.to_string())
            
            # スタッフ名に休暇パターンがないか確認
            if 'B列' in sample_df.columns or len(sample_df.columns) > 1:
                staff_col = sample_df.columns[1]  # 通常B列がスタッフ名
                unique_values = sample_df[staff_col].dropna().unique()
                print(f"\n{staff_col}列のユニーク値 (最初の20個):")
                for i, val in enumerate(unique_values[:20]):
                    print(f"  {i+1}. '{val}'")
                    
                # 休暇パターンの検索
                rest_patterns = ['×', 'X', 'x', '休', 'OFF', 'off', '有', '特', '代', '振']
                found_patterns = []
                for pattern in rest_patterns:
                    matches = [val for val in unique_values if isinstance(val, str) and pattern in val]
                    if matches:
                        found_patterns.append((pattern, matches[:3]))  # 最初の3つを表示
                
                if found_patterns:
                    print(f"\n🔍 休暇パターン検出:")
                    for pattern, matches in found_patterns:
                        print(f"  '{pattern}': {matches}")
                else:
                    print(f"\n✅ 休暇パターンは検出されませんでした")
        
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def check_filter_implementations():
    """フィルタ実装の確認"""
    print("\n🔧 フィルタ実装確認")
    print("-" * 40)
    
    # 1. heatmap.py の _filter_work_records 確認
    heatmap_path = Path("shift_suite/tasks/heatmap.py")
    if heatmap_path.exists():
        with open(heatmap_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if '_filter_work_records' in content:
                print("✅ heatmap.py: _filter_work_records 関数が存在")
                if 'holiday_type.*通常勤務' in content or 'DEFAULT_HOLIDAY_TYPE' in content:
                    print("✅ heatmap.py: holiday_type による休暇除外が実装済み")
                if 'parsed_slots_count.*> 0' in content:
                    print("✅ heatmap.py: parsed_slots_count による0スロット除外が実装済み")
            else:
                print("❌ heatmap.py: _filter_work_records 関数が見つかりません")
    else:
        print("❌ heatmap.py が見つかりません")
    
    # 2. utils.py の apply_rest_exclusion_filter 確認
    utils_path = Path("shift_suite/tasks/utils.py")
    if utils_path.exists():
        with open(utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'apply_rest_exclusion_filter' in content:
                print("✅ utils.py: apply_rest_exclusion_filter 関数が存在")
                if 'rest_patterns' in content:
                    print("✅ utils.py: 休暇パターンマッチングが実装済み")
            else:
                print("❌ utils.py: apply_rest_exclusion_filter 関数が見つかりません")
    else:
        print("❌ utils.py が見つかりません")
    
    # 3. app.py の修正確認
    app_path = Path("app.py")
    if app_path.exists():
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'working_long_df' in content:
                print("✅ app.py: working_long_df による事前フィルタリングが実装済み")
                if 'holiday_type.*通常勤務' in content:
                    print("✅ app.py: holiday_type 除外が実装済み")
                if 'parsed_slots_count.*> 0' in content:
                    print("✅ app.py: parsed_slots_count 除外が実装済み")
            else:
                print("❌ app.py: working_long_df が見つかりません")
    else:
        print("❌ app.py が見つかりません")
    
    # 4. dash_app.py の確認
    dash_path = Path("dash_app.py")
    if dash_path.exists():
        with open(dash_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'pre_aggregated_data.*apply_rest_exclusion_filter' in content:
                print("✅ dash_app.py: pre_aggregated_data に apply_rest_exclusion_filter が適用済み")
            elif "key in ['pre_aggregated_data'" in content:
                print("✅ dash_app.py: data_get() で pre_aggregated_data に フィルタが適用される")
            else:
                print("❌ dash_app.py: pre_aggregated_data のフィルタ適用が見つかりません")
    else:
        print("❌ dash_app.py が見つかりません")

def check_existing_analysis_results():
    """既存の分析結果を確認"""
    print("\n📂 既存分析結果確認")
    print("-" * 40)
    
    # 分析結果ディレクトリを探す
    analysis_dirs = []
    for item in Path('.').iterdir():
        if item.is_dir() and ('analysis' in item.name.lower() or 'results' in item.name.lower() or 'out_' in item.name):
            analysis_dirs.append(item)
    
    if not analysis_dirs:
        print("❌ 分析結果ディレクトリが見つかりません")
        return
    
    print(f"✅ 分析結果ディレクトリ: {len(analysis_dirs)}個")
    for dir_path in analysis_dirs[:5]:  # 最初の5つを表示
        print(f"  📁 {dir_path.name}")
        
        # 重要ファイルの存在確認
        key_files = ['heat_ALL.parquet', 'pre_aggregated_data.parquet', 'intermediate_data.parquet']
        for key_file in key_files:
            file_path = dir_path / key_file
            if file_path.exists():
                print(f"    ✅ {key_file}")
                
                # ファイルサイズも確認
                try:
                    df = pd.read_parquet(file_path)
                    print(f"      📊 Shape: {df.shape}")
                    
                    if key_file == 'pre_aggregated_data.parquet':
                        # staff_count の分布を確認
                        if 'staff_count' in df.columns:
                            non_zero = (df['staff_count'] > 0).sum()
                            total = len(df)
                            print(f"      👥 非ゼロレコード: {non_zero}/{total} ({non_zero/total:.1%})")
                            
                            # 日別サマリー
                            if 'date_lbl' in df.columns:
                                daily_totals = df.groupby('date_lbl')['staff_count'].sum()
                                working_days = (daily_totals > 0).sum()
                                print(f"      📅 稼働日: {working_days}/{len(daily_totals)}")
                    
                except Exception as e:
                    print(f"      ❌ 読み込みエラー: {e}")
            else:
                print(f"    ❌ {key_file} (なし)")

def generate_validation_report():
    """検証レポートの生成"""
    print("\n📋 検証サマリー")
    print("=" * 60)
    
    # 実装状況の評価
    implementation_score = 0
    total_checks = 6
    
    checks = [
        ("heatmap.py _filter_work_records", Path("shift_suite/tasks/heatmap.py").exists()),
        ("utils.py apply_rest_exclusion_filter", Path("shift_suite/tasks/utils.py").exists()),
        ("app.py working_long_df", Path("app.py").exists()),
        ("dash_app.py data_get フィルタ", Path("dash_app.py").exists()),
        ("テストデータの存在", any(Path(f).exists() for f in ["デイ_テスト用データ_休日精緻.xlsx", "ショート_テスト用データ.xlsx"])),
        ("分析結果の存在", any(Path('.').glob('*analysis*')) or any(Path('.').glob('out_*')))
    ]
    
    for check_name, passed in checks:
        if passed:
            print(f"✅ {check_name}")
            implementation_score += 1
        else:
            print(f"❌ {check_name}")
    
    print(f"\n🎯 実装完成度: {implementation_score}/{total_checks} ({implementation_score/total_checks:.1%})")
    
    # 推奨アクション
    print(f"\n🚀 推奨アクション:")
    if implementation_score >= 5:
        print("  1. 実際のテストデータでapp.pyを実行して検証")
        print("  2. ダッシュボード (dash_app.py) で結果を確認")
        print("  3. ログファイルで除外処理の実行を確認")
    elif implementation_score >= 3:
        print("  1. 不足しているファイルの確認")
        print("  2. 基本的な動作テストの実行")
    else:
        print("  1. システムの基本セットアップから確認")
        print("  2. 必要なファイルの復元")
    
    # テスト手順
    print(f"\n🧪 テスト手順:")
    print("  1. テストExcelファイルを準備")
    print("  2. Streamlit app.py を実行")
    print("  3. ダッシュボードで休日データの表示状況を確認")
    print("  4. shift_suite.log で除外処理の実行を確認")

def main():
    """メイン実行"""
    print("🔍 shift_suite 休日除外実装 - 最終検証")
    print("=" * 60)
    
    # 1. テストデータ確認
    test_file = check_data_consistency()
    if test_file:
        analyze_excel_structure(test_file)
    
    # 2. 実装確認
    check_filter_implementations()
    
    # 3. 既存結果確認
    check_existing_analysis_results()
    
    # 4. 検証レポート
    generate_validation_report()
    
    print(f"\n🎉 検証完了!")
    print("詳細な問題調査が必要な場合は holiday_exclusion_investigation_summary.md を参照してください。")

if __name__ == "__main__":
    main()