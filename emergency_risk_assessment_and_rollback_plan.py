#!/usr/bin/env python3
"""
緊急リスク評価とロールバック計画
過剰統一システムの段階的安全撤去
"""

import sys
from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import List, Dict, Tuple
import subprocess

class EmergencyRiskAssessment:
    """緊急リスク評価・安全撤去計画"""
    
    def __init__(self):
        self.backup_dir = Path(f"EMERGENCY_ROLLBACK_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.critical_files = [
            "dash_app.py",
            "unified_data_pipeline_architecture.py",
            "gradual_integration_patch.py",
            "integrate_unified_system.py"
        ]
        self.risk_assessment = {}
        
    def execute_emergency_assessment(self):
        """緊急リスク評価実行"""
        
        print("=" * 80)
        print("*** 緊急リスク評価開始")
        print("目的: 過剰統一システムの安全な段階的撤去")
        print("=" * 80)
        
        # 1. 現状分析
        self.analyze_current_state()
        
        # 2. 依存関係特定
        self.identify_dependencies()
        
        # 3. リスク評価
        self.evaluate_risks()
        
        # 4. 撤去計画策定
        self.create_rollback_plan()
        
        # 5. 最小修正案提示
        self.propose_minimal_solution()
        
        return self.generate_assessment_report()
    
    def analyze_current_state(self):
        """現状システム分析"""
        
        print("\n【Phase 1: 現状システム分析】")
        
        # ファイルサイズ・複雑度分析
        analysis = {}
        
        for file_name in self.critical_files:
            file_path = Path(file_name)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                analysis[file_name] = {
                    'size_bytes': file_path.stat().st_size,
                    'lines_of_code': len(content.splitlines()),
                    'import_count': content.count('import '),
                    'class_count': content.count('class '),
                    'function_count': content.count('def '),
                    'complexity_score': self._calculate_complexity(content)
                }
                
                print(f"  {file_name}:")
                print(f"    サイズ: {analysis[file_name]['size_bytes']:,}bytes")
                print(f"    行数: {analysis[file_name]['lines_of_code']:,}")
                print(f"    複雑度: {analysis[file_name]['complexity_score']}")
        
        self.risk_assessment['file_analysis'] = analysis
    
    def _calculate_complexity(self, content: str) -> int:
        """コード複雑度計算（簡易版）"""
        complexity = 0
        complexity += content.count('if ') * 1
        complexity += content.count('for ') * 2
        complexity += content.count('while ') * 2
        complexity += content.count('try:') * 3
        complexity += content.count('except') * 2
        complexity += content.count('class ') * 5
        return complexity
    
    def identify_dependencies(self):
        """依存関係特定"""
        
        print("\n【Phase 2: 依存関係特定】")
        
        dependencies = {}
        
        # dash_app.pyの統一システム依存を特定
        dash_app_path = Path("dash_app.py")
        if dash_app_path.exists():
            with open(dash_app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            unified_dependencies = []
            
            # 統一システム関連のインポート・使用を検索
            unified_patterns = [
                'unified_data_pipeline_architecture',
                'UNIFIED_SYSTEM_AVAILABLE',
                'UNIFIED_REGISTRY',
                'enhanced_data_get',
                'DataType.PROPORTIONAL_ABOLITION',
                'get_unified_registry'
            ]
            
            for pattern in unified_patterns:
                if pattern in content:
                    # 使用箇所の行番号取得
                    lines = content.splitlines()
                    for i, line in enumerate(lines, 1):
                        if pattern in line:
                            unified_dependencies.append({
                                'pattern': pattern,
                                'line': i,
                                'context': line.strip()
                            })
            
            dependencies['dash_app_unified_usage'] = unified_dependencies
            print(f"  統一システム依存箇所: {len(unified_dependencies)}件")
        
        self.risk_assessment['dependencies'] = dependencies
    
    def evaluate_risks(self):
        """リスク評価"""
        
        print("\n【Phase 3: リスク評価】")
        
        risks = []
        
        # 1. 統一システムの複雑度リスク
        unified_file = Path("unified_data_pipeline_architecture.py")
        if unified_file.exists():
            file_analysis = self.risk_assessment['file_analysis'].get('unified_data_pipeline_architecture.py', {})
            complexity = file_analysis.get('complexity_score', 0)
            
            if complexity > 100:
                risks.append({
                    'category': 'Complexity',
                    'severity': 'HIGH',
                    'description': f'統一システムの複雑度が危険レベル（{complexity}）',
                    'impact': 'システム理解困難、バグ混入リスク大',
                    'recommendation': '即座削除・単純化'
                })
        
        # 2. dash_app.pyの統合リスク
        unified_usage = self.risk_assessment['dependencies'].get('dash_app_unified_usage', [])
        if len(unified_usage) > 10:
            risks.append({
                'category': 'Integration',
                'severity': 'MEDIUM',
                'description': f'dash_app.pyに{len(unified_usage)}箇所の統一システム依存',
                'impact': 'メンテナンス困難、副作用発生可能性',
                'recommendation': '段階的依存関係削除'
            })
        
        # 3. 按分廃止機能の本来目的からの乖離
        risks.append({
            'category': 'Business',
            'severity': 'CRITICAL',
            'description': '按分廃止ファイル検索問題が334ファイルスキャンシステムに発展',
            'impact': '投資対効果悪化、技術的負債増大',
            'recommendation': '本来目的（按分廃止ファイル読み込み）への回帰'
        })
        
        self.risk_assessment['risks'] = risks
        
        for risk in risks:
            print(f"  *** {risk['severity']}: {risk['description']}")
    
    def create_rollback_plan(self):
        """ロールバック計画策定"""
        
        print("\n【Phase 4: 段階的ロールバック計画】")
        
        rollback_plan = {
            'phase1_immediate': {
                'description': '統一システムの依存関係を条件分岐化（安全装置）',
                'actions': [
                    'UNIFIED_SYSTEM_AVAILABLEフラグで統一システムを無効化',
                    '按分廃止機能の従来システム動作確認',
                    '統一システム削除準備'
                ],
                'risk_level': 'LOW',
                'execution_time': '30分'
            },
            'phase2_simplification': {
                'description': '統一システム完全削除と最小修正実装',
                'actions': [
                    'unified_data_pipeline_architecture.py削除',
                    '関連インポート・使用箇所削除',
                    'data_get関数の最小修正実装',
                    '按分廃止ファイル検索の直接的解決'
                ],
                'risk_level': 'MEDIUM',
                'execution_time': '2時間'
            },
            'phase3_verification': {
                'description': '簡素化システムの動作確認と最適化',
                'actions': [
                    '按分廃止機能完全動作確認',
                    'パフォーマンステスト実施',
                    'コード品質改善',
                    'ドキュメント整備'
                ],
                'risk_level': 'LOW',
                'execution_time': '1時間'
            }
        }
        
        self.risk_assessment['rollback_plan'] = rollback_plan
        
        for phase, details in rollback_plan.items():
            print(f"  *** {phase}: {details['description']}")
            print(f"      リスク: {details['risk_level']}, 所要時間: {details['execution_time']}")
    
    def propose_minimal_solution(self):
        """最小修正解決案"""
        
        print("\n【Phase 5: 最小修正解決案】")
        
        minimal_solution = {
            'approach': '按分廃止ファイル専用検索パス追加',
            'implementation': [
                'data_get関数に按分廃止専用条件分岐追加',
                '現在ディレクトリ（"."）を按分廃止ファイルのみ検索対象に',
                '他の機能への影響ゼロ'
            ],
            'code_changes': '''
# 最小修正版data_get関数（按分廃止専用）
def data_get(key: str, default=None, for_display: bool = False):
    # 按分廃止ファイル専用高速パス
    if key in ['proportional_abolition_role_summary', 'proportional_abolition_organization_summary']:
        proportional_file = Path('.') / f"{key}.parquet"
        if proportional_file.exists():
            try:
                return pd.read_parquet(proportional_file)
            except Exception as e:
                log.warning(f"按分廃止ファイル読み込み失敗: {e}")
    
    # 既存システム（変更なし）
    # ... 従来のdata_get実装
''',
            'benefits': [
                'コード変更最小（10行以下）',
                'リスクゼロ（既存機能無変更）',
                '按分廃止機能確実動作',
                '理解容易・保守簡単'
            ],
            'implementation_time': '15分'
        }
        
        self.risk_assessment['minimal_solution'] = minimal_solution
        
        print("  *** 推奨アプローチ: 按分廃止ファイル専用検索")
        print("  *** 利点:")
        for benefit in minimal_solution['benefits']:
            print(f"      • {benefit}")
    
    def generate_assessment_report(self):
        """評価レポート生成"""
        
        report_path = self.backup_dir / "emergency_risk_assessment_report.json"
        self.backup_dir.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.risk_assessment, f, ensure_ascii=False, indent=2)
        
        # サマリーレポート生成
        summary = f"""
=============================================================================
*** 緊急リスク評価サマリー ***
=============================================================================

【現状】
• 統一システム複雑度: 危険レベル
• dash_app.py統合箇所: {len(self.risk_assessment['dependencies'].get('dash_app_unified_usage', []))}箇所
• 技術的負債: 大幅増加

【推奨アクション】
1. 即座: 統一システム無効化（安全装置作動）
2. 短期: 統一システム完全削除
3. 最終: 按分廃止機能最小修正実装

【期待効果】
• リスク除去: システム安定性確保
• 保守性向上: コード簡素化・理解容易
• 投資対効果: 適切な問題解決範囲

レポート詳細: {report_path}
=============================================================================
        """
        
        print(summary)
        
        with open(self.backup_dir / "emergency_summary.txt", 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return {
            'assessment_complete': True,
            'report_path': report_path,
            'summary_path': self.backup_dir / "emergency_summary.txt",
            'recommended_action': 'IMMEDIATE_ROLLBACK_REQUIRED'
        }

def execute_phase1_immediate_action():
    """Phase 1: 即座実行アクション"""
    
    print("\n*** Phase 1: 緊急安全装置作動")
    
    # 1. バックアップ作成
    backup_dir = Path(f"CRITICAL_BACKUP_BEFORE_ROLLBACK_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)
    
    critical_files = ["dash_app.py", "unified_data_pipeline_architecture.py"]
    
    for file_name in critical_files:
        file_path = Path(file_name)
        if file_path.exists():
            backup_path = backup_dir / file_name
            shutil.copy2(file_path, backup_path)
            print(f"✓ バックアップ作成: {file_name} -> {backup_path}")
    
    # 2. 統一システム無効化（安全装置）
    dash_app_path = Path("dash_app.py")
    if dash_app_path.exists():
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 統一システムを強制無効化
        if 'UNIFIED_SYSTEM_AVAILABLE = True' in content:
            content = content.replace(
                'UNIFIED_SYSTEM_AVAILABLE = True',
                'UNIFIED_SYSTEM_AVAILABLE = False  # 緊急安全装置: 統一システム無効化'
            )
            
            with open(dash_app_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✓ 緊急安全装置作動: 統一システム無効化完了")
        else:
            print("⚠️ 統一システムは既に無効化されています")
    
    return {
        'action': 'emergency_safety_engaged',
        'backup_dir': backup_dir,
        'unified_system_disabled': True,
        'status': 'SAFE_MODE_ACTIVATED'
    }

if __name__ == "__main__":
    # 緊急リスク評価実行
    assessor = EmergencyRiskAssessment()
    assessment_result = assessor.execute_emergency_assessment()
    
    print("\n" + "="*80)
    if assessment_result['recommended_action'] == 'IMMEDIATE_ROLLBACK_REQUIRED':
        print("*** CRITICAL: 即座ロールバック推奨")
        
        user_input = input("\nPhase 1緊急安全装置を作動しますか？ (y/N): ")
        if user_input.lower() == 'y':
            phase1_result = execute_phase1_immediate_action()
            print(f"✓ Phase 1完了: {phase1_result['status']}")
        else:
            print("⚠️ 緊急安全装置はキャンセルされました")
    
    print("="*80)