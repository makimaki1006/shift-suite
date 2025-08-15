#!/usr/bin/env python3
"""
実データ分析結果の検証スクリプト
入力Excel と 出力ZIPファイルの内容を確認
"""

import pandas as pd
import zipfile
import json
from pathlib import Path
import os

def analyze_input_excel():
    """入力Excelファイルの概要確認"""
    print("=" * 80)
    print("1. 入力Excelファイルの確認")
    print("=" * 80)
    
    excel_path = "デイ_テスト用データ_休日精緻.xlsx"
    
    try:
        # Excelファイルの基本情報
        file_size = os.path.getsize(excel_path) / 1024
        print(f"ファイルサイズ: {file_size:.1f} KB")
        
        # シート名の確認
        xl_file = pd.ExcelFile(excel_path)
        sheet_names = xl_file.sheet_names
        print(f"シート数: {len(sheet_names)}")
        print(f"シート名: {sheet_names}")
        
        # 各シートの概要
        for sheet_name in sheet_names[:3]:  # 最初の3シートのみ
            print(f"\n--- シート: {sheet_name} ---")
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=5)
                print(f"行数: {len(pd.read_excel(excel_path, sheet_name=sheet_name))} (全体)")
                print(f"列数: {len(df.columns)}")
                print(f"列名: {list(df.columns)[:10]}...")  # 最初の10列
                
                # データ型の確認
                if 'code' in df.columns:
                    codes = pd.read_excel(excel_path, sheet_name=sheet_name)['code'].dropna().unique()
                    print(f"勤務コード種類: {len(codes)}種類")
                    print(f"サンプル: {list(codes)[:5]}")
                    
            except Exception as e:
                print(f"  エラー: {e}")
                
    except Exception as e:
        print(f"Excelファイル読み込みエラー: {e}")
        return False
    
    return True

def analyze_output_zip():
    """出力ZIPファイルの内容確認"""
    print("\n" + "=" * 80)
    print("2. 出力ZIPファイルの確認")
    print("=" * 80)
    
    zip_path = "analysis_results (55).zip"
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # ZIPファイルの内容一覧
            file_list = zip_file.namelist()
            print(f"ファイル数: {len(file_list)}")
            
            # ファイル種別ごとの集計
            file_types = {}
            for file_name in file_list:
                ext = Path(file_name).suffix
                file_types[ext] = file_types.get(ext, 0) + 1
            
            print("\nファイル種別:")
            for ext, count in sorted(file_types.items()):
                print(f"  {ext}: {count}ファイル")
            
            # 重要なファイルの確認
            print("\n--- 重要ファイルの内容確認 ---")
            
            # 1. 不足分析結果の確認
            shortage_files = [f for f in file_list if 'shortage' in f and f.endswith('.xlsx')]
            if shortage_files:
                print(f"\n不足分析ファイル: {len(shortage_files)}個")
                for shortage_file in shortage_files[:2]:
                    print(f"\n  {shortage_file}:")
                    try:
                        with zip_file.open(shortage_file) as f:
                            df = pd.read_excel(f)
                            print(f"    行数: {len(df)}")
                            if 'lack_h' in df.columns:
                                total_shortage = df['lack_h'].sum()
                                max_shortage = df['lack_h'].max()
                                print(f"    総不足時間: {total_shortage:.2f}時間")
                                print(f"    最大不足時間: {max_shortage:.2f}時間")
                                print(f"    平均不足時間: {df['lack_h'].mean():.2f}時間")
                                
                                # 異常値チェック
                                if total_shortage > 10000:
                                    print(f"    ⚠️ 警告: 総不足時間が異常に大きい！")
                                elif total_shortage == 0:
                                    print(f"    ⚠️ 警告: 不足時間が0！")
                                else:
                                    print(f"    ✅ 不足時間は妥当な範囲")
                    except Exception as e:
                        print(f"    読み込みエラー: {e}")
            
            # 2. AI包括レポート（JSON）の確認
            json_files = [f for f in file_list if 'comprehensive' in f and f.endswith('.json')]
            if json_files:
                print(f"\nAI包括レポート: {len(json_files)}個")
                for json_file in json_files[:1]:
                    print(f"\n  {json_file}:")
                    try:
                        with zip_file.open(json_file) as f:
                            data = json.load(f)
                            
                        # デフォルト値のチェック
                        default_count = 0
                        actual_value_count = 0
                        
                        def check_values(obj, path=""):
                            nonlocal default_count, actual_value_count
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    if v in [0, 0.0, "N/A", "default", None, "", []]:
                                        default_count += 1
                                        if len(path) < 100:  # 深さ制限
                                            print(f"    デフォルト値: {path}.{k} = {v}")
                                    else:
                                        actual_value_count += 1
                                    if isinstance(v, (dict, list)):
                                        check_values(v, f"{path}.{k}")
                            elif isinstance(obj, list):
                                for i, item in enumerate(obj):
                                    if isinstance(item, (dict, list)):
                                        check_values(item, f"{path}[{i}]")
                        
                        check_values(data)
                        
                        print(f"\n    統計:")
                        print(f"    実データ数: {actual_value_count}")
                        print(f"    デフォルト値数: {default_count}")
                        print(f"    実データ率: {actual_value_count/(actual_value_count+default_count)*100:.1f}%")
                        
                        # 主要メトリクスの確認
                        if 'shortage_analysis' in data:
                            shortage = data['shortage_analysis']
                            print(f"\n    不足分析データ:")
                            print(f"      総不足時間: {shortage.get('total_shortage_hours', 'なし')}")
                            print(f"      データ整合性: {shortage.get('data_integrity', 'なし')}")
                            
                        if 'fatigue_analysis' in data:
                            fatigue = data['fatigue_analysis']
                            print(f"\n    疲労分析データ:")
                            print(f"      平均疲労スコア: {fatigue.get('avg_fatigue_score', 'なし')}")
                            
                        if 'fairness_analysis' in data:
                            fairness = data['fairness_analysis']
                            print(f"\n    公平性分析データ:")
                            print(f"      平均公平性スコア: {fairness.get('avg_fairness_score', 'なし')}")
                            
                    except Exception as e:
                        print(f"    JSONエラー: {e}")
            
            # 3. 設定ファイルの確認
            config_files = [f for f in file_list if 'config' in f and f.endswith('.json')]
            if config_files:
                print(f"\n設定ファイル: {len(config_files)}個")
                for config_file in config_files[:1]:
                    print(f"\n  {config_file}:")
                    try:
                        with zip_file.open(config_file) as f:
                            config = json.load(f)
                            
                        if 'slot_minutes' in config:
                            print(f"    スロット間隔: {config['slot_minutes']}分")
                        if 'need_calculation_method' in config:
                            print(f"    計算方法: {config['need_calculation_method']}")
                            
                    except Exception as e:
                        print(f"    設定読み込みエラー: {e}")
                        
    except Exception as e:
        print(f"ZIPファイル読み込みエラー: {e}")
        return False
    
    return True

def check_slot_calculation():
    """スロット計算の妥当性確認"""
    print("\n" + "=" * 80)
    print("3. スロット計算の妥当性確認")
    print("=" * 80)
    
    # 最新のログファイルから動的スロット設定を確認
    log_path = "shift_suite.log"
    if Path(log_path).exists():
        print(f"\nログファイルから動的スロット設定を確認:")
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 最新のスロット設定を検索
            slot_lines = [line for line in lines if 'スロット' in line or 'slot' in line.lower()]
            if slot_lines:
                print("最新のスロット関連ログ:")
                for line in slot_lines[-5:]:  # 最後の5行
                    print(f"  {line.strip()}")
            else:
                print("  スロット関連のログが見つかりません")
                
        except Exception as e:
            print(f"  ログ読み込みエラー: {e}")

def main():
    """メイン処理"""
    print("🔍 実データ分析結果の検証")
    print(f"入力: デイ_テスト用データ_休日精緻.xlsx")
    print(f"出力: analysis_results (55).zip")
    
    # 各種分析の実行
    input_ok = analyze_input_excel()
    output_ok = analyze_output_zip()
    check_slot_calculation()
    
    # 総合評価
    print("\n" + "=" * 80)
    print("検証結果サマリー")
    print("=" * 80)
    
    if input_ok and output_ok:
        print("✅ 入出力ファイルの読み込み成功")
        print("\n次のステップ:")
        print("1. 上記の数値（特に不足時間）が妥当か確認")
        print("2. JSONの実データ率が80%以上か確認")
        print("3. 動的スロット設定が正しく反映されているか確認")
    else:
        print("❌ ファイル読み込みに問題があります")

if __name__ == "__main__":
    main()