#!/usr/bin/env python3
"""
緊急問題特定システム - メインアプリの実際の状況を詳細に分析
"""
import requests
import json
import time
from pathlib import Path

def analyze_dash_app_structure():
    """Dashアプリの構造を詳細に分析"""
    print("=" * 80)
    print("❌ 緊急問題特定システム - メインアプリ分析")
    print("=" * 80)
    
    base_url = "http://127.0.0.1:8050"
    
    # 1. メインページの詳細分析
    print("\n🔍 1. メインページ詳細分析:")
    try:
        response = requests.get(base_url, timeout=10)
        html_content = response.text
        
        # 重要な要素の存在確認
        key_elements = [
            ("function-selector-dropdown", "プルダウンナビゲーション"),
            ("scenario-dropdown", "シナリオ選択"),
            ("main-content", "メインコンテンツ"),
            ("シフト分析システム", "タイトル"),
            ("main-title", "メインタイトルクラス"),
            ("navbar", "ナビゲーションバー"),
        ]
        
        print("  重要要素の存在確認:")
        for element_id, description in key_elements:
            found = element_id in html_content
            status = "✅" if found else "❌"
            print(f"    {status} {description} ({element_id}): {'検出' if found else '未検出'}")
        
        # CSS読み込み確認
        print("\n  CSS読み込み状況:")
        css_files = ["style.css", "test_style.css", "c2-mobile-integrated.css"]
        for css_file in css_files:
            found = css_file in html_content
            status = "✅" if found else "❌"
            print(f"    {status} {css_file}: {'読み込み中' if found else '未読み込み'}")
            
    except Exception as e:
        print(f"❌ メインページ分析エラー: {e}")
        return False
    
    # 2. Dashコンポーネント状態の確認
    print("\n🔍 2. Dashコンポーネント状態確認:")
    try:
        # _dash-config の確認
        if '_dash-config' in html_content:
            print("  ✅ Dash設定は存在")
            # 設定内容の詳細分析
            config_start = html_content.find('{"url_base_pathname"')
            if config_start != -1:
                config_end = html_content.find('}</script>', config_start) + 1
                config_text = html_content[config_start:config_end]
                try:
                    config = json.loads(config_text)
                    print(f"    - Dashバージョン: {config.get('dash_version', 'Unknown')}")
                    print(f"    - コールバック例外抑制: {config.get('suppress_callback_exceptions', 'Unknown')}")
                except:
                    print("    ⚠️ 設定の解析に失敗")
        else:
            print("  ❌ Dash設定が見つからない")
            
        # React entry point の確認
        if 'react-entry-point' in html_content:
            print("  ✅ Reactエントリーポイントは存在")
            if '_dash-loading' in html_content:
                print("  ⚠️ Dashは読み込み状態で停止している可能性")
        else:
            print("  ❌ Reactエントリーポイントが見つからない")
            
    except Exception as e:
        print(f"❌ コンポーネント状態確認エラー: {e}")
    
    # 3. 実際のUIレンダリング確認
    print("\n🔍 3. 実際のUIレンダリング確認:")
    try:
        # より詳細なHTTPリクエストでDashの内部状態を確認
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        
        # HTMLのサイズと内容を確認
        html_size = len(response.text)
        print(f"  HTMLサイズ: {html_size} bytes")
        
        if html_size < 1000:
            print("  ❌ HTMLが非常に小さい - レンダリング問題の可能性")
        elif html_size < 5000:
            print("  ⚠️ HTMLが小さい - 基本構造のみの可能性")
        else:
            print("  ✅ HTMLサイズは正常")
            
        # Dashの実際のコンテンツ確認
        if 'Loading...' in response.text and 'function-selector-dropdown' not in response.text:
            print("  ❌ DashコンテンツがLoading状態で停止")
            print("  ⚠️ 原因: コールバックエラーまたはJavaScript実行エラー")
        
    except Exception as e:
        print(f"❌ UIレンダリング確認エラー: {e}")
    
    return True

def analyze_critical_problems():
    """重大問題の特定"""
    print("\n" + "=" * 80)
    print("🚨 重大問題の特定と分類")
    print("=" * 80)
    
    problems = []
    
    # dash_app.pyの存在と基本構造確認
    dash_app_path = Path("C:/ShiftAnalysis/dash_app.py")
    if dash_app_path.exists():
        print("✅ dash_app.py は存在")
        
        # ファイルサイズ確認
        file_size = dash_app_path.stat().st_size
        print(f"  ファイルサイズ: {file_size:,} bytes")
        
        if file_size < 10000:
            problems.append("❌ dash_app.py が異常に小さい")
        
        # 重要な要素の存在確認
        try:
            with open(dash_app_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            critical_elements = [
                ("function-selector-dropdown", "プルダウンID"),
                ("ALL_FUNCTION_OPTIONS", "プルダウンオプション"),
                ("create_main_ui_tabs", "メインUI関数"),
                ("app.run_server", "サーバー起動"),
                ("assets_folder", "アセット設定"),
            ]
            
            print("  重要要素の存在確認:")
            for element, description in critical_elements:
                found = element in content
                status = "✅" if found else "❌"
                print(f"    {status} {description}: {'存在' if found else '未存在'}")
                if not found:
                    problems.append(f"❌ {description}が見つからない")
                    
        except Exception as e:
            problems.append(f"❌ dash_app.py 読み込みエラー: {e}")
    else:
        problems.append("❌ dash_app.py が存在しない")
    
    # CSSファイルの確認
    css_path = Path("C:/ShiftAnalysis/assets/style.css")
    if css_path.exists():
        print("\n✅ style.css は存在")
        css_size = css_path.stat().st_size
        print(f"  CSSファイルサイズ: {css_size:,} bytes")
        
        if css_size < 1000:
            problems.append("❌ style.css が異常に小さい")
    else:
        problems.append("❌ style.css が存在しない")
    
    return problems

def generate_critical_report(problems):
    """重大問題レポートの生成"""
    print("\n" + "=" * 80)
    print("📋 重大問題レポート")
    print("=" * 80)
    
    if not problems:
        print("✅ ファイル構造上の問題は検出されませんでした")
        print("⚠️ 問題はRuntime（実行時）エラーの可能性があります")
    else:
        print(f"❌ {len(problems)}個の重大問題を検出:")
        for i, problem in enumerate(problems, 1):
            print(f"  {i}. {problem}")
    
    print("\n🎯 次のステップの推奨:")
    print("1. Dashアプリのコールバックエラー詳細確認")
    print("2. ブラウザのJavaScriptコンソールエラー確認") 
    print("3. プルダウンナビゲーション実装の詳細検証")
    print("4. CSS適用状況の実際の確認")
    
    print("\n⚠️ 重要な注意:")
    print("現在のアプリは基本起動するが、実用的な機能が動作していない")
    print("表面的な「成功」ではなく、実際のユーザビリティが重要")

if __name__ == "__main__":
    try:
        # 基本分析
        if analyze_dash_app_structure():
            # 重大問題の特定
            problems = analyze_critical_problems()
            
            # レポート生成
            generate_critical_report(problems)
            
        print("\n" + "=" * 80)
        print("📊 結論: 詳細な問題分析が完了しました")
        print("次の段階: 特定された問題の修正計画立案")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 分析中にエラー: {e}")
        print("これ自体が重大な問題を示している可能性があります")