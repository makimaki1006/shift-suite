#!/usr/bin/env python
"""
shortage.py の重複排除ロジック改善パッチ

このパッチをshortage.pyの600-635行に適用することで、
職種別needファイルの重複加算問題を解決します。
"""

import re
import pandas as pd
from pathlib import Path
import logging

def improved_role_deduplication(need_role_files, log):
    """
    改善された職種重複排除ロジック
    
    Args:
        need_role_files: 職種別needファイルのリスト
        log: ロガー
        
    Returns:
        選択された主要ファイルのリスト
    """
    log.info(f"[IMPROVED_DEDUP] 職種重複排除開始: {len(need_role_files)}個のファイル")
    
    # 1. 基本職種パターン定義
    base_role_patterns = {
        '介護': r'need_per_date_slot_role_介護\.parquet$',  # 正確な介護のみ
        '看護師': r'need_per_date_slot_role_看護師\.parquet$',
        '事務': r'need_per_date_slot_role_事務\.parquet$', 
        '機能訓練士': r'need_per_date_slot_role_機能訓練士\.parquet$',
        '運転士': r'need_per_date_slot_role_運転士\.parquet$',
        '管理者': r'need_per_date_slot_role_管理者\.parquet$'
    }
    
    # 2. 除外すべき重複パターン
    exclusion_patterns = [
        r'介護\（W_\d+\）',    # 介護（W_2）、介護（W_3）など
        r'介護・',             # 介護・相談員など  
        r'・介護',             # 事務・介護など
        r'管理者・',           # 管理者・相談員など
        r'・管理者',           # ・管理者など
    ]
    
    selected_files = []
    excluded_files = []
    role_file_groups = {}
    
    # 3. ファイル分類
    for file_path in need_role_files:
        file_name = file_path.name
        
        # 除外パターンチェック
        is_excluded = any(re.search(pattern, file_name) for pattern in exclusion_patterns)
        
        if is_excluded:
            excluded_files.append(file_path)
            log.warning(f"[IMPROVED_DEDUP] 重複職種除外: {file_name}")
            continue
        
        # 基本職種パターンマッチング
        matched_role = None
        for role, pattern in base_role_patterns.items():
            if re.search(pattern, file_name):
                matched_role = role
                break
        
        if matched_role:
            if matched_role not in role_file_groups:
                role_file_groups[matched_role] = []
            role_file_groups[matched_role].append(file_path)
        else:
            # 不明な職種は個別に処理
            selected_files.append(file_path)
            log.info(f"[IMPROVED_DEDUP] 不明職種を個別追加: {file_name}")
    
    # 4. 各職種グループから最適なファイルを選択
    for role, files in role_file_groups.items():
        if len(files) == 1:
            selected_files.append(files[0])
            log.info(f"[IMPROVED_DEDUP] {role}: 単一ファイル -> {files[0].name}")
        else:
            # 複数ファイルがある場合は最大需要のファイルを選択
            best_file = None
            max_need = 0
            
            for file_path in files:
                try:
                    df = pd.read_parquet(file_path)
                    total_need = df.sum().sum()
                    if total_need > max_need:
                        max_need = total_need
                        best_file = file_path
                    log.info(f"[IMPROVED_DEDUP] {role} 候補: {file_path.name} (需要: {total_need:.1f})")
                except Exception as e:
                    log.error(f"[IMPROVED_DEDUP] ファイル読み込みエラー {file_path.name}: {e}")
            
            if best_file:
                selected_files.append(best_file)
                log.info(f"[IMPROVED_DEDUP] {role}: 最大需要ファイル選択 -> {best_file.name}")
    
    # 5. 結果レポート
    total_original_need = 0
    total_selected_need = 0
    
    for file_path in need_role_files:
        try:
            df = pd.read_parquet(file_path)
            total_original_need += df.sum().sum()
        except:
            pass
    
    for file_path in selected_files:
        try:
            df = pd.read_parquet(file_path)
            total_selected_need += df.sum().sum()
        except:
            pass
    
    reduction_ratio = ((total_original_need - total_selected_need) / total_original_need * 100) if total_original_need > 0 else 0
    
    log.info(f"[IMPROVED_DEDUP] === 重複排除完了 ===")
    log.info(f"[IMPROVED_DEDUP] 元ファイル数: {len(need_role_files)}個")
    log.info(f"[IMPROVED_DEDUP] 選択ファイル数: {len(selected_files)}個")
    log.info(f"[IMPROVED_DEDUP] 除外ファイル数: {len(excluded_files)}個")
    log.info(f"[IMPROVED_DEDUP] 元総需要: {total_original_need:.1f}")
    log.info(f"[IMPROVED_DEDUP] 修正後需要: {total_selected_need:.1f}")
    log.info(f"[IMPROVED_DEDUP] 削減率: {reduction_ratio:.1f}%")
    
    return selected_files

# shortage.py の600-635行を以下のコードで置き換える
def replacement_code_for_shortage_py():
    """
    shortage.py に適用する置き換えコード
    
    # shortage.py の600-635行を以下で置き換え:
    
    need_role_files = list(out_dir_path.glob("need_per_date_slot_role_*.parquet"))
    
    if need_role_files:
        log.info(f"[shortage] ★★★ 改善版重複排除: {len(need_role_files)}個の職種別Needファイルを処理 ★★★")
        
        # 改善された重複排除ロジックを適用
        primary_role_files = improved_role_deduplication(need_role_files, log)
        
        combined_need_df = pd.DataFrame()
        
        for need_file in primary_role_files:
            try:
                role_need_df = pd.read_parquet(need_file)
                if combined_need_df.empty:
                    combined_need_df = role_need_df.copy()
                else:
                    # 同じ時間帯・日付での需要を合計
                    combined_need_df = combined_need_df.add(role_need_df, fill_value=0)
                log.debug(f"[shortage] 統合: {need_file.name} (形状: {role_need_df.shape})")
            except Exception as e:
                log.warning(f"[shortage] {need_file.name} の読み込みエラー: {e}")
        
        need_per_date_slot_df = combined_need_df
        log.info(f"[shortage] ★★★ 改善版Need統合完了: 形状 {need_per_date_slot_df.shape} ★★★")
    else:
        # フォールバック処理は既存のままでOK
        ...
    """
    pass

if __name__ == "__main__":
    print("このファイルはshortage.py の修正パッチです。")
    print("improved_role_deduplication 関数をshortage.py にコピーして使用してください。")