#!/usr/bin/env python3
"""
疲労度分析の実行テスト
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta

def create_test_data():
    """テストデータを作成"""
    print("🔨 テストデータを作成中...")
    
    # 簡単なテストデータを作成
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(30)]
    
    staff_names = ["山田太郎", "佐藤花子", "田中一郎"]
    
    test_data = []
    for staff in staff_names:
        for date in dates:
            # 日勤データ
            test_data.append({
                "staff": staff,
                "ds": datetime.combine(date, time(9, 0)),
                "code": "日勤",
                "parsed_slots_count": 8,  # 8時間勤務
                "start_time": "09:00"
            })
            
            # ランダムに夜勤も追加
            if np.random.random() < 0.3:  # 30%の確率で夜勤
                test_data.append({
                    "staff": staff,
                    "ds": datetime.combine(date, time(22, 0)),
                    "code": "夜勤",
                    "parsed_slots_count": 8,
                    "start_time": "22:00"
                })
    
    df = pd.DataFrame(test_data)
    print(f"✅ テストデータ作成完了: {len(df)}行, スタッフ数: {len(staff_names)}")
    return df

def test_fatigue_analysis():
    """疲労度分析のテスト"""
    print("🧪 疲労度分析の実行テスト")
    print("=" * 50)
    
    try:
        # モジュールのインポート
        from shift_suite.tasks.fatigue import train_fatigue
        print("✅ train_fatigue関数のインポート成功")
        
        # テストデータ作成
        test_df = create_test_data()
        
        # 出力ディレクトリ作成
        output_dir = Path("temp_fatigue_test")
        output_dir.mkdir(exist_ok=True)
        print(f"📁 出力ディレクトリ: {output_dir}")
        
        # 疲労度分析の実行
        print("🔬 疲労度分析を実行中...")
        
        weights = {
            "start_var": 1.0,
            "diversity": 1.0,
            "worktime_var": 1.0,
            "short_rest": 1.0,
            "consecutive": 1.0,
            "night_ratio": 1.0,
        }
        
        result = train_fatigue(
            test_df, 
            output_dir, 
            weights=weights, 
            slot_minutes=30
        )
        
        print("✅ 疲労度分析実行完了")
        
        # 結果ファイルの確認
        parquet_file = output_dir / "fatigue_score.parquet"
        xlsx_file = output_dir / "fatigue_score.xlsx"
        
        if parquet_file.exists():
            print(f"✅ parquetファイル生成: {parquet_file}")
            # ファイル内容の確認
            df_result = pd.read_parquet(parquet_file)
            print(f"📊 結果データ: {len(df_result)}行, {len(df_result.columns)}列")
            print("列名:", list(df_result.columns))
            print("先頭5行:")
            print(df_result.head())
        else:
            print("❌ parquetファイルが生成されていません")
            
        if xlsx_file.exists():
            print(f"✅ Excelファイル生成: {xlsx_file}")
        else:
            print("❌ Excelファイルが生成されていません")
            
        return True
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト"""
    print("🔍 疲労度分析の包括的な実行テスト")
    print("=" * 60)
    
    success = test_fatigue_analysis()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 疲労度分析の実行テストが成功しました！")
        print("\n📝 確認事項:")
        print("1. temp_fatigue_testフォルダにファイルが生成されているか")
        print("2. fatigue_score.parquet/xlsxファイルの内容")
        print("3. 6つの疲労要因が正しく計算されているか")
    else:
        print("⚠️ 疲労度分析の実行でエラーが発生しました")
        print("app.pyでの実行でも同様のエラーが起きる可能性があります")
    
    return success

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 テスト完了: {'成功' if success else '失敗'}")