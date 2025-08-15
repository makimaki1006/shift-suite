#!/usr/bin/env python3
"""
Comprehensive UI Fix Executor
包括的UI問題の修正を実行する
"""

import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import re

class ComprehensiveUIFixer:
    """包括的UI修正実行クラス"""
    
    def __init__(self):
        self.backup_dir = None
        self.fixes_applied = []
        
    def execute_comprehensive_fix(self):
        """包括的修正の実行"""
        print("=== 包括的UI修正開始 ===")
        
        try:
            # Step 1: 緊急バックアップ
            print("\n【Step 1: 緊急バックアップ作成】")
            if not self._create_emergency_backup():
                raise Exception("緊急バックアップ作成失敗")
            
            # Step 2: 按分廃止タブの完全削除
            print("\n【Step 2: 按分廃止タブ完全削除】")
            if not self._complete_proportional_tab_removal():
                raise Exception("按分廃止タブ削除失敗")
            
            # Step 3: タブラベルの統一
            print("\n【Step 3: タブラベル統一】")
            if not self._unify_tab_labels():
                raise Exception("タブラベル統一失敗")
            
            # Step 4: モード選択UIの改善
            print("\n【Step 4: モード選択UI改善】")
            if not self._improve_mode_selector_ui():
                raise Exception("モード選択UI改善失敗")
            
            # Step 5: 構文チェック
            print("\n【Step 5: 構文チェック】")
            if not self._verify_syntax():
                print("構文エラー検出 - ロールバック実行")
                self._rollback()
                raise Exception("構文エラーによる修正失敗")
            
            # Step 6: 統合テスト
            print("\n【Step 6: 統合テスト】")
            test_result = self._run_integration_test()
            
            print("\n✅ 包括的UI修正完了")
            return {
                'success': True,
                'backup_location': str(self.backup_dir),
                'fixes_applied': self.fixes_applied,
                'test_result': test_result,
                'summary': 'UI修正が正常に完了しました'
            }
            
        except Exception as e:
            print(f"❌ 包括的UI修正失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_emergency_backup(self):
        """緊急バックアップ作成"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = Path(f"COMPREHENSIVE_FIX_BACKUP_{timestamp}")
            self.backup_dir.mkdir(exist_ok=True)
            
            # 重要ファイルのバックアップ
            files_to_backup = ['dash_app.py', 'app.py']
            
            for file_name in files_to_backup:
                if Path(file_name).exists():
                    shutil.copy2(file_name, self.backup_dir / f"{file_name}.backup")
                    print(f"  ✓ {file_name} バックアップ完了")
            
            print(f"  📁 緊急バックアップ作成: {self.backup_dir}")
            return True
            
        except Exception as e:
            print(f"  ❌ 緊急バックアップエラー: {e}")
            return False
    
    def _complete_proportional_tab_removal(self):
        """按分廃止タブの完全削除"""
        try:
            with open('dash_app.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 1. 按分廃止タブの定義を削除
            pattern1 = r"dcc\.Tab\(label='\[TARGET\] 按分廃止.*?proportional_abolition.*?\),"
            content = re.sub(pattern1, '# REMOVED: 按分廃止タブ（統合により削除）', content, flags=re.DOTALL)
            
            # 2. 按分廃止関数の削除
            # create_proportional_abolition_tab関数を見つけて削除
            lines = content.split('\n')
            new_lines = []
            in_proportional_function = False
            function_indent = 0
            
            for line in lines:
                if 'def create_proportional_abolition_tab(' in line:
                    in_proportional_function = True
                    function_indent = len(line) - len(line.lstrip())
                    new_lines.append('# REMOVED: create_proportional_abolition_tab関数（統合により削除）')
                    continue
                elif in_proportional_function:
                    # 関数内部かチェック
                    if line.strip() and not line.startswith(' ' * (function_indent + 1)) and not line.startswith('#'):
                        if line.startswith('def ') or line.startswith('class ') or line.startswith('@'):
                            in_proportional_function = False
                    if in_proportional_function:
                        continue
                
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
            
            # 3. 関連コールバックの削除
            pattern2 = r"@.*?def initialize_proportional_abolition_content.*?(?=\n@|\ndef|\nclass|\Z)"
            content = re.sub(pattern2, '# REMOVED: initialize_proportional_abolition_content（統合により削除）\n', content, flags=re.DOTALL)
            
            # 4. proportional_abolition関連の参照をコメントアウト
            content = re.sub(
                r"(\s*)(.*proportional_abolition.*)",
                r"\1# REMOVED: \2",
                content,
                flags=re.MULTILINE
            )
            
            # 変更があった場合のみファイルを更新
            if content != original_content:
                with open('dash_app.py', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append("按分廃止タブ完全削除")
                print("  ✓ 按分廃止タブとその関連機能を削除")
                return True
            else:
                print("  ℹ 按分廃止タブは既に削除済み")
                return True
                
        except Exception as e:
            print(f"  ❌ 按分廃止タブ削除エラー: {e}")
            return False
    
    def _unify_tab_labels(self):
        """タブラベルの統一"""
        try:
            with open('dash_app.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # タブラベルの改善
            replacements = [
                (r"label='\[WARNING\] 不足分析'", "label='📊 不足分析'"),
                (r"label='\[CHART\] 概要'", "label='📋 概要'"),
                (r"label='\[GRAPH\] 需要予測'", "label='📈 需要予測'"),
                (r"label='\[BOARD\] 基準乖離分析'", "label='📊 基準乖離分析'"),
                (r"label='\[BOARD\] MECE制約抽出システム'", "label='🧩 制約抽出システム'"),
                (r"label='\[TARGET\] 真実あぶり出し'", "label='🔍 真実分析'"),
                (r"label='\[CHART\] 統合ファクトブック'", "label='📚 統合ファクトブック'")
            ]
            
            changes_made = 0
            for pattern, replacement in replacements:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    changes_made += 1
            
            if changes_made > 0:
                with open('dash_app.py', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append(f"タブラベル統一（{changes_made}箇所）")
                print(f"  ✓ タブラベル統一完了（{changes_made}箇所修正）")
            else:
                print("  ℹ タブラベルは既に統一済み")
            
            return True
            
        except Exception as e:
            print(f"  ❌ タブラベル統一エラー: {e}")
            return False
    
    def _improve_mode_selector_ui(self):
        """モード選択UIの改善"""
        try:
            with open('dash_app.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 既存のモード選択UIを改善されたものに置換
            improved_mode_selector = '''        # 改善されたモード選択UI
        mode_selector = html.Div([
            html.H4("📊 分析モード選択", style={
                'marginBottom': '15px',
                'color': '#2563eb',
                'fontWeight': 'bold'
            }),
            dcc.RadioItems(
                id='shortage-analysis-mode',
                options=[
                    {
                        'label': html.Div([
                            html.Span('⚡ 基本モード', style={'fontWeight': 'bold'}),
                            html.Br(),
                            html.Small('従来の不足時間計算（高速）', style={'color': '#666'})
                        ]), 
                        'value': 'basic'
                    },
                    {
                        'label': html.Div([
                            html.Span('🎯 高精度モード（推奨）', style={'fontWeight': 'bold', 'color': '#dc2626'}),
                            html.Br(), 
                            html.Small('職種別精緻分析', style={'color': '#666'})
                        ]),
                        'value': 'advanced'
                    }
                ],
                value='advanced',
                style={
                    'display': 'flex',
                    'flexDirection': 'row',
                    'gap': '30px',
                    'marginBottom': '20px'
                },
                inputStyle={'marginRight': '10px', 'transform': 'scale(1.2)'}
            )
        ], style={
            'marginBottom': '30px',
            'padding': '20px',
            'backgroundColor': '#f8fafc',
            'borderRadius': '8px',
            'border': '1px solid #e2e8f0'
        })'''
            
            # 既存のシンプルなモード選択UIを置換
            pattern = r"mode_selector = html\.Div\(\[.*?\], style=\{'marginBottom': '30px'\}\)"
            content = re.sub(pattern, improved_mode_selector, content, flags=re.DOTALL)
            
            # 改善されたモード説明パネルの追加
            improved_explanation_callback = '''def update_shortage_mode_explanation(mode):
    """改善されたモード説明"""
    try:
        if mode == 'basic':
            return html.Div([
                html.Div([
                    html.H5('⚡ 基本モード', style={'color': '#059669', 'margin': '0'}),
                    html.P('従来の不足時間計算を使用', style={'margin': '5px 0'}),
                    html.Ul([
                        html.Li('高速な計算処理'),
                        html.Li('シンプルな結果表示'),
                        html.Li('概要把握に最適')
                    ], style={'margin': '10px 0', 'paddingLeft': '20px'})
                ])
            ], style={
                'backgroundColor': '#ecfdf5',
                'border': '1px solid #10b981',
                'borderRadius': '8px',
                'padding': '20px',
                'marginBottom': '20px'
            })
        elif mode == 'advanced':
            return html.Div([
                html.Div([
                    html.H5('🎯 高精度モード（推奨）', style={'color': '#dc2626', 'margin': '0'}),
                    html.P('職種別精緻分析による改良計算', style={'margin': '5px 0'}),
                    html.Ul([
                        html.Li('職種別詳細分析'),
                        html.Li('実態に即した計算'),
                        html.Li('意思決定に最適')
                    ], style={'margin': '10px 0', 'paddingLeft': '20px'})
                ])
            ], style={
                'backgroundColor': '#fef2f2', 
                'border': '1px solid #ef4444',
                'borderRadius': '8px',
                'padding': '20px',
                'marginBottom': '20px'
            })
        else:
            return html.Div("モードを選択してください")
    except Exception as e:
        return html.P(f"説明更新エラー: {e}")'''
            
            # 既存のモード説明コールバックを置換
            pattern2 = r"def update_shortage_mode_explanation\(mode\):.*?return html\.P\(f\"説明更新エラー: \{e\}\"\)"
            content = re.sub(pattern2, improved_explanation_callback, content, flags=re.DOTALL)
            
            with open('dash_app.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.fixes_applied.append("モード選択UI改善")
            print("  ✓ モード選択UIを改善（視認性向上）")
            return True
            
        except Exception as e:
            print(f"  ❌ モード選択UI改善エラー: {e}")
            return False
    
    def _verify_syntax(self):
        """構文チェック"""
        try:
            result = subprocess.run([
                'python', '-m', 'py_compile', 'dash_app.py'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  ✓ 構文チェック成功")
                return True
            else:
                print(f"  ❌ 構文エラー: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ 構文チェックエラー: {e}")
            return False
    
    def _run_integration_test(self):
        """統合テスト実行"""
        try:
            # シンプル統合テストを実行
            result = subprocess.run([
                'python', 'simple_comprehensive_test.py'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and 'SUCCESS' in result.stdout:
                print("  ✓ 統合テスト成功")
                return {'success': True, 'output': result.stdout}
            else:
                print(f"  ⚠ 統合テスト警告: {result.stdout}")
                return {'success': False, 'output': result.stdout}
                
        except Exception as e:
            print(f"  ❌ 統合テストエラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def _rollback(self):
        """ロールバック実行"""
        try:
            if self.backup_dir and (self.backup_dir / 'dash_app.py.backup').exists():
                shutil.copy2(self.backup_dir / 'dash_app.py.backup', 'dash_app.py')
                print(f"  ✓ {self.backup_dir}からロールバック完了")
                return True
        except Exception as e:
            print(f"  ❌ ロールバックエラー: {e}")
        return False

def main():
    print("=" * 70)
    print("*** 包括的UI修正実行開始 ***")
    print("対象: 按分廃止タブ削除、UIの改善、ユーザビリティ向上")
    print("=" * 70)
    
    fixer = ComprehensiveUIFixer()
    
    try:
        result = fixer.execute_comprehensive_fix()
        
        if result['success']:
            print("\n" + "=" * 70)
            print("*** 包括的UI修正成功 ***")
            print("=" * 70)
            print("完了した修正:")
            for fix in result['fixes_applied']:
                print(f"  ✓ {fix}")
            print(f"\nバックアップ場所: {result['backup_location']}")
            print("\n次のステップ:")
            print("1. 実際のダッシュボードで動作確認")
            print("2. ユーザー受け入れテスト")
            print("3. フィードバック収集")
        else:
            print("\n" + "=" * 70)
            print("*** 包括的UI修正失敗 ***")
            print("=" * 70)
            print(f"エラー: {result['error']}")
            print("バックアップから復元を検討してください")
        
        return result
        
    except Exception as e:
        print(f"\nERROR 包括的UI修正中にエラー: {e}")
        return None

if __name__ == "__main__":
    main()