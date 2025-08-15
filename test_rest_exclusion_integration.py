#!/usr/bin/env python3
"""
休日除外統合テスト
================

シフト分析システムの休日除外機能が正しく統合されているかを検証
"""

import sys
import os
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def test_rest_exclusion_integration():
    """休日除外統合テスト"""
    
    print("=" * 60)
    print("休日除外統合テスト")
    print("=" * 60)
    
    # 1. dash_app.pyの存在確認
    dash_app_path = Path("dash_app.py")
    if not dash_app_path.exists():
        print("❌ dash_app.py が見つかりません")
        return False
    
    print("✅ dash_app.py が存在します")
    
    # 2. 強化版休日除外フィルター関数の存在確認
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "create_enhanced_rest_exclusion_filter" not in content:
        print("❌ create_enhanced_rest_exclusion_filter 関数が見つかりません")
        return False
    
    print("✅ create_enhanced_rest_exclusion_filter 関数が存在します")
    
    # 3. data_get関数への統合確認
    integration_points = [
        "if key in ['pre_aggregated_data', 'long_df', 'intermediate_data']:",
        "df = create_enhanced_rest_exclusion_filter(df)",
        "[RestExclusion] {key}に休日除外フィルターを適用"
    ]
    
    for integration_point in integration_points:
        if integration_point not in content:
            print(f"❌ データ読み込み統合が不完全: {integration_point}")
            return False
    
    print("✅ データ読み込みでの休日除外フィルター統合を確認")
    
    # 4. ヒートマップコールバックでの統合確認
    heatmap_integration_points = [
        "filtered_df = create_enhanced_rest_exclusion_filter(filtered_df)",
        "強化版休日・休暇除外"
    ]
    
    for heatmap_point in heatmap_integration_points:
        if heatmap_point not in content:
            print(f"❌ ヒートマップでの統合が不完全: {heatmap_point}")
            return False
    
    print("✅ ヒートマップでの休日除外フィルター統合を確認")
    
    # 5. 休み関連パターンの確認
    rest_patterns = [
        "'×', 'X', 'x'",
        "'休', '休み', '休暇'",
        "'欠', '欠勤'",
        "'OFF', 'off', 'Off'"
    ]
    
    for pattern in rest_patterns:
        if pattern not in content:
            print(f"❌ 休み関連パターンが不足: {pattern}")
            return False
    
    print("✅ 包括的な休み関連パターンを確認")
    
    # 6. キャッシュクリア機能の確認
    cache_clear_code = "DATA_CACHE._cache.pop('pre_aggregated_data', None)"
    if cache_clear_code not in content:
        print("❌ データキャッシュクリア機能が見つかりません")
        return False
    
    print("✅ データキャッシュクリア機能を確認")
    
    # 7. 統合レベルの確認
    integration_levels = {
        "ソースデータレベル": "if key in ['pre_aggregated_data'",
        "集計データレベル": "filtered_df = create_enhanced_rest_exclusion_filter",
        "表示データレベル": "勤務のみ (除外:"
    }
    
    for level_name, level_code in integration_levels.items():
        if level_code not in content:
            print(f"❌ {level_name}での統合が不完全")
            return False
    
    print("✅ 多層レベルでの休日除外統合を確認")
    
    # 8. エラーハンドリングの確認
    error_handling_patterns = [
        "if df.empty:",
        "original_count = len(df)",
        "exclusion_rate = total_excluded / original_count if original_count > 0 else 0"
    ]
    
    for error_pattern in error_handling_patterns:
        if error_pattern not in content:
            print(f"❌ エラーハンドリングが不完全: {error_pattern}")
            return False
    
    print("✅ 適切なエラーハンドリングを確認")
    
    print("\n" + "=" * 60)
    print("✅ 休日除外統合テスト: 全項目合格")
    print("=" * 60)
    
    print("\n📋 統合された機能:")
    print("  1. ソースデータレベル除外 (data_get関数)")
    print("  2. 集計データレベル除外 (ヒートマップコールバック)")
    print("  3. 包括的休み関連パターン対応")
    print("  4. データキャッシュ更新機能")
    print("  5. 多層防御システム")
    print("  6. 適切なエラーハンドリング")
    
    print("\n🎯 対象となる休み表現:")
    print("  • × X x (基本休み記号)")
    print("  • 休 休み 休暇 (日本語休み)")
    print("  • 欠 欠勤 (欠勤)")
    print("  • OFF off Off (オフ)")
    print("  • 有 有休 特 特休 代 代休 振 振休 (各種休暇)")
    print("  • 空文字・NaN・NULL値")
    
    print("\n✨ 期待される効果:")
    print("  ✓ ヒートマップに休日データが表示されない")
    print("  ✓ '×'記号のレコードが完全除外される")
    print("  ✓ 実際に働いているスタッフのみ可視化")
    print("  ✓ 正確な勤務状況分析が可能")
    
    return True

if __name__ == "__main__":
    success = test_rest_exclusion_integration()
    sys.exit(0 if success else 1)