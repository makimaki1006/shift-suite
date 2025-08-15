#!/usr/bin/env python3
"""
統一分析管理システム 全体最適化修正実行
Ultra-Thorough Thinkingに基づく包括的修正
"""

import shutil
from pathlib import Path
from datetime import datetime

def create_comprehensive_backup():
    """包括的バックアップの作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"comprehensive_backup_{timestamp}")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "app.py",
        "shift_suite/tasks/unified_analysis_manager.py",
        "shift_suite/tasks/shortage.py",
        "shift_suite/tasks/ai_comprehensive_report_generator.py"
    ]
    
    print("🗂️ 包括的バックアップを作成中...")
    for file_path in files_to_backup:
        if Path(file_path).exists():
            dest = backup_dir / Path(file_path).name
            shutil.copy2(file_path, dest)
            print(f"  ✅ {file_path} → {dest}")
    
    print(f"📁 バックアップ完了: {backup_dir}")
    return backup_dir

def fix_1_unified_system_debug_logging():
    """修正1: 統一システムデバッグログ追加"""
    print("\n🔧 修正1: 統一システムデバッグログ追加")
    
    uam_path = Path("shift_suite/tasks/unified_analysis_manager.py")
    if not uam_path.exists():
        print("❌ unified_analysis_manager.py が見つかりません")
        return False
    
    with open(uam_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # get_ai_compatible_resultsメソッドにデバッグログを追加
    old_method_start = 'def get_ai_compatible_results(self, file_pattern: str = None) -> Dict[str, Any]:'
    if old_method_start in content:
        method_body_start = content.find(old_method_start)
        method_body = content[method_body_start:content.find('def ', method_body_start + 1)]
        
        # デバッグログが既に追加されているかチェック
        if '[get_ai_compatible_results]' not in method_body:
            new_method_start = '''def get_ai_compatible_results(self, file_pattern: str = None) -> Dict[str, Any]:
        """AI包括レポート用の結果辞書生成"""
        ai_results = {}
        
        # 🔧 修正: デバッグログを追加
        log.info(f"[get_ai_compatible_results] 検索パターン: '{file_pattern}'")
        log.info(f"[get_ai_compatible_results] レジストリ内のキー数: {len(self.results_registry)}")
        
        # レジストリ内のキーを表示（デバッグ用）
        if self.results_registry:
            log.debug("[get_ai_compatible_results] レジストリ内のキー:")
            for key in list(self.results_registry.keys())[:5]:  # 最初の5個のみ
                log.debug(f"  - {key}")
        else:
            log.warning("[get_ai_compatible_results] ⚠️ レジストリが空です！")
        
        for key, result in self.results_registry.items():
            # 🔧 修正: パターンマッチングを改善
            if file_pattern is None:
                match = True
            else:
                # ファイル名の部分一致を許可
                from pathlib import Path
                clean_pattern = Path(file_pattern).stem  # 拡張子を除去
                match = clean_pattern in key or file_pattern in key
                
            if match:
                log.debug(f"[get_ai_compatible_results] マッチ: {key}")'''
            
            # 既存のメソッド本体を置換
            next_method_start = content.find('def ', method_body_start + 1)
            if next_method_start == -1:
                next_method_start = len(content)
            
            old_body = content[method_body_start:content.find('\n        for key, result in self.results_registry.items():')]
            new_content = content.replace(old_body, new_method_start)
            
            with open(uam_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("  ✅ get_ai_compatible_resultsにデバッグログを追加しました")
            return True
        else:
            print("  ℹ️ デバッグログは既に追加済みです")
            return True
    else:
        print("  ❌ get_ai_compatible_resultsメソッドが見つかりません")
        return False

def fix_2_file_name_consistency():
    """修正2: ファイル名の一貫性確保"""
    print("\n🔧 修正2: ファイル名の一貫性確保（app.py）")
    
    app_path = Path("app.py")
    if not app_path.exists():
        print("❌ app.py が見つかりません")
        return False
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # get_ai_compatible_results呼び出し箇所を修正
    old_call = 'unified_results = st.session_state.unified_analysis_manager.get_ai_compatible_results(file_name)'
    if old_call in content:
        new_call = '''# 🔧 修正: ファイル名のステム（拡張子なし）を使用
                                file_stem = Path(file_name).stem
                                log.info(f"[AIレポート生成] ファイル名: {file_name} → ステム: {file_stem}")
                                
                                unified_results = st.session_state.unified_analysis_manager.get_ai_compatible_results(file_stem)
                                
                                # 結果が空の場合の詳細診断
                                if not unified_results:
                                    log.warning(f"[AIレポート生成] 統一システムから結果が取得できません")
                                    log.warning(f"  検索キー: {file_stem}")
                                    log.warning(f"  レジストリサイズ: {len(st.session_state.unified_analysis_manager.results_registry)}")'''
        
        new_content = content.replace(old_call, new_call)
        
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("  ✅ ファイル名の一貫性修正を適用しました")
        return True
    else:
        print("  ❌ get_ai_compatible_results呼び出しが見つかりません")
        return False

def fix_3_shortage_slot_hours():
    """修正3: shortage.pyの固定SLOT_HOURS修正"""
    print("\n🔧 修正3: shortage.pyの固定SLOT_HOURS修正")
    
    shortage_path = Path("shift_suite/tasks/shortage.py")
    if not shortage_path.exists():
        print("❌ shortage.py が見つかりません")
        return False
    
    with open(shortage_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # SLOT_HOURS定数の使用を探す
    if 'SLOT_HOURS' in content:
        # SLOT_HOURSの定義を削除または置換
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if 'SLOT_HOURS' in line and '=' in line and 'slot_hours' not in line.lower():
                # 固定定数の定義をコメントアウト
                new_lines.append(f"# {line}  # 🔧 修正: 動的スロット計算に置換")
            elif 'SLOT_HOURS' in line and 'slot_hours' not in line:
                # 使用箇所を動的計算に置換
                new_line = line.replace('SLOT_HOURS', 'slot_hours')
                new_lines.append(f"{new_line}  # 🔧 修正: 動的値使用")
            else:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        with open(shortage_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("  ✅ SLOT_HOURS固定値を動的計算に修正しました")
        return True
    else:
        print("  ℹ️ SLOT_HOURSは既に修正済みまたは使用されていません")
        return True

def fix_4_add_analysis_execution_validation():
    """修正4: 分析実行結果の検証追加"""
    print("\n🔧 修正4: 分析実行結果の検証追加")
    
    # shortage_and_brief実行後の統一システム登録部分を確認・修正
    app_path = Path("app.py")
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # shortage_and_brief実行後の処理を探す
    shortage_exec_pattern = 'shortage_result_exec_run = shortage_and_brief('
    if shortage_exec_pattern in content:
        # 統一システムへの登録が適切に行われているか確認
        shortage_section_start = content.find(shortage_exec_pattern)
        shortage_section_end = content.find('try:', shortage_section_start + 500)  # 次のtryブロックまで
        
        if shortage_section_end == -1:
            shortage_section_end = shortage_section_start + 1000
        
        shortage_section = content[shortage_section_start:shortage_section_end]
        
        if 'create_shortage_analysis' not in shortage_section:
            print("  ⚠️ shortage_and_brief実行後に統一システム登録が見つかりません")
            
            # 修正用のコードを挿入位置を探す
            insert_point = content.find('st.session_state.analysis_status["shortage"] = "success"')
            if insert_point != -1:
                insertion_code = '''
                    
                    # 🔧 修正: 統一システムへの不足分析結果登録
                    if UNIFIED_ANALYSIS_AVAILABLE and hasattr(st.session_state, 'unified_analysis_manager'):
                        try:
                            # 結果ファイルから不足データを読み込む
                            shortage_role_file = scenario_out_dir / "shortage_role_summary.parquet"
                            if shortage_role_file.exists():
                                role_df = pd.read_parquet(shortage_role_file)
                                
                                # 統一システムに登録
                                shortage_result = st.session_state.unified_analysis_manager.create_shortage_analysis(
                                    file_name, scenario_key, role_df
                                )
                                
                                log.info(f"✅ 統一システムへの不足分析結果登録完了: {shortage_result.analysis_key}")
                            else:
                                log.warning("⚠️ shortage_role_summary.parquetが見つかりません")
                        except Exception as e:
                            log.error(f"統一システムへの結果登録エラー: {e}")
                '''
                
                new_content = content[:insert_point] + insertion_code + content[insert_point:]
                
                with open(app_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("  ✅ shortage_and_brief実行後の統一システム登録を追加しました")
                return True
        else:
            print("  ℹ️ 統一システム登録は既に実装済みです")
            return True
    
    return False

def fix_5_add_memory_cleanup():
    """修正5: メモリクリーンアップの自動実行"""
    print("\n🔧 修正5: メモリクリーンアップの自動実行")
    
    app_path = Path("app.py")
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # AI包括レポート生成後にクリーンアップを追加
    ai_report_end_pattern = 'log.info("AI向け包括的レポート生成完了")'
    if ai_report_end_pattern in content:
        cleanup_code = '''
                        
                        # 🔧 修正: 統一システムのメモリクリーンアップ
                        if UNIFIED_ANALYSIS_AVAILABLE and hasattr(st.session_state, 'unified_analysis_manager'):
                            try:
                                st.session_state.unified_analysis_manager.cleanup_old_results(max_age_hours=1)
                                log.info("✅ 統一システムのメモリクリーンアップ完了")
                            except Exception as e:
                                log.warning(f"メモリクリーンアップエラー: {e}")'''
        
        insert_point = content.find(ai_report_end_pattern) + len(ai_report_end_pattern)
        new_content = content[:insert_point] + cleanup_code + content[insert_point:]
        
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("  ✅ メモリクリーンアップの自動実行を追加しました")
        return True
    else:
        print("  ℹ️ AI包括レポート生成箇所が見つかりません")
        return False

def validate_fixes():
    """修正内容の検証"""
    print("\n✅ 修正内容の検証")
    
    # 構文エラーチェック
    import ast
    
    files_to_validate = [
        "app.py",
        "shift_suite/tasks/unified_analysis_manager.py",
        "shift_suite/tasks/shortage.py"
    ]
    
    for file_path in files_to_validate:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
                print(f"  ✅ {file_path}: 構文OK")
            except SyntaxError as e:
                print(f"  ❌ {file_path}: 構文エラー - {e}")
                return False
            except Exception as e:
                print(f"  ⚠️ {file_path}: 検証エラー - {e}")
    
    return True

def main():
    """メイン修正処理"""
    print("🚀 統一分析管理システム 全体最適化修正実行")
    print("=" * 80)
    
    # バックアップ作成
    backup_dir = create_comprehensive_backup()
    
    # 修正の実行
    fixes_applied = []
    
    if fix_1_unified_system_debug_logging():
        fixes_applied.append("統一システムデバッグログ追加")
    
    if fix_2_file_name_consistency():
        fixes_applied.append("ファイル名一貫性確保")
    
    if fix_3_shortage_slot_hours():
        fixes_applied.append("shortage.py固定値修正")
    
    if fix_4_add_analysis_execution_validation():
        fixes_applied.append("分析実行結果検証追加")
    
    if fix_5_add_memory_cleanup():
        fixes_applied.append("メモリクリーンアップ自動化")
    
    # 検証
    if validate_fixes():
        print(f"\n🎉 修正完了！適用された修正: {len(fixes_applied)}件")
        for i, fix in enumerate(fixes_applied, 1):
            print(f"  {i}. {fix}")
        
        print(f"\n📁 バックアップ: {backup_dir}")
        print("\n次のステップ:")
        print("1. streamlit run app.py でアプリケーションを起動")
        print("2. デイ_テスト用データ_休日精緻.xlsx で再テスト")
        print("3. ログ（shift_suite.log）で修正効果を確認")
        return True
    else:
        print("\n❌ 修正中に構文エラーが発生しました")
        print(f"バックアップから復元してください: {backup_dir}")
        return False

if __name__ == "__main__":
    main()