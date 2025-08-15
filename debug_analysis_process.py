#!/usr/bin/env python3
"""
分析プロセスのデバッグ
なぜ最新の分析で異常値が出るのか調査
"""

def debug_analysis_changes():
    """分析処理の変更点調査"""
    
    print("🔍 === 分析プロセス変更点の調査 ===\n")
    
    print("【正常だった時期】")
    print("- 7月25日: 総不足時間 373-670時間")
    print("- ファイル: temp_analysis_check/out_p25_based/")
    print("- アウトプット: 2025年07月25日15時10分_アウトプット.txt")
    print("")
    
    print("【異常値が出た時期】")
    print("- 7月30日: 総不足時間 48,972時間")
    print("- shortage_analysis.log: 15:58:19の記録")
    print("- 介護だけで17,482時間")
    print("")
    
    print("【考えられる変更点】")
    print("1. **データファイルの変更**")
    print("   - より大きなデータセット？")
    print("   - 複数月分のデータ？")
    print("   - データ構造の変更？")
    print("")
    
    print("2. **計算ロジックの変更**")
    print("   - shortage.pyの修正により計算方法が変わった？")
    print("   - スロット時間の設定が変わった？")
    print("   - 集計方法の変更？")
    print("")
    
    print("3. **設定の変更**")
    print("   - config.jsonの設定変更？")
    print("   - スロット時間設定の変更？")
    print("   - 分析対象期間の変更？")
    print("")
    
    print("【確認すべき項目】")
    print("✓ 使用したExcelファイルのサイズ・データ量")
    print("✓ スロット時間設定（15分？30分？60分？）")
    print("✓ 分析対象期間（1ヶ月？複数月？）")
    print("✓ shortage.pyの最近の変更履歴")
    print("✓ データの日付範囲・職種数・スタッフ数")

if __name__ == "__main__":
    debug_analysis_changes()