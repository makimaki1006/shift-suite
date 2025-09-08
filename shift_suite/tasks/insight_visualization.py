"""
洞察結果の可視化モジュール
分析で検出された洞察をStreamlit/Dashで表示
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path
import json
from typing import Dict, List, Optional
from datetime import datetime


class InsightVisualizer:
    """洞察結果を可視化するクラス"""
    
    def __init__(self, insight_report_path: Optional[Path] = None):
        """
        Args:
            insight_report_path: 洞察レポートのJSONファイルパス
        """
        self.report = None
        self.insights = []
        
        if insight_report_path and insight_report_path.exists():
            self.load_report(insight_report_path)
    
    def load_report(self, report_path: Path):
        """洞察レポートを読み込み"""
        with open(report_path, 'r', encoding='utf-8') as f:
            self.report = json.load(f)
            self.insights = self.report.get('insights', [])
    
    def create_severity_gauge(self) -> go.Figure:
        """重要度ゲージチャート"""
        if not self.report:
            return go.Figure()
        
        critical = self.report['by_severity'].get('critical', 0)
        high = self.report['by_severity'].get('high', 0)
        medium = self.report['by_severity'].get('medium', 0)
        
        # 重要度スコア（重み付け）
        severity_score = (critical * 3 + high * 2 + medium * 1) / max((critical + high + medium), 1) * 33.33
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=severity_score,
            title={'text': "問題の深刻度"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkred" if severity_score > 66 else "orange" if severity_score > 33 else "green"},
                'steps': [
                    {'range': [0, 33], 'color': "lightgreen"},
                    {'range': [33, 66], 'color': "lightyellow"},
                    {'range': [66, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300)
        return fig
    
    def create_financial_impact_waterfall(self) -> go.Figure:
        """財務影響のウォーターフォールチャート"""
        if not self.insights:
            return go.Figure()
        
        # 財務影響のある洞察を抽出
        financial_insights = [i for i in self.insights if i.get('financial_impact')]
        financial_insights.sort(key=lambda x: x['financial_impact'], reverse=True)
        
        # 上位10個に限定
        top_insights = financial_insights[:10]
        
        x = ['現状コスト']
        y = [0]
        measure = ['absolute']
        
        for insight in top_insights:
            title = insight['title'][:20] + '...' if len(insight['title']) > 20 else insight['title']
            x.append(title)
            y.append(-insight['financial_impact'])  # 削減なので負の値
            measure.append('relative')
        
        x.append('改善後コスト')
        y.append(None)
        measure.append('total')
        
        fig = go.Figure(go.Waterfall(
            x=x,
            y=y,
            measure=measure,
            text=[f"{abs(v):.1f}" if v else "" for v in y],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#48bb78"}},
            increasing={"marker": {"color": "#f56565"}},
            totals={"marker": {"color": "#4299e1"}}
        ))
        
        fig.update_layout(
            title="財務影響分析（万円/月）",
            showlegend=False,
            height=400
        )
        
        return fig
    
    def create_category_distribution(self) -> go.Figure:
        """カテゴリ別分布のドーナツチャート"""
        if not self.report:
            return go.Figure()
        
        categories = self.report.get('by_category', {})
        
        # カテゴリ名を日本語に変換
        category_labels = {
            'cost_waste': 'コスト無駄',
            'risk': 'リスク',
            'opportunity': '改善機会',
            'anomaly': '異常値',
            'pattern': 'パターン',
            'constraint': '制約問題',
            'fairness': '公平性',
            'efficiency': '効率性'
        }
        
        labels = [category_labels.get(k, k) for k in categories.keys()]
        values = list(categories.values())
        colors = px.colors.qualitative.Set3[:len(labels)]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=colors
        )])
        
        fig.update_layout(
            title="問題カテゴリの分布",
            height=400
        )
        
        return fig
    
    def create_insight_timeline(self) -> go.Figure:
        """洞察の優先度タイムライン"""
        if not self.insights:
            return go.Figure()
        
        # 優先度別にグループ化
        priority_groups = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for insight in self.insights:
            severity = insight.get('severity', 'low')
            if severity in priority_groups:
                priority_groups[severity].append(insight)
        
        fig = go.Figure()
        
        colors = {
            'critical': '#dc2626',
            'high': '#ea580c',
            'medium': '#ca8a04',
            'low': '#16a34a'
        }
        
        y_positions = {
            'critical': 3,
            'high': 2,
            'medium': 1,
            'low': 0
        }
        
        for severity, insights_list in priority_groups.items():
            if insights_list:
                x = list(range(len(insights_list)))
                y = [y_positions[severity]] * len(insights_list)
                text = [i['title'][:30] + '...' if len(i['title']) > 30 else i['title'] 
                       for i in insights_list]
                
                fig.add_trace(go.Scatter(
                    x=x,
                    y=y,
                    mode='markers+text',
                    name=severity.upper(),
                    text=text,
                    textposition="top center",
                    marker=dict(
                        size=15,
                        color=colors[severity],
                        symbol='diamond'
                    ),
                    hovertemplate='<b>%{text}</b><extra></extra>'
                ))
        
        fig.update_layout(
            title="優先度別アクションタイムライン",
            xaxis_title="順序",
            yaxis=dict(
                title="優先度",
                tickmode='array',
                tickvals=[0, 1, 2, 3],
                ticktext=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            ),
            height=400,
            showlegend=True
        )
        
        return fig
    
    def render_streamlit_dashboard(self):
        """Streamlitダッシュボードをレンダリング"""
        
        st.title("🔍 リアルタイム洞察ダッシュボード")
        
        if not self.report:
            st.warning("洞察レポートが読み込まれていません")
            return
        
        # サマリー情報
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "検出された洞察",
                self.report['total_insights'],
                delta=None
            )
        
        with col2:
            critical = self.report['by_severity'].get('critical', 0)
            st.metric(
                "緊急対応必要",
                critical,
                delta="要注意" if critical > 0 else None,
                delta_color="inverse"
            )
        
        with col3:
            high = self.report['by_severity'].get('high', 0)
            st.metric(
                "高優先度",
                high,
                delta=None
            )
        
        with col4:
            impact = self.report.get('total_financial_impact', 0)
            st.metric(
                "財務影響",
                f"{impact:.1f}万円/月",
                delta="削減可能" if impact > 0 else None
            )
        
        st.divider()
        
        # グラフセクション
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(self.create_severity_gauge(), use_container_width=True)
            st.plotly_chart(self.create_category_distribution(), use_container_width=True)
        
        with col2:
            st.plotly_chart(self.create_financial_impact_waterfall(), use_container_width=True)
            st.plotly_chart(self.create_insight_timeline(), use_container_width=True)
        
        st.divider()
        
        # 重要な洞察の詳細
        st.subheader("🚨 重要な洞察 TOP 5")
        
        critical_insights = [i for i in self.insights 
                           if i.get('severity') in ['critical', 'high']][:5]
        
        for i, insight in enumerate(critical_insights, 1):
            with st.expander(f"{i}. {insight['title']}", expanded=(i <= 2)):
                st.write(f"**説明:** {insight['description']}")
                
                if insight.get('financial_impact'):
                    st.write(f"**財務影響:** {insight['financial_impact']:.1f}万円/月")
                
                if insight.get('affected_staff'):
                    st.write(f"**影響を受けるスタッフ:** {', '.join(insight['affected_staff'])}")
                
                if insight.get('recommended_action'):
                    st.info(f"💡 **推奨アクション:** {insight['recommended_action']}")
                
                # データエビデンス
                if insight.get('data_evidence'):
                    st.write("**データエビデンス:**")
                    evidence_df = pd.DataFrame([insight['data_evidence']])
                    st.dataframe(evidence_df)
        
        st.divider()
        
        # アクションプラン
        st.subheader("📋 推奨アクションプラン")
        
        critical_actions = self.report.get('critical_actions', [])
        
        if critical_actions:
            action_df = pd.DataFrame(critical_actions)
            
            # 優先度を追加
            action_df['優先度'] = ['🔴 緊急', '🟠 高', '🟡 中', '🟢 低', '⚪ 情報'][:len(action_df)]
            
            # 列の順序を調整
            columns_order = ['優先度', 'title', 'action', 'impact']
            action_df = action_df[columns_order]
            
            # 列名を日本語に
            action_df.columns = ['優先度', '課題', 'アクション', '影響(万円/月)']
            
            st.dataframe(
                action_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    '影響(万円/月)': st.column_config.NumberColumn(
                        format="%.1f"
                    )
                }
            )
        
        # 生データのダウンロード
        st.divider()
        st.subheader("📥 データエクスポート")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSONレポートのダウンロード
            json_str = json.dumps(self.report, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 洞察レポート (JSON)",
                data=json_str,
                file_name=f"insight_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # CSVエクスポート
            if self.insights:
                insights_df = pd.DataFrame(self.insights)
                csv = insights_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📊 洞察一覧 (CSV)",
                    data=csv,
                    file_name=f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )


def add_insight_tab_to_streamlit(app_instance):
    """
    既存のStreamlitアプリに洞察タブを追加
    
    使用例:
        import streamlit as st
        from insight_visualization import add_insight_tab_to_streamlit
        
        tabs = st.tabs(["分析", "可視化", "洞察"])
        
        with tabs[2]:
            add_insight_tab_to_streamlit(app)
    """
    
    # 分析結果ディレクトリを取得
    if 'analysis_dir' in st.session_state:
        analysis_dir = Path(st.session_state['analysis_dir'])
        insight_report_path = analysis_dir / 'real_time_insights.json'
        
        if insight_report_path.exists():
            visualizer = InsightVisualizer(insight_report_path)
            visualizer.render_streamlit_dashboard()
        else:
            st.info("洞察レポートがまだ生成されていません。分析を実行してください。")
    else:
        st.warning("分析ディレクトリが設定されていません。")


def create_insight_summary_card(insight_report_path: Path) -> str:
    """
    洞察サマリーカードのHTMLを生成（既存UIへの埋め込み用）
    
    Returns:
        HTML文字列
    """
    
    if not insight_report_path.exists():
        return "<p>洞察レポートが見つかりません</p>"
    
    with open(insight_report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    total = report.get('total_insights', 0)
    critical = report.get('by_severity', {}).get('critical', 0)
    high = report.get('by_severity', {}).get('high', 0)
    impact = report.get('total_financial_impact', 0)
    
    # 最重要の洞察を1つ取得
    top_insight = None
    insights = report.get('insights', [])
    for insight in insights:
        if insight.get('severity') == 'critical':
            top_insight = insight
            break
    
    html = f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h3 style="margin: 0 0 15px 0;">🔍 リアルタイム洞察検出結果</h3>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">
            <div style="text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{total}</div>
                <div style="opacity: 0.9; font-size: 0.9em;">検出された洞察</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2em; font-weight: bold; color: #ff6b6b;">{critical}</div>
                <div style="opacity: 0.9; font-size: 0.9em;">緊急対応</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2em; font-weight: bold; color: #ffa500;">{high}</div>
                <div style="opacity: 0.9; font-size: 0.9em;">高優先度</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{impact:.0f}万円</div>
                <div style="opacity: 0.9; font-size: 0.9em;">月間削減可能額</div>
            </div>
        </div>
    """
    
    if top_insight:
        html += f"""
        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
            <h4 style="margin: 0 0 10px 0;">⚠️ 最重要課題</h4>
            <p style="margin: 5px 0;"><strong>{top_insight['title']}</strong></p>
            <p style="margin: 5px 0; opacity: 0.9; font-size: 0.9em;">{top_insight['description']}</p>
            {f"<p style='margin: 5px 0;'>💡 {top_insight['recommended_action']}</p>" 
             if top_insight.get('recommended_action') else ""}
        </div>
        """
    
    html += "</div>"
    
    return html