"""
UIヘルパー関数
Streamlitアプリケーションでの警告・ステータス表示を統一
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

log = logging.getLogger(__name__)

class UINotificationManager:
    """UI通知マネージャー"""
    
    def __init__(self):
        """初期化"""
        self.warnings = []
        self.errors = []
        self.info = []
        self.success = []
    
    def add_warning(self, message: str, detail: Optional[str] = None):
        """警告を追加"""
        self.warnings.append({'message': message, 'detail': detail})
        log.warning(message)
    
    def add_error(self, message: str, detail: Optional[str] = None):
        """エラーを追加"""
        self.errors.append({'message': message, 'detail': detail})
        log.error(message)
    
    def add_info(self, message: str, detail: Optional[str] = None):
        """情報を追加"""
        self.info.append({'message': message, 'detail': detail})
        log.info(message)
    
    def add_success(self, message: str, detail: Optional[str] = None):
        """成功メッセージを追加"""
        self.success.append({'message': message, 'detail': detail})
        log.info(f"SUCCESS: {message}")
    
    def display_all(self):
        """全ての通知を表示"""
        # エラーを最初に表示
        for item in self.errors:
            st.error(f"❌ {item['message']}")
            if item['detail']:
                with st.expander("詳細", expanded=False):
                    st.write(item['detail'])
        
        # 警告を表示
        for item in self.warnings:
            st.warning(f"⚠️ {item['message']}")
            if item['detail']:
                with st.expander("詳細", expanded=False):
                    st.write(item['detail'])
        
        # 情報を表示
        for item in self.info:
            st.info(f"ℹ️ {item['message']}")
            if item['detail']:
                with st.expander("詳細", expanded=False):
                    st.write(item['detail'])
        
        # 成功メッセージを表示
        for item in self.success:
            st.success(f"✅ {item['message']}")
            if item['detail']:
                with st.expander("詳細", expanded=False):
                    st.write(item['detail'])
    
    def clear(self):
        """全ての通知をクリア"""
        self.warnings = []
        self.errors = []
        self.info = []
        self.success = []
    
    def has_notifications(self) -> bool:
        """通知があるかチェック"""
        return bool(self.warnings or self.errors or self.info or self.success)
    
    def get_summary(self) -> Dict[str, int]:
        """通知のサマリーを取得"""
        return {
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'info': len(self.info),
            'success': len(self.success)
        }

def display_analysis_warnings(warnings_file: Path):
    """分析警告ファイルを読み込んで表示"""
    if not warnings_file.exists():
        return
    
    try:
        with open(warnings_file, 'r', encoding='utf-8') as f:
            warnings_data = json.load(f)
        
        # 不足時間の警告
        if warnings_data.get('shortage_warnings', {}).get('has_warnings'):
            count = warnings_data['shortage_warnings']['warning_count']
            st.warning(f"⚠️ 不足時間分析で{count}件の異常値を検出しました")
            
            # 詳細情報がある場合
            details = warnings_data['shortage_warnings'].get('warning_details', [])
            if details:
                with st.expander("警告の詳細", expanded=False):
                    for detail in details[:5]:  # 最初の5件のみ表示
                        severity = detail.get('severity', 'unknown')
                        severity_icon = "🔴" if severity == 'high' else "🟡"
                        st.write(f"{severity_icon} {detail['date']}: {detail['shortage_hours']:.1f}時間")
                    if len(details) > 5:
                        st.write(f"... 他{len(details) - 5}件")
        
        # 需要データの警告
        if warnings_data.get('need_validation', {}).get('warnings'):
            st.warning("⚠️ 需要データに異常な値を検出しました")
            with st.expander("需要データ警告の詳細", expanded=False):
                for warning in warnings_data['need_validation']['warnings']:
                    st.write(f"• {warning}")
        
        # 期間依存性リスク
        risk_info = warnings_data.get('period_risk', {})
        risk_level = risk_info.get('risk_level')
        if risk_level in ['high', 'critical']:
            if risk_level == 'critical':
                st.error(f"🚨 期間依存性リスク: {risk_level}")
            else:
                st.warning(f"⚠️ 期間依存性リスク: {risk_level}")
            
            st.write(risk_info.get('recommendation', ''))
            
            # 統計情報を表示
            with st.expander("リスク詳細", expanded=False):
                st.write(f"- 日平均不足: {risk_info.get('daily_shortage', 0):.1f}時間/日")
                st.write(f"- 月間推定不足: {risk_info.get('monthly_shortage', 0):.1f}時間/月")
                st.write(f"- 分析期間: {risk_info.get('period_days', 0)}日")
    
    except Exception as e:
        log.debug(f"警告情報の表示エラー: {e}")

def display_settings_status():
    """現在の設定状態を表示"""
    from .constants import _settings, FACILITY_SETTINGS_PATH
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 設定ファイル状態")
        if FACILITY_SETTINGS_PATH.exists():
            st.success(f"✅ 設定ファイル: 読み込み済み")
            st.caption(f"パス: {FACILITY_SETTINGS_PATH}")
        else:
            st.info(f"ℹ️ デフォルト設定を使用中")
    
    with col2:
        st.markdown("### ⚙️ 主要設定値")
        if _settings:
            slot_minutes = _settings.get('time_settings', {}).get('slot_minutes', 30)
            st.write(f"- スロット時間: {slot_minutes}分")
            
            wage_direct = _settings.get('wage_settings', {}).get('regular_staff', {}).get('default', 1500)
            wage_temp = _settings.get('wage_settings', {}).get('temporary_staff', {}).get('default', 2200)
            st.write(f"- 正規職員時給: ¥{wage_direct:,}")
            st.write(f"- 派遣職員時給: ¥{wage_temp:,}")

def create_status_sidebar():
    """サイドバーにステータス表示を作成"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📊 システム状態")
        
        # 設定ファイルの状態
        from .constants import FACILITY_SETTINGS_PATH
        if FACILITY_SETTINGS_PATH.exists():
            st.success("設定: ✅ ファイル読み込み済み")
        else:
            st.info("設定: ℹ️ デフォルト値使用")
        
        # モジュールの利用可能状態
        try:
            import app
            if hasattr(app, '_HAS_ANOMALY'):
                if app._HAS_ANOMALY:
                    st.success("異常検知: ✅ 利用可能")
                else:
                    st.warning("異常検知: ⚠️ 利用不可")
            
            if hasattr(app, '_HAS_CLUSTER'):
                if app._HAS_CLUSTER:
                    st.success("クラスタリング: ✅ 利用可能")
                else:
                    st.warning("クラスタリング: ⚠️ 利用不可")
        except:
            pass
        
        st.markdown("---")