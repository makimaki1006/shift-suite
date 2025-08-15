#!/usr/bin/env python3
"""
統一分析管理システム修正スクリプト
生成日時: 2025-07-30 09:43:36
"""

import re
from pathlib import Path

def fix_app_py():
    """app.pyに統一システムへの結果登録を追加"""
    
    app_path = Path("app.py")
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 不足分析実行後に統一システムへの登録を追加
    # 注: 実際の修正は手動で行うことを推奨
    
    print("app.pyの修正箇所:")
    print("1. run_shortage実行後に以下を追加:")
    print("""
    # 統一システムへの結果登録
    if UNIFIED_ANALYSIS_AVAILABLE and hasattr(st.session_state, 'unified_analysis_manager'):
        try:
            # 結果ファイルから不足データを読み込む
            shortage_file = scenario_out_dir / "shortage_role_summary.parquet"
            if shortage_file.exists():
                role_df = pd.read_parquet(shortage_file)
                
                # 統一システムに登録
                shortage_result = st.session_state.unified_analysis_manager.create_shortage_analysis(
                    file_name, scenario_key, role_df
                )
                
                log.info(f"統一システムへの不足分析結果登録完了")
        except Exception as e:
            log.error(f"統一システムへの結果登録エラー: {e}")
    """)

def fix_unified_manager():
    """統一分析管理システムにデバッグ機能を追加"""
    
    print("\nunified_analysis_manager.pyの修正箇所:")
    print("1. get_ai_compatible_resultsメソッドの先頭に追加:")
    print("""
    log.info(f"[get_ai_compatible_results] 呼び出し: file_pattern={file_pattern}")
    log.info(f"[get_ai_compatible_results] レジストリ内のキー数: {len(self.results_registry)}")
    
    if not self.results_registry:
        log.warning("[get_ai_compatible_results] レジストリが空です！")
    """)

if __name__ == "__main__":
    print("修正内容を確認してください。")
    print("実際の修正は手動で行うことを推奨します。")
    fix_app_py()
    fix_unified_manager()
