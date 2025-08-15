#!/usr/bin/env python3
"""
按分廃止タブ機能テスト
"""

import sys
sys.path.append('.')
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

def test_proportional_tab():
    """按分廃止タブのテスト"""
    
    print("=== 按分廃止タブ機能テスト ===")
    
    try:
        # dash_appから按分廃止タブ作成関数をインポート
        from dash_app import create_proportional_abolition_tab
        
        print("按分廃止タブ作成関数のテスト開始...")
        
        # タブを作成
        tab_content = create_proportional_abolition_tab("test_scenario")
        
        if tab_content:
            print("成功: 按分廃止タブが正常に作成されました")
            print(f"タブコンテンツタイプ: {type(tab_content)}")
            
            # HTML内容の確認
            if hasattr(tab_content, 'children') and tab_content.children:
                print(f"子要素数: {len(tab_content.children)}")
                
                # エラーメッセージが含まれていないことを確認
                tab_str = str(tab_content)
                if "按分廃止分析結果が見つかりません" in tab_str:
                    print("警告: 按分廃止データが見つからないエラーメッセージが表示されています")
                else:
                    print("成功: 按分廃止データが正常に読み込まれました")
            else:
                print("警告: タブコンテンツに子要素がありません")
        else:
            print("エラー: 按分廃止タブの作成に失敗しました")
            
    except Exception as e:
        print(f"エラー: 按分廃止タブのテストに失敗: {e}")
        import traceback
        print("詳細エラー:")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_proportional_tab()