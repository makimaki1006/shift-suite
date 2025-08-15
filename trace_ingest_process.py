#!/usr/bin/env python3
"""
ingest_excel処理フローの詳細追跡
"""

import sys
import pandas as pd
from pathlib import Path
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ログ設定を詳細に
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def trace_ingest_process():
    """ingest_excel処理の詳細追跡"""
    
    print("=== ingest_excel Processing Flow Trace ===")
    
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    
    try:
        # 手動でingest_excelの各ステップを再現
        from shift_suite.tasks.io_excel import load_shift_patterns
        
        print("\n1. load_shift_patterns 実行...")
        wt_df, code2slots = load_shift_patterns(test_file, slot_minutes=30)
        
        print(f"   勤務区分読み込み完了: {len(wt_df)}行")
        print(f"   code2slots: {len(code2slots)}個のコード")
        
        # 実際に勤務時間があるコードを確認
        work_codes = {code: len(slots) for code, slots in code2slots.items() if len(slots) > 0}
        leave_codes = {code: len(slots) for code, slots in code2slots.items() if len(slots) == 0}
        
        print(f"   勤務コード（スロット>0）: {len(work_codes)}個")
        for code, slots in list(work_codes.items())[:5]:
            print(f"     {code}: {slots}スロット")
        
        print(f"   休暇コード（スロット=0）: {len(leave_codes)}個")
        for code, slots in list(leave_codes.items())[:5]:
            print(f"     {code}: {slots}スロット")
        
        print("\n2. 実績シート処理開始...")
        
        # R7.2シートを手動で処理
        shift_sheets = ["R7.2"]
        records = []
        unknown_codes = set()
        
        for sheet_name in shift_sheets:
            print(f"\n   === {sheet_name}シート処理 ===")
            
            # シート読み込み
            df_sheet = pd.read_excel(
                test_file,
                sheet_name=sheet_name,
                header=0,  # ヘッダー行
                dtype=str,
            ).fillna("")
            
            print(f"   読み込み形状: {df_sheet.shape}")
            print(f"   列名: {df_sheet.columns.tolist()[:5]}...")
            
            # 列名マッピング
            from shift_suite.tasks.io_excel import SHEET_COL_ALIAS, _normalize
            
            print(f"   列名マッピング前の最初の3列: {df_sheet.columns[:3].tolist()}")
            
            df_sheet.columns = [
                SHEET_COL_ALIAS.get(_normalize(str(c)), _normalize(str(c)))
                for c in df_sheet.columns
            ]
            
            print(f"   列名マッピング後の最初の3列: {df_sheet.columns[:3].tolist()}")
            
            # staff, role列の確認
            has_staff = "staff" in df_sheet.columns
            has_role = "role" in df_sheet.columns
            print(f"   staff列存在: {has_staff}")
            print(f"   role列存在: {has_role}")
            
            if not has_staff or not has_role:
                print(f"   ❌ 必須列不足: staff={has_staff}, role={has_role}")
                continue
            
            # 日付列候補の特定
            date_cols_candidate = [
                c for c in df_sheet.columns
                if c not in ("staff", "role", "employment")
                and not str(c).startswith("Unnamed:")
            ]
            
            print(f"   日付列候補: {len(date_cols_candidate)}個")
            print(f"   候補例: {date_cols_candidate[:5]}")
            
            # 日付解析
            from shift_suite.tasks.utils import _parse_as_date
            
            date_col_map = {}
            for c in date_cols_candidate[:5]:  # 最初の5個だけテスト
                parsed_dt = _parse_as_date(str(c))
                if parsed_dt:
                    date_col_map[str(c)] = parsed_dt
                    print(f"     {c} → {parsed_dt} ✓")
                else:
                    print(f"     {c} → 解析失敗 ❌")
            
            print(f"   解析成功した日付列: {len(date_col_map)}個")
            
            if len(date_col_map) == 0:
                print(f"   ❌ 日付列が1つも解析できない！")
                continue
            
            # 実際のデータ行処理（最初の3行）
            print(f"\n   データ行処理...")
            
            valid_records = 0
            for row_idx in range(min(3, len(df_sheet))):
                row_data = df_sheet.iloc[row_idx]
                staff = _normalize(row_data.get("staff", ""))
                role = _normalize(row_data.get("role", ""))
                
                print(f"     行{row_idx}: staff='{staff}', role='{role}'")
                
                if staff == "" and role == "":
                    print(f"       スキップ: staff・role両方空")
                    continue
                
                # 日付列の勤務コードチェック
                for col_name, date_val in list(date_col_map.items())[:3]:  # 最初の3日分
                    shift_code_raw = row_data.get(col_name, "")
                    code_val = _normalize(str(shift_code_raw))
                    
                    print(f"       {col_name}: '{code_val}'")
                    
                    if code_val in ("", "nan", "NaN"):
                        print(f"         空コード")
                        continue
                    
                    if code_val not in code2slots:
                        print(f"         未知コード: '{code_val}'")
                        unknown_codes.add(code_val)
                        continue
                    
                    slots = code2slots.get(code_val, [])
                    print(f"         定義済みコード: {len(slots)}スロット")
                    
                    if len(slots) > 0:
                        valid_records += 1
                        print(f"         ✓ 有効レコード生成")
            
            print(f"   {sheet_name}で生成された有効レコード数: {valid_records}")
            
        print(f"\n=== 処理結果サマリー ===")
        print(f"総有効レコード数: {valid_records}")
        print(f"未知コード: {sorted(unknown_codes)}")
        
        if valid_records == 0:
            print("❌ 有効なレコードが1つも生成されていない！")
            print("これが「有効なシフトレコードが生成されませんでした」エラーの原因")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_ingest_process()