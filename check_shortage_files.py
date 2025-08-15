#!/usr/bin/env python3
"""
不足分析ファイルの詳細確認
"""

import zipfile
import json
from pathlib import Path

def check_shortage_analysis():
    zip_path = "analysis_results (55).zip"
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # 不足分析関連ファイルを探す
        shortage_files = [f for f in zf.namelist() if 'shortage' in f.lower()]
        
        print(f"🔍 不足分析ファイルの確認")
        print("=" * 80)
        print(f"不足分析関連ファイル数: {len(shortage_files)}")
        
        # カテゴリ別に分類
        xlsx_files = [f for f in shortage_files if f.endswith('.xlsx')]
        json_files = [f for f in shortage_files if f.endswith('.json')]
        parquet_files = [f for f in shortage_files if f.endswith('.parquet')]
        
        print(f"\n種類別:")
        print(f"  XLSX: {len(xlsx_files)}個")
        print(f"  JSON: {len(json_files)}個")
        print(f"  Parquet: {len(parquet_files)}個")
        
        # proportional関連のファイルを確認
        proportional_files = [f for f in shortage_files if 'proportional' in f.lower()]
        print(f"\nProportional分析ファイル: {len(proportional_files)}個")
        for f in proportional_files[:5]:
            print(f"  - {f}")
        
        # JSONメタデータの確認
        meta_files = [f for f in json_files if 'meta' in f]
        if meta_files:
            print(f"\n📄 メタデータファイルの内容:")
            for meta_file in meta_files[:2]:
                print(f"\n  {meta_file}:")
                try:
                    with zf.open(meta_file) as f:
                        meta = json.load(f)
                    
                    # 主要な値を表示
                    if isinstance(meta, dict):
                        for k, v in meta.items():
                            if isinstance(v, (int, float, str)):
                                print(f"    {k}: {v}")
                            elif k == 'summary' and isinstance(v, dict):
                                print(f"    summary:")
                                for sk, sv in v.items():
                                    print(f"      {sk}: {sv}")
                                    
                        # 計算パラメータの確認
                        if 'calculation_params' in meta:
                            params = meta['calculation_params']
                            print(f"    計算パラメータ:")
                            if 'slot_minutes' in params:
                                print(f"      slot_minutes: {params['slot_minutes']}分")
                                if params['slot_minutes'] != 30:
                                    print(f"        ℹ️ デフォルト（30分）以外のスロット設定")
                            if 'method' in params:
                                print(f"      method: {params['method']}")
                                
                except Exception as e:
                    print(f"    読み込みエラー: {e}")
        
        # 実際の不足時間データの確認（XLSXファイルから）
        print(f"\n📊 不足時間の実データ確認:")
        
        # scenario_defaultディレクトリのファイルを優先
        default_scenario_files = [f for f in xlsx_files if 'scenario_default' in f]
        if default_scenario_files:
            print(f"\nscenario_defaultの不足分析ファイル: {len(default_scenario_files)}個")
            
            # shortage_role_summaryを探す
            role_summary_files = [f for f in default_scenario_files if 'role_summary' in f]
            if role_summary_files:
                print(f"\n  役職別サマリーファイル: {role_summary_files[0]}")
                print(f"  （Excelファイルのため詳細は直接確認が必要）")
            
            # proportional関連
            prop_files = [f for f in default_scenario_files if 'proportional' in f]
            if prop_files:
                print(f"\n  Proportional分析ファイル: {len(prop_files)}個")
                for f in prop_files[:3]:
                    print(f"    - {Path(f).name}")
        
        # ログファイルから実行時のパラメータを確認
        print(f"\n📝 実行ログの確認:")
        log_files = [f for f in zf.namelist() if f.endswith('.log') or f.endswith('.txt')]
        analysis_logs = [f for f in log_files if 'analysis' in f or 'execution' in f]
        
        if analysis_logs:
            print(f"  分析ログファイル: {len(analysis_logs)}個")
            for log_file in analysis_logs[:1]:
                print(f"\n  {log_file}の内容（一部）:")
                try:
                    with zf.open(log_file) as f:
                        lines = f.read().decode('utf-8', errors='ignore').split('\n')
                    
                    # スロット関連の行を抽出
                    slot_lines = [l for l in lines if 'slot' in l.lower() or 'スロット' in l]
                    if slot_lines:
                        print("    スロット関連ログ:")
                        for line in slot_lines[:3]:
                            print(f"      {line.strip()}")
                    
                    # 不足時間関連の行を抽出
                    shortage_lines = [l for l in lines if '不足' in l or 'shortage' in l.lower()]
                    if shortage_lines:
                        print("\n    不足時間関連ログ:")
                        for line in shortage_lines[:3]:
                            print(f"      {line.strip()}")
                            
                except Exception as e:
                    print(f"    ログ読み込みエラー: {e}")

if __name__ == "__main__":
    check_shortage_analysis()