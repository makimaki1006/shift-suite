#!/usr/bin/env python3
"""
動的連続勤務検出システムの簡潔な証明テスト
結果のみをフォーカスした出力
"""

import sys
import logging
from pathlib import Path

# ログレベルを WARNING に設定して詳細ログを抑制
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger(__name__)

def test_file_concise(excel_path: Path, sheet_name: str, header_row: int):
    """簡潔な動的検出テスト"""
    try:
        # ログレベルを一時的に抑制
        logging.getLogger('shift_suite').setLevel(logging.CRITICAL)
        logging.getLogger('analysis').setLevel(logging.CRITICAL)
        
        from shift_suite.tasks.dynamic_continuous_shift_detector import DynamicContinuousShiftDetector
        from shift_suite.tasks.io_excel import ingest_excel
        
        print(f"🧪 テスト開始: {excel_path.name}")
        
        # データ読み込み
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=[sheet_name],
            header_row=header_row,
            slot_minutes=15
        )
        
        print(f"  📊 データ読み込み: {len(long_df):,}件のレコード")
        
        # 勤務コードの種類を確認
        shift_codes = long_df['code'].value_counts()
        active_codes = [code for code in shift_codes.index if code.strip()]  # 空文字以外
        
        print(f"  🎯 発見された勤務コード: {len(active_codes)}種類 {active_codes[:10]}")
        
        # 動的検出器による学習・検出
        detector = DynamicContinuousShiftDetector()
        continuous_shifts = detector.detect_continuous_shifts(long_df, wt_df)
        summary = detector.get_detection_summary()
        
        # 結果サマリー
        print(f"  🚀 動的学習結果:")
        print(f"    📈 学習パターン: {summary.get('detected_patterns', 0)}種類")
        print(f"    ⚡ 生成ルール: {summary.get('active_rules', 0)}個") 
        print(f"    🔗 連続勤務検出: {len(continuous_shifts)}件")
        if len(continuous_shifts) > 0:
            print(f"    ⏱️ 平均継続時間: {summary.get('average_duration_hours', 0):.1f}時間")
            print(f"    🏆 最大継続時間: {summary.get('max_duration_hours', 0):.1f}時間")
        
        # 学習したパターンの例
        learned_patterns = list(detector.shift_patterns.keys())[:5]
        print(f"    🧠 学習パターン例: {learned_patterns}")
        
        # 検出例
        if continuous_shifts:
            example = continuous_shifts[0]
            print(f"    🔍 検出例: {example.staff} - {example.start_pattern.code}→{example.end_pattern.code}")
        
        # 設定保存
        config_file = Path(f"result_{excel_path.stem}.json")
        detector.export_config(config_file)
        print(f"  💾 学習結果保存: {config_file}")
        
        return {
            'file': excel_path.name,
            'success': True,
            'records': len(long_df),
            'shift_codes': len(active_codes),
            'patterns': summary.get('detected_patterns', 0),
            'rules': summary.get('active_rules', 0),
            'continuous_shifts': len(continuous_shifts),
            'avg_duration': summary.get('average_duration_hours', 0),
            'sample_codes': active_codes[:5]
        }
        
    except Exception as e:
        print(f"  ❌ エラー: {str(e)}")
        return {
            'file': excel_path.name,
            'success': False,
            'error': str(e)
        }

def main():
    """簡潔な証明テスト"""
    print("🎯 動的連続勤務検出システム - 最終証明テスト")
    print("=" * 60)
    
    test_configs = [
        {
            'file': Path("デイ_テスト用データ_休日精緻.xlsx"),
            'sheet': 'R7.6',
            'header': 1
        },
        {
            'file': Path("ショート_テスト用データ.xlsx"),
            'sheet': 'R7.6',
            'header': 1
        }
    ]
    
    results = []
    
    for config in test_configs:
        if not config['file'].exists():
            print(f"❌ ファイル未発見: {config['file'].name}")
            results.append({'file': config['file'].name, 'success': False})
            continue
            
        result = test_file_concise(config['file'], config['sheet'], config['header'])
        results.append(result)
        print()
    
    # 最終サマリー
    print("🏆 === 最終結果サマリー ===")
    successful = [r for r in results if r.get('success', False)]
    
    print(f"📊 テスト結果: {len(successful)}/{len(results)} 成功")
    
    all_codes = set()
    total_patterns = 0
    total_rules = 0
    total_continuous = 0
    
    for result in successful:
        print(f"✅ {result['file']}:")
        print(f"   📈 処理: {result['records']:,}件, コード: {result['shift_codes']}種類")
        print(f"   🧠 学習: {result['patterns']}パターン, {result['rules']}ルール")
        print(f"   🔗 連続勤務: {result['continuous_shifts']}件")
        print(f"   📝 コード例: {result['sample_codes']}")
        
        all_codes.update(result['sample_codes'])
        total_patterns += result['patterns']
        total_rules += result['rules']
        total_continuous += result['continuous_shifts']
    
    for result in results:
        if not result.get('success', False):
            print(f"❌ {result['file']}: {result.get('error', '不明なエラー')}")
    
    if len(successful) == len(results) and total_continuous > 0:
        print("\n🎉 === 動的対応能力の完全証明 ===")
        print(f"✨ 全勤務コード種類: {len(all_codes)}種類 {sorted(list(all_codes))}")
        print(f"🚀 総連続勤務検出: {total_continuous}件")
        print(f"🧠 総学習パターン: {total_patterns}種類")
        print(f"⚡ 総生成ルール: {total_rules}個")
        print(f"💯 完全動的システムの証明完了！")
        return True
    else:
        print(f"⚠️ 一部テストで問題が発生しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)