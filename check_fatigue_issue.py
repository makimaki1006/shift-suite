#!/usr/bin/env python3
"""疲労分析タブの問題を調査するスクリプト"""

import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_fatigue_module():
    """疲労分析モジュールの状態を確認"""
    print("=== 疲労分析モジュールの確認 ===")
    
    # 1. ENABLE_ADVANCED_FEATURESの確認
    dash_app_path = project_root / "dash_app.py"
    if dash_app_path.exists():
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'ENABLE_ADVANCED_FEATURES = False' in content:
                print("❌ ENABLE_ADVANCED_FEATURES = False に設定されています")
                print("   → 疲労分析タブは無効化されています")
            elif 'ENABLE_ADVANCED_FEATURES = True' in content:
                print("✅ ENABLE_ADVANCED_FEATURES = True に設定されています")
            else:
                print("⚠️  ENABLE_ADVANCED_FEATURESの設定が見つかりません")
    
    # 2. 疲労分析データファイルの存在確認
    print("\n=== 疲労分析データファイルの確認 ===")
    analysis_results_dir = project_root / "analysis_results"
    if analysis_results_dir.exists():
        fatigue_files = list(analysis_results_dir.rglob("fatigue_score.parquet"))
        if fatigue_files:
            print(f"✅ {len(fatigue_files)}個の疲労分析データファイルが見つかりました:")
            for file in fatigue_files[:5]:  # 最初の5個まで表示
                print(f"   - {file.relative_to(project_root)}")
                # ファイルサイズを確認
                file_size = file.stat().st_size
                print(f"     ファイルサイズ: {file_size} bytes")
        else:
            print("❌ fatigue_score.parquetファイルが見つかりません")
    
    # 3. 疲労分析関数の存在確認
    print("\n=== 疲労分析関数の確認 ===")
    fatigue_module_path = project_root / "shift_suite" / "tasks" / "fatigue.py"
    if fatigue_module_path.exists():
        print("✅ shift_suite/tasks/fatigue.py が存在します")
        with open(fatigue_module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'def train_fatigue' in content:
                print("✅ train_fatigue関数が定義されています")
            if 'fatigue_score.parquet' in content:
                print("✅ fatigue_score.parquetの保存処理が実装されています")
    else:
        print("❌ shift_suite/tasks/fatigue.py が見つかりません")
    
    # 4. dash_app.pyでの疲労分析タブの実装確認
    print("\n=== dash_app.pyでの疲労分析タブ実装の確認 ===")
    if dash_app_path.exists():
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            checks = {
                'create_fatigue_tab関数': 'def create_fatigue_tab',
                '疲労分析タブの定義': "dcc.Tab(label='疲労分析', value='fatigue')",
                'fatigue-tab-container': "id='fatigue-tab-container'",
                'fatigue_score データ取得': "data_get('fatigue_score'",
                'initialize_fatigue_content コールバック': "def initialize_fatigue_content"
            }
            
            for check_name, check_str in checks.items():
                if check_str in content:
                    print(f"✅ {check_name} が実装されています")
                else:
                    print(f"❌ {check_name} が見つかりません")
    
    # 5. app.pyでの疲労分析実行の確認
    print("\n=== app.pyでの疲労分析実行の確認 ===")
    app_path = project_root / "app.py"
    if app_path.exists():
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'train_fatigue' in content:
                print("✅ train_fatigue関数の呼び出しが実装されています")
                # train_fatigueの呼び出し回数を数える
                count = content.count('train_fatigue(')
                print(f"   呼び出し回数: {count}回")
            else:
                print("❌ train_fatigue関数の呼び出しが見つかりません")

def main():
    """メイン処理"""
    print("疲労分析タブの問題調査を開始します...\n")
    
    check_fatigue_module()
    
    print("\n=== 推奨される対処法 ===")
    print("1. ENABLE_ADVANCED_FEATURES = True に設定する")
    print("2. app.pyで分析を実行して fatigue_score.parquet を生成する")
    print("3. dash_app.pyを再起動して疲労分析タブを確認する")

if __name__ == "__main__":
    main()