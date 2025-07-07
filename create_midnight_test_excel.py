
import pandas as pd
from pathlib import Path

def create_test_excel():
    excel_path = Path("test_midnight_edge_cases.xlsx")
    wt_df = pd.DataFrame({
        "コード": ["夜勤終了", "日勤開始"],
        "開始": ["16:45", "00:00"],
        "終了": ["24:00", "10:00"],
        "備考": ["", ""]
    })
    shift_df = pd.DataFrame({
        "氏名": ["スタッフC"],
        "職種": ["看護師"],
        "1": ["夜勤終了"],
        "2": ["日勤開始"]
    })
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        wt_df.to_excel(writer, sheet_name="勤務区分", index=False)
        # 年月情報をA1セルに書き込む
        ym_df = pd.DataFrame([["2025年8月"]])
        ym_df.to_excel(writer, sheet_name="2025年8月", index=False, header=False)
        # 実際のシフトデータは3行目から書き込む
        shift_df.to_excel(writer, sheet_name="2025年8月", index=False, header=True, startrow=1)

if __name__ == "__main__":
    create_test_excel()
    print(f"Created 'test_midnight_edge_cases.xlsx'")
