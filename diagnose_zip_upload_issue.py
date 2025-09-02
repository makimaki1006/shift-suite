#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ZIPファイルアップロード問題の包括的診断スクリプト
複数の原因パターンを体系的に調査
"""

import sys
import re
from pathlib import Path
import json

def print_section(title):
    """セクション見出しを表示"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_file_structure():
    """必要なファイル構造を確認"""
    print_section("1. ファイル構造チェック")
    
    required_files = {
        'dash_app.py': 'メインアプリケーション',
        'error_boundary.py': 'エラーハンドリング',
        'memory_guard.py': 'メモリ管理',
        'shift_suite/tasks/utils.py': 'ユーティリティ',
        'assets/style.css': 'スタイルシート'
    }
    
    issues = []
    for file_path, description in required_files.items():
        if Path(file_path).exists():
            print(f"  OK {file_path} - {description}")
        else:
            print(f"  NG {file_path} - {description} [欠落]")
            issues.append(f"Missing: {file_path}")
    
    return issues

def check_layout_elements():
    """レイアウト要素の存在確認"""
    print_section("2. レイアウト要素チェック")
    
    if not Path('dash_app.py').exists():
        print("  NG dash_app.py が見つかりません")
        return ["dash_app.py not found"]
    
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_elements = {
        "id='upload-data'": "アップロードコンポーネント",
        "id='data-ingestion-output'": "データ出力ストレージ",
        "id='scenario-dropdown'": "シナリオドロップダウン",
        "id='scenario-selector-div'": "シナリオセレクタコンテナ",
        "id='upload-status'": "アップロードステータス表示"
    }
    
    issues = []
    for element_id, description in required_elements.items():
        # IDの両方の記法をチェック
        pattern1 = element_id.replace("'", '"')  # ダブルクォート版
        pattern2 = element_id  # シングルクォート版
        
        if pattern1 in content or pattern2 in content:
            print(f"  OK {element_id} - {description}")
        else:
            print(f"  NG {element_id} - {description} [未定義]")
            issues.append(f"Missing element: {element_id}")
    
    return issues

def check_callback_chain():
    """コールバックチェーンの確認"""
    print_section("3. コールバックチェーン")
    
    if not Path('dash_app.py').exists():
        return ["dash_app.py not found"]
    
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    callback_patterns = [
        (r'Input\(["\']upload-data["\'],\s*["\']contents["\']', 
         "アップロードコールバック"),
        (r'def handle_file_upload\(contents, filename\):', 
         "handle_file_upload関数"),
        (r'def process_upload\(contents, filename\):', 
         "process_upload関数"),
        (r'Output\(["\']scenario-dropdown["\'],\s*["\']options["\']', 
         "scenario-dropdown更新")
    ]
    
    issues = []
    for pattern, description in callback_patterns:
        if re.search(pattern, content):
            print(f"  OK {description}")
        else:
            print(f"  NG {description} [未検出]")
            issues.append(f"Missing: {description}")
    
    return issues

def check_data_flow():
    """データフローの完全性確認"""
    print_section("4. データフローチェック")
    
    if not Path('dash_app.py').exists():
        return ["dash_app.py not found"]
    
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    data_flow_checks = [
        (r'global TEMP_DIR_OBJ', "TEMP_DIR_OBJ グローバル変数"),
        (r'global CURRENT_SCENARIO_DIR', "CURRENT_SCENARIO_DIR グローバル変数"),
        (r'clear_data_cache\(\)', "キャッシュクリア呼び出し"),
        (r'detect_slot_intervals_from_data|detect_and_update_slot_interval', "スロット間隔検出"),
        (r'tempfile\.TemporaryDirectory', "一時ディレクトリ作成"),
        (r'zipfile\.ZipFile', "ZIP解凍処理")
    ]
    
    issues = []
    for pattern, description in data_flow_checks:
        if re.search(pattern, content):
            print(f"  OK {description}")
        else:
            print(f"  NG {description} [未実装]")
            issues.append(f"Missing: {description}")
    
    return issues

def check_error_handling():
    """エラーハンドリングの確認"""
    print_section("5. エラーハンドリング")
    
    if not Path('dash_app.py').exists():
        return ["dash_app.py not found"]
    
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    error_patterns = [
        (r'@safe_callback', "safe_callbackデコレータ"),
        (r'try:.*?except.*?zipfile\.BadZipFile', "BadZipFileハンドリング"),
        (r'PreventUpdate', "PreventUpdate使用"),
        (r'log\.error\(.*?\[handle_file_upload\]', "handle_file_uploadエラーログ"),
        (r'log\.info\(.*?\[データ入稿\]', "データ入稿ログ")
    ]
    
    issues = []
    for pattern, description in error_patterns:
        if re.search(pattern, content, re.DOTALL):
            print(f"  OK {description}")
        else:
            print(f"  NG {description} [未実装]")
            issues.append(f"Missing: {description}")
    
    return issues

def check_common_issues():
    """よくある問題パターンのチェック"""
    print_section("6. よくある問題パターン")
    
    if not Path('dash_app.py').exists():
        return ["dash_app.py not found"]
    
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 問題になりやすいパターン
    potential_issues = []
    
    # 1. handle_file_uploadがprocess_uploadを呼んでいるか
    if 'def handle_file_upload' in content:
        func_start = content.index('def handle_file_upload')
        func_end = content.find('\ndef ', func_start + 1)
        if func_end == -1:
            func_end = content.find('\n@app.callback', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        if 'process_upload(' not in func_body:
            print("  NG handle_file_uploadがprocess_uploadを呼び出していない")
            potential_issues.append("handle_file_upload doesn't call process_upload")
        else:
            print("  OK handle_file_uploadがprocess_uploadを正しく呼び出している")
    
    # 2. process_uploadの戻り値が正しいか
    if 'def process_upload' in content:
        func_start = content.index('def process_upload')
        func_end = content.find('\ndef ', func_start + 1)
        if func_end == -1:
            func_end = content.find('\n@app.callback', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        # 4つの要素を返しているか確認
        return_pattern = r'return\s+[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+'
        if not re.search(return_pattern, func_body):
            print("  NG process_uploadが4つの値を返していない可能性")
            potential_issues.append("process_upload may not return 4 values")
        else:
            print("  OK process_uploadが正しい形式で値を返している")
    
    # 3. Interval更新が過剰でないか
    interval_count = content.count('dcc.Interval(')
    if interval_count > 5:
        print(f"  WARN Intervalコンポーネントが{interval_count}個 - パフォーマンスに影響の可能性")
        potential_issues.append(f"Too many Interval components: {interval_count}")
    else:
        print(f"  OK Intervalコンポーネント数: {interval_count}個（適正）")
    
    return potential_issues

def generate_fix_suggestions(all_issues):
    """修正提案の生成"""
    print_section("修正提案")
    
    if not all_issues:
        print("  OK 重大な問題は検出されませんでした")
        return
    
    suggestions = {
        "Missing element: id='upload-status'": 
            "dash_app.pyのレイアウトに以下を追加:\n"
            "  html.Div(id='upload-status', style={'marginTop': '10px'})",
        
        "Missing element: id='data-ingestion-output'":
            "dash_app.pyのレイアウトに以下を追加:\n"
            "  dcc.Store(id='data-ingestion-output', storage_type='memory')",
        
        "Missing element: id='scenario-selector-div'":
            "scenario-selector-divはすでに存在します。\n"
            "  コールバックのOutputを確認してください。",
        
        "Missing: handle_file_upload関数":
            "handle_file_uploadコールバック関数が定義されていません。\n"
            "  fix_upload_callback.pyを参照して追加してください。",
        
        "handle_file_upload doesn't call process_upload":
            "handle_file_upload内でprocess_upload関数を呼び出すように修正:\n"
            "  result = process_upload(contents, filename)",
        
        "Missing: キャッシュクリア呼び出し":
            "process_upload関数内でキャッシュをクリア:\n"
            "  clear_data_cache()",
        
        "Missing: CURRENT_SCENARIO_DIR グローバル変数":
            "process_upload関数内でグローバル変数を更新:\n"
            "  global CURRENT_SCENARIO_DIR\n"
            "  CURRENT_SCENARIO_DIR = temp_dir_path / first_scenario"
    }
    
    for issue in all_issues:
        if issue in suggestions:
            print(f"\n  FIX {issue}")
            print(f"     {suggestions[issue]}")

def main():
    """メイン診断処理"""
    print("="*60)
    print("  ZIPファイルアップロード問題 - 包括的診断")
    print("="*60)
    
    all_issues = []
    
    # 各チェックを実行
    all_issues.extend(check_file_structure())
    all_issues.extend(check_layout_elements())
    all_issues.extend(check_callback_chain())
    all_issues.extend(check_data_flow())
    all_issues.extend(check_error_handling())
    all_issues.extend(check_common_issues())
    
    # 結果サマリー
    print_section("診断結果サマリー")
    
    if all_issues:
        print(f"  WARN {len(all_issues)}個の問題が検出されました:")
        for i, issue in enumerate(all_issues, 1):
            print(f"    {i}. {issue}")
    else:
        print("  OK 構造的な問題は検出されませんでした")
        print("\n  他の可能性:")
        print("    - ブラウザのキャッシュ問題")
        print("    - ZIPファイル自体の構造問題")
        print("    - ネットワークタイムアウト")
        print("    - メモリ不足")
    
    # 修正提案
    generate_fix_suggestions(all_issues)
    
    # 診断ログファイル作成
    print_section("診断ログ")
    
    log_data = {
        'issues': all_issues,
        'file_exists': {
            'dash_app.py': Path('dash_app.py').exists(),
            'error_boundary.py': Path('error_boundary.py').exists(),
            'memory_guard.py': Path('memory_guard.py').exists()
        }
    }
    
    with open('zip_upload_diagnosis.json', 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    print("  診断結果を zip_upload_diagnosis.json に保存しました")
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)