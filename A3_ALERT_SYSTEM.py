#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3.1.4 アラートシステム
Phase 2/3.1監視結果に基づく異常時即座通知システム
全体最適化の観点で重要度別アラート設定
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    """アラート重要度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertCategory(Enum):
    """アラートカテゴリ"""
    PHASE2_INTEGRITY = "phase2_integrity"
    PHASE31_INTEGRITY = "phase31_integrity"
    SLOT_HOURS_CALCULATION = "slot_hours_calculation"
    NUMERICAL_CONSISTENCY = "numerical_consistency"
    SYSTEM_HEALTH = "system_health"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    FILE_INTEGRITY = "file_integrity"

@dataclass
class AlertRule:
    """アラートルール定義"""
    rule_id: str
    name: str
    category: AlertCategory
    severity: AlertSeverity
    condition: str
    threshold: Any
    description: str
    immediate_action: str
    escalation_minutes: int = 15

@dataclass
class Alert:
    """アラート"""
    alert_id: str
    rule_id: str
    timestamp: str
    severity: AlertSeverity
    category: AlertCategory
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolved_timestamp: Optional[str] = None

class AlertSystem:
    """Phase 2/3.1専門アラートシステム"""
    
    def __init__(self):
        self.alerts_dir = Path("logs/alerts")
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        self.monitoring_dir = Path("logs/monitoring")
        
        # アラートルール定義（深い思考による重要度設定）
        self.alert_rules = self._define_alert_rules()
        
        # アクティブアラート管理
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # 通知設定
        self.notification_config = {
            "log_file": True,
            "console": True,
            "email": False,  # 実装時にTrue
            "slack": False   # 実装時にTrue
        }
    
    def _define_alert_rules(self) -> List[AlertRule]:
        """深い思考によるアラートルール定義"""
        
        return [
            # Phase 2 重大問題
            AlertRule(
                rule_id="PHASE2_SLOT_HOURS_MISSING",
                name="Phase 2 SLOT_HOURS乗算不足",
                category=AlertCategory.PHASE2_INTEGRITY,
                severity=AlertSeverity.CRITICAL,
                condition="slot_hours_multiplications < expected_multiplications",
                threshold=4,
                description="Phase 2でSLOT_HOURS乗算が期待数より少ない",
                immediate_action="Phase 2ファイル確認・修正実施",
                escalation_minutes=5
            ),
            AlertRule(
                rule_id="PHASE2_WRONG_COMMENT",
                name="Phase 2 不正コメント検出",
                category=AlertCategory.PHASE2_INTEGRITY,
                severity=AlertSeverity.HIGH,
                condition="wrong_comment_detected",
                threshold=True,
                description="parsed_slots_count is already in hours コメント残存",
                immediate_action="不正コメント除去",
                escalation_minutes=10
            ),
            
            # Phase 3.1 重大問題
            AlertRule(
                rule_id="PHASE31_SLOT_HOURS_MISSING",
                name="Phase 3.1 SLOT_HOURS乗算不足",
                category=AlertCategory.PHASE31_INTEGRITY,
                severity=AlertSeverity.CRITICAL,
                condition="slot_hours_multiplications < expected_multiplications",
                threshold=1,
                description="Phase 3.1でSLOT_HOURS乗算が期待数より少ない",
                immediate_action="Phase 3.1ファイル確認・修正実施",
                escalation_minutes=5
            ),
            
            # SLOT_HOURS計算精度
            AlertRule(
                rule_id="SLOT_HOURS_CALCULATION_ERROR",
                name="SLOT_HOURS計算エラー",
                category=AlertCategory.SLOT_HOURS_CALCULATION,
                severity=AlertSeverity.CRITICAL,
                condition="calculation_mismatch",
                threshold=0.01,  # 0.01時間以上の誤差
                description="SLOT_HOURS計算で期待値との不一致",
                immediate_action="計算ロジック確認・修正",
                escalation_minutes=5
            ),
            
            # 数値整合性
            AlertRule(
                rule_id="NUMERICAL_BASELINE_DEVIATION",
                name="数値基準値逸脱",
                category=AlertCategory.NUMERICAL_CONSISTENCY,
                severity=AlertSeverity.HIGH,
                condition="baseline_deviation",
                threshold=10.0,  # 670時間から10時間以上の逸脱
                description="基準値670時間から大幅逸脱",
                immediate_action="数値整合性詳細調査",
                escalation_minutes=15
            ),
            
            # システム健全性
            AlertRule(
                rule_id="CRITICAL_FILE_MISSING",
                name="重要ファイル欠損",
                category=AlertCategory.FILE_INTEGRITY,
                severity=AlertSeverity.CRITICAL,
                condition="critical_file_missing",
                threshold=1,
                description="Phase 2/3.1重要ファイルの欠損",
                immediate_action="バックアップからの復旧",
                escalation_minutes=5
            ),
            
            # パフォーマンス劣化
            AlertRule(
                rule_id="PERFORMANCE_DEGRADATION",
                name="処理性能劣化",
                category=AlertCategory.PERFORMANCE_DEGRADATION,
                severity=AlertSeverity.MEDIUM,
                condition="response_time_exceeded",
                threshold=5.0,  # 5秒以上の処理時間
                description="Phase 2/3.1処理時間が閾値超過",
                immediate_action="性能調査・最適化検討",
                escalation_minutes=30
            ),
            
            # システム全般
            AlertRule(
                rule_id="SYSTEM_HEALTH_WARNING",
                name="システム健全性警告",
                category=AlertCategory.SYSTEM_HEALTH,
                severity=AlertSeverity.MEDIUM,
                condition="health_status_warning",
                threshold="warning",
                description="システム監視で警告ステータス検出",
                immediate_action="システム状態詳細確認",
                escalation_minutes=20
            )
        ]
    
    def check_monitoring_results(self) -> List[Alert]:
        """監視結果からアラート判定"""
        
        print("🚨 A3.1.4 アラートシステム開始")
        print("🎯 Phase 2/3.1監視結果に基づく異常検知")
        print("=" * 80)
        
        new_alerts = []
        
        # 最新監視結果取得
        latest_results = self._get_latest_monitoring_results()
        
        if not latest_results:
            print("⚠️ 監視結果が見つかりません")
            return new_alerts
        
        print("📊 監視結果分析...")
        
        # 各アラートルールをチェック
        for rule in self.alert_rules:
            alert = self._evaluate_alert_rule(rule, latest_results)
            if alert:
                new_alerts.append(alert)
                self.active_alerts.append(alert)
        
        return new_alerts
    
    def _get_latest_monitoring_results(self) -> Dict[str, Any]:
        """最新監視結果取得"""
        
        monitoring_files = []
        
        # 各監視結果ファイル検索
        patterns = [
            "monitoring_report_*.json",
            "error_log_*_*.json", 
            "performance_*_*.json"
        ]
        
        for pattern in patterns:
            monitoring_files.extend(self.monitoring_dir.glob(pattern))
        
        if not monitoring_files:
            return {}
        
        # 最新ファイル選択
        latest_file = max(monitoring_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"  ❌ 監視結果読み込みエラー: {e}")
            return {}
    
    def _evaluate_alert_rule(self, rule: AlertRule, monitoring_data: Dict[str, Any]) -> Optional[Alert]:
        """アラートルール評価"""
        
        try:
            # カテゴリ別評価ロジック
            if rule.category == AlertCategory.PHASE2_INTEGRITY:
                return self._check_phase2_integrity(rule, monitoring_data)
            elif rule.category == AlertCategory.PHASE31_INTEGRITY:
                return self._check_phase31_integrity(rule, monitoring_data)
            elif rule.category == AlertCategory.SLOT_HOURS_CALCULATION:
                return self._check_slot_hours_calculation(rule, monitoring_data)
            elif rule.category == AlertCategory.NUMERICAL_CONSISTENCY:
                return self._check_numerical_consistency(rule, monitoring_data)
            elif rule.category == AlertCategory.FILE_INTEGRITY:
                return self._check_file_integrity(rule, monitoring_data)
            elif rule.category == AlertCategory.PERFORMANCE_DEGRADATION:
                return self._check_performance_degradation(rule, monitoring_data)
            elif rule.category == AlertCategory.SYSTEM_HEALTH:
                return self._check_system_health(rule, monitoring_data)
            
        except Exception as e:
            print(f"  ❌ アラートルール評価エラー ({rule.rule_id}): {e}")
        
        return None
    
    def _check_phase2_integrity(self, rule: AlertRule, data: Dict[str, Any]) -> Optional[Alert]:
        """Phase 2整合性チェック"""
        
        phase2_data = self._extract_phase2_data(data)
        if not phase2_data:
            return None
        
        if rule.rule_id == "PHASE2_SLOT_HOURS_MISSING":
            slot_hours_count = phase2_data.get("slot_hours_multiplications", 0)
            if slot_hours_count < rule.threshold:
                return self._create_alert(
                    rule,
                    f"Phase 2 SLOT_HOURS乗算数: {slot_hours_count}/{rule.threshold}",
                    {"current_count": slot_hours_count, "expected": rule.threshold}
                )
        
        elif rule.rule_id == "PHASE2_WRONG_COMMENT":
            wrong_comment = not phase2_data.get("wrong_comments_removed", True)
            if wrong_comment:
                return self._create_alert(
                    rule,
                    "Phase 2に不正コメント'parsed_slots_count is already in hours'が残存",
                    {"wrong_comment_detected": True}
                )
        
        return None
    
    def _check_phase31_integrity(self, rule: AlertRule, data: Dict[str, Any]) -> Optional[Alert]:
        """Phase 3.1整合性チェック"""
        
        phase31_data = self._extract_phase31_data(data)
        if not phase31_data:
            return None
        
        if rule.rule_id == "PHASE31_SLOT_HOURS_MISSING":
            slot_hours_count = phase31_data.get("slot_hours_multiplications", 0)
            if slot_hours_count < rule.threshold:
                return self._create_alert(
                    rule,
                    f"Phase 3.1 SLOT_HOURS乗算数: {slot_hours_count}/{rule.threshold}",
                    {"current_count": slot_hours_count, "expected": rule.threshold}
                )
        
        return None
    
    def _check_slot_hours_calculation(self, rule: AlertRule, data: Dict[str, Any]) -> Optional[Alert]:
        """SLOT_HOURS計算チェック"""
        
        calculation_data = self._extract_calculation_data(data)
        if not calculation_data:
            return None
        
        if rule.rule_id == "SLOT_HOURS_CALCULATION_ERROR":
            for test_name, test_result in calculation_data.items():
                if not test_result.get("match", True):
                    expected = test_result.get("expected_hours", 0)
                    calculated = test_result.get("calculated_hours", 0)
                    deviation = abs(expected - calculated)
                    
                    if deviation > rule.threshold:
                        return self._create_alert(
                            rule,
                            f"SLOT_HOURS計算誤差: {test_name} 期待値{expected}h vs 計算値{calculated}h",
                            {"test": test_name, "expected": expected, "calculated": calculated, "deviation": deviation}
                        )
        
        return None
    
    def _check_numerical_consistency(self, rule: AlertRule, data: Dict[str, Any]) -> Optional[Alert]:
        """数値整合性チェック"""
        
        numerical_data = self._extract_numerical_data(data)
        if not numerical_data:
            return None
        
        if rule.rule_id == "NUMERICAL_BASELINE_DEVIATION":
            baseline_check = numerical_data.get("baseline_check", {})
            if not baseline_check.get("baseline_confirmed", True):
                return self._create_alert(
                    rule,
                    "数値基準値670時間の確認が取れません",
                    {"baseline_status": "unconfirmed"}
                )
        
        return None
    
    def _check_file_integrity(self, rule: AlertRule, data: Dict[str, Any]) -> Optional[Alert]:
        """ファイル整合性チェック"""
        
        files_data = self._extract_files_data(data)
        if not files_data:
            return None
        
        if rule.rule_id == "CRITICAL_FILE_MISSING":
            missing_files = []
            for file_path, file_info in files_data.items():
                if not file_info.get("exists", True):
                    missing_files.append(file_path)
            
            if missing_files:
                return self._create_alert(
                    rule,
                    f"重要ファイル欠損: {', '.join(missing_files)}",
                    {"missing_files": missing_files}
                )
        
        return None
    
    def _check_performance_degradation(self, rule: AlertRule, data: Dict[str, Any]) -> Optional[Alert]:
        """パフォーマンス劣化チェック"""
        
        performance_data = self._extract_performance_data(data)
        if not performance_data:
            return None
        
        if rule.rule_id == "PERFORMANCE_DEGRADATION":
            slow_operations = []
            for component, tests in performance_data.items():
                if isinstance(tests, dict) and "tests" in tests:
                    for test_name, test_result in tests["tests"].items():
                        duration = test_result.get("duration_seconds", 0)
                        if duration > rule.threshold:
                            slow_operations.append(f"{component}:{test_name} ({duration:.3f}s)")
            
            if slow_operations:
                return self._create_alert(
                    rule,
                    f"処理時間閾値超過: {', '.join(slow_operations)}",
                    {"slow_operations": slow_operations}
                )
        
        return None
    
    def _check_system_health(self, rule: AlertRule, data: Dict[str, Any]) -> Optional[Alert]:
        """システム健全性チェック"""
        
        if rule.rule_id == "SYSTEM_HEALTH_WARNING":
            overall_status = self._extract_overall_status(data)
            if overall_status in ["warning", "error", "poor"]:
                return self._create_alert(
                    rule,
                    f"システム健全性警告: ステータス = {overall_status}",
                    {"overall_status": overall_status}
                )
        
        return None
    
    def _extract_phase2_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2データ抽出"""
        results = data.get("results", {})
        phase_integrity = results.get("phase_integrity", {})
        return phase_integrity.get("phase2", {})
    
    def _extract_phase31_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3.1データ抽出"""
        results = data.get("results", {})
        phase_integrity = results.get("phase_integrity", {})
        return phase_integrity.get("phase31", {})
    
    def _extract_calculation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """計算データ抽出"""
        results = data.get("results", {})
        numerical = results.get("numerical", {})
        return numerical.get("calculation_verification", {})
    
    def _extract_numerical_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数値データ抽出"""
        results = data.get("results", {})
        return results.get("numerical", {})
    
    def _extract_files_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ファイルデータ抽出"""
        results = data.get("results", {})
        files = results.get("files", {})
        return files.get("files", {})
    
    def _extract_performance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンスデータ抽出"""
        return data.get("performance_tests", {})
    
    def _extract_overall_status(self, data: Dict[str, Any]) -> str:
        """全体ステータス抽出"""
        results = data.get("results", {})
        if results:
            # 各ステータス確認
            statuses = []
            for key, value in results.items():
                if isinstance(value, dict) and "status" in value:
                    statuses.append(value["status"])
            
            if "error" in statuses:
                return "error"
            elif "warning" in statuses:
                return "warning"
            elif "poor" in statuses:
                return "poor"
            else:
                return "healthy"
        
        return data.get("analysis", {}).get("overall_status", "unknown")
    
    def _create_alert(self, rule: AlertRule, message: str, details: Dict[str, Any]) -> Alert:
        """アラート作成"""
        
        alert_id = f"{rule.rule_id}_{int(time.time())}"
        
        return Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            timestamp=datetime.now().isoformat(),
            severity=rule.severity,
            category=rule.category,
            message=message,
            details=details
        )
    
    def process_alerts(self, alerts: List[Alert]) -> Dict[str, Any]:
        """アラート処理"""
        
        processing_results = {
            "timestamp": datetime.now().isoformat(),
            "alerts_processed": len(alerts),
            "severity_breakdown": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            },
            "notifications_sent": [],
            "immediate_actions": []
        }
        
        for alert in alerts:
            # 重要度別カウント
            processing_results["severity_breakdown"][alert.severity.value] += 1
            
            # 通知送信
            notification_result = self._send_notifications(alert)
            processing_results["notifications_sent"].append(notification_result)
            
            # 即座アクション記録
            rule = next((r for r in self.alert_rules if r.rule_id == alert.rule_id), None)
            if rule:
                processing_results["immediate_actions"].append({
                    "alert_id": alert.alert_id,
                    "action": rule.immediate_action,
                    "escalation_minutes": rule.escalation_minutes
                })
        
        return processing_results
    
    def _send_notifications(self, alert: Alert) -> Dict[str, Any]:
        """通知送信"""
        
        notification_result = {
            "alert_id": alert.alert_id,
            "methods": [],
            "success": True
        }
        
        # コンソール通知
        if self.notification_config["console"]:
            self._send_console_notification(alert)
            notification_result["methods"].append("console")
        
        # ログファイル通知
        if self.notification_config["log_file"]:
            self._send_log_notification(alert)
            notification_result["methods"].append("log_file")
        
        # その他の通知方法（将来実装）
        # if self.notification_config["email"]:
        #     self._send_email_notification(alert)
        # if self.notification_config["slack"]:
        #     self._send_slack_notification(alert)
        
        return notification_result
    
    def _send_console_notification(self, alert: Alert):
        """コンソール通知"""
        
        severity_icons = {
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.HIGH: "🟠",
            AlertSeverity.MEDIUM: "🟡",
            AlertSeverity.LOW: "🔵",
            AlertSeverity.INFO: "⚪"
        }
        
        icon = severity_icons.get(alert.severity, "❓")
        
        print(f"\n{'='*60}")
        print(f"🚨 **アラート発生** {icon} {alert.severity.value.upper()}")
        print(f"{'='*60}")
        print(f"時刻: {alert.timestamp}")
        print(f"カテゴリ: {alert.category.value}")
        print(f"メッセージ: {alert.message}")
        if alert.details:
            print(f"詳細: {json.dumps(alert.details, ensure_ascii=False, indent=2)}")
        print(f"{'='*60}")
    
    def _send_log_notification(self, alert: Alert):
        """ログファイル通知"""
        
        alert_log_file = self.alerts_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.log"
        
        log_entry = f"{alert.timestamp} [{alert.severity.value.upper()}] {alert.category.value}: {alert.message}\n"
        
        with open(alert_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def generate_alert_report(self, alerts: List[Alert], processing_results: Dict[str, Any]) -> str:
        """アラートレポート生成"""
        
        report = f"""
🚨 **A3.1.4 アラートシステムレポート**
実行日時: {processing_results['timestamp']}
アラート数: {processing_results['alerts_processed']}件

📊 **重要度別内訳**
- 🔴 Critical: {processing_results['severity_breakdown']['critical']}件
- 🟠 High: {processing_results['severity_breakdown']['high']}件  
- 🟡 Medium: {processing_results['severity_breakdown']['medium']}件
- 🔵 Low: {processing_results['severity_breakdown']['low']}件
- ⚪ Info: {processing_results['severity_breakdown']['info']}件

🎯 **アラート詳細**"""

        if alerts:
            for i, alert in enumerate(alerts, 1):
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}.get(alert.severity.value, "❓")
                report += f"""
{i}. {severity_icon} {alert.message}
   カテゴリ: {alert.category.value}
   時刻: {alert.timestamp}"""
        else:
            report += "\n✅ アラート発生なし - システム正常"

        report += f"""

💡 **推奨アクション**"""
        
        critical_count = processing_results['severity_breakdown']['critical']
        high_count = processing_results['severity_breakdown']['high']
        
        if critical_count > 0:
            report += """
🚨 Critical アラート対応が必要:
  1. 即座にPhase 2/3.1システム確認
  2. 緊急修正・復旧作業実施
  3. エスカレーション手順開始"""
        elif high_count > 0:
            report += """
⚠️ High アラート対応が必要:
  1. 優先的にアラート内容確認
  2. 予防的対策の実施
  3. 監視強化の継続"""
        else:
            report += """
✅ システム正常稼働中:
  1. A3.2 データ品質監視への進行
  2. 継続的監視の維持
  3. アラート設定の定期見直し"""
        
        return report
    
    def save_alert_results(self, alerts: List[Alert], processing_results: Dict[str, Any]) -> str:
        """アラート結果保存"""
        
        result_file = self.alerts_dir / f"alert_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        alert_data = {
            "alert_system_version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "rule_id": alert.rule_id,
                    "timestamp": alert.timestamp,
                    "severity": alert.severity.value,
                    "category": alert.category.value,
                    "message": alert.message,
                    "details": alert.details,
                    "resolved": alert.resolved
                }
                for alert in alerts
            ],
            "processing_results": processing_results,
            "alert_rules_count": len(self.alert_rules),
            "metadata": {
                "monitoring_tool": "A3_ALERT_SYSTEM",
                "focus": "Phase 2/3.1 integrity monitoring",
                "deep_thinking_applied": True
            }
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(alert_data, f, indent=2, ensure_ascii=False)
        
        return str(result_file)

def main():
    """メイン実行"""
    
    try:
        alert_system = AlertSystem()
        
        # 1. 監視結果からアラート判定
        print("\n🔍 監視結果チェック...")
        alerts = alert_system.check_monitoring_results()
        
        # 2. アラート処理
        print(f"\n📋 アラート処理... ({len(alerts)}件)")
        processing_results = alert_system.process_alerts(alerts)
        
        # 3. レポート生成・表示
        print("\n" + "=" * 80)
        print("📋 アラートシステムレポート")
        print("=" * 80)
        
        report = alert_system.generate_alert_report(alerts, processing_results)
        print(report)
        
        # 4. 結果保存
        result_file = alert_system.save_alert_results(alerts, processing_results)
        print(f"\n📁 アラート結果保存: {result_file}")
        
        # 5. 成功判定
        critical_alerts = processing_results['severity_breakdown']['critical']
        success = critical_alerts == 0
        status_text = "✅ 完了" if success else "❌ Critical対応必要"
        print(f"\n🎯 A3.1.4 アラートシステム: {status_text}")
        
        return success
        
    except Exception as e:
        print(f"❌ アラートシステムエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)