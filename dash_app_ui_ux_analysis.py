#!/usr/bin/env python
"""
dash_app.py UI/UX分析と改善確認

現在のdash_app.pyのUI/UX問題を特定し、改善状況を評価
"""

import re
import ast
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class DashAppUIUXAnalyzer:
    """dash_app.py UI/UX分析クラス"""
    
    def __init__(self, dash_app_path: Path = None):
        self.dash_app_path = dash_app_path or Path("C:/ShiftAnalysis/dash_app.py")
        self.analysis_results = {}
        
    def analyze_ui_ux_issues(self):
        """UI/UX問題の包括的分析"""
        
        print("=== dash_app.py UI/UX分析 ===")
        print("=" * 50)
        
        if not self.dash_app_path.exists():
            print(f"エラー: {self.dash_app_path} が見つかりません")
            return {'error': 'File not found'}
        
        # ファイル読み込み
        with open(self.dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 各種UI/UX分析
        analyses = [
            ("レスポンシブデザイン", self._analyze_responsive_design),
            ("エラーハンドリング", self._analyze_error_handling),
            ("ローディング状態", self._analyze_loading_states),
            ("ユーザビリティ", self._analyze_usability),
            ("アクセシビリティ", self._analyze_accessibility),
            ("パフォーマンス", self._analyze_performance),
            ("データ可視化", self._analyze_data_visualization),
            ("ナビゲーション", self._analyze_navigation)
        ]
        
        for name, analysis_func in analyses:
            print(f"\n[分析] {name}...")
            try:
                result = analysis_func(content)
                self.analysis_results[name] = result
                self._print_analysis_result(name, result)
            except Exception as e:
                self.analysis_results[name] = {'error': str(e)}
                print(f"   [エラー] {e}")
        
        # 総合評価
        overall_result = self._generate_overall_assessment()
        
        return overall_result
    
    def _analyze_responsive_design(self, content: str):
        """レスポンシブデザインの分析"""
        
        issues = []
        improvements = []
        
        # モバイル対応の確認
        mobile_patterns = [
            r'@media.*max-width',
            r'viewport.*width=device-width',
            r'responsive.*True',
            r'mobile.*style',
            r'flex.*direction.*column'
        ]
        
        mobile_support = sum(1 for pattern in mobile_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if mobile_support < 2:
            issues.append("モバイル対応が不十分")
        else:
            improvements.append("基本的なモバイル対応を実装")
        
        # Grid/Flexbox レイアウトの確認
        layout_patterns = [
            r'display.*grid',
            r'display.*flex',
            r'grid-template',
            r'flex-direction'
        ]
        
        modern_layout = sum(1 for pattern in layout_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if modern_layout == 0:
            issues.append("モダンレイアウト（Grid/Flex）が未使用")
        else:
            improvements.append("モダンレイアウトを部分的に使用")
        
        # ブレイクポイントの確認
        breakpoint_patterns = [
            r'sm.*',
            r'md.*',
            r'lg.*',
            r'xl.*'
        ]
        
        breakpoints = sum(1 for pattern in breakpoint_patterns if re.search(pattern, content))
        
        if breakpoints < 2:
            issues.append("ブレイクポイント設定が不十分")
        else:
            improvements.append("複数ブレイクポイントを設定")
        
        return {
            'score': max(0, 100 - len(issues) * 25),
            'issues': issues,
            'improvements': improvements,
            'mobile_support_score': mobile_support,
            'layout_score': modern_layout,
            'breakpoints_score': breakpoints
        }
    
    def _analyze_error_handling(self, content: str):
        """エラーハンドリングの分析"""
        
        issues = []
        improvements = []
        
        # try-except の使用確認
        try_except_count = len(re.findall(r'try:', content))
        
        if try_except_count < 5:
            issues.append("try-except文の使用が少ない")
        else:
            improvements.append(f"try-except文を{try_except_count}箇所で使用")
        
        # エラーメッセージの確認
        error_message_patterns = [
            r'エラー.*:',
            r'Error.*:',
            r'失敗.*:',
            r'問題.*:'
        ]
        
        error_messages = sum(1 for pattern in error_message_patterns if re.search(pattern, content))
        
        if error_messages < 3:
            issues.append("ユーザー向けエラーメッセージが不足")
        else:
            improvements.append("ユーザー向けエラーメッセージを実装")
        
        # ログ出力の確認
        logging_patterns = [
            r'log\.',
            r'logging\.',
            r'print\('
        ]
        
        logging_usage = sum(1 for pattern in logging_patterns if re.search(pattern, content))
        
        if logging_usage < 10:
            issues.append("ログ出力が不十分")
        else:
            improvements.append("適切なログ出力を実装")
        
        # PreventUpdate の使用確認
        prevent_update_count = len(re.findall(r'PreventUpdate', content))
        
        if prevent_update_count < 3:
            issues.append("PreventUpdateの活用が不十分")
        else:
            improvements.append("PreventUpdateを適切に使用")
        
        return {
            'score': max(0, 100 - len(issues) * 20),
            'issues': issues,
            'improvements': improvements,
            'try_except_count': try_except_count,
            'error_messages': error_messages,
            'logging_usage': logging_usage,
            'prevent_update_count': prevent_update_count
        }
    
    def _analyze_loading_states(self, content: str):
        """ローディング状態の分析"""
        
        issues = []
        improvements = []
        
        # ローディングスピナーの確認
        loading_patterns = [
            r'loading.*True',
            r'Spinner',
            r'Loading',
            r'loading.*spinner',
            r'dcc\.Loading'
        ]
        
        loading_indicators = sum(1 for pattern in loading_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if loading_indicators < 3:
            issues.append("ローディング表示が不十分")
        else:
            improvements.append("ローディング表示を実装")
        
        # 非同期処理の確認
        async_patterns = [
            r'callback',
            r'@app\.callback',
            r'async.*def',
            r'await'
        ]
        
        async_usage = sum(1 for pattern in async_patterns if re.search(pattern, content))
        
        if async_usage < 10:
            issues.append("非同期処理の活用が不十分")
        else:
            improvements.append("非同期処理を適切に実装")
        
        # プログレスバーの確認
        progress_patterns = [
            r'Progress',
            r'progress.*bar',
            r'percentage',
            r'進捗'
        ]
        
        progress_indicators = sum(1 for pattern in progress_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if progress_indicators == 0:
            issues.append("プログレス表示がない")
        else:
            improvements.append("プログレス表示を実装")
        
        return {
            'score': max(0, 100 - len(issues) * 30),
            'issues': issues,
            'improvements': improvements,
            'loading_indicators': loading_indicators,
            'async_usage': async_usage,
            'progress_indicators': progress_indicators
        }
    
    def _analyze_usability(self, content: str):
        """ユーザビリティの分析"""
        
        issues = []
        improvements = []
        
        # フォームバリデーションの確認
        validation_patterns = [
            r'valid.*',
            r'invalid.*',
            r'validation',
            r'バリデーション',
            r'validate'
        ]
        
        validation_usage = sum(1 for pattern in validation_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if validation_usage < 5:
            issues.append("フォームバリデーションが不十分")
        else:
            improvements.append("フォームバリデーションを実装")
        
        # ツールチップ・ヘルプの確認
        help_patterns = [
            r'tooltip',
            r'help.*text',
            r'title.*=',
            r'説明',
            r'ヘルプ'
        ]
        
        help_usage = sum(1 for pattern in help_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if help_usage < 5:
            issues.append("ヘルプ・説明が不足")
        else:
            improvements.append("ヘルプ・ツールチップを実装")
        
        # 検索・フィルタ機能の確認
        search_patterns = [
            r'search',
            r'filter',
            r'検索',
            r'フィルタ',
            r'絞り込み'
        ]
        
        search_usage = sum(1 for pattern in search_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if search_usage < 3:
            issues.append("検索・フィルタ機能が不足")
        else:
            improvements.append("検索・フィルタ機能を実装")
        
        # キーボードショートカットの確認
        shortcut_patterns = [
            r'keydown',
            r'keypress',
            r'KeyboardEvent',
            r'shortcut',
            r'ショートカット'
        ]
        
        shortcut_usage = sum(1 for pattern in shortcut_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if shortcut_usage == 0:
            issues.append("キーボードショートカットがない")
        else:
            improvements.append("キーボードショートカットを実装")
        
        return {
            'score': max(0, 100 - len(issues) * 20),
            'issues': issues,
            'improvements': improvements,
            'validation_usage': validation_usage,
            'help_usage': help_usage,
            'search_usage': search_usage,
            'shortcut_usage': shortcut_usage
        }
    
    def _analyze_accessibility(self, content: str):
        """アクセシビリティの分析"""
        
        issues = []
        improvements = []
        
        # ARIA属性の確認
        aria_patterns = [
            r'aria-label',
            r'aria-describedby',
            r'role=',
            r'aria-expanded',
            r'aria-hidden'
        ]
        
        aria_usage = sum(1 for pattern in aria_patterns if re.search(pattern, content))
        
        if aria_usage < 5:
            issues.append("ARIA属性の使用が不十分")
        else:
            improvements.append("ARIA属性を適切に使用")
        
        # セマンティックHTML要素の確認
        semantic_patterns = [
            r'<nav',
            r'<main',
            r'<header',
            r'<footer',
            r'<section',
            r'<article'
        ]
        
        semantic_usage = sum(1 for pattern in semantic_patterns if re.search(pattern, content))
        
        if semantic_usage < 3:
            issues.append("セマンティックHTML要素が不足")
        else:
            improvements.append("セマンティックHTML要素を使用")
        
        # カラーコントラストの考慮
        color_patterns = [
            r'color.*contrast',
            r'コントラスト',
            r'#.*accessibility',
            r'high.*contrast'
        ]
        
        color_consideration = sum(1 for pattern in color_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if color_consideration == 0:
            issues.append("カラーコントラストの考慮が不足")
        else:
            improvements.append("カラーコントラストを考慮")
        
        # フォーカス管理の確認
        focus_patterns = [
            r'focus',
            r'tabindex',
            r'tab.*navigation',
            r'フォーカス'
        ]
        
        focus_management = sum(1 for pattern in focus_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if focus_management < 2:
            issues.append("フォーカス管理が不十分")
        else:
            improvements.append("フォーカス管理を実装")
        
        return {
            'score': max(0, 100 - len(issues) * 25),
            'issues': issues,
            'improvements': improvements,
            'aria_usage': aria_usage,
            'semantic_usage': semantic_usage,
            'color_consideration': color_consideration,
            'focus_management': focus_management
        }
    
    def _analyze_performance(self, content: str):
        """パフォーマンスの分析"""
        
        issues = []
        improvements = []
        
        # キャッシュ機能の確認
        cache_patterns = [
            r'@lru_cache',
            r'cache',
            r'memoize',
            r'キャッシュ',
            r'cached'
        ]
        
        cache_usage = sum(1 for pattern in cache_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if cache_usage < 3:
            issues.append("キャッシュ機能が不十分")
        else:
            improvements.append("キャッシュ機能を実装")
        
        # 仮想化・ページネーションの確認
        virtualization_patterns = [
            r'virtualization',
            r'pagination',
            r'page.*size',
            r'仮想化',
            r'ページング'
        ]
        
        virtualization_usage = sum(1 for pattern in virtualization_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if virtualization_usage == 0:
            issues.append("大量データの最適化が不足")
        else:
            improvements.append("データ表示の最適化を実装")
        
        # 遅延読み込みの確認
        lazy_patterns = [
            r'lazy.*load',
            r'defer',
            r'遅延',
            r'動的.*読み込み'
        ]
        
        lazy_loading = sum(1 for pattern in lazy_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if lazy_loading == 0:
            issues.append("遅延読み込みが未実装")
        else:
            improvements.append("遅延読み込みを実装")
        
        # メモリ管理の確認
        memory_patterns = [
            r'gc\.',
            r'weakref',
            r'del\s+',
            r'memory.*management',
            r'メモリ'
        ]
        
        memory_management = sum(1 for pattern in memory_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if memory_management < 2:
            issues.append("メモリ管理が不十分")
        else:
            improvements.append("メモリ管理を実装")
        
        return {
            'score': max(0, 100 - len(issues) * 25),
            'issues': issues,
            'improvements': improvements,
            'cache_usage': cache_usage,
            'virtualization_usage': virtualization_usage,
            'lazy_loading': lazy_loading,
            'memory_management': memory_management
        }
    
    def _analyze_data_visualization(self, content: str):
        """データ可視化の分析"""
        
        issues = []
        improvements = []
        
        # グラフライブラリの使用確認
        viz_patterns = [
            r'plotly',
            r'go\.',
            r'px\.',
            r'Graph',
            r'chart'
        ]
        
        viz_usage = sum(1 for pattern in viz_patterns if re.search(pattern, content))
        
        if viz_usage < 10:
            issues.append("データ可視化の活用が不十分")
        else:
            improvements.append("多様なデータ可視化を実装")
        
        # インタラクティブ要素の確認
        interactive_patterns = [
            r'hover',
            r'click',
            r'selection',
            r'zoom',
            r'pan',
            r'interactive'
        ]
        
        interactive_usage = sum(1 for pattern in interactive_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if interactive_usage < 5:
            issues.append("インタラクティブ要素が不足")
        else:
            improvements.append("インタラクティブな可視化を実装")
        
        # カスタマイゼーション機能の確認
        custom_patterns = [
            r'config.*=',
            r'layout.*=',
            r'style.*=',
            r'theme',
            r'カスタマイズ'
        ]
        
        customization = sum(1 for pattern in custom_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if customization < 5:
            issues.append("カスタマイゼーション機能が不足")
        else:
            improvements.append("カスタマイゼーション機能を実装")
        
        # データエクスポート機能の確認
        export_patterns = [
            r'download',
            r'export',
            r'save',
            r'csv',
            r'excel',
            r'pdf'
        ]
        
        export_functionality = sum(1 for pattern in export_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if export_functionality < 3:
            issues.append("データエクスポート機能が不足")
        else:
            improvements.append("データエクスポート機能を実装")
        
        return {
            'score': max(0, 100 - len(issues) * 20),
            'issues': issues,
            'improvements': improvements,
            'viz_usage': viz_usage,
            'interactive_usage': interactive_usage,
            'customization': customization,
            'export_functionality': export_functionality
        }
    
    def _analyze_navigation(self, content: str):
        """ナビゲーションの分析"""
        
        issues = []
        improvements = []
        
        # タブ・ページ構造の確認
        navigation_patterns = [
            r'dcc\.Tabs',
            r'tab.*id',
            r'page.*navigation',
            r'nav.*menu',
            r'ナビゲーション'
        ]
        
        navigation_usage = sum(1 for pattern in navigation_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if navigation_usage < 3:
            issues.append("ナビゲーション構造が不十分")
        else:
            improvements.append("適切なナビゲーション構造を実装")
        
        # ブレッドクラム・パンくずリストの確認
        breadcrumb_patterns = [
            r'breadcrumb',
            r'パンくず',
            r'navigation.*trail',
            r'path.*navigation'
        ]
        
        breadcrumb_usage = sum(1 for pattern in breadcrumb_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if breadcrumb_usage == 0:
            issues.append("ブレッドクラムナビゲーションがない")
        else:
            improvements.append("ブレッドクラムナビゲーションを実装")
        
        # サイドバー・メニューの確認
        sidebar_patterns = [
            r'sidebar',
            r'side.*menu',
            r'navigation.*panel',
            r'サイドバー'
        ]
        
        sidebar_usage = sum(1 for pattern in sidebar_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if sidebar_usage == 0:
            issues.append("サイドバーナビゲーションがない")
        else:
            improvements.append("サイドバーナビゲーションを実装")
        
        # 検索機能の確認
        search_nav_patterns = [
            r'search.*box',
            r'search.*input',
            r'global.*search',
            r'検索ボックス'
        ]
        
        search_nav_usage = sum(1 for pattern in search_nav_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if search_nav_usage == 0:
            issues.append("検索機能がない")
        else:
            improvements.append("検索機能を実装")
        
        return {
            'score': max(0, 100 - len(issues) * 25),
            'issues': issues,
            'improvements': improvements,
            'navigation_usage': navigation_usage,
            'breadcrumb_usage': breadcrumb_usage,
            'sidebar_usage': sidebar_usage,
            'search_nav_usage': search_nav_usage
        }
    
    def _print_analysis_result(self, category: str, result: dict):
        """分析結果の表示"""
        
        if 'error' in result:
            print(f"   [エラー] {result['error']}")
            return
        
        score = result.get('score', 0)
        issues = result.get('issues', [])
        improvements = result.get('improvements', [])
        
        print(f"   スコア: {score}/100")
        
        if improvements:
            print(f"   [実装済み] {len(improvements)}項目:")
            for improvement in improvements[:3]:  # 最初の3項目のみ表示
                print(f"     - {improvement}")
            if len(improvements) > 3:
                print(f"     - その他{len(improvements)-3}項目...")
        
        if issues:
            print(f"   [要改善] {len(issues)}項目:")
            for issue in issues[:3]:  # 最初の3項目のみ表示
                print(f"     - {issue}")
            if len(issues) > 3:
                print(f"     - その他{len(issues)-3}項目...")
    
    def _generate_overall_assessment(self):
        """総合評価の生成"""
        
        print("\n" + "=" * 50)
        print("総合UI/UX評価")
        print("=" * 50)
        
        categories = []
        total_score = 0
        total_issues = 0
        total_improvements = 0
        
        for category, result in self.analysis_results.items():
            if 'error' not in result:
                score = result.get('score', 0)
                issues = len(result.get('issues', []))
                improvements = len(result.get('improvements', []))
                
                categories.append({
                    'category': category,
                    'score': score,
                    'issues': issues,
                    'improvements': improvements
                })
                
                total_score += score
                total_issues += issues
                total_improvements += improvements
        
        if categories:
            average_score = total_score / len(categories)
            
            print(f"平均スコア: {average_score:.1f}/100")
            print(f"総改善項目: {total_improvements}")
            print(f"総課題項目: {total_issues}")
            
            print(f"\nカテゴリ別:")
            for cat in categories:
                status = "優秀" if cat['score'] >= 80 else "良好" if cat['score'] >= 60 else "要改善"
                print(f"  {cat['category']}: {cat['score']}/100 ({status})")
            
            # 優先改善項目の特定
            priority_categories = sorted(categories, key=lambda x: x['score'])[:3]
            
            print(f"\n優先改善カテゴリ:")
            for cat in priority_categories:
                print(f"  1. {cat['category']} (スコア: {cat['score']}/100)")
            
            # 総合評価
            if average_score >= 80:
                overall_status = "優秀 - UI/UXは高品質です"
            elif average_score >= 60:
                overall_status = "良好 - 基本的なUI/UXは実装済み"
            elif average_score >= 40:
                overall_status = "要改善 - いくつかの重要な問題があります"
            else:
                overall_status = "大幅改善必要 - UI/UXの全面的な見直しが必要"
            
            print(f"\n総合評価: {overall_status}")
            
            return {
                'overall_score': average_score,
                'total_improvements': total_improvements,
                'total_issues': total_issues,
                'categories': categories,
                'priority_improvements': priority_categories,
                'overall_status': overall_status,
                'analysis_results': self.analysis_results
            }
        
        else:
            print("分析データが不足しています")
            return {'error': 'Insufficient analysis data'}

def main():
    """メイン実行"""
    
    analyzer = DashAppUIUXAnalyzer()
    result = analyzer.analyze_ui_ux_issues()
    
    return result

if __name__ == "__main__":
    ui_ux_result = main()