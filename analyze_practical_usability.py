#!/usr/bin/env python3
"""
問題5: 実用性向上 - 意思決定支援機能強化分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def analyze_practical_usability():
    """実用性・意思決定支援機能の不足問題を詳細分析"""
    
    print("=" * 80)
    print("問題5: 実用性向上 - 意思決定支援機能強化分析")
    print("=" * 80)
    
    # 1. 現在の出力形式・内容の分析
    print("\n【STEP 1: 現在の出力形式・内容分析】")
    
    # stats_summary.txt の内容確認
    stats_files = list(Path("extracted_results").rglob("stats_summary.txt"))
    
    if stats_files:
        print("現在の出力内容:")
        try:
            with open(stats_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')[:20]  # 最初の20行
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        except Exception as e:
            print(f"  読み込みエラー: {e}")
    else:
        print("stats_summary.txt ファイルが見つかりません")
    
    # 2. 意思決定に必要な情報の不足分析
    print("\n【STEP 2: 意思決定に必要な情報の不足分析】")
    
    decision_requirements = {
        "人員増減判断": [
            "どの職種を何人増員すべきか？",
            "増員の優先順位は？",
            "増員によるコスト効果は？"
        ],
        "シフト改善判断": [
            "どの時間帯の人員配置を変更すべきか？",
            "どの曜日が最も問題か？",
            "改善による効果予測は？"
        ],
        "予算計画判断": [
            "必要な追加人件費は？",
            "ROI（投資対効果）は？",
            "段階的改善プランの費用は？"
        ],
        "リスク管理判断": [
            "現在の不足レベルは緊急度何段階？",
            "放置した場合のリスクは？",
            "最低限必要な対策は？"
        ]
    }
    
    print("現在の出力で意思決定に必要な情報の不足:")
    for category, questions in decision_requirements.items():
        print(f"\n{category}:")
        for question in questions:
            print(f"  Q: {question}")
            print("    → 現在の出力からは判断不可")
    
    # 3. 現在の数値の実用性評価
    print("\n【STEP 3: 現在の数値の実用性評価】")
    
    if stats_files:
        try:
            with open(stats_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 不足時間の抽出
            total_shortage = None
            lines = content.split('\n')
            for line in lines:
                if 'lack_hours_total:' in line:
                    total_shortage = float(line.split(':')[1].strip())
                    break
            
            if total_shortage:
                print(f"現在の出力例: 全体不足時間 {total_shortage}時間")
                print("\n実用性の問題:")
                print(f"  Q: {total_shortage}時間の不足は危機的？許容範囲？")
                print(f"  Q: 何人増員すれば{total_shortage}時間の不足を解決できる？")
                print(f"  Q: {total_shortage}時間分の人件費はいくら？")
                print(f"  Q: 他施設と比較して多い？少ない？")
                print(f"  Q: 昨月・昨年と比較して改善？悪化？")
                
                # 簡易な実用性判断例を提示
                print(f"\n実用的な判断に必要な追加情報:")
                if total_shortage > 500:
                    print("  WARN 500時間超え → 緊急対応必要レベル")
                elif total_shortage > 200:
                    print("  WARN 200-500時間 → 早急改善推奨レベル")
                elif total_shortage > 50:
                    print("  WARN 50-200時間 → 計画的改善レベル")
                else:
                    print("  OK 50時間未満 → 許容範囲内")
                    
                print(f"  推定必要増員: {total_shortage / 160:.1f}人（月160時間勤務想定）")
                print(f"  推定追加人件費: {total_shortage * 2000:,.0f}円（時給2000円想定）")
                
        except Exception as e:
            print(f"分析エラー: {e}")
    
    # 4. 実用性・意思決定支援の不足問題特定
    print("\n【STEP 4: 実用性・意思決定支援の不足問題分析】")
    
    problems = [
        "NG 実用性A: 判断基準の欠如",
        "   - 373時間の不足が「危機的」か「許容範囲」か判定不可",
        "   - 業界標準・自施設過去データとの比較なし",
        "   - 緊急度・優先度の明確な基準なし",
        "",
        "NG 実用性B: 具体的行動指針の欠如", 
        "   - 「何を」「いつまでに」「どの程度」改善すべきか不明",
        "   - 増員数・配置変更の具体的提案なし",
        "   - 段階的改善プランの提示なし",
        "",
        "NG 実用性C: コスト・効果情報の欠如",
        "   - 改善に必要な追加人件費が不明",
        "   - 投資対効果（ROI）の試算なし",
        "   - 予算制約下での最適解提示なし",
        "",
        "NG 実用性D: 比較・トレンド情報の欠如",
        "   - 過去データとの比較（改善・悪化）なし",
        "   - 他部門・他施設との比較なし",
        "   - 季節変動・トレンド分析なし",
        "",
        "NG 実用性E: リスク・影響評価の欠如",
        "   - 不足継続時の業務影響評価なし",
        "   - 安全・品質リスクの定量評価なし",
        "   - 法的コンプライアンス影響の評価なし"
    ]
    
    for problem in problems:
        print(problem)
    
    # 5. 意思決定支援機能強化提案
    print("\n【STEP 5: 意思決定支援機能強化提案】")
    
    improvements = [
        "OK 改善A: 判断基準・レベル分け機能",
        "   - 5段階緊急度評価（緊急～良好）",
        "   - 業界標準比較スコア（偏差値形式）",
        "   - 自施設過去平均との比較（前年同月比等）",
        "",
        "OK 改善B: 具体的行動提案機能",
        "   - 推奨増員数・配置案の自動生成",
        "   - 優先改善職種・時間帯の明確化",
        "   - 段階的改善プラン（3ヶ月・6ヶ月・1年）",
        "",
        "OK 改善C: コスト・効果試算機能",
        "   - 改善策別コスト試算（人件費・研修費等）",
        "   - ROI計算（改善効果÷投資コスト）",
        "   - 予算制約条件での最適化提案",
        "",
        "OK 改善D: 比較・トレンド分析機能",
        "   - 時系列グラフによる改善・悪化の可視化",
        "   - ベンチマーク比較（同規模施設平均）",
        "   - 季節調整済み比較（季節要因除去）",
        "",
        "OK 改善E: リスク・影響評価機能",
        "   - 業務継続影響度評価（1-5段階）",
        "   - 安全・品質リスクスコア算出",
        "   - 法的コンプライアンス充足度評価"
    ]
    
    for improvement in improvements:
        print(improvement)
    
    # 6. 具体的な実装案
    print("\n【STEP 6: 意思決定支援機能の具体的実装案】")
    
    implementation_examples = [
        "1. 判断基準レベル分け例:",
        "   レベル5（緊急）: 月500時間超の不足 → 即時対応要",
        "   レベル4（重要）: 月300-500時間の不足 → 1ヶ月以内対応",
        "   レベル3（注意）: 月150-300時間の不足 → 3ヶ月以内対応",
        "   レベル2（軽微）: 月50-150時間の不足 → 6ヶ月以内対応",
        "   レベル1（良好）: 月50時間未満の不足 → 現状維持",
        "",
        "2. 行動提案出力例:",
        "   【緊急改善提案】",
        "   - 介護職2名増員（優先度★★★）",
        "   - 朝8:30-12:00の配置強化（効果大）",
        "   - 看護師1名増員（専門性要求）",
        "   - 予算制約下では介護職優先推奨",
        "",
        "3. コスト試算出力例:",
        "   【改善プラン別コスト試算】",
        "   プランA（フル改善）: 月120万円、効果100%",
        "   プランB（重点改善）: 月80万円、効果70%",
        "   プランC（最小改善）: 月40万円、効果40%",
        "   ROI: プランB最優（効果/コスト = 0.88）",
        "",
        "4. ダッシュボード表示例:",
        "   ┌─────────────────────┐",
        "   │ 人員不足状況 レベル4【重要】   │",
        "   │ 373時間/月（前月比+15%悪化）   │",
        "   │ 業界平均比: 偏差値45（やや不足）│",
        "   │ 推奨対応期限: 1ヶ月以内       │",
        "   └─────────────────────┘"
    ]
    
    for example in implementation_examples:
        print(example)
    
    print("\n" + "=" * 80)
    print("分析完了: 問題5 - 実用性向上・意思決定支援機能強化")
    print("総括: 過不足分析ロジック5問題の完全分析終了")
    print("=" * 80)

if __name__ == "__main__":
    analyze_practical_usability()