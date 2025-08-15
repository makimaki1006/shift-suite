#!/usr/bin/env python3
"""
職員個人分析タブの動作確認テスト
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dash_app import create_individual_analysis_tab
import pandas as pd
from unittest.mock import patch, MagicMock

def test_individual_analysis_tab_creation():
    """個別分析タブの作成テスト"""
    
    # テストデータの準備
    test_data = pd.DataFrame({
        'staff': ['職員A', '職員B', '職員C'],
        'role': ['看護師', '医師', '薬剤師'],
        'employment': ['正社員', '正社員', 'パート'],
        'work_hours': [8, 10, 6]
    })
    
    with patch('dash_app.data_get') as mock_data_get:
        mock_data_get.return_value = test_data
        
        # create_individual_analysis_tab関数を呼び出し
        result = create_individual_analysis_tab()
        
        # 結果の確認
        assert result is not None
        print("✓ create_individual_analysis_tab関数が正常に動作しました")
        print(f"✓ 返された要素の型: {type(result)}")
        
        # 含まれるべき要素を確認
        result_str = str(result)
        
        # 必要なIDが含まれているか確認
        assert 'individual-staff-dropdown' in result_str
        assert 'individual-staff-summary' in result_str
        assert 'individual-staff-charts' in result_str
        assert 'synergy-analysis-type' in result_str
        
        print("✓ 必要なUI要素のIDが全て含まれています")
        print("  - individual-staff-dropdown: ✓")
        print("  - individual-staff-summary: ✓")
        print("  - individual-staff-charts: ✓")
        print("  - synergy-analysis-type: ✓")
        
        # スタッフオプションが正しく設定されているか確認
        assert '職員A' in result_str
        assert '職員B' in result_str
        assert '職員C' in result_str
        
        print("✓ スタッフオプションが正しく設定されています")
        
        print("\n=== テスト完了: 個別分析タブは正常に作成されました ===")

if __name__ == "__main__":
    test_individual_analysis_tab_creation()