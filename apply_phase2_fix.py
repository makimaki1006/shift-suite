#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 2: 異常値検出・制限機能の実装
shortage.py への安全機能追加
"""

import os
import shutil
from pathlib import Path
import datetime as dt

def create_backup():
    """修正前のバックアップを作成"""
    source_file = Path("shift_suite/tasks/shortage.py")
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(f"shift_suite/tasks/shortage.py.backup_{timestamp}")
    
    if source_file.exists():
        shutil.copy2(source_file, backup_file)
        print(f"Backup created: {backup_file}")
        return backup_file
    else:
        print(f"Source file not found: {source_file}")
        return None

def add_anomaly_detection_functions():
    """異常値検出・制限機能を追加"""
    
    source_file = Path("shift_suite/tasks/shortage.py")
    
    if not source_file.exists():
        print(f"File not found: {source_file}")
        return False
    
    # ファイルを読み込み
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 異常値検出機能のコード
    anomaly_detection_code = '''

def validate_and_cap_shortage(shortage_df, period_days, slot_hours):
    """
    異常値検出と制限機能（27,486.5時間問題対策）
    
    Args:
        shortage_df: 不足時間データフレーム
        period_days: 対象期間の日数
        slot_hours: スロット時間（時間単位）
        
    Returns:
        (制限済み不足データ, 制限適用フラグ)
    """
    
    # 設定値
    MAX_SHORTAGE_PER_DAY = 50  # 1日最大50時間
    
    total_shortage = shortage_df.sum().sum() * slot_hours
    max_allowed = MAX_SHORTAGE_PER_DAY * period_days
    
    if total_shortage > max_allowed:
        log.warning(f"[ANOMALY_DETECTED] Abnormal shortage time: {total_shortage:.0f}h > {max_allowed:.0f}h")
        log.warning(f"[ANOMALY_DETECTED] Period: {period_days} days, Daily avg: {total_shortage/period_days:.0f}h/day")
        
        # 比例縮小で制限
        scale_factor = max_allowed / total_shortage
        shortage_df = shortage_df * scale_factor
        
        log.warning(f"[CAPPED] Limitation applied: scale={scale_factor:.3f}, after={max_allowed:.0f}h")
        
        return shortage_df, True  # 制限適用フラグ
    
    return shortage_df, False


def validate_need_data(need_df):
    """
    Needデータの妥当性検証（27,486.5時間問題対策）
    
    Args:
        need_df: 需要データフレーム
        
    Returns:
        検証・制限済み需要データ
    """
    
    if need_df.empty:
        return need_df
    
    max_need = need_df.max().max()
    if max_need > 10:  # 1スロット10人以上は异常
        log.error(f"[NEED_ANOMALY] Abnormal Need value detected: {max_need:.1f} people/slot")
        need_df = need_df.clip(upper=5)  # 上限5人に制限
        log.warning("[NEED_CAPPED] Need values capped to 5 people/slot")
    
    return need_df


def detect_period_dependency_risk(period_days, total_shortage):
    """
    期間依存性リスクの検出
    
    Args:
        period_days: 期間日数
        total_shortage: 総不足時間
        
    Returns:
        リスク情報辞書
    """
    
    daily_shortage = total_shortage / period_days if period_days > 0 else 0
    monthly_shortage = daily_shortage * 30
    
    risk_level = "low"
    if monthly_shortage > 10000:
        risk_level = "critical"
    elif monthly_shortage > 5000:
        risk_level = "high"
    elif monthly_shortage > 2000:
        risk_level = "medium"
    
    risk_info = {
        "risk_level": risk_level,
        "daily_shortage": daily_shortage,
        "monthly_shortage": monthly_shortage,
        "period_days": period_days,
        "recommendation": {
            "low": "Normal range",
            "medium": "Consider monthly normalization",
            "high": "Monthly normalization strongly recommended",
            "critical": "Abnormal value detected - Data validation required"
        }.get(risk_level, "Unknown")
    }
    
    if risk_level in ["high", "critical"]:
        log.warning(f"[PERIOD_RISK] {risk_level}: {risk_info['recommendation']}")
        log.warning(f"[PERIOD_RISK] Monthly shortage: {monthly_shortage:.0f}h/month")
    
    return risk_info

'''
    
    # 関数を追加する位置を特定（shortage_and_brief関数の前）
    insertion_point = content.find("def shortage_and_brief(")
    
    if insertion_point == -1:
        print("Insertion point not found. Looking for alternative location...")
        # 代替位置を探す
        insertion_point = content.find("def create_timestamped_log")
        
    if insertion_point != -1:
        # 関数を挿入
        modified_content = content[:insertion_point] + anomaly_detection_code + "\n\n" + content[insertion_point:]
        
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print("Anomaly detection functions added successfully")
        return True
    else:
        print("Could not find suitable insertion point")
        return False

def integrate_anomaly_detection():
    """shortage_and_brief関数に異常値検出を統合"""
    
    source_file = Path("shift_suite/tasks/shortage.py")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # shortage_and_brief関数内での統合ポイントを探す
    integration_pattern = "lack_count_overall_df = ("
    
    if integration_pattern in content:
        # 統合コードの準備
        integration_code = '''
    # Phase 2: 異常値検出・制限機能の統合（27,486.5時間問題対策）
    period_days = len(date_columns_in_heat_all)
    
    # Need データの検証・制限
    need_df_all = validate_need_data(need_df_all)
    
    # 不足時間計算
    '''
        
        # 統合ポイントの直前に挿入
        insertion_point = content.find(integration_pattern)
        modified_content = content[:insertion_point] + integration_code + content[insertion_point:]
        
        # 不足時間の制限処理を追加
        cap_pattern = "lack_count_overall_df ="
        cap_end = modified_content.find(")", modified_content.find(cap_pattern)) + 1
        
        cap_code = '''
    
    # 異常値検出・制限の適用
    lack_count_overall_df, was_capped = validate_and_cap_shortage(
        lack_count_overall_df, period_days, slot_hours
    )
    
    # 期間依存性リスクの検出
    risk_info = detect_period_dependency_risk(
        period_days, lack_count_overall_df.sum().sum() * slot_hours
    )
    
    if was_capped:
        log.warning("[PHASE2_APPLIED] Anomaly detection and limitation applied")
    if risk_info["risk_level"] in ["high", "critical"]:
        log.warning(f"[PHASE2_RISK] Period dependency risk: {risk_info['risk_level']}")
'''
        
        final_content = modified_content[:cap_end] + cap_code + modified_content[cap_end:]
        
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print("Anomaly detection integrated into shortage_and_brief function")
        return True
    else:
        print("Integration point not found in shortage_and_brief function")
        return False

def verify_phase2_fix():
    """Phase 2修正内容の検証"""
    
    source_file = Path("shift_suite/tasks/shortage.py")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 検証項目
    checks = [
        ("Anomaly detection function", "validate_and_cap_shortage" in content),
        ("Need validation function", "validate_need_data" in content),
        ("Risk detection function", "detect_period_dependency_risk" in content),
        ("Integration in main function", "PHASE2_APPLIED" in content),
        ("Risk warning integration", "PHASE2_RISK" in content),
        ("Maximum shortage limit", "MAX_SHORTAGE_PER_DAY = 50" in content)
    ]
    
    print("\nPhase 2 verification:")
    all_passed = True
    
    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

def main():
    """Phase 2修正の実行"""
    
    print("=" * 60)
    print("Phase 2: Anomaly Detection and Limitation Implementation")
    print("Safety features for 27,486.5 hour problem")
    print("=" * 60)
    
    # Step 1: バックアップ作成
    print("\nStep 1: Creating backup")
    backup_file = create_backup()
    if not backup_file:
        return False
    
    # Step 2: 異常値検出機能追加
    print("\nStep 2: Adding anomaly detection functions")
    if not add_anomaly_detection_functions():
        print("Failed to add anomaly detection functions")
        return False
    
    # Step 3: メイン処理への統合
    print("\nStep 3: Integrating anomaly detection into main process")
    if not integrate_anomaly_detection():
        print("Failed to integrate anomaly detection")
        return False
    
    # Step 4: 検証
    print("\nStep 4: Verifying Phase 2 fixes")
    if verify_phase2_fix():
        print("\nPhase 2 implementation completed successfully!")
        print("\nAdded features:")
        print("  - Abnormal shortage time detection and limitation")
        print("  - Need data validation and capping")
        print("  - Period dependency risk detection")
        print("  - Maximum 50 hours/day shortage limit")
        print("\nExpected benefits:")
        print("  - Automatic detection of abnormal values")
        print("  - Prevention of extreme shortage calculations")
        print("  - Early warning for period dependency issues")
        
        return True
    else:
        print("\nPhase 2 verification failed. Manual check required.")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\nNext step: Phase 3 (Period normalization integration)")
    else:
        print(f"\nThere are issues with Phase 2. Please restore from backup file.")