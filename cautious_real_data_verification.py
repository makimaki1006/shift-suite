#!/usr/bin/env python3
"""
慎重な実データ検証スクリプト
Phase 2進行前の必須事前確認
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
from datetime import datetime

def cautious_real_data_verification():
    """実データの慎重な検証と安全性確認"""
    
    print("=" * 80)
    print("慎重な実データ検証: Phase 2事前確認")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. 実データファイルの存在確認
    print("\n【STEP 1: 実データファイル存在確認】")
    
    base_dir = Path("extracted_results/out_p25_based")
    required_files = {
        'need_data': 'need_per_date_slot.parquet',
        'heatmap_meta': 'heatmap.meta.json',
        'stats_summary': 'stats_summary.txt'
    }
    
    missing_files = []
    for name, filename in required_files.items():
        filepath = base_dir / filename
        if filepath.exists():
            print(f"OK {name}: {filename} (存在確認)")
        else:
            print(f"NG {name}: {filename} (ファイルなし)")
            missing_files.append(filename)
    
    if missing_files:
        print(f"ABORT 必須ファイル不足: {missing_files}")
        return False
    
    # 2. need_per_date_slot.parquetの詳細調査
    print("\n【STEP 2: need_per_date_slot.parquet 詳細調査】")
    
    try:
        need_data_path = base_dir / 'need_per_date_slot.parquet'
        print(f"読み込み対象: {need_data_path}")
        
        # ファイルサイズ確認
        file_size = need_data_path.stat().st_size
        print(f"ファイルサイズ: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        if file_size > 10 * 1024 * 1024:  # 10MB超
            print("WARN ファイルサイズが大きすぎる可能性 (>10MB)")
            
        # データ読み込み（安全な方法）
        need_df = pd.read_parquet(need_data_path)
        
        print(f"データ形状: {need_df.shape}")
        print(f"メモリ使用量: {need_df.memory_usage(deep=True).sum() / 1024:.1f} KB")
        
        # カラム構造の確認
        print(f"カラム数: {len(need_df.columns)}")
        print("主要カラム:")
        for i, col in enumerate(need_df.columns[:10]):  # 最初の10カラムのみ
            print(f"  [{i}] {col} ({need_df[col].dtype})")
        if len(need_df.columns) > 10:
            print(f"  ... 他{len(need_df.columns)-10}カラム")
            
        # データ品質確認
        null_count = need_df.isnull().sum().sum()
        print(f"NULL値総数: {null_count}")
        
        if null_count > need_df.size * 0.1:  # 10%以上NULL
            print("WARN NULL値が多すぎる (>10%)")
            
    except Exception as e:
        print(f"ERROR need_data読み込みエラー: {e}")
        print("詳細エラー情報:")
        import traceback
        print(traceback.format_exc()[:500])  # エラー詳細（500文字まで）
        return False
    
    # 3. 職種データの実在確認
    print("\n【STEP 3: 職種データ実在確認】")
    
    try:
        if 'role' in need_df.columns:
            unique_roles = need_df['role'].unique()
            print(f"実際の職種数: {len(unique_roles)}")
            print(f"職種一覧: {list(unique_roles)}")
            
            # 介護職種の確認
            care_roles = [role for role in unique_roles if '介護' in str(role)]
            print(f"介護関連職種: {care_roles}")
            
            if not care_roles:
                print("ERROR ターゲット職種（介護）が存在しない")
                return False
                
            # 各職種のデータ量確認
            role_counts = need_df['role'].value_counts()
            print("職種別データ件数:")
            for role in care_roles[:3]:  # 介護関連3職種まで
                count = role_counts.get(role, 0)
                print(f"  {role}: {count}件")
                if count == 0:
                    print(f"  WARN {role}のデータが0件")
                    
        else:
            print("ERROR 'role'カラムが存在しない")
            print(f"利用可能カラム: {list(need_df.columns[:5])}")
            return False
            
    except Exception as e:
        print(f"ERROR 職種データ確認エラー: {e}")
        return False
    
    # 4. 時間軸データの構造確認
    print("\n【STEP 4: 時間軸データ構造確認】")
    
    try:
        # 時間関連カラムの検出
        time_columns = [col for col in need_df.columns if 'slot_' in col or '時' in col]
        print(f"時間軸カラム数: {len(time_columns)}")
        
        if time_columns:
            print(f"時間軸カラム例: {time_columns[:5]}")
            
            # 時間データの数値確認
            if len(time_columns) > 0:
                sample_col = time_columns[0]
                sample_data = need_df[sample_col].describe()
                print(f"サンプル時間データ統計 ({sample_col}):")
                print(f"  平均: {sample_data.get('mean', 0):.2f}")
                print(f"  最大: {sample_data.get('max', 0):.2f}")
                print(f"  最小: {sample_data.get('min', 0):.2f}")
                
                # 異常値チェック
                if sample_data.get('max', 0) > 100:
                    print("WARN 時間データに異常値の可能性 (>100)")
                if sample_data.get('min', 0) < 0:
                    print("WARN 時間データに負値の可能性")
        else:
            print("ERROR 時間軸カラムが見つからない")
            return False
            
    except Exception as e:
        print(f"ERROR 時間軸データ確認エラー: {e}")
        return False
    
    # 5. メタデータとの整合性確認
    print("\n【STEP 5: メタデータ整合性確認】")
    
    try:
        meta_path = base_dir / 'heatmap.meta.json'
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
            
        meta_roles = meta_data.get('roles', [])
        actual_roles = list(need_df['role'].unique()) if 'role' in need_df.columns else []
        
        print(f"メタデータ職種数: {len(meta_roles)}")
        print(f"実データ職種数: {len(actual_roles)}")
        
        # 職種の一致確認
        missing_in_data = set(meta_roles) - set(actual_roles)
        extra_in_data = set(actual_roles) - set(meta_roles)
        
        if missing_in_data:
            print(f"WARN メタにあるが実データにない職種: {missing_in_data}")
        if extra_in_data:
            print(f"WARN 実データにあるがメタにない職種: {extra_in_data}")
            
        consistency_rate = len(set(meta_roles) & set(actual_roles)) / max(len(meta_roles), 1) * 100
        print(f"メタデータ整合率: {consistency_rate:.1f}%")
        
        if consistency_rate < 80:
            print("ERROR メタデータと実データの整合性不足 (<80%)")
            return False
            
    except Exception as e:
        print(f"ERROR メタデータ整合性確認エラー: {e}")
        return False
    
    # 6. 最終的なリスク評価
    print("\n【STEP 6: Phase 2進行リスク評価】")
    
    risk_factors = []
    
    # データ量リスク
    if need_df.shape[0] > 10000:
        risk_factors.append("大量データ処理リスク")
    if need_df.shape[1] > 100:
        risk_factors.append("高次元データ処理リスク")
        
    # データ品質リスク  
    if null_count > 0:
        risk_factors.append("NULL値含有リスク")
    if len(time_columns) > 50:
        risk_factors.append("時間軸複雑性リスク")
        
    # システムリスク
    memory_mb = need_df.memory_usage(deep=True).sum() / (1024*1024)
    if memory_mb > 100:
        risk_factors.append("メモリ使用量リスク")
        
    print(f"識別されたリスク要因: {len(risk_factors)}個")
    for i, risk in enumerate(risk_factors, 1):
        print(f"  {i}. {risk}")
    
    # 最終判定
    if len(risk_factors) == 0:
        risk_level = "低"
        proceed_recommendation = "GO"
    elif len(risk_factors) <= 2:
        risk_level = "中"
        proceed_recommendation = "条件付きGO"
    else:
        risk_level = "高"  
        proceed_recommendation = "NO-GO"
    
    print(f"\n総合リスクレベル: {risk_level}")
    print(f"Phase 2進行推奨: {proceed_recommendation}")
    
    # 7. 最終レポート
    print("\n【Phase 2事前検証 最終レポート】")
    print(f"実データファイル: 正常読み込み可能")
    print(f"データ規模: {need_df.shape[0]:,}行 × {need_df.shape[1]}列")
    print(f"メモリ使用量: {memory_mb:.1f}MB")
    print(f"対象職種確認: {len(care_roles)}個の介護関連職種")
    print(f"時間軸カラム: {len(time_columns)}個")
    print(f"データ整合性: {consistency_rate:.1f}%")
    
    if proceed_recommendation == "GO":
        print("\nOK Phase 2進行可能 - 実データでの動作が期待できる")
        return True
    elif proceed_recommendation == "条件付きGO":
        print("\nWARN Phase 2進行は可能だが追加の注意が必要")
        print("推奨事項:")
        print("- メモリ使用量の監視")
        print("- エラーハンドリングの強化") 
        print("- 段階的な処理実装")
        return True
    else:
        print("\nNG Phase 2進行は推奨されない - リスクが高すぎる")
        return False

if __name__ == "__main__":
    success = cautious_real_data_verification()
    sys.exit(0 if success else 1)