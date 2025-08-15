#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3.1.2 エラーログ監視システム
Phase 2/3.1関連エラーの専門的検知・分析
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ErrorPattern:
    """エラーパターン定義"""
    pattern: str
    severity: str
    category: str
    description: str

class ErrorLogMonitor:
    """Phase 2/3.1専門エラーログ監視"""
    
    def __init__(self):
        self.monitoring_dir = Path("logs/monitoring")
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        # Phase 2/3.1専門エラーパターン
        self.error_patterns = [
            # SLOT_HOURS関連
            ErrorPattern(
                r"SLOT_HOURS.*(?:not.*defined|undefined|NameError)",
                "critical",
                "calculation",
                "SLOT_HOURS定数未定義エラー"
            ),
            ErrorPattern(
                r"parsed_slots_count.*(?:already.*hours|double.*conversion)",
                "warning", 
                "calculation",
                "不正な重複変換コメント検出"
            ),
            
            # Phase 2特有エラー
            ErrorPattern(
                r"FactExtractorPrototype.*(?:Error|Exception|Failed)",
                "error",
                "phase2",
                "Phase 2ファクト抽出エラー"
            ),
            ErrorPattern(
                r"fact_extractor.*(?:import.*error|module.*not.*found)",
                "critical",
                "phase2",
                "Phase 2モジュールインポートエラー"
            ),
            
            # Phase 3.1特有エラー
            ErrorPattern(
                r"LightweightAnomalyDetector.*(?:Error|Exception|Failed)",
                "error",
                "phase31",
                "Phase 3.1異常検知エラー"
            ),
            ErrorPattern(
                r"anomaly_detector.*(?:import.*error|module.*not.*found)",
                "critical",
                "phase31",
                "Phase 3.1モジュールインポートエラー"
            ),
            
            # 統合・データフロー関連
            ErrorPattern(
                r"FactBookVisualizer.*(?:Error|Exception|Failed)",
                "error",
                "integration",
                "統合可視化エラー"
            ),
            ErrorPattern(
                r"dash_fact_book.*(?:Error|Exception|Failed)",
                "error",
                "integration",
                "Dash統合エラー"
            ),
            
            # 数値計算関連
            ErrorPattern(
                r"(?:ValueError|TypeError).*(?:hours|slots|calculation)",
                "error",
                "calculation",
                "数値計算型エラー"
            ),
            ErrorPattern(
                r"(?:670|shortage).*(?:mismatch|inconsistent|error)",
                "warning",
                "calculation",
                "基準値不整合警告"
            ),
            
            # システム全般
            ErrorPattern(
                r"(?:CRITICAL|FATAL).*(?:Phase|SLOT|hours)",
                "critical",
                "system",
                "システム重大エラー"
            ),
            ErrorPattern(
                r"(?:ImportError|ModuleNotFoundError).*(?:shift_suite|tasks)",
                "critical",
                "system",
                "重要モジュール不在エラー"
            )
        ]
    
    def find_log_files(self) -> List[Path]:
        """ログファイル検索"""
        
        log_locations = [
            "logs",
            ".",
            "shift_suite",
            "temp_analysis_check"
        ]
        
        log_files = []
        
        for location in log_locations:
            location_path = Path(location)
            if location_path.exists():
                # .logファイル
                log_files.extend(location_path.glob("*.log"))
                # .txtファイル（エラー出力）
                log_files.extend(location_path.glob("*error*.txt"))
                # サブディレクトリの.logファイル
                log_files.extend(location_path.glob("**/*.log"))
        
        # 重複除去・存在確認
        unique_files = []
        for file_path in log_files:
            if file_path.exists() and file_path not in unique_files:
                unique_files.append(file_path)
        
        return unique_files
    
    def scan_log_file(self, file_path: Path, hours_back: int = 24) -> Dict[str, Any]:
        """単一ログファイルスキャン"""
        
        results = {
            "file": str(file_path),
            "size_bytes": 0,
            "lines_scanned": 0,
            "errors_found": [],
            "status": "ok"
        }
        
        try:
            stat = file_path.stat()
            results["size_bytes"] = stat.st_size
            results["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # ファイルが大きすぎる場合は末尾から読む
            if stat.st_size > 10 * 1024 * 1024:  # 10MB以上
                with open(file_path, 'rb') as f:
                    f.seek(-1024*1024, 2)  # 最後の1MBのみ
                    content = f.read().decode('utf-8', errors='ignore')
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            lines = content.splitlines()
            results["lines_scanned"] = len(lines)
            
            # 時刻フィルタリング（可能な場合）
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for line_num, line in enumerate(lines, 1):
                # エラーパターンマッチング
                for pattern in self.error_patterns:
                    if re.search(pattern.pattern, line, re.IGNORECASE):
                        error_entry = {
                            "line_number": line_num,
                            "content": line.strip()[:200],  # 最初の200文字
                            "pattern": pattern.pattern,
                            "severity": pattern.severity,
                            "category": pattern.category,
                            "description": pattern.description,
                            "timestamp": self.extract_timestamp(line)
                        }
                        results["errors_found"].append(error_entry)
                        
                        if pattern.severity in ["critical", "error"]:
                            results["status"] = pattern.severity
            
        except Exception as e:
            results["error"] = str(e)
            results["status"] = "error"
        
        return results
    
    def extract_timestamp(self, line: str) -> Optional[str]:
        """ログ行からタイムスタンプ抽出"""
        
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',
            r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}'
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()
        
        return None
    
    def analyze_error_trends(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """エラー傾向分析"""
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_files_scanned": len(all_results),
            "total_errors": 0,
            "severity_breakdown": {"critical": 0, "error": 0, "warning": 0},
            "category_breakdown": {},
            "recent_errors": [],
            "trending_patterns": [],
            "risk_assessment": "low"
        }
        
        all_errors = []
        
        for file_result in all_results:
            if file_result["status"] != "error":
                analysis["total_errors"] += len(file_result["errors_found"])
                all_errors.extend(file_result["errors_found"])
        
        # 重要度別集計
        for error in all_errors:
            severity = error["severity"]
            analysis["severity_breakdown"][severity] += 1
            
            category = error["category"]
            if category not in analysis["category_breakdown"]:
                analysis["category_breakdown"][category] = 0
            analysis["category_breakdown"][category] += 1
        
        # 最近のエラー（最新10件）
        recent_errors = sorted(all_errors, 
                              key=lambda x: x.get("timestamp", ""), 
                              reverse=True)[:10]
        analysis["recent_errors"] = recent_errors
        
        # パターン分析
        pattern_counts = {}
        for error in all_errors:
            desc = error["description"]
            if desc not in pattern_counts:
                pattern_counts[desc] = 0
            pattern_counts[desc] += 1
        
        analysis["trending_patterns"] = [
            {"pattern": pattern, "count": count}
            for pattern, count in sorted(pattern_counts.items(), 
                                       key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # リスク評価
        critical_count = analysis["severity_breakdown"]["critical"]
        error_count = analysis["severity_breakdown"]["error"]
        
        if critical_count > 0:
            analysis["risk_assessment"] = "critical"
        elif error_count > 5:
            analysis["risk_assessment"] = "high"
        elif error_count > 0 or analysis["severity_breakdown"]["warning"] > 10:
            analysis["risk_assessment"] = "medium"
        else:
            analysis["risk_assessment"] = "low"
        
        return analysis
    
    def generate_monitoring_report(self, analysis: Dict[str, Any]) -> str:
        """エラー監視レポート生成"""
        
        risk_icons = {
            "critical": "🔴",
            "high": "🟠", 
            "medium": "🟡",
            "low": "🟢"
        }
        
        risk_icon = risk_icons.get(analysis["risk_assessment"], "❓")
        
        report = f"""
🚨 **A3.1.2 エラーログ監視レポート**
実行日時: {analysis['timestamp']}
リスク評価: {risk_icon} {analysis['risk_assessment'].upper()}

📊 **監視結果サマリー**
- スキャンファイル: {analysis['total_files_scanned']}ファイル
- 検出エラー総数: {analysis['total_errors']}件
- 重大エラー: {analysis['severity_breakdown']['critical']}件
- 一般エラー: {analysis['severity_breakdown']['error']}件  
- 警告: {analysis['severity_breakdown']['warning']}件

🎯 **カテゴリ別分析**"""

        for category, count in analysis["category_breakdown"].items():
            if count > 0:
                report += f"\n- {category}: {count}件"
        
        if analysis["recent_errors"]:
            report += f"""

🔍 **最新エラー（上位3件）**"""
            for i, error in enumerate(analysis["recent_errors"][:3], 1):
                severity_icon = {"critical": "🔴", "error": "🟠", "warning": "🟡"}.get(error["severity"], "❓")
                report += f"""
{i}. {severity_icon} {error['description']}
   内容: {error['content'][:100]}..."""

        if analysis["trending_patterns"]:
            report += f"""

📈 **頻出パターン**"""
            for pattern in analysis["trending_patterns"][:3]:
                report += f"\n- {pattern['pattern']}: {pattern['count']}回"

        report += f"""

💡 **推奨アクション**"""
        
        if analysis["risk_assessment"] == "critical":
            report += """
🚨 即座対応が必要です:
  1. 重大エラーの詳細調査
  2. Phase 2/3.1機能の停止検討
  3. バックアップからの復旧準備"""
        elif analysis["risk_assessment"] == "high":
            report += """
⚠️ 早急な対応が必要です:
  1. エラー原因の特定
  2. 関連機能の動作確認
  3. 予防的対策の実施"""
        elif analysis["risk_assessment"] == "medium":
            report += """
📋 監視強化が必要です:
  1. エラーパターンの継続監視
  2. 警告レベルの詳細確認
  3. 定期チェックの強化"""
        else:
            report += """
✅ 正常稼働中です:
  1. 継続的監視の維持
  2. A3.1.3 パフォーマンス監視へ進行
  3. 定期レポートの確認"""
        
        return report
    
    def save_monitoring_results(self, analysis: Dict[str, Any], all_results: List[Dict[str, Any]]) -> str:
        """監視結果保存"""
        
        result_file = self.monitoring_dir / f"error_log_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        monitoring_data = {
            "monitoring_version": "error_log_1.0",
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "detailed_results": all_results,
            "metadata": {
                "monitoring_tool": "A3_ERROR_LOG_MONITOR",
                "scan_duration": "24_hours",
                "patterns_checked": len(self.error_patterns)
            }
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(monitoring_data, f, indent=2, ensure_ascii=False)
        
        return str(result_file)

def main():
    """メイン実行"""
    
    print("🚨 A3.1.2 エラーログ監視システム開始")
    print("🎯 Phase 2/3.1関連エラーの専門検知")
    print("=" * 80)
    
    try:
        monitor = ErrorLogMonitor()
        
        # 1. ログファイル検索
        print("📁 ログファイル検索...")
        log_files = monitor.find_log_files()
        print(f"  検出ファイル: {len(log_files)}件")
        
        if not log_files:
            print("  ⚠️ ログファイルが見つかりません")
            return True
        
        # 2. 各ログファイルスキャン
        print("\n🔍 ログファイルスキャン...")
        all_results = []
        
        for i, log_file in enumerate(log_files, 1):
            print(f"  {i}/{len(log_files)} {log_file.name}: ", end="")
            result = monitor.scan_log_file(log_file)
            
            error_count = len(result["errors_found"])
            if error_count > 0:
                print(f"⚠️ {error_count}件エラー検出")
            else:
                print("✅ 正常")
                
            all_results.append(result)
        
        # 3. エラー傾向分析
        print("\n📊 エラー傾向分析...")
        analysis = monitor.analyze_error_trends(all_results)
        
        # 4. レポート生成・表示
        print("\n" + "=" * 80)
        print("📋 エラー監視レポート")
        print("=" * 80)
        
        report = monitor.generate_monitoring_report(analysis)
        print(report)
        
        # 5. 結果保存
        result_file = monitor.save_monitoring_results(analysis, all_results)
        print(f"\n📁 監視結果保存: {result_file}")
        
        # 6. 成功判定
        success = analysis["risk_assessment"] in ["low", "medium"]
        status_text = "✅ 完了" if success else "❌ 要対応"
        print(f"\n🎯 A3.1.2 エラーログ監視: {status_text}")
        
        return success
        
    except Exception as e:
        print(f"❌ エラーログ監視システムエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)