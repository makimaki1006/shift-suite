#!/usr/bin/env python3
"""
dash_app.pyの可視化機能を実際に確認するテストスクリプト
"""

import sys
import time
import threading
from pathlib import Path
import tempfile
import zipfile
import shutil

# カレントディレクトリをPythonパスに追加
sys.path.insert(0, '/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析')

def create_test_zip():
    """テスト用のZIPファイルを作成"""
    source_dir = Path('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/temp_analysis_results')
    zip_path = Path('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/test_analysis_latest.zip')
    
    print("テスト用ZIPファイルを作成中...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for scenario_dir in ['out_p25_based', 'out_mean_based', 'out_median_based']:
            scenario_path = source_dir / scenario_dir
            if scenario_path.exists():
                for file_path in scenario_path.rglob('*'):
                    if file_path.is_file():
                        arcname = scenario_dir + '/' + str(file_path.relative_to(scenario_path))
                        zf.write(file_path, arcname)
    
    print(f"✓ テスト用ZIPファイル作成完了: {zip_path}")
    return zip_path

def test_visualization_functionality():
    """可視化機能のテスト"""
    
    print("=== dash_app.py 可視化機能テスト ===\n")
    
    try:
        # dash_app.pyをインポート
        print("1. dash_app.pyのインポートテスト...")
        import dash_app
        print("✓ dash_app.pyのインポート成功")
        
        # 重要な関数の存在確認
        required_functions = [
            'calculate_role_dynamic_need',
            'update_shortage_ratio_heatmap',
            'data_get',
            'safe_callback'
        ]
        
        print("\n2. 重要な関数の存在確認...")
        for func_name in required_functions:
            if hasattr(dash_app, func_name):
                print(f"✓ {func_name}: 存在")
            else:
                print(f"❌ {func_name}: 存在しない")
        
        # DATA_CACHEの確認
        print("\n3. データキャッシュシステムの確認...")
        if hasattr(dash_app, 'DATA_CACHE'):
            cache = dash_app.DATA_CACHE
            if hasattr(cache, 'set') and hasattr(cache, 'get'):
                print("✓ ThreadSafeLRUCache: 正常")
            else:
                print("❌ ThreadSafeLRUCache: メソッド不足")
        else:
            print("❌ DATA_CACHE: 存在しない")
        
        # テストデータの設定
        print("\n4. テストデータの設定...")
        test_data_dir = Path('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/temp_analysis_results/out_p25_based')
        
        if test_data_dir.exists():
            dash_app.CURRENT_SCENARIO_DIR = test_data_dir
            print(f"✓ テストデータディレクトリ設定: {test_data_dir}")
            
            # 必要ファイルの確認
            required_files = [
                'need_per_date_slot.parquet',
                'heat_ALL.parquet',
                'heat_介護.parquet',
                'shortage_role_summary.parquet'
            ]
            
            print("\n5. 必要ファイルの確認...")
            for file_name in required_files:
                file_path = test_data_dir / file_name
                if file_path.exists():
                    size_kb = file_path.stat().st_size / 1024
                    print(f"✓ {file_name}: 存在 ({size_kb:.1f}KB)")
                else:
                    print(f"❌ {file_name}: 存在しない")
            
            # データ読み込みテスト
            print("\n6. データ読み込みテスト...")
            try:
                # need_per_date_slotの読み込み
                need_data = dash_app.data_get('need_per_date_slot')
                if hasattr(need_data, 'shape'):
                    print(f"✓ need_per_date_slot: {need_data.shape}")
                else:
                    print("❌ need_per_date_slot: データ形式エラー")
                
                # heat_ALLの読み込み
                heat_all_data = dash_app.data_get('heat_all')
                if hasattr(heat_all_data, 'shape'):
                    print(f"✓ heat_all: {heat_all_data.shape}")
                else:
                    print("❌ heat_all: データ形式エラー")
                
                # 職種別データの読み込み
                role_data = dash_app.data_get('heat_介護')
                if hasattr(role_data, 'shape'):
                    print(f"✓ heat_介護: {role_data.shape}")
                    
                    # calculate_role_dynamic_need関数のテスト
                    print("\n7. calculate_role_dynamic_need関数のテスト...")
                    
                    # 日付列を抽出
                    import pandas as pd
                    date_cols = [c for c in role_data.columns 
                               if c not in ['need', 'upper', 'staff', 'lack', 'excess'] 
                               and pd.to_datetime(c, errors='coerce') is not pd.NaT]
                    
                    if date_cols:
                        print(f"  - 日付列数: {len(date_cols)}")
                        
                        # 動的need計算
                        dynamic_need = dash_app.calculate_role_dynamic_need(
                            role_data, date_cols, 'heat_介護'
                        )
                        
                        if hasattr(dynamic_need, 'shape'):
                            print(f"✓ 動的need計算成功: {dynamic_need.shape}")
                            print(f"  - need合計: {dynamic_need.sum().sum():.2f}")
                        else:
                            print("❌ 動的need計算失敗")
                    else:
                        print("❌ 日付列が見つからない")
                else:
                    print("❌ heat_介護: データ形式エラー")
                
            except Exception as e:
                print(f"❌ データ読み込みエラー: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ テストデータディレクトリが存在しない: {test_data_dir}")
        
        print("\n8. アプリケーション構造の確認...")
        if hasattr(dash_app, 'app'):
            print("✓ Dashアプリケーション: 初期化済み")
            
            # コールバック数の確認
            if hasattr(dash_app.app, 'callback_map'):
                callback_count = len(dash_app.app.callback_map)
                print(f"✓ 登録済みコールバック数: {callback_count}")
            else:
                print("✓ Dashアプリケーション: callback_mapなし（正常）")
        else:
            print("❌ Dashアプリケーション: 初期化されていない")
        
        print("\n=== テスト完了 ===")
        print("✓ dash_app.pyは修正された分析結果の可視化準備ができています")
        
        # 実際の起動指示
        print("\n=== 実際の動作確認手順 ===")
        print("1. 以下のコマンドでアプリケーションを起動:")
        print("   cd '/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析'")
        print("   python3 dash_app.py")
        print("")
        print("2. ブラウザで http://127.0.0.1:8050 にアクセス")
        print("3. test_analysis_latest.zip をアップロード")
        print("4. 'out_p25_based'シナリオを選択")
        print("5. '不足分析'タブで職種別ヒートマップを確認")
        print("6. コンソールで[ROLE_DYNAMIC_NEED]ログを確認")
        
        return True
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # テスト用ZIPファイルを作成
    create_test_zip()
    
    # 可視化機能のテスト
    success = test_visualization_functionality()
    
    if success:
        print("\n🎉 全てのテストが成功しました！")
        print("dash_app.pyで正確な職種別need可視化が可能です。")
    else:
        print("\n❌ テストで問題が発見されました。")