#!/usr/bin/env python3
"""
介護業界の現状を考慮した過不足分析ロジック総合評価
法定基準は満たすが「なんとなくの不足感」を数値化する手法の妥当性分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def industry_context_enhanced_analysis():
    """介護業界の実情を踏まえた過不足分析の総合評価"""
    
    print("=" * 80)
    print("介護業界現状考慮: 過不足分析ロジック総合評価")
    print("=" * 80)
    
    # 1. 介護業界の特殊事情の整理
    print("\n【STEP 1: 介護業界の特殊事情】")
    
    industry_context = {
        "法定基準の限界": [
            "介護保険法の人員配置基準は「最低限」の基準",
            "実際の業務量・利用者ニーズはそれを上回る",
            "法定基準 = 安全・安心な介護とは限らない"
        ],
        "なんとなくの不足感の実態": [
            "現場職員の体感的な忙しさ・負荷感",
            "利用者対応の質的な余裕の不足",
            "緊急時・イレギュラー対応への不安",
            "職員の疲労・離職リスクの高まり"
        ],
        "言語化の困難": [
            "定量化しにくい「ケアの質」",
            "職員個人の経験・感覚に依存",
            "施設ごとの利用者特性の違い"
        ]
    }
    
    for category, items in industry_context.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")
    
    # 2. 現在の統計手法（平均・中央値・25%ile）の妥当性評価
    print("\n【STEP 2: 統計手法の妥当性評価】")
    
    # 実データで各統計手法の結果を比較
    stats_results = {}
    methods = ['mean', 'median', 'p25']
    
    for method in methods:
        stats_file = Path(f"extracted_results/out_{method}_based/stats_summary.txt")
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for line in content.split('\n'):
                    if 'lack_hours_total:' in line:
                        stats_results[method] = float(line.split(':')[1].strip())
                        break
            except Exception as e:
                print(f"{method}データ読み込みエラー: {e}")
    
    print("3統計手法の結果比較:")
    for method, value in stats_results.items():
        method_name = {
            'mean': '平均値',
            'median': '中央値', 
            'p25': '25パーセンタイル'
        }[method]
        print(f"  {method_name}: {value}時間")
    
    if len(stats_results) >= 2:
        values = list(stats_results.values())
        print(f"\n統計手法間の差異:")
        print(f"  最大差: {max(values) - min(values):.1f}時間")
        print(f"  変動係数: {np.std(values) / np.mean(values) * 100:.1f}%")
        
        if max(values) - min(values) < 10:
            print("  → 手法間差異は小さく、どの手法も妥当")
        else:
            print("  → 手法間差異が大きく、手法選択が重要")
    
    # 3. 「なんとなくの基準値」数値化アプローチの評価
    print("\n【STEP 3: なんとなくの基準値数値化アプローチ評価】")
    
    current_approach_pros = [
        "OK 実績データベース: 過去の勤務実績から客観的に算出",
        "OK 曜日特性反映: 月～日曜の業務量差を考慮",
        "OK 時間帯特性反映: 朝昼夕の忙しさの違いを考慮",
        "OK 統計的安定性: 外れ値の影響を軽減（25%ile使用）",
        "OK 法定基準+α: 最低基準を上回る現実的な必要人員"
    ]
    
    current_approach_cons = [
        "NG 主観的要素欠如: 職員の体感的負荷を反映しない",
        "NG 利用者特性無視: 重症度・認知症レベルの個体差未考慮",
        "NG 業務内容差無視: ケア業務とその他業務の区別なし",
        "NG ピーク対応力不足: 緊急時・イレギュラー対応の余裕なし",
        "NG 質的評価欠如: ケアの質・職員満足度の観点なし"
    ]
    
    print("現在のアプローチの長所:")
    for pro in current_approach_pros:
        print(f"  {pro}")
    
    print("\n現在のアプローチの課題:")
    for con in current_approach_cons:
        print(f"  {con}")
    
    # 4. 介護業界特化型改善提案
    print("\n【STEP 4: 介護業界特化型改善提案】")
    
    industry_specific_improvements = [
        "OK 改善1: ケア密度係数の導入",
        "   - 利用者要介護度別の必要ケア時間データベース",
        "   - 認知症レベル別の見守り・対応時間係数",
        "   - 医療的ケア必要者の専門対応時間",
        "",
        "OK 改善2: 職員負荷感センサー",
        "   - 定期的な職員アンケート（5段階負荷評価）",
        "   - 負荷感スコアと数値的不足の相関分析",
        "   - 主観的不足感の客観的指標への変換",
        "",
        "OK 改善3: 緊急対応余裕率",
        "   - 通常業務に加えて緊急対応用の余裕人員",
        "   - 過去の緊急事態頻度データから余裕率算出",
        "   - 時間帯別・曜日別の緊急対応確率反映",
        "",
        "OK 改善4: ケア品質保証人員",
        "   - 最低限ケア vs 理想的ケアの人員差",
        "   - 利用者・家族満足度と人員配置の関係分析",
        "   - 品質向上のための追加人員算定",
        "",
        "OK 改善5: 法定基準+現実ギャップ分析",
        "   - 法定最低人員 vs 実際必要人員の定量比較",
        "   - 地域・施設規模別の現実的基準値設定",
        "   - 段階的改善目標の設定（法定+10%, +20%, +30%等）"
    ]
    
    for improvement in industry_specific_improvements:
        print(improvement)
    
    # 5. 実装可能性の評価
    print("\n【STEP 5: 実装可能性の評価】")
    
    # 現在の373時間不足を例とした実用性分析
    if stats_results:
        avg_shortage = np.mean(list(stats_results.values()))
        
        print(f"現在の不足時間（平均）: {avg_shortage:.1f}時間/月")
        
        # 介護業界視点での評価
        monthly_working_hours = 160  # 月間労働時間
        hourly_wage = 1800  # 介護職平均時給
        
        needed_staff = avg_shortage / monthly_working_hours
        monthly_cost = avg_shortage * hourly_wage
        
        print(f"\n介護業界視点での実用性評価:")
        print(f"  必要増員数: {needed_staff:.1f}人")
        print(f"  月間追加人件費: {monthly_cost:,.0f}円")
        print(f"  年間追加人件費: {monthly_cost * 12:,.0f}円")
        
        # 法定基準との比較（仮想的な計算）
        legal_minimum_hours = 30 * 8 * 3  # 30日×8時間×3人（仮想的最低配置）
        current_total_hours = legal_minimum_hours + avg_shortage
        shortage_rate = (avg_shortage / legal_minimum_hours) * 100
        
        print(f"  法定基準比不足率: {shortage_rate:.1f}%")
        
        if shortage_rate > 50:
            urgency = "緊急"
        elif shortage_rate > 30:
            urgency = "重要"
        elif shortage_rate > 15:
            urgency = "要注意"
        else:
            urgency = "軽微"
            
        print(f"  介護業界基準緊急度: 【{urgency}】")
    
    # 6. 最終総合評価
    print("\n【STEP 6: 最終総合評価】")
    
    final_assessment = [
        "■ 現在のアプローチの総合評価: B+ (良好、改善余地あり)",
        "",
        "【評価根拠】",
        "✓ 優秀な点:",
        "  - 実績ベースの客観的算出（恣意性排除）",
        "  - 曜日・時間帯特性の適切な反映",
        "  - 統計的手法による安定した結果",
        "  - 法定基準を上回る現実的な人員算定",
        "",
        "⚠️ 改善点:",
        "  - 職員の主観的負荷感との乖離可能性",
        "  - 利用者個別特性（要介護度等）の未反映",
        "  - 緊急時対応余裕の未考慮",
        "  - ケアの質的側面の評価不足",
        "",
        "■ 推奨改善方向:",
        "1. 現在の数値的アプローチを基盤として維持",
        "2. 職員負荷感調査との相関分析を追加",
        "3. 利用者特性別のケア密度係数を段階導入",
        "4. 緊急対応余裕率の検討・試算",
        "",
        "■ 結論:",
        "「なんとなくの不足感」を数値化する現在のアプローチは",
        "介護業界の実情に適した合理的な手法である。",
        "完璧ではないが、実用的で改善可能な基盤として評価できる。"
    ]
    
    for assessment in final_assessment:
        print(assessment)
    
    print("\n" + "=" * 80)
    print("分析完了: 介護業界現状考慮・過不足分析ロジック総合評価")
    print("=" * 80)

if __name__ == "__main__":
    industry_context_enhanced_analysis()