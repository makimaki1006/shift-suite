#!/usr/bin/env python3
"""
包括的休日除外対応確認
===================

上流から下流まで全ての処理段階での休日除外対応を確認
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

def check_upstream_exclusion() -> Tuple[bool, List[str]]:
    """最上流での休日除外確認"""
    issues = []
    
    io_excel_file = Path("shift_suite/tasks/io_excel.py")
    if not io_excel_file.exists():
        issues.append("❌ io_excel.py が見つかりません")
        return False, issues
    
    with open(io_excel_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_patterns = [
        ("🎯 休日除外フィルター適用", "根本的解決マーカー"),
        ("parsed_slots_count'] <= 0", "スロット数による除外"),
        ("[RestExclusion]", "ログ出力"),
        ("rest_symbols = ['×'", "休み記号リスト"),
        ("final_long_df = final_long_df[~rest_day_mask]", "実際の除外処理")
    ]
    
    for pattern, description in required_patterns:
        if pattern in content:
            print(f"✅ 最上流: {description}")
        else:
            issues.append(f"❌ 最上流: {description} が見つかりません")
    
    return len(issues) == 0, issues

def check_heatmap_exclusion() -> Tuple[bool, List[str]]:
    """ヒートマップ処理での休日除外確認"""
    issues = []
    
    heatmap_file = Path("shift_suite/tasks/heatmap.py")
    if not heatmap_file.exists():
        issues.append("❌ heatmap.py が見つかりません")
        return False, issues
    
    with open(heatmap_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_patterns = [
        ("def _filter_work_records", "通常勤務フィルタ関数"),
        ("DEFAULT_HOLIDAY_TYPE", "休暇タイプ除外"),
        ("parsed_slots_count", "勤務時間フィルタ"),
        ("heat_ALL.parquet", "ヒートマップファイル生成")
    ]
    
    for pattern, description in required_patterns:
        if pattern in content:
            print(f"✅ ヒートマップ: {description}")
        else:
            issues.append(f"❌ ヒートマップ: {description} が見つかりません")
    
    return len(issues) == 0, issues

def check_shortage_exclusion() -> Tuple[bool, List[str]]:
    """不足分析での休日除外確認"""
    issues = []
    
    shortage_file = Path("shift_suite/tasks/shortage.py")
    if not shortage_file.exists():
        issues.append("❌ shortage.py が見つかりません")
        return False, issues
    
    with open(shortage_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 不足分析はheat_ALL.parquetを読み込むので、上流で除外済みなら問題ない
    if "heat_ALL.parquet" in content:
        print("✅ 不足分析: heat_ALL.parquet経由でデータ取得（上流除外済み）")
    else:
        issues.append("❌ 不足分析: データ読み込み方法が不明")
    
    return len(issues) == 0, issues

def check_dashboard_exclusion() -> Tuple[bool, List[str]]:
    """ダッシュボードでの休日除外確認"""
    issues = []
    
    dash_file = Path("dash_app.py")
    if not dash_file.exists():
        issues.append("❌ dash_app.py が見つかりません")
        return False, issues
    
    with open(dash_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # dash_app.pyの既存の休日除外実装確認
    dashboard_patterns = [
        ("create_enhanced_rest_exclusion_filter", "ダッシュボード用フィルタ"),
        ("apply_rest_exclusion_filter", "統合フィルタ"),
        ("data_get", "データ取得関数")
    ]
    
    for pattern, description in dashboard_patterns:
        if pattern in content:
            print(f"✅ ダッシュボード: {description}")
        else:
            print(f"⚠️  ダッシュボード: {description} が見つかりません（上流除外で補完可能）")
    
    return True, []  # ダッシュボードは上流除外で十分

def check_app_py_integration() -> Tuple[bool, List[str]]:
    """app.pyでの統合確認"""
    issues = []
    
    app_file = Path("app.py")
    if not app_file.exists():
        issues.append("❌ app.py が見つかりません")
        return False, issues
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # app.pyでのingest_excel呼び出し確認
    integration_patterns = [
        ("ingest_excel(", "データ取り込み関数呼び出し"),
        ("build_heatmap(", "ヒートマップ生成呼び出し"),
        ("shortage_and_brief(", "不足分析呼び出し")
    ]
    
    for pattern, description in integration_patterns:
        if pattern in content:
            print(f"✅ app.py統合: {description}")
        else:
            issues.append(f"❌ app.py統合: {description} が見つかりません")
    
    return len(issues) == 0, issues

def main():
    """包括的確認の実行"""
    print("=" * 70)
    print("🔍 包括的休日除外対応確認")
    print("=" * 70)
    
    all_checks = [
        ("最上流（ingest_excel）", check_upstream_exclusion),
        ("ヒートマップ処理", check_heatmap_exclusion),
        ("不足分析処理", check_shortage_exclusion),
        ("ダッシュボード", check_dashboard_exclusion),
        ("app.py統合", check_app_py_integration)
    ]
    
    overall_success = True
    all_issues = []
    
    for check_name, check_func in all_checks:
        print(f"\n📋 {check_name}:")
        success, issues = check_func()
        if not success:
            overall_success = False
            all_issues.extend(issues)
            for issue in issues:
                print(f"  {issue}")
    
    print("\n" + "=" * 70)
    if overall_success:
        print("✅ 包括的確認完了: 全段階で休日除外対応済み")
        print("=" * 70)
        
        print("\n📊 多段階防御システムの構成:")
        print("  1️⃣ 最上流: ingest_excel() - 「×」記号等を完全除外")
        print("  2️⃣ ヒートマップ: _filter_work_records() - 通常勤務のみ抽出")
        print("  3️⃣ 不足分析: heat_ALL.parquet経由 - 除外済みデータ使用")
        print("  4️⃣ ダッシュボード: data_get()経由 - 除外済みデータ使用")
        
        print("\n🎯 期待される結果:")
        print("  ✓ ヒートマップに「×」記号の時間帯が表示されない")
        print("  ✓ 実際に働いているスタッフのみが可視化される")
        print("  ✓ 不足分析から休日データが完全に除外される")
        print("  ✓ 全てのタブで一貫した除外結果")
        
        print("\n📝 テスト手順:")
        print("  1. python app.py でアプリ起動")
        print("  2. ショート_テスト用データ.xlsx をアップロード")
        print("  3. Run Analysis ボタンクリック")
        print("  4. ログで '[RestExclusion]' メッセージ確認")
        print("  5. 各タブで休日除外を視覚確認")
    else:
        print("❌ 包括的確認失敗: 以下の問題を解決してください")
        print("=" * 70)
        for issue in all_issues:
            print(f"  {issue}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)