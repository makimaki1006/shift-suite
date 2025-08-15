#!/usr/bin/env python3
"""
営業資料用のデモ画面イメージ生成スクリプト
各分析機能の見本画面を生成
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta

# カラーパレット定義
COLORS = {
    'primary': '#0d47a1',
    'secondary': '#2196f3',
    'accent': '#64b5f6',
    'danger': '#f44336',
    'warning': '#ff9800',
    'success': '#4caf50',
    'light': '#f5f5f5',
    'dark': '#333333'
}

def create_shortage_heatmap():
    """
    人員不足分析のヒートマップを生成
    """
    # 時間帯ラベル（30分刻み）
    time_labels = []
    for hour in range(24):
        for minute in ['00', '30']:
            time_labels.append(f"{hour:02d}:{minute}")
    
    # 日付ラベル（6月の30日間）
    dates = pd.date_range('2024-06-01', '2024-06-30')
    date_labels = [d.strftime('%m/%d') for d in dates]
    
    # 不足データの生成（リアルな問題パターン）
    shortage_data = np.zeros((len(time_labels), len(dates)))
    
    # 朝食後の人員不足（10:00-11:00）
    for i, time in enumerate(time_labels):
        if time in ['10:00', '10:30']:
            shortage_data[i, :] = np.random.uniform(-2.5, -1.5, len(dates))
    
    # 夕食時の人員不足（18:00-19:00）
    for i, time in enumerate(time_labels):
        if time in ['18:00', '18:30']:
            shortage_data[i, :] = np.random.uniform(-1.5, -0.5, len(dates))
    
    # 土日の早番不足
    for i, date in enumerate(dates):
        if date.weekday() in [5, 6]:  # 土日
            for j, time in enumerate(time_labels):
                if time in ['07:00', '07:30', '08:00']:
                    shortage_data[j, i] -= 1
    
    # 午後の過剰配置（14:00-15:00）
    for i, time in enumerate(time_labels):
        if time in ['14:00', '14:30']:
            shortage_data[i, :] = np.random.uniform(1, 2, len(dates))
    
    # ヒートマップ作成
    fig = go.Figure(data=go.Heatmap(
        z=shortage_data,
        x=date_labels,
        y=time_labels,
        colorscale=[
            [0, COLORS['danger']],     # 不足（赤）
            [0.5, 'white'],            # 適正（白）
            [1, COLORS['secondary']]   # 過剰（青）
        ],
        zmid=0,
        colorbar=dict(
            title="過不足人数",
            titleside="right",
            tickmode="array",
            tickvals=[-2, -1, 0, 1, 2],
            ticktext=["-2名", "-1名", "適正", "+1名", "+2名"]
        ),
        hovertemplate='%{y}<br>%{x}: %{z:.1f}名<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': '人員配置 過不足分析（2024年6月）',
            'font': {'size': 24, 'color': COLORS['primary']}
        },
        xaxis_title="日付",
        yaxis_title="時間帯",
        height=800,
        width=1200,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    # 問題箇所にアノテーション追加
    fig.add_annotation(
        x='06/15', y='10:30',
        text="朝食後の人手不足<br>-2名",
        showarrow=True,
        arrowhead=2,
        arrowcolor=COLORS['danger'],
        ax=-50, ay=-50,
        bgcolor=COLORS['danger'],
        font=dict(color='white'),
        borderpad=4
    )
    
    fig.add_annotation(
        x='06/22', y='18:30',
        text="夕食時の人手不足<br>-1名",
        showarrow=True,
        arrowhead=2,
        arrowcolor=COLORS['danger'],
        ax=50, ay=-50,
        bgcolor=COLORS['danger'],
        font=dict(color='white'),
        borderpad=4
    )
    
    return fig

def create_fatigue_analysis():
    """
    疲労度分析のダッシュボードを生成
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '職員別疲労度スコア',
            '連続勤務日数分布',
            '月間夜勤回数',
            '疲労度推移（高リスク職員）'
        ),
        specs=[
            [{'type': 'bar'}, {'type': 'histogram'}],
            [{'type': 'bar'}, {'type': 'scatter'}]
        ]
    )
    
    # 職員名（問題のある職員を上位に）
    staff_names = [
        '佐藤太郎', '山田美咲', '小林愛', '松本和也',
        '中村大輔', '加藤翔', '田中花子', '高橋美咲',
        '渡辺健', '伊藤直子', '吉田恵', '鈴木一郎'
    ]
    
    # 疲労度スコア（高い順）
    fatigue_scores = [85, 78, 72, 70, 65, 62, 58, 55, 52, 50, 48, 45]
    colors = [COLORS['danger'] if score > 70 else COLORS['warning'] if score > 60 else COLORS['success'] 
              for score in fatigue_scores]
    
    # 1. 職員別疲労度スコア
    fig.add_trace(
        go.Bar(
            x=staff_names,
            y=fatigue_scores,
            marker_color=colors,
            text=fatigue_scores,
            textposition='outside',
            name='疲労度スコア'
        ),
        row=1, col=1
    )
    
    # 危険ラインを追加
    fig.add_hline(
        y=70, line_dash="dash", line_color=COLORS['danger'],
        annotation_text="危険レベル", row=1, col=1
    )
    
    # 2. 連続勤務日数分布
    continuous_days = np.concatenate([
        np.random.normal(3, 1, 15),  # 通常
        [6, 6, 5, 5, 4]  # 問題ケース
    ])
    fig.add_trace(
        go.Histogram(
            x=continuous_days,
            nbinsx=7,
            marker_color=COLORS['secondary'],
            name='連続勤務日数'
        ),
        row=1, col=2
    )
    
    # 3. 月間夜勤回数
    night_shifts = [10, 8, 8, 7, 6, 6, 5, 4, 4, 3, 2, 2]
    fig.add_trace(
        go.Bar(
            x=staff_names,
            y=night_shifts,
            marker_color=COLORS['primary'],
            text=night_shifts,
            textposition='outside',
            name='夜勤回数'
        ),
        row=2, col=1
    )
    
    # 4. 疲労度推移（高リスク職員）
    days = list(range(1, 31))
    sato_fatigue = [50 + i*0.5 + np.random.normal(0, 3) for i in range(30)]
    sato_fatigue[9:16] = [70 + i*2 for i in range(7)]  # 連続勤務期間
    
    yamada_fatigue = [45 + i*0.3 + np.random.normal(0, 2) for i in range(30)]
    yamada_fatigue[4] = 75  # 夜勤明け早番
    yamada_fatigue[11] = 78
    yamada_fatigue[19] = 73
    
    fig.add_trace(
        go.Scatter(
            x=days, y=sato_fatigue,
            mode='lines+markers',
            name='佐藤太郎',
            line=dict(color=COLORS['danger'], width=3)
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=days, y=yamada_fatigue,
            mode='lines+markers',
            name='山田美咲',
            line=dict(color=COLORS['warning'], width=3)
        ),
        row=2, col=2
    )
    
    # 危険ラインを追加
    fig.add_hline(
        y=70, line_dash="dash", line_color=COLORS['danger'],
        annotation_text="危険", row=2, col=2
    )
    
    # レイアウト設定
    fig.update_layout(
        title={
            'text': '職員疲労度分析ダッシュボード',
            'font': {'size': 24, 'color': COLORS['primary']}
        },
        showlegend=False,
        height=800,
        width=1200,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    fig.update_xaxes(title_text="職員名", row=1, col=1)
    fig.update_yaxes(title_text="疲労度スコア", row=1, col=1)
    fig.update_xaxes(title_text="連続勤務日数", row=1, col=2)
    fig.update_yaxes(title_text="人数", row=1, col=2)
    fig.update_xaxes(title_text="職員名", row=2, col=1)
    fig.update_yaxes(title_text="夜勤回数", row=2, col=1)
    fig.update_xaxes(title_text="日付", row=2, col=2)
    fig.update_yaxes(title_text="疲労度スコア", row=2, col=2)
    
    return fig

def create_fairness_analysis():
    """
    公平性分析のダッシュボードを生成
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '月間勤務時間の分布',
            '夜勤回数の公平性',
            '休日勤務の偏り',
            '公平性スコアマトリックス'
        ),
        specs=[
            [{'type': 'box'}, {'type': 'bar'}],
            [{'type': 'bar'}, {'type': 'heatmap'}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # 職員リスト
    staff_names = ['佐藤太郎', '山田美咲', '田中花子', '中村大輔', 
                   '小林愛', '加藤翔', '高橋美咲', '渡辺健',
                   '伊藤直子', '松本和也', '吉田恵', '鈴木一郎']
    
    # 1. 月間勤務時間の分布（不公平を表現）
    work_hours = {
        '正規職員': np.concatenate([
            np.random.normal(160, 5, 8),  # 通常
            [185, 190, 195, 140]  # 偏り
        ]),
        'パート': np.random.normal(80, 10, 8)
    }
    
    for emp_type, hours in work_hours.items():
        fig.add_trace(
            go.Box(
                y=hours,
                name=emp_type,
                boxpoints='all',
                jitter=0.3,
                pointpos=-1.8
            ),
            row=1, col=1
        )
    
    # 2. 夜勤回数の公平性
    night_counts = [10, 8, 8, 7, 6, 6, 5, 4, 4, 4, 3, 2]
    colors = [COLORS['danger'] if n >= 8 else COLORS['warning'] if n >= 6 else COLORS['success'] 
              for n in night_counts]
    
    fig.add_trace(
        go.Bar(
            x=staff_names,
            y=night_counts,
            marker_color=colors,
            text=night_counts,
            textposition='outside'
        ),
        row=1, col=2
    )
    
    # 平均ラインを追加
    avg_nights = np.mean(night_counts)
    fig.add_hline(
        y=avg_nights, line_dash="dash", line_color='black',
        annotation_text=f"平均: {avg_nights:.1f}回", row=1, col=2
    )
    
    # 3. 休日勤務の偏り
    weekend_counts = [8, 7, 6, 6, 5, 4, 4, 3, 3, 2, 2, 1]
    
    fig.add_trace(
        go.Bar(
            x=staff_names,
            y=weekend_counts,
            marker_color=COLORS['warning'],
            text=weekend_counts,
            textposition='outside'
        ),
        row=2, col=1
    )
    
    # 4. 公平性スコアマトリックス
    metrics = ['勤務時間', '夜勤回数', '休日勤務', '残業時間']
    fairness_matrix = np.array([
        [50, 30, 40, 45],  # 佐藤
        [60, 50, 50, 55],  # 山田
        [80, 70, 75, 80],  # 田中
        [75, 65, 70, 75],  # 中村
        [70, 40, 60, 70],  # 小林
        [85, 75, 80, 85],  # 加藤
        [90, 85, 85, 90],  # 高橋
        [85, 90, 90, 85],  # 渡辺
    ])
    
    fig.add_trace(
        go.Heatmap(
            z=fairness_matrix,
            x=metrics,
            y=staff_names[:8],
            colorscale=[
                [0, COLORS['danger']],
                [0.5, COLORS['warning']],
                [1, COLORS['success']]
            ],
            text=fairness_matrix,
            texttemplate='%{text}',
            textfont={"size": 12},
            colorbar=dict(title="公平性スコア")
        ),
        row=2, col=2
    )
    
    # レイアウト設定
    fig.update_layout(
        title={
            'text': '勤務公平性分析ダッシュボード',
            'font': {'size': 24, 'color': COLORS['primary']}
        },
        showlegend=True,
        height=800,
        width=1200,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # 軸ラベル設定
    fig.update_yaxes(title_text="勤務時間", row=1, col=1)
    fig.update_xaxes(title_text="職員名", tickangle=-45, row=1, col=2)
    fig.update_yaxes(title_text="夜勤回数", row=1, col=2)
    fig.update_xaxes(title_text="職員名", tickangle=-45, row=2, col=1)
    fig.update_yaxes(title_text="休日勤務日数", row=2, col=1)
    
    return fig

def create_integrated_dashboard():
    """
    統合ダッシュボードを生成
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '疲労度 vs パフォーマンス',
            '公平性レーダーチャート',
            '勤務区分対応能力',
            '総合評価スコア'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'polar'}],
            [{'type': 'bar'}, {'type': 'indicator'}]
        ],
        vertical_spacing=0.15
    )
    
    # 職員データ
    staff_names = ['佐藤太郎', '山田美咲', '田中花子', '中村大輔', 
                   '小林愛', '加藤翔', '高橋美咲', '渡辺健',
                   '伊藤直子', '松本和也', '吉田恵', '鈴木一郎']
    
    # 1. 疲労度 vs パフォーマンス
    fatigue = [85, 78, 55, 65, 72, 62, 52, 50, 48, 70, 58, 45]
    performance = [60, 65, 90, 80, 70, 85, 92, 88, 90, 75, 85, 95]
    
    fig.add_trace(
        go.Scatter(
            x=fatigue,
            y=performance,
            mode='markers+text',
            text=staff_names,
            textposition="top center",
            marker=dict(
                size=15,
                color=fatigue,
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title="疲労度", x=0.45)
            )
        ),
        row=1, col=1
    )
    
    # 危険ゾーンを追加
    fig.add_vrect(
        x0=70, x1=100,
        fillcolor=COLORS['danger'], opacity=0.1,
        layer="below", line_width=0,
        row=1, col=1
    )
    
    # 2. 公平性レーダーチャート（代表3名）
    categories = ['勤務時間', '夜勤配分', '休日勤務', '残業時間', '希望休']
    
    fig.add_trace(
        go.Scatterpolar(
            r=[50, 30, 40, 45, 60],
            theta=categories,
            fill='toself',
            name='佐藤太郎',
            line_color=COLORS['danger']
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatterpolar(
            r=[80, 85, 85, 90, 85],
            theta=categories,
            fill='toself',
            name='高橋美咲',
            line_color=COLORS['success']
        ),
        row=1, col=2
    )
    
    # 3. 勤務区分対応能力
    shift_types = ['早番', 'リーダー', '遅番', '夜勤']
    capable_counts = [18, 8, 18, 12]
    total_staff = 22
    
    fig.add_trace(
        go.Bar(
            x=shift_types,
            y=capable_counts,
            text=[f'{c}/{total_staff}名<br>({c/total_staff*100:.0f}%)' for c in capable_counts],
            textposition='outside',
            marker_color=[COLORS['success'], COLORS['warning'], COLORS['success'], COLORS['secondary']]
        ),
        row=2, col=1
    )
    
    # 4. 総合評価スコア
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=73,
            delta={'reference': 60, 'increasing': {'color': COLORS['success']}},
            title={'text': "施設総合スコア"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': COLORS['primary']},
                'steps': [
                    {'range': [0, 50], 'color': COLORS['light']},
                    {'range': [50, 70], 'color': '#ffe0b2'},
                    {'range': [70, 90], 'color': '#c8e6c9'},
                    {'range': [90, 100], 'color': '#81c784'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=2, col=2
    )
    
    # レイアウト設定
    fig.update_layout(
        title={
            'text': '統合分析ダッシュボード - 全体俯瞰',
            'font': {'size': 24, 'color': COLORS['primary']}
        },
        showlegend=True,
        height=800,
        width=1200,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # 軸設定
    fig.update_xaxes(title_text="疲労度スコア", row=1, col=1)
    fig.update_yaxes(title_text="パフォーマンススコア", row=1, col=1)
    fig.update_xaxes(title_text="勤務区分", row=2, col=1)
    fig.update_yaxes(title_text="対応可能人数", row=2, col=1)
    
    # レーダーチャートの設定
    fig.update_polars(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        ),
        row=1, col=2
    )
    
    return fig

def create_blueprint_analysis():
    """
    ブループリント分析の可視化
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'ペアリング相性マトリックス',
            '個人別制約条件',
            'スキルレベル分布',
            'シフトパターン頻度'
        ),
        specs=[
            [{'type': 'heatmap'}, {'type': 'table'}],
            [{'type': 'sunburst'}, {'type': 'bar'}]
        ]
    )
    
    # 1. ペアリング相性マトリックス
    staff_subset = ['田中', '佐藤', '山田', '中村', '小林', '加藤', '高橋', '渡辺']
    compatibility = np.array([
        [10, 8, 9, 7, 6, 8, 9, 8],
        [8, 10, 5, 8, 7, 9, 7, 8],
        [9, 5, 10, 8, 8, 7, 9, 7],
        [7, 8, 8, 10, 9, 8, 7, 8],
        [6, 7, 8, 9, 10, 7, 8, 9],
        [8, 9, 7, 8, 7, 10, 8, 7],
        [9, 7, 9, 7, 8, 8, 10, 9],
        [8, 8, 7, 8, 9, 7, 9, 10]
    ])
    
    fig.add_trace(
        go.Heatmap(
            z=compatibility,
            x=staff_subset,
            y=staff_subset,
            colorscale='RdYlGn',
            text=compatibility,
            texttemplate='%{text}',
            textfont={"size": 12},
            colorbar=dict(title="相性スコア")
        ),
        row=1, col=1
    )
    
    # 2. 個人別制約条件
    constraints_data = [
        ['田中花子', '水曜早番NG', '子供の送迎'],
        ['佐藤太郎', '連続夜勤NG', '体調配慮'],
        ['山田美咲', '土日連続NG', '家族の介護'],
        ['中村大輔', '月10日夜勤まで', '年齢配慮'],
        ['小林愛', '早番優先', '通勤事情']
    ]
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=['職員名', '制約条件', '理由'],
                fill_color=COLORS['primary'],
                font=dict(color='white', size=14),
                align='left'
            ),
            cells=dict(
                values=list(zip(*constraints_data)),
                fill_color=['lightgray', 'white', 'white'],
                align='left',
                font_size=12
            )
        ),
        row=1, col=2
    )
    
    # 3. スキルレベル分布
    skill_data = dict(
        labels=['介護士', 'ベテラン', '中堅', '若手', 'リーダー候補', '新人'],
        parents=['', '介護士', '介護士', '介護士', 'ベテラン', '若手'],
        values=[22, 6, 8, 5, 2, 1]
    )
    
    fig.add_trace(
        go.Sunburst(
            labels=skill_data['labels'],
            parents=skill_data['parents'],
            values=skill_data['values'],
            branchvalues='total',
            marker=dict(
                colors=[COLORS['primary'], COLORS['success'], 
                       COLORS['secondary'], COLORS['warning'],
                       COLORS['accent'], COLORS['danger']]
            )
        ),
        row=2, col=1
    )
    
    # 4. シフトパターン頻度
    patterns = ['早番→日勤', '日勤→遅番', '遅番→休み', '夜勤→明け', 
                '休み→早番', '連続夜勤', '夜勤→早番']
    frequencies = [45, 38, 42, 30, 35, 8, 3]
    colors = [COLORS['success'] if f < 10 else COLORS['warning'] if f < 40 else COLORS['primary'] 
              for f in frequencies]
    
    fig.add_trace(
        go.Bar(
            x=patterns,
            y=frequencies,
            marker_color=colors,
            text=frequencies,
            textposition='outside'
        ),
        row=2, col=2
    )
    
    # レイアウト設定
    fig.update_layout(
        title={
            'text': 'シフト作成ブループリント分析',
            'font': {'size': 24, 'color': COLORS['primary']}
        },
        showlegend=False,
        height=800,
        width=1200,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    fig.update_xaxes(title_text="シフトパターン", tickangle=-45, row=2, col=2)
    fig.update_yaxes(title_text="発生回数", row=2, col=2)
    
    return fig

def create_cost_analysis():
    """
    コスト分析ダッシュボードを生成
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '月別人件費推移と予測',
            'コスト構成要素',
            '時間帯別コスト効率',
            'ROI予測シミュレーション'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'pie'}],
            [{'type': 'heatmap'}, {'type': 'waterfall'}]
        ]
    )
    
    # 1. 月別人件費推移と予測
    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月予測', '8月予測', '9月予測']
    actual_cost = [620, 615, 625, 618, 622, 630, None, None, None]
    predicted_cost = [None, None, None, None, None, 630, 595, 590, 585]
    
    fig.add_trace(
        go.Scatter(
            x=months[:6],
            y=actual_cost[:6],
            mode='lines+markers',
            name='実績',
            line=dict(color=COLORS['primary'], width=3)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=months[5:],
            y=predicted_cost[5:],
            mode='lines+markers',
            name='AI予測（最適化後）',
            line=dict(color=COLORS['success'], width=3, dash='dot')
        ),
        row=1, col=1
    )
    
    # 2. コスト構成要素
    fig.add_trace(
        go.Pie(
            labels=['基本給', '残業代', '夜勤手当', 'スポット費用', 'その他手当'],
            values=[450, 80, 50, 30, 20],
            marker_colors=[COLORS['primary'], COLORS['danger'], 
                          COLORS['secondary'], COLORS['warning'], COLORS['accent']],
            textinfo='label+percent+value',
            texttemplate='%{label}<br>%{value}万円<br>(%{percent})',
            hole=0.3
        ),
        row=1, col=2
    )
    
    # 3. 時間帯別コスト効率
    time_slots = [f'{h:02d}:00' for h in range(0, 24, 3)]
    days = ['月', '火', '水', '木', '金', '土', '日']
    
    # コスト効率データ（高いほど非効率）
    cost_efficiency = np.array([
        [0.8, 0.8, 0.8, 0.8, 0.8, 1.2, 1.2],  # 0-3時
        [0.7, 0.7, 0.7, 0.7, 0.7, 1.1, 1.1],  # 3-6時
        [1.1, 1.1, 1.1, 1.1, 1.1, 1.3, 1.3],  # 6-9時
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.2],  # 9-12時
        [0.9, 0.9, 0.9, 0.9, 0.9, 1.0, 1.0],  # 12-15時
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.2],  # 15-18時
        [1.2, 1.2, 1.2, 1.2, 1.2, 1.3, 1.3],  # 18-21時
        [0.9, 0.9, 0.9, 0.9, 0.9, 1.1, 1.1]   # 21-24時
    ])
    
    fig.add_trace(
        go.Heatmap(
            z=cost_efficiency,
            x=days,
            y=time_slots,
            colorscale='RdYlGn_r',
            text=cost_efficiency,
            texttemplate='%{text:.1f}',
            colorbar=dict(title="コスト指数")
        ),
        row=2, col=1
    )
    
    # 4. ROI予測シミュレーション
    fig.add_trace(
        go.Waterfall(
            name="ROI",
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["現状コスト", "残業削減", "スポット削減", "離職コスト削減", "生産性向上", "最適化後"],
            y=[710, -30, -10, -37.5, -42.5, 590],
            text=["+710", "-30", "-10", "-37.5", "-42.5", "590"],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ),
        row=2, col=2
    )
    
    # レイアウト設定
    fig.update_layout(
        title={
            'text': 'コスト分析・予測ダッシュボード',
            'font': {'size': 24, 'color': COLORS['primary']}
        },
        showlegend=True,
        height=800,
        width=1200,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # 軸設定
    fig.update_xaxes(title_text="月", row=1, col=1)
    fig.update_yaxes(title_text="人件費（万円）", row=1, col=1)
    fig.update_xaxes(title_text="曜日", row=2, col=1)
    fig.update_yaxes(title_text="時間帯", row=2, col=1)
    fig.update_yaxes(title_text="コスト（万円/月）", row=2, col=2)
    
    return fig

def save_all_demo_images():
    """
    全てのデモ画像を生成・保存
    """
    output_dir = "demo_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # 各分析画面を生成
    demos = {
        'heatmap_shortage_demo.html': create_shortage_heatmap(),
        'fatigue_analysis_demo.html': create_fatigue_analysis(),
        'fairness_analysis_demo.html': create_fairness_analysis(),
        'integrated_dashboard_demo.html': create_integrated_dashboard(),
        'blueprint_analysis_demo.html': create_blueprint_analysis(),
        'cost_analysis_demo.html': create_cost_analysis()
    }
    
    # HTMLファイルとして保存
    for filename, fig in demos.items():
        filepath = os.path.join(output_dir, filename)
        fig.write_html(filepath)
        print(f"✅ {filename} を生成しました")
    
    # 静的画像も生成（kaleido必要）
    try:
        for filename, fig in demos.items():
            img_filename = filename.replace('.html', '.png')
            img_filepath = os.path.join(output_dir, img_filename)
            fig.write_image(img_filepath, width=1200, height=800, scale=2)
            print(f"📸 {img_filename} を生成しました")
    except Exception as e:
        print(f"⚠️ 画像生成にはkaleidoのインストールが必要です: pip install kaleido")
        print(f"エラー: {e}")
    
    print(f"\n✨ 全てのデモ画像を {output_dir} フォルダに生成しました")
    print("営業資料のHTMLファイル内の画像パスを適切に更新してください")

if __name__ == "__main__":
    save_all_demo_images()