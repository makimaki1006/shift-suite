#!/usr/bin/env python3
"""
Phase 0: 詳細調査
既存のdash_app.py不足分析タブと按分廃止タブの完全分析
"""

import re
import ast
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

class DetailedCodeInvestigation:
    """詳細コード調査クラス"""
    
    def __init__(self):
        self.investigation_results = {}
        self.code_analysis = {}
        self.data_compatibility = {}
        self.dependency_mapping = {}
        
    def conduct_comprehensive_investigation(self):
        """包括的調査実行"""
        print("=== Phase 0: 詳細調査開始 ===")
        
        investigation = {
            'existing_code_analysis': {},
            'data_format_analysis': {},
            'dependency_mapping': {},
            'callback_analysis': {},
            'risk_assessment': {},
            'compatibility_matrix': {}
        }
        
        # 1. 既存コード詳細分析
        print("\n【既存コード詳細分析】")
        code_analysis = self._analyze_existing_code()
        investigation['existing_code_analysis'] = code_analysis
        
        # 2. データフォーマット分析
        print("\n【データフォーマット分析】")
        data_analysis = self._analyze_data_formats()
        investigation['data_format_analysis'] = data_analysis
        
        # 3. 依存関係マッピング
        print("\n【依存関係マッピング】")
        dependency_mapping = self._map_dependencies()
        investigation['dependency_mapping'] = dependency_mapping
        
        # 4. コールバック分析
        print("\n【コールバック分析】")
        callback_analysis = self._analyze_callbacks()
        investigation['callback_analysis'] = callback_analysis
        
        # 5. リスク評価
        print("\n【リスク評価】")
        risk_assessment = self._assess_integration_risks()
        investigation['risk_assessment'] = risk_assessment
        
        # 6. 互換性マトリックス
        print("\n【互換性マトリックス】")
        compatibility_matrix = self._create_compatibility_matrix()
        investigation['compatibility_matrix'] = compatibility_matrix
        
        self.investigation_results = investigation
        return investigation
    
    def _analyze_existing_code(self):
        """既存コード詳細分析"""
        print("既存のタブ実装を詳細分析中...")
        
        code_analysis = {
            'shortage_tab_analysis': {},
            'proportional_tab_analysis': {},
            'shared_components': {},
            'code_complexity': {}
        }
        
        try:
            # dash_app.py読み込み
            dash_app_path = Path('dash_app.py')
            with open(dash_app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            total_lines = len(lines)
            
            # 不足分析タブの分析
            shortage_tab_start = self._find_function_boundaries(content, 'create_shortage_tab')
            if shortage_tab_start:
                code_analysis['shortage_tab_analysis'] = {
                    'function_name': 'create_shortage_tab',
                    'start_line': shortage_tab_start['start'],
                    'end_line': shortage_tab_start['end'],
                    'line_count': shortage_tab_start['end'] - shortage_tab_start['start'],
                    'complexity_score': self._calculate_complexity(shortage_tab_start['code']),
                    'data_dependencies': self._extract_data_dependencies(shortage_tab_start['code']),
                    'ui_components': self._extract_ui_components(shortage_tab_start['code'])
                }
                print(f"  不足分析タブ: {shortage_tab_start['end'] - shortage_tab_start['start']}行")
            
            # 按分廃止タブの分析
            prop_tab_start = self._find_function_boundaries(content, 'create_proportional_abolition_tab')
            if prop_tab_start:
                code_analysis['proportional_tab_analysis'] = {
                    'function_name': 'create_proportional_abolition_tab',
                    'start_line': prop_tab_start['start'],
                    'end_line': prop_tab_start['end'],
                    'line_count': prop_tab_start['end'] - prop_tab_start['start'],
                    'complexity_score': self._calculate_complexity(prop_tab_start['code']),
                    'data_dependencies': self._extract_data_dependencies(prop_tab_start['code']),
                    'ui_components': self._extract_ui_components(prop_tab_start['code'])
                }
                print(f"  按分廃止タブ: {prop_tab_start['end'] - prop_tab_start['start']}行")
            
            # 共通コンポーネント抽出
            code_analysis['shared_components'] = self._identify_shared_components(
                shortage_tab_start['code'] if shortage_tab_start else '',
                prop_tab_start['code'] if prop_tab_start else ''
            )
            
            # 全体複雑度
            code_analysis['code_complexity'] = {
                'total_lines': total_lines,
                'function_count': content.count('def '),
                'callback_count': content.count('@app.callback'),
                'import_count': content.count('import '),
                'complexity_rating': 'very_high' if total_lines > 5000 else 'high'
            }
            
            print(f"  dash_app.py総行数: {total_lines}")
            print(f"  コールバック数: {content.count('@app.callback')}")
            
        except Exception as e:
            print(f"  ERROR: コード分析失敗 - {e}")
            code_analysis['analysis_error'] = str(e)
        
        return code_analysis
    
    def _find_function_boundaries(self, content: str, function_name: str) -> Optional[Dict]:
        """関数の境界を特定"""
        lines = content.split('\n')
        
        # 関数開始行を見つける
        start_line = None
        for i, line in enumerate(lines):
            if f'def {function_name}(' in line:
                start_line = i + 1  # 1ベースの行番号
                break
        
        if start_line is None:
            return None
        
        # 関数終了行を見つける（次の同レベル関数またはファイル終端）
        indent_level = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
        end_line = len(lines)
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            if line.strip() and not line.startswith(' ' * (indent_level + 1)) and not line.startswith('#'):
                if line.startswith('def ') or line.startswith('class ') or line.startswith('@'):
                    end_line = i
                    break
        
        function_code = '\n'.join(lines[start_line - 1:end_line])
        
        return {
            'start': start_line,
            'end': end_line,
            'code': function_code
        }
    
    def _calculate_complexity(self, code: str) -> Dict:
        """コードの複雑度計算"""
        if_count = code.count('if ')
        for_count = code.count('for ')
        while_count = code.count('while ')
        try_count = code.count('try:')
        function_calls = len(re.findall(r'\w+\(', code))
        
        complexity_score = if_count + for_count * 2 + while_count * 2 + try_count + function_calls * 0.1
        
        return {
            'if_statements': if_count,
            'for_loops': for_count,
            'while_loops': while_count,
            'try_blocks': try_count,
            'function_calls': function_calls,
            'complexity_score': complexity_score,
            'complexity_level': 'high' if complexity_score > 50 else 'medium' if complexity_score > 20 else 'low'
        }
    
    def _extract_data_dependencies(self, code: str) -> List[str]:
        """データ依存関係抽出"""
        dependencies = []
        
        # .parquetファイル参照
        parquet_files = re.findall(r"['\"]([^'\"]*\.parquet)['\"]", code)
        dependencies.extend(parquet_files)
        
        # データ取得関数呼び出し
        data_functions = re.findall(r'(data_get|enhanced_data_get|safe_read_excel)\s*\([^)]*[\'"]([^\'"]*)[\'"]', code)
        dependencies.extend([match[1] for match in data_functions])
        
        # UNIFIED_SYSTEM使用
        if 'UNIFIED_SYSTEM' in code:
            dependencies.append('unified_data_pipeline')
        
        return list(set(dependencies))
    
    def _extract_ui_components(self, code: str) -> List[str]:
        """UIコンポーネント抽出"""
        components = []
        
        # Dashコンポーネント
        dash_components = re.findall(r'(html\.\w+|dcc\.\w+|dash_table\.\w+)', code)
        components.extend(dash_components)
        
        # Plotlyコンポーネント
        plotly_components = re.findall(r'(go\.\w+|px\.\w+)', code)
        components.extend(plotly_components)
        
        return list(set(components))
    
    def _identify_shared_components(self, shortage_code: str, prop_code: str) -> Dict:
        """共通コンポーネント特定"""
        if not shortage_code or not prop_code:
            return {}
        
        shortage_components = set(self._extract_ui_components(shortage_code))
        prop_components = set(self._extract_ui_components(prop_code))
        
        shared_ui = shortage_components.intersection(prop_components)
        
        shortage_data = set(self._extract_data_dependencies(shortage_code))
        prop_data = set(self._extract_data_dependencies(prop_code))
        
        shared_data = shortage_data.intersection(prop_data)
        
        return {
            'shared_ui_components': list(shared_ui),
            'shared_data_dependencies': list(shared_data),
            'ui_reuse_potential': len(shared_ui) / len(shortage_components.union(prop_components)) if shortage_components.union(prop_components) else 0,
            'data_overlap': len(shared_data) > 0
        }
    
    def _analyze_data_formats(self):
        """データフォーマット分析"""
        print("データフォーマットを分析中...")
        
        data_analysis = {
            'shortage_data_format': {},
            'proportional_data_format': {},
            'format_compatibility': {},
            'conversion_requirements': {}
        }
        
        try:
            # 不足分析データの確認
            shortage_files = [
                'shortage_time.parquet',
                'shortage_role_summary.parquet',
                'shortage_employment_summary.parquet'
            ]
            
            for file_name in shortage_files:
                file_path = Path(file_name)
                if file_path.exists():
                    try:
                        df = pd.read_parquet(file_path)
                        data_analysis['shortage_data_format'][file_name] = {
                            'exists': True,
                            'shape': df.shape,
                            'columns': df.columns.tolist(),
                            'dtypes': df.dtypes.astype(str).to_dict(),
                            'sample_data': df.head(2).to_dict() if len(df) > 0 else {}
                        }
                        print(f"  {file_name}: {df.shape}")
                    except Exception as e:
                        data_analysis['shortage_data_format'][file_name] = {
                            'exists': True,
                            'error': str(e)
                        }
                else:
                    data_analysis['shortage_data_format'][file_name] = {
                        'exists': False
                    }
            
            # 按分廃止データの確認
            prop_files = [
                'proportional_abolition_role_summary.parquet',
                'proportional_abolition_organization_summary.parquet'
            ]
            
            for file_name in prop_files:
                file_path = Path(file_name)
                if file_path.exists():
                    try:
                        df = pd.read_parquet(file_path)
                        data_analysis['proportional_data_format'][file_name] = {
                            'exists': True,
                            'shape': df.shape,
                            'columns': df.columns.tolist(),
                            'dtypes': df.dtypes.astype(str).to_dict(),
                            'sample_data': df.head(2).to_dict() if len(df) > 0 else {}
                        }
                        print(f"  {file_name}: {df.shape}")
                    except Exception as e:
                        data_analysis['proportional_data_format'][file_name] = {
                            'exists': True,
                            'error': str(e)
                        }
                else:
                    data_analysis['proportional_data_format'][file_name] = {
                        'exists': False
                    }
            
            # フォーマット互換性分析
            data_analysis['format_compatibility'] = self._analyze_format_compatibility(
                data_analysis['shortage_data_format'],
                data_analysis['proportional_data_format']
            )
            
        except Exception as e:
            print(f"  ERROR: データフォーマット分析失敗 - {e}")
            data_analysis['analysis_error'] = str(e)
        
        return data_analysis
    
    def _analyze_format_compatibility(self, shortage_format, prop_format):
        """フォーマット互換性分析"""
        compatibility = {
            'column_overlap': {},
            'data_type_compatibility': {},
            'structural_differences': {},
            'integration_complexity': 'unknown'
        }
        
        # 存在するファイルから列情報を収集
        shortage_columns = set()
        prop_columns = set()
        
        for file_info in shortage_format.values():
            if file_info.get('exists') and 'columns' in file_info:
                shortage_columns.update(file_info['columns'])
        
        for file_info in prop_format.values():
            if file_info.get('exists') and 'columns' in file_info:
                prop_columns.update(file_info['columns'])
        
        if shortage_columns and prop_columns:
            common_columns = shortage_columns.intersection(prop_columns)
            compatibility['column_overlap'] = {
                'common_columns': list(common_columns),
                'shortage_only': list(shortage_columns - prop_columns),
                'proportional_only': list(prop_columns - shortage_columns),
                'overlap_ratio': len(common_columns) / len(shortage_columns.union(prop_columns))
            }
            
            # 統合複雑度の評価
            if compatibility['column_overlap']['overlap_ratio'] > 0.7:
                compatibility['integration_complexity'] = 'low'
            elif compatibility['column_overlap']['overlap_ratio'] > 0.3:
                compatibility['integration_complexity'] = 'medium'
            else:
                compatibility['integration_complexity'] = 'high'
        
        return compatibility
    
    def _map_dependencies(self):
        """依存関係マッピング"""
        print("依存関係をマッピング中...")
        
        dependency_map = {
            'import_dependencies': {},
            'function_dependencies': {},
            'data_dependencies': {},
            'callback_dependencies': {}
        }
        
        try:
            dash_app_path = Path('dash_app.py')
            with open(dash_app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # インポート依存関係
            imports = re.findall(r'from\s+([^\s]+)\s+import|import\s+([^\s\n]+)', content)
            import_modules = []
            for match in imports:
                import_modules.extend([m for m in match if m])
            
            dependency_map['import_dependencies'] = {
                'total_imports': len(import_modules),
                'unique_modules': list(set(import_modules)),
                'shift_suite_imports': [m for m in import_modules if 'shift_suite' in m],
                'external_dependencies': [m for m in import_modules if not ('shift_suite' in m or m in ['os', 'sys', 'json', 'pathlib'])]
            }
            
            # 関数依存関係（shortage/proportional関連）
            shortage_functions = re.findall(r'(shortage_\w+|create_shortage_\w+)', content)
            prop_functions = re.findall(r'(proportional_\w+|create_proportional_\w+)', content)
            
            dependency_map['function_dependencies'] = {
                'shortage_related_functions': list(set(shortage_functions)),
                'proportional_related_functions': list(set(prop_functions)),
                'shared_functions': list(set(shortage_functions).intersection(set(prop_functions)))
            }
            
            print(f"  インポート数: {len(import_modules)}")
            print(f"  shift_suite依存: {len([m for m in import_modules if 'shift_suite' in m])}")
            
        except Exception as e:
            print(f"  ERROR: 依存関係マッピング失敗 - {e}")
            dependency_map['mapping_error'] = str(e)
        
        return dependency_map
    
    def _analyze_callbacks(self):
        """コールバック分析"""
        print("コールバック構造を分析中...")
        
        callback_analysis = {
            'shortage_tab_callbacks': {},
            'proportional_tab_callbacks': {},
            'callback_conflicts': {},
            'integration_impact': {}
        }
        
        try:
            dash_app_path = Path('dash_app.py')
            with open(dash_app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # コールバック抽出
            callback_pattern = r'@app\.callback\s*\(\s*([^)]+)\)\s*\ndef\s+(\w+)'
            callbacks = re.findall(callback_pattern, content, re.MULTILINE | re.DOTALL)
            
            shortage_callbacks = []
            prop_callbacks = []
            
            for callback_def, function_name in callbacks:
                if 'shortage' in function_name.lower():
                    shortage_callbacks.append({
                        'function_name': function_name,
                        'definition': callback_def.strip()
                    })
                elif 'proportional' in function_name.lower():
                    prop_callbacks.append({
                        'function_name': function_name,
                        'definition': callback_def.strip()
                    })
            
            callback_analysis['shortage_tab_callbacks'] = {
                'count': len(shortage_callbacks),
                'callbacks': shortage_callbacks
            }
            
            callback_analysis['proportional_tab_callbacks'] = {
                'count': len(prop_callbacks),
                'callbacks': prop_callbacks
            }
            
            # コンフリクト分析
            all_ids = []
            for callback in shortage_callbacks + prop_callbacks:
                # Input/Outputから要素IDを抽出
                ids_in_callback = re.findall(r"['\"]([^'\"]*-[^'\"]*)['\"]", callback['definition'])
                all_ids.extend(ids_in_callback)
            
            id_counts = {}
            for id_name in all_ids:
                id_counts[id_name] = id_counts.get(id_name, 0) + 1
            
            conflicts = {id_name: count for id_name, count in id_counts.items() if count > 1}
            
            callback_analysis['callback_conflicts'] = {
                'conflicting_ids': conflicts,
                'conflict_count': len(conflicts),
                'risk_level': 'high' if len(conflicts) > 0 else 'low'
            }
            
            print(f"  不足分析コールバック: {len(shortage_callbacks)}個")
            print(f"  按分廃止コールバック: {len(prop_callbacks)}個")
            print(f"  ID競合: {len(conflicts)}個")
            
        except Exception as e:
            print(f"  ERROR: コールバック分析失敗 - {e}")
            callback_analysis['analysis_error'] = str(e)
        
        return callback_analysis
    
    def _assess_integration_risks(self):
        """統合リスク評価"""
        print("統合リスクを評価中...")
        
        risk_assessment = {
            'code_modification_risks': {},
            'data_compatibility_risks': {},
            'ui_integration_risks': {},
            'performance_risks': {},
            'overall_risk_level': 'medium'
        }
        
        # 既存分析結果に基づくリスク評価
        code_analysis = self.investigation_results.get('existing_code_analysis', {})
        data_analysis = self.investigation_results.get('data_format_analysis', {})
        callback_analysis = self.investigation_results.get('callback_analysis', {})
        
        # コード修正リスク
        shortage_complexity = code_analysis.get('shortage_tab_analysis', {}).get('complexity_score', {}).get('complexity_score', 0)
        prop_complexity = code_analysis.get('proportional_tab_analysis', {}).get('complexity_score', {}).get('complexity_score', 0)
        
        risk_assessment['code_modification_risks'] = {
            'shortage_tab_complexity': shortage_complexity,
            'proportional_tab_complexity': prop_complexity,
            'integration_complexity': shortage_complexity + prop_complexity,
            'risk_level': 'high' if (shortage_complexity + prop_complexity) > 100 else 'medium'
        }
        
        # データ互換性リスク
        format_compatibility = data_analysis.get('format_compatibility', {})
        integration_complexity = format_compatibility.get('integration_complexity', 'unknown')
        
        risk_assessment['data_compatibility_risks'] = {
            'format_integration_complexity': integration_complexity,
            'data_conversion_required': integration_complexity in ['medium', 'high'],
            'risk_level': 'high' if integration_complexity == 'high' else 'medium'
        }
        
        # UI統合リスク
        callback_conflicts = callback_analysis.get('callback_conflicts', {}).get('conflict_count', 0)
        
        risk_assessment['ui_integration_risks'] = {
            'callback_conflicts': callback_conflicts,
            'id_collision_risk': callback_conflicts > 0,
            'risk_level': 'high' if callback_conflicts > 2 else 'medium' if callback_conflicts > 0 else 'low'
        }
        
        # 総合リスクレベル
        risk_levels = [
            risk_assessment['code_modification_risks']['risk_level'],
            risk_assessment['data_compatibility_risks']['risk_level'],
            risk_assessment['ui_integration_risks']['risk_level']
        ]
        
        high_risks = risk_levels.count('high')
        if high_risks >= 2:
            risk_assessment['overall_risk_level'] = 'high'
        elif high_risks == 1 or risk_levels.count('medium') >= 2:
            risk_assessment['overall_risk_level'] = 'medium'
        else:
            risk_assessment['overall_risk_level'] = 'low'
        
        print(f"  総合リスクレベル: {risk_assessment['overall_risk_level']}")
        
        return risk_assessment
    
    def _create_compatibility_matrix(self):
        """互換性マトリックス作成"""
        print("互換性マトリックスを作成中...")
        
        matrix = {
            'ui_compatibility': {},
            'data_compatibility': {},
            'function_compatibility': {},
            'integration_feasibility': {}
        }
        
        # 分析結果から互換性を評価
        code_analysis = self.investigation_results.get('existing_code_analysis', {})
        data_analysis = self.investigation_results.get('data_format_analysis', {})
        
        # UI互換性
        shared_components = code_analysis.get('shared_components', {})
        ui_reuse_potential = shared_components.get('ui_reuse_potential', 0)
        
        matrix['ui_compatibility'] = {
            'reuse_potential': ui_reuse_potential,
            'shared_components': shared_components.get('shared_ui_components', []),
            'compatibility_score': ui_reuse_potential * 10,
            'integration_difficulty': 'low' if ui_reuse_potential > 0.5 else 'medium' if ui_reuse_potential > 0.2 else 'high'
        }
        
        # データ互換性
        format_compatibility = data_analysis.get('format_compatibility', {})
        overlap_ratio = format_compatibility.get('column_overlap', {}).get('overlap_ratio', 0)
        
        matrix['data_compatibility'] = {
            'column_overlap_ratio': overlap_ratio,
            'integration_complexity': format_compatibility.get('integration_complexity', 'unknown'),
            'compatibility_score': overlap_ratio * 10,
            'conversion_required': overlap_ratio < 0.7
        }
        
        # 統合実現可能性
        ui_score = matrix['ui_compatibility']['compatibility_score']
        data_score = matrix['data_compatibility']['compatibility_score']
        overall_score = (ui_score + data_score) / 2
        
        matrix['integration_feasibility'] = {
            'overall_compatibility_score': overall_score,
            'feasibility_level': 'high' if overall_score > 7 else 'medium' if overall_score > 4 else 'low',
            'recommended_approach': self._recommend_integration_approach(overall_score),
            'critical_challenges': self._identify_critical_challenges()
        }
        
        print(f"  統合実現可能性: {matrix['integration_feasibility']['feasibility_level']}")
        
        return matrix
    
    def _recommend_integration_approach(self, compatibility_score):
        """統合アプローチ推奨"""
        if compatibility_score > 7:
            return 'direct_integration'
        elif compatibility_score > 4:
            return 'gradual_integration_with_adapter'
        else:
            return 'separate_implementation_with_shared_ui'
    
    def _identify_critical_challenges(self):
        """重要課題特定"""
        challenges = []
        
        risk_assessment = self.investigation_results.get('risk_assessment', {})
        
        if risk_assessment.get('code_modification_risks', {}).get('risk_level') == 'high':
            challenges.append('複雑なコード統合')
        
        if risk_assessment.get('data_compatibility_risks', {}).get('risk_level') == 'high':
            challenges.append('データフォーマット変換')
        
        if risk_assessment.get('ui_integration_risks', {}).get('risk_level') == 'high':
            challenges.append('UIコンポーネント競合解決')
        
        return challenges
    
    def save_investigation_report(self):
        """調査レポート保存"""
        print("\n=== Phase 0調査レポート保存 ===")
        
        comprehensive_report = {
            'metadata': {
                'investigation_type': 'Phase0_Detailed_Code_Investigation',
                'timestamp': datetime.now().isoformat(),
                'scope': 'shortage_tab_proportional_tab_integration_analysis'
            },
            'investigation_results': self.investigation_results,
            'executive_summary': self._generate_executive_summary(),
            'recommendations': self._generate_recommendations()
        }
        
        # レポートファイル保存
        report_path = Path(f'phase0_detailed_investigation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"Phase 0調査レポート保存: {report_path}")
        
        # サマリー表示
        self._display_investigation_summary(comprehensive_report['executive_summary'])
        
        return comprehensive_report
    
    def _generate_executive_summary(self):
        """エグゼクティブサマリー生成"""
        risk_assessment = self.investigation_results.get('risk_assessment', {})
        compatibility_matrix = self.investigation_results.get('compatibility_matrix', {})
        
        return {
            'investigation_completion': 'successful',
            'overall_risk_level': risk_assessment.get('overall_risk_level', 'unknown'),
            'integration_feasibility': compatibility_matrix.get('integration_feasibility', {}).get('feasibility_level', 'unknown'),
            'recommended_approach': compatibility_matrix.get('integration_feasibility', {}).get('recommended_approach', 'unknown'),
            'critical_findings': self._extract_critical_findings(),
            'next_phase_readiness': self._assess_next_phase_readiness()
        }
    
    def _extract_critical_findings(self):
        """重要発見事項抽出"""
        findings = []
        
        code_analysis = self.investigation_results.get('existing_code_analysis', {})
        
        # コード複雑度
        shortage_lines = code_analysis.get('shortage_tab_analysis', {}).get('line_count', 0)
        prop_lines = code_analysis.get('proportional_tab_analysis', {}).get('line_count', 0)
        
        if shortage_lines + prop_lines > 500:
            findings.append(f'統合対象コードが{shortage_lines + prop_lines}行と大規模')
        
        # データ互換性
        data_analysis = self.investigation_results.get('data_format_analysis', {})
        compatibility = data_analysis.get('format_compatibility', {}).get('integration_complexity', 'unknown')
        
        if compatibility == 'high':
            findings.append('データフォーマットの互換性が低く、変換処理が必要')
        
        # コールバック競合
        callback_analysis = self.investigation_results.get('callback_analysis', {})
        conflicts = callback_analysis.get('callback_conflicts', {}).get('conflict_count', 0)
        
        if conflicts > 0:
            findings.append(f'UIコンポーネントID競合が{conflicts}個発見')
        
        return findings
    
    def _assess_next_phase_readiness(self):
        """次フェーズ準備状況評価"""
        risk_level = self.investigation_results.get('risk_assessment', {}).get('overall_risk_level', 'medium')
        feasibility = self.investigation_results.get('compatibility_matrix', {}).get('integration_feasibility', {}).get('feasibility_level', 'medium')
        
        if risk_level == 'low' and feasibility == 'high':
            return {
                'ready_for_phase1': True,
                'confidence_level': 'high',
                'recommended_timeline': 'proceed_as_planned'
            }
        elif risk_level == 'medium' or feasibility == 'medium':
            return {
                'ready_for_phase1': True,
                'confidence_level': 'medium',
                'recommended_timeline': 'proceed_with_caution'
            }
        else:
            return {
                'ready_for_phase1': False,
                'confidence_level': 'low',
                'recommended_timeline': 'risk_mitigation_required'
            }
    
    def _generate_recommendations(self):
        """推奨事項生成"""
        compatibility_matrix = self.investigation_results.get('compatibility_matrix', {})
        risk_assessment = self.investigation_results.get('risk_assessment', {})
        
        return {
            'integration_approach': compatibility_matrix.get('integration_feasibility', {}).get('recommended_approach', 'unknown'),
            'risk_mitigation_priorities': compatibility_matrix.get('integration_feasibility', {}).get('critical_challenges', []),
            'implementation_recommendations': [
                '段階的統合アプローチを採用',
                'データ変換レイヤーの事前実装',
                'UIコンポーネントID名前空間の整理',
                '包括的テスト計画の策定'
            ],
            'timeline_adjustments': {
                'additional_preparation_needed': risk_assessment.get('overall_risk_level') == 'high',
                'estimated_additional_hours': 8 if risk_assessment.get('overall_risk_level') == 'high' else 4
            }
        }
    
    def _display_investigation_summary(self, summary):
        """調査サマリー表示"""
        print("\n" + "=" * 70)
        print("*** Phase 0 詳細調査完了サマリー ***")
        print("=" * 70)
        
        print(f"\n【調査完了ステータス】: {summary['investigation_completion']}")
        print(f"【総合リスクレベル】: {summary['overall_risk_level']}")
        print(f"【統合実現可能性】: {summary['integration_feasibility']}")
        print(f"【推奨アプローチ】: {summary['recommended_approach']}")
        
        print(f"\n【重要発見事項】:")
        for i, finding in enumerate(summary['critical_findings'], 1):
            print(f"  {i}. {finding}")
        
        readiness = summary['next_phase_readiness']
        print(f"\n【次フェーズ準備状況】:")
        print(f"  Phase1準備完了: {'✅' if readiness['ready_for_phase1'] else '❌'}")
        print(f"  信頼度レベル: {readiness['confidence_level']}")
        print(f"  推奨タイムライン: {readiness['recommended_timeline']}")
        
        print("\n" + "=" * 70)

def main():
    print("=" * 70)
    print("*** Phase 0: 詳細調査開始 ***")
    print("目的: 不足分析タブと按分廃止タブの統合に向けた包括的調査")
    print("=" * 70)
    
    investigator = DetailedCodeInvestigation()
    
    try:
        # 包括的調査実行
        investigation_results = investigator.conduct_comprehensive_investigation()
        
        # 調査レポート保存
        report = investigator.save_investigation_report()
        
        return report
        
    except Exception as e:
        print(f"\nERROR Phase 0調査中にエラー: {e}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    main()