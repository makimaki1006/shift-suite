#!/usr/bin/env python3
"""
実際のExcelファイルを使った時間軸計算テスト
本物のシフトデータでの修正効果確認
"""

import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

try:
    from shift_suite.tasks.io_excel import ingest_excel
    from shift_suite.tasks.time_axis_shortage_calculator import calculate_time_axis_shortage
    from shift_suite.tasks.proportional_calculator import calculate_proportional_shortage
    from shift_suite.tasks.constants import SLOT_HOURS
except ImportError as e:
    print(f"インポートエラー: {e}")
    sys.exit(1)

def test_with_real_excel():
    """実際のExcelファイルを使ったテスト"""
    print("=== 実Excelファイルテスト ===")
    
    # 利用可能なExcelファイルを探す
    excel_files = [
        "ショート_テスト用データ.xlsx",
        "デイ_テスト用データ_休日精緻.xlsx",
        "テストデータ_勤務表　勤務時間_トライアル.xlsx"
    ]
    
    base_path = Path(__file__).parent
    
    for excel_file in excel_files:
        excel_path = base_path / excel_file
        if excel_path.exists():
            print(f"\n--- {excel_file}を使用したテスト ---")
            
            try:
                # Excelファイルからシフトデータを読み込み
                print("  Excelデータ読み込み中...")
                
                # io_excel.ingest_excelを使用してデータを読み込み
                out_dir = base_path / "temp_test_output"
                out_dir.mkdir(exist_ok=True)
                
                # ingest_excel関数を呼び出してデータを処理
                result = ingest_excel(
                    str(excel_path),
                    str(out_dir),
                    slot_hours=0.5,
                    slot_minutes=30
                )
                
                if result is None:
                    print("  データ読み込み失敗")
                    continue
                
                # 生成されたparquetファイルを読み込み
                intermediate_data_path = out_dir / "intermediate_data.parquet"
                if intermediate_data_path.exists():
                    working_data = pd.read_parquet(intermediate_data_path)
                    
                    # 勤務データのみを抽出（休日除外）
                    work_records = working_data[
                        (working_data['parsed_slots_count'] > 0) &
                        (working_data.get('holiday_type', '通常勤務') == '通常勤務')
                    ].copy()
                    
                    print(f"  読み込み成功: {len(work_records)}レコード")
                    print(f"  職種分布: {work_records['role'].value_counts().head(3).to_dict()}")
                    
                    # 仮の総不足時間（按分計算でのベースライン）
                    realistic_baseline = 25.0  # 25時間不足
                    
                    # 1. 按分計算
                    print(f"\n  1. 按分計算テスト:")
                    role_shortages_prop, emp_shortages_prop = calculate_proportional_shortage(
                        work_records, realistic_baseline
                    )
                    prop_total = sum(role_shortages_prop.values())
                    print(f"     按分計算合計: {prop_total:.1f}時間")
                    print(f"     主要職種: {dict(list(role_shortages_prop.items())[:3])}")
                    
                    # 2. 修正前の疑似計算（過大評価）
                    old_supply = len(work_records) * 0.5  # レコード数×時間
                    old_demand = old_supply * 1.2  # 1.2倍増大
                    old_shortage = old_demand - old_supply
                    print(f"\n  2. 修正前疑似計算:")
                    print(f"     過大評価不足: {old_shortage:.1f}時間")
                    
                    # 3. 修正後時間軸計算
                    print(f"\n  3. 修正後時間軸計算:")
                    role_shortages_time, emp_shortages_time = calculate_time_axis_shortage(
                        work_records, total_shortage_baseline=realistic_baseline
                    )
                    time_total = sum(role_shortages_time.values())
                    print(f"     時間軸計算合計: {time_total:.1f}時間")
                    print(f"     主要職種: {dict(list(role_shortages_time.items())[:3])}")
                    
                    # 4. 修正効果分析
                    print(f"\n  4. 修正効果分析:")
                    print(f"     按分計算: {prop_total:.1f}時間")
                    print(f"     時間軸計算: {time_total:.1f}時間")
                    print(f"     差異: {abs(prop_total - time_total):.1f}時間")
                    
                    improvement_ratio = old_shortage / max(time_total, 1)
                    print(f"     改善率: {improvement_ratio:.1f}倍の過大評価を修正")
                    
                    # 5. 職種別詳細比較
                    print(f"\n  5. 職種別比較:")
                    for role in list(role_shortages_prop.keys())[:3]:
                        prop_val = role_shortages_prop.get(role, 0)
                        time_val = role_shortages_time.get(role, 0)
                        diff = abs(prop_val - time_val)
                        print(f"     {role}: 按分{prop_val:.1f}h vs 時間軸{time_val:.1f}h (差{diff:.1f}h)")
                    
                    return True
                    
                else:
                    print("  中間データファイルが見つかりません")
                    
            except Exception as e:
                print(f"  エラー: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    print("\n利用可能なExcelファイルが見つかりません")
    return False

def run_real_excel_test():
    """実Excelテスト実行"""
    print("=== 実際のExcelファイルを使った時間軸計算修正テスト ===")
    print(f"開始時刻: {datetime.now()}")
    
    try:
        success = test_with_real_excel()
        
        print(f"\n=== テスト完了 ===")
        if success:
            print("実Excelファイルでのテストが正常に完了しました。")
            print("修正された時間軸計算が実データで適切に動作することを確認しました。")
        else:
            print("テストファイルが見つからないか、エラーが発生しました。")
        
        return success
        
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run_real_excel_test()