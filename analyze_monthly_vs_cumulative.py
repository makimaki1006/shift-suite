#!/usr/bin/env python3
"""
月別分析 vs 3ヶ月一気分析の比較
なぜ結果が異なるのか調査
"""

import os
from pathlib import Path

def analyze_zip_comparison():
    """ZIPファイル比較分析"""
    
    print("🔍 === 月別 vs 累積分析の比較調査 ===\n")
    
    zip_files = [
        "3か月一気に.zip",
        "7月分.zip", 
        "8月分.zip",
        "9月分.zip"
    ]
    
    print("【分析対象ファイル】")
    for zip_file in zip_files:
        zip_path = Path(zip_file)
        if zip_path.exists():
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {zip_file}: {size_mb:.1f}MB")
        else:
            print(f"  ❌ {zip_file}: ファイルが見つかりません")
    
    print("\n【予想される問題】")
    print("1. **Need計算の累積効果**")
    print("   - 月別: 各月独立でNeed計算")
    print("   - 3ヶ月: 全期間通してNeed計算 → 異なる基準値？")
    print("")
    
    print("2. **統計値の変化**")
    print("   - 中央値ベース: データ量が増えると中央値が変わる")
    print("   - 平均値ベース: 外れ値の影響が累積される")
    print("   - P25ベース: 分布の25%点が変化する")
    print("")
    
    print("3. **時間軸ベース分析の影響**")
    print("   - 短期間: パターンが明確")
    print("   - 長期間: 季節変動・トレンドが混入")
    print("")
    
    print("4. **休日・祝日処理の違い**")
    print("   - 月別: 各月の休日パターン")
    print("   - 3ヶ月: 長期間の休日パターン")
    print("")
    
    print("【期待される結果パターン】")
    print("✓ **加算性が成り立つ場合**:")
    print("  3ヶ月一気 ≈ 7月分 + 8月分 + 9月分")
    print("")
    print("❌ **加算性が成り立たない場合**:")
    print("  3ヶ月一気 ≠ 7月分 + 8月分 + 9月分")
    print("  → 分析ロジックに期間依存性がある")
    print("")
    
    print("【確認すべき要素】")
    print("1. 各分析の総不足時間")
    print("2. 職種別不足時間の内訳") 
    print("3. Need計算の基準値（中央値・平均値）")
    print("4. 対象日数・スロット数")
    print("5. 休日除外の適用状況")

if __name__ == "__main__":
    analyze_zip_comparison()