#!/usr/bin/env python3
"""
Need積算修正ロールバック後の検証スクリプト
"""
import pandas as pd
from pathlib import Path
import json
import datetime

def verify_rollback():
    """ロールバック後の検証実行"""
    print('=' * 60)
    print('Need積算ロールバック検証開始')
    print(f'実行時刻: {datetime.datetime.now()}')
    print('=' * 60)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    # 1. Needファイル存在確認
    print('\n【Step 1: Needファイル存在確認】')
    need_files = list(scenario_dir.glob('need_per_date_slot_role_*.parquet'))
    print(f'検出Needファイル数: {len(need_files)} (期待値: 9)')
    
    expected_roles = [
        '事務・介護', '介護', '介護・相談員', '介護（W_2）', '介護（W_3）',
        '機能訓練士', '看護師', '管理者・相談員', '運転士'
    ]
    
    found_roles = []
    for need_file in need_files:
        for role in expected_roles:
            if role in need_file.name:
                found_roles.append(role)
                break
    
    print(f'対応職種数: {len(found_roles)}/{len(expected_roles)}')
    
    if len(need_files) != 9:
        print('❌ ERROR: Needファイル数が不正')
        return False
    
    # 2. ファイルサイズ確認
    print('\n【Step 2: ファイルサイズ確認】')
    size_ok = True
    for need_file in need_files:
        size_mb = need_file.stat().st_size / (1024 * 1024)
        print(f'  {need_file.name}: {size_mb:.2f}MB')
        
        if size_mb < 0.01:  # 10KB未満は異常
            print(f'❌ ERROR: {need_file.name} のサイズが異常に小さい')
            size_ok = False
    
    if not size_ok:
        return False
    
    # 3. intermediate_data.parquet 確認
    print('\n【Step 3: 基礎データ確認】')
    try:
        intermediate_data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        print(f'intermediate_data レコード数: {len(intermediate_data)}')
        print(f'期間: {intermediate_data["ds"].min()} ～ {intermediate_data["ds"].max()}')
        
        if len(intermediate_data) != 6073:
            print('⚠️ WARNING: レコード数が期待値(6,073)と異なる')
    
    except Exception as e:
        print(f'❌ ERROR: intermediate_data 読み込み失敗 - {e}')
        return False
    
    # 4. Needファイル内容確認
    print('\n【Step 4: Needファイル内容確認】')
    total_need = 0
    need_summary = {}
    
    for need_file in need_files:
        try:
            df = pd.read_parquet(need_file)
            file_need = df.sum().sum()
            total_need += file_need
            
            role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
            need_summary[role_name] = {
                'need_total': file_need,
                'shape': df.shape,
                'non_zero_ratio': (df > 0).sum().sum() / (df.shape[0] * df.shape[1])
            }
            
            print(f'  {role_name}: {file_need} (非ゼロ比率: {need_summary[role_name]["non_zero_ratio"]:.3f})')
            
        except Exception as e:
            print(f'❌ ERROR: {need_file} 読み込み失敗 - {e}')
            return False
    
    print(f'Need総合計: {total_need}')
    
    # 5. 組織分析実行テスト
    print('\n【Step 5: 組織分析実行テスト】')
    try:
        # comprehensive_organizational_shortage_analyzer の簡易実行
        intermediate_data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        
        # 動的スロット時間計算
        time_slots = intermediate_data['ds'].dt.time.unique()
        slot_hours = 24 / len(time_slots)
        period_days = intermediate_data['ds'].dt.date.nunique()
        
        # 組織全体の配置時間
        total_records = len(intermediate_data)
        total_allocated_hours = total_records * slot_hours
        
        # 組織全体のNeed時間
        org_need_hours = total_need * slot_hours
        
        # 日次差分
        org_difference = org_need_hours - total_allocated_hours
        org_daily_difference = org_difference / period_days
        
        print(f'組織全体需要: {org_need_hours:.1f}時間')
        print(f'組織全体配置: {total_allocated_hours:.1f}時間')
        print(f'組織全体日次差分: {org_daily_difference:.1f}時間/日')
        
        # ベースライン値(-22.7時間/日)との比較
        baseline_daily_diff = -22.7
        diff_from_baseline = abs(org_daily_difference - baseline_daily_diff)
        
        print(f'ベースラインからの乖離: {diff_from_baseline:.1f}時間/日')
        
        if diff_from_baseline < 5.0:  # 5時間以内の誤差
            print('✅ OK: ベースライン値に近い値に復旧')
            baseline_ok = True
        else:
            print('⚠️ WARNING: ベースライン値と乖離が大きい')
            baseline_ok = False
        
    except Exception as e:
        print(f'❌ ERROR: 組織分析実行失敗 - {e}')
        return False
    
    # 6. 介護系職種の比率確認
    print('\n【Step 6: 介護系職種比率確認】')
    care_roles = ['介護', '介護・相談員', '介護（W_2）', '介護（W_3）', '事務・介護']
    
    care_need_total = 0
    care_actual_total = 0
    
    for role_key, role_data in need_summary.items():
        if any(care_role in role_key for care_role in care_roles):
            care_need_total += role_data['need_total']
    
    # 実配置
    care_actual_records = 0
    for care_role in care_roles:
        matching_records = intermediate_data[
            intermediate_data['role'].str.contains(care_role, na=False)
        ]
        care_actual_records += len(matching_records)
    
    if care_actual_records > 0:
        care_ratio = care_need_total / care_actual_records
        print(f'介護系Need/実配置比率: {care_ratio:.2f}')
        
        # ベースライン範囲(0.09-0.54)の確認
        if 0.05 <= care_ratio <= 0.60:
            print('✅ OK: 介護系比率がベースライン範囲内')
            care_ratio_ok = True
        else:
            print('❌ ERROR: 介護系比率がベースライン範囲外')
            care_ratio_ok = False
    else:
        care_ratio_ok = False
    
    # 7. 総合判定
    print('\n' + '=' * 60)
    print('ロールバック検証結果サマリー')
    print('=' * 60)
    
    checks = [
        ('Needファイル数', len(need_files) == 9),
        ('ファイルサイズ', size_ok),
        ('Need総合計値', total_need > 0),
        ('組織分析実行', True),  # Step5で例外が発生しなければOK
        ('ベースライン復旧', baseline_ok if 'baseline_ok' in locals() else False),
        ('介護系比率', care_ratio_ok if 'care_ratio_ok' in locals() else False)
    ]
    
    passed_checks = sum(1 for _, result in checks if result)
    total_checks = len(checks)
    
    print(f'\n検証項目: {passed_checks}/{total_checks} 合格')
    
    for check_name, result in checks:
        status = '✅ PASS' if result else '❌ FAIL'
        print(f'  {check_name}: {status}')
    
    overall_success = passed_checks >= total_checks - 1  # 1項目まで許容
    
    print(f'\n最終判定: {"✅ ロールバック成功" if overall_success else "❌ ロールバック失敗"}')
    
    # 検証レポート保存
    report = {
        'verification_timestamp': datetime.datetime.now().isoformat(),
        'need_files_count': len(need_files),
        'total_need': total_need,
        'org_daily_difference': org_daily_difference if 'org_daily_difference' in locals() else None,
        'care_ratio': care_ratio if 'care_ratio' in locals() else None,
        'checks_passed': passed_checks,
        'checks_total': total_checks,
        'overall_success': overall_success,
        'need_summary': need_summary
    }
    
    with open('rollback_verification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f'\n検証レポート保存: rollback_verification_report.json')
    
    return overall_success

if __name__ == "__main__":
    success = verify_rollback()
    exit(0 if success else 1)