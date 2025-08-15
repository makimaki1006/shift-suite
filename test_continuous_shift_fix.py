#!/usr/bin/env python3
"""
連続勤務修正機能のテストスクリプト
テストデータ_勤務表　勤務時間_トライアル.xlsxを使用して修正内容を検証
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import datetime as dt

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger(__name__)

def test_continuous_shift_detection():
    """連続勤務検出機能のテスト"""
    try:
        from shift_suite.tasks.continuous_shift_detector import ContinuousShiftDetector
        from shift_suite.tasks.io_excel import ingest_excel
        
        log.info("=== 連続勤務検出機能テスト開始 ===")
        
        # テストデータの読み込み
        excel_path = Path("テストデータ_勤務表　勤務時間_トライアル.xlsx")
        if not excel_path.exists():
            log.error(f"テストファイルが見つかりません: {excel_path}")
            return False
        
        log.info(f"テストファイル読み込み: {excel_path}")
        
        # シフトデータ解析
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=["R7.6"],
            header_row=2,
            slot_minutes=15  # 15分間隔でテスト
        )
        
        log.info(f"シフトデータ読み込み完了: {len(long_df)}件")
        
        # 連続勤務検出
        detector = ContinuousShiftDetector()
        continuous_shifts = detector.detect_continuous_shifts(long_df)
        
        log.info(f"連続勤務検出結果: {len(continuous_shifts)}件")
        
        # 統計情報
        summary = detector.get_continuous_shift_summary()
        log.info(f"連続勤務統計: {summary}")
        
        # 具体的な連続勤務例を出力
        if continuous_shifts:
            log.info("=== 連続勤務の具体例 ===")
            for i, shift in enumerate(continuous_shifts[:5]):  # 最初の5件
                log.info(
                    f"{i+1}. {shift.staff}: {shift.start_date} {shift.start_time} → "
                    f"{shift.end_date} {shift.end_time} ({shift.total_duration_hours:.1f}時間)"
                )
        
        return len(continuous_shifts) > 0
        
    except Exception as e:
        log.error(f"連続勤務検出テストエラー: {e}", exc_info=True)
        return False

def test_need_calculation_with_continuous_shifts():
    """連続勤務考慮のNeed計算テスト"""
    try:
        from shift_suite.tasks.heatmap import build_heatmap
        from shift_suite.tasks.io_excel import ingest_excel
        
        log.info("=== Need計算（連続勤務考慮）テスト開始 ===")
        
        # テストデータの読み込み
        excel_path = Path("テストデータ_勤務表　勤務時間_トライアル.xlsx")
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=["R7.6"],
            header_row=2,
            slot_minutes=15
        )
        
        # ヒートマップ生成（連続勤務考慮）
        out_dir = Path("test_results_continuous_fix")
        out_dir.mkdir(exist_ok=True)
        
        log.info("ヒートマップ生成開始（連続勤務考慮版）")
        
        build_heatmap(
            long_df=long_df,
            out_dir=out_dir,
            slot_minutes=15,
            ref_start_date_for_need=dt.date(2025, 6, 1),
            ref_end_date_for_need=dt.date(2025, 6, 30),
            need_statistic_method="平均値",
            need_remove_outliers=True,
            need_iqr_multiplier=1.5
        )
        
        log.info("ヒートマップ生成完了")
        
        # 結果検証
        heat_all_file = out_dir / "heat_ALL.parquet"
        if heat_all_file.exists():
            heat_all_df = pd.read_parquet(heat_all_file)
            
            # 0:00時点のNeed値確認
            if 'need' in heat_all_df.columns:
                midnight_need = heat_all_df.loc['00:00', 'need'] if '00:00' in heat_all_df.index else 0
                log.info(f"修正後 0:00のNeed値: {midnight_need}")
                
                # 深夜時間帯のNeed値サマリー
                midnight_hours = ['00:00', '00:15', '00:30', '00:45', '01:00', '01:15', '01:30', '01:45']
                for time_slot in midnight_hours:
                    if time_slot in heat_all_df.index:
                        need_val = heat_all_df.loc[time_slot, 'need']
                        log.info(f"  {time_slot}: Need={need_val}")
            
            return True
        else:
            log.error("ヒートマップファイルが生成されませんでした")
            return False
            
    except Exception as e:
        log.error(f"Need計算テストエラー: {e}", exc_info=True)
        return False

def test_duplicate_removal():
    """重複除去機能のテスト"""
    try:
        log.info("=== 重複除去機能テスト開始 ===")
        
        # サンプルデータで重複除去をテスト
        from shift_suite.tasks.continuous_shift_detector import ContinuousShiftDetector
        
        # サンプルlong_df作成
        sample_data = [
            {'ds': '2025-06-02 23:45:00', 'staff': '花田', 'role': '3F介護', 'code': '夜'},
            {'ds': '2025-06-03 00:00:00', 'staff': '花田', 'role': '3F介護', 'code': '明'},  # これが重複対象
            {'ds': '2025-06-03 00:15:00', 'staff': '花田', 'role': '3F介護', 'code': '明'},
            {'ds': '2025-06-03 00:00:00', 'staff': '田中', 'role': '4F介護', 'code': '日'},  # 別職員は除去対象外
        ]
        
        sample_df = pd.DataFrame(sample_data)
        sample_df['ds'] = pd.to_datetime(sample_df['ds'])
        
        detector = ContinuousShiftDetector()
        continuous_shifts = detector.detect_continuous_shifts(sample_df)
        
        log.info(f"サンプルデータでの連続勤務検出: {len(continuous_shifts)}件")
        
        # 重複除去対象の特定
        duplicates = detector.get_duplicate_time_slots('2025-06-03')
        log.info(f"重複除去対象: {duplicates}")
        
        # 期待される結果: ('花田', '00:00') が重複対象として検出されること
        expected_duplicate = ('花田', '00:00')
        success = expected_duplicate in duplicates
        
        log.info(f"重複除去機能テスト結果: {'成功' if success else '失敗'}")
        return success
        
    except Exception as e:
        log.error(f"重複除去テストエラー: {e}", exc_info=True)
        return False

def main():
    """メインテスト実行"""
    log.info("连续勤務修正機能 統合テスト開始")
    
    tests = [
        ("連続勤務検出", test_continuous_shift_detection),
        ("Need計算（連続勤務考慮）", test_need_calculation_with_continuous_shifts),
        ("重複除去機能", test_duplicate_removal),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        log.info(f"\n{'='*50}")
        log.info(f"テスト実行: {test_name}")
        log.info(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
            log.info(f"{test_name}: {'✅ 成功' if result else '❌ 失敗'}")
        except Exception as e:
            log.error(f"{test_name}: ❌ エラー - {e}")
            results[test_name] = False
    
    # 総合結果
    log.info(f"\n{'='*50}")
    log.info("テスト結果サマリー")
    log.info(f"{'='*50}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        log.info(f"{test_name}: {status}")
    
    log.info(f"\n総合結果: {passed_tests}/{total_tests} テスト成功")
    
    if passed_tests == total_tests:
        log.info("🎉 全テスト成功！連続勤務修正機能が正常に動作しています。")
        return True
    else:
        log.warning("⚠️  一部テストが失敗しました。修正内容を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)