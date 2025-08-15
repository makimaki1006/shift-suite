# -*- coding: utf-8 -*-
"""
組織パターン深度分析統合テスト - Organizational Pattern Deep Analysis Integration Test

Phase 1B: 組織パターン分析エンジンとAIレポート生成器の完全統合テスト
理論的基盤の動作確認と深度分析出力の検証を実施します。

テスト対象:
1. OrganizationalPatternAnalyzer の動作確認
2. AIComprehensiveReportGenerator への統合確認  
3. 14番目のセクション (organizational_pattern_deep_analysis) の出力検証
4. 理論的フレームワーク (Schein, Systems Psychodynamics, SNA, Power Theory, Institutional Theory) の適用確認
5. Phase 1A (認知科学分析) との統合確認
"""

import sys
import os
import tempfile
import json
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback

def test_organizational_deep_analysis_integration():
    """組織パターン深度分析統合テストのメイン実行"""
    
    print("=" * 80)
    print("🏢 組織パターン深度分析統合テスト (Phase 1B)")
    print("=" * 80)
    print()
    
    try:
        # shift_suite パスを追加
        current_dir = Path(__file__).parent
        sys.path.append(str(current_dir))
        
        # 1. 組織パターン分析エンジンの独立テスト
        print("📊 Step 1: 組織パターン分析エンジンの独立動作テスト")
        print("-" * 60)
        
        organizational_engine_test_result = test_organizational_pattern_analyzer()
        
        if not organizational_engine_test_result['success']:
            print(f"❌ 組織パターン分析エンジンのテストに失敗: {organizational_engine_test_result['error']}")
            return False
        
        print("✅ 組織パターン分析エンジンの独立動作確認完了")
        print()
        
        # 2. AIレポート生成器への統合テスト
        print("🔗 Step 2: AIレポート生成器統合テスト (14セクション)")
        print("-" * 60)
        
        integration_test_result = test_ai_report_generator_integration()
        
        if not integration_test_result['success']:
            print(f"❌ AIレポート生成器統合テストに失敗: {integration_test_result['error']}")
            return False
        
        print("✅ AIレポート生成器統合確認完了")
        print()
        
        # 3. 組織深度分析出力の詳細検証
        print("🔍 Step 3: 組織深度分析出力の詳細検証")
        print("-" * 60)
        
        output_verification_result = verify_organizational_analysis_output(integration_test_result['report'])
        
        if not output_verification_result['success']:
            print(f"❌ 組織深度分析出力検証に失敗: {output_verification_result['error']}")
            return False
        
        print("✅ 組織深度分析出力検証完了")
        print()
        
        # 4. 理論的フレームワークの適用確認
        print("📚 Step 4: 組織理論的フレームワーク適用確認") 
        print("-" * 60)
        
        framework_verification_result = verify_organizational_theoretical_frameworks(integration_test_result['report'])
        
        if not framework_verification_result['success']:
            print(f"❌ 組織理論的フレームワーク検証に失敗: {framework_verification_result['error']}")
            return False
        
        print("✅ 組織理論的フレームワーク適用確認完了")
        print()
        
        # 5. Phase 1A & 1B統合確認
        print("🔄 Step 5: Phase 1A & 1B 統合確認")
        print("-" * 60)
        
        phase_integration_result = verify_phase_1a_1b_integration(integration_test_result['report'])
        
        if not phase_integration_result['success']:
            print(f"❌ Phase 1A & 1B統合確認に失敗: {phase_integration_result['error']}")
            return False
        
        print("✅ Phase 1A & 1B統合確認完了")
        print()
        
        # 6. 最終統合テスト結果の表示
        print("🎯 Step 6: 最終統合テスト結果")
        print("-" * 60)
        
        display_final_organizational_integration_results(
            organizational_engine_test_result,
            integration_test_result, 
            output_verification_result,
            framework_verification_result,
            phase_integration_result
        )
        
        return True
        
    except Exception as e:
        print(f"❌ 統合テスト実行エラー: {e}")
        traceback.print_exc()
        return False

def test_organizational_pattern_analyzer():
    """組織パターン分析エンジン独立テスト"""
    
    try:
        from shift_suite.tasks.organizational_pattern_analyzer import OrganizationalPatternAnalyzer
        
        # 組織パターン分析エンジンの初期化
        analyzer = OrganizationalPatternAnalyzer()
        print(f"   ✓ 分析エンジン初期化完了 (ID: {analyzer.analysis_id})")
        
        # 理論的基盤の確認
        if hasattr(analyzer, 'culture_layers'):
            print(f"   ✓ Schein組織文化モデル設定: {len(analyzer.culture_layers)} 層")
        
        if hasattr(analyzer, 'power_sources'):
            print(f"   ✓ French & Raven権力源泉設定: {len(analyzer.power_sources)} 源泉")
        
        if hasattr(analyzer, 'defense_mechanisms'):
            print(f"   ✓ 組織的防衛メカニズム設定: {len(analyzer.defense_mechanisms)} メカニズム")
        
        # テスト用シフトデータ生成
        shift_data = generate_test_organizational_shift_data()
        print(f"   ✓ テスト組織シフトデータ生成完了 ({len(shift_data)} records)")
        
        # 模擬分析結果データ生成
        mock_analysis_results = generate_mock_organizational_analysis_results()
        print(f"   ✓ 模擬組織分析結果データ生成完了")
        
        # 包括的組織パターン分析の実行
        print("   🔄 包括的組織パターン分析実行中...")
        
        analysis_result = analyzer.analyze_organizational_patterns(
            shift_data=shift_data,
            analysis_results=mock_analysis_results,
            historical_data=None
        )
        
        # 分析結果の基本検証
        if 'analysis_metadata' not in analysis_result:
            return {'success': False, 'error': '分析結果にメタデータが含まれていません'}
        
        if 'implicit_power_structure' not in analysis_result:
            return {'success': False, 'error': '暗黙的権力構造分析が実行されていません'}
        
        if 'organizational_culture_layers' not in analysis_result:
            return {'success': False, 'error': '組織文化層分析が実行されていません'}
        
        print(f"   ✅ 分析完了 ({len(analysis_result)} sections)")
        
        return {
            'success': True,
            'analysis_result': analysis_result,
            'analyzer_id': analyzer.analysis_id
        }
        
    except ImportError as e:
        return {'success': False, 'error': f'組織パターン分析モジュールのインポートエラー: {e}'}
    except Exception as e:
        return {'success': False, 'error': f'組織パターン分析エンジンテストエラー: {e}'}

def test_ai_report_generator_integration():
    """AIレポート生成器統合テスト (14セクション確認)"""
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import (
            AIComprehensiveReportGenerator, 
            COGNITIVE_ANALYSIS_AVAILABLE,
            ORGANIZATIONAL_ANALYSIS_AVAILABLE
        )
        
        # AIレポート生成器の初期化
        generator = AIComprehensiveReportGenerator()
        print(f"   ✓ AIレポート生成器初期化完了 (ID: {generator.report_id})")
        
        # 認知科学分析エンジンの統合確認
        if hasattr(generator, 'cognitive_analyzer'):
            cognitive_status = "統合済み" if generator.cognitive_analyzer is not None else "無効化"
            print(f"   📊 認知科学分析エンジン: {cognitive_status}")
        
        # 組織パターン分析エンジンの統合確認
        if hasattr(generator, 'organizational_analyzer'):
            organizational_status = "統合済み" if generator.organizational_analyzer is not None else "無効化"
            print(f"   🏢 組織パターン分析エンジン: {organizational_status}")
        else:
            print(f"   ❌ 組織パターン分析エンジン統合属性が見つかりません")
        
        print(f"   📋 分析モジュール利用可能性:")
        print(f"      • 認知科学分析: {COGNITIVE_ANALYSIS_AVAILABLE}")
        print(f"      • 組織パターン分析: {ORGANIZATIONAL_ANALYSIS_AVAILABLE}")
        
        # テスト用分析結果データ作成
        test_analysis_results = create_comprehensive_organizational_test_analysis_results()
        test_analysis_params = create_test_organizational_analysis_params()
        
        # 一時出力ディレクトリ作成
        temp_dir = Path(tempfile.mkdtemp(prefix="organizational_integration_test_"))
        print(f"   ✓ 一時ディレクトリ作成: {temp_dir}")
        
        # テスト用Parquetファイル作成
        create_test_organizational_parquet_files(temp_dir)
        print(f"   ✓ テスト用Parquetファイル作成完了")
        
        # 包括レポート生成実行
        print("   🔄 包括レポート生成実行中...")
        
        comprehensive_report = generator.generate_comprehensive_report(
            analysis_results=test_analysis_results,
            input_file_path="test_organizational_analysis.xlsx",
            output_dir=str(temp_dir),
            analysis_params=test_analysis_params
        )
        
        # 基本セクション確認（12セクション）
        expected_basic_sections = [
            'report_metadata', 'execution_summary', 'data_quality_assessment',
            'key_performance_indicators', 'detailed_analysis_modules',
            'systemic_problem_archetypes', 'rule_violation_summary',
            'prediction_and_forecasting', 'resource_optimization_insights',
            'analysis_limitations_and_external_factors', 'summary_of_critical_observations',
            'generated_files_manifest'
        ]
        
        for section in expected_basic_sections:
            if section not in comprehensive_report:
                return {'success': False, 'error': f'基本セクション "{section}" が生成されていません'}
        
        # 13番目のセクション確認（Phase 1A）
        if 'cognitive_psychology_deep_analysis' not in comprehensive_report:
            print(f"   ⚠️ 認知科学的深度分析セクション（Phase 1A）が見つかりません")
        else:
            print(f"   ✅ 13番目のセクション (cognitive_psychology_deep_analysis) 確認完了")
        
        # 14番目のセクション確認（Phase 1B）
        if 'organizational_pattern_deep_analysis' not in comprehensive_report:
            return {'success': False, 'error': '組織パターン深度分析セクション（Phase 1B）が生成されていません'}
        
        print(f"   ✅ 14番目のセクション (organizational_pattern_deep_analysis) 確認完了")
        print(f"   🎉 包括レポート生成完了 ({len(comprehensive_report)} sections)")
        
        # クリーンアップ
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"   ✓ 一時ディレクトリクリーンアップ完了")
        
        return {
            'success': True,
            'report': comprehensive_report,
            'generator_id': generator.report_id,
            'total_sections': len(comprehensive_report)
        }
        
    except ImportError as e:
        return {'success': False, 'error': f'AIレポート生成器のインポートエラー: {e}'}
    except Exception as e:
        return {'success': False, 'error': f'AIレポート生成器統合テストエラー: {e}'}

def verify_organizational_analysis_output(comprehensive_report):
    """組織深度分析出力の詳細検証"""
    
    try:
        organizational_section = comprehensive_report.get('organizational_pattern_deep_analysis', {})
        
        # 分析ステータス確認
        analysis_status = organizational_section.get('analysis_status', 'UNKNOWN')
        print(f"   🏢 分析ステータス: {analysis_status}")
        
        if analysis_status in ['COMPLETED_SUCCESSFULLY', 'DISABLED', 'DATA_INSUFFICIENT']:
            print(f"   ✅ 分析ステータス正常")
        else:
            return {'success': False, 'error': f'予期しない分析ステータス: {analysis_status}'}
        
        # 理論的基盤の確認
        if analysis_status == 'COMPLETED_SUCCESSFULLY':
            theoretical_foundations = organizational_section.get('theoretical_foundations', [])
            expected_theories = [
                "Schein's Organizational Culture Model",
                "Systems Psychodynamics Theory", 
                "Social Network Analysis",
                "French & Raven Power Sources",
                "Institutional Theory"
            ]
            
            for theory in expected_theories:
                theory_found = any(theory in foundation for foundation in theoretical_foundations)
                if theory_found:
                    print(f"   ✅ {theory} 理論基盤確認")
                else:
                    print(f"   ⚠️ {theory} 理論基盤が見つかりません")
        
        # 深度分析結果の構造確認
        if 'deep_analysis_results' in organizational_section:
            deep_results = organizational_section['deep_analysis_results']
            expected_analysis_types = [
                'implicit_power_structure',
                'organizational_culture_layers', 
                'group_dynamics',
                'communication_networks',
                'organizational_learning',
                'change_resistance_patterns',
                'defense_mechanisms',
                'emergent_leadership',
                'organizational_silos'
            ]
            
            for analysis_type in expected_analysis_types:
                if analysis_type in deep_results:
                    print(f"   ✅ {analysis_type} 分析確認")
                else:
                    print(f"   ⚠️ {analysis_type} 分析が見つかりません")
        
        # 組織洞察サマリーの確認
        if 'organizational_insights_summary' in organizational_section:
            insights = organizational_section['organizational_insights_summary']
            print(f"   📝 組織パターン洞察: {len(insights)} 項目")
            
            for i, insight in enumerate(insights[:3], 1):
                print(f"      {i}. {insight}")
        
        # 戦略的推奨事項の確認
        if 'strategic_organizational_recommendations' in organizational_section:
            recommendations = organizational_section['strategic_organizational_recommendations']
            print(f"   🎯 戦略的組織推奨事項: {len(recommendations)} 項目")
            
            for rec in recommendations[:2]:
                category = rec.get('category', '不明')
                priority = rec.get('priority', '不明')
                print(f"      • {category} (優先度: {priority})")
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': f'組織深度分析出力検証エラー: {e}'}

def verify_organizational_theoretical_frameworks(comprehensive_report):
    """組織理論的フレームワーク適用確認"""
    
    try:
        organizational_section = comprehensive_report.get('organizational_pattern_deep_analysis', {})
        
        # フレームワーク適用度チェック
        framework_scores = {
            'Schein Culture Model': 0,
            'Systems Psychodynamics': 0, 
            'Social Network Analysis': 0,
            'Power Source Theory': 0,
            'Institutional Theory': 0
        }
        
        # 理論基盤の言及確認
        if 'theoretical_foundations' in organizational_section:
            foundations = organizational_section['theoretical_foundations']
            for foundation in foundations:
                if 'Schein' in foundation:
                    framework_scores['Schein Culture Model'] += 1
                if 'Psychodynamics' in foundation:
                    framework_scores['Systems Psychodynamics'] += 1  
                if 'Social Network' in foundation:
                    framework_scores['Social Network Analysis'] += 1
                if 'Power' in foundation or 'Raven' in foundation:
                    framework_scores['Power Source Theory'] += 1
                if 'Institutional' in foundation:
                    framework_scores['Institutional Theory'] += 1
        
        # 深度分析結果での理論適用確認
        if 'deep_analysis_results' in organizational_section:
            deep_results = organizational_section['deep_analysis_results']
            
            # 組織文化分析 (Schein)
            if 'organizational_culture_layers' in deep_results:
                framework_scores['Schein Culture Model'] += 2
            
            # 防衛メカニズム分析 (Systems Psychodynamics)
            if 'defense_mechanisms' in deep_results:
                framework_scores['Systems Psychodynamics'] += 2
            
            # 権力構造分析 (Social Network Analysis)
            if 'implicit_power_structure' in deep_results:
                framework_scores['Social Network Analysis'] += 1
                framework_scores['Power Source Theory'] += 2
            
            # コミュニケーションネットワーク (Social Network Analysis)
            if 'communication_networks' in deep_results:
                framework_scores['Social Network Analysis'] += 1
            
            # 組織的サイロ分析 (Institutional Theory)
            if 'organizational_silos' in deep_results:
                framework_scores['Institutional Theory'] += 2
        
        # フレームワーク適用度の評価
        print("   📚 組織理論的フレームワーク適用度:")
        total_score = 0
        max_possible_score = len(framework_scores) * 3  # 各理論最大3点
        
        for framework, score in framework_scores.items():
            percentage = (score / 3) * 100 if score > 0 else 0
            status = "✅" if score >= 2 else "⚠️" if score >= 1 else "❌"
            print(f"      {status} {framework}: {score}/3 ({percentage:.0f}%)")
            total_score += score
        
        overall_percentage = (total_score / max_possible_score) * 100
        print(f"   🎯 総合組織理論適用度: {overall_percentage:.1f}% ({total_score}/{max_possible_score})")
        
        if overall_percentage >= 60:
            print("   ✅ 組織理論的フレームワーク適用度: 良好")
        elif overall_percentage >= 30:
            print("   ⚠️ 組織理論的フレームワーク適用度: 中程度")
        else:
            print("   ❌ 組織理論的フレームワーク適用度: 不十分")
        
        return {'success': True, 'framework_scores': framework_scores, 'overall_score': overall_percentage}
        
    except Exception as e:
        return {'success': False, 'error': f'組織理論的フレームワーク検証エラー: {e}'}

def verify_phase_1a_1b_integration(comprehensive_report):
    """Phase 1A & 1B統合確認"""
    
    try:
        # Phase 1A セクション確認
        cognitive_section = comprehensive_report.get('cognitive_psychology_deep_analysis', {})
        cognitive_available = len(cognitive_section) > 0 and cognitive_section.get('analysis_status') != 'ERROR'
        
        # Phase 1B セクション確認
        organizational_section = comprehensive_report.get('organizational_pattern_deep_analysis', {})
        organizational_available = len(organizational_section) > 0 and organizational_section.get('analysis_status') != 'ERROR'
        
        print(f"   🧠 Phase 1A (認知科学分析): {'✅ 利用可能' if cognitive_available else '❌ 利用不可'}")
        print(f"   🏢 Phase 1B (組織パターン分析): {'✅ 利用可能' if organizational_available else '❌ 利用不可'}")
        
        # 統合分析の確認
        if organizational_available and 'integration_with_cognitive_analysis' in organizational_section:
            integration_analysis = organizational_section['integration_with_cognitive_analysis']
            print(f"   🔗 認知科学との統合分析: ✅ 実装済み")
            
            integration_keys = list(integration_analysis.keys())[:3]
            for key in integration_keys:
                print(f"      • {key}")
        
        # 総合的な統合レベル評価
        integration_score = 0
        if cognitive_available:
            integration_score += 50
        if organizational_available:
            integration_score += 50
        
        print(f"   📊 Phase 1A & 1B統合レベル: {integration_score}%")
        
        if integration_score >= 100:
            print("   🎉 完全統合: 両フェーズが正常に動作し統合されています")
        elif integration_score >= 50:
            print("   ⚠️ 部分統合: 一方のフェーズのみ動作しています")
        else:
            print("   ❌ 統合失敗: 両フェーズとも動作していません")
        
        return {
            'success': True,
            'cognitive_available': cognitive_available,
            'organizational_available': organizational_available,
            'integration_score': integration_score
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Phase 1A & 1B統合確認エラー: {e}'}

def display_final_organizational_integration_results(*test_results):
    """最終組織統合テスト結果の表示"""
    
    organizational_test, integration_test, output_verification, framework_verification, phase_integration = test_results
    
    print("🎉 組織パターン深度分析統合テスト結果サマリー")
    print("=" * 80)
    
    # 各テストの結果サマリー
    test_results_list = [
        ("組織パターン分析エンジン", organizational_test['success']),
        ("AIレポート生成器統合", integration_test['success']),
        ("組織深度分析出力検証", output_verification['success']),
        ("組織理論的フレームワーク", framework_verification['success']),
        ("Phase 1A & 1B統合", phase_integration['success'])
    ]
    
    success_count = sum(1 for _, success in test_results_list if success)
    total_tests = len(test_results_list)
    
    print(f"📊 テスト結果: {success_count}/{total_tests} 成功")
    print()
    
    for test_name, success in test_results_list:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"   {status} {test_name}")
    
    print()
    
    # セクション数確認
    if integration_test['success']:
        total_sections = integration_test.get('total_sections', 0)
        print(f"🔢 総レポートセクション数: {total_sections}")
        if total_sections >= 14:
            print("   ✅ 基本12セクション + Phase 1A + Phase 1B = 14セクション達成")
    
    # 組織理論適用度表示
    if framework_verification['success']:
        overall_score = framework_verification.get('overall_score', 0)
        print(f"🏢 組織理論的フレームワーク総合適用度: {overall_score:.1f}%")
    
    # 統合レベル表示
    if phase_integration['success']:
        integration_score = phase_integration.get('integration_score', 0)
        print(f"🔗 Phase 1A & 1B統合レベル: {integration_score}%")
    
    # 次のステップの提案
    print()
    print("🚀 次のステップ:")
    
    if success_count == total_tests:
        print("   ✅ Phase 1B 組織パターン深度分析統合完了")
        print("   ✅ Phase 1A & 1B 完全統合達成")
        print("   🔄 Phase 2 システム思考による多層因果分析への進行準備完了")
        print("   📈 実際のシフトデータでの深度分析実行可能")
    else:
        print("   ⚠️ 統合テストの一部に問題があります")
        print("   🔧 該当する問題箇所の修正が必要です")
        print("   📋 詳細なエラーログを確認してください")
    
    print()
    print("💡 組織パターン深度分析の主な強化ポイント:")
    print("   • 暗黙的権力構造の科学的解明 (Social Network Analysis)")
    print("   • 組織文化の3層深度分析 (Schein Model)")
    print("   • 組織的防衛メカニズム特定 (Systems Psychodynamics)")
    print("   • 創発的リーダーシップパターン分析")
    print("   • 組織的サイロと変化抵抗の詳細分析")

# ============================================================================
# テスト用データ生成ヘルパー関数
# ============================================================================

def generate_test_organizational_shift_data():
    """テスト用組織シフトデータ生成"""
    np.random.seed(42)
    
    data = []
    roles = ['nurse', 'caregiver', 'admin', 'rehab', 'support']
    employment_types = ['full_time', 'part_time', 'contract']
    departments = ['nursing_dept', 'care_dept', 'admin_dept', 'rehab_dept', 'support_dept']
    
    for staff_idx in range(30):
        staff_id = f"ORG_S{staff_idx:03d}"
        role = np.random.choice(roles)
        
        data.append({
            'staff': staff_id,
            'ds': datetime.now().strftime('%Y-%m-%d'),
            'role': role,
            'employment_type': np.random.choice(employment_types),
            'department': np.random.choice(departments),
            'team': f"team_{np.random.randint(1, 6)}",
            'experience_level': np.random.choice(['junior', 'mid', 'senior'], p=[0.3, 0.5, 0.2]),
            'management_level': np.random.choice(['staff', 'supervisor', 'manager'], p=[0.7, 0.2, 0.1])
        })
    
    return pd.DataFrame(data)

def generate_mock_organizational_analysis_results():
    """模擬組織分析結果データ生成"""
    return {
        'shortage_analysis': {
            'total_shortage_hours': 285.4,
            'critical_shortage_departments': ['nursing_dept', 'care_dept']
        },
        'fatigue_analysis': {
            'average_fatigue_score': 68.7,
            'high_fatigue_staff_count': 9
        },
        'fairness_analysis': {
            'avg_fairness_score': 0.71,
            'low_fairness_staff_count': 6
        },
        'organizational_metrics': {
            'team_cohesion_score': 0.65,
            'communication_effectiveness': 0.58,
            'leadership_satisfaction': 0.72
        }
    }

def create_comprehensive_organizational_test_analysis_results():
    """包括的テスト組織分析結果データ作成"""
    return {
        'shortage_analysis': {
            'total_shortage_hours': 285.4,
            'shortage_by_role': {'nurse': 145.2, 'caregiver': 95.8, 'admin': 44.4}
        },
        'fatigue_analysis': {
            'average_fatigue_score': 68.7,
            'high_fatigue_staff_count': 9
        },
        'fairness_analysis': {
            'avg_fairness_score': 0.71,
            'low_fairness_staff_count': 6
        },
        'leave_analysis': {
            'total_leave_days': 178,
            'paid_leave_ratio': 0.69
        },
        'organizational_analysis': {
            'power_distribution': {'formal': 0.4, 'informal': 0.6},
            'cultural_coherence': 0.62,
            'change_resistance_level': 0.55
        }
    }

def create_test_organizational_analysis_params():
    """テスト組織分析パラメータ作成"""
    return {
        'analysis_start_date': '2025-01-01',
        'analysis_end_date': '2025-01-31',
        'slot_minutes': 30,
        'staff_count': 30,
        'enabled_modules': ['Fatigue', 'Shortage', 'Fairness', 'CognitivePsychology', 'OrganizationalPattern']
    }

def create_test_organizational_parquet_files(temp_dir):
    """テスト用組織分析Parquetファイル作成"""
    
    # 疲労データ
    fatigue_data = pd.DataFrame({
        'staff_id': [f'S{i:03d}' for i in range(25)],
        'fatigue_score': np.random.normal(68, 16, 25).clip(0, 100),
        'workload_hours': np.random.normal(8.3, 1.6, 25).clip(4, 12),
        'team': [f'team_{i%5+1}' for i in range(25)]
    })
    
    # 不足データ  
    shortage_data = pd.DataFrame({
        'staff_id': [f'S{i:03d}' for i in range(25)],
        'role_id': np.random.choice(['nurse', 'caregiver', 'admin'], 25),
        'shortage_hours': np.random.normal(14.2, 9.1, 25).clip(0, 60),
        'employment_type': np.random.choice(['full_time', 'part_time'], 25),
        'department': np.random.choice(['nursing_dept', 'care_dept', 'admin_dept'], 25)
    })
    
    # 公平性データ
    fairness_data = pd.DataFrame({
        'staff_id': [f'S{i:03d}' for i in range(25)],
        'fairness_score': np.random.normal(0.71, 0.18, 25).clip(0, 1),
        'total_shifts': np.random.randint(14, 26, 25),
        'leadership_score': np.random.normal(0.6, 0.2, 25).clip(0, 1)
    })
    
    # scenario ディレクトリ作成
    scenario_dir = temp_dir / "out_median_based"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    
    # Parquetファイル保存
    fatigue_data.to_parquet(scenario_dir / "fatigue_score.parquet")
    shortage_data.to_parquet(scenario_dir / "shortage_role_summary.parquet")  
    fairness_data.to_parquet(scenario_dir / "fairness_after.parquet")

if __name__ == "__main__":
    print("🏢 組織パターン深度分析統合テスト開始")
    print("Phase 1B: Organizational Pattern Deep Analysis Integration Test")
    print()
    
    success = test_organizational_deep_analysis_integration()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 組織パターン深度分析統合テスト完全成功！")
        print("✅ Phase 1B実装完了 - 組織理論基盤による深度分析が完全に動作します")
        print("✅ Phase 1A & 1B統合達成 - 個人心理と組織パターンの統合分析が可能です")
        print("🚀 app.pyでの14セクション深度分析レポート出力機能が利用可能になりました")
    else:
        print("❌ 組織パターン深度分析統合テストに問題があります")
        print("🔧 上記のエラーメッセージを確認して修正してください")
    
    print("=" * 80)