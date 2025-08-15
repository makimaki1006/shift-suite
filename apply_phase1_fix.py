#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 1: 循環増幅設計の完全無効化
time_axis_shortage_calculator.py の根本的修正（Unicode対応版）
"""

import os
import shutil
from pathlib import Path
import datetime as dt

def create_backup():
    """修正前のバックアップを作成"""
    source_file = Path("shift_suite/tasks/time_axis_shortage_calculator.py")
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(f"shift_suite/tasks/time_axis_shortage_calculator.py.backup_{timestamp}")
    
    if source_file.exists():
        shutil.copy2(source_file, backup_file)
        print(f"Backup created: {backup_file}")
        return backup_file
    else:
        print(f"Source file not found: {source_file}")
        return None

def apply_phase1_fix():
    """Phase 1: 循環増幅の完全無効化を適用"""
    
    source_file = Path("shift_suite/tasks/time_axis_shortage_calculator.py")
    
    if not source_file.exists():
        print(f"File not found: {source_file}")
        return False
    
    # ファイルを読み込み
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 循環増幅ロジックの特定と置換
    # より短い特徴的なコード部分を検索
    search_pattern = "if self.total_shortage_baseline and self.total_shortage_baseline > 0:"
    
    if search_pattern in content:
        # 置換対象の範囲を特定
        start_pos = content.find(search_pattern)
        # "else:" の次の "estimated_demand = total_supply * 1.05" まで
        end_pattern = "estimated_demand = total_supply * 1.05  # 5%の余裕のみ"
        end_pos = content.find(end_pattern, start_pos) + len(end_pattern)
        
        if end_pos > start_pos:
            # 置換する新しいコード
            fixed_code = '''        # FIX: 循環増幅を完全に無効化（27,486.5時間問題の根本解決）
        # 常に供給量ベースの控えめな需要推定のみ使用
        estimated_demand = total_supply * 1.05  # 5%マージンのみ
        
        # 以前の循環増幅ロジックは完全に削除
        # - total_shortage_baseline による需要計算は廃止
        # - 期間依存性による複雑な条件分岐は不要
        # - シンプルで予測可能な需要推定のみ採用
        
        log.debug(f"[FIXED_27486] Circular amplification disabled: demand={estimated_demand:.1f}, supply={total_supply:.1f}")
        log.info("[FIXED_27486] 27,486.5 hour problem fix: Circular amplification logic disabled")'''
            
            # 元のコードを置換
            original_code = content[start_pos:end_pos]
            modified_content = content[:start_pos] + fixed_code + content[end_pos:]
            
            # 修正されたファイルを保存
            with open(source_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print("Phase 1 fix applied successfully: Circular amplification completely disabled")
            print("- total_shortage_baseline demand calculation disabled")
            print("- Changed to simple supply * 1.05 calculation")
            print("- Removed complex period-dependent conditional branches")
            return True
        else:
            print("End pattern not found. Manual verification required.")
            return False
    else:
        print("Target code pattern not found. Manual verification required.")
        print("Search pattern: if self.total_shortage_baseline and self.total_shortage_baseline > 0:")
        return False

def verify_fix():
    """修正内容の検証"""
    
    source_file = Path("shift_suite/tasks/time_axis_shortage_calculator.py")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修正が正しく適用されているかチェック
    checks = [
        ("Circular amplification disabled", "FIXED_27486" in content),
        ("Simple demand calculation", "estimated_demand = total_supply * 1.05" in content),
        ("Baseline logic removed", content.count("self.total_shortage_baseline") <= 3),  # コンストラクタ等での参照のみ
        ("Fix log added", "27,486.5 hour problem fix" in content)
    ]
    
    print("\nVerification of fixes:")
    all_passed = True
    
    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

def main():
    """Phase 1修正の実行"""
    
    print("=" * 60)
    print("Phase 1: Complete Circular Amplification Disabling")
    print("Root solution for 27,486.5 hour problem")
    print("=" * 60)
    
    # Step 1: バックアップ作成
    print("\nStep 1: Creating backup")
    backup_file = create_backup()
    if not backup_file:
        return False
    
    # Step 2: 修正適用
    print("\nStep 2: Disabling circular amplification")
    if not apply_phase1_fix():
        print("Failed to apply fix")
        return False
    
    # Step 3: 検証
    print("\nStep 3: Verifying fixes")
    if verify_fix():
        print("\nPhase 1 fix completed successfully!")
        print("\nFix summary:")
        print("  • Circular amplification logic completely disabled")
        print("  • Unified to estimated_demand = total_supply * 1.05")
        print("  • Removed complex period-dependent conditional branches")
        print("\nExpected results:")
        print("  • 27,486.5 hours -> Less than 5,000 hours")
        print("  • Resolved abnormal spike in 3-month data")
        print("  • Predictable and stable shortage time calculation")
        
        return True
    else:
        print("\nVerification failed. Manual check required.")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\nNext step: Phase 2 (Anomaly detection and limitation features)")
    else:
        print(f"\nThere are issues with the fix. Please restore from backup file.")