#!/usr/bin/env python3
"""
アラート通知送信スクリプト
"""

import json
import datetime

def send_alert(alert_data):
    print(f"[ALERT] {alert_data['severity']}: {alert_data['message']}")
    
    # 通知チャネル別処理
    if 'email' in alert_data['channels']:
        send_email_alert(alert_data)
    
    if 'slack' in alert_data['channels']:
        send_slack_alert(alert_data)
    
    if 'dashboard' in alert_data['channels']:
        update_dashboard_alert(alert_data)

def send_email_alert(alert_data):
    print(f"Email送信: {alert_data['message']}")

def send_slack_alert(alert_data):
    print(f"Slack通知: {alert_data['message']}")

def update_dashboard_alert(alert_data):
    print(f"ダッシュボード更新: {alert_data['message']}")

if __name__ == "__main__":
    # テストアラート
    test_alert = {
        'severity': 'warning',
        'message': 'システムヘルス低下検出',
        'channels': ['email', 'slack', 'dashboard'],
        'timestamp': datetime.datetime.now().isoformat()
    }
    send_alert(test_alert)
