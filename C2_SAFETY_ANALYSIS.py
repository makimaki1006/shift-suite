"""
C2 ユーザビリティ向上 - 事前安全確認システム
既存機能への影響を徹底調査し、エラーリスクを最小化
"""

import os
import json
import ast
import re
import importlib.util
from datetime import datetime
from typing import Dict, List, Tuple, Any, Set
import traceback

class SystemSafetyAnalyzer:
    """システム安全性分析器"""
    
    def __init__(self):
        self.base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        self.critical_files = [
            "app.py",
            "dash_app.py", 
            "shift_suite/__init__.py",
            "shift_suite/tasks/utils.py",
            "shift_suite/tasks/shortage.py",
            "shift_suite/tasks/fact_extractor_prototype.py",
            "shift_suite/tasks/lightweight_anomaly_detector.py"
        ]
        self.mobile_related_files = []
        self.dependency_map = {}
        self.safety_report = {}
        
    def analyze_system_safety(self):
        """システム安全性の包括分析"""
        print("🔍 C2実装前システム安全性分析開始...")
        
        try:
            # 1. 重要ファイルの存在確認・構文チェック
            print("\n📋 Step 1: 重要ファイル構文チェック...")
            syntax_results = self._check_critical_files_syntax()
            
            # 2. モバイル関連既存実装の調査
            print("\n📱 Step 2: 既存モバイル実装調査...")
            mobile_analysis = self._analyze_existing_mobile_implementation()
            
            # 3. 依存関係マッピング
            print("\n🔗 Step 3: 依存関係マッピング...")
            dependency_analysis = self._analyze_dependencies()
            
            # 4. Phase 2/3.1統合の安全性確認
            print("\n⚡ Step 4: Phase 2/3.1統合安全性...")
            integration_safety = self._verify_phase_integration_safety()
            
            # 5. SLOT_HOURS計算への影響評価
            print("\n🧮 Step 5: SLOT_HOURS計算影響評価...")
            slot_hours_impact = self._assess_slot_hours_impact()
            
            # 6. リスク評価・推奨事項
            print("\n⚠️ Step 6: リスク評価...")
            risk_assessment = self._perform_risk_assessment()
            
            # 総合安全性レポート生成
            self.safety_report = {
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'c2_pre_implementation_safety',
                'system_status': 'analyzed',
                'syntax_check': syntax_results,
                'mobile_implementation': mobile_analysis,
                'dependency_analysis': dependency_analysis,
                'integration_safety': integration_safety,
                'slot_hours_impact': slot_hours_impact,
                'risk_assessment': risk_assessment,
                'safety_score': self._calculate_safety_score(),
                'recommendations': self._generate_safety_recommendations()
            }
            
            return self.safety_report
            
        except Exception as e:
            error_report = {
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'c2_safety_analysis_error',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'status': 'failed'
            }
            return error_report
    
    def _check_critical_files_syntax(self):
        """重要ファイルの構文チェック"""
        results = {}
        
        for file_path in self.critical_files:
            full_path = os.path.join(self.base_path, file_path)
            
            if not os.path.exists(full_path):
                results[file_path] = {
                    'status': 'missing',
                    'error': 'ファイルが存在しません'
                }
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 構文チェック
                ast.parse(content)
                
                # Phase 2/3.1関連の重要関数確認
                critical_patterns = self._get_critical_patterns()
                pattern_matches = {}
                
                for pattern_name, pattern in critical_patterns.items():
                    matches = re.findall(pattern, content)
                    pattern_matches[pattern_name] = len(matches)
                
                results[file_path] = {
                    'status': 'ok',
                    'file_size': len(content),
                    'lines': len(content.split('\\n')),
                    'critical_patterns': pattern_matches,
                    'has_slot_hours': '* SLOT_HOURS' in content or 'SLOT_HOURS =' in content
                }
                
            except SyntaxError as e:
                results[file_path] = {
                    'status': 'syntax_error',
                    'error': str(e),
                    'line': e.lineno,
                    'column': e.offset
                }
            except Exception as e:
                results[file_path] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def _get_critical_patterns(self):
        """重要パターン定義"""
        return {
            'slot_hours_multiplication': r'\\* SLOT_HOURS',
            'slot_hours_definition': r'SLOT_HOURS\\s*=\\s*0\\.5',
            'parsed_slots_count': r'parsed_slots_count',
            'dash_callback': r'@app\\.callback',
            'import_statements': r'^import\\s+\\w+',
            'class_definitions': r'^class\\s+\\w+',
            'function_definitions': r'^def\\s+\\w+'
        }
    
    def _analyze_existing_mobile_implementation(self):
        """既存モバイル実装の分析"""
        mobile_files = [
            "dash_app.py",
            "dash_components/visualization_engine.py",
            "improved_ui_components.py"
        ]
        
        analysis = {}
        
        for file_path in mobile_files:
            full_path = os.path.join(self.base_path, file_path)
            
            if not os.path.exists(full_path):
                analysis[file_path] = {'status': 'not_found'}
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # モバイル関連機能の検出
                mobile_features = {
                    'responsive_breakpoints': len(re.findall(r'mobile.*768|768.*mobile', content, re.IGNORECASE)),
                    'viewport_meta': len(re.findall(r'viewport.*width=device-width', content)),
                    'media_queries': len(re.findall(r'@media.*max-width|@media.*min-width', content)),
                    'mobile_classes': len(re.findall(r'mobile-\\w+', content)),
                    'responsive_functions': len(re.findall(r'responsive.*function|create_responsive', content)),
                    'device_detection': len(re.findall(r'device.*type|viewport.*width', content))
                }
                
                analysis[file_path] = {
                    'status': 'analyzed',
                    'file_size': len(content),
                    'mobile_features': mobile_features,
                    'mobile_readiness': sum(mobile_features.values()) > 0
                }
                
            except Exception as e:
                analysis[file_path] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return analysis
    
    def _analyze_dependencies(self):
        """依存関係分析"""
        analysis = {
            'import_map': {},
            'internal_dependencies': {},
            'external_dependencies': set(),
            'circular_dependencies': []
        }
        
        # 主要ファイルのインポート分析
        for file_path in self.critical_files:
            full_path = os.path.join(self.base_path, file_path)
            
            if not os.path.exists(full_path):
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # インポート文の抽出
                imports = self._extract_imports(content)
                analysis['import_map'][file_path] = imports
                
                # 内部依存関係の特定
                internal_deps = [imp for imp in imports if 'shift_suite' in imp or imp.startswith('.')]
                analysis['internal_dependencies'][file_path] = internal_deps
                
                # 外部依存関係の収集
                external_deps = [imp for imp in imports if not (imp.startswith('.') or 'shift_suite' in imp)]
                analysis['external_dependencies'].update(external_deps)
                
            except Exception as e:
                analysis['import_map'][file_path] = {'error': str(e)}
        
        # 外部依存関係をリストに変換
        analysis['external_dependencies'] = sorted(list(analysis['external_dependencies']))
        
        return analysis
    
    def _extract_imports(self, content):
        """インポート文の抽出"""
        imports = []
        
        # 通常のimport文
        import_pattern = r'^\\s*import\\s+([\\w\\.]+)'
        imports.extend(re.findall(import_pattern, content, re.MULTILINE))
        
        # from import文
        from_pattern = r'^\\s*from\\s+([\\w\\.]+)\\s+import'
        imports.extend(re.findall(from_pattern, content, re.MULTILINE))
        
        return imports
    
    def _verify_phase_integration_safety(self):
        """Phase 2/3.1統合の安全性確認"""
        safety_check = {
            'phase2_integration': {},
            'phase31_integration': {},
            'slot_hours_consistency': {},
            'calculation_chain': {}
        }
        
        # Phase 2統合確認
        phase2_file = os.path.join(self.base_path, "shift_suite/tasks/fact_extractor_prototype.py")
        if os.path.exists(phase2_file):
            with open(phase2_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            safety_check['phase2_integration'] = {
                'file_exists': True,
                'slot_hours_multiplications': len(re.findall(r'\\* SLOT_HOURS', content)),
                'parsed_slots_usage': len(re.findall(r'parsed_slots_count', content)),
                'has_proper_calculation': '* SLOT_HOURS' in content
            }
        
        # Phase 3.1統合確認
        phase31_file = os.path.join(self.base_path, "shift_suite/tasks/lightweight_anomaly_detector.py")
        if os.path.exists(phase31_file):
            with open(phase31_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            safety_check['phase31_integration'] = {
                'file_exists': True,
                'slot_hours_multiplications': len(re.findall(r'\\* SLOT_HOURS', content)),
                'parsed_slots_usage': len(re.findall(r'parsed_slots_count', content)),
                'has_proper_calculation': '* SLOT_HOURS' in content
            }
        
        return safety_check
    
    def _assess_slot_hours_impact(self):
        """SLOT_HOURS計算への影響評価"""
        impact_assessment = {
            'current_implementation': {},
            'potential_risks': [],
            'mobile_specific_risks': [],
            'calculation_consistency': {}
        }
        
        # 現在の実装状況確認
        slot_hours_files = []
        for file_path in self.critical_files:
            full_path = os.path.join(self.base_path, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'SLOT_HOURS' in content:
                    slot_hours_files.append({
                        'file': file_path,
                        'slot_hours_count': content.count('SLOT_HOURS'),
                        'multiplication_count': content.count('* SLOT_HOURS'),
                        'definition_present': 'SLOT_HOURS = 0.5' in content
                    })
        
        impact_assessment['current_implementation'] = {
            'affected_files': len(slot_hours_files),
            'files_detail': slot_hours_files
        }
        
        # 潜在的リスクの評価
        if len(slot_hours_files) > 0:
            impact_assessment['potential_risks'] = [
                "モバイル用UI変更による計算ロジック意図しない変更",
                "レスポンシブ対応でのデータ表示フォーマット変更",
                "JavaScript/CSS変更による数値処理への影響"
            ]
        else:
            impact_assessment['potential_risks'] = ["SLOT_HOURS使用ファイルが検出されませんでした"]
        
        return impact_assessment
    
    def _perform_risk_assessment(self):
        """リスク評価"""
        risks = {
            'critical_risks': [],
            'medium_risks': [],
            'low_risks': [],
            'mitigation_strategies': []
        }
        
        # 構文エラーチェック
        syntax_errors = [f for f, result in self.safety_report.get('syntax_check', {}).items() 
                        if result.get('status') == 'syntax_error']
        
        if syntax_errors:
            risks['critical_risks'].append({
                'type': 'syntax_error',
                'description': f'構文エラーが検出されました: {syntax_errors}',
                'impact': 'システム全体の動作停止',
                'priority': 'immediate'
            })
        
        # 重要ファイル欠損チェック
        missing_files = [f for f, result in self.safety_report.get('syntax_check', {}).items() 
                        if result.get('status') == 'missing']
        
        if missing_files:
            risks['critical_risks'].append({
                'type': 'missing_files',
                'description': f'重要ファイルが欠損: {missing_files}',
                'impact': '機能停止・エラー多発',
                'priority': 'immediate'
            })
        
        # モバイル実装の競合リスク
        risks['medium_risks'].append({
            'type': 'mobile_implementation_conflict',
            'description': '既存モバイル実装との競合可能性',
            'impact': 'UI/UX不整合・表示エラー',
            'priority': 'high'
        })
        
        # 軽減戦略
        risks['mitigation_strategies'] = [
            "段階的実装（小さな変更から開始）",
            "各段階での包括的テスト実行",
            "バックアップ作成・ロールバック準備",
            "既存機能の動作確認テスト必須",
            "Phase 2/3.1計算ロジック保護"
        ]
        
        return risks
    
    def _calculate_safety_score(self):
        """安全性スコア計算"""
        score = 100
        
        # 構文エラーによる減点
        syntax_check = self.safety_report.get('syntax_check', {})
        for file_result in syntax_check.values():
            if file_result.get('status') == 'syntax_error':
                score -= 30
            elif file_result.get('status') == 'missing':
                score -= 20
            elif file_result.get('status') == 'error':
                score -= 10
        
        # 依存関係問題による減点
        dependency_issues = len(self.safety_report.get('dependency_analysis', {}).get('circular_dependencies', []))
        score -= dependency_issues * 5
        
        # リスク評価による減点
        risk_assessment = self.safety_report.get('risk_assessment', {})
        critical_risks = len(risk_assessment.get('critical_risks', []))
        medium_risks = len(risk_assessment.get('medium_risks', []))
        
        score -= critical_risks * 15
        score -= medium_risks * 5
        
        return max(0, score)
    
    def _generate_safety_recommendations(self):
        """安全性推奨事項生成"""
        recommendations = []
        
        # 構文エラーがある場合
        syntax_check = self.safety_report.get('syntax_check', {})
        syntax_errors = [f for f, result in syntax_check.items() if result.get('status') == 'syntax_error']
        
        if syntax_errors:
            recommendations.append({
                'priority': 'critical',
                'action': '構文エラー修正',
                'description': f'以下のファイルの構文エラーを修正: {syntax_errors}',
                'before_c2': True
            })
        
        # 基本推奨事項
        recommendations.extend([
            {
                'priority': 'high',
                'action': 'バックアップ作成',
                'description': 'C2実装前に現在の全システムのバックアップ作成',
                'before_c2': True
            },
            {
                'priority': 'high', 
                'action': '段階的実装',
                'description': '小さな変更から開始し、各段階で動作確認',
                'before_c2': False
            },
            {
                'priority': 'medium',
                'action': '既存モバイル機能調査',
                'description': '現在のレスポンシブ機能との重複・競合チェック',
                'before_c2': True
            },
            {
                'priority': 'medium',
                'action': 'Phase 2/3.1保護',
                'description': 'SLOT_HOURS計算ロジックの保護・検証',
                'before_c2': False
            },
            {
                'priority': 'low',
                'action': '包括テスト計画',
                'description': '全機能の回帰テスト計画策定',
                'before_c2': True
            }
        ])
        
        return recommendations

def main():
    """安全性分析メイン実行"""
    print("🛡️ C2ユーザビリティ向上 - 事前安全性分析開始...")
    
    analyzer = SystemSafetyAnalyzer()
    report = analyzer.analyze_system_safety()
    
    # レポート保存
    report_file = f"C2_safety_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 結果表示
    if 'error' in report:
        print(f"❌ 分析エラー: {report['error']}")
        return report
    
    print(f"\\n📊 分析完了 - 安全性スコア: {report['safety_score']}/100")
    
    # 重要な結果の表示
    syntax_check = report.get('syntax_check', {})
    syntax_ok = sum(1 for result in syntax_check.values() if result.get('status') == 'ok')
    syntax_total = len(syntax_check)
    
    print(f"📋 構文チェック: {syntax_ok}/{syntax_total} ファイル正常")
    
    # リスク概要
    risks = report.get('risk_assessment', {})
    critical_risks = len(risks.get('critical_risks', []))
    medium_risks = len(risks.get('medium_risks', []))
    
    if critical_risks > 0:
        print(f"🚨 重大リスク: {critical_risks}件 - C2実装前に対処必須")
    if medium_risks > 0:
        print(f"⚠️ 中リスク: {medium_risks}件 - 慎重な実装が必要")
    
    # 推奨事項
    recommendations = report.get('recommendations', [])
    before_c2_actions = [r for r in recommendations if r.get('before_c2')]
    
    print(f"\\n📋 C2実装前推奨事項: {len(before_c2_actions)}件")
    for rec in before_c2_actions[:3]:  # 上位3件表示
        print(f"  • {rec['action']}: {rec['description']}")
    
    print(f"\\n📁 詳細レポート: {report_file}")
    
    # 次のステップの推奨
    if report['safety_score'] >= 80:
        print("\\n✅ 安全性良好 - C2実装計画策定に進行可能")
    elif report['safety_score'] >= 60:
        print("\\n⚠️ 注意要 - リスク軽減後にC2実装推奨")
    else:
        print("\\n🚨 危険 - 重大問題解決後にC2実装検討")
    
    return report

if __name__ == "__main__":
    result = main()