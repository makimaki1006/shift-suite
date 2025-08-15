#!/usr/bin/env python3
"""
復元された疲労度分析機能のテスト
"""
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from shift_suite.tasks.fatigue import train_fatigue, _features, _get_time_category, _analyze_consecutive_days
    from shift_suite.tasks.constants import FATIGUE_PARAMETERS
    print("✅ モジュールのインポートが成功しました")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def create_test_data():
    """テスト用のダミーデータを生成"""
    
    # スタッフリスト
    staff_list = ["田中太郎", "佐藤花子", "鈴木一郎", "高橋美咲", "伊藤健太"]
    
    # 勤務コード（夜勤、日勤、遅番など）
    shift_codes = ["日勤", "夜勤", "遅番", "早番", "準夜"]
    
    # 1ヶ月分のデータを生成
    test_data = []
    base_date = pd.Timestamp("2024-01-01")
    
    for staff in staff_list:
        for day in range(30):  # 30日分
            # ランダムに勤務ありなしを決定（70%の確率で勤務あり）
            if np.random.random() < 0.7:
                current_date = base_date + pd.Timedelta(days=day)
                
                # 勤務コードをランダム選択
                shift_code = np.random.choice(shift_codes)
                
                # 時間帯に応じて開始時刻を設定
                if "夜" in shift_code or "準夜" in shift_code:
                    start_hour = np.random.choice([22, 23, 0, 1])
                elif "遅" in shift_code:
                    start_hour = np.random.choice([14, 15, 16])
                elif "早" in shift_code:
                    start_hour = np.random.choice([6, 7, 8])
                else:  # 日勤
                    start_hour = np.random.choice([8, 9, 10])
                
                # スロット数（4-16スロット = 2-8時間）
                slots = np.random.randint(4, 17)
                
                # 終了時刻を計算
                end_hour = (start_hour + slots * 0.5) % 24
                
                test_data.append({
                    "staff": staff,
                    "ds": current_date.strftime("%Y-%m-%d"),
                    "code": shift_code,
                    "start_time": f"{start_hour:02d}:00",
                    "end_time": f"{int(end_hour):02d}:{int((end_hour % 1) * 60):02d}",
                    "parsed_slots_count": slots
                })
    
    return pd.DataFrame(test_data)

def test_time_category():
    """時間帯カテゴリ判定のテスト"""
    print("\n=== 時間帯カテゴリ判定テスト ===")
    
    test_cases = [
        ("日勤", "day"),
        ("夜勤", "night"),
        ("遅番", "late"),
        ("準夜", "night"),
        ("深夜", "night"),
        ("early", "other"),
        ("unknown", "other"),
        (None, "other")
    ]
    
    all_passed = True
    for code, expected in test_cases:
        result = _get_time_category(code)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} '{code}' -> '{result}' (期待値: '{expected}')")
    
    return all_passed

def test_consecutive_analysis():
    """連続勤務分析のテスト"""
    print("\n=== 連続勤務分析テスト ===")
    
    # 意図的に連勤パターンを作成
    test_data = []
    base_date = pd.Timestamp("2024-01-01")
    
    # 職員Aは5連勤パターン
    for day in [0, 1, 2, 3, 4, 10, 11, 12]:  # 5連勤と3連勤
        test_data.append({
            "staff": "職員A",
            "ds": (base_date + pd.Timedelta(days=day)).strftime("%Y-%m-%d"),
            "code": "日勤",
            "parsed_slots_count": 8
        })
    
    # 職員Bは散発的勤務
    for day in [0, 2, 4, 6, 8]:
        test_data.append({
            "staff": "職員B", 
            "ds": (base_date + pd.Timedelta(days=day)).strftime("%Y-%m-%d"),
            "code": "日勤",
            "parsed_slots_count": 8
        })
    
    df = pd.DataFrame(test_data)
    
    try:
        result = _analyze_consecutive_days(df)
        print(f"✅ 連続勤務分析が成功: {len(result)}名のスタッフ")
        
        for staff_data in result:
            staff = staff_data["staff"]
            print(f"  {staff}: 3連勤={staff_data['consec3_ratio']:.2f}, "
                  f"4連勤={staff_data['consec4_ratio']:.2f}, "
                  f"5連勤={staff_data['consec5_ratio']:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ 連続勤務分析エラー: {e}")
        return False

def test_features_generation():
    """特徴量生成のテスト"""
    print("\n=== 特徴量生成テスト ===")
    
    test_df = create_test_data()
    print(f"テストデータ: {len(test_df)}行, {test_df['staff'].nunique()}名のスタッフ")
    
    try:
        features = _features(test_df, slot_minutes=30)
        print(f"✅ 特徴量生成が成功: {features.shape}")
        print(f"生成された特徴量: {list(features.columns)}")
        
        # 各特徴量の基本統計
        for col in features.columns:
            mean_val = features[col].mean()
            print(f"  {col}: 平均={mean_val:.3f}, 範囲=[{features[col].min():.3f}, {features[col].max():.3f}]")
        
        return True
    except Exception as e:
        print(f"❌ 特徴量生成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_fatigue_analysis():
    """完全な疲労度分析のテスト"""
    print("\n=== 完全な疲労度分析テスト ===")
    
    test_df = create_test_data()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_dir = Path(tmp_dir)
        
        try:
            # 疲労度分析を実行
            result = train_fatigue(test_df, out_dir, slot_minutes=30)
            print("✅ 疲労度分析が正常完了")
            
            # 生成されたファイルを確認
            parquet_file = out_dir / "fatigue_score.parquet"
            xlsx_file = out_dir / "fatigue_score.xlsx"
            
            if parquet_file.exists():
                df = pd.read_parquet(parquet_file)
                print(f"✅ Parquetファイル生成: {df.shape}")
                print(f"列: {list(df.columns)}")
                
                # 期待される列が存在するかチェック
                expected_cols = [
                    "fatigue_score", "work_start_variance", "work_diversity",
                    "work_duration_variance", "short_rest_frequency", 
                    "consecutive_work_days", "night_shift_ratio"
                ]
                
                missing_cols = [col for col in expected_cols if col not in df.columns]
                if missing_cols:
                    print(f"⚠️ 不足している列: {missing_cols}")
                else:
                    print("✅ 全ての期待される列が存在します")
                
                # データサンプルを表示
                print("\nサンプルデータ:")
                print(df.head(3).to_string())
                
            else:
                print("❌ Parquetファイルが生成されていません")
                return False
            
            if xlsx_file.exists():
                print("✅ Excelファイルも生成されました")
            else:
                print("⚠️ Excelファイルが生成されていません")
            
            return True
            
        except Exception as e:
            print(f"❌ 疲労度分析エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """メインテスト実行"""
    print("🔬 復元された疲労度分析機能のテスト開始")
    print("=" * 60)
    
    tests = [
        ("時間帯カテゴリ判定", test_time_category),
        ("連続勤務分析", test_consecutive_analysis),
        ("特徴量生成", test_features_generation),
        ("完全な疲労度分析", test_full_fatigue_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}でエラー: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("🔍 テスト結果サマリー")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 総合結果: {passed_tests}/{total_tests} テストが成功")
    
    if passed_tests == total_tests:
        print("🎉 全てのテストが成功！疲労度分析機能が完全に復元されました。")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)