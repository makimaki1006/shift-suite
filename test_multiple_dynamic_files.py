#!/usr/bin/env python3
"""
複数のテストファイルでの動的連続勤務検出システムのテスト
異なるデータ形式での完全動的対応を証明
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

def analyze_excel_structure(excel_path: Path):
    """Excelファイルの構造を分析"""
    log.info(f"=== ファイル構造分析: {excel_path.name} ===")
    
    try:
        # シート名の取得
        xl_file = pd.ExcelFile(excel_path)
        sheet_names = xl_file.sheet_names
        log.info(f"利用可能なシート: {sheet_names}")
        
        # 各シートの基本構造を確認
        for sheet_name in sheet_names:
            if sheet_name == '勤務区分':
                continue  # 勤務区分シートは後で処理
                
            try:
                # 最初の数行を読み取って構造を把握
                df_preview = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, nrows=5)
                log.info(f"  シート '{sheet_name}': shape={df_preview.shape}")
                
                # ヘッダー候補を探す
                for header_row in [0, 1, 2]:
                    try:
                        df_test = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row, dtype=str)
                        cols_sample = list(df_test.columns[:5])
                        log.info(f"    ヘッダー行{header_row}: {cols_sample}")
                        
                        # 職員/職種列の存在確認
                        has_staff = any('職員' in str(col) or '氏名' in str(col) or '����' in str(col) for col in df_test.columns)
                        has_role = any('職種' in str(col) or '部署' in str(col) or '�E��' in str(col) for col in df_test.columns)
                        
                        if has_staff and has_role:
                            log.info(f"      → 適切なヘッダー行: {header_row} (職員列・職種列あり)")
                            return sheet_name, header_row
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                log.warning(f"  シート '{sheet_name}' の読み込みエラー: {e}")
                
        # 勤務区分シートの確認
        if '勤務区分' in sheet_names:
            try:
                wt_df = pd.read_excel(excel_path, sheet_name='勤務区分', dtype=str)
                log.info(f"  勤務区分シート: shape={wt_df.shape}, columns={wt_df.columns.tolist()}")
            except Exception as e:
                log.warning(f"  勤務区分シートの読み込みエラー: {e}")
        
        return None, None
        
    except Exception as e:
        log.error(f"ファイル分析エラー: {e}")
        return None, None

def test_dynamic_detection_with_file(excel_path: Path, sheet_name: str, header_row: int):
    """指定されたファイルで動的検出テスト"""
    try:
        from shift_suite.tasks.dynamic_continuous_shift_detector import DynamicContinuousShiftDetector
        from shift_suite.tasks.io_excel import ingest_excel
        
        log.info(f"=== 動的検出テスト: {excel_path.name} ===")
        
        # データ読み込み
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=[sheet_name],
            header_row=header_row,
            slot_minutes=15
        )
        
        log.info(f"データ読み込み完了: {len(long_df)}件のレコード")
        
        if unknown_codes:
            log.warning(f"未知のコード: {sorted(unknown_codes)}")
        
        # 動的検出器の初期化（毎回クリーンな状態から開始）
        detector = DynamicContinuousShiftDetector()
        
        # データから完全に動的に学習・検出
        continuous_shifts = detector.detect_continuous_shifts(long_df, wt_df)
        
        # 結果のサマリー
        summary = detector.get_detection_summary()
        
        log.info(f"検出結果:")
        log.info(f"  連続勤務検出数: {len(continuous_shifts)}件")
        log.info(f"  学習したパターン数: {summary.get('detected_patterns', 0)}")
        log.info(f"  生成されたルール数: {summary.get('active_rules', 0)}")
        log.info(f"  平均連続勤務時間: {summary.get('average_duration_hours', 0):.1f}時間")
        
        # パターン統計
        if 'pattern_statistics' in summary:
            log.info("  検出パターン:")
            for pattern, count in summary['pattern_statistics'].items():
                log.info(f"    {pattern}: {count}件")
        
        # ルール統計
        if 'rule_statistics' in summary:
            log.info("  適用ルール:")
            for rule, count in summary['rule_statistics'].items():
                log.info(f"    {rule}: {count}件")
        
        # 具体例の表示
        if continuous_shifts:
            log.info("  検出例（最初の3件）:")
            for i, shift in enumerate(continuous_shifts[:3], 1):
                log.info(f"    {i}. {shift.staff}: {shift.start_pattern.code}({shift.start_date}) → {shift.end_pattern.code}({shift.end_date}) | ルール: {shift.rule.name}")
        
        # 学習設定の保存
        config_file = Path(f"learned_config_{excel_path.stem}.json")
        detector.export_config(config_file)
        log.info(f"学習済み設定保存: {config_file}")
        
        return {
            'file': excel_path.name,
            'records': len(long_df),
            'continuous_shifts': len(continuous_shifts),
            'patterns': summary.get('detected_patterns', 0),
            'rules': summary.get('active_rules', 0),
            'avg_duration': summary.get('average_duration_hours', 0),
            'success': True
        }
        
    except Exception as e:
        log.error(f"動的検出テストエラー ({excel_path.name}): {e}", exc_info=True)
        return {
            'file': excel_path.name,
            'success': False,
            'error': str(e)
        }

def main():
    """メインテスト実行"""
    log.info("=== 複数ファイルでの動的連続勤務検出システム検証 ===")
    
    test_files = [
        Path("デイ_テスト用データ_休日精緻.xlsx"),
        Path("ショート_テスト用データ.xlsx")
    ]
    
    results = []
    
    for test_file in test_files:
        log.info(f"\n{'='*80}")
        log.info(f"テストファイル: {test_file}")
        log.info(f"{'='*80}")
        
        if not test_file.exists():
            log.error(f"ファイルが見つかりません: {test_file}")
            results.append({
                'file': test_file.name,
                'success': False,
                'error': 'ファイルが見つかりません'
            })
            continue
        
        # ファイル構造分析
        sheet_name, header_row = analyze_excel_structure(test_file)
        
        if sheet_name is None:
            log.error(f"適切なシート構造が見つかりませんでした: {test_file}")
            results.append({
                'file': test_file.name,
                'success': False,
                'error': '適切なシート構造が見つかりません'
            })
            continue
        
        # 動的検出テスト実行
        result = test_dynamic_detection_with_file(test_file, sheet_name, header_row)
        results.append(result)
    
    # 総合結果
    log.info(f"\n{'='*80}")
    log.info("=== 動的システム検証結果サマリー ===")
    log.info(f"{'='*80}")
    
    successful_tests = [r for r in results if r.get('success', False)]
    total_tests = len(results)
    
    log.info(f"総テスト数: {total_tests}")
    log.info(f"成功テスト数: {len(successful_tests)}")
    
    for result in results:
        if result['success']:
            log.info(f"✅ {result['file']}: {result['continuous_shifts']}件の連続勤務を検出")
            log.info(f"   パターン: {result['patterns']}種類, ルール: {result['rules']}個")
            log.info(f"   平均時間: {result['avg_duration']:.1f}時間, レコード: {result['records']}件")
        else:
            log.error(f"❌ {result['file']}: {result.get('error', '不明なエラー')}")
    
    if len(successful_tests) == total_tests:
        log.info("🎉 全テストファイルで動的連続勤務検出が成功しました！")
        log.info("✨ システムは完全に異なるデータ形式に動的対応可能です。")
        return True
    else:
        log.warning(f"⚠️ {total_tests - len(successful_tests)}個のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)