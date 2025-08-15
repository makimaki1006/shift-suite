# -*- coding: utf-8 -*-
"""
認知科学的深度分析の簡易動作確認テスト
WSL環境でも実行可能な基本的な統合確認
"""

import sys
import os
from pathlib import Path

def test_basic_imports():
    """基本的なインポートテスト"""
    
    print("🧠 認知科学的深度分析 - 基本動作確認テスト")
    print("=" * 60)
    print()
    
    try:
        # shift_suite パスを追加
        current_dir = Path(__file__).parent
        sys.path.append(str(current_dir))
        
        # 1. 認知科学分析エンジンのインポートテスト
        print("📊 Step 1: 認知科学分析エンジン インポートテスト")
        try:
            from shift_suite.tasks.cognitive_psychology_analyzer import CognitivePsychologyAnalyzer
            print("   ✅ CognitivePsychologyAnalyzer インポート成功")
            
            # 基本初期化テスト
            analyzer = CognitivePsychologyAnalyzer()
            print(f"   ✅ 分析エンジン初期化成功 (ID: {analyzer.analysis_id})")
            
            # 基本メソッドの存在確認
            required_methods = [
                'analyze_comprehensive_psychology',
                '_analyze_fatigue_psychology_patterns',
                '_analyze_motivation_engagement',
                '_analyze_stress_coping_patterns',
                '_analyze_cognitive_load_patterns',
                '_analyze_psychological_safety_autonomy'
            ]
            
            for method_name in required_methods:
                if hasattr(analyzer, method_name):
                    print(f"   ✅ {method_name} メソッド確認")
                else:
                    print(f"   ❌ {method_name} メソッドが見つかりません")
            
        except ImportError as e:
            print(f"   ❌ 認知科学分析エンジンインポートエラー: {e}")
            return False
        except Exception as e:
            print(f"   ❌ 認知科学分析エンジン初期化エラー: {e}")
            return False
        
        print()
        
        # 2. AIレポート生成器の統合確認
        print("🔗 Step 2: AIレポート生成器統合確認")
        try:
            from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator, COGNITIVE_ANALYSIS_AVAILABLE
            print("   ✅ AIComprehensiveReportGenerator インポート成功")
            
            print(f"   📊 認知科学分析利用可能性: {COGNITIVE_ANALYSIS_AVAILABLE}")
            
            # 基本初期化テスト
            generator = AIComprehensiveReportGenerator()
            print(f"   ✅ AIレポート生成器初期化成功 (ID: {generator.report_id})")
            
            # 認知科学分析エンジンの統合確認
            if hasattr(generator, 'cognitive_analyzer'):
                if generator.cognitive_analyzer is not None:
                    print(f"   ✅ 認知科学分析エンジン統合成功")
                    print(f"   📋 統合エンジンID: {generator.cognitive_analyzer.analysis_id}")
                else:
                    print(f"   ⚠️ 認知科学分析エンジンは無効化されています")
            else:
                print(f"   ❌ 認知科学分析エンジン統合属性が見つかりません")
            
            # 新しいメソッドの存在確認
            cognitive_methods = [
                '_generate_cognitive_psychology_deep_analysis',
                '_prepare_cognitive_analysis_data',
                '_enhance_cognitive_analysis_results',
                '_generate_fallback_cognitive_insights'
            ]
            
            for method_name in cognitive_methods:
                if hasattr(generator, method_name):
                    print(f"   ✅ {method_name} メソッド確認")
                else:
                    print(f"   ❌ {method_name} メソッドが見つかりません")
            
        except ImportError as e:
            print(f"   ❌ AIレポート生成器インポートエラー: {e}")
            return False
        except Exception as e:
            print(f"   ❌ AIレポート生成器初期化エラー: {e}")
            return False
        
        print()
        
        # 3. 理論的フレームワークの確認
        print("📚 Step 3: 理論的フレームワーク確認")
        
        # 燃え尽きの閾値設定確認
        if hasattr(analyzer, 'burnout_thresholds'):
            thresholds = analyzer.burnout_thresholds
            print(f"   ✅ Maslach燃え尽き症候群閾値設定: {len(thresholds)} 項目")
            for threshold_name, value in thresholds.items():
                print(f"      • {threshold_name}: {value}")
        
        # ストレス段階境界確認
        if hasattr(analyzer, 'stress_phase_boundaries'):
            boundaries = analyzer.stress_phase_boundaries
            print(f"   ✅ Selye ストレス段階境界設定: {len(boundaries)} 項目")
            for boundary_name, value in boundaries.items():
                print(f"      • {boundary_name}: {value}")
        
        print()
        
        # 4. 統合状態の確認
        print("🎯 Step 4: 統合状態確認")
        
        integration_status = {
            'cognitive_analyzer_available': COGNITIVE_ANALYSIS_AVAILABLE,
            'generator_has_cognitive_analyzer': hasattr(generator, 'cognitive_analyzer'),
            'cognitive_analyzer_initialized': generator.cognitive_analyzer is not None if hasattr(generator, 'cognitive_analyzer') else False,
            'theoretical_frameworks_configured': hasattr(analyzer, 'burnout_thresholds') and hasattr(analyzer, 'stress_phase_boundaries')
        }
        
        success_count = sum(1 for status in integration_status.values() if status)
        total_checks = len(integration_status)
        
        print(f"   📊 統合状態: {success_count}/{total_checks} 成功")
        
        for check_name, status in integration_status.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {check_name}")
        
        print()
        
        # 5. 最終確認
        print("🏁 最終確認")
        
        if success_count == total_checks:
            print("   🎉 認知科学的深度分析統合 - 完全成功！")
            print("   ✅ Phase 1A実装完了")
            print("   🚀 深度分析機能がapp.pyで利用可能です")
            
            print()
            print("   💡 利用可能な深度分析機能:")
            print("      • 燃え尽き症候群の3次元分析 (Maslach理論)")
            print("      • ストレス蓄積段階分析 (Selye理論)")
            print("      • 動機・エンゲージメント分析 (自己決定理論)")  
            print("      • 認知負荷パターン分析 (認知負荷理論)")
            print("      • 心理的安全性・自律性分析 (Job Demand-Control)")
            
            return True
        else:
            print("   ⚠️ 一部の統合に問題があります")
            print("   🔧 Windows環境での完全テストを推奨します")
            return False
        
    except Exception as e:
        print(f"❌ 基本テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_imports()
    
    print()
    print("=" * 60)
    if success:
        print("🎊 認知科学的深度分析 基本統合テスト成功！")
        print("📋 次のステップ: Windows環境での完全テスト実行")
    else:
        print("🔧 統合に問題があります。詳細を確認してください。")
    print("=" * 60)