"""
修正された dash_app.py をテストするスクリプト
"""
import sys
sys.path.insert(0, r'C:\Users\fuji1\OneDrive\デスクトップ\シフト分析')

def test_initialization():
    """初期化テスト"""
    print("=== 初期化テスト ===")
    
    try:
        # dash_app.pyをインポート
        import dash_app
        
        # CURRENT_SCENARIO_DIRの確認
        print(f"CURRENT_SCENARIO_DIR: {dash_app.CURRENT_SCENARIO_DIR}")
        
        if dash_app.CURRENT_SCENARIO_DIR:
            print(f"シナリオディレクトリが設定されています: {dash_app.CURRENT_SCENARIO_DIR}")
            print(f"ディレクトリの存在確認: {dash_app.CURRENT_SCENARIO_DIR.exists()}")
            
            # 重要ファイルの存在確認
            key_files = [
                'pre_aggregated_data.parquet',
                'shortage_time.parquet',
                'need_per_date_slot.parquet'
            ]
            
            print("重要ファイルの確認:")
            for file_name in key_files:
                file_path = dash_app.CURRENT_SCENARIO_DIR / file_name
                exists = file_path.exists()
                print(f"  {file_name}: {'OK' if exists else 'Missing'}")
        else:
            print("エラー: CURRENT_SCENARIO_DIRが設定されていません")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def test_data_loading():
    """データ読み込みテスト"""
    print("\n=== データ読み込みテスト ===")
    
    try:
        import dash_app
        
        # 重要なデータの読み込みテスト
        test_keys = [
            'pre_aggregated_data',
            'shortage_time',
            'need_per_date_slot'
        ]
        
        for key in test_keys:
            print(f"\n--- {key} ---")
            try:
                data = dash_app.data_get(key)
                print(f"タイプ: {type(data)}")
                
                if hasattr(data, 'shape'):
                    print(f"形状: {data.shape}")
                    print(f"空のデータ: {data.empty}")
                    if not data.empty:
                        print(f"列名: {list(data.columns)[:5]}")  # 最初の5列のみ表示
                else:
                    print(f"値: {data}")
                    
            except Exception as e:
                print(f"エラー: {e}")
                
    except Exception as e:
        print(f"全般エラー: {e}")
        import traceback
        traceback.print_exc()

def test_overview_tab():
    """概要タブのテスト"""
    print("\n=== 概要タブテスト ===")
    
    try:
        import dash_app
        
        # create_overview_tab関数をテスト
        print("create_overview_tab関数を実行中...")
        overview_content = dash_app.create_overview_tab()
        
        print(f"概要タブの内容タイプ: {type(overview_content)}")
        print("概要タブの作成に成功しました")
        
    except Exception as e:
        print(f"概要タブエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("dash_app.py 修正テスト開始\n")
    
    # 1. 初期化テスト
    test_initialization()
    
    # 2. データ読み込みテスト
    test_data_loading()
    
    # 3. 概要タブテスト
    test_overview_tab()
    
    print("\n修正テスト完了")