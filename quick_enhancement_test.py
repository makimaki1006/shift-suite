#!/usr/bin/env python3
"""
実行可能制約強化システムの簡単なテスト
"""

import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def test_enhancement_system():
    """制約強化システムの基本テスト"""
    log.info("実行可能制約強化システム基本テスト開始")
    
    # サンプル制約
    sample_constraint = {
        'type': 'staff_count_constraint',
        'rule': '日勤時間帯には最低2名の職員を配置する',
        'confidence': 0.8,
        'category': 'staffing'
    }
    
    # 強化処理のシミュレーション
    enhanced_constraint = enhance_constraint(sample_constraint)
    
    log.info("=== 元の制約 ===")
    log.info(f"タイプ: {sample_constraint['type']}")
    log.info(f"ルール: {sample_constraint['rule']}")
    log.info(f"信頼度: {sample_constraint['confidence']}")
    
    log.info("\n=== 強化後の制約 ===")
    log.info(f"実行可能性スコア: {enhanced_constraint['actionability_score']:.2f}")
    log.info(f"IF条件: {enhanced_constraint['execution_rule']['condition']}")
    log.info(f"THEN行動: {enhanced_constraint['execution_rule']['action']}")
    log.info(f"例外処理: {enhanced_constraint['execution_rule']['exception']}")
    log.info(f"最小値: {enhanced_constraint['quantified_criteria']['minimum_value']}")
    log.info(f"最大値: {enhanced_constraint['quantified_criteria']['maximum_value']}")
    log.info(f"検証方法: {enhanced_constraint['verification_method']['method']}")
    
    return enhanced_constraint


def enhance_constraint(constraint):
    """制約の強化処理"""
    enhanced = constraint.copy()
    
    # IF-THENルールの追加
    enhanced['execution_rule'] = {
        'condition': f"シフト時間帯に配置される職員数が基準値を下回る場合",
        'action': f"最低限必要な職員数を確保する",
        'exception': f"緊急時は一時的な基準緩和を許可"
    }
    
    # 数値基準の明確化
    enhanced['quantified_criteria'] = {
        'minimum_value': 2,
        'maximum_value': 10,
        'confidence_level': 'high' if constraint.get('confidence', 0) > 0.8 else 'medium'
    }
    
    # 実行可能性スコアの計算
    score = 0.0
    score += 0.3  # IF-THENルール存在
    score += 0.25  # 数値基準明確
    score += 0.2  # 制約タイプ具体性
    score += constraint.get('confidence', 0) * 0.15  # 信頼度
    score += 0.1  # 検証可能性
    
    enhanced['actionability_score'] = min(1.0, score)
    
    # 検証方法の追加
    enhanced['verification_method'] = {
        'method': 'スタッフ配置数の自動カウント',
        'frequency': 'リアルタイム',
        'metrics': '配置人数, 職種別カウント'
    }
    
    # 優先度の設定
    enhanced['priority'] = 'high' if enhanced['actionability_score'] >= 0.8 else 'medium'
    
    return enhanced


def main():
    """メイン実行"""
    try:
        enhanced_constraint = test_enhancement_system()
        
        # 結果保存
        result = {
            'test_result': enhanced_constraint,
            'test_timestamp': datetime.now().isoformat(),
            'success': True
        }
        
        with open('quick_enhancement_test_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        log.info("\n✅ 制約強化システム基本テスト完了")
        log.info("結果をquick_enhancement_test_result.jsonに保存しました")
        
    except Exception as e:
        log.error(f"テストエラー: {e}")


if __name__ == "__main__":
    main()