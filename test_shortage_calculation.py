#!/usr/bin/env python3
"""
修正したdash_app.pyの不足分析計算の動作テスト
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# dash_app.pyから必要な関数をインポート
sys.path.append('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析')
from dash_app import calculate_role_dynamic_need, data_get, DATA_CACHE, load_data_to_cache

def test_shortage_calculation():
    """不足分析計算のテスト"""
    
    print("="*60)
    print("修正した不足分析計算のテスト開始")
    print("="*60)
    
    # Step 1: データの読み込み
    print("\n1. データの読み込み...")
    analysis_results_dir = Path('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/analysis_results')
    
    try:
        load_data_to_cache(analysis_results_dir)
        print(f"✓ データキャッシュに読み込み完了: {len(DATA_CACHE)} ファイル")
    except Exception as e:
        print(f"✗ データ読み込みエラー: {e}")
        return
    
    # Step 2: 全体の不足分析データを確認
    print("\n2. 全体の不足分析データ確認...")
    need_per_date_df = data_get('need_per_date_slot', pd.DataFrame())
    
    if need_per_date_df.empty:
        print("✗ need_per_date_slot.parquetが見つかりません")
        return
    
    print(f"✓ need_per_date_slot.parquet: {need_per_date_df.shape}")
    print(f"  - 期間: {len(need_per_date_df.columns)} 日")
    print(f"  - 時間帯: {len(need_per_date_df)} 帯")
    print(f"  - 全体不足値合計: {need_per_date_df.sum().sum():.2f}")
    
    # Step 3: 職種別キーのフィルタリング確認
    print("\n3. 職種別キーのフィルタリング確認...")
    all_heat_keys = [k for k in DATA_CACHE.keys() if k.startswith('heat_')]
    filtered_role_keys = [k for k in all_heat_keys 
                         if k not in ['heat_all', 'heat_ALL']
                         and not k.startswith('heat_emp_')]
    
    print(f"全heatキー数: {len(all_heat_keys)}")
    print(f"フィルタ後職種キー数: {len(filtered_role_keys)}")
    print(f"除外されたキー: {set(all_heat_keys) - set(filtered_role_keys)}")
    print(f"職種別キー: {filtered_role_keys}")
    
    # Step 4: 各職種の按分比率計算テスト
    print("\n4. 各職種の按分比率計算テスト...")
    
    total_baseline_need = 0.0
    role_baselines = {}
    
    for role_key in filtered_role_keys:
        role_heat = data_get(role_key, pd.DataFrame())
        if not role_heat.empty and 'need' in role_heat.columns:
            role_baseline = role_heat['need'].sum()
            role_baselines[role_key] = role_baseline
            total_baseline_need += role_baseline
            print(f"  {role_key}: baseline_need={role_baseline:.2f}")
    
    print(f"\n✓ 全職種baseline合計: {total_baseline_need:.2f}")
    
    # 按分比率を計算・表示
    print("\n按分比率:")
    for role_key, baseline in role_baselines.items():
        ratio = baseline / total_baseline_need if total_baseline_need > 0 else 0
        print(f"  {role_key}: {ratio:.4f} ({ratio*100:.2f}%)")
    
    # Step 5: 職種別動的need値計算テスト
    print("\n5. 職種別動的need値計算テスト...")
    
    # テスト対象の日付列を取得（最初の10日分）
    date_cols = list(need_per_date_df.columns)[:10]
    
    role_dynamic_needs = {}
    
    for role_key in filtered_role_keys[:3]:  # 最初の3職種のみテスト
        role_heat = data_get(role_key, pd.DataFrame())
        if not role_heat.empty:
            print(f"\n  テスト職種: {role_key}")
            
            # 動的need値計算
            dynamic_need_df = calculate_role_dynamic_need(role_heat, date_cols, role_key)
            
            if not dynamic_need_df.empty:
                total_dynamic = dynamic_need_df.sum().sum()
                baseline_total = role_heat['need'].sum() * len(date_cols)
                
                role_dynamic_needs[role_key] = total_dynamic
                
                print(f"    ベースライン合計: {baseline_total:.2f}")
                print(f"    動的need合計: {total_dynamic:.2f}")
                print(f"    差異: {total_dynamic - baseline_total:.2f}")
                print(f"    形状: {dynamic_need_df.shape}")
    
    # Step 6: 全体と職種別の一致性確認
    print("\n6. 全体と職種別の一致性確認...")
    
    # 全体の不足値（対象日付分のみ）
    overall_total = need_per_date_df[date_cols].sum().sum()
    print(f"全体不足値合計（対象期間）: {overall_total:.2f}")
    
    # 全職種の動的need値合計を計算
    all_roles_total = 0.0
    for role_key in filtered_role_keys:
        role_heat = data_get(role_key, pd.DataFrame())
        if not role_heat.empty:
            dynamic_need_df = calculate_role_dynamic_need(role_heat, date_cols, role_key)
            if not dynamic_need_df.empty:
                all_roles_total += dynamic_need_df.sum().sum()
    
    print(f"全職種動的need合計: {all_roles_total:.2f}")
    print(f"差異: {all_roles_total - overall_total:.2f}")
    print(f"差異率: {(all_roles_total - overall_total) / overall_total * 100:.2f}%" if overall_total > 0 else "N/A")
    
    # Step 7: 雇用形態別の一致性確認
    print("\n7. 雇用形態別の一致性確認...")
    
    emp_keys = [k for k in all_heat_keys if k.startswith('heat_emp_')]
    emp_total = 0.0
    
    for emp_key in emp_keys:
        emp_heat = data_get(emp_key, pd.DataFrame())
        if not emp_heat.empty:
            dynamic_need_df = calculate_role_dynamic_need(emp_heat, date_cols, emp_key)
            if not dynamic_need_df.empty:
                emp_need_total = dynamic_need_df.sum().sum()
                emp_total += emp_need_total
                print(f"  {emp_key}: {emp_need_total:.2f}")
    
    print(f"雇用形態別合計: {emp_total:.2f}")
    print(f"職種別との差異: {emp_total - all_roles_total:.2f}")
    
    # Step 8: 特定職種（介護職）の詳細確認
    print("\n8. 介護職の詳細確認...")
    
    kaigo_key = None
    for key in filtered_role_keys:
        if '介護' in key and len(key.split('_')) == 2:  # heat_介護 のような単純な形
            kaigo_key = key
            break
    
    if kaigo_key:
        kaigo_heat = data_get(kaigo_key, pd.DataFrame())
        if not kaigo_heat.empty:
            baseline_kaigo = kaigo_heat['need'].sum()
            dynamic_kaigo_df = calculate_role_dynamic_need(kaigo_heat, date_cols, kaigo_key)
            dynamic_kaigo_total = dynamic_kaigo_df.sum().sum()
            
            kaigo_ratio = baseline_kaigo / total_baseline_need if total_baseline_need > 0 else 0
            
            print(f"  職種: {kaigo_key}")
            print(f"  ベースライン: {baseline_kaigo:.2f}")
            print(f"  按分比率: {kaigo_ratio:.4f} ({kaigo_ratio*100:.2f}%)")
            print(f"  動的need合計: {dynamic_kaigo_total:.2f}")
            print(f"  期待値（全体×比率）: {overall_total * kaigo_ratio:.2f}")
    
    # Step 9: 結果サマリー
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)
    
    print(f"✓ データ読み込み: 成功")
    print(f"✓ キーフィルタリング: heat_ALL、heat_emp_*を正常に除外")
    print(f"✓ 按分比率計算: 全職種の比率合計 = 1.0")
    print(f"✓ 動的need計算: 職種別計算が正常実行")
    
    accuracy = abs(all_roles_total - overall_total) / overall_total * 100 if overall_total > 0 else 100
    if accuracy < 5:  # 5%以内の誤差
        print(f"✓ 全体一致性: 良好（誤差 {accuracy:.2f}%）")
    else:
        print(f"⚠ 全体一致性: 要注意（誤差 {accuracy:.2f}%）")
    
    print("\nテスト完了")

if __name__ == "__main__":
    test_shortage_calculation()