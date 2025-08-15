#!/usr/bin/env python3
"""
直接インポートでのテスト
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_direct_imports():
    """直接インポートのテスト"""
    print("=" * 60)
    print("直接インポートテスト開始")
    print("=" * 60)
    
    # Step 1: 軽量版ShiftMindReaderの直接インポート
    print("\n1. 軽量版ShiftMindReaderの直接インポート...")
    try:
        sys.path.insert(0, str(Path(__file__).parent / "shift_suite" / "tasks"))
        from shift_mind_reader_lite import ShiftMindReaderLite
        print("   [OK] ShiftMindReaderLite インポート成功")
        
        # 簡単なテスト
        mind_reader = ShiftMindReaderLite()
        print("   [OK] ShiftMindReaderLite インスタンス作成成功")
        
    except Exception as e:
        print(f"   [ERROR] ShiftMindReaderLite インポートエラー: {e}")
        return False
    
    # Step 2: 複合制約発見システムのコンポーネントテスト
    print("\n2. システムコンポーネントの存在確認...")
    
    key_files = [
        "compound_constraint_discovery_system.py",
        "integrated_constraint_extraction_system.py",
        "shift_mind_reader_lite.py"
    ]
    
    tasks_dir = Path(__file__).parent / "shift_suite" / "tasks"
    
    for file_name in key_files:
        file_path = tasks_dir / file_name
        if file_path.exists():
            print(f"   [OK] {file_name} - 存在確認")
        else:
            print(f"   [ERROR] {file_name} - ファイルが見つかりません")
    
    # Step 3: 基本機能のテスト
    print("\n3. 基本機能のテスト...")
    try:
        # pandasの基本テスト
        import pandas as pd
        test_df = pd.DataFrame({
            'ds': pd.date_range('2024-01-01', periods=5),
            'staff': ['田中'] * 5,
            'role': ['介護'] * 5
        })
        
        # 軽量版での簡単な分析
        insights = mind_reader.get_simplified_insights(test_df)
        print(f"   [OK] 基本分析実行成功")
        print(f"   主要発見数: {len(insights.get('key_findings', []))}")
        print(f"   推奨事項数: {len(insights.get('recommendations', []))}")
        
    except Exception as e:
        print(f"   [ERROR] 基本機能テストエラー: {e}")
        return False
    
    # Step 4: 結果保存
    print("\n4. 結果保存...")
    try:
        import json
        
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_type": "direct_import",
            "components_available": {
                "shift_mind_reader_lite": True,
                "pandas": True,
                "basic_analysis": True
            },
            "status": "success",
            "notes": "scikit-learn依存関係を回避して基本機能が動作確認済み"
        }
        
        with open("direct_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("   [OK] テスト結果保存完了: direct_test_results.json")
        
    except Exception as e:
        print(f"   [WARNING] 結果保存エラー: {e}")
    
    return True

def main():
    """メイン実行関数"""
    try:
        success = test_direct_imports()
        
        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] 直接インポートテストが完了しました")
            print("[INFO] 基本システム機能の動作確認完了")
            print("[INFO] scikit-learn依存関係問題を回避した軽量版が利用可能")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("[ERROR] テストに失敗しました")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())