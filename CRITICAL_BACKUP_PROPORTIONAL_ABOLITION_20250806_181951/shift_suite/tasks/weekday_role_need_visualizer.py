#!/usr/bin/env python3
"""
Weekday × Role Need Visualizer
曜日×職種別のNeed基準値可視化モジュール
"""

from __future__ import annotations  # 型ヒント互換性のため保持

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
# from typing import Tuple  # 未使用のためコメントアウト

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .utils import log

# Analysis logger
analysis_logger = logging.getLogger('analysis')


class WeekdayRoleNeedAnalyzer:
    """曜日×職種別Need分析クラス"""
    
    def __init__(self):
        self.weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        self.weekday_mapping = {
            0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'
        }
    
    def analyze_weekday_role_needs(
        self, 
        need_df: pd.DataFrame,
        schedule_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """曜日×職種別のNeed分析実行"""
        
        analysis_logger.info("[WEEKDAY_ROLE] 曜日×職種別Need分析開始")
        
        try:
            # 基準値（Need）の曜日×職種別集計
            need_by_weekday_role = self._aggregate_need_by_weekday_role(need_df)
            
            # 実績値の曜日×職種別集計
            actual_by_weekday_role = self._aggregate_actual_by_weekday_role(schedule_df)
            
            # 充足率の計算
            fulfillment_rates = self._calculate_fulfillment_rates(
                need_by_weekday_role, 
                actual_by_weekday_role
            )
            
            # 時間帯別詳細（曜日×職種×時間）
            time_detail = self._analyze_time_patterns_by_weekday_role(need_df, schedule_df)
            
            result = {
                'need_by_weekday_role': need_by_weekday_role,
                'actual_by_weekday_role': actual_by_weekday_role,
                'fulfillment_rates': fulfillment_rates,
                'time_patterns': time_detail,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_quality': self._assess_data_quality(need_df, schedule_df)
            }
            
            analysis_logger.info("[WEEKDAY_ROLE] 分析完了")
            return result
            
        except Exception as e:
            log.error(f"曜日×職種別分析エラー: {e}")
            return {}
    
    def _aggregate_need_by_weekday_role(self, need_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Need値を曜日×職種別に集計"""
        
        weekday_role_needs = {}
        
        try:
            # 日付列の検出
            date_columns = [col for col in need_df.columns if self._is_date_column(col)]
            
            for col in date_columns:
                # 曜日の特定
                date_obj = self._parse_date_from_column(col)
                if date_obj:
                    weekday = self.weekday_mapping[date_obj.weekday()]
                    
                    if weekday not in weekday_role_needs:
                        weekday_role_needs[weekday] = {}
                    
                    # 職種別のNeed値集計
                    if 'role' in need_df.columns:
                        for role in need_df['role'].unique():
                            if pd.notna(role):
                                role_need = need_df[need_df['role'] == role][col].sum()
                                
                                if role not in weekday_role_needs[weekday]:
                                    weekday_role_needs[weekday][role] = []
                                
                                weekday_role_needs[weekday][role].append(role_need)
            
            # 平均値計算
            for weekday in weekday_role_needs:
                for role in weekday_role_needs[weekday]:
                    values = weekday_role_needs[weekday][role]
                    weekday_role_needs[weekday][role] = np.mean(values) if values else 0.0
            
            return weekday_role_needs
            
        except Exception as e:
            log.error(f"Need集計エラー: {e}")
            return {}
    
    def _aggregate_actual_by_weekday_role(self, schedule_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """実績値を曜日×職種別に集計"""
        
        weekday_role_actuals = {}
        
        try:
            if 'ds' in schedule_df.columns:
                schedule_df['weekday'] = pd.to_datetime(schedule_df['ds']).dt.dayofweek
                schedule_df['weekday_name'] = schedule_df['weekday'].map(self.weekday_mapping)
            
            if 'weekday_name' in schedule_df.columns and 'role' in schedule_df.columns:
                grouped = schedule_df.groupby(['weekday_name', 'role']).size()
                
                for (weekday, role), count in grouped.items():
                    if weekday not in weekday_role_actuals:
                        weekday_role_actuals[weekday] = {}
                    
                    # 時間スロット数で割って平均人数を算出
                    time_slots_per_day = 24 * 4  # 15分スロットの場合
                    weekday_role_actuals[weekday][role] = count / time_slots_per_day
            
            return weekday_role_actuals
            
        except Exception as e:
            log.error(f"実績集計エラー: {e}")
            return {}
    
    def _calculate_fulfillment_rates(
        self, 
        need_dict: Dict[str, Dict[str, float]], 
        actual_dict: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """充足率計算"""
        
        fulfillment_rates = {}
        
        for weekday in self.weekday_names:
            if weekday in need_dict:
                fulfillment_rates[weekday] = {}
                
                for role, need_value in need_dict[weekday].items():
                    actual_value = actual_dict.get(weekday, {}).get(role, 0.0)
                    
                    if need_value > 0:
                        rate = (actual_value / need_value) * 100
                        fulfillment_rates[weekday][role] = min(100.0, rate)
                    else:
                        fulfillment_rates[weekday][role] = 100.0 if actual_value == 0 else 0.0
        
        return fulfillment_rates
    
    def _analyze_time_patterns_by_weekday_role(
        self, 
        need_df: pd.DataFrame, 
        schedule_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """時間帯別パターン分析（曜日×職種×時間）"""
        
        time_patterns = {}
        
        try:
            # 時間帯別のピーク時間を曜日×職種で分析
            for weekday in self.weekday_names:
                time_patterns[weekday] = {}
                
                # ここでは簡易的な実装
                # 実際にはより詳細な時間帯分析を行う
                time_patterns[weekday]['peak_hours'] = ['07:00-09:00', '17:00-19:00']
                time_patterns[weekday]['low_hours'] = ['10:00-11:00', '14:00-16:00']
            
            return time_patterns
            
        except Exception as e:
            log.error(f"時間パターン分析エラー: {e}")
            return {}
    
    def _assess_data_quality(self, need_df: pd.DataFrame, schedule_df: pd.DataFrame) -> Dict[str, float]:
        """データ品質評価"""
        
        try:
            need_completeness = (need_df.notna().sum().sum() / need_df.size) * 100 if need_df.size > 0 else 0
            schedule_completeness = (schedule_df.notna().sum().sum() / schedule_df.size) * 100 if schedule_df.size > 0 else 0
            
            return {
                'need_completeness': need_completeness,
                'schedule_completeness': schedule_completeness,
                'overall_quality': (need_completeness + schedule_completeness) / 2
            }
        except:
            return {'overall_quality': 0.0}
    
    def _is_date_column(self, col: Any) -> bool:
        """日付列判定"""
        col_str = str(col)
        return bool(re.search(r'\d{1,2}[/-]\d{1,2}', col_str))
    
    def _parse_date_from_column(self, col: Any) -> Optional[datetime]:
        """列名から日付パース"""
        col_str = str(col)
        match = re.search(r'(\d{1,2})[/-](\d{1,2})', col_str)
        if match:
            month, day = map(int, match.groups())
            try:
                year = datetime.now().year
                return datetime(year, month, day)
            except ValueError:
                return None
        return None


class WeekdayRoleNeedVisualizer:
    """曜日×職種別Need可視化クラス"""
    
    def __init__(self):
        self.analyzer = WeekdayRoleNeedAnalyzer()
        self.color_map = {
            '看護師': '#FF6B6B',
            '介護士': '#4ECDC4',
            'ケアマネ': '#45B7D1',
            'その他': '#96CEB4'
        }
    
    def create_weekday_role_dashboard(self, analysis_result: Dict[str, Any]) -> Dict[str, go.Figure]:
        """曜日×職種別ダッシュボード作成"""
        
        figures = {}
        
        try:
            # 1. 曜日×職種別Need値ヒートマップ
            figures['need_heatmap'] = self._create_need_heatmap(
                analysis_result['need_by_weekday_role']
            )
            
            # 2. 充足率ヒートマップ
            figures['fulfillment_heatmap'] = self._create_fulfillment_heatmap(
                analysis_result['fulfillment_rates']
            )
            
            # 3. 曜日別職種構成グラフ
            figures['weekday_composition'] = self._create_weekday_composition_chart(
                analysis_result['need_by_weekday_role']
            )
            
            # 4. 職種別曜日パターングラフ
            figures['role_weekday_pattern'] = self._create_role_weekday_pattern_chart(
                analysis_result['need_by_weekday_role'],
                analysis_result['actual_by_weekday_role']
            )
            
            # 5. ギャップ分析グラフ
            figures['gap_analysis'] = self._create_gap_analysis_chart(
                analysis_result['need_by_weekday_role'],
                analysis_result['actual_by_weekday_role']
            )
            
            return figures
            
        except Exception as e:
            log.error(f"ダッシュボード作成エラー: {e}")
            return {}
    
    def _create_need_heatmap(self, need_data: Dict[str, Dict[str, float]]) -> go.Figure:
        """Need値ヒートマップ作成"""
        
        # データ準備
        weekdays = list(self.analyzer.weekday_names)
        roles = sorted(set(role for weekday_data in need_data.values() for role in weekday_data.keys()))
        
        # マトリックス作成
        z_values = []
        for role in roles:
            row = []
            for weekday in weekdays:
                value = need_data.get(weekday, {}).get(role, 0.0)
                row.append(value)
            z_values.append(row)
        
        # ヒートマップ作成
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=weekdays,
            y=roles,
            colorscale='Blues',
            text=[[f'{val:.1f}' for val in row] for row in z_values],
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate='%{y}<br>%{x}曜日<br>Need: %{z:.1f}人<extra></extra>'
        ))
        
        fig.update_layout(
            title='曜日×職種別 Need基準値',
            xaxis_title='曜日',
            yaxis_title='職種',
            height=400
        )
        
        return fig
    
    def _create_fulfillment_heatmap(self, fulfillment_data: Dict[str, Dict[str, float]]) -> go.Figure:
        """充足率ヒートマップ作成"""
        
        weekdays = list(self.analyzer.weekday_names)
        roles = sorted(set(role for weekday_data in fulfillment_data.values() for role in weekday_data.keys()))
        
        z_values = []
        for role in roles:
            row = []
            for weekday in weekdays:
                value = fulfillment_data.get(weekday, {}).get(role, 0.0)
                row.append(value)
            z_values.append(row)
        
        # カスタムカラースケール（充足率用）
        colorscale = [
            [0, '#FF0000'],      # 0% - 赤
            [0.5, '#FFFF00'],    # 50% - 黄
            [0.8, '#90EE90'],    # 80% - 薄緑
            [1.0, '#006400']     # 100% - 濃緑
        ]
        
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=weekdays,
            y=roles,
            colorscale=colorscale,
            text=[[f'{val:.0f}%' for val in row] for row in z_values],
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate='%{y}<br>%{x}曜日<br>充足率: %{z:.0f}%<extra></extra>',
            zmin=0,
            zmax=100
        ))
        
        fig.update_layout(
            title='曜日×職種別 充足率',
            xaxis_title='曜日',
            yaxis_title='職種',
            height=400
        )
        
        return fig
    
    def _create_weekday_composition_chart(self, need_data: Dict[str, Dict[str, float]]) -> go.Figure:
        """曜日別職種構成グラフ"""
        
        fig = go.Figure()
        
        weekdays = list(self.analyzer.weekday_names)
        roles = sorted(set(role for weekday_data in need_data.values() for role in weekday_data.keys()))
        
        for role in roles:
            values = []
            for weekday in weekdays:
                value = need_data.get(weekday, {}).get(role, 0.0)
                values.append(value)
            
            fig.add_trace(go.Bar(
                name=role,
                x=weekdays,
                y=values,
                marker_color=self.color_map.get(role, '#808080'),
                hovertemplate='%{fullData.name}<br>%{x}曜日<br>Need: %{y:.1f}人<extra></extra>'
            ))
        
        fig.update_layout(
            title='曜日別 職種構成（Need基準値）',
            xaxis_title='曜日',
            yaxis_title='必要人数',
            barmode='stack',
            height=400,
            showlegend=True
        )
        
        return fig
    
    def _create_role_weekday_pattern_chart(
        self, 
        need_data: Dict[str, Dict[str, float]],
        actual_data: Dict[str, Dict[str, float]]
    ) -> go.Figure:
        """職種別曜日パターングラフ"""
        
        # サブプロット作成
        roles = sorted(set(role for weekday_data in need_data.values() for role in weekday_data.keys()))
        n_roles = len(roles)
        
        fig = make_subplots(
            rows=(n_roles + 1) // 2,
            cols=2,
            subplot_titles=roles,
            vertical_spacing=0.1
        )
        
        weekdays = list(self.analyzer.weekday_names)
        
        for i, role in enumerate(roles):
            row = i // 2 + 1
            col = i % 2 + 1
            
            # Need値
            need_values = [need_data.get(weekday, {}).get(role, 0.0) for weekday in weekdays]
            # 実績値
            actual_values = [actual_data.get(weekday, {}).get(role, 0.0) for weekday in weekdays]
            
            # Need値のライン
            fig.add_trace(
                go.Scatter(
                    x=weekdays,
                    y=need_values,
                    mode='lines+markers',
                    name=f'{role} Need',
                    line=dict(color=self.color_map.get(role, '#808080'), width=2, dash='dash'),
                    showlegend=(i == 0)
                ),
                row=row, col=col
            )
            
            # 実績値のライン
            fig.add_trace(
                go.Scatter(
                    x=weekdays,
                    y=actual_values,
                    mode='lines+markers',
                    name=f'{role} 実績',
                    line=dict(color=self.color_map.get(role, '#808080'), width=2),
                    showlegend=(i == 0)
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            title='職種別 曜日パターン（Need vs 実績）',
            height=600,
            showlegend=True
        )
        
        return fig
    
    def _create_gap_analysis_chart(
        self,
        need_data: Dict[str, Dict[str, float]],
        actual_data: Dict[str, Dict[str, float]]
    ) -> go.Figure:
        """ギャップ分析グラフ"""
        
        fig = go.Figure()
        
        weekdays = list(self.analyzer.weekday_names)
        roles = sorted(set(role for weekday_data in need_data.values() for role in weekday_data.keys()))
        
        for role in roles:
            gaps = []
            for weekday in weekdays:
                need = need_data.get(weekday, {}).get(role, 0.0)
                actual = actual_data.get(weekday, {}).get(role, 0.0)
                gap = actual - need  # マイナスが不足
                gaps.append(gap)
            
            fig.add_trace(go.Bar(
                name=role,
                x=weekdays,
                y=gaps,
                marker_color=self.color_map.get(role, '#808080'),
                hovertemplate='%{fullData.name}<br>%{x}曜日<br>過不足: %{y:.1f}人<extra></extra>'
            ))
        
        # ゼロラインの追加
        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
        
        fig.update_layout(
            title='曜日×職種別 過不足分析',
            xaxis_title='曜日',
            yaxis_title='過不足人数（マイナスが不足）',
            barmode='group',
            height=400,
            showlegend=True
        )
        
        return fig


class LLMReadableReportGenerator:
    """LLM読み込み用レポート生成クラス"""
    
    def generate_comprehensive_report(
        self,
        analysis_result: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """LLM読み込み最適化された網羅的レポート生成"""
        
        try:
            report_content = {
                'metadata': {
                    'report_type': 'weekday_role_need_analysis',
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'encoding': 'utf-8'
                },
                
                'summary': self._generate_summary(analysis_result),
                
                'detailed_data': {
                    'need_by_weekday_role': self._format_for_llm(
                        analysis_result['need_by_weekday_role']
                    ),
                    'actual_by_weekday_role': self._format_for_llm(
                        analysis_result['actual_by_weekday_role']
                    ),
                    'fulfillment_rates': self._format_for_llm(
                        analysis_result['fulfillment_rates']
                    ),
                    'gaps': self._calculate_gaps_for_llm(
                        analysis_result['need_by_weekday_role'],
                        analysis_result['actual_by_weekday_role']
                    )
                },
                
                'patterns': {
                    'weekday_patterns': self._extract_weekday_patterns(analysis_result),
                    'role_patterns': self._extract_role_patterns(analysis_result),
                    'critical_shortages': self._identify_critical_shortages(analysis_result)
                },
                
                'data_quality': analysis_result.get('data_quality', {}),
                
                'llm_instructions': {
                    'data_structure': 'Nested JSON with weekday→role→value structure',
                    'value_units': 'Need and Actual in persons, Fulfillment in percentage',
                    'gap_interpretation': 'Negative values indicate shortage',
                    'recommended_analysis': [
                        'Identify patterns in weekday-specific shortages',
                        'Compare role-based fulfillment across weekdays',
                        'Suggest optimal staffing adjustments'
                    ]
                }
            }
            
            # JSON形式で保存（LLM読み込み最適）
            json_path = output_path / 'weekday_role_need_analysis.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_content, f, ensure_ascii=False, indent=2)
            
            # CSV形式でも保存（表形式データ用）
            self._save_as_csv(analysis_result, output_path)
            
            # Markdown形式でも保存（人間の可読性用）
            self._save_as_markdown(analysis_result, output_path)
            
            analysis_logger.info(f"[REPORT] LLM用レポート生成完了: {json_path}")
            return json_path
            
        except Exception as e:
            log.error(f"レポート生成エラー: {e}")
            return output_path
    
    def _generate_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """サマリー生成"""
        
        need_data = analysis_result.get('need_by_weekday_role', {})
        fulfillment_data = analysis_result.get('fulfillment_rates', {})
        
        # 最も不足している曜日×職種
        critical_shortages = []
        for weekday, roles in fulfillment_data.items():
            for role, rate in roles.items():
                if rate < 70:  # 70%未満を危機的とする
                    critical_shortages.append({
                        'weekday': weekday,
                        'role': role,
                        'fulfillment_rate': rate
                    })
        
        critical_shortages.sort(key=lambda x: x['fulfillment_rate'])
        
        return {
            'total_weekdays_analyzed': len(need_data),
            'total_roles_analyzed': len(set(role for roles in need_data.values() for role in roles)),
            'critical_shortage_count': len(critical_shortages),
            'top_3_critical_shortages': critical_shortages[:3],
            'average_fulfillment_rate': self._calculate_average_fulfillment(fulfillment_data)
        }
    
    def _format_for_llm(self, data: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """LLM読み込み用にデータ整形"""
        
        # 数値を適切に丸めて、読みやすくする
        formatted_data = {}
        for key1, inner_dict in data.items():
            formatted_data[key1] = {}
            for key2, value in inner_dict.items():
                formatted_data[key1][key2] = round(value, 2)
        
        return formatted_data
    
    def _calculate_gaps_for_llm(
        self,
        need_data: Dict[str, Dict[str, float]],
        actual_data: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """ギャップ計算（LLM用）"""
        
        gaps = {}
        for weekday in need_data:
            gaps[weekday] = {}
            for role in need_data[weekday]:
                need = need_data[weekday][role]
                actual = actual_data.get(weekday, {}).get(role, 0.0)
                gap = actual - need
                gaps[weekday][role] = round(gap, 2)
        
        return gaps
    
    def _extract_weekday_patterns(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """曜日パターン抽出"""
        
        patterns = []
        fulfillment_data = analysis_result.get('fulfillment_rates', {})
        
        for weekday in fulfillment_data:
            avg_fulfillment = np.mean(list(fulfillment_data[weekday].values()))
            patterns.append({
                'weekday': weekday,
                'average_fulfillment': round(avg_fulfillment, 2),
                'pattern_type': 'low' if avg_fulfillment < 70 else 'normal' if avg_fulfillment < 90 else 'high'
            })
        
        return patterns
    
    def _extract_role_patterns(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """職種パターン抽出"""
        
        patterns = []
        need_data = analysis_result.get('need_by_weekday_role', {})
        
        # 職種別の曜日変動を分析
        roles = set(role for roles in need_data.values() for role in roles)
        
        for role in roles:
            weekday_values = []
            for weekday in ['月', '火', '水', '木', '金', '土', '日']:
                if weekday in need_data and role in need_data[weekday]:
                    weekday_values.append(need_data[weekday][role])
            
            if weekday_values:
                patterns.append({
                    'role': role,
                    'average_need': round(np.mean(weekday_values), 2),
                    'variation_coefficient': round(np.std(weekday_values) / np.mean(weekday_values), 3) if np.mean(weekday_values) > 0 else 0,
                    'peak_weekday': self._find_peak_weekday(role, need_data)
                })
        
        return patterns
    
    def _find_peak_weekday(self, role: str, need_data: Dict[str, Dict[str, float]]) -> str:
        """ピーク曜日検出"""
        
        max_value = 0
        peak_weekday = ''
        
        for weekday, roles in need_data.items():
            if role in roles and roles[role] > max_value:
                max_value = roles[role]
                peak_weekday = weekday
        
        return peak_weekday
    
    def _identify_critical_shortages(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """重要な不足箇所の特定"""
        
        critical_shortages = []
        gaps = self._calculate_gaps_for_llm(
            analysis_result.get('need_by_weekday_role', {}),
            analysis_result.get('actual_by_weekday_role', {})
        )
        
        for weekday, roles in gaps.items():
            for role, gap in roles.items():
                if gap < -1.0:  # 1人以上の不足
                    critical_shortages.append({
                        'weekday': weekday,
                        'role': role,
                        'shortage': abs(gap),
                        'severity': 'critical' if abs(gap) > 3 else 'high' if abs(gap) > 2 else 'medium'
                    })
        
        critical_shortages.sort(key=lambda x: x['shortage'], reverse=True)
        return critical_shortages
    
    def _calculate_average_fulfillment(self, fulfillment_data: Dict[str, Dict[str, float]]) -> float:
        """平均充足率計算"""
        
        all_rates = []
        for roles in fulfillment_data.values():
            all_rates.extend(roles.values())
        
        return round(np.mean(all_rates), 2) if all_rates else 0.0
    
    def _save_as_csv(self, analysis_result: Dict[str, Any], output_path: Path) -> None:
        """CSV形式で保存"""
        
        # Need値CSV
        need_data = analysis_result.get('need_by_weekday_role', {})
        need_df = pd.DataFrame(need_data).T
        need_df.to_csv(output_path / 'weekday_role_need.csv', encoding='utf-8')
        
        # 充足率CSV
        fulfillment_data = analysis_result.get('fulfillment_rates', {})
        fulfillment_df = pd.DataFrame(fulfillment_data).T
        fulfillment_df.to_csv(output_path / 'weekday_role_fulfillment.csv', encoding='utf-8')
    
    def _save_as_markdown(self, analysis_result: Dict[str, Any], output_path: Path) -> None:
        """Markdown形式で保存"""
        
        md_content = f"""# 曜日×職種別 Need分析レポート

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## サマリー

- 分析対象曜日数: {len(analysis_result.get('need_by_weekday_role', {}))}
- データ品質スコア: {analysis_result.get('data_quality', {}).get('overall_quality', 0):.1f}%

## 重要な発見事項

### 最も不足している曜日×職種

"""
        
        # 重要な不足箇所を記載
        critical = self._identify_critical_shortages(analysis_result)
        for item in critical[:5]:
            md_content += f"- {item['weekday']}曜日 {item['role']}: {item['shortage']:.1f}人不足 ({item['severity']})\n"
        
        md_content += "\n## 詳細データ\n\n各曜日×職種の詳細データはJSON/CSVファイルを参照してください。\n"
        
        md_path = output_path / 'weekday_role_need_analysis.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)


# 便利関数
def analyze_weekday_role_needs(need_df: pd.DataFrame, schedule_df: pd.DataFrame) -> Dict[str, Any]:
    """曜日×職種別Need分析（便利関数）"""
    analyzer = WeekdayRoleNeedAnalyzer()
    return analyzer.analyze_weekday_role_needs(need_df, schedule_df)


def create_weekday_role_visualizations(analysis_result: Dict[str, Any]) -> Dict[str, go.Figure]:
    """曜日×職種別可視化作成（便利関数）"""
    visualizer = WeekdayRoleNeedVisualizer()
    return visualizer.create_weekday_role_dashboard(analysis_result)


def generate_llm_readable_report(analysis_result: Dict[str, Any], output_path: Path) -> Path:
    """LLM用レポート生成（便利関数）"""
    generator = LLMReadableReportGenerator()
    return generator.generate_comprehensive_report(analysis_result, output_path)


# Export
__all__ = [
    'WeekdayRoleNeedAnalyzer',
    'WeekdayRoleNeedVisualizer',
    'LLMReadableReportGenerator',
    'analyze_weekday_role_needs',
    'create_weekday_role_visualizations',
    'generate_llm_readable_report'
]