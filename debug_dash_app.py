"""
dash_app.pyの問題を特定するためのデバッグスクリプト
"""
import os
import sys
import tempfile
import zipfile
import io
import base64
from pathlib import Path
import pandas as pd
import traceback

# dash_app.pyと同じディレクトリにPATHを追加
sys.path.insert(0, '/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析')

def test_zip_extraction():
    """zipファイルの展開テスト"""
    print("=== ZIPファイル展開テスト ===")
    
    zip_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/analysis_results (26).zip"
    
    if not os.path.exists(zip_path):
        print(f"エラー: ZIPファイルが見つかりません: {zip_path}")
        return None
    
    try:
        # 一時ディレクトリを作成
        temp_dir = tempfile.mkdtemp(prefix="shift_suite_test_")
        temp_path = Path(temp_dir)
        print(f"一時ディレクトリ: {temp_path}")
        
        # ZIPファイルを展開
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_path)
        
        # シナリオディレクトリを検索
        scenarios = [d.name for d in temp_path.iterdir() if d.is_dir() and d.name.startswith('out_')]
        print(f"発見されたシナリオ: {scenarios}")
        
        if scenarios:
            first_scenario = scenarios[0]
            scenario_path = temp_path / first_scenario
            print(f"テスト対象シナリオ: {first_scenario}")
            print(f"シナリオパス: {scenario_path}")
            
            # 重要ファイルの存在確認
            key_files = [
                'pre_aggregated_data.parquet',
                'intermediate_data.parquet',
                'need_per_date_slot.parquet',
                'shortage_time.parquet'
            ]
            
            for key_file in key_files:
                file_path = scenario_path / key_file
                exists = file_path.exists()
                print(f"  {key_file}: {'存在' if exists else '未存在'}")
                if exists:
                    try:
                        size = file_path.stat().st_size
                        print(f"    サイズ: {size} bytes")
                    except Exception as e:
                        print(f"    サイズ取得エラー: {e}")
            
            return scenario_path
        else:
            print("エラー: シナリオディレクトリが見つかりません")
            return None
    
    except Exception as e:
        print(f"ZIP展開エラー: {e}")
        traceback.print_exc()
        return None

def test_data_loading(scenario_path):
    """データ読み込みテスト"""
    print("\n=== データ読み込みテスト ===")
    
    if not scenario_path:
        print("シナリオパスが無効です")
        return
    
    # 重要ファイルをテスト
    test_files = [
        'pre_aggregated_data.parquet',
        'intermediate_data.parquet',
        'need_per_date_slot.parquet',
        'shortage_time.parquet'
    ]
    
    for file_name in test_files:
        file_path = scenario_path / file_name
        print(f"\n--- {file_name} ---")
        
        if not file_path.exists():
            print(f"ファイルが存在しません: {file_path}")
            continue
            
        try:
            # pandas読み込みテスト
            df = pd.read_parquet(file_path)
            print(f"読み込み成功: shape={df.shape}")
            print(f"列名: {list(df.columns)}")
            
            # 空のデータフレームかチェック
            if df.empty:
                print("警告: データフレームが空です")
            else:
                print("データフレームに内容があります")
            
            # メモリ使用量確認
            memory_usage = df.memory_usage(deep=True).sum()
            print(f"メモリ使用量: {memory_usage / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            print(f"読み込みエラー: {e}")
            traceback.print_exc()

def test_dash_app_components():
    """dash_app.pyのコンポーネントをテスト"""
    print("\n=== dash_app.py コンポーネントテスト ===")
    
    try:
        # dash_app.pyのコンポーネントをインポート
        from dash_app import data_get, create_overview_tab, CURRENT_SCENARIO_DIR
        
        print("dash_app.pyからの関数インポート成功")
        
        # CURRENT_SCENARIO_DIRの確認
        print(f"CURRENT_SCENARIO_DIR: {CURRENT_SCENARIO_DIR}")
        
        # data_get関数のテスト
        print("\ndata_get関数テスト:")
        try:
            pre_aggr = data_get('pre_aggregated_data')
            print(f"pre_aggregated_data: {type(pre_aggr)} (empty: {pre_aggr.empty if hasattr(pre_aggr, 'empty') else 'N/A'})")
        except Exception as e:
            print(f"data_get('pre_aggregated_data') エラー: {e}")
            
        try:
            shortage_time = data_get('shortage_time')
            print(f"shortage_time: {type(shortage_time)} (empty: {shortage_time.empty if hasattr(shortage_time, 'empty') else 'N/A'})")
        except Exception as e:
            print(f"data_get('shortage_time') エラー: {e}")
        
    except Exception as e:
        print(f"dash_app.pyインポートエラー: {e}")
        traceback.print_exc()

def simulate_upload_process():
    """アップロード処理をシミュレート"""
    print("\n=== アップロード処理シミュレーション ===")
    
    zip_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/analysis_results (26).zip"
    
    if not os.path.exists(zip_path):
        print(f"ZIPファイルが見つかりません: {zip_path}")
        return
    
    try:
        # ZIPファイルをbase64エンコード（dash_app.pyと同じ方法）
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
        
        encoded_data = base64.b64encode(zip_data).decode()
        contents = f"data:application/zip;base64,{encoded_data}"
        
        print(f"ZIPファイルサイズ: {len(zip_data)} bytes")
        print(f"エンコード後サイズ: {len(encoded_data)} bytes")
        
        # dash_app.pyのprocess_upload関数をシミュレート
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # 一時ディレクトリ作成
        temp_dir = tempfile.mkdtemp(prefix="shift_suite_dash_sim_")
        temp_dir_path = Path(temp_dir)
        
        # ZIP展開
        with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
            zf.extractall(temp_dir_path)
        
        scenarios = [d.name for d in temp_dir_path.iterdir() if d.is_dir() and d.name.startswith('out_')]
        
        print(f"シミュレーション成功: {len(scenarios)} シナリオ発見")
        print(f"シナリオ: {scenarios}")
        
        return True
        
    except Exception as e:
        print(f"シミュレーションエラー: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("dash_app.py デバッグ開始\n")
    
    # 1. ZIPファイル展開テスト
    scenario_path = test_zip_extraction()
    
    # 2. データ読み込みテスト
    test_data_loading(scenario_path)
    
    # 3. アップロード処理シミュレーション
    simulate_upload_process()
    
    # 4. dash_app.pyコンポーネントテスト
    test_dash_app_components()
    
    print("\nデバッグ完了")