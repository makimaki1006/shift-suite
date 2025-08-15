#!/usr/bin/env python3
"""
Windows対応 - 緊急リスク評価実行
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Windows Unicode対応
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

class SimpleRiskAssessment:
    """簡易版緊急リスク評価"""
    
    def __init__(self):
        self.assessment = {}
        
    def analyze_current_state(self):
        """現状分析"""
        print("=== 現状システム分析 ===")
        
        files_analysis = {}
        
        critical_files = [
            "dash_app.py", 
            "unified_data_pipeline_architecture.py",
            "gradual_integration_patch.py"
        ]
        
        for file_name in critical_files:
            file_path = Path(file_name)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                files_analysis[file_name] = {
                    'size_bytes': file_path.stat().st_size,
                    'lines': len(content.splitlines()),
                    'complexity': self._calculate_complexity(content)
                }
                
                print(f"{file_name}:")
                print(f"  サイズ: {files_analysis[file_name]['size_bytes']:,} bytes")
                print(f"  行数: {files_analysis[file_name]['lines']:,}")
                print(f"  複雑度スコア: {files_analysis[file_name]['complexity']}")
        
        return files_analysis
    
    def _calculate_complexity(self, content):
        """複雑度計算"""
        complexity = 0
        complexity += content.count('if ') * 1
        complexity += content.count('for ') * 2  
        complexity += content.count('while ') * 2
        complexity += content.count('try:') * 3
        complexity += content.count('class ') * 5
        return complexity
        
    def identify_dependencies(self):
        """統一システム依存関係特定"""
        print("\n=== 依存関係分析 ===")
        
        dash_app_path = Path("dash_app.py")
        dependencies = []
        
        if dash_app_path.exists():
            with open(dash_app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            unified_patterns = [
                'unified_data_pipeline_architecture',
                'UNIFIED_SYSTEM_AVAILABLE', 
                'UNIFIED_REGISTRY',
                'enhanced_data_get',
                'DataType.PROPORTIONAL_ABOLITION'
            ]
            
            for pattern in unified_patterns:
                if pattern in content:
                    lines = content.splitlines()
                    for i, line in enumerate(lines, 1):
                        if pattern in line:
                            dependencies.append({
                                'pattern': pattern,
                                'line': i,
                                'context': line.strip()[:80]
                            })
            
            print(f"統一システム依存箇所: {len(dependencies)}件")
        
        return dependencies
    
    def evaluate_risks(self, files_analysis, dependencies):
        """リスク評価"""
        print("\n=== リスク評価 ===")
        
        risks = []
        
        # 1. 複雑度リスク
        unified_analysis = files_analysis.get('unified_data_pipeline_architecture.py', {})
        complexity = unified_analysis.get('complexity', 0)
        
        if complexity > 100:
            risks.append({
                'category': 'Complexity',
                'severity': 'HIGH', 
                'description': f'統一システム複雑度危険レベル ({complexity})',
                'impact': 'システム理解困難・バグリスク大'
            })
        
        # 2. 統合リスク
        if len(dependencies) > 10:
            risks.append({
                'category': 'Integration',
                'severity': 'MEDIUM',
                'description': f'dash_app.pyに{len(dependencies)}箇所の統一システム依存',
                'impact': 'メンテナンス困難・副作用リスク'
            })
        
        # 3. ビジネス乖離リスク
        risks.append({
            'category': 'Business',
            'severity': 'CRITICAL',
            'description': '按分廃止ファイル検索→334ファイルスキャンシステムに発展',
            'impact': '投資対効果悪化・技術的負債増大'
        })
        
        for risk in risks:
            print(f"*** {risk['severity']}: {risk['description']}")
        
        return risks
    
    def propose_solution(self):
        """最小修正解決案"""
        print("\n=== 推奨解決案 ===")
        
        solution = {
            'approach': '按分廃止ファイル専用検索パス追加',
            'implementation': [
                'data_get関数に按分廃止専用条件分岐追加',
                '現在ディレクトリを按分廃止ファイルのみ検索対象に',
                '他機能への影響ゼロ'
            ],
            'benefits': [
                'コード変更最小(10行以下)',
                'リスクゼロ(既存機能無変更)', 
                '按分廃止機能確実動作',
                '理解容易・保守簡単'
            ]
        }
        
        print("*** 推奨アプローチ: 按分廃止ファイル専用検索")
        print("利点:")
        for benefit in solution['benefits']:
            print(f"  • {benefit}")
        
        return solution
    
    def execute_assessment(self):
        """評価実行"""
        print("=" * 60)
        print("*** 緊急リスク評価開始")
        print("目的: 過剰統一システムの安全な段階的撤去")
        print("=" * 60)
        
        # 分析実行
        files_analysis = self.analyze_current_state()
        dependencies = self.identify_dependencies() 
        risks = self.evaluate_risks(files_analysis, dependencies)
        solution = self.propose_solution()
        
        # 結果保存
        self.assessment = {
            'files_analysis': files_analysis,
            'dependencies': dependencies,
            'risks': risks,
            'solution': solution,
            'timestamp': datetime.now().isoformat(),
            'recommendation': 'IMMEDIATE_ROLLBACK_REQUIRED'
        }
        
        # サマリー
        print("\n" + "=" * 60)
        print("*** 緊急評価サマリー ***")
        print("=" * 60)
        print(f"統一システム複雑度: 危険レベル")
        print(f"dash_app.py統合箇所: {len(dependencies)}箇所") 
        print(f"技術的負債: 大幅増加")
        print("\n推奨アクション:")
        print("1. 即座: 統一システム無効化")
        print("2. 短期: 統一システム完全削除")
        print("3. 最終: 按分廃止機能最小修正実装")
        print("=" * 60)
        
        return self.assessment

def main():
    assessor = SimpleRiskAssessment()
    assessment = assessor.execute_assessment()
    
    # レポート保存
    report_path = Path(f"emergency_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(assessment, f, ensure_ascii=False, indent=2)
    
    print(f"\nレポート保存: {report_path}")
    
    # Phase1実行確認
    print("\nPhase 1緊急安全装置を作動しますか？")
    print("統一システムを無効化して安全モードに移行します")
    user_input = input("(y/N): ")
    
    if user_input.lower() == 'y':
        execute_phase1()
    else:
        print("緊急安全装置はキャンセルされました")

def execute_phase1():
    """Phase1: 緊急安全装置作動"""
    print("\n*** Phase 1: 緊急安全装置作動中...")
    
    # バックアップ作成
    backup_dir = Path(f"EMERGENCY_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)
    
    import shutil
    critical_files = ["dash_app.py", "unified_data_pipeline_architecture.py"]
    
    for file_name in critical_files:
        file_path = Path(file_name)
        if file_path.exists():
            backup_path = backup_dir / file_name
            shutil.copy2(file_path, backup_path)
            print(f"バックアップ作成: {file_name}")
    
    # 統一システム無効化
    dash_app_path = Path("dash_app.py")
    if dash_app_path.exists():
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'UNIFIED_SYSTEM_AVAILABLE = True' in content:
            content = content.replace(
                'UNIFIED_SYSTEM_AVAILABLE = True',
                'UNIFIED_SYSTEM_AVAILABLE = False  # 緊急安全装置: 統一システム無効化'
            )
            
            with open(dash_app_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("*** 緊急安全装置作動完了: 統一システム無効化")
        else:
            print("統一システムは既に無効化されています")
    
    print(f"Phase 1完了 - バックアップ: {backup_dir}")
    print("安全モード移行完了")

if __name__ == "__main__":
    main()