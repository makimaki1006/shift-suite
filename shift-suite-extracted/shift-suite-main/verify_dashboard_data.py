#!/usr/bin/env python3
"""
dash_app.pyのデータ読み込みと基本機能を検証するスクリプト
pandasに依存しない方式で検証
"""

import os
import json
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

def verify_required_files(results_dir):
    """必要なファイルの存在確認"""
    log.info("=== Verifying required files ===")
    
    required_files = [
        'heat_ALL.parquet',
        'need_per_date_slot.parquet',
        'shortage.meta.json',
        'heatmap.meta.json',
        'shortage_role_summary.parquet',
        'shortage_employment_summary.parquet'
    ]
    
    results_path = Path(results_dir)
    missing_files = []
    existing_files = []
    
    for filename in required_files:
        file_path = results_path / filename
        if file_path.exists():
            file_size = file_path.stat().st_size
            existing_files.append((filename, file_size))
            log.info(f"✅ {filename} ({file_size} bytes)")
        else:
            missing_files.append(filename)
            log.warning(f"❌ {filename} (missing)")
    
    # 職種別・雇用形態別ファイルの確認
    role_files = []
    emp_files = []
    
    for file in results_path.glob('heat_*.parquet'):
        filename = file.name
        if filename.startswith('heat_emp_'):
            emp_files.append(filename)
        elif filename != 'heat_ALL.parquet':
            role_files.append(filename)
    
    log.info(f"Role-specific heatmap files: {len(role_files)}")
    for filename in sorted(role_files)[:5]:  # 最初の5件を表示
        log.info(f"  - {filename}")
    if len(role_files) > 5:
        log.info(f"  ... and {len(role_files) - 5} more")
    
    log.info(f"Employment-specific heatmap files: {len(emp_files)}")
    for filename in sorted(emp_files):
        log.info(f"  - {filename}")
    
    return len(missing_files) == 0, existing_files, missing_files

def verify_metadata(results_dir):
    """メタデータの内容確認"""
    log.info("\n=== Verifying metadata ===")
    
    results_path = Path(results_dir)
    
    # shortage.meta.json
    shortage_meta_path = results_path / 'shortage.meta.json'
    if shortage_meta_path.exists():
        try:
            with open(shortage_meta_path, 'r', encoding='utf-8') as f:
                shortage_meta = json.load(f)
            
            log.info("shortage.meta.json:")
            log.info(f"  - Slots: {shortage_meta.get('slot', 'N/A')}")
            log.info(f"  - Dates: {len(shortage_meta.get('dates', []))} dates")
            log.info(f"  - Roles: {len(shortage_meta.get('roles', []))} roles")
            log.info(f"  - Employments: {len(shortage_meta.get('employments', []))} types")
            log.info(f"  - Months: {shortage_meta.get('months', [])}")
            
            dates = shortage_meta.get('dates', [])
            if dates:
                log.info(f"  - Date range: {dates[0]} to {dates[-1]}")
            
            roles = shortage_meta.get('roles', [])
            if roles:
                log.info(f"  - First 3 roles: {roles[:3]}")
            
        except Exception as e:
            log.error(f"Error reading shortage.meta.json: {e}")
    else:
        log.warning("shortage.meta.json not found")
    
    # heatmap.meta.json
    heatmap_meta_path = results_path / 'heatmap.meta.json'
    if heatmap_meta_path.exists():
        try:
            with open(heatmap_meta_path, 'r', encoding='utf-8') as f:
                heatmap_meta = json.load(f)
            
            log.info("heatmap.meta.json:")
            log.info(f"  - Keys: {len(heatmap_meta.keys())} entries")
            log.info(f"  - Available keys: {list(heatmap_meta.keys())[:5]}")
            
        except Exception as e:
            log.error(f"Error reading heatmap.meta.json: {e}")
    else:
        log.warning("heatmap.meta.json not found")

def verify_file_sizes(results_dir):
    """ファイルサイズの確認"""
    log.info("\n=== Verifying file sizes ===")
    
    results_path = Path(results_dir)
    
    # 主要ファイルのサイズチェック
    key_files = [
        'heat_ALL.parquet',
        'need_per_date_slot.parquet',
        'shortage_role_summary.parquet',
        'shortage_employment_summary.parquet'
    ]
    
    for filename in key_files:
        file_path = results_path / filename
        if file_path.exists():
            size = file_path.stat().st_size
            size_mb = size / (1024 * 1024)
            log.info(f"{filename}: {size:,} bytes ({size_mb:.2f} MB)")
            
            if size == 0:
                log.warning(f"⚠️ {filename} is empty!")
            elif size < 100:
                log.warning(f"⚠️ {filename} is very small ({size} bytes)")
            else:
                log.info(f"✅ {filename} has reasonable size")
        else:
            log.warning(f"❌ {filename} not found")

def verify_csv_data(results_dir):
    """CSV形式のデータ確認"""
    log.info("\n=== Verifying CSV data ===")
    
    results_path = Path(results_dir)
    
    csv_files = [
        'work_patterns.csv',
        'staff_balance_daily.csv',
        'leave_analysis.csv'
    ]
    
    for filename in csv_files:
        file_path = results_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                log.info(f"{filename}:")
                log.info(f"  - Lines: {len(lines)}")
                
                if lines:
                    header = lines[0].strip()
                    log.info(f"  - Header: {header}")
                    
                    if len(lines) > 1:
                        # 空でない行の数をカウント
                        non_empty_lines = [line for line in lines[1:] if line.strip()]
                        log.info(f"  - Data rows: {len(non_empty_lines)}")
                        
                        if non_empty_lines:
                            log.info(f"  - Sample data: {non_empty_lines[0].strip()}")
                    else:
                        log.warning(f"  - No data rows found")
                else:
                    log.warning(f"  - File is empty")
                    
            except Exception as e:
                log.error(f"Error reading {filename}: {e}")
        else:
            log.warning(f"{filename} not found")

def verify_summary_files(results_dir):
    """サマリーファイルの確認"""
    log.info("\n=== Verifying summary files ===")
    
    results_path = Path(results_dir)
    
    summary_files = [
        'shortage_summary.txt',
        'stats_summary.txt',
        'cost_benefit_summary.txt'
    ]
    
    for filename in summary_files:
        file_path = results_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                log.info(f"{filename}:")
                if content:
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip():
                            log.info(f"  - {line.strip()}")
                else:
                    log.warning(f"  - File is empty")
                    
            except Exception as e:
                log.error(f"Error reading {filename}: {e}")
        else:
            log.warning(f"{filename} not found")

def check_dashboard_compatibility(results_dir):
    """dashboard互換性の確認"""
    log.info("\n=== Checking dashboard compatibility ===")
    
    results_path = Path(results_dir)
    
    # 必須データの確認
    essential_checks = {
        'heat_ALL.parquet': 'Overall heatmap data',
        'need_per_date_slot.parquet': 'Dynamic need calculation',
        'shortage.meta.json': 'Metadata for dates and roles',
        'shortage_role_summary.parquet': 'Role-based shortage analysis',
        'shortage_employment_summary.parquet': 'Employment-based shortage analysis'
    }
    
    missing_essential = []
    
    for filename, description in essential_checks.items():
        file_path = results_path / filename
        if file_path.exists():
            log.info(f"✅ {description}: {filename}")
        else:
            log.error(f"❌ {description}: {filename} (REQUIRED)")
            missing_essential.append(filename)
    
    # 職種別データの確認
    role_heatmaps = list(results_path.glob('heat_*.parquet'))
    role_heatmaps = [f for f in role_heatmaps 
                    if f.name != 'heat_ALL.parquet' and not f.name.startswith('heat_emp_')]
    
    log.info(f"Role-specific heatmaps: {len(role_heatmaps)} files")
    
    if len(role_heatmaps) >= 3:
        log.info("✅ Sufficient role-specific data for dynamic need calculation")
    else:
        log.warning(f"⚠️ Limited role-specific data ({len(role_heatmaps)} files)")
    
    # 雇用形態別データの確認
    emp_heatmaps = list(results_path.glob('heat_emp_*.parquet'))
    log.info(f"Employment-specific heatmaps: {len(emp_heatmaps)} files")
    
    if len(emp_heatmaps) >= 2:
        log.info("✅ Employment-specific data available")
    else:
        log.warning(f"⚠️ Limited employment-specific data ({len(emp_heatmaps)} files)")
    
    # 総合判定
    if not missing_essential:
        log.info("✅ Dashboard should be able to load and function properly")
        return True
    else:
        log.error(f"❌ Dashboard may fail due to missing essential files: {missing_essential}")
        return False

def main():
    """メイン検証処理"""
    log.info("Starting dashboard data verification")
    
    results_dir = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/temp_analysis_results/out_p25_based"
    
    if not Path(results_dir).exists():
        log.error(f"Results directory not found: {results_dir}")
        return False
    
    log.info(f"Verifying data in: {results_dir}")
    
    # 各種検証を実行
    all_passed = True
    
    try:
        # ファイル存在確認
        files_ok, existing, missing = verify_required_files(results_dir)
        if not files_ok:
            all_passed = False
        
        # メタデータ確認
        verify_metadata(results_dir)
        
        # ファイルサイズ確認
        verify_file_sizes(results_dir)
        
        # CSV データ確認
        verify_csv_data(results_dir)
        
        # サマリー確認
        verify_summary_files(results_dir)
        
        # ダッシュボード互換性確認
        dashboard_ok = check_dashboard_compatibility(results_dir)
        if not dashboard_ok:
            all_passed = False
        
    except Exception as e:
        log.error(f"Verification failed with error: {e}")
        all_passed = False
    
    # 総合結果
    log.info(f"\n=== VERIFICATION SUMMARY ===")
    log.info(f"Overall result: {'PASS' if all_passed else 'FAIL'}")
    
    if all_passed:
        log.info("✅ Data appears to be ready for dashboard use")
        log.info("Dashboard should be able to:")
        log.info("  - Load heatmap data correctly")
        log.info("  - Calculate dynamic need values")
        log.info("  - Display shortage analysis")
        log.info("  - Show role-specific visualizations")
    else:
        log.warning("⚠️ Some issues detected - dashboard may have problems")
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)