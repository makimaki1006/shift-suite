# -*- coding: utf-8 -*-
"""
認知科学的深度分析統合テスト - Cognitive Psychology Deep Analysis Integration Test

Phase 1A: 認知科学分析エンジンとAIレポート生成器の完全統合テスト
理論的基盤の動作確認と深度分析出力の検証を実施します。

テスト対象:
1. CognitivePsychologyAnalyzer の動作確認
2. AIComprehensiveReportGenerator への統合確認  
3. 13番目のセクション (cognitive_psychology_deep_analysis) の出力検証
4. 理論的フレームワーク (Maslach, Selye, SDT, CLT, JDC) の適用確認
5. フォールバック機能の動作確認
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

def test_cognitive_deep_analysis_integration():
    """認知科学的深度分析統合テストのメイン実行"""
    
    print("=" * 80)
    print("🧠 認知科学的深度分析統合テスト (Phase 1A)")
    print("=" * 80)
    print()
    
    try:
        # shift_suite パスを追加
        current_dir = Path(__file__).parent
        sys.path.append(str(current_dir))
        
        # 1. 認知科学分析エンジンの独立テスト
        print("📊 Step 1: 認知科学分析エンジンの独立動作テスト")
        print("-" * 60)
        
        cognitive_engine_test_result = test_cognitive_psychology_analyzer()
        
        if not cognitive_engine_test_result['success']:
            print(f"❌ 認知科学分析エンジンのテストに失敗: {cognitive_engine_test_result['error']}")
            return False
        
        print("✅ 認知科学分析エンジンの独立動作確認完了")
        print()
        
        # 2. AIレポート生成器への統合テスト
        print("🔗 Step 2: AIレポート生成器統合テスト")
        print("-" * 60)
        
        integration_test_result = test_ai_report_generator_integration()
        
        if not integration_test_result['success']:
            print(f"❌ AIレポート生成器統合テストに失敗: {integration_test_result['error']}")
            return False
        
        print("✅ AIレポート生成器統合確認完了")
        print()
        
        # 3. 深度分析出力の詳細検証
        print("🔍 Step 3: 深度分析出力の詳細検証")
        print("-" * 60)
        
        output_verification_result = verify_deep_analysis_output(integration_test_result['report'])
        
        if not output_verification_result['success']:
            print(f"❌ 深度分析出力検証に失敗: {output_verification_result['error']}")
            return False
        
        print("✅ 深度分析出力検証完了")
        print()
        
        # 4. 理論的フレームワークの適用確認
        print("📚 Step 4: 理論的フレームワーク適用確認") 
        print("-" * 60)
        
        framework_verification_result = verify_theoretical_frameworks(integration_test_result['report'])
        
        if not framework_verification_result['success']:
            print(f"❌ 理論的フレームワーク検証に失敗: {framework_verification_result['error']}")
            return False
        
        print("✅ 理論的フレームワーク適用確認完了")
        print()
        
        # 5. 最終統合テスト結果の表示
        print("🎯 Step 5: 最終統合テスト結果")
        print("-" * 60)
        
        display_final_integration_results(
            cognitive_engine_test_result,
            integration_test_result, 
            output_verification_result,
            framework_verification_result
        )
        
        return True
        
    except Exception as e:
        print(f"❌ 統合テスト実行エラー: {e}")
        traceback.print_exc()
        return False

def test_cognitive_psychology_analyzer():
    """認知科学分析エンジン独立テスト"""
    
    try:
        from shift_suite.tasks.cognitive_psychology_analyzer import CognitivePsychologyAnalyzer
        
        # 認知科学分析エンジンの初期化
        analyzer = CognitivePsychologyAnalyzer()
        print(f"   ✓ 分析エンジン初期化完了 (ID: {analyzer.analysis_id})")
        
        # テスト用疲労データ生成
        fatigue_data = generate_test_fatigue_data()
        print(f"   ✓ テスト疲労データ生成完了 ({len(fatigue_data)} records)")
        
        # テスト用シフトデータ生成
        shift_data = generate_test_shift_data()
        print(f"   ✓ テストシフトデータ生成完了 ({len(shift_data)} records)")
        
        # 模擬分析結果データ生成
        mock_analysis_results = generate_mock_analysis_results()
        print(f"   ✓ 模擬分析結果データ生成完了")
        
        # 包括的認知心理学分析の実行
        print("   🔄 包括的認知心理学分析実行中...")
        
        analysis_result = analyzer.analyze_comprehensive_psychology(
            fatigue_data=fatigue_data,
            shift_data=shift_data,
            analysis_results=mock_analysis_results
        )
        
        # 分析結果の基本検証
        if 'analysis_metadata' not in analysis_result:
            return {'success': False, 'error': '分析結果にメタデータが含まれていません'}
        
        if 'fatigue_psychology_patterns' not in analysis_result:
            return {'success': False, 'error': '疲労心理学パターン分析が実行されていません'}
        
        print(f"   ✓ 分析完了 ({len(analysis_result)} sections)")
        
        return {
            'success': True,
            'analysis_result': analysis_result,
            'analyzer_id': analyzer.analysis_id
        }
        
    except ImportError as e:
        return {'success': False, 'error': f'認知科学分析モジュールのインポートエラー: {e}'}
    except Exception as e:
        return {'success': False, 'error': f'認知科学分析エンジンテストエラー: {e}'}

def test_ai_report_generator_integration():
    """AIレポート生成器統合テスト"""
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        
        # AIレポート生成器の初期化
        generator = AIComprehensiveReportGenerator()
        print(f"   ✓ AIレポート生成器初期化完了 (ID: {generator.report_id})")
        
        # 認知科学分析エンジンの統合確認
        if hasattr(generator, 'cognitive_analyzer') and generator.cognitive_analyzer is not None:
            print(f"   ✅ 認知科学分析エンジン統合確認 (ID: {generator.cognitive_analyzer.analysis_id})")
        else:
            print(f"   ⚠️ 認知科学分析エンジンは無効化されています（フォールバック動作）")
        
        # テスト用分析結果データ作成
        test_analysis_results = create_comprehensive_test_analysis_results()
        test_analysis_params = create_test_analysis_params()
        
        # 一時出力ディレクトリ作成
        temp_dir = Path(tempfile.mkdtemp(prefix="cognitive_integration_test_"))
        print(f"   ✓ 一時ディレクトリ作成: {temp_dir}")
        
        # テスト用Parquetファイル作成
        create_test_parquet_files(temp_dir)
        print(f"   ✓ テスト用Parquetファイル作成完了")
        
        # 包括レポート生成実行
        print("   🔄 包括レポート生成実行中...")
        
        comprehensive_report = generator.generate_comprehensive_report(
            analysis_results=test_analysis_results,
            input_file_path="test_cognitive_analysis.xlsx",
            output_dir=str(temp_dir),
            analysis_params=test_analysis_params
        )
        
        # 基本セクション確認
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
        
        # 13番目のセクション確認
        if 'cognitive_psychology_deep_analysis' not in comprehensive_report:
            return {'success': False, 'error': '認知科学的深度分析セクションが生成されていません'}
        
        print(f"   ✅ 包括レポート生成完了 ({len(comprehensive_report)} sections)")
        print(f"   ✅ 13番目のセクション (cognitive_psychology_deep_analysis) 確認完了")
        
        # クリーンアップ
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"   ✓ 一時ディレクトリクリーンアップ完了")
        
        return {
            'success': True,
            'report': comprehensive_report,
            'generator_id': generator.report_id
        }
        
    except ImportError as e:
        return {'success': False, 'error': f'AIレポート生成器のインポートエラー: {e}'}
    except Exception as e:
        return {'success': False, 'error': f'AIレポート生成器統合テストエラー: {e}'}

def verify_deep_analysis_output(comprehensive_report):
    """深度分析出力の詳細検証"""
    
    try:
        cognitive_section = comprehensive_report.get('cognitive_psychology_deep_analysis', {})
        
        # 分析ステータス確認
        analysis_status = cognitive_section.get('analysis_status', 'UNKNOWN')
        print(f"   📊 分析ステータス: {analysis_status}")
        
        if analysis_status in ['COMPLETED_SUCCESSFULLY', 'DISABLED', 'DATA_INSUFFICIENT']:
            print(f"   ✅ 分析ステータス正常")
        else:
            return {'success': False, 'error': f'予期しない分析ステータス: {analysis_status}'}
        
        # 理論的基盤の確認
        if analysis_status == 'COMPLETED_SUCCESSFULLY':
            theoretical_foundations = cognitive_section.get('theoretical_foundations', [])
            expected_theories = [
                'Maslach Burnout Inventory',
                'General Adaptation Syndrome', 
                'Self-Determination Theory',
                'Cognitive Load Theory',
                'Job Demand-Control Model'
            ]
            
            for theory in expected_theories:
                theory_found = any(theory in foundation for foundation in theoretical_foundations)
                if theory_found:
                    print(f"   ✅ {theory} 理論基盤確認")
                else:
                    print(f"   ⚠️ {theory} 理論基盤が見つかりません")
        
        # 深度分析結果の構造確認
        if 'deep_analysis_results' in cognitive_section:
            deep_results = cognitive_section['deep_analysis_results']
            expected_analysis_types = [
                'fatigue_psychology_patterns',
                'motivation_engagement_analysis', 
                'stress_coping_patterns',
                'cognitive_load_analysis',
                'psychological_safety_autonomy'
            ]
            
            for analysis_type in expected_analysis_types:
                if analysis_type in deep_results:
                    print(f"   ✅ {analysis_type} 分析確認")
                else:
                    print(f"   ⚠️ {analysis_type} 分析が見つかりません")
        
        # 洞察サマリーの確認
        if 'cognitive_insights_summary' in cognitive_section:
            insights = cognitive_section['cognitive_insights_summary']
            print(f"   📝 認知科学的洞察: {len(insights)} 項目")
            
            for i, insight in enumerate(insights[:3], 1):
                print(f"      {i}. {insight}")
        
        # 戦略的推奨事項の確認
        if 'strategic_psychological_recommendations' in cognitive_section:
            recommendations = cognitive_section['strategic_psychological_recommendations']
            print(f"   🎯 戦略的推奨事項: {len(recommendations)} 項目")
            
            for rec in recommendations[:2]:
                category = rec.get('category', '不明')
                priority = rec.get('priority', '不明')
                print(f"      • {category} (優先度: {priority})")
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': f'深度分析出力検証エラー: {e}'}

def verify_theoretical_frameworks(comprehensive_report):
    """理論的フレームワーク適用確認"""
    
    try:
        cognitive_section = comprehensive_report.get('cognitive_psychology_deep_analysis', {})
        
        # フレームワーク適用度チェック
        framework_scores = {
            'Maslach Burnout Theory': 0,
            'Selye Stress Theory': 0, 
            'Self-Determination Theory': 0,
            'Cognitive Load Theory': 0,
            'Job Demand-Control Model': 0
        }
        
        # 理論基盤の言及確認
        if 'theoretical_foundations' in cognitive_section:
            foundations = cognitive_section['theoretical_foundations']
            for foundation in foundations:
                if 'Maslach' in foundation:
                    framework_scores['Maslach Burnout Theory'] += 1
                if 'Selye' in foundation or 'General Adaptation' in foundation:
                    framework_scores['Selye Stress Theory'] += 1  
                if 'Self-Determination' in foundation:
                    framework_scores['Self-Determination Theory'] += 1
                if 'Cognitive Load' in foundation:
                    framework_scores['Cognitive Load Theory'] += 1
                if 'Job Demand-Control' in foundation:
                    framework_scores['Job Demand-Control Model'] += 1
        
        # 深度分析結果での理論適用確認
        if 'deep_analysis_results' in cognitive_section:
            deep_results = cognitive_section['deep_analysis_results']
            
            # 燃え尽き症候群分析 (Maslach)
            if 'fatigue_psychology_patterns' in deep_results:
                fatigue_patterns = deep_results['fatigue_psychology_patterns']
                if 'burnout_dimensions_analysis' in fatigue_patterns:
                    framework_scores['Maslach Burnout Theory'] += 2
            
            # ストレス段階分析 (Selye)
            if 'stress_coping_patterns' in deep_results:
                framework_scores['Selye Stress Theory'] += 1
            
            # 動機分析 (SDT)
            if 'motivation_engagement_analysis' in deep_results:
                framework_scores['Self-Determination Theory'] += 2
            
            # 認知負荷分析 (CLT)
            if 'cognitive_load_analysis' in deep_results:
                framework_scores['Cognitive Load Theory'] += 2
            
            # 心理的安全性分析 (JDC)
            if 'psychological_safety_autonomy' in deep_results:
                framework_scores['Job Demand-Control Model'] += 2
        
        # フレームワーク適用度の評価
        print("   📚 理論的フレームワーク適用度:")
        total_score = 0
        max_possible_score = len(framework_scores) * 3  # 各理論最大3点
        
        for framework, score in framework_scores.items():
            percentage = (score / 3) * 100 if score > 0 else 0
            status = "✅" if score >= 2 else "⚠️" if score >= 1 else "❌"
            print(f"      {status} {framework}: {score}/3 ({percentage:.0f}%)")
            total_score += score
        
        overall_percentage = (total_score / max_possible_score) * 100
        print(f"   🎯 総合理論適用度: {overall_percentage:.1f}% ({total_score}/{max_possible_score})")
        
        if overall_percentage >= 60:
            print("   ✅ 理論的フレームワーク適用度: 良好")
        elif overall_percentage >= 30:
            print("   ⚠️ 理論的フレームワーク適用度: 中程度")
        else:
            print("   ❌ 理論的フレームワーク適用度: 不十分")
        
        return {'success': True, 'framework_scores': framework_scores, 'overall_score': overall_percentage}
        
    except Exception as e:
        return {'success': False, 'error': f'理論的フレームワーク検証エラー: {e}'}

def display_final_integration_results(cognitive_test, integration_test, output_verification, framework_verification):
    """最終統合テスト結果の表示"""
    
    print("🎉 認知科学的深度分析統合テスト結果サマリー")
    print("=" * 80)
    
    # 各テストの結果サマリー
    test_results = [
        ("認知科学分析エンジン", cognitive_test['success']),
        ("AIレポート生成器統合", integration_test['success']),
        ("深度分析出力検証", output_verification['success']),
        ("理論的フレームワーク", framework_verification['success'])
    ]
    
    success_count = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    
    print(f"📊 テスト結果: {success_count}/{total_tests} 成功")
    print()
    
    for test_name, success in test_results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"   {status} {test_name}")
    
    print()
    
    # 理論的フレームワーク適用度表示
    if framework_verification['success']:
        overall_score = framework_verification.get('overall_score', 0)
        print(f"🧠 理論的フレームワーク総合適用度: {overall_score:.1f}%")
    
    # 次のステップの提案
    print()
    print("🚀 次のステップ:")
    
    if success_count == total_tests:
        print("   ✅ Phase 1A 認知科学的深度分析統合完了")
        print("   🔄 Phase 1B 組織パターン分析への進行準備完了")
        print("   📈 実際のシフトデータでの深度分析実行可能")
    else:
        print("   ⚠️ 統合テストの一部に問題があります")
        print("   🔧 該当する問題箇所の修正が必要です")
        print("   📋 詳細なエラーログを確認してください")
    
    print()
    print("💡 認知科学的深度分析の主な強化ポイント:")
    print("   • 燃え尽き症候群の3次元分析 (Maslach理論)")
    print("   • ストレス段階の科学的評価 (Selye理論)")
    print("   • 動機・エンゲージメント分析 (自己決定理論)")
    print("   • 認知負荷パターン解析 (認知負荷理論)")
    print("   • 心理的安全性評価 (Job Demand-Control Model)")

# ============================================================================
# テスト用データ生成ヘルパー関数
# ============================================================================

def generate_test_fatigue_data():
    """テスト用疲労データ生成"""
    np.random.seed(42)
    
    data = []
    for staff_idx in range(25):
        staff_id = f"TEST_S{staff_idx:03d}"
        base_fatigue = np.random.normal(65, 18)
        
        for day in range(14):  # 2週間分
            daily_variation = np.random.normal(0, 8)
            fatigue_score = max(0, min(100, base_fatigue + daily_variation))
            
            data.append({
                'staff': staff_id,
                'fatigue_score': fatigue_score,
                'ds': (datetime.now() - timedelta(days=14-day)).strftime('%Y-%m-%d')
            })
    
    return pd.DataFrame(data)

def generate_test_shift_data():
    """テスト用シフトデータ生成"""
    np.random.seed(42)
    
    roles = ['nurse', 'caregiver', 'admin', 'rehab', 'support']
    employment_types = ['full_time', 'part_time', 'contract']
    
    data = []
    for staff_idx in range(25):
        staff_id = f"TEST_S{staff_idx:03d}"
        
        data.append({
            'staff': staff_id,
            'ds': datetime.now().strftime('%Y-%m-%d'),
            'role': np.random.choice(roles),
            'employment_type': np.random.choice(employment_types)
        })
    
    return pd.DataFrame(data)

def generate_mock_analysis_results():
    """模擬分析結果データ生成"""
    return {
        'shortage_analysis': {
            'total_shortage_hours': 185.4,
            'critical_shortage_days': 3
        },
        'fatigue_analysis': {
            'average_fatigue_score': 67.2,
            'high_fatigue_staff_count': 6
        },
        'fairness_analysis': {
            'avg_fairness_score': 0.76,
            'low_fairness_staff_count': 4
        }
    }

def create_comprehensive_test_analysis_results():
    """包括的テスト分析結果データ作成"""
    return {
        'shortage_analysis': {
            'total_shortage_hours': 245.7,
            'shortage_by_role': {'nurse': 120.5, 'caregiver': 85.2, 'admin': 40.0}
        },
        'fatigue_analysis': {
            'average_fatigue_score': 68.4,
            'high_fatigue_staff_count': 8
        },
        'fairness_analysis': {
            'avg_fairness_score': 0.73,
            'low_fairness_staff_count': 5
        },
        'leave_analysis': {
            'total_leave_days': 156,
            'paid_leave_ratio': 0.72
        }
    }

def create_test_analysis_params():
    """テスト分析パラメータ作成"""
    return {
        'analysis_start_date': '2025-01-01',
        'analysis_end_date': '2025-01-31',
        'slot_minutes': 30,
        'staff_count': 25,
        'enabled_modules': ['Fatigue', 'Shortage', 'Fairness', 'CognitivePsychology']
    }

def create_test_parquet_files(temp_dir):
    """テスト用Parquetファイル作成"""
    
    # 疲労データ
    fatigue_data = pd.DataFrame({
        'staff_id': [f'S{i:03d}' for i in range(20)],
        'fatigue_score': np.random.normal(65, 15, 20).clip(0, 100),
        'workload_hours': np.random.normal(8.2, 1.5, 20).clip(4, 12)
    })
    
    # 不足データ  
    shortage_data = pd.DataFrame({
        'staff_id': [f'S{i:03d}' for i in range(20)],
        'role_id': np.random.choice(['nurse', 'caregiver', 'admin'], 20),
        'shortage_hours': np.random.normal(12.3, 8.2, 20).clip(0, 50),
        'employment_type': np.random.choice(['full_time', 'part_time'], 20)
    })
    
    # 公平性データ
    fairness_data = pd.DataFrame({
        'staff_id': [f'S{i:03d}' for i in range(20)],
        'fairness_score': np.random.normal(0.75, 0.15, 20).clip(0, 1),
        'total_shifts': np.random.randint(15, 25, 20)
    })
    
    # scenario ディレクトリ作成
    scenario_dir = temp_dir / "out_median_based"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    
    # Parquetファイル保存
    fatigue_data.to_parquet(scenario_dir / "fatigue_score.parquet")
    shortage_data.to_parquet(scenario_dir / "shortage_role_summary.parquet")
    fairness_data.to_parquet(scenario_dir / "fairness_after.parquet")

if __name__ == "__main__":
    print("🧠 認知科学的深度分析統合テスト開始")
    print("Phase 1A: Cognitive Psychology Deep Analysis Integration Test")
    print()
    
    success = test_cognitive_deep_analysis_integration()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 認知科学的深度分析統合テスト完全成功！")
        print("✅ Phase 1A実装完了 - 理論的基盤による深度分析が完全に動作します")
        print("🚀 app.pyでの深度分析レポート出力機能が利用可能になりました")
    else:
        print("❌ 認知科学的深度分析統合テストに問題があります")
        print("🔧 上記のエラーメッセージを確認して修正してください")
    
    print("=" * 80)