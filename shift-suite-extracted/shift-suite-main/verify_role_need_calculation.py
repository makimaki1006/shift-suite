#!/usr/bin/env python3
"""
職種別need計算の検証スクリプト
temp_analysis_results/配下の最新の分析結果を使用して検証を行う
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# パッケージパスを追加
sys.path.append('.')

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    print("WARNING: pandas not available, using limited verification")
    HAS_PANDAS = False

def get_latest_analysis_dir() -> Path:
    """最新の分析結果ディレクトリを取得"""
    temp_dir = Path('temp_analysis_results')
    if not temp_dir.exists():
        raise FileNotFoundError("temp_analysis_results directory not found")
    
    # 利用可能なディレクトリ
    subdirs = [d for d in temp_dir.iterdir() if d.is_dir()]
    if not subdirs:
        raise FileNotFoundError("No analysis result directories found")
    
    # out_p25_basedが最新とみなす
    preferred = temp_dir / 'out_p25_based'
    if preferred.exists():
        return preferred
    
    # フォールバック：最新のディレクトリを選択
    return max(subdirs, key=lambda x: x.stat().st_mtime)

def verify_file_structure(analysis_dir: Path) -> Dict:
    """ファイル構造の検証"""
    results = {
        "analysis_dir": str(analysis_dir),
        "files_found": {},
        "structure_check": {}
    }
    
    # 必須ファイルの確認
    required_files = [
        'need_per_date_slot.parquet',
        'heat_ALL.parquet',
        'heatmap.meta.json'
    ]
    
    for file in required_files:
        file_path = analysis_dir / file
        results["files_found"][file] = file_path.exists()
        if file_path.exists():
            results["structure_check"][file] = {
                "size_bytes": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            }
    
    # 職種別heatファイルの確認
    heat_files = list(analysis_dir.glob('heat_*.parquet'))
    role_files = [f for f in heat_files if 'ALL' not in f.name and 'emp_' not in f.name]
    emp_files = [f for f in heat_files if 'emp_' in f.name]
    
    results["files_found"]["role_heat_files"] = len(role_files)
    results["files_found"]["employment_heat_files"] = len(emp_files)
    results["files_found"]["total_heat_files"] = len(heat_files)
    
    return results

def verify_metadata(analysis_dir: Path) -> Dict:
    """メタデータの検証"""
    results = {"metadata_check": {}}
    
    meta_file = analysis_dir / 'heatmap.meta.json'
    if not meta_file.exists():
        results["metadata_check"]["error"] = "heatmap.meta.json not found"
        return results
    
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        
        results["metadata_check"]["roles_count"] = len(meta_data.get("roles", []))
        results["metadata_check"]["dates_count"] = len(meta_data.get("dates", []))
        results["metadata_check"]["employments"] = meta_data.get("employments", [])
        
        # dow_need_patternの検証
        dow_pattern = meta_data.get("dow_need_pattern", [])
        if dow_pattern:
            # 非ゼロneed値の時間帯を確認
            non_zero_slots = []
            for slot in dow_pattern:
                for dow in range(7):  # 0-6 (Monday-Sunday)
                    if slot.get(str(dow), 0) > 0:
                        non_zero_slots.append(f"{slot['time']}_DOW{dow}")
            
            results["metadata_check"]["non_zero_need_slots"] = len(non_zero_slots)
            results["metadata_check"]["sample_non_zero_slots"] = non_zero_slots[:10]
        
        # need_calculation_paramsの確認
        calc_params = meta_data.get("need_calculation_params", {})
        results["metadata_check"]["calculation_method"] = calc_params.get("statistic_method")
        results["metadata_check"]["reference_period"] = f"{calc_params.get('ref_start_date')} to {calc_params.get('ref_end_date')}"
        
    except Exception as e:
        results["metadata_check"]["error"] = f"Failed to parse metadata: {e}"
    
    return results

def verify_with_pandas(analysis_dir: Path) -> Dict:
    """pandasを使った詳細検証"""
    if not HAS_PANDAS:
        return {"pandas_check": {"error": "pandas not available"}}
    
    results = {"pandas_check": {}}
    
    try:
        # 1. 全体needファイルの読み込み
        need_file = analysis_dir / 'need_per_date_slot.parquet'
        if need_file.exists():
            df_need = pd.read_parquet(need_file)
            results["pandas_check"]["global_need"] = {
                "shape": df_need.shape,
                "total_need": float(df_need.values.sum()),
                "non_zero_ratio": float((df_need > 0).sum().sum() / (df_need.shape[0] * df_need.shape[1])),
                "daily_totals": df_need.sum(axis=0).head(5).to_dict()
            }
        
        # 2. 職種別heatファイルの検証
        heat_files = list(analysis_dir.glob('heat_*.parquet'))
        role_files = [f for f in heat_files if 'ALL' not in f.name and 'emp_' not in f.name]
        
        role_need_totals = {}
        for role_file in role_files[:5]:  # 最初の5つの職種
            role_name = role_file.name.replace('heat_', '').replace('.parquet', '')
            try:
                df_role = pd.read_parquet(role_file)
                need_cols = [col for col in df_role.columns if 'need' in col.lower()]
                
                if need_cols:
                    role_need_sum = df_role[need_cols].sum().sum()
                    role_need_totals[role_name] = float(role_need_sum)
                else:
                    role_need_totals[role_name] = 0.0
                    
            except Exception as e:
                role_need_totals[role_name] = f"Error: {e}"
        
        results["pandas_check"]["role_need_totals"] = role_need_totals
        
        # 3. heat_ALLファイルの検証
        all_file = analysis_dir / 'heat_ALL.parquet'
        if all_file.exists():
            df_all = pd.read_parquet(all_file)
            need_cols_all = [col for col in df_all.columns if 'need' in col.lower()]
            
            if need_cols_all:
                all_need_sum = df_all[need_cols_all].sum().sum()
                results["pandas_check"]["all_heat_need"] = float(all_need_sum)
                
                # 整合性チェック
                role_total = sum(v for v in role_need_totals.values() if isinstance(v, (int, float)))
                results["pandas_check"]["consistency_check"] = {
                    "role_total": role_total,
                    "all_heat_total": float(all_need_sum),
                    "difference": abs(float(all_need_sum) - role_total),
                    "ratio": role_total / float(all_need_sum) if all_need_sum > 0 else 0
                }
        
    except Exception as e:
        results["pandas_check"]["error"] = f"Pandas verification failed: {e}"
    
    return results

def main():
    """メイン実行関数"""
    print("=== 職種別need計算の検証 ===")
    print()
    
    try:
        # 最新の分析ディレクトリを取得
        analysis_dir = get_latest_analysis_dir()
        print(f"検証対象ディレクトリ: {analysis_dir}")
        print()
        
        # 1. ファイル構造の検証
        print("1. ファイル構造の検証")
        structure_results = verify_file_structure(analysis_dir)
        
        print(f"  必須ファイル:")
        for file, exists in structure_results["files_found"].items():
            if isinstance(exists, bool):
                status = "✓" if exists else "✗"
                print(f"    {status} {file}")
            else:
                print(f"    - {file}: {exists}")
        print()
        
        # 2. メタデータの検証
        print("2. メタデータの検証")
        metadata_results = verify_metadata(analysis_dir)
        
        if "error" not in metadata_results["metadata_check"]:
            meta_check = metadata_results["metadata_check"]
            print(f"  職種数: {meta_check.get('roles_count', 'N/A')}")
            print(f"  対象日数: {meta_check.get('dates_count', 'N/A')}")
            print(f"  雇用形態: {meta_check.get('employments', 'N/A')}")
            print(f"  非ゼロneed時間帯: {meta_check.get('non_zero_need_slots', 'N/A')}")
            print(f"  計算手法: {meta_check.get('calculation_method', 'N/A')}")
            print(f"  参照期間: {meta_check.get('reference_period', 'N/A')}")
        else:
            print(f"  エラー: {metadata_results['metadata_check']['error']}")
        print()
        
        # 3. pandasを使った詳細検証
        print("3. 数値データの検証")
        pandas_results = verify_with_pandas(analysis_dir)
        
        if "error" not in pandas_results["pandas_check"]:
            pandas_check = pandas_results["pandas_check"]
            
            # 全体need情報
            if "global_need" in pandas_check:
                global_info = pandas_check["global_need"]
                print(f"  全体need:")
                print(f"    データ形状: {global_info['shape']}")
                print(f"    total_need: {global_info['total_need']:.2f}")
                print(f"    非ゼロ比率: {global_info['non_zero_ratio']:.2%}")
            
            # 職種別need情報
            if "role_need_totals" in pandas_check:
                print(f"  職種別need合計:")
                for role, total in list(pandas_check["role_need_totals"].items())[:5]:
                    if isinstance(total, (int, float)):
                        print(f"    {role}: {total:.2f}")
                    else:
                        print(f"    {role}: {total}")
            
            # 整合性チェック
            if "consistency_check" in pandas_check:
                consistency = pandas_check["consistency_check"]
                print(f"  整合性チェック:")
                print(f"    職種別合計: {consistency['role_total']:.2f}")
                print(f"    heat_ALL合計: {consistency['all_heat_total']:.2f}")
                print(f"    差異: {consistency['difference']:.2f}")
                print(f"    比率: {consistency['ratio']:.2%}")
                
                # 判定
                if consistency['difference'] < 0.01:
                    print("    ✓ 整合性: 良好")
                elif consistency['difference'] < 1.0:
                    print("    ⚠ 整合性: 軽微な差異")
                else:
                    print("    ✗ 整合性: 大きな差異")
        else:
            print(f"  エラー: {pandas_results['pandas_check']['error']}")
        print()
        
        # 4. 総合判定
        print("4. 総合判定")
        
        # 必須ファイルの存在確認
        required_files_ok = all(structure_results["files_found"].get(f, False) 
                               for f in ['need_per_date_slot.parquet', 'heat_ALL.parquet', 'heatmap.meta.json'])
        
        # メタデータの妥当性確認
        metadata_ok = "error" not in metadata_results["metadata_check"]
        
        # データの整合性確認
        data_consistency_ok = False
        if HAS_PANDAS and "consistency_check" in pandas_results.get("pandas_check", {}):
            diff = pandas_results["pandas_check"]["consistency_check"]["difference"]
            data_consistency_ok = diff < 1.0
        
        print(f"  必須ファイル: {'✓' if required_files_ok else '✗'}")
        print(f"  メタデータ: {'✓' if metadata_ok else '✗'}")
        print(f"  データ整合性: {'✓' if data_consistency_ok else '✗' if HAS_PANDAS else 'N/A'}")
        
        overall_status = required_files_ok and metadata_ok and (data_consistency_ok or not HAS_PANDAS)
        print(f"  総合評価: {'✓ 正常' if overall_status else '✗ 問題あり'}")
        
    except Exception as e:
        print(f"検証中にエラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())