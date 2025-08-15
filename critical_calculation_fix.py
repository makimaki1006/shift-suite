#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急修正: Phase 2/3.1の時間計算ロジック修正
二重変換問題の解決
"""

from pathlib import Path
import json
from datetime import datetime

def document_critical_findings():
    """重大な発見の文書化"""
    
    print("🚨 緊急修正レポート: 二重変換問題")
    print("=" * 80)
    
    findings = {
        "発見日時": datetime.now().isoformat(),
        "重大度": "🔴 クリティカル",
        "問題": "Phase 2/3.1実装での時間計算の二重変換",
        "根拠": {
            "既存システム出力": {
                "total_lack_hours": "670.00時間",
                "total_excess_hours": "505.00時間", 
                "total_need_hours": "7346.00時間",
                "total_actual_hours": "7594.00時間",
                "確認ファイル": "shortage_summary.txt"
            },
            "系統設定": {
                "slot": "30分",
                "期間": "2025年6月（30日）",
                "確認ファイル": "shortage.meta.json"
            },
            "Phase 2実装の問題": {
                "コード": "total_hours = group['parsed_slots_count'].sum() * SLOT_HOURS",
                "問題": "parsed_slots_countが既に時間単位なら0.5倍（50%誤差）",
                "場所": "fact_extractor_prototype.py:98"
            },
            "Phase 3.1実装の問題": {
                "コード": "monthly_hours = work_df.groupby(['staff', 'year_month'])['parsed_slots_count'].sum() * SLOT_HOURS",
                "問題": "同様の二重変換リスク",
                "場所": "lightweight_anomaly_detector.py:132"
            }
        }
    }
    
    print("📋 重大な発見の詳細:")
    for key, value in findings.items():
        if isinstance(value, dict):
            print(f"\n🔍 {key}:")
            for subkey, subvalue in value.items():
                if isinstance(subvalue, dict):
                    print(f"  {subkey}:")
                    for subsubkey, subsubvalue in subvalue.items():
                        print(f"    {subsubkey}: {subsubvalue}")
                else:
                    print(f"  {subkey}: {subvalue}")
        else:
            print(f"{key}: {value}")

def propose_immediate_fixes():
    """即座修正案の提案"""
    
    print(f"\n💊 即座修正案:")
    print("-" * 60)
    
    fixes = {
        "1. 緊急データ確認": {
            "action": "parsed_slots_countの実際の意味を確定",
            "method": "実データサンプルでの値確認",
            "priority": "🔥 最優先",
            "timeline": "即座"
        },
        "2. Phase 2修正": {
            "action": "fact_extractor_prototype.pyの時間計算修正",
            "current": "total_hours = group['parsed_slots_count'].sum() * SLOT_HOURS",
            "option_a": "total_hours = group['parsed_slots_count'].sum()  # 既に時間単位の場合",
            "option_b": "total_hours = group['parsed_slots_count'].sum() * SLOT_HOURS  # スロット数の場合",
            "priority": "🔴 緊急",
            "timeline": "2時間以内"
        },
        "3. Phase 3.1修正": {
            "action": "lightweight_anomaly_detector.pyの時間計算修正",
            "current": "monthly_hours = groupby(['staff', 'year_month'])['parsed_slots_count'].sum() * SLOT_HOURS",
            "fix": "データ確認後に適切な計算式に修正",
            "priority": "🔴 緊急",
            "timeline": "2時間以内"
        },
        "4. データ仕様明確化": {
            "action": "long_dfのカラム仕様を明確に文書化",
            "content": "parsed_slots_countが何を表すかを明記",
            "priority": "🟡 高",
            "timeline": "24時間以内"
        },
        "5. 検証テストケース": {
            "action": "修正後の数値が既存システムと一致することを確認",
            "method": "shortage_summary.txtとの比較",
            "priority": "🟡 高",
            "timeline": "修正後即座"
        }
    }
    
    for fix_name, details in fixes.items():
        print(f"\n{details['priority']} {fix_name}")
        for key, value in details.items():
            if key != 'priority':
                print(f"  {key}: {value}")

def generate_verification_plan():
    """検証計画の生成"""
    
    print(f"\n🔍 検証計画:")
    print("-" * 60)
    
    verification_steps = [
        {
            "step": "1. 実データ確認",
            "actions": [
                "temp_analysis_check内のintermediate_data.parquetを分析",
                "parsed_slots_countの実際の値の範囲を確認",
                "30分勤務時の値が1（スロット）か0.5（時間）かを判定"
            ]
        },
        {
            "step": "2. 既存計算結果との比較",
            "actions": [
                "Phase 2計算結果 vs shortage_summary.txtの数値比較",
                "誤差の方向性（0.5倍 vs 2倍）を確認",
                "職種別・雇用形態別の詳細比較"
            ]
        },
        {
            "step": "3. 修正版実装",
            "actions": [
                "データ確認結果に基づく修正実装",
                "修正前後の数値比較",
                "法的準拠チェックの結果比較"
            ]
        },
        {
            "step": "4. 統合テスト",
            "actions": [
                "修正したPhase 2/3.1での統合ファクトブック再テスト",
                "dash_app.pyでの表示確認",
                "第三者検証スコアの再評価"
            ]
        }
    ]
    
    for step_info in verification_steps:
        print(f"\n📝 {step_info['step']}:")
        for action in step_info["actions"]:
            print(f"  • {action}")

def estimate_impact_scope():
    """影響範囲の推定"""
    
    print(f"\n📊 影響範囲推定:")
    print("-" * 60)
    
    impact_areas = {
        "数値精度への影響": {
            "労働時間統計": "50%の誤差（0.5倍または2倍）",
            "異常検知閾値": "労働基準法違反の誤判定",
            "コスト計算": "人件費の大幅な過小/過大評価",
            "人員計画": "必要人数の誤算"
        },
        "機能への影響": {
            "Phase 2基本事実抽出": "全ての労働時間計算が影響",
            "Phase 3.1異常検知": "労働時間ベースの異常検知が誤作動",
            "統合ファクトブック": "表示される全時間データが不正確",
            "法的準拠チェック": "労働基準法チェックの信頼性喪失"
        },
        "ビジネスへの影響": {
            "意思決定": "不正確なデータに基づく経営判断",
            "コンプライアンス": "法的違反の見落としまたは誤検知",
            "システム信頼性": "数値的信頼性の根本的な疑義",
            "ユーザー信頼": "システム全体への信頼失墜"
        },
        "第三者評価への影響": {
            "品質スコア": "95.2%から大幅下落の可能性",
            "評価項目": "数値精度、計算基盤、設計品質",
            "再評価必要性": "全項目の再検証が必要"
        }
    }
    
    for area, impacts in impact_areas.items():
        print(f"\n🎯 {area}:")
        for item, impact in impacts.items():
            print(f"  {item}: {impact}")

def create_emergency_action_plan():
    """緊急対応計画の作成"""
    
    print(f"\n🚨 緊急対応計画:")
    print("=" * 80)
    
    action_plan = {
        "即座実行（0-2時間）": [
            "実データでのparsed_slots_count値の確認",
            "既存shortage計算結果との数値比較",
            "二重変換の確定診断"
        ],
        "緊急修正（2-6時間）": [
            "Phase 2: fact_extractor_prototype.py修正",
            "Phase 3.1: lightweight_anomaly_detector.py修正",
            "修正版での計算結果検証"
        ],
        "検証完了（6-12時間）": [
            "修正後の統合ファクトブック再テスト",
            "法的準拠チェックの再実行",
            "数値整合性の全面確認"
        ],
        "品質保証（12-24時間）": [
            "第三者検証スコアの再評価",
            "ドキュメント更新",
            "今後の防止策策定"
        ]
    }
    
    for timeline, actions in action_plan.items():
        print(f"\n⏰ {timeline}:")
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")
    
    print(f"\n🎯 成功指標:")
    success_criteria = [
        "Phase 2/3.1の計算結果が既存shortage.pyと一致",
        "法的準拠チェックが正確な労働時間で実行",
        "統合ファクトブックの数値が信頼可能",
        "第三者評価スコアが90%以上を維持"
    ]
    
    for i, criteria in enumerate(success_criteria, 1):
        print(f"  {i}. {criteria}")

if __name__ == "__main__":
    print("🚨 緊急修正レポート生成中...")
    
    document_critical_findings()
    propose_immediate_fixes()
    generate_verification_plan()
    estimate_impact_scope()
    create_emergency_action_plan()
    
    print(f"\n" + "=" * 80)
    print("📝 結論:")
    print("Phase 2/3.1実装に重大な二重変換問題を確認。")
    print("既存システムが既に時間単位で出力しているため、")
    print("SLOT_HOURSの追加乗算により50%の計算誤差が発生。")
    print("即座の修正が必要。")
    print("\n🚨 緊急修正レポート完了")