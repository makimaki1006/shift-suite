#!/usr/bin/env python3
"""
dash_app.pyの基本機能を簡単に確認
"""

import sys
from pathlib import Path

# カレントディレクトリを追加
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def simple_test():
    """簡単な動作確認"""
    
    print("=== dash_app.py 簡単動作確認 ===\n")
    
    try:
        print("1. dash_app.pyインポートテスト...")
        import dash_app
        print("✓ インポート成功")
        
        print("\n2. 重要機能の確認...")
        
        # calculate_role_dynamic_need関数
        if hasattr(dash_app, 'calculate_role_dynamic_need'):
            print("✓ calculate_role_dynamic_need関数: 存在")
        else:
            print("❌ calculate_role_dynamic_need関数: 存在しない")
        
        # DATA_CACHE
        if hasattr(dash_app, 'DATA_CACHE'):
            cache = dash_app.DATA_CACHE
            if hasattr(cache, 'set') and hasattr(cache, 'get'):
                print("✓ ThreadSafeLRUCache: 正常")
                
                # 簡単なキャッシュテスト
                cache.set('test_key', 'test_value')
                if cache.get('test_key') == 'test_value':
                    print("✓ キャッシュ動作: 正常")
                else:
                    print("❌ キャッシュ動作: 異常")
            else:
                print("❌ ThreadSafeLRUCache: メソッド不足")
        else:
            print("❌ DATA_CACHE: 存在しない")
        
        # safe_callback
        if hasattr(dash_app, 'safe_callback'):
            print("✓ safe_callback関数: 存在")
        else:
            print("❌ safe_callback関数: 存在しない")
        
        # アプリケーション本体
        if hasattr(dash_app, 'app'):
            print("✓ Dashアプリケーション: 初期化済み")
        else:
            print("❌ Dashアプリケーション: 初期化されていない")
        
        print("\n3. テストデータディレクトリの確認...")
        test_dir = current_dir / "temp_analysis_results" / "out_p25_based"
        
        if test_dir.exists():
            print(f"✓ テストデータディレクトリ: 存在")
            
            # 重要ファイルの確認
            important_files = [
                'need_per_date_slot.parquet',
                'heat_ALL.parquet', 
                'heat_介護.parquet'
            ]
            
            for filename in important_files:
                file_path = test_dir / filename
                if file_path.exists():
                    size_kb = file_path.stat().st_size / 1024
                    print(f"  ✓ {filename}: {size_kb:.1f}KB")
                else:
                    print(f"  ❌ {filename}: 存在しない")
        else:
            print(f"❌ テストデータディレクトリ: 存在しない ({test_dir})")
        
        print("\n4. 基本的なデータ読み込みテスト...")
        
        # CURRENT_SCENARIO_DIRを設定
        if test_dir.exists():
            dash_app.CURRENT_SCENARIO_DIR = test_dir
            print("✓ シナリオディレクトリ設定完了")
            
            # データ読み込みテスト
            try:
                # キャッシュクリア
                dash_app.DATA_CACHE.clear()
                
                # need_per_date_slotの読み込み
                need_data = dash_app.data_get('need_per_date_slot')
                if hasattr(need_data, 'shape') and len(need_data) > 0:
                    print(f"✓ need_per_date_slot読み込み: {need_data.shape}")
                else:
                    print("❌ need_per_date_slot読み込み: 失敗")
                
                # heat_ALLの読み込み  
                heat_all = dash_app.data_get('heat_all')
                if hasattr(heat_all, 'shape') and len(heat_all) > 0:
                    print(f"✓ heat_all読み込み: {heat_all.shape}")
                else:
                    print("❌ heat_all読み込み: 失敗")
                
            except Exception as e:
                print(f"❌ データ読み込みエラー: {e}")
        
        print("\n=== 確認完了 ===")
        print("\n📋 実際の動作確認手順:")
        print("1. コマンドプロンプトで以下を実行:")
        print(f"   cd \"{current_dir}\"")
        print("   python dash_app.py")
        print("")
        print("2. ブラウザで http://127.0.0.1:8050 にアクセス")
        print("3. temp_analysis_results内のデータをアップロード")
        print("4. '不足分析'タブで職種別ヒートマップを確認")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = simple_test()
    
    if success:
        print("\n🎉 基本機能の確認が完了しました！")
        print("実際の動作確認をお試しください。")
    else:
        print("\n❌ 問題が発見されました。")