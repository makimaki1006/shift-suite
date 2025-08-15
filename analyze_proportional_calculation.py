#!/usr/bin/env python3
"""
問題3: 按分計算非現実性修正 - 職種間労働密度差反映分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def analyze_proportional_calculation():
    """按分計算の非現実性問題を詳細分析"""
    
    print("=" * 80)
    print("問題3: 按分計算非現実性修正 - 職種間労働密度差分析")
    print("=" * 80)
    
    # 1. 現在の按分計算ロジック分析
    print("\n【STEP 1: 現在の按分計算ロジック分析】")
    
    print("現在の按分計算式:")
    print("  職種不足時間 = 全体不足時間 × (職種レコード数 / 全レコード数)")
    print("  雇用不足時間 = 全体不足時間 × (雇用レコード数 / 全レコード数)")
    print("")
    print("基本仮定:")
    print("  - 全職種の労働密度が等しい")
    print("  - 全雇用形態の労働密度が等しい")
    print("  - 時間帯による需要差なし")
    print("  - スキル・専門性の違いなし")
    
    # 2. 実データで按分計算の結果を確認
    print("\n【STEP 2: 実データでの按分計算結果確認】")
    
    # stats_summary.txt の分析
    stats_files = list(Path("extracted_results").rglob("stats_summary.txt"))
    
    if stats_files:
        for stats_file in stats_files[:3]:
            try:
                print(f"\n分析対象: {stats_file}")
                
                with open(stats_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 全体不足時間を抽出
                lines = content.split('\n')
                total_shortage = None
                role_shortages = {}
                employment_shortages = {}
                
                for line in lines:
                    if 'lack_hours_total:' in line:
                        total_shortage = float(line.split(':')[1].strip())
                    elif line.startswith('  - ') and '不足時間:' in line:
                        parts = line.split('不足時間:')
                        if len(parts) == 2:
                            name = parts[0].replace('  - ', '').strip()
                            hours = float(parts[1].replace('時間', '').strip())
                            
                            # 職種か雇用形態かを判別（簡易）
                            if any(keyword in name for keyword in ['介護', '看護', '事務', '運転', '機能', '管理', '施設']):
                                role_shortages[name] = hours
                            else:
                                employment_shortages[name] = hours
                
                if total_shortage:
                    print(f"全体不足時間: {total_shortage}時間")
                    
                    if role_shortages:
                        print("\n職種別不足時間:")
                        role_total = sum(role_shortages.values())
                        for role, hours in role_shortages.items():
                            percentage = (hours / total_shortage) * 100
                            print(f"  {role}: {hours:.1f}時間 ({percentage:.1f}%)")
                        print(f"  職種別合計: {role_total:.1f}時間")
                        
                        # 按分比率の妥当性分析
                        print(f"  按分精度: {abs(role_total - total_shortage):.1f}時間差")
                    
                    if employment_shortages:
                        print("\n雇用形態別不足時間:")
                        employment_total = sum(employment_shortages.values())
                        for employment, hours in employment_shortages.items():
                            percentage = (hours / total_shortage) * 100
                            print(f"  {employment}: {hours:.1f}時間 ({percentage:.1f}%)")
                        print(f"  雇用別合計: {employment_total:.1f}時間")
                        print(f"  按分精度: {abs(employment_total - total_shortage):.1f}時間差")
                        
            except Exception as e:
                print(f"  分析エラー: {e}")
    else:
        print("stats_summary.txt ファイルが見つかりません")
    
    # 3. heatmap.meta.json から職種・雇用形態情報を取得
    print("\n【STEP 3: 職種・雇用形態の実態分析】")
    
    meta_files = list(Path("extracted_results").rglob("heatmap.meta.json"))
    if meta_files:
        try:
            with open(meta_files[0], 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            roles = meta_data.get('roles', [])
            employments = meta_data.get('employments', [])
            leave_stats = meta_data.get('leave_statistics', {})
            
            print(f"登録職種数: {len(roles)}")
            print("職種一覧:")
            for role in roles:
                print(f"  - {role}")
                
            print(f"\n登録雇用形態数: {len(employments)}")
            print("雇用形態一覧:")
            for employment in employments:
                print(f"  - {employment}")
            
            if leave_stats:
                total_records = leave_stats.get('total_records', 0)
                print(f"\n総レコード数: {total_records:,}件")
                
                holiday_breakdown = leave_stats.get('holiday_type_breakdown', {})
                if holiday_breakdown:
                    print("勤務タイプ別レコード数:")
                    for holiday_type, count in holiday_breakdown.items():
                        percentage = (count / total_records) * 100
                        print(f"  {holiday_type}: {count:,}件 ({percentage:.1f}%)")
                        
        except Exception as e:
            print(f"メタデータ分析エラー: {e}")
    
    # 4. 按分計算の非現実性問題特定
    print("\n【STEP 4: 按分計算の非現実性問題分析】")
    
    problems = [
        "NG 非現実A: 職種間労働密度の無視",
        "   - 介護職と事務職の1時間あたり業務量は大きく異なる",
        "   - 看護師と運転士では専門性・責任レベルが違う",
        "   - 単純な人数比例では現実的でない",
        "",
        "NG 非現実B: 時間帯別需要パターンの無視", 
        "   - 朝の忙しい時間帯と昼間では必要人員が異なる",
        "   - 職種により活動時間帯が違う（看護師vs運転士）",
        "   - 一律按分では時間軸の実態を反映できない",
        "",
        "NG 非現実C: スキル代替性の無視",
        "   - 介護職は相互代替可能だが、看護師は代替不可",
        "   - 専門職（機能訓練士）は特定時間のみ必要",
        "   - 按分計算では代替性を考慮できない",
        "",
        "NG 非現実D: 法定配置基準の無視",
        "   - 介護保険法による人員配置基準あり",
        "   - 看護師配置は利用者数との比率で決まる",
        "   - 按分計算は法的要件を反映しない",
        "",
        "NG 非現実E: 労働生産性の個人差無視",
        "   - 正社員とパートでは稼働時間・責任が違う",
        "   - スポット職員は限定的な業務のみ",
        "   - 雇用形態按分は生産性差を無視"
    ]
    
    for problem in problems:
        print(problem)
    
    # 5. 現実的な按分計算改善提案
    print("\n【STEP 5: 現実的な按分計算改善提案】")
    
    improvements = [
        "OK 改善A: 職種別労働密度係数導入",
        "   - 職種別標準作業時間データベース構築",
        "   - 業務量調査による密度係数設定",
        "   - 密度係数 × 人数 による現実的按分",
        "",
        "OK 改善B: 時間帯別需要ウェイト",
        "   - heatmap.meta.jsonの時間帯別needパターン活用",
        "   - 職種×時間帯のマトリックス按分",
        "   - ピーク時間の需要集中を反映",
        "",
        "OK 改善C: スキル代替マトリックス",
        "   - 職種間代替可能性マトリックス",
        "   - 専門職の独立性考慮",
        "   - 柔軟性スコアによる按分調整",
        "",
        "OK 改善D: 法定基準準拠按分",
        "   - 介護保険法配置基準をベースライン",
        "   - 法定最小人員 + 超過分按分",
        "   - コンプライアンス保証型按分",
        "",
        "OK 改善E: 雇用形態別生産性係数",
        "   - 正社員=1.0, パート=0.7, スポット=0.5 等",
        "   - 実働時間・責任レベル反映",
        "   - 実効労働力ベース按分"
    ]
    
    for improvement in improvements:
        print(improvement)
    
    # 6. 具体的実装案
    print("\n【STEP 6: 現実的按分計算の具体的実装案】")
    
    implementation_examples = [
        "1. 職種別密度係数例:",
        "   介護職: 1.0 (基準)",
        "   看護師: 1.5 (高度専門性)",
        "   事務職: 0.6 (間接業務)",
        "   運転士: 0.8 (特定時間集中)",
        "   機能訓練士: 2.0 (専門性・希少性)",
        "",
        "2. 時間帯ウェイト例:",
        "   08:00-12:00: 1.5 (朝の忙しい時間)",
        "   12:00-16:00: 1.0 (標準時間)",
        "   16:00-18:00: 1.2 (夕方忙しい時間)",
        "",
        "3. 新按分計算式:",
        "   職種不足 = 全体不足 × (職種人数 × 密度係数 × 時間ウェイト) / 総加重人数",
        "",
        "4. 検証メカニズム:",
        "   - 按分結果の合計 = 全体不足時間（誤差1%以内）",
        "   - 法定最小人員確保チェック",
        "   - 現実性スコア（専門家評価）"
    ]
    
    for example in implementation_examples:
        print(example)
    
    print("\n" + "=" * 80)
    print("分析完了: 問題3 - 按分計算非現実性修正")
    print("次段階: 職種間労働密度差を反映した按分システム実装")
    print("=" * 80)

if __name__ == "__main__":
    analyze_proportional_calculation()