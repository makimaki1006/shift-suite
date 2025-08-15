#!/usr/bin/env python3
"""
コーディング品質と技術的問題の特定
- 統一システムを継続前提で技術的問題を分析
- パフォーマンス、保守性、コード品質の観点から評価
- 具体的な改善提案
"""

import ast
import re
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class CodingQualityAnalyzer:
    """コーディング品質分析器"""
    
    def __init__(self):
        self.analysis_result = {}
        self.issues = {
            'performance': [],
            'maintainability': [],
            'code_quality': [],
            'security': [],
            'scalability': []
        }
    
    def analyze_unified_system_code_quality(self):
        """統一システムのコード品質分析"""
        print("=== 統一システム コード品質分析 ===")
        
        unified_file = Path('unified_data_pipeline_architecture.py')
        if not unified_file.exists():
            print("統一システムファイルが存在しません")
            return
        
        with open(unified_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 基本メトリクス
        lines = content.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        
        basic_metrics = {
            'total_lines': len(lines),
            'code_lines': len(non_empty_lines),
            'classes': content.count('class '),
            'functions': content.count('def '),
            'imports': len([line for line in lines if line.strip().startswith(('import ', 'from '))]),
            'comments': len([line for line in lines if line.strip().startswith('#')]),
            'docstrings': content.count('"""') + content.count("'''")
        }
        
        print("基本メトリクス:")
        for metric, value in basic_metrics.items():
            print(f"  {metric}: {value}")
        
        # 2. 複雑度分析
        complexity_issues = self._analyze_complexity(content)
        
        # 3. パフォーマンス問題
        performance_issues = self._analyze_performance_issues(content)
        
        # 4. 保守性問題
        maintainability_issues = self._analyze_maintainability_issues(content)
        
        self.analysis_result['unified_system'] = {
            'basic_metrics': basic_metrics,
            'complexity_issues': complexity_issues,
            'performance_issues': performance_issues,
            'maintainability_issues': maintainability_issues
        }
        
        return basic_metrics
    
    def _analyze_complexity(self, content: str) -> List[Dict]:
        """複雑度問題分析"""
        print("\n複雑度分析:")
        
        issues = []
        lines = content.splitlines()
        
        # 長い関数の検出
        current_function = None
        function_start = 0
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('def '):
                if current_function:
                    length = i - function_start
                    if length > 50:  # 50行を超える関数
                        issues.append({
                            'type': 'long_function',
                            'function': current_function,
                            'line': function_start,
                            'length': length,
                            'severity': 'medium' if length < 100 else 'high'
                        })
                        print(f"  長い関数: {current_function} ({length}行, {function_start}行目)")
                
                current_function = line.strip().split('(')[0].replace('def ', '')
                function_start = i
        
        # 最後の関数もチェック
        if current_function:
            length = len(lines) - function_start
            if length > 50:
                issues.append({
                    'type': 'long_function',
                    'function': current_function,
                    'line': function_start,
                    'length': length,
                    'severity': 'medium' if length < 100 else 'high'
                })
                print(f"  長い関数: {current_function} ({length}行, {function_start}行目)")
        
        # ネストの深さ
        max_nesting = 0
        current_nesting = 0
        deep_nesting_lines = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if any(stripped.startswith(keyword) for keyword in ['if ', 'for ', 'while ', 'with ', 'try:']):
                current_nesting += 1
                if current_nesting > 4:  # 4レベルを超えるネスト
                    deep_nesting_lines.append((i, current_nesting, stripped[:50]))
                max_nesting = max(max_nesting, current_nesting)
            elif any(stripped.startswith(keyword) for keyword in ['def ', 'class ']):
                current_nesting = 1
            elif stripped == '' or not stripped.startswith(' '):
                current_nesting = 0
        
        if deep_nesting_lines:
            print(f"  深いネスト (最大{max_nesting}レベル):")
            for line_no, nesting, code in deep_nesting_lines:
                issues.append({
                    'type': 'deep_nesting',
                    'line': line_no,
                    'nesting_level': nesting,
                    'code': code,
                    'severity': 'medium' if nesting < 6 else 'high'
                })
                print(f"    {line_no}行目: {nesting}レベル - {code}")
        
        self.issues['code_quality'].extend(issues)
        return issues
    
    def _analyze_performance_issues(self, content: str) -> List[Dict]:
        """パフォーマンス問題分析"""
        print("\nパフォーマンス問題分析:")
        
        issues = []
        lines = content.splitlines()
        
        # 潜在的なパフォーマンス問題パターン
        performance_patterns = {
            r'\.rglob\(.*\)': {
                'issue': '再帰的ディレクトリスキャン',
                'impact': 'ファイル数に比例して処理時間増加',
                'severity': 'high'
            },
            r'for.*in.*\.rglob': {
                'issue': '再帰的スキャンでのループ処理',
                'impact': '大量ファイル時のパフォーマンス劣化',
                'severity': 'high'
            },
            r'hashlib\..*\(': {
                'issue': 'ファイルハッシュ計算',
                'impact': 'ファイルサイズに比例した処理時間',
                'severity': 'medium'
            },
            r'\.stat\(\)': {
                'issue': 'ファイル統計情報取得',
                'impact': 'ファイルシステムI/O待機',
                'severity': 'low'
            },
            r'\.exists\(\)': {
                'issue': 'ファイル存在確認',
                'impact': 'ファイルシステムアクセス',
                'severity': 'low'
            },
            r'\.read\(\).*\.read\(\)': {
                'issue': '複数回のファイル読み込み',
                'impact': '不要なI/O処理',
                'severity': 'medium'
            }
        }
        
        for i, line in enumerate(lines, 1):
            for pattern, issue_info in performance_patterns.items():
                if re.search(pattern, line):
                    issues.append({
                        'type': 'performance',
                        'pattern': pattern,
                        'line': i,
                        'code': line.strip(),
                        'issue': issue_info['issue'],
                        'impact': issue_info['impact'],
                        'severity': issue_info['severity']
                    })
                    print(f"  {i}行目: {issue_info['issue']} - {issue_info['impact']}")
        
        # 990ファイルスキャンの影響分析
        rglob_count = content.count('.rglob(')
        if rglob_count > 0:
            estimated_files = 990  # 先ほどの分析結果
            estimated_operations = estimated_files * 6  # ファイル毎の処理数
            
            issues.append({
                'type': 'performance_impact',
                'issue': f'{rglob_count}箇所での全ファイルスキャン',
                'estimated_files': estimated_files,
                'estimated_operations': estimated_operations,
                'severity': 'critical',
                'improvement_potential': f'特定ファイル検索に変更で{estimated_operations-2}回の処理削減可能'
            })
            
            print(f"  全体影響: {estimated_files}ファイル × 6処理 = {estimated_operations}回の処理")
            print(f"  改善ポテンシャル: 特定ファイル検索で{estimated_operations-2}回削減可能")
        
        self.issues['performance'].extend(issues)
        return issues
    
    def _analyze_maintainability_issues(self, content: str) -> List[Dict]:
        """保守性問題分析"""
        print("\n保守性問題分析:")
        
        issues = []
        lines = content.splitlines()
        
        # 保守性問題パターン
        maintainability_patterns = {
            'hardcoded_values': {
                'patterns': [r'\d{4}', r'3600', r'\.parquet', r'\.csv'],
                'description': 'ハードコーディング値',
                'severity': 'medium'
            },
            'magic_numbers': {
                'patterns': [r'\b[0-9]{2,}\b'],  # 2桁以上の数値
                'description': 'マジックナンバー',
                'severity': 'low'
            },
            'complex_conditions': {
                'patterns': [r'if.*and.*and', r'if.*or.*or'],
                'description': '複雑な条件分岐',
                'severity': 'medium'
            }
        }
        
        for issue_type, config in maintainability_patterns.items():
            for i, line in enumerate(lines, 1):
                for pattern in config['patterns']:
                    if re.search(pattern, line) and not line.strip().startswith('#'):
                        issues.append({
                            'type': issue_type,
                            'line': i,
                            'code': line.strip(),
                            'description': config['description'],
                            'severity': config['severity'],
                            'pattern': pattern
                        })
                        print(f"  {i}行目: {config['description']} - {line.strip()[:50]}...")
        
        # クラス・メソッドの責任範囲分析
        class_methods = {}
        current_class = None
        
        for line in lines:
            if line.startswith('class '):
                current_class = line.split('class ')[1].split('(')[0].split(':')[0]
                class_methods[current_class] = []
            elif line.strip().startswith('def ') and current_class:
                method_name = line.strip().split('def ')[1].split('(')[0]
                class_methods[current_class].append(method_name)
        
        print(f"\nクラス責任範囲分析:")
        for class_name, methods in class_methods.items():
            print(f"  {class_name}: {len(methods)}メソッド")
            if len(methods) > 15:  # 15メソッドを超える場合
                issues.append({
                    'type': 'large_class',
                    'class': class_name,
                    'method_count': len(methods),
                    'severity': 'medium',
                    'suggestion': 'クラスの分割を検討'
                })
                print(f"    → 大きすぎるクラス: 分割を検討")
        
        self.issues['maintainability'].extend(issues)
        return issues
    
    def analyze_dash_app_integration_issues(self):
        """dash_app.py統合部分の問題分析"""
        print("\n=== dash_app.py統合問題分析 ===")
        
        dash_app_file = Path('dash_app.py')
        if not dash_app_file.exists():
            print("dash_app.pyが存在しません")
            return
        
        with open(dash_app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        integration_issues = []
        
        # 統一システム関連コードの検出と分析
        unified_patterns = [
            'UNIFIED_SYSTEM_AVAILABLE',
            'UNIFIED_REGISTRY',
            'enhanced_data_get',
            'unified_data_pipeline_architecture'
        ]
        
        print("統一システム統合箇所:")
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            for pattern in unified_patterns:
                if pattern in line:
                    print(f"  {i}行目: {pattern} - {line.strip()[:60]}...")
                    
                    # 問題のパターンチェック
                    if 'try:' in line or 'except' in line:
                        integration_issues.append({
                            'type': 'error_handling',
                            'line': i,
                            'code': line.strip(),
                            'issue': '例外処理での統一システム依存',
                            'severity': 'medium'
                        })
                    
                    if '# 🚀' in line or 'log.info' in line:
                        integration_issues.append({
                            'type': 'logging_overhead',
                            'line': i,
                            'code': line.strip(),
                            'issue': '統一システム用の追加ログ処理',
                            'severity': 'low'
                        })
        
        # フォールバック機構の複雑性
        fallback_count = content.count('フォールバック')
        if fallback_count > 0:
            print(f"\nフォールバック機構: {fallback_count}箇所")
            integration_issues.append({
                'type': 'fallback_complexity',
                'count': fallback_count,
                'issue': '統一システム・従来システム間の複雑なフォールバック',
                'severity': 'medium',
                'impact': 'デバッグ困難、実行パス予測困難'
            })
        
        self.analysis_result['dash_app_integration'] = integration_issues
        self.issues['maintainability'].extend(integration_issues)
        
        return integration_issues
    
    def identify_specific_technical_debt(self):
        """具体的な技術的負債の特定"""
        print("\n=== 具体的な技術的負債 ===")
        
        technical_debt = {
            'architecture_debt': [
                {
                    'debt': 'データアクセスの二重化',
                    'description': '統一システム + 従来システムの並存',
                    'impact': 'コードの複雑化、テスト困難',
                    'cost': 'high'
                },
                {
                    'debt': '990ファイルスキャンのオーバーヘッド',
                    'description': '按分2ファイルのために全ファイルスキャン',
                    'impact': '起動時間増加、メモリ使用量増加',
                    'cost': 'high'
                }
            ],
            'code_debt': [
                {
                    'debt': 'ハードコーディングされた設定値',
                    'description': 'キャッシュTTL、ファイル拡張子等',
                    'impact': '設定変更が困難、テスト困難',
                    'cost': 'medium'
                },
                {
                    'debt': '複雑な条件分岐',
                    'description': '統一システム利用可否の判定ロジック',
                    'impact': 'バグ混入リスク、理解困難',
                    'cost': 'medium'
                }
            ],
            'performance_debt': [
                {
                    'debt': 'I/O集約的な初期化処理',
                    'description': '全ファイルのハッシュ計算・メタデータ生成',
                    'impact': '初期化時間の大幅増加',
                    'cost': 'high'
                },
                {
                    'debt': '不要なファイルアクセス',
                    'description': '按分以外の988ファイルへの無駄アクセス',
                    'impact': 'リソース浪費、パフォーマンス劣化',
                    'cost': 'high'
                }
            ]
        }
        
        for debt_category, debts in technical_debt.items():
            print(f"\n{debt_category.replace('_', ' ').title()}:")
            for debt in debts:
                print(f"  【{debt['debt']}】")
                print(f"    内容: {debt['description']}")
                print(f"    影響: {debt['impact']}")
                print(f"    コスト: {debt['cost']}")
        
        self.analysis_result['technical_debt'] = technical_debt
        
        return technical_debt
    
    def propose_coding_improvements(self):
        """コーディング改善提案"""
        print("\n=== コーディング改善提案 ===")
        
        improvements = {
            'immediate_fixes': [
                {
                    'title': '条件付きファイルスキャン',
                    'description': '特定データタイプのみスキャンする機能追加',
                    'implementation': '_scan_available_data(data_types=None) メソッド修正',
                    'effort': 'low',
                    'impact': 'high',
                    'code_example': '''
def _scan_available_data(self, target_types: Optional[List[DataType]] = None):
    # 按分廃止のみの場合は2ファイルのみチェック
    if target_types == [DataType.PROPORTIONAL_ABOLITION_ROLE, DataType.PROPORTIONAL_ABOLITION_ORG]:
        specific_files = [
            "proportional_abolition_role_summary.parquet",
            "proportional_abolition_organization_summary.parquet"
        ]
        for file_name in specific_files:
            file_path = Path(".") / file_name
            if file_path.exists():
                self._register_file(file_path)
        return
    
    # 従来の全ファイルスキャン
    # ... existing code
'''
                },
                {
                    'title': 'ハードコード値の設定ファイル化',
                    'description': 'キャッシュ設定、拡張子等を外部設定に',
                    'implementation': 'config.json読み込み機能追加',
                    'effort': 'medium',
                    'impact': 'medium',
                    'code_example': '''
# unified_config.json
{
    "cache_ttl_seconds": 3600,
    "allowed_extensions": [".parquet", ".csv", ".json"],
    "scan_mode": "selective",  // "full" or "selective"
    "max_file_size_mb": 100
}
'''
                }
            ],
            'medium_term_improvements': [
                {
                    'title': '段階的初期化',
                    'description': '必要な時に必要なデータのみロード',
                    'implementation': 'lazy loading pattern実装',
                    'effort': 'medium',
                    'impact': 'high'
                },
                {
                    'title': 'キャッシュ戦略最適化',
                    'description': '使用頻度に基づく適応的キャッシュ',
                    'implementation': 'LFU + TTLハイブリッド',
                    'effort': 'high',
                    'impact': 'medium'
                }
            ],
            'long_term_improvements': [
                {
                    'title': 'プラグイン アーキテクチャ',
                    'description': '分析タイプ別の独立モジュール化',
                    'implementation': 'データローダーのプラグイン化',
                    'effort': 'high',
                    'impact': 'high'
                }
            ]
        }
        
        for improvement_category, items in improvements.items():
            print(f"\n{improvement_category.replace('_', ' ').title()}:")
            for item in items:
                print(f"  【{item['title']}】")
                print(f"    説明: {item['description']}")
                print(f"    工数: {item['effort']}, 効果: {item['impact']}")
                if 'code_example' in item:
                    print(f"    実装例: {item['code_example'][:100]}...")
        
        self.analysis_result['improvements'] = improvements
        
        return improvements
    
    def generate_priority_action_plan(self):
        """優先アクションプラン生成"""
        print("\n=== 優先アクションプラン ===")
        
        # 問題の重要度計算
        high_priority_issues = [
            issue for category_issues in self.issues.values()
            for issue in category_issues
            if issue.get('severity') in ['high', 'critical']
        ]
        
        action_plan = {
            'phase1_immediate': {
                'duration': '1-2時間',
                'actions': [
                    '条件付きファイルスキャン実装（990→2ファイル化）',
                    'パフォーマンス測定追加（初期化時間計測）',
                    '不要ログ出力削減'
                ],
                'expected_improvement': '初期化時間80-90%短縮'
            },
            'phase2_optimization': {
                'duration': '4-6時間',
                'actions': [
                    'ハードコード値設定ファイル化',
                    'エラーハンドリング簡素化',
                    'キャッシュ戦略見直し'
                ],
                'expected_improvement': '保守性向上、設定変更容易化'
            },
            'phase3_architecture': {
                'duration': '1-2日',
                'actions': [
                    'データローダーのモジュール化',
                    'プラグイン機構検討',
                    '総合テスト強化'
                ],
                'expected_improvement': '長期保守性向上、拡張性確保'
            }
        }
        
        print("優先度別アクションプラン:")
        for phase, plan in action_plan.items():
            print(f"\n{phase.replace('_', ' ').title()} ({plan['duration']}):")
            for action in plan['actions']:
                print(f"  - {action}")
            print(f"  期待効果: {plan['expected_improvement']}")
        
        print(f"\n高優先問題数: {len(high_priority_issues)}件")
        print("最重要課題: 990ファイルスキャン → 按分2ファイル特定スキャン")
        
        self.analysis_result['action_plan'] = action_plan
        
        return action_plan
    
    def execute_analysis(self):
        """分析実行"""
        print("=" * 70)
        print("*** コーディング品質・技術的問題分析 ***")
        print("前提: 統一システム継続、包括的分析システムとして発展")
        print("=" * 70)
        
        self.analyze_unified_system_code_quality()
        self.analyze_dash_app_integration_issues()
        self.identify_specific_technical_debt()
        self.propose_coding_improvements()
        self.generate_priority_action_plan()
        
        # 結果保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = Path(f"coding_quality_technical_issues_{timestamp}.json")
        
        self.analysis_result['metadata'] = {
            'timestamp': timestamp,
            'analysis_scope': '統一システム継続前提でのコーディング問題',
            'key_finding': '990ファイルスキャンが最大の技術的問題'
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n分析レポート保存: {report_path}")
        
        return self.analysis_result

def main():
    analyzer = CodingQualityAnalyzer()
    result = analyzer.execute_analysis()
    
    print("\n" + "=" * 70)
    print("*** 分析完了 ***")
    print("統一システムを継続しつつ、技術的問題を特定しました。")
    print("最重要課題: 990ファイルスキャン → 特定ファイルスキャンへの最適化")
    print("=" * 70)

if __name__ == "__main__":
    main()