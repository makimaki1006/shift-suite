#!/usr/bin/env python3
"""
動的連続勤務検出システムの簡潔なテスト
文字化け回避のため英語出力を使用
"""

import sys
import logging
from pathlib import Path

# ログ抑制
logging.basicConfig(level=logging.CRITICAL)

def test_file(excel_path: Path, sheet_name: str, header_row: int):
    """簡潔な動的検出テスト"""
    try:
        # ログ抑制
        for logger_name in ['shift_suite', 'analysis', 'root']:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        
        from shift_suite.tasks.dynamic_continuous_shift_detector import DynamicContinuousShiftDetector
        from shift_suite.tasks.io_excel import ingest_excel
        
        print(f"Testing: {excel_path.name}")
        
        # データ読み込み
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=[sheet_name],
            header_row=header_row,
            slot_minutes=15
        )
        
        print(f"  Records loaded: {len(long_df):,}")
        
        # 勤務コード分析
        shift_codes = long_df['code'].value_counts()
        active_codes = [code for code in shift_codes.index if code.strip()]
        
        print(f"  Shift codes found: {len(active_codes)} types")
        print(f"  Sample codes: {active_codes[:5]}")
        
        # 動的検出実行
        detector = DynamicContinuousShiftDetector()
        continuous_shifts = detector.detect_continuous_shifts(long_df, wt_df)
        summary = detector.get_detection_summary()
        
        # 結果表示
        print(f"  Dynamic learning results:")
        print(f"    Patterns learned: {summary.get('detected_patterns', 0)}")
        print(f"    Rules generated: {summary.get('active_rules', 0)}")
        print(f"    Continuous shifts detected: {len(continuous_shifts)}")
        
        if len(continuous_shifts) > 0:
            print(f"    Average duration: {summary.get('average_duration_hours', 0):.1f}h")
            print(f"    Max duration: {summary.get('max_duration_hours', 0):.1f}h")
            
            # 検出例
            example = continuous_shifts[0]
            print(f"    Example: {example.staff} - {example.start_pattern.code}->{example.end_pattern.code}")
        
        # 設定保存
        config_file = Path(f"config_{excel_path.stem}.json")
        detector.export_config(config_file)
        print(f"  Config saved: {config_file}")
        
        return {
            'file': excel_path.name,
            'success': True,
            'records': len(long_df),
            'shift_codes': len(active_codes),
            'patterns': summary.get('detected_patterns', 0),
            'rules': summary.get('active_rules', 0),
            'continuous_shifts': len(continuous_shifts),
            'sample_codes': active_codes[:3]
        }
        
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return {
            'file': excel_path.name,
            'success': False,
            'error': str(e)
        }

def main():
    """動的証明テスト実行"""
    print("Dynamic Continuous Shift Detection System - Final Proof Test")
    print("=" * 60)
    
    test_configs = [
        {
            'file': Path("デイ_テスト用データ_休日精緻.xlsx"),
            'sheet': 'R7.6',
            'header': 1
        },
        {
            'file': Path("ショート_テスト用データ.xlsx"),
            'sheet': 'R7.6',
            'header': 1
        }
    ]
    
    results = []
    
    for config in test_configs:
        if not config['file'].exists():
            print(f"File not found: {config['file'].name}")
            results.append({'file': config['file'].name, 'success': False})
            continue
            
        result = test_file(config['file'], config['sheet'], config['header'])
        results.append(result)
        print()
    
    # 最終サマリー
    print("=== FINAL RESULTS ===")
    successful = [r for r in results if r.get('success', False)]
    
    print(f"Test results: {len(successful)}/{len(results)} successful")
    
    all_codes = set()
    total_patterns = 0
    total_rules = 0
    total_continuous = 0
    
    for result in successful:
        print(f"SUCCESS {result['file']}:")
        print(f"   Records: {result['records']:,}, Codes: {result['shift_codes']}")
        print(f"   Learning: {result['patterns']} patterns, {result['rules']} rules")
        print(f"   Continuous shifts: {result['continuous_shifts']}")
        print(f"   Sample codes: {result['sample_codes']}")
        
        all_codes.update(result['sample_codes'])
        total_patterns += result['patterns']
        total_rules += result['rules']
        total_continuous += result['continuous_shifts']
    
    for result in results:
        if not result.get('success', False):
            print(f"FAILED {result['file']}: {result.get('error', 'Unknown error')}")
    
    if len(successful) == len(results) and total_continuous > 0:
        print("\n=== DYNAMIC SYSTEM CAPABILITY PROVEN ===")
        print(f"Total code types: {len(all_codes)} - {sorted(list(all_codes))}")
        print(f"Total continuous shifts detected: {total_continuous}")
        print(f"Total patterns learned: {total_patterns}")
        print(f"Total rules generated: {total_rules}")
        print("COMPLETE DYNAMIC SYSTEM PROOF SUCCESSFUL!")
        return True
    else:
        print("Some tests failed or no continuous shifts detected.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)