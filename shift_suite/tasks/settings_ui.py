"""
設定管理UI
Streamlitアプリケーションでの設定変更機能を提供
"""

import streamlit as st
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .config_loader import get_config, get_setting

log = logging.getLogger(__name__)

class SettingsUI:
    """設定管理UIクラス"""
    
    def __init__(self):
        """初期化"""
        self.config = get_config()
        self.settings_changed = False
    
    def render_settings_editor(self) -> bool:
        """
        設定エディタUIをレンダリング
        
        Returns:
            設定が変更されたかどうか
        """
        st.markdown("### ⚙️ 設定エディタ")
        
        # タブで設定カテゴリを分割
        tabs = st.tabs([
            "⏰ 時間設定",
            "💰 賃金設定",
            "💵 コスト設定",
            "🏢 施設タイプ",
            "📊 統計閾値"
        ])
        
        with tabs[0]:
            self._render_time_settings()
        
        with tabs[1]:
            self._render_wage_settings()
        
        with tabs[2]:
            self._render_cost_settings()
        
        with tabs[3]:
            self._render_facility_settings()
        
        with tabs[4]:
            self._render_statistical_settings()
        
        # 保存ボタン
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            if st.button("💾 設定を保存", type="primary"):
                if self._save_settings():
                    st.success("✅ 設定を保存しました")
                    self.settings_changed = True
                else:
                    st.error("❌ 設定の保存に失敗しました")
        
        with col3:
            if st.button("🔄 デフォルトに戻す"):
                if self._reset_to_defaults():
                    st.success("✅ デフォルト設定に戻しました")
                    self.settings_changed = True
                    st.rerun()
        
        return self.settings_changed
    
    def _render_time_settings(self):
        """時間設定のレンダリング"""
        st.markdown("#### 時間設定")
        
        current_slot = get_setting('time_settings.slot_minutes', 30)
        new_slot = st.number_input(
            "スロット時間（分）",
            min_value=5,
            max_value=120,
            value=current_slot,
            step=5,
            help="分析の時間単位（デフォルト: 30分）"
        )
        if new_slot != current_slot:
            self.config.update_runtime('time_settings.slot_minutes', new_slot)
        
        current_night_start = get_setting('time_settings.night_start_hour', 22)
        new_night_start = st.number_input(
            "夜勤開始時刻",
            min_value=0,
            max_value=23,
            value=current_night_start,
            help="夜勤手当の開始時刻（デフォルト: 22時）"
        )
        if new_night_start != current_night_start:
            self.config.update_runtime('time_settings.night_start_hour', new_night_start)
        
        current_night_end = get_setting('time_settings.night_end_hour', 6)
        new_night_end = st.number_input(
            "夜勤終了時刻",
            min_value=0,
            max_value=23,
            value=current_night_end,
            help="夜勤手当の終了時刻（デフォルト: 6時）"
        )
        if new_night_end != current_night_end:
            self.config.update_runtime('time_settings.night_end_hour', new_night_end)
    
    def _render_wage_settings(self):
        """賃金設定のレンダリング"""
        st.markdown("#### 賃金設定")
        
        # 正規職員
        st.markdown("##### 正規職員")
        col1, col2 = st.columns(2)
        with col1:
            current_regular = get_setting('wage_settings.regular_staff.default', 1500)
            new_regular = st.number_input(
                "基本時給（円）",
                min_value=1000,
                max_value=5000,
                value=current_regular,
                step=100,
                help="正規職員の基本時給"
            )
            if new_regular != current_regular:
                self.config.update_runtime('wage_settings.regular_staff.default', new_regular)
        
        # 派遣職員
        st.markdown("##### 派遣職員")
        col1, col2 = st.columns(2)
        with col1:
            current_temp = get_setting('wage_settings.temporary_staff.default', 2200)
            new_temp = st.number_input(
                "基本時給（円）",
                min_value=1500,
                max_value=6000,
                value=current_temp,
                step=100,
                help="派遣職員の基本時給"
            )
            if new_temp != current_temp:
                self.config.update_runtime('wage_settings.temporary_staff.default', new_temp)
        
        # 各種手当
        st.markdown("##### 各種手当倍率")
        col1, col2, col3 = st.columns(3)
        with col1:
            current_night = get_setting('wage_settings.night_differential', 1.25)
            new_night = st.number_input(
                "夜勤手当倍率",
                min_value=1.0,
                max_value=2.0,
                value=float(current_night),
                step=0.05,
                format="%.2f",
                help="夜勤時の賃金倍率"
            )
            if new_night != current_night:
                self.config.update_runtime('wage_settings.night_differential', new_night)
        
        with col2:
            current_overtime = get_setting('wage_settings.overtime_multiplier', 1.25)
            new_overtime = st.number_input(
                "残業手当倍率",
                min_value=1.0,
                max_value=2.0,
                value=float(current_overtime),
                step=0.05,
                format="%.2f",
                help="残業時の賃金倍率"
            )
            if new_overtime != current_overtime:
                self.config.update_runtime('wage_settings.overtime_multiplier', new_overtime)
        
        with col3:
            current_weekend = get_setting('wage_settings.weekend_differential', 1.10)
            new_weekend = st.number_input(
                "週末手当倍率",
                min_value=1.0,
                max_value=2.0,
                value=float(current_weekend),
                step=0.05,
                format="%.2f",
                help="週末勤務の賃金倍率"
            )
            if new_weekend != current_weekend:
                self.config.update_runtime('wage_settings.weekend_differential', new_weekend)
    
    def _render_cost_settings(self):
        """コスト設定のレンダリング"""
        st.markdown("#### コスト設定")
        
        current_recruit = get_setting('cost_settings.recruit_cost_per_hire', 200000)
        new_recruit = st.number_input(
            "採用コスト（円/人）",
            min_value=50000,
            max_value=1000000,
            value=current_recruit,
            step=10000,
            help="1人あたりの採用コスト"
        )
        if new_recruit != current_recruit:
            self.config.update_runtime('cost_settings.recruit_cost_per_hire', new_recruit)
        
        current_penalty = get_setting('cost_settings.penalty_per_shortage_hour', 4000)
        new_penalty = st.number_input(
            "不足ペナルティ（円/時間）",
            min_value=1000,
            max_value=10000,
            value=current_penalty,
            step=500,
            help="1時間あたりの人員不足ペナルティ"
        )
        if new_penalty != current_penalty:
            self.config.update_runtime('cost_settings.penalty_per_shortage_hour', new_penalty)
        
        current_monthly = get_setting('cost_settings.monthly_hours_fte', 160)
        new_monthly = st.number_input(
            "月間標準労働時間",
            min_value=120,
            max_value=200,
            value=current_monthly,
            help="フルタイム職員の月間標準労働時間"
        )
        if new_monthly != current_monthly:
            self.config.update_runtime('cost_settings.monthly_hours_fte', new_monthly)
    
    def _render_facility_settings(self):
        """施設タイプ設定のレンダリング"""
        st.markdown("#### 施設タイプ設定")
        
        facility_type = st.selectbox(
            "施設タイプ",
            options=["day_care", "residential"],
            format_func=lambda x: {
                "day_care": "デイサービス",
                "residential": "入所施設"
            }.get(x, x)
        )
        
        if facility_type:
            prefix = f'facility_types.{facility_type}'
            
            col1, col2 = st.columns(2)
            with col1:
                current_ratio = get_setting(f'{prefix}.staff_ratio', 3.0)
                new_ratio = st.number_input(
                    "職員配置基準",
                    min_value=1.0,
                    max_value=10.0,
                    value=float(current_ratio),
                    step=0.5,
                    format="%.1f",
                    help="利用者数に対する職員の配置基準"
                )
                if new_ratio != current_ratio:
                    self.config.update_runtime(f'{prefix}.staff_ratio', new_ratio)
            
            with col2:
                current_capacity = get_setting(f'{prefix}.max_capacity', 30)
                new_capacity = st.number_input(
                    "最大定員",
                    min_value=10,
                    max_value=200,
                    value=current_capacity,
                    help="施設の最大定員数"
                )
                if new_capacity != current_capacity:
                    self.config.update_runtime(f'{prefix}.max_capacity', new_capacity)
            
            col1, col2 = st.columns(2)
            with col1:
                current_hours = get_setting(f'{prefix}.operating_hours', 10)
                new_hours = st.number_input(
                    "営業時間",
                    min_value=1,
                    max_value=24,
                    value=current_hours,
                    help="1日の営業時間"
                )
                if new_hours != current_hours:
                    self.config.update_runtime(f'{prefix}.operating_hours', new_hours)
            
            with col2:
                current_warning = get_setting(f'{prefix}.shortage_warning_ratio', 0.15)
                new_warning = st.number_input(
                    "不足警告閾値",
                    min_value=0.05,
                    max_value=0.50,
                    value=float(current_warning),
                    step=0.05,
                    format="%.2f",
                    help="不足警告を表示する閾値（比率）"
                )
                if new_warning != current_warning:
                    self.config.update_runtime(f'{prefix}.shortage_warning_ratio', new_warning)
    
    def _render_statistical_settings(self):
        """統計閾値設定のレンダリング"""
        st.markdown("#### 統計閾値設定")
        
        col1, col2 = st.columns(2)
        with col1:
            current_confidence = get_setting('statistical_thresholds.confidence_level', 0.95)
            new_confidence = st.number_input(
                "信頼水準",
                min_value=0.80,
                max_value=0.99,
                value=float(current_confidence),
                step=0.01,
                format="%.2f",
                help="統計的信頼水準"
            )
            if new_confidence != current_confidence:
                self.config.update_runtime('statistical_thresholds.confidence_level', new_confidence)
        
        with col2:
            current_alpha = get_setting('statistical_thresholds.significance_alpha', 0.05)
            new_alpha = st.number_input(
                "有意水準（α）",
                min_value=0.01,
                max_value=0.20,
                value=float(current_alpha),
                step=0.01,
                format="%.2f",
                help="統計的有意性の判定基準"
            )
            if new_alpha != current_alpha:
                self.config.update_runtime('statistical_thresholds.significance_alpha', new_alpha)
        
        current_correlation = get_setting('statistical_thresholds.correlation_threshold', 0.7)
        new_correlation = st.number_input(
            "相関閾値",
            min_value=0.5,
            max_value=0.95,
            value=float(current_correlation),
            step=0.05,
            format="%.2f",
            help="強い相関と判定する閾値"
        )
        if new_correlation != current_correlation:
            self.config.update_runtime('statistical_thresholds.correlation_threshold', new_correlation)
    
    def _save_settings(self) -> bool:
        """
        設定をファイルに保存
        
        Returns:
            保存成功の可否
        """
        try:
            config_dir = Path('config')
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / 'facility_settings.yaml'
            settings = self.config.get_all()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(settings, f, allow_unicode=True, default_flow_style=False)
            
            log.info(f"設定をファイルに保存しました: {config_file}")
            return True
            
        except Exception as e:
            log.error(f"設定の保存に失敗: {e}")
            return False
    
    def _reset_to_defaults(self) -> bool:
        """
        デフォルト設定に戻す
        
        Returns:
            リセット成功の可否
        """
        try:
            from .config_loader import DEFAULT_SETTINGS
            
            # デフォルト設定で上書き
            for key, value in DEFAULT_SETTINGS.items():
                self.config._settings[key] = value
            
            # ファイルに保存
            return self._save_settings()
            
        except Exception as e:
            log.error(f"デフォルト設定へのリセットに失敗: {e}")
            return False

def render_settings_page():
    """設定ページをレンダリング（Streamlitページ用）"""
    st.title("⚙️ システム設定")
    
    st.markdown("""
    このページでは、Shift-Suiteの各種設定を変更できます。
    設定を変更した後は「設定を保存」ボタンをクリックして保存してください。
    """)
    
    settings_ui = SettingsUI()
    
    if settings_ui.render_settings_editor():
        st.info("ℹ️ 設定が変更されました。アプリケーションを再起動すると新しい設定が適用されます。")
    
    # 現在の設定を表示
    with st.expander("📋 現在の設定内容", expanded=False):
        st.json(settings_ui.config.get_all())