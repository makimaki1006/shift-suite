import pandas as pd
from pathlib import Path


def generate_correct_shortage_file(directory: str):
    """正しいNeedデータに基づき、不足時間ファイルを確実に再生成するスクリプト。
    結果は shortage_time_CORRECTED.parquet として出力される。
    """
    base_path = Path(directory)
    print("--- 不足時間ファイルの再生成処理を開始します ---")

    # --- 1. 必要なファイルのパスを定義 ---
    path_need_detail = base_path / "need_per_date_slot.parquet"
    path_actual_staff = base_path / "heat_ALL.parquet"
    output_path = base_path / "shortage_time_CORRECTED.parquet"

    # --- 2. ファイルの存在確認 ---
    if not path_need_detail.exists():
        print(f"❌ エラー: 正しいNeedファイルが見つかりません: {path_need_detail}")
        return
    if not path_actual_staff.exists():
        print(f"❌ エラー: 実績ファイルが見つかりません: {path_actual_staff}")
        return

    print("✅ 必要なファイルを2つ確認しました。")

    # --- 3. データを読み込む ---
    try:
        df_need = pd.read_parquet(path_need_detail)
        df_heat_all = pd.read_parquet(path_actual_staff)
        print("✅ データの読み込みに成功しました。")
    except Exception as e:
        print(f"❌ エラー: ファイル読み込み中にエラーが発生しました: {e}")
        return

    # --- 4. 実績データ(staff)を抽出 ---
    # heat_ALLから日付形式の列のみを抽出
    date_columns = [col for col in df_heat_all.columns if isinstance(col, str) and col.count('-') == 2]
    try:
        # 日付文字列をdatetimeオブジェクトに変換してソートし、また文字列に戻すことで順序を保証
        sorted_date_columns = sorted(pd.to_datetime(date_columns).to_series()).dt.strftime('%Y-%m-%d').tolist()
    except Exception:
        # パースできない列が含まれる場合は、単純にソート
        sorted_date_columns = sorted(date_columns)

    df_staff = df_heat_all[sorted_date_columns]

    # --- 5. 正しい不足数を計算 ---
    print("⚙️  正しいロジックで不足数を再計算中...")
    # df_need と df_staff の列とインデックスを合わせる
    # これにより、日付や時間帯のズレを防ぐ
    common_cols = df_staff.columns.intersection(df_need.columns)
    common_index = df_staff.index.intersection(df_need.index)

    df_need_aligned = df_need.loc[common_index, common_cols]
    df_staff_aligned = df_staff.loc[common_index, common_cols]

    # 不足数を計算 (Need - Staff)、マイナスは0にする
    df_shortage_corrected = (df_need_aligned - df_staff_aligned).clip(lower=0).fillna(0)
    print("✅ 計算が完了しました。")

    # --- 6. 結果を新しいファイルに保存 ---
    try:
        df_shortage_corrected.to_parquet(output_path)
        print(f"🎉 成功: 修正済みの不足データが '{output_path.name}' として保存されました。")
    except Exception as e:
        print(f"❌ エラー: 結果のファイル保存中にエラーが発生しました: {e}")
        return

    # --- 7. 検証のために休日のデータを確認 ---
    # '2025-06-08' のような休日をサンプルとして確認
    sample_holiday = '2025-06-08'
    if sample_holiday in df_shortage_corrected.columns:
        holiday_shortage_sum = df_shortage_corrected[sample_holiday].sum()
        print(f"\n--- 検証: {sample_holiday} のデータ ---")
        print(f"計算後の不足合計: {holiday_shortage_sum}")
        if holiday_shortage_sum == 0:
            print("👍 休日 ({sample_holiday}) の不足は正しく 0 になっています。")
        else:
            print(f"⚠️ 休日 ({sample_holiday}) の不足が 0 ではありません。データを確認してください。")


if __name__ == "__main__":
    # ▼▼▼▼▼ このパスを、ご自身の環境に合わせて設定してください ▼▼▼▼▼
    # 例: "C:\\Users\\fuji1\\OneDrive\\デスクトップ"
    DIRECTORY_PATH = "C:\\Users\\fuji1\\OneDrive\\デスクトップ"
    # ▲▲▲▲▲ 設定はここまで ▲▲▲▲▲

    generate_correct_shortage_file(DIRECTORY_PATH)
