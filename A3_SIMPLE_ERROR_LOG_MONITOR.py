#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3.1.2 簡易エラーログ監視
軽量版Phase 2/3.1エラー検知
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

def scan_error_logs():
    """エラーログ簡易スキャン"""
    
    print("🚨 A3.1.2 エラーログ監視システム開始")
    print("🎯 Phase 2/3.1関連エラーの検知")
    print("=" * 60)
    
    # 重要エラーパターン
    critical_patterns = [
        (r"SLOT_HOURS.*(?:not.*defined|undefined)", "SLOT_HOURS未定義"),
        (r"FactExtractorPrototype.*(?:Error|Exception)", "Phase 2エラー"),
        (r"LightweightAnomalyDetector.*(?:Error|Exception)", "Phase 3.1エラー"),
        (r"(?:CRITICAL|FATAL).*(?:Phase|SLOT)", "システム重大エラー"),
        (r"parsed_slots_count.*already.*hours", "重複変換コメント")
    ]
    
    # ログファイル検索
    log_files = [
        "./analysis_log.log",
        "./shift_suite.log", 
        "./shortage_analysis.log",
        "./shortage_dashboard.log"
    ]
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "files_scanned": 0,
        "total_errors": 0,
        "critical_errors": [],
        "status": "healthy"
    }
    
    print("📁 ログファイルスキャン...")
    
    for log_file in log_files:
        path = Path(log_file)
        if not path.exists():
            continue
            
        try:
            results["files_scanned"] += 1
            print(f"  📄 {path.name}: ", end="")
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            file_errors = 0
            for pattern, description in critical_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    file_errors += len(matches)
                    results["critical_errors"].append({
                        "file": str(path),
                        "pattern": description,
                        "matches": len(matches)
                    })
            
            if file_errors > 0:
                print(f"⚠️ {file_errors}件エラー")
                results["total_errors"] += file_errors
                results["status"] = "warning"
            else:
                print("✅ 正常")
                
        except Exception as e:
            print(f"❌ 読み込みエラー: {e}")
    
    # Phase 2/3.1専用ファイル確認
    print("\n🔍 Phase 2/3.1ファイル確認...")
    phase_files = [
        "shift_suite/tasks/fact_extractor_prototype.py",
        "shift_suite/tasks/lightweight_anomaly_detector.py"
    ]
    
    for phase_file in phase_files:
        path = Path(phase_file)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 不正コメント確認
                if "parsed_slots_count is already in hours" in content:
                    results["critical_errors"].append({
                        "file": phase_file,
                        "pattern": "不正コメント残存",
                        "matches": 1
                    })
                    results["status"] = "error"
                    print(f"  ❌ {path.name}: 不正コメント検出")
                else:
                    print(f"  ✅ {path.name}: 正常")
                    
            except Exception as e:
                print(f"  ❌ {path.name}: {e}")
    
    # 結果保存
    monitoring_dir = Path("logs/monitoring")
    monitoring_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = monitoring_dir / f"error_log_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # レポート表示
    print("\n" + "=" * 60)
    print("📋 エラー監視レポート")
    print("=" * 60)
    
    status_icon = {"healthy": "🟢", "warning": "🟡", "error": "🔴"}.get(results["status"], "❓")
    
    print(f"""
🔍 **A3.1.2 エラーログ監視結果**
実行日時: {results['timestamp']}
ステータス: {status_icon} {results['status'].upper()}

📊 **スキャン結果**
- ファイル数: {results['files_scanned']}件
- エラー総数: {results['total_errors']}件

🎯 **検出エラー詳細**""")
    
    if results["critical_errors"]:
        for error in results["critical_errors"]:
            print(f"- {error['file']}: {error['pattern']} ({error['matches']}件)")
    else:
        print("- エラー検出なし ✅")
    
    print(f"""
💡 **推奨アクション**""")
    
    if results["status"] == "error":
        print("""🚨 即座対応が必要:
  1. 検出されたエラーの修正
  2. Phase 2/3.1ファイルの確認
  3. システム動作の検証""")
    elif results["status"] == "warning":
        print("""⚠️ 注意が必要:
  1. 警告内容の詳細確認
  2. 予防的対策の検討
  3. 継続監視の強化""")
    else:
        print("""✅ 正常稼働中:
  1. A3.1.3 パフォーマンス監視へ進行
  2. 継続的監視の維持
  3. 定期チェックの実施""")
    
    print(f"\n📁 結果保存: {result_file}")
    print(f"🎯 A3.1.2 エラーログ監視: {'✅ 完了' if results['status'] != 'error' else '❌ 要対応'}")
    
    return results["status"] != "error"

if __name__ == "__main__":
    try:
        success = scan_error_logs()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 監視システムエラー: {e}")
        exit(1)