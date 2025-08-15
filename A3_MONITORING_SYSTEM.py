#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3.1 基本監視体制
システム稼働・エラーログ・パフォーマンス・アラートの統合監視システム
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import psutil
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# 監視設定
@dataclass
class MonitoringConfig:
    """監視設定クラス"""
    
    # システム監視対象
    critical_files: List[str]
    log_directories: List[str]
    
    # パフォーマンス閾値
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 85.0
    max_response_time: float = 10.0
    
    # アラート設定
    alert_email: str = "admin@shift-suite.com"
    alert_threshold: int = 3  # 連続エラー数
    
    # 監視間隔
    check_interval: int = 300  # 5分
    log_retention_days: int = 30

class SystemMonitor:
    """システム稼働監視"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.setup_logging()
        self.last_check = datetime.now()
        self.error_count = 0
        
    def setup_logging(self):
        """ログ設定"""
        log_dir = Path("logs/monitoring")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"system_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_critical_files(self) -> Dict[str, Any]:
        """重要ファイルの存在確認"""
        
        critical_files = [
            "shift_suite/tasks/fact_extractor_prototype.py",
            "shift_suite/tasks/lightweight_anomaly_detector.py", 
            "shift_suite/tasks/fact_book_visualizer.py",
            "shift_suite/tasks/dash_fact_book_integration.py",
            "dash_app.py",
            "app.py"
        ]
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "files": {},
            "status": "healthy"
        }
        
        for file_path in critical_files:
            path = Path(file_path)
            if path.exists():
                # ファイルサイズとタイムスタンプ確認
                stat = path.stat()
                results["files"][file_path] = {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "status": "ok"
                }
            else:
                results["files"][file_path] = {
                    "exists": False,
                    "status": "missing"
                }
                results["status"] = "warning"
                self.logger.warning(f"Critical file missing: {file_path}")
        
        return results
    
    def check_process_status(self) -> Dict[str, Any]:
        """プロセス状況確認"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "processes": {},
            "system": {},
            "status": "healthy"
        }
        
        # システムリソース確認
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            results["system"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            }
            
            # CPU/メモリ閾値チェック
            if cpu_percent > self.config.max_cpu_percent:
                results["status"] = "warning"
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > self.config.max_memory_percent:
                results["status"] = "warning"
                self.logger.warning(f"High memory usage: {memory.percent}%")
                
        except Exception as e:
            results["system"]["error"] = str(e)
            results["status"] = "error"
            self.logger.error(f"System monitoring error: {e}")
        
        return results
    
    def check_phase2_31_integration(self) -> Dict[str, Any]:
        """Phase 2/3.1統合状況確認"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "phase2": {},
            "phase31": {},
            "integration": {},
            "status": "healthy"
        }
        
        try:
            # Phase 2ファイル確認
            phase2_file = Path("shift_suite/tasks/fact_extractor_prototype.py")
            if phase2_file.exists():
                with open(phase2_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                slot_hours_count = content.count('* SLOT_HOURS')
                wrong_comment = "parsed_slots_count is already in hours" in content
                
                results["phase2"] = {
                    "file_exists": True,
                    "slot_hours_multiplications": slot_hours_count,
                    "wrong_comments": wrong_comment,
                    "expected_multiplications": 4,
                    "status": "ok" if slot_hours_count >= 4 and not wrong_comment else "warning"
                }
                
                if slot_hours_count < 4 or wrong_comment:
                    results["status"] = "warning"
                    self.logger.warning(f"Phase 2 integrity issue: SLOT_HOURS={slot_hours_count}, wrong_comment={wrong_comment}")
            
            # Phase 3.1ファイル確認
            phase31_file = Path("shift_suite/tasks/lightweight_anomaly_detector.py")
            if phase31_file.exists():
                with open(phase31_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                slot_hours_count = content.count('* SLOT_HOURS')
                wrong_comment = "parsed_slots_count is already in hours" in content
                
                results["phase31"] = {
                    "file_exists": True,
                    "slot_hours_multiplications": slot_hours_count,
                    "wrong_comments": wrong_comment,
                    "expected_multiplications": 1,
                    "status": "ok" if slot_hours_count >= 1 and not wrong_comment else "warning"
                }
                
                if slot_hours_count < 1 or wrong_comment:
                    results["status"] = "warning"
                    self.logger.warning(f"Phase 3.1 integrity issue: SLOT_HOURS={slot_hours_count}, wrong_comment={wrong_comment}")
            
            # 統合確認
            factbook_file = Path("shift_suite/tasks/fact_book_visualizer.py")
            if factbook_file.exists():
                with open(factbook_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                phase2_integration = "FactExtractorPrototype" in content
                phase31_integration = "LightweightAnomalyDetector" in content
                
                results["integration"] = {
                    "factbook_exists": True,
                    "phase2_integration": phase2_integration,
                    "phase31_integration": phase31_integration,
                    "status": "ok" if phase2_integration and phase31_integration else "warning"
                }
                
                if not (phase2_integration and phase31_integration):
                    results["status"] = "warning"
                    self.logger.warning(f"Integration issue: Phase2={phase2_integration}, Phase3.1={phase31_integration}")
                    
        except Exception as e:
            results["error"] = str(e)
            results["status"] = "error"
            self.logger.error(f"Phase 2/3.1 integration check error: {e}")
        
        return results

class ErrorLogMonitor:
    """エラーログ監視"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.last_position = {}
    
    def scan_logs(self) -> Dict[str, Any]:
        """ログファイルスキャン"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "logs_scanned": 0,
            "errors_found": 0,
            "warnings_found": 0,
            "critical_errors": [],
            "status": "healthy"
        }
        
        # ログディレクトリ候補
        log_paths = [
            "logs",
            ".",
            "shift_suite"
        ]
        
        error_patterns = [
            "ERROR",
            "CRITICAL", 
            "FATAL",
            "Exception",
            "Traceback",
            "Phase 2",
            "Phase 3.1",
            "SLOT_HOURS",
            "parsed_slots_count"
        ]
        
        for log_dir in log_paths:
            log_path = Path(log_dir)
            if not log_path.exists():
                continue
                
            # ログファイル検索
            for log_file in log_path.glob("*.log"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        results["logs_scanned"] += 1
                        
                        for line_num, line in enumerate(lines, 1):
                            for pattern in error_patterns:
                                if pattern.lower() in line.lower():
                                    if "ERROR" in line.upper() or "CRITICAL" in line.upper():
                                        results["errors_found"] += 1
                                        results["critical_errors"].append({
                                            "file": str(log_file),
                                            "line": line_num,
                                            "content": line.strip(),
                                            "pattern": pattern
                                        })
                                    elif "WARNING" in line.upper():
                                        results["warnings_found"] += 1
                                        
                except Exception as e:
                    self.logger.error(f"Error reading log file {log_file}: {e}")
        
        # 状態判定
        if results["errors_found"] > 0:
            results["status"] = "error"
        elif results["warnings_found"] > 5:
            results["status"] = "warning"
        
        return results

class PerformanceMonitor:
    """パフォーマンス監視"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def measure_response_times(self) -> Dict[str, Any]:
        """レスポンス時間測定"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "average_response_time": 0.0,
            "status": "healthy"
        }
        
        # Python構文チェック（応答性テスト）
        test_files = [
            "shift_suite/tasks/fact_extractor_prototype.py",
            "shift_suite/tasks/lightweight_anomaly_detector.py"
        ]
        
        total_time = 0.0
        test_count = 0
        
        for file_path in test_files:
            if Path(file_path).exists():
                try:
                    start_time = time.time()
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", file_path],
                        capture_output=True,
                        timeout=self.config.max_response_time
                    )
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    total_time += response_time
                    test_count += 1
                    
                    results["tests"][file_path] = {
                        "response_time": response_time,
                        "syntax_ok": result.returncode == 0,
                        "status": "ok" if result.returncode == 0 and response_time < self.config.max_response_time else "warning"
                    }
                    
                    if response_time > self.config.max_response_time:
                        results["status"] = "warning"
                        self.logger.warning(f"Slow response: {file_path} took {response_time:.2f}s")
                        
                except subprocess.TimeoutExpired:
                    results["tests"][file_path] = {
                        "response_time": self.config.max_response_time,
                        "syntax_ok": False,
                        "status": "timeout"
                    }
                    results["status"] = "error"
                    self.logger.error(f"Timeout: {file_path}")
                    
                except Exception as e:
                    results["tests"][file_path] = {
                        "error": str(e),
                        "status": "error"
                    }
                    results["status"] = "error"
                    self.logger.error(f"Performance test error for {file_path}: {e}")
        
        if test_count > 0:
            results["average_response_time"] = total_time / test_count
        
        return results

class AlertSystem:
    """アラートシステム"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.alert_history = []
    
    def send_alert(self, alert_type: str, message: str, severity: str = "warning") -> bool:
        """アラート送信"""
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
            "severity": severity
        }
        
        self.alert_history.append(alert)
        
        # ログ出力
        if severity == "critical":
            self.logger.critical(f"ALERT [{alert_type}]: {message}")
        elif severity == "error":
            self.logger.error(f"ALERT [{alert_type}]: {message}")
        else:
            self.logger.warning(f"ALERT [{alert_type}]: {message}")
        
        # 実際の通知（メール・Slack等）はここで実装
        # 現在はログ出力のみ
        
        return True

class MonitoringCoordinator:
    """監視統合管理"""
    
    def __init__(self):
        self.config = MonitoringConfig(
            critical_files=[
                "shift_suite/tasks/fact_extractor_prototype.py",
                "shift_suite/tasks/lightweight_anomaly_detector.py",
                "dash_app.py"
            ],
            log_directories=["logs", "."]
        )
        
        self.system_monitor = SystemMonitor(self.config)
        self.error_monitor = ErrorLogMonitor(self.config)
        self.performance_monitor = PerformanceMonitor(self.config)
        self.alert_system = AlertSystem(self.config)
        
        # 結果保存ディレクトリ
        self.results_dir = Path("logs/monitoring/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """包括的監視チェック実行"""
        
        print("🔍 A3.1 包括的システム監視実行")
        print("=" * 60)
        
        comprehensive_results = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_version": "1.0",
            "checks": {},
            "overall_status": "healthy",
            "summary": {}
        }
        
        # 1. システム稼働確認
        print("📊 システム稼働確認...")
        system_results = self.system_monitor.check_critical_files()
        process_results = self.system_monitor.check_process_status()
        phase_results = self.system_monitor.check_phase2_31_integration()
        
        comprehensive_results["checks"]["system"] = {
            "files": system_results,
            "processes": process_results, 
            "phase_integration": phase_results
        }
        
        # 2. エラーログスキャン
        print("📋 エラーログスキャン...")
        log_results = self.error_monitor.scan_logs()
        comprehensive_results["checks"]["logs"] = log_results
        
        # 3. パフォーマンス測定
        print("⚡ パフォーマンス測定...")
        performance_results = self.performance_monitor.measure_response_times()
        comprehensive_results["checks"]["performance"] = performance_results
        
        # 4. 総合ステータス判定
        all_statuses = [
            system_results["status"],
            process_results["status"],
            phase_results["status"],
            log_results["status"],
            performance_results["status"]
        ]
        
        if "error" in all_statuses:
            comprehensive_results["overall_status"] = "error"
        elif "warning" in all_statuses:
            comprehensive_results["overall_status"] = "warning"
        else:
            comprehensive_results["overall_status"] = "healthy"
        
        # 5. サマリー生成
        comprehensive_results["summary"] = {
            "files_checked": len(system_results["files"]),
            "files_healthy": sum(1 for f in system_results["files"].values() if f["status"] == "ok"),
            "logs_scanned": log_results["logs_scanned"],
            "errors_found": log_results["errors_found"],
            "warnings_found": log_results["warnings_found"],
            "average_response_time": performance_results["average_response_time"],
            "overall_health": comprehensive_results["overall_status"]
        }
        
        # 6. 結果保存
        result_file = self.results_dir / f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)
        
        # 7. アラート判定・送信
        if comprehensive_results["overall_status"] == "error":
            self.alert_system.send_alert(
                "system_health", 
                f"Critical system issues detected. Errors: {log_results['errors_found']}", 
                "critical"
            )
        elif comprehensive_results["overall_status"] == "warning":
            self.alert_system.send_alert(
                "system_health",
                f"System warnings detected. Warnings: {log_results['warnings_found']}",
                "warning"
            )
        
        return comprehensive_results
    
    def generate_monitoring_report(self, results: Dict[str, Any]) -> str:
        """監視レポート生成"""
        
        report = f"""
🔍 **システム監視レポート**
実行日時: {results['timestamp']}
総合ステータス: {results['overall_status']}

📊 **監視結果サマリー**
- ファイル確認: {results['summary']['files_healthy']}/{results['summary']['files_checked']} 正常
- ログスキャン: {results['summary']['logs_scanned']}ファイル
- エラー検出: {results['summary']['errors_found']}件
- 警告検出: {results['summary']['warnings_found']}件
- 平均応答時間: {results['summary']['average_response_time']:.2f}秒

🎯 **Phase 2/3.1 統合状況**
Phase 2: {results['checks']['system']['phase_integration']['phase2'].get('status', 'unknown')}
Phase 3.1: {results['checks']['system']['phase_integration']['phase31'].get('status', 'unknown')}
統合: {results['checks']['system']['phase_integration']['integration'].get('status', 'unknown')}

💡 **推奨アクション**
"""
        
        if results['overall_status'] == "error":
            report += "🚨 即座対応が必要です。エラーログを確認し、必要に応じてロールバックを検討してください。"
        elif results['overall_status'] == "warning":
            report += "⚠️ 注意が必要です。警告内容を確認し、予防的対策を検討してください。"
        else:
            report += "✅ システムは正常に動作しています。継続監視を続けてください。"
        
        return report

def main():
    """メイン実行"""
    
    print("🚨 A3.1 基本監視体制 - 開始")
    print("🎯 Phase 2/3.1修正成果の安定運用監視")
    print("=" * 80)
    
    try:
        # 監視システム初期化
        coordinator = MonitoringCoordinator()
        
        # 包括的チェック実行
        results = coordinator.run_comprehensive_check()
        
        # レポート生成・表示
        report = coordinator.generate_monitoring_report(results)
        print("\n" + "=" * 80)
        print("📋 監視結果レポート")
        print("=" * 80)
        print(report)
        
        # 次ステップ提案
        print("\n🚀 次ステップ:")
        if results['overall_status'] == "healthy":
            print("  1. A3.1.2 エラーログ監視の詳細設定")
            print("  2. A3.1.3 パフォーマンス監視の継続実行")
            print("  3. A3.1.4 アラートシステムの本格運用")
        else:
            print("  1. 検出された問題の詳細調査")
            print("  2. 必要に応じた修正・対策実施")
            print("  3. 監視システムの再実行")
        
        return results['overall_status'] == "healthy"
        
    except Exception as e:
        print(f"❌ 監視システムエラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)