#!/usr/bin/env python3
"""
テストファイルの詳細分析
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def analyze_file_in_detail(filepath: Path):
    """ファイルの詳細分析"""
    log.info(f"=== 詳細分析: {filepath.name} ===")
    
    try:
        # 全シート名取得
        xl_file = pd.ExcelFile(filepath)
        log.info(f"シート名: {xl_file.sheet_names}")
        
        # 各シートの詳細確認
        for sheet_name in xl_file.sheet_names:
            log.info(f"\n--- シート: {sheet_name} ---")
            
            if sheet_name == '勤務区分':
                # 勤務区分シートの分析
                try:
                    wt_df = pd.read_excel(filepath, sheet_name=sheet_name, dtype=str)
                    log.info(f"勤務区分シート: shape={wt_df.shape}")
                    log.info(f"列名: {wt_df.columns.tolist()}")
                    if not wt_df.empty:
                        log.info(f"最初の3行:")
                        for i in range(min(3, len(wt_df))):
                            log.info(f"  {i}: {wt_df.iloc[i].tolist()}")
                except Exception as e:
                    log.error(f"勤務区分シート読み込みエラー: {e}")
                continue
            
            # 通常のシート分析
            try:
                # 生データ確認（ヘッダーなし）
                df_raw = pd.read_excel(filepath, sheet_name=sheet_name, header=None, nrows=10)
                log.info(f"生データ shape: {df_raw.shape}")
                
                # 最初の数行を表示
                log.info("最初の数行（生データ）:")
                for i in range(min(5, len(df_raw))):
                    row_data = [str(val)[:20] for val in df_raw.iloc[i]]  # 各値を20文字に制限
                    log.info(f"  行{i}: {row_data}")
                
                # 各ヘッダー行での結果を確認
                for header_row in [0, 1, 2]:
                    try:
                        df_test = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row, dtype=str)
                        log.info(f"ヘッダー行{header_row}: shape={df_test.shape}")
                        
                        # 列名チェック
                        cols = df_test.columns.tolist()
                        log.info(f"  列名（最初の5つ）: {cols[:5]}")
                        
                        # 職員・職種列の確認
                        staff_cols = [col for col in cols if any(keyword in str(col) for keyword in ['職員', '氏名', '����', 'staff', 'name'])]
                        role_cols = [col for col in cols if any(keyword in str(col) for keyword in ['職種', '部署', '�E��', 'role', 'department'])]
                        
                        log.info(f"  職員関連列: {staff_cols}")
                        log.info(f"  職種関連列: {role_cols}")
                        
                        # 日付列の確認
                        date_cols = []
                        for col in cols:
                            if isinstance(col, pd.Timestamp) or 'datetime' in str(type(col)):
                                date_cols.append(str(col))
                            elif str(col).replace('-', '').replace('/', '').isdigit() and len(str(col)) >= 8:
                                date_cols.append(str(col))
                        
                        log.info(f"  日付関連列数: {len(date_cols)}")
                        if date_cols:
                            log.info(f"  日付列例: {date_cols[:3]}")
                        
                        # データサンプル
                        if not df_test.empty:
                            log.info(f"  データ例（最初の行）: {[str(val)[:15] for val in df_test.iloc[0]][:5]}")
                            
                    except Exception as e:
                        log.warning(f"  ヘッダー行{header_row}でエラー: {e}")
                        
            except Exception as e:
                log.error(f"シート '{sheet_name}' の分析エラー: {e}")
    
    except Exception as e:
        log.error(f"ファイル '{filepath}' の分析エラー: {e}")

def main():
    test_files = [
        Path("デイ_テスト用データ_休日精緻.xlsx"),
        Path("ショート_テスト用データ.xlsx")
    ]
    
    for filepath in test_files:
        if filepath.exists():
            analyze_file_in_detail(filepath)
        else:
            log.error(f"ファイルが見つかりません: {filepath}")

if __name__ == "__main__":
    main()