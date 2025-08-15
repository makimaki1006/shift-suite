#!/usr/bin/env python3
"""
統一分析管理システム 全体フロー分析
全体最適の観点から問題を網羅的に検出
"""

import re
from pathlib import Path
from datetime import datetime

class ComprehensiveFlowAnalyzer:
    """全体フローの包括的分析"""
    
    def __init__(self):
        self.issues = []
        self.flow_map = {}
        self.critical_paths = []
        
    def analyze_complete_flow(self):
        """完全なデータフローを分析"""
        print("🔍 統一分析管理システム 全体フロー分析")
        print("=" * 80)
        
        # 1. データ入力フロー
        self.analyze_data_input_flow()
        
        # 2. 分析実行フロー
        self.analyze_analysis_execution_flow()
        
        # 3. 結果保存フロー
        self.analyze_result_storage_flow()
        
        # 4. データ取得フロー
        self.analyze_data_retrieval_flow()
        
        # 5. 出力生成フロー
        self.analyze_output_generation_flow()
        
        # 6. エラー処理フロー
        self.analyze_error_handling_flow()
        
        # 7. 設定伝播フロー
        self.analyze_configuration_propagation_flow()
        
        return self.generate_comprehensive_report()
    
    def analyze_data_input_flow(self):
        """データ入力フローの分析"""
        print("\n1️⃣ データ入力フロー分析")
        
        # app.pyでのファイルアップロード処理を確認
        app_path = Path("app.py")
        if app_path.exists():
            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ファイルアップロード関連の処理を検索
            upload_patterns = [
                r'st\.file_uploader',
                r'uploaded_file',
                r'file_name\s*=',
                r'Path\(.*\)\.stem'
            ]
            
            for pattern in upload_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    print(f"  ✓ {pattern}: {len(matches)}箇所")
            
            # 問題: ファイル名の扱いが一貫していない可能性
            if 'Path(' in content and '.stem' in content:
                stem_count = content.count('.stem')
                path_count = content.count('Path(')
                if stem_count < path_count / 2:
                    self.issues.append({
                        'severity': 'HIGH',
                        'category': 'データ入力',
                        'issue': 'ファイル名の扱いが一貫していない',
                        'detail': f'Path使用: {path_count}回, stem使用: {stem_count}回',
                        'fix': 'すべてのファイル名処理で一貫してPath().stemを使用'
                    })
    
    def analyze_analysis_execution_flow(self):
        """分析実行フローの分析"""
        print("\n2️⃣ 分析実行フロー分析")
        
        # 各分析モジュールの呼び出しを確認
        modules = ['shortage', 'fatigue', 'fairness']
        app_path = Path("app.py")
        
        if app_path.exists():
            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for module in modules:
                print(f"\n  {module}分析:")
                
                # run_taskパターンを探す
                run_pattern = f'run_task.*{module}'
                run_matches = re.findall(run_pattern, content, re.IGNORECASE)
                print(f"    run_task呼び出し: {len(run_matches)}回")
                
                # 統一システムへの登録を探す
                unified_pattern = f'unified_analysis_manager\\.create_{module}_analysis'
                unified_matches = re.findall(unified_pattern, content)
                print(f"    統一システム登録: {len(unified_matches)}回")
                
                # 問題: 分析実行と統一システム登録の不一致
                if len(run_matches) != len(unified_matches):
                    self.issues.append({
                        'severity': 'CRITICAL',
                        'category': '分析実行',
                        'issue': f'{module}分析の実行と統一システム登録の不一致',
                        'detail': f'実行: {len(run_matches)}回, 登録: {len(unified_matches)}回',
                        'fix': '各分析実行後に必ず統一システムへの登録を行う'
                    })
    
    def analyze_result_storage_flow(self):
        """結果保存フローの分析"""
        print("\n3️⃣ 結果保存フロー分析")
        
        # unified_analysis_manager.pyの結果保存処理を確認
        uam_path = Path("shift_suite/tasks/unified_analysis_manager.py")
        if uam_path.exists():
            with open(uam_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # レジストリへの保存処理を確認
            registry_saves = content.count('self.results_registry[')
            print(f"  レジストリ保存: {registry_saves}箇所")
            
            # メモリクリーンアップの確認
            cleanup_exists = 'cleanup_old_results' in content
            print(f"  クリーンアップ機能: {'あり' if cleanup_exists else 'なし'}")
            
            # 問題: クリーンアップが自動実行されていない
            if cleanup_exists:
                app_content = open("app.py", 'r', encoding='utf-8').read()
                if 'cleanup_old_results' not in app_content:
                    self.issues.append({
                        'severity': 'MEDIUM',
                        'category': '結果保存',
                        'issue': 'メモリクリーンアップが自動実行されていない',
                        'detail': 'cleanup_old_resultsメソッドが定義されているが呼ばれていない',
                        'fix': '分析完了後に自動的にクリーンアップを実行'
                    })
    
    def analyze_data_retrieval_flow(self):
        """データ取得フローの分析"""
        print("\n4️⃣ データ取得フロー分析")
        
        # get_ai_compatible_resultsの使用状況を確認
        app_path = Path("app.py")
        if app_path.exists():
            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # get_ai_compatible_results呼び出しを探す
            get_pattern = r'get_ai_compatible_results\((.*?)\)'
            get_matches = re.findall(get_pattern, content)
            
            print(f"  get_ai_compatible_results呼び出し: {len(get_matches)}回")
            for i, match in enumerate(get_matches):
                print(f"    {i+1}: get_ai_compatible_results({match})")
                
                # 問題: ファイル名の形式が一貫していない
                if 'file_name' in match and '.stem' not in content[max(0, content.find(match)-200):content.find(match)]:
                    self.issues.append({
                        'severity': 'HIGH',
                        'category': 'データ取得',
                        'issue': 'ファイル名形式の不一致',
                        'detail': f'get_ai_compatible_results({match})で拡張子付きファイル名を使用',
                        'fix': 'Path(file_name).stemを使用して拡張子を除去'
                    })
    
    def analyze_output_generation_flow(self):
        """出力生成フローの分析"""
        print("\n5️⃣ 出力生成フロー分析")
        
        # AI包括レポート生成の確認
        ai_gen_path = Path("shift_suite/tasks/ai_comprehensive_report_generator.py")
        if ai_gen_path.exists():
            with open(ai_gen_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # データ整合性チェックの確認
            integrity_checks = content.count('data_integrity')
            print(f"  データ整合性チェック: {integrity_checks}箇所")
            
            # デフォルト値の使用確認
            default_patterns = [
                r'get\([\'"].*?[\'"],\s*0\)',
                r'get\([\'"].*?[\'"],\s*0\.0\)',
                r'get\([\'"].*?[\'"],\s*[\'"]N/A[\'"]'
            ]
            
            default_count = 0
            for pattern in default_patterns:
                default_count += len(re.findall(pattern, content))
            
            print(f"  デフォルト値使用: {default_count}箇所")
            
            # 問題: 過度なデフォルト値使用
            if default_count > 50:
                self.issues.append({
                    'severity': 'MEDIUM',
                    'category': '出力生成',
                    'issue': '過度なデフォルト値の使用',
                    'detail': f'{default_count}箇所でデフォルト値を使用',
                    'fix': '実データの有無を確認してから適切な処理を行う'
                })
    
    def analyze_error_handling_flow(self):
        """エラー処理フローの分析"""
        print("\n6️⃣ エラー処理フロー分析")
        
        files_to_check = [
            "app.py",
            "shift_suite/tasks/unified_analysis_manager.py",
            "shift_suite/tasks/shortage.py"
        ]
        
        total_try = 0
        total_except = 0
        bare_except = 0
        
        for file_path in files_to_check:
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_try = content.count('try:')
                file_except = content.count('except')
                file_bare = len(re.findall(r'except:\s*\n', content))
                
                total_try += file_try
                total_except += file_except
                bare_except += file_bare
                
                print(f"  {Path(file_path).name}: try={file_try}, except={file_except}, bare={file_bare}")
        
        # 問題: 汎用的すぎるexcept節
        if bare_except > 0:
            self.issues.append({
                'severity': 'LOW',
                'category': 'エラー処理',
                'issue': '汎用的なexcept節の使用',
                'detail': f'{bare_except}箇所で具体的な例外を指定していない',
                'fix': '具体的な例外タイプを指定（Exception as eなど）'
            })
    
    def analyze_configuration_propagation_flow(self):
        """設定伝播フローの分析"""
        print("\n7️⃣ 設定伝播フロー分析")
        
        # スロット設定の伝播を確認
        slot_usage = {}
        files_to_check = [
            "shift_suite/tasks/shortage.py",
            "shift_suite/tasks/fatigue.py",
            "shift_suite/tasks/heatmap.py"
        ]
        
        for file_path in files_to_check:
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # スロット関連の使用を確認
                slot_minutes = content.count('slot_minutes')
                slot_hours = content.count('slot_hours')
                slot_fixed = content.count('SLOT_HOURS')
                
                slot_usage[Path(file_path).name] = {
                    'slot_minutes': slot_minutes,
                    'slot_hours': slot_hours,
                    'SLOT_HOURS': slot_fixed
                }
                
                print(f"  {Path(file_path).name}: minutes={slot_minutes}, hours={slot_hours}, FIXED={slot_fixed}")
                
                # 問題: 固定値の使用
                if slot_fixed > 0:
                    self.issues.append({
                        'severity': 'HIGH',
                        'category': '設定伝播',
                        'issue': f'{Path(file_path).name}で固定SLOT_HOURS使用',
                        'detail': f'{slot_fixed}箇所で固定値を使用',
                        'fix': '動的なslot_minutesパラメータを使用'
                    })
    
    def generate_comprehensive_report(self):
        """包括的レポートの生成"""
        print("\n" + "=" * 80)
        print("📊 全体フロー分析結果")
        print("=" * 80)
        
        # 重要度別に問題を分類
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        medium_issues = [i for i in self.issues if i['severity'] == 'MEDIUM']
        low_issues = [i for i in self.issues if i['severity'] == 'LOW']
        
        print(f"\n発見された問題: 合計{len(self.issues)}件")
        print(f"  🔴 CRITICAL: {len(critical_issues)}件")
        print(f"  🟠 HIGH: {len(high_issues)}件")
        print(f"  🟡 MEDIUM: {len(medium_issues)}件")
        print(f"  🟢 LOW: {len(low_issues)}件")
        
        # 詳細表示
        for severity, issues in [
            ('CRITICAL', critical_issues),
            ('HIGH', high_issues),
            ('MEDIUM', medium_issues),
            ('LOW', low_issues)
        ]:
            if issues:
                print(f"\n{severity}レベルの問題:")
                for issue in issues:
                    print(f"\n  [{issue['category']}] {issue['issue']}")
                    print(f"    詳細: {issue['detail']}")
                    print(f"    修正: {issue['fix']}")
        
        return self.issues

def main():
    """メイン処理"""
    analyzer = ComprehensiveFlowAnalyzer()
    issues = analyzer.analyze_complete_flow()
    
    # 修正計画の生成
    print("\n" + "=" * 80)
    print("🔧 全体最適化修正計画")
    print("=" * 80)
    
    if not issues:
        print("✅ 重大な問題は発見されませんでした")
    else:
        print("\n優先順位に従って以下の修正を実施してください：")
        
        critical_count = len([i for i in issues if i['severity'] == 'CRITICAL'])
        if critical_count > 0:
            print(f"\n1. 即座に修正すべきCRITICAL問題: {critical_count}件")
            print("   これらは統一システムの基本動作に影響します")
        
        high_count = len([i for i in issues if i['severity'] == 'HIGH'])
        if high_count > 0:
            print(f"\n2. 本日中に修正すべきHIGH問題: {high_count}件")
            print("   これらはデータの正確性に影響します")

if __name__ == "__main__":
    main()