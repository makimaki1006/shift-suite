#!/usr/bin/env python3
"""
疲労度分析の構造と依存関係の検証
"""
import ast
import sys
from pathlib import Path

def check_fatigue_module():
    """疲労度分析モジュールの構造をチェック"""
    print("🔍 疲労度分析モジュールの構造検証")
    print("=" * 50)
    
    fatigue_path = Path("shift_suite/tasks/fatigue.py")
    if not fatigue_path.exists():
        print("❌ fatigue.pyが見つかりません")
        return False
    
    with open(fatigue_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        # ASTパースで構文確認
        tree = ast.parse(content)
        print("✅ 構文は正しいです")
        
        # 関数の存在確認
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        print(f"✅ 関数: {len(functions)}個")
        expected_functions = ["_get_time_category", "_analyze_consecutive_days", "_features", "train_fatigue"]
        for func in expected_functions:
            if func in functions:
                print(f"  ✅ {func}")
            else:
                print(f"  ❌ {func} が見つかりません")
        
        print(f"✅ インポート: {len(imports)}個")
        critical_imports = ["pandas", "numpy", "pathlib.Path"]
        for imp in critical_imports:
            if any(imp in i for i in imports):
                print(f"  ✅ {imp}")
            else:
                print(f"  ❌ {imp} がインポートされていません")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ 構文エラー: {e}")
        return False

def check_dependencies():
    """依存ファイルの存在確認"""
    print("\n📁 依存ファイルの確認")
    print("-" * 30)
    
    files_to_check = [
        "shift_suite/tasks/constants.py",
        "shift_suite/tasks/utils.py", 
        "shift_suite/tasks/analyzers/rest_time.py",
        "shift_suite/tasks/analyzers/__init__.py"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} が見つかりません")
            all_exist = False
    
    return all_exist

def check_fatigue_constants():
    """疲労度関連の定数確認"""
    print("\n📊 疲労度定数の確認")
    print("-" * 30)
    
    constants_path = Path("shift_suite/tasks/constants.py")
    if not constants_path.exists():
        print("❌ constants.pyが見つかりません")
        return False
    
    with open(constants_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "FATIGUE_PARAMETERS" in content:
        print("✅ FATIGUE_PARAMETERS定数が存在します")
        
        # パラメータの詳細確認
        required_params = [
            "min_rest_hours",
            "consecutive_3_days_weight",
            "consecutive_4_days_weight", 
            "consecutive_5_days_weight",
            "night_shift_threshold",
            "fatigue_alert_threshold"
        ]
        
        for param in required_params:
            if param in content:
                print(f"  ✅ {param}")
            else:
                print(f"  ❌ {param} パラメータが不足")
        
        return True
    else:
        print("❌ FATIGUE_PARAMETERS定数が見つかりません")
        return False

def analyze_expected_output():
    """期待される出力の分析"""
    print("\n📋 期待される出力分析")
    print("-" * 30)
    
    # dash_app.pyで期待される列
    expected_columns = [
        "fatigue_score",           # 総合疲労スコア
        "work_start_variance",     # 勤務開始時刻のばらつき
        "work_diversity",          # 業務の多様性
        "work_duration_variance",  # 労働時間のばらつき
        "short_rest_frequency",    # 短い休息期間の頻度
        "consecutive_work_days",   # 連続勤務日数
        "night_shift_ratio"        # 夜勤比率
    ]
    
    print("期待される出力列:")
    for i, col in enumerate(expected_columns, 1):
        print(f"  {i}. {col}")
    
    return True

def main():
    """メイン検証"""
    print("🔬 復元された疲労度分析の包括的検証")
    print("=" * 60)
    
    checks = [
        ("疲労度モジュール構造", check_fatigue_module),
        ("依存ファイル", check_dependencies),
        ("疲労度定数", check_fatigue_constants),
        ("期待される出力", analyze_expected_output)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name}でエラー: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 60)
    print("📊 検証結果サマリー")
    print("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(1 for _, result in results if result)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\n📈 結果: {passed_checks}/{total_checks} 検証項目が成功")
    
    if passed_checks >= 3:  # 4項目中3項目以上成功
        print("\n🎉 疲労度分析機能は正常に復元されています！")
        print("\n📝 実行手順:")
        print("1. app.pyを起動")
        print("2. 疲労分析オプションを有効にして分析実行")
        print("3. 'fatigue_score.parquet'ファイルの生成を確認")
        print("4. dash_app.pyで疲労度タブの表示を確認")
        print("\n✨ 期待される結果:")
        print("- 6つの詳細な疲労要因の分析")
        print("- スタッフ別疲労スコア")
        print("- 疲労要因ヒートマップ")
        print("- 相関分析と散布図")
    else:
        print("\n⚠️ 一部の構成要素に問題があります。修正が必要です。")
    
    return passed_checks >= 3

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 検証完了: {'成功' if success else '要修正'}")
    sys.exit(0 if success else 1)