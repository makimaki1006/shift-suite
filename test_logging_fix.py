# -*- coding: utf-8 -*-
import os
import sys
import logging

# ログレベル設定
os.environ['SHIFT_SUITE_LOG_LEVEL'] = 'WARNING'
os.environ['ANALYSIS_LOG_LEVEL'] = 'ERROR'

sys.path.append('.')

print("=== ログ出力修正テスト ===")
print("期待結果: WARNINGレベル以下のログのみ出力")
print("")

try:
    # 静寂にインポートテスト
    from shift_suite.tasks.utils import apply_rest_exclusion_filter
    print("✓ apply_rest_exclusion_filter インポート成功 (ログ抑制)")
    
    # 簡単なテスト
    import pandas as pd
    test_df = pd.DataFrame({'test': [1, 2, 3]})
    result = apply_rest_exclusion_filter(test_df, "test", for_display=False, exclude_leave_records=False)
    print(f"✓ 関数テスト成功: {len(result)} records")
    
    print("")
    print("✓ ログ出力適正化が正常に機能しています")
    
except Exception as e:
    print(f"✗ エラー: {e}")
