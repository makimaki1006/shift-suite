"""
ステータス表示モジュール
システムの状態と分析結果のサマリーを表示
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime

log = logging.getLogger(__name__)

class StatusDisplay:
    """ステータス表示クラス"""
    
    def __init__(self, scenario_dir: Optional[Path] = None):
        """
        初期化
        
        Args:
            scenario_dir: シナリオディレクトリ
        """
        self.scenario_dir = scenario_dir
        self.status_data = {}
        self._load_status_data()
    
    def _load_status_data(self):
        """ステータスデータを読み込む"""
        if not self.scenario_dir or not self.scenario_dir.exists():
            return
        
        # 分析警告データ
        warnings_file = self.scenario_dir / "analysis_warnings.json"
        if warnings_file.exists():
            try:
                with open(warnings_file, 'r', encoding='utf-8') as f:
                    self.status_data['warnings'] = json.load(f)
            except Exception as e:
                log.debug(f"警告データ読み込みエラー: {e}")
        
        # 分析結果サマリー
        summary_file = self.scenario_dir / "analysis_summary.json"
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    self.status_data['summary'] = json.load(f)
            except Exception as e:
                log.debug(f"サマリーデータ読み込みエラー: {e}")
    
    def render_dashboard(self):
        """ステータスダッシュボードをレンダリング"""
        st.markdown("## 📊 システムステータスダッシュボード")
        
        # メトリクスの表示
        self._render_metrics()
        
        # タブで各種情報を表示
        tabs = st.tabs([
            "⚠️ 警告・アラート",
            "📈 分析結果サマリー",
            "⚙️ システム設定",
            "📋 実行ログ",
            "🔍 データ品質"
        ])
        
        with tabs[0]:
            self._render_warnings()
        
        with tabs[1]:
            self._render_analysis_summary()
        
        with tabs[2]:
            self._render_system_settings()
        
        with tabs[3]:
            self._render_execution_log()
        
        with tabs[4]:
            self._render_data_quality()
    
    def _render_metrics(self):
        """主要メトリクスを表示"""
        col1, col2, col3, col4 = st.columns(4)
        
        # 警告数
        warnings = self.status_data.get('warnings', {})
        shortage_warnings = warnings.get('shortage_warnings', {})
        warning_count = shortage_warnings.get('warning_count', 0)
        
        with col1:
            st.metric(
                "警告数",
                warning_count,
                delta=None if warning_count == 0 else f"+{warning_count}",
                delta_color="inverse"
            )
        
        # リスクレベル
        risk_level = warnings.get('period_risk', {}).get('risk_level', 'low')
        risk_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }.get(risk_level, '⚪')
        
        with col2:
            st.metric(
                "リスクレベル",
                f"{risk_emoji} {risk_level.upper()}"
            )
        
        # 不足時間
        summary = self.status_data.get('summary', {})
        total_shortage = summary.get('total_shortage_hours', 0)
        
        with col3:
            st.metric(
                "総不足時間",
                f"{total_shortage:,.1f}h",
                delta=None if total_shortage == 0 else f"+{total_shortage:.1f}h",
                delta_color="inverse"
            )
        
        # データ品質スコア
        data_quality = self._calculate_data_quality_score()
        
        with col4:
            st.metric(
                "データ品質",
                f"{data_quality}%",
                delta=None if data_quality >= 80 else f"{data_quality - 100}%",
                delta_color="normal" if data_quality >= 80 else "inverse"
            )
    
    def _render_warnings(self):
        """警告・アラートを表示"""
        st.markdown("### 警告・アラート")
        
        warnings = self.status_data.get('warnings', {})
        
        if not warnings:
            st.success("✅ 警告はありません")
            return
        
        # 不足時間警告
        shortage_warnings = warnings.get('shortage_warnings', {})
        if shortage_warnings.get('has_warnings'):
            with st.expander(f"⚠️ 不足時間警告 ({shortage_warnings.get('warning_count', 0)}件)", expanded=True):
                details = shortage_warnings.get('warning_details', [])
                for detail in details[:10]:  # 最大10件表示
                    severity = detail.get('severity', 'unknown')
                    icon = "🔴" if severity == 'high' else "🟡"
                    col1, col2, col3 = st.columns([1, 2, 2])
                    with col1:
                        st.write(icon)
                    with col2:
                        st.write(detail.get('date', 'N/A'))
                    with col3:
                        st.write(f"{detail.get('shortage_hours', 0):.1f}時間")
        
        # 需要データ警告
        need_warnings = warnings.get('need_validation', {}).get('warnings', [])
        if need_warnings:
            with st.expander(f"⚠️ 需要データ警告 ({len(need_warnings)}件)"):
                for warning in need_warnings:
                    st.write(f"• {warning}")
        
        # リスク評価
        risk_info = warnings.get('period_risk', {})
        risk_level = risk_info.get('risk_level')
        if risk_level in ['high', 'critical']:
            st.error(f"🚨 期間依存性リスク: {risk_level.upper()}")
            st.write(risk_info.get('recommendation', ''))
            
            with st.expander("リスク詳細"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("日平均不足", f"{risk_info.get('daily_shortage', 0):.1f}h")
                with col2:
                    st.metric("月間推定不足", f"{risk_info.get('monthly_shortage', 0):.1f}h")
                with col3:
                    st.metric("分析期間", f"{risk_info.get('period_days', 0)}日")
    
    def _render_analysis_summary(self):
        """分析結果サマリーを表示"""
        st.markdown("### 分析結果サマリー")
        
        summary = self.status_data.get('summary', {})
        
        if not summary:
            st.info("ℹ️ 分析結果がまだありません")
            return
        
        # 基本統計
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("分析期間", f"{summary.get('analysis_days', 0)}日")
        with col2:
            st.metric("対象職員数", f"{summary.get('staff_count', 0)}人")
        with col3:
            st.metric("職種数", f"{summary.get('role_count', 0)}")
        
        # 不足分析結果
        if 'shortage_analysis' in summary:
            st.markdown("#### 不足分析")
            shortage = summary['shortage_analysis']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総不足時間", f"{shortage.get('total_hours', 0):,.1f}h")
            with col2:
                st.metric("日平均不足", f"{shortage.get('daily_average', 0):.1f}h")
            with col3:
                st.metric("最大不足日", f"{shortage.get('max_shortage', 0):.1f}h")
        
        # コスト分析結果
        if 'cost_analysis' in summary:
            st.markdown("#### コスト分析")
            cost = summary['cost_analysis']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総コスト", f"¥{cost.get('total_cost', 0):,.0f}")
            with col2:
                st.metric("不足ペナルティ", f"¥{cost.get('penalty_cost', 0):,.0f}")
            with col3:
                st.metric("採用コスト", f"¥{cost.get('hiring_cost', 0):,.0f}")
    
    def _render_system_settings(self):
        """システム設定を表示"""
        st.markdown("### システム設定")
        
        from .constants import _settings, FACILITY_SETTINGS_PATH
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 設定ファイル")
            if FACILITY_SETTINGS_PATH.exists():
                st.success(f"✅ カスタム設定使用中")
                st.caption(f"パス: {FACILITY_SETTINGS_PATH}")
            else:
                st.info(f"ℹ️ デフォルト設定使用中")
        
        with col2:
            st.markdown("#### 主要パラメータ")
            if _settings:
                params = []
                params.append(f"スロット時間: {_settings.get('time_settings', {}).get('slot_minutes', 30)}分")
                params.append(f"正規時給: ¥{_settings.get('wage_settings', {}).get('regular_staff', {}).get('default', 1500):,}")
                params.append(f"派遣時給: ¥{_settings.get('wage_settings', {}).get('temporary_staff', {}).get('default', 2200):,}")
                
                for param in params:
                    st.write(f"• {param}")
        
        # モジュール利用可能性
        st.markdown("#### モジュール状態")
        modules = self._check_module_availability()
        
        col1, col2, col3 = st.columns(3)
        icons = {"available": "✅", "unavailable": "❌", "partial": "⚠️"}
        
        for i, (module_name, status) in enumerate(modules.items()):
            col = [col1, col2, col3][i % 3]
            with col:
                st.write(f"{icons.get(status, '❓')} {module_name}")
    
    def _render_execution_log(self):
        """実行ログを表示"""
        st.markdown("### 実行ログ")
        
        log_file = self.scenario_dir / "execution_log.txt" if self.scenario_dir else None
        
        if not log_file or not log_file.exists():
            st.info("ℹ️ 実行ログがありません")
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # 最新のログを表示
            st.text_area(
                "最新の実行ログ",
                value=log_content[-5000:],  # 最後の5000文字
                height=300,
                disabled=True
            )
            
            # ダウンロードボタン
            st.download_button(
                label="📥 完全なログをダウンロード",
                data=log_content,
                file_name=f"execution_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"ログの読み込みエラー: {e}")
    
    def _render_data_quality(self):
        """データ品質情報を表示"""
        st.markdown("### データ品質")
        
        quality_score = self._calculate_data_quality_score()
        
        # スコアゲージ
        st.progress(quality_score / 100)
        st.write(f"データ品質スコア: {quality_score}%")
        
        # 品質チェック項目
        checks = self._perform_quality_checks()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 完全性チェック")
            for check_name, passed in checks['completeness'].items():
                icon = "✅" if passed else "❌"
                st.write(f"{icon} {check_name}")
        
        with col2:
            st.markdown("#### 妥当性チェック")
            for check_name, passed in checks['validity'].items():
                icon = "✅" if passed else "❌"
                st.write(f"{icon} {check_name}")
        
        # 推奨事項
        if quality_score < 80:
            st.warning("⚠️ データ品質に改善の余地があります")
            recommendations = self._get_quality_recommendations(checks)
            for rec in recommendations:
                st.write(f"• {rec}")
    
    def _calculate_data_quality_score(self) -> int:
        """
        データ品質スコアを計算
        
        Returns:
            品質スコア（0-100）
        """
        checks = self._perform_quality_checks()
        
        total_checks = 0
        passed_checks = 0
        
        for category in checks.values():
            for passed in category.values():
                total_checks += 1
                if passed:
                    passed_checks += 1
        
        if total_checks == 0:
            return 100
        
        return int((passed_checks / total_checks) * 100)
    
    def _perform_quality_checks(self) -> Dict[str, Dict[str, bool]]:
        """
        データ品質チェックを実行
        
        Returns:
            チェック結果
        """
        checks = {
            'completeness': {},
            'validity': {}
        }
        
        if not self.scenario_dir or not self.scenario_dir.exists():
            return checks
        
        # 完全性チェック
        required_files = [
            'intermediate_data.parquet',
            'shortage_role_summary.parquet',
            'hire_plan.parquet'
        ]
        
        for file_name in required_files:
            file_path = self.scenario_dir / file_name
            checks['completeness'][file_name.replace('.parquet', '')] = file_path.exists()
        
        # 妥当性チェック
        warnings = self.status_data.get('warnings', {})
        
        # 不足時間の妥当性
        shortage_warnings = warnings.get('shortage_warnings', {})
        checks['validity']['不足時間妥当性'] = not shortage_warnings.get('has_warnings', False)
        
        # 需要データの妥当性
        need_warnings = warnings.get('need_validation', {})
        checks['validity']['需要データ妥当性'] = len(need_warnings.get('warnings', [])) == 0
        
        # リスクレベル
        risk_level = warnings.get('period_risk', {}).get('risk_level', 'low')
        checks['validity']['リスク評価'] = risk_level in ['low', 'medium']
        
        return checks
    
    def _get_quality_recommendations(self, checks: Dict[str, Dict[str, bool]]) -> List[str]:
        """
        品質改善の推奨事項を取得
        
        Args:
            checks: チェック結果
            
        Returns:
            推奨事項リスト
        """
        recommendations = []
        
        # 完全性の問題
        for check_name, passed in checks['completeness'].items():
            if not passed:
                recommendations.append(f"{check_name}データが不足しています。分析を再実行してください。")
        
        # 妥当性の問題
        if not checks['validity'].get('不足時間妥当性', True):
            recommendations.append("異常な不足時間が検出されています。入力データを確認してください。")
        
        if not checks['validity'].get('需要データ妥当性', True):
            recommendations.append("需要データに異常値があります。需要計算の設定を見直してください。")
        
        if not checks['validity'].get('リスク評価', True):
            recommendations.append("高リスクと評価されています。より長期間のデータで分析することを推奨します。")
        
        return recommendations
    
    def _check_module_availability(self) -> Dict[str, str]:
        """
        モジュールの利用可能性をチェック
        
        Returns:
            モジュール名と状態のマッピング
        """
        modules = {}
        
        # 異常検知
        try:
            from shift_suite.tasks import anomaly_detector
            modules['異常検知'] = 'available'
        except ImportError:
            modules['異常検知'] = 'unavailable'
        
        # クラスタリング
        try:
            from sklearn.cluster import KMeans
            modules['クラスタリング'] = 'available'
        except ImportError:
            modules['クラスタリング'] = 'unavailable'
        
        # 予測モデル
        try:
            import pmdarima
            modules['ARIMA予測'] = 'available'
        except ImportError:
            modules['ARIMA予測'] = 'partial'
        
        # XGBoost
        try:
            import xgboost
            modules['XGBoost'] = 'available'
        except ImportError:
            modules['XGBoost'] = 'unavailable'
        
        # 深層学習
        try:
            import torch
            modules['深層学習'] = 'available'
        except ImportError:
            modules['深層学習'] = 'unavailable'
        
        return modules

def render_status_dashboard(scenario_dir: Optional[Path] = None):
    """
    ステータスダッシュボードをレンダリング（Streamlitページ用）
    
    Args:
        scenario_dir: シナリオディレクトリ
    """
    display = StatusDisplay(scenario_dir)
    display.render_dashboard()