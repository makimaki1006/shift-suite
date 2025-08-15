#!/usr/bin/env python3
"""
統一分析管理システムの最小限修正パッチ
不足時間0問題を解決する緊急修正
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_files():
    """修正前のファイルをバックアップ"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backup_{timestamp}")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "app.py",
        "shift_suite/tasks/unified_analysis_manager.py"
    ]
    
    for file_path in files_to_backup:
        if Path(file_path).exists():
            dest = backup_dir / Path(file_path).name
            shutil.copy2(file_path, dest)
            print(f"✅ バックアップ: {file_path} → {dest}")
    
    return backup_dir

def apply_minimal_fix():
    """最小限の修正を適用"""
    
    # 1. app.pyの修正箇所を特定
    print("\n🔧 app.pyの修正箇所を確認中...")
    
    app_path = Path("app.py")
    if not app_path.exists():
        print("❌ app.pyが見つかりません")
        return False
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 不足分析実行箇所を探す
    if "run_shortage:" in content:
        print("✅ 不足分析実行箇所を発見")
        
        # 統一システムへの結果登録が欠けているかチェック
        shortage_section_start = content.find("if run_shortage:")
        shortage_section_end = content.find("if run_fatigue:", shortage_section_start)
        
        if shortage_section_end == -1:
            shortage_section_end = len(content)
        
        shortage_section = content[shortage_section_start:shortage_section_end]
        
        if "unified_analysis_manager.create_shortage_analysis" not in shortage_section:
            print("⚠️ 統一システムへの結果登録が欠けています")
            print("  → 修正が必要です")
            
            # 修正箇所の行番号を特定
            lines_before = content[:shortage_section_start].count('\n')
            print(f"  修正箇所: {lines_before + 1}行目付近")
        else:
            print("✅ 統一システムへの結果登録は実装済み")
    
    # 2. 統一分析管理システムのデバッグ
    print("\n🔧 統一分析管理システムのデバッグ情報追加...")
    
    uam_path = Path("shift_suite/tasks/unified_analysis_manager.py")
    if uam_path.exists():
        with open(uam_path, 'r', encoding='utf-8') as f:
            uam_content = f.read()
        
        # get_ai_compatible_resultsメソッドを確認
        if "def get_ai_compatible_results" in uam_content:
            print("✅ get_ai_compatible_resultsメソッドを発見")
            
            # デバッグログが不足しているかチェック
            method_start = uam_content.find("def get_ai_compatible_results")
            method_end = uam_content.find("\n    def ", method_start + 1)
            if method_end == -1:
                method_end = len(uam_content)
            
            method_content = uam_content[method_start:method_end]
            
            if "log.info" not in method_content and "log.debug" not in method_content:
                print("⚠️ デバッグログが不足しています")
                print("  → ログ追加が推奨されます")
    
    return True

def generate_fix_script():
    """修正用スクリプトを生成"""
    fix_script = '''#!/usr/bin/env python3
"""
統一分析管理システム修正スクリプト
生成日時: {timestamp}
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
            log.error(f"統一システムへの結果登録エラー: {{e}}")
    """)

def fix_unified_manager():
    """統一分析管理システムにデバッグ機能を追加"""
    
    print("\\nunified_analysis_manager.pyの修正箇所:")
    print("1. get_ai_compatible_resultsメソッドの先頭に追加:")
    print("""
    log.info(f"[get_ai_compatible_results] 呼び出し: file_pattern={{file_pattern}}")
    log.info(f"[get_ai_compatible_results] レジストリ内のキー数: {{len(self.results_registry)}}")
    
    if not self.results_registry:
        log.warning("[get_ai_compatible_results] レジストリが空です！")
    """)

if __name__ == "__main__":
    print("修正内容を確認してください。")
    print("実際の修正は手動で行うことを推奨します。")
    fix_app_py()
    fix_unified_manager()
'''.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    fix_script_path = Path("apply_unified_system_fix.py")
    with open(fix_script_path, 'w', encoding='utf-8') as f:
        f.write(fix_script)
    
    print(f"\n📝 修正用スクリプトを生成しました: {fix_script_path}")
    return fix_script_path

def main():
    """メイン処理"""
    print("🔧 統一分析管理システム 緊急修正診断")
    print("=" * 60)
    
    # 1. バックアップ
    print("\n1. ファイルのバックアップ")
    backup_dir = backup_files()
    
    # 2. 問題診断
    print("\n2. 問題の診断")
    if apply_minimal_fix():
        print("\n✅ 診断完了")
    
    # 3. 修正スクリプト生成
    print("\n3. 修正スクリプトの生成")
    fix_script = generate_fix_script()
    
    print("\n" + "=" * 60)
    print("診断結果サマリー:")
    print(f"- バックアップ先: {backup_dir}")
    print(f"- 修正スクリプト: {fix_script}")
    print("\n次のステップ:")
    print("1. 生成された修正スクリプトの内容を確認")
    print("2. 手動で慎重に修正を適用")
    print("3. streamlit run app.py で動作確認")

if __name__ == "__main__":
    main()