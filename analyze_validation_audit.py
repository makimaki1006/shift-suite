#!/usr/bin/env python3
"""
問題4: 検証・監査機能追加 - 逆算検証機能実装分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def analyze_validation_audit():
    """検証・監査機能の不足問題を詳細分析"""
    
    print("=" * 80)
    print("問題4: 検証・監査機能追加 - 逆算検証機能分析")
    print("=" * 80)
    
    # 1. 現在の検証機能の有無確認
    print("\n【STEP 1: 現在の検証機能調査】")
    
    print("現在の検証機能:")
    print("  OK データ形状チェック（行数・列数）")
    print("  OK 基本統計値出力（合計・平均等）")
    print("  NG 逆算検証機能")
    print("  NG 一貫性チェック機能")
    print("  NG 異常値検出機能")
    print("  NG 手計算との照合機能")
    print("  NG 監査ログ出力")
    
    print("\n検証不足により発生するリスク:")
    print("  - 計算ミスの発見遅れ")
    print("  - データ処理エラーの見落とし")
    print("  - 結果の信頼性低下")
    print("  - トレーサビリティの欠如")
    
    # 2. 実データで基本的な整合性をチェック
    print("\n【STEP 2: 実データでの整合性確認】")
    
    stats_files = list(Path("extracted_results").rglob("stats_summary.txt"))
    
    if stats_files:
        for stats_file in stats_files[:3]:
            try:
                print(f"\n分析対象: {stats_file}")
                
                with open(stats_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 基本数値を抽出
                lines = content.split('\n')
                total_shortage = None
                total_excess = None
                individual_totals = []
                
                for line in lines:
                    if 'lack_hours_total:' in line:
                        total_shortage = float(line.split(':')[1].strip())
                    elif 'excess_hours_total:' in line:
                        total_excess = float(line.split(':')[1].strip())
                    elif line.startswith('  - ') and ('不足時間:' in line or '過剰時間:' in line):
                        if '不足時間:' in line:
                            hours_str = line.split('不足時間:')[1].replace('時間', '').strip()
                        else:
                            hours_str = line.split('過剰時間:')[1].replace('時間', '').strip()
                        try:
                            individual_totals.append(float(hours_str))
                        except:
                            pass
                
                # 基本整合性チェック実行
                print("基本整合性チェック:")
                
                if total_shortage is not None:
                    print(f"  全体不足時間: {total_shortage}時間")
                    
                    if individual_totals:
                        individual_sum = sum(individual_totals)
                        print(f"  個別合計時間: {individual_sum:.1f}時間")
                        difference = abs(total_shortage - individual_sum)
                        print(f"  差異: {difference:.1f}時間")
                        
                        if difference < 0.1:
                            print("  OK 整合性: OK")
                        elif difference < 1.0:
                            print("  WARN 整合性: 軽微な差異あり")
                        else:
                            print("  ERROR 整合性: 重大な差異あり")
                    else:
                        print("  UNKNOWN 整合性: 個別データ不足で検証不可")
                        
                if total_excess is not None:
                    print(f"  全体過剰時間: {total_excess}時間")
                        
            except Exception as e:
                print(f"  分析エラー: {e}")
    else:
        print("stats_summary.txt ファイルが見つかりません")
    
    # 3. parquetファイルレベルでの検証
    print("\n【STEP 3: parquetファイルレベル検証】")
    
    parquet_files = list(Path("extracted_results").rglob("*.parquet"))
    parquet_counts = {}
    
    for pf in parquet_files[:10]:  # 最初の10ファイルを確認
        try:
            df = pd.read_parquet(pf)
            parquet_counts[pf.name] = {
                'shape': df.shape,
                'non_zero_count': (df != 0).sum().sum(),
                'total_sum': df.sum().sum()
            }
        except Exception as e:
            parquet_counts[pf.name] = {'error': str(e)}
    
    print("parquetファイル検証結果:")
    for filename, info in parquet_counts.items():
        print(f"  {filename}:")
        if 'error' in info:
            print(f"    ERROR: {info['error']}")
        else:
            print(f"    形状: {info['shape']}")
            print(f"    非ゼロ値数: {info['non_zero_count']:,}")
            print(f"    総和: {info['total_sum']:.1f}")
    
    # 4. 検証・監査機能不足の問題点特定
    print("\n【STEP 4: 検証・監査機能不足の問題分析】")
    
    problems = [
        "NG 検証不足A: 逆算検証機能の欠如",
        "   - 最終結果から元データを逆算する機能なし",
        "   - 計算過程の妥当性を確認できない",
        "   - エラーの早期発見が困難",
        "",
        "NG 検証不足B: 一貫性チェック機能の欠如",
        "   - 複数データ間の整合性確認なし",
        "   - 時系列データの連続性チェックなし",
        "   - 職種別・期間別の一貫性未確認",
        "",
        "NG 検証不足C: 異常値検出機能の欠如",
        "   - 統計的外れ値の自動検出なし",
        "   - ビジネスルール違反の検出なし",
        "   - 急激な変化の警告なし",
        "",
        "NG 検証不足D: 手計算照合機能の欠如",
        "   - 簡単な手計算例での確認機能なし",
        "   - サンプルデータでの動作確認なし",
        "   - 理論値との比較機能なし",
        "",
        "NG 検証不足E: 監査ログ・トレース機能の欠如",
        "   - 計算過程の詳細記録なし",
        "   - パラメータ変更履歴の記録なし",
        "   - 監査証跡の生成なし"
    ]
    
    for problem in problems:
        print(problem)
    
    # 5. 検証・監査機能強化提案
    print("\n【STEP 5: 検証・監査機能強化提案】")
    
    improvements = [
        "OK 改善A: 多段階逆算検証システム",
        "   - Level 1: 基本合計チェック（総和=個別和）",
        "   - Level 2: 按分精度チェック（按分後合計=元合計）",
        "   - Level 3: 時間軸整合チェック（日別×時間=総計）",
        "",
        "OK 改善B: 自動一貫性チェックシステム",
        "   - 職種別データの論理的整合性",
        "   - 期間別データの連続性確認",
        "   - 統計手法間の結果比較",
        "",
        "OK 改善C: 統計的異常値検出システム",
        "   - 3σ法による外れ値検出",
        "   - IQRベース異常値検出",
        "   - 前期比較による急変検出",
        "",
        "OK 改善D: 手計算照合・サンプル検証",
        "   - 簡単な手計算例での動作確認",
        "   - 既知データでの期待値比較",
        "   - ユニットテスト的検証機能",
        "",
        "OK 改善E: 包括的監査ログシステム",
        "   - 全計算過程の詳細ログ記録",
        "   - パラメータ・設定値の履歴管理",
        "   - JSON形式監査証跡生成"
    ]
    
    for improvement in improvements:
        print(improvement)
    
    # 6. 具体的実装案
    print("\n【STEP 6: 検証・監査機能の具体的実装案】")
    
    implementation_examples = [
        "1. 逆算検証関数例:",
        "   def reverse_validation(final_result, source_data):",
        "       # 最終結果から逆算して元データとの整合性確認",
        "       calculated_total = sum(final_result.values())",
        "       expected_total = source_data.total_shortage",
        "       return abs(calculated_total - expected_total) < 0.01",
        "",
        "2. 一貫性チェック例:",
        "   def consistency_check(role_data, employment_data, total):",
        "       role_sum = sum(role_data.values())",
        "       employment_sum = sum(employment_data.values())", 
        "       return all([",
        "           abs(role_sum - total) < 0.01,",
        "           abs(employment_sum - total) < 0.01",
        "       ])",
        "",
        "3. 監査ログ出力例:",
        "   audit_log = {",
        "       'timestamp': '2025-01-01T10:00:00Z',",
        "       'calculation_method': 'proportional',",
        "       'input_parameters': {...},",
        "       'validation_results': {...},",
        "       'anomalies_detected': [...],",
        "       'confidence_score': 0.95",
        "   }",
        "",
        "4. 異常値検出例:",
        "   def detect_anomalies(daily_shortages):",
        "       mean = daily_shortages.mean()",
        "       std = daily_shortages.std()",
        "       threshold = mean + 3 * std",
        "       return daily_shortages[daily_shortages > threshold]"
    ]
    
    for example in implementation_examples:
        print(example)
    
    print("\n" + "=" * 80)
    print("分析完了: 問題4 - 検証・監査機能追加")
    print("次段階: 逆算検証機能を含む包括的監査システム実装")
    print("=" * 80)

if __name__ == "__main__":
    analyze_validation_audit()