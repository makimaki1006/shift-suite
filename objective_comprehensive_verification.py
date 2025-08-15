#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客観的包括検証システム - ユーザー目線でのUI/UX完全性確認
"""

import os
import sys
import time
import traceback
from pathlib import Path

# UTF-8出力設定
os.environ['PYTHONIOENCODING'] = 'utf-8'

def comprehensive_verification():
    print("=== 客観的包括検証 - ユーザー目線チェック ===")
    print()
    
    verification_results = {
        'basic_functionality': [],
        'ui_ux_issues': [],
        'data_consistency': [],
        'error_handling': [],
        'performance_issues': [],
        'user_experience': []
    }
    
    # 1. 基本機能検証
    print("1. 基本機能の動作検証")
    print("-" * 40)
    
    try:
        # ダッシュボード起動テスト（実際のUI生成）
        print("1.1 ダッシュボード起動テスト")
        start_time = time.time()
        import dash_app
        
        # アプリケーション基本情報
        app = dash_app.app
        if not app:
            verification_results['basic_functionality'].append("CRITICAL: Dashアプリインスタンス生成失敗")
        
        # レイアウト生成テスト
        try:
            layout = app.layout
            if layout:
                print("   ✓ レイアウト生成: OK")
            else:
                print("   ✗ レイアウト生成: NG - レイアウトが None")
                verification_results['basic_functionality'].append("MAJOR: レイアウト生成失敗")
        except Exception as e:
            print(f"   ✗ レイアウト生成: ERROR - {e}")
            verification_results['basic_functionality'].append(f"CRITICAL: レイアウトエラー - {e}")
        
        # データ読み込み機能テスト
        print("1.2 データ読み込み機能テスト")
        scenario_dir = getattr(dash_app, 'CURRENT_SCENARIO_DIR', None)
        if scenario_dir and scenario_dir.exists():
            # 重要ファイルの存在確認
            critical_files = [
                'shortage_role_summary.parquet',
                'shortage_employment_summary.parquet', 
                'shortage_time.parquet'
            ]
            
            missing_files = []
            for file_name in critical_files:
                if not (scenario_dir / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                print(f"   ✗ 重要データファイル不足: {missing_files}")
                verification_results['data_consistency'].append(f"MAJOR: データファイル不足 - {missing_files}")
            else:
                print("   ✓ 重要データファイル: OK")
        else:
            print("   ! シナリオディレクトリ未設定 - 実データでの検証不可")
            verification_results['user_experience'].append("MINOR: 初回起動時にデータが利用できない")
        
    except Exception as e:
        print(f"   ✗ 基本機能テスト失敗: {e}")
        verification_results['basic_functionality'].append(f"CRITICAL: 基本機能障害 - {e}")
    
    print()
    
    # 2. UI/UXの問題確認
    print("2. UI/UX問題の確認")
    print("-" * 40)
    
    # タブ機能の確認
    try:
        print("2.1 タブ機能確認")
        # ファクトブック統合タブの確認
        fact_book_available = getattr(dash_app, 'FACT_BOOK_INTEGRATION_AVAILABLE', False)
        if fact_book_available:
            print("   ✓ ファクトブックタブ: 利用可能")
        else:
            print("   ! ファクトブックタブ: 利用不可 (機能制限)")
            verification_results['ui_ux_issues'].append("MINOR: ファクトブック分析タブが利用できない")
        
        # ネットワーク分析の確認
        cyto_available = getattr(dash_app, 'CYTOSCAPE_AVAILABLE', False)
        if cyto_available:
            print("   ✓ ネットワーク分析: 利用可能")
        else:
            print("   ! ネットワーク分析: 利用不可")
            verification_results['ui_ux_issues'].append("MAJOR: ネットワーク分析機能が完全に利用できない")
            
    except Exception as e:
        print(f"   ✗ UI機能確認エラー: {e}")
        verification_results['ui_ux_issues'].append(f"MAJOR: UI機能確認不可 - {e}")
    
    # 3. エラーハンドリングの検証
    print()
    print("3. エラーハンドリング検証")
    print("-" * 40)
    
    try:
        print("3.1 データ未読み込み時の動作確認")
        # データが無い状態でのアクセス確認
        try:
            # data_get関数のテスト（存在しないキー）
            if hasattr(dash_app, 'data_get'):
                result = dash_app.data_get('non_existent_data')
                if result is None or (hasattr(result, 'empty') and result.empty):
                    print("   ✓ 存在しないデータ処理: 適切にハンドル")
                else:
                    print("   ? 存在しないデータ処理: 要確認")
            else:
                print("   ! data_get関数が見つからない")
                verification_results['error_handling'].append("MINOR: データ取得関数の確認不可")
                
        except Exception as e:
            print(f"   ✗ エラーハンドリングテスト失敗: {e}")
            verification_results['error_handling'].append(f"MAJOR: エラーハンドリング不備 - {e}")
            
    except Exception as e:
        verification_results['error_handling'].append(f"CRITICAL: エラーハンドリング検証失敗 - {e}")
    
    # 4. パフォーマンス問題の確認
    print()
    print("4. パフォーマンス問題確認")
    print("-" * 40)
    
    startup_time = time.time() - start_time
    print(f"4.1 起動時間: {startup_time:.2f}秒")
    
    if startup_time > 20:
        verification_results['performance_issues'].append(f"MAJOR: 起動時間が遅い ({startup_time:.1f}秒)")
    elif startup_time > 10:
        verification_results['performance_issues'].append(f"MINOR: 起動時間やや遅い ({startup_time:.1f}秒)")
    else:
        print("   ✓ 起動時間: 良好")
    
    # 5. 実際のユーザー操作シミュレーション
    print()
    print("5. ユーザー操作シミュレーション")
    print("-" * 40)
    
    try:
        print("5.1 データアップロード機能確認")
        # ファイルアップロード機能の存在確認
        layout_str = str(app.layout) if app.layout else ""
        if 'dcc.Upload' in layout_str or 'Upload' in layout_str:
            print("   ✓ ファイルアップロード: UI存在")
        else:
            print("   ! ファイルアップロード: UI要確認")
            verification_results['user_experience'].append("MINOR: ファイルアップロードUIの確認が必要")
        
        print("5.2 エラーメッセージの表示確認")
        # エラー表示領域の確認
        if 'alert' in layout_str.lower() or 'error' in layout_str.lower():
            print("   ✓ エラー表示機能: UI存在")
        else:
            print("   ! エラー表示機能: UI要確認")
            verification_results['user_experience'].append("MINOR: エラーメッセージ表示の改善が必要")
            
    except Exception as e:
        print(f"   ✗ ユーザー操作シミュレーション失敗: {e}")
        verification_results['user_experience'].append(f"MAJOR: ユーザー操作テスト失敗 - {e}")
    
    # 6. 結果の総合評価
    print()
    print("=" * 60)
    print("客観的検証結果サマリー")
    print("=" * 60)
    
    total_issues = 0
    critical_issues = 0
    major_issues = 0
    minor_issues = 0
    
    for category, issues in verification_results.items():
        if issues:
            print(f"\n【{category.upper()}】")
            for issue in issues:
                if issue.startswith('CRITICAL'):
                    critical_issues += 1
                    print(f"🔴 {issue}")
                elif issue.startswith('MAJOR'):
                    major_issues += 1
                    print(f"🟡 {issue}")
                elif issue.startswith('MINOR'):
                    minor_issues += 1
                    print(f"🔵 {issue}")
                total_issues += 1
    
    if total_issues == 0:
        print("\n🎉 問題は検出されませんでした")
        quality_score = 100
    else:
        quality_score = max(0, 100 - (critical_issues * 30) - (major_issues * 15) - (minor_issues * 5))
        print(f"\n📊 検出された問題:")
        print(f"   🔴 CRITICAL: {critical_issues}件")
        print(f"   🟡 MAJOR: {major_issues}件") 
        print(f"   🔵 MINOR: {minor_issues}件")
    
    print(f"\n📈 総合品質スコア: {quality_score}/100点")
    
    # 客観的評価
    if quality_score >= 95:
        status = "EXCELLENT - 本番利用可能"
    elif quality_score >= 80:
        status = "GOOD - 軽微な改善で本番利用可能"
    elif quality_score >= 60:
        status = "FAIR - 重要な問題の修正が必要"
    else:
        status = "POOR - 大幅な改善が必要"
    
    print(f"🎯 客観的評価: {status}")
    
    return quality_score >= 80, verification_results

if __name__ == "__main__":
    success, results = comprehensive_verification()
    sys.exit(0 if success else 1)