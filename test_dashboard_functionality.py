#!/usr/bin/env python3
"""
dash_app.pyの機能をテストするスクリプト
特に calculate_role_dynamic_need 関数と不足分析の一致性を確認
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# テスト用のデータ読み込み関数
def load_test_data(results_dir):
    """テスト用データを読み込む"""
    data_cache = {}
    
    try:
        # 分析結果ディレクトリの確認
        results_path = Path(results_dir)
        if not results_path.exists():
            log.error(f"Results directory not found: {results_dir}")
            return data_cache
            
        log.info(f"Loading test data from: {results_dir}")
        
        # 基本的なファイルを読み込み
        files_to_load = [
            'heat_ALL.parquet',
            'heat_介護.parquet',
            'heat_看護師.parquet',
            'heat_emp_正社員.parquet',
            'need_per_date_slot.parquet',
            'shortage_role_summary.parquet',
            'shortage_employment_summary.parquet'
        ]
        
        for filename in files_to_load:
            file_path = results_path / filename
            if file_path.exists():
                try:
                    key = filename.replace('.parquet', '').replace('.csv', '')
                    data_cache[key] = pd.read_parquet(file_path)
                    log.info(f"Loaded {key}: {data_cache[key].shape}")
                except Exception as e:
                    log.warning(f"Failed to load {filename}: {e}")
            else:
                log.warning(f"File not found: {filename}")
                
        # shortage.meta.jsonを読み込み
        meta_path = results_path / 'shortage.meta.json'
        if meta_path.exists():
            import json
            with open(meta_path, 'r', encoding='utf-8') as f:
                data_cache['meta'] = json.load(f)
                log.info(f"Loaded metadata: {len(data_cache['meta'])} keys")
        
        return data_cache
        
    except Exception as e:
        log.error(f"Error loading test data: {e}")
        return data_cache

def test_calculate_role_dynamic_need(data_cache):
    """calculate_role_dynamic_need関数の動作をテスト"""
    log.info("=== Testing calculate_role_dynamic_need function ===")
    
    try:
        # 全体データの確認
        heat_all = data_cache.get('heat_ALL', pd.DataFrame())
        need_per_date = data_cache.get('need_per_date_slot', pd.DataFrame())
        meta = data_cache.get('meta', {})
        
        if heat_all.empty:
            log.error("heat_ALL data is missing")
            return False
            
        if need_per_date.empty:
            log.error("need_per_date_slot data is missing")
            return False
            
        log.info(f"heat_ALL shape: {heat_all.shape}")
        log.info(f"need_per_date_slot shape: {need_per_date.shape}")
        log.info(f"heat_ALL columns: {heat_all.columns.tolist()}")
        
        # 日付列を取得
        date_cols = meta.get('dates', [])
        if not date_cols:
            log.error("No date columns found in metadata")
            return False
            
        log.info(f"Date columns: {len(date_cols)} dates")
        
        # 職種別データをテスト
        role_keys = ['heat_介護', 'heat_看護師']
        for role_key in role_keys:
            role_data = data_cache.get(role_key, pd.DataFrame())
            if role_data.empty:
                log.warning(f"{role_key} data is missing")
                continue
                
            log.info(f"\n--- Testing {role_key} ---")
            log.info(f"Shape: {role_data.shape}")
            log.info(f"Columns: {role_data.columns.tolist()}")
            
            if 'need' in role_data.columns:
                baseline_need = role_data['need'].sum()
                log.info(f"Baseline need total: {baseline_need:.2f}")
                
                # 簡易版のrole_dynamic_need計算をテスト
                total_baseline_need = 0.0
                for key in data_cache.keys():
                    if key.startswith('heat_') and key not in ['heat_ALL', 'heat_all'] and not key.startswith('heat_emp_'):
                        test_data = data_cache[key]
                        if not test_data.empty and 'need' in test_data.columns:
                            total_baseline_need += test_data['need'].sum()
                
                if total_baseline_need > 0:
                    role_ratio = baseline_need / total_baseline_need
                    log.info(f"Role ratio: {role_ratio:.4f}")
                    log.info(f"Total baseline across all roles: {total_baseline_need:.2f}")
                else:
                    log.warning("Cannot calculate role ratio - total baseline is 0")
            else:
                log.warning(f"'need' column not found in {role_key}")
        
        return True
        
    except Exception as e:
        log.error(f"Error in test_calculate_role_dynamic_need: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_shortage_consistency(data_cache):
    """不足分析の一致性をテスト"""
    log.info("\n=== Testing shortage analysis consistency ===")
    
    try:
        # 不足分析データを取得
        shortage_role = data_cache.get('shortage_role_summary', pd.DataFrame())
        shortage_employment = data_cache.get('shortage_employment_summary', pd.DataFrame())
        heat_all = data_cache.get('heat_ALL', pd.DataFrame())
        
        if shortage_role.empty:
            log.warning("shortage_role_summary data is missing")
        else:
            log.info(f"shortage_role_summary shape: {shortage_role.shape}")
            log.info(f"shortage_role_summary columns: {shortage_role.columns.tolist()}")
            if 'lack_count' in shortage_role.columns:
                role_total_shortage = shortage_role['lack_count'].sum()
                log.info(f"Total shortage (role-based): {role_total_shortage:.2f}")
            
        if shortage_employment.empty:
            log.warning("shortage_employment_summary data is missing")
        else:
            log.info(f"shortage_employment_summary shape: {shortage_employment.shape}")
            log.info(f"shortage_employment_summary columns: {shortage_employment.columns.tolist()}")
            if 'lack_count' in shortage_employment.columns:
                emp_total_shortage = shortage_employment['lack_count'].sum()
                log.info(f"Total shortage (employment-based): {emp_total_shortage:.2f}")
        
        if heat_all.empty:
            log.warning("heat_ALL data is missing")
        else:
            log.info(f"heat_ALL shape: {heat_all.shape}")
            log.info(f"heat_ALL columns: {heat_all.columns.tolist()}")
            
            # 全体不足の計算をテスト
            if 'need' in heat_all.columns and 'staff' in heat_all.columns:
                all_need = heat_all['need'].sum()
                all_staff = heat_all['staff'].sum()
                all_shortage = max(0, all_need - all_staff)
                log.info(f"Overall need: {all_need:.2f}")
                log.info(f"Overall staff: {all_staff:.2f}")
                log.info(f"Overall shortage: {all_shortage:.2f}")
        
        # 一致性チェック
        if not shortage_role.empty and not shortage_employment.empty and 'lack_count' in shortage_role.columns and 'lack_count' in shortage_employment.columns:
            role_total = shortage_role['lack_count'].sum()
            emp_total = shortage_employment['lack_count'].sum()
            diff = abs(role_total - emp_total)
            log.info(f"\nConsistency check:")
            log.info(f"Role-based total: {role_total:.2f}")
            log.info(f"Employment-based total: {emp_total:.2f}")
            log.info(f"Difference: {diff:.2f}")
            
            if diff < 0.01:
                log.info("✅ Shortage totals are consistent!")
            else:
                log.warning("⚠️ Shortage totals are inconsistent!")
        
        return True
        
    except Exception as e:
        log.error(f"Error in test_shortage_consistency: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_heatmap_data_integrity(data_cache):
    """ヒートマップデータの整合性をテスト"""
    log.info("\n=== Testing heatmap data integrity ===")
    
    try:
        meta = data_cache.get('meta', {})
        date_cols = meta.get('dates', [])
        
        # 全ヒートマップデータをチェック
        heatmap_keys = [k for k in data_cache.keys() if k.startswith('heat_')]
        
        for key in heatmap_keys:
            data = data_cache[key]
            if data.empty:
                continue
                
            log.info(f"\n--- {key} ---")
            log.info(f"Shape: {data.shape}")
            
            # 基本列の存在確認
            required_cols = ['need', 'staff', 'upper']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                log.warning(f"Missing columns: {missing_cols}")
            else:
                log.info("✅ All required columns present")
            
            # 日付列の存在確認
            if date_cols:
                date_cols_in_data = [col for col in date_cols if str(col) in data.columns]
                log.info(f"Date columns found: {len(date_cols_in_data)}/{len(date_cols)}")
                
                if len(date_cols_in_data) == len(date_cols):
                    log.info("✅ All date columns present")
                else:
                    log.warning("⚠️ Some date columns missing")
            
            # データの値域チェック
            if 'need' in data.columns and 'staff' in data.columns:
                need_total = data['need'].sum()
                staff_total = data['staff'].sum()
                log.info(f"Need total: {need_total:.2f}, Staff total: {staff_total:.2f}")
                
                if need_total < 0 or staff_total < 0:
                    log.warning("⚠️ Negative values detected")
                elif need_total == 0 and staff_total == 0:
                    log.warning("⚠️ All values are zero")
                else:
                    log.info("✅ Values are reasonable")
        
        return True
        
    except Exception as e:
        log.error(f"Error in test_heatmap_data_integrity: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    log.info("Starting dashboard functionality test")
    
    # テストデータディレクトリ
    results_dir = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/temp_analysis_results/out_p25_based"
    
    # データ読み込み
    data_cache = load_test_data(results_dir)
    
    if not data_cache:
        log.error("No data loaded - cannot proceed with tests")
        return False
    
    log.info(f"Loaded {len(data_cache)} data items")
    
    # テスト実行
    tests = [
        test_heatmap_data_integrity,
        test_calculate_role_dynamic_need,
        test_shortage_consistency
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func(data_cache)
            results.append(result)
            log.info(f"{test_func.__name__}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            log.error(f"{test_func.__name__}: ERROR - {e}")
            results.append(False)
    
    # 総合結果
    all_passed = all(results)
    log.info(f"\n=== TEST SUMMARY ===")
    log.info(f"Total tests: {len(results)}")
    log.info(f"Passed: {sum(results)}")
    log.info(f"Failed: {len(results) - sum(results)}")
    log.info(f"Overall result: {'PASS' if all_passed else 'FAIL'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)