#!/usr/bin/env python3
"""
Simple app.py Integration Module for Import
簡易app統合モジュール - インポート用
"""

import sys
sys.path.append('.')

# メインモジュールからインポート
from app_interface_integration_module_20250808_091705 import (
    AppParameterExtractor,
    DynamicNeedCalculationIntegration,
    create_proportional_abolition_dashboard,
    test_app_integration_complete
)

# 簡易実行関数
def quick_app_integration():
    """クイックapp統合実行"""
    integration = DynamicNeedCalculationIntegration('app.py')
    results = integration.execute_integrated_calculation()
    display_data = integration.get_streamlit_display_data()
    return display_data

# Streamlit統合用関数
def get_dashboard_data():
    """ダッシュボード用データ取得"""
    return quick_app_integration()
