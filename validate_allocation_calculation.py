
import pandas as pd
from pathlib import Path

# --- 定数定義 ---
DATA_FILE = Path("extracted_results/out_p25_based/intermediate_data.parquet")
DYNAMIC_SLOT_HOURS = 0.5
TARGET_STAFF_FOR_POC = "田中恵里"

def validate_calculation():
    """
    実配置時間の計算ロジックの妥当性を、概念実証（PoC）と全体検証の二段階で検証する。
    """
    print("="*70)
    print("改訂版・「実配置時間」計算ロジック検証スクリプト")
    print("="*70)

    if not DATA_FILE.exists():
        print(f"エラー: データファイルが見つかりません: {DATA_FILE}")
        return

    try:
        df = pd.read_parquet(DATA_FILE)
        print(f"検証データ {DATA_FILE} を正常に読み込みました。")
        print(f"総レコード数（休暇含む）: {len(df)} 件")
    except Exception as e:
        print(f"エラー: データファイルの読み込みに失敗しました: {e}")
        return

    # --- ステップ2.1: 概念実証（Proof of Concept） ---
    print("\n--- 【ステップ2.1: 概念実証（PoC）】 ---")
    print(f"サンプル対象スタッフ: '{TARGET_STAFF_FOR_POC}'")

    # 1. サンプルデータを抽出
    sample_df = df[df["staff"] == TARGET_STAFF_FOR_POC].copy()
    print(f"'{TARGET_STAFF_FOR_POC}'さんの総レコード数（休暇含む）: {len(sample_df)} 件")

    # 2. 「手計算」をシミュレート
    manual_work_df = sample_df[sample_df["parsed_slots_count"] > 0]
    manual_total_slots = manual_work_df["parsed_slots_count"].sum()
    manual_total_hours = manual_total_slots * DYNAMIC_SLOT_HOURS
    print(f"\n[手計算シミュレーション]")
    print(f"  1. 勤務レコードを抽出: {len(manual_work_df)} 件")
    print(f"  2. 勤務スロット数を合計: {manual_total_slots} スロット")
    print(f"  3. 合計時間に換算 ({manual_total_slots} * {DYNAMIC_SLOT_HOURS}h): {manual_total_hours:.2f} 時間")

    # 3. 「あるべき正しいロジック」をプログラムで実行
    correct_logic_work_df = sample_df[
        (sample_df["holiday_type"].isin(["通常勤務", "NORMAL"])) &
        (sample_df["parsed_slots_count"] > 0)
    ].copy()
    correct_logic_total_slots = correct_logic_work_df["parsed_slots_count"].sum()
    correct_logic_total_hours = correct_logic_total_slots * DYNAMIC_SLOT_HOURS
    print(f"\n[プログラムによる計算]")
    print(f"  1. 勤務レコードを抽出: {len(correct_logic_work_df)} 件")
    print(f"  2. 勤務スロット数を合計: {correct_logic_total_slots} スロット")
    print(f"  3. 合計時間に換算 ({correct_logic_total_slots} * {DYNAMIC_SLOT_HOURS}h): {correct_logic_total_hours:.2f} 時間")

    # 4. PoCの結果判定
    print("\n[PoC 結果]")
    if manual_total_hours == correct_logic_total_hours:
        print("  成功: 「手計算」と「あるべきロジック」の計算結果が完全に一致しました。")
        print("  結論: 提案する新しい計算ロジックは、サンプルの範囲において正しいことが証明されました。")
    else:
        print("  失敗: 計算結果が一致しませんでした。ロジックの再検討が必要です。")

    # --- 全体検証 ---
    print("\n--- 【全体検証】（上記PoCの成功を前提） ---")
    
    # 方法1: 現在の問題がある計算ロジック
    flawed_allocated_records = len(df)
    flawed_allocated_hours = flawed_allocated_records * DYNAMIC_SLOT_HOURS

    # 方法2: あるべき正しい計算ロジック
    work_df_all = df[
        (df["holiday_type"].isin(["通常勤務", "NORMAL"])) &
        (df["parsed_slots_count"] > 0)
    ].copy()
    total_working_slots_all = work_df_all["parsed_slots_count"].sum()
    correct_allocated_hours_all = total_working_slots_all * DYNAMIC_SLOT_HOURS
    
    # 比較
    print("\n【全体データでの計算結果比較】")
    print(f"問題のある計算結果 (方法1): {flawed_allocated_hours:12.2f} 時間")
    print(f"あるべき計算結果 (方法2):   {correct_allocated_hours_all:12.2f} 時間")
    discrepancy = correct_allocated_hours_all - flawed_allocated_hours
    print(f"乖離（ズレ）:               {discrepancy:12.2f} 時間")
    if correct_allocated_hours_all > 0:
        error_percentage = abs(discrepancy / correct_allocated_hours_all) * 100
        print(f"誤差率:                     {error_percentage:.2f}%")
    print("="*70)

if __name__ == "__main__":
    validate_calculation()
