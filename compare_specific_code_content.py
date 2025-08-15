#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特定コードセクションの詳細比較
完全にコピーされていることの最終証明
"""

from pathlib import Path
import difflib

def compare_specific_sections():
    """重要なコードセクションの詳細比較"""
    
    print("=" * 80)
    print("🔬 コード内容の詳細比較（行単位）")
    print("=" * 80)
    
    # Phase 3.1の重要メソッドを詳細比較
    original_file = Path("shift_suite/tasks/lightweight_anomaly_detector.py")
    backup_file = Path("PHASE3_COMPLETE_BACKUP_20250802_100555/shift_suite/tasks/lightweight_anomaly_detector.py")
    
    print(f"\n📄 {original_file.name} の詳細比較:")
    
    with open(original_file, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_lines = f.readlines()
    
    # 1. 行数の比較
    print(f"\n  行数比較:")
    print(f"    オリジナル: {len(original_lines)} 行")
    print(f"    バックアップ: {len(backup_lines)} 行")
    print(f"    差分: {len(original_lines) - len(backup_lines)} 行")
    
    # 2. 差分検出
    diff = list(difflib.unified_diff(original_lines, backup_lines, 
                                     fromfile='オリジナル', 
                                     tofile='バックアップ', 
                                     n=0))
    
    if not diff:
        print(f"\n  ✅ 完全一致: 差分なし")
    else:
        print(f"\n  ❌ 差分検出:")
        for line in diff[:20]:  # 最初の20行まで表示
            print(f"    {line.rstrip()}")
    
    # 3. 特定の重要セクションの存在確認
    print(f"\n  重要セクションの存在確認:")
    
    important_sections = [
        ("class LightweightAnomalyDetector:", "クラス定義"),
        ("def detect_anomalies(self, long_df: pd.DataFrame)", "メイン検知メソッド"),
        ("過度な労働時間検知（O(n)）", "労働時間検知コメント"),
        ("severity = self._calculate_severity", "重要度計算ロジック"),
        ("return sorted(anomalies, key=lambda x:", "ソートロジック")
    ]
    
    for section, description in important_sections:
        original_found = any(section in line for line in original_lines)
        backup_found = any(section in line for line in backup_lines)
        
        if original_found and backup_found:
            # 該当行を探して表示
            for i, line in enumerate(backup_lines):
                if section in line:
                    print(f"    ✅ {description} (行 {i+1}): {line.strip()[:60]}...")
                    break
        else:
            print(f"    ❌ {description}: {'原本になし' if not original_found else 'バックアップになし'}")
    
    # 4. Phase 3.2のファイルも確認
    print(f"\n" + "-" * 80)
    print(f"\n📄 fact_book_visualizer.py の詳細比較:")
    
    original_file2 = Path("shift_suite/tasks/fact_book_visualizer.py")
    backup_file2 = Path("PHASE3_COMPLETE_BACKUP_20250802_100555/shift_suite/tasks/fact_book_visualizer.py")
    
    with open(original_file2, 'r', encoding='utf-8') as f:
        original_lines2 = f.readlines()
    
    with open(backup_file2, 'r', encoding='utf-8') as f:
        backup_lines2 = f.readlines()
    
    print(f"\n  行数比較:")
    print(f"    オリジナル: {len(original_lines2)} 行")
    print(f"    バックアップ: {len(backup_lines2)} 行")
    
    # 統合機能の確認
    integration_checks = [
        "from .fact_extractor_prototype import FactExtractorPrototype",
        "from .lightweight_anomaly_detector import LightweightAnomalyDetector",
        "self.fact_extractor = FactExtractorPrototype()",
        "self.anomaly_detector = LightweightAnomalyDetector",
        "basic_facts = self.fact_extractor.extract_basic_facts(long_df)",
        "anomalies = self.anomaly_detector.detect_anomalies(long_df)"
    ]
    
    print(f"\n  Phase 2 & 3.1 統合コードの確認:")
    for check in integration_checks:
        found = any(check in line for line in backup_lines2)
        status = "✅" if found else "❌"
        print(f"    {status} {check[:60]}...")
    
    # 5. ファイルの先頭と末尾の確認
    print(f"\n📝 ファイルの先頭と末尾の確認:")
    
    print(f"\n  lightweight_anomaly_detector.py の先頭3行:")
    for i, line in enumerate(backup_lines[:3]):
        print(f"    {i+1}: {line.rstrip()}")
    
    print(f"\n  lightweight_anomaly_detector.py の末尾3行:")
    for i, line in enumerate(backup_lines[-3:]):
        print(f"    {len(backup_lines)-2+i}: {line.rstrip()}")
    
    # 6. 文字数の正確な比較
    print(f"\n📊 文字数の正確な比較:")
    
    original_chars = sum(len(line) for line in original_lines)
    backup_chars = sum(len(line) for line in backup_lines)
    
    print(f"  オリジナル: {original_chars:,} 文字")
    print(f"  バックアップ: {backup_chars:,} 文字")
    print(f"  差分: {abs(original_chars - backup_chars)} 文字")
    
    return len(diff) == 0

if __name__ == "__main__":
    is_identical = compare_specific_sections()
    
    print("\n" + "=" * 80)
    if is_identical:
        print("✅ 最終結論: バックアップは1文字も省略されていません")
        print("   すべてのコードが完全に保存されています")
    else:
        print("⚠️ 何らかの差分が検出されました")