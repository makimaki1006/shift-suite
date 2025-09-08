"""
高度不足分析システムの統合モジュール
app.pyおよびdash_app.pyから呼び出すためのインターフェース
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# 高度分析モジュールのインポート
from comprehensive_enhanced_shortage_analysis_fixed import (
    ComprehensiveShortageAnalyzer,
    cache_manager
)

logger = logging.getLogger(__name__)


def display_advanced_shortage_tab(tab_container, data_dir: Path):
    """
    Streamlit用の高度不足分析タブを表示
    
    Args:
        tab_container: Streamlitのタブコンテナ
        data_dir: データディレクトリのパス
    """
    with tab_container:
        st.header("🔬 高度不足分析")
        
        # キャッシュクリアボタン
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 キャッシュクリア", help="分析結果のキャッシュをクリアして最新データで再計算"):
                cache_manager.clear()
                st.success("キャッシュをクリアしました")
        
        # アナライザー初期化
        try:
            analyzer = ComprehensiveShortageAnalyzer(data_dir)
            
            # データ読み込み
            with st.spinner("データ読み込み中..."):
                if not analyzer.load_all_data():
                    st.error("データの読み込みに失敗しました。データファイルを確認してください。")
                    return
            
            # 分析モード選択
            analysis_mode = st.selectbox(
                "分析モード選択",
                ["包括的レポート", "根本原因分析", "コスト影響分析", 
                 "将来予測", "最適配置シミュレーション", "個人負荷分析", "統計分析"]
            )
            
            # 分析実行
            if st.button("🚀 分析実行", type="primary"):
                with st.spinner(f"{analysis_mode}を実行中..."):
                    display_analysis_results(analyzer, analysis_mode)
                    
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            logger.error(f"Advanced shortage analysis error: {e}", exc_info=True)


def display_analysis_results(analyzer: ComprehensiveShortageAnalyzer, mode: str):
    """分析結果を表示"""
    
    try:
        if mode == "包括的レポート":
            report = analyzer.generate_comprehensive_report()
            display_comprehensive_report(report)
            
        elif mode == "根本原因分析":
            results = analyzer.analyze_root_causes()
            display_root_cause_analysis(results)
            
        elif mode == "コスト影響分析":
            impact = analyzer.analyze_cost_impact()
            display_cost_impact(impact)
            
        elif mode == "将来予測":
            col1, col2 = st.columns([3, 1])
            with col2:
                use_ml = st.checkbox("機械学習使用", value=True)
            prediction = analyzer.predict_future_shortage(use_ml=use_ml)
            display_future_prediction(prediction)
            
        elif mode == "最適配置シミュレーション":
            simulation = analyzer.simulate_optimal_allocation()
            display_optimal_allocation(simulation)
            
        elif mode == "個人負荷分析":
            workload = analyzer.analyze_individual_workload()
            display_workload_analysis(workload)
            
        elif mode == "統計分析":
            insights = analyzer.perform_advanced_statistical_analysis()
            display_statistical_insights(insights)
            
    except Exception as e:
        st.error(f"分析中にエラーが発生しました: {str(e)}")
        logger.error(f"Analysis execution error: {e}", exc_info=True)


def display_comprehensive_report(report: Dict):
    """包括的レポートの表示"""
    st.subheader("📊 包括的分析レポート")
    
    # エグゼクティブサマリー
    if "executive_summary" in report:
        with st.expander("📋 エグゼクティブサマリー", expanded=True):
            summary = report["executive_summary"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総不足時間", f"{summary.get('total_shortage_hours', 0):.1f}h")
            with col2:
                st.metric("影響コスト", f"¥{summary.get('total_cost_impact', 0):,.0f}")
            with col3:
                st.metric("リスクレベル", summary.get('overall_risk_level', 'N/A'))
    
    # データ品質
    if "data_quality" in report:
        with st.expander("✅ データ品質評価"):
            quality = report["data_quality"]
            st.write(f"完全性: {quality.get('completeness', 0):.1%}")
            st.write(f"一貫性: {quality.get('consistency', 0):.1%}")
            if quality.get('outliers_detected'):
                st.warning(f"外れ値検出: {quality['outliers_detected']}件")
    
    # その他のセクション
    for section in ["root_causes", "cost_impact", "future_prediction", 
                   "optimal_allocation", "workload_analysis", "statistical_insights"]:
        if section in report:
            display_section_details(section, report[section])


def display_root_cause_analysis(results: Dict):
    """根本原因分析の表示"""
    st.subheader("🔍 根本原因分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("総不足時間", f"{results.get('total_shortage_hours', 0):.1f}h")
        
        # 統計的要因分解
        if "statistical_breakdown" in results:
            breakdown = results["statistical_breakdown"]
            st.write("**主要因:**")
            for role, hours in breakdown.get("top_contributing_roles", {}).items():
                st.write(f"- {role}: {hours:.1f}h")
    
    with col2:
        # 時間パターン
        if "time_patterns" in results:
            patterns = results["time_patterns"]
            st.write("**時間パターン:**")
            st.write(f"ピーク時間: {', '.join(patterns.get('peak_hours', []))}")
            st.write(f"ピーク曜日: {', '.join(patterns.get('peak_days', []))}")
    
    # 推奨事項
    if "recommendations" in results:
        st.write("**推奨事項:**")
        for rec in results["recommendations"]:
            st.write(f"• {rec}")


def display_cost_impact(impact):
    """コスト影響分析の表示"""
    st.subheader("💰 コスト影響分析")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("残業コスト", f"¥{impact.overtime_cost:,.0f}")
    with col2:
        st.metric("派遣コスト", f"¥{impact.dispatch_cost:,.0f}")
    with col3:
        st.metric("機会損失", f"¥{impact.opportunity_loss:,.0f}")
    with col4:
        st.metric("総影響額", f"¥{impact.total_impact:,.0f}")
    
    # リスクレベル
    st.write(f"**離職リスク:** {impact.turnover_risk}")
    
    # 月次予測
    if impact.monthly_projection:
        st.write("**月次予測:**")
        projection_df = pd.DataFrame([impact.monthly_projection])
        st.dataframe(projection_df)


def display_future_prediction(prediction: Dict):
    """将来予測の表示"""
    st.subheader("🔮 将来予測")
    
    # 予測結果
    st.write("**30日後予測:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pred_value = prediction.get("prediction_30_days", {})
        st.metric("予測不足時間", f"{pred_value.get('predicted_shortage', 0):.1f}h")
    with col2:
        st.metric("信頼区間下限", f"{pred_value.get('confidence_interval', [0, 0])[0]:.1f}h")
    with col3:
        st.metric("信頼区間上限", f"{pred_value.get('confidence_interval', [0, 0])[1]:.1f}h")
    
    # トレンド
    if "trend_analysis" in prediction:
        trend = prediction["trend_analysis"]
        st.write(f"**トレンド:** {trend.get('direction', 'N/A')}")
        st.write(f"**季節性:** {trend.get('seasonality', 'N/A')}")
    
    # モデル性能
    if "model_performance" in prediction:
        perf = prediction["model_performance"]
        st.write(f"**モデル精度 (R²):** {perf.get('r2_score', 0):.3f}")


def display_optimal_allocation(simulation: Dict):
    """最適配置シミュレーションの表示"""
    st.subheader("🎯 最適配置シミュレーション")
    
    # 改善指標
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current = simulation.get("current_shortage", 0)
        st.metric("現在の不足", f"{current:.1f}h")
    with col2:
        optimized = simulation.get("optimized_shortage", 0)
        st.metric("最適化後", f"{optimized:.1f}h", 
                 delta=f"{optimized - current:.1f}h")
    with col3:
        improvement = simulation.get("improvement_percentage", 0)
        st.metric("改善率", f"{improvement:.1f}%")
    
    # 推奨配置
    if "recommended_allocation" in simulation:
        st.write("**推奨配置:**")
        alloc_df = pd.DataFrame(simulation["recommended_allocation"])
        st.dataframe(alloc_df)
    
    # 制約条件
    if "constraints_satisfied" in simulation:
        satisfied = simulation["constraints_satisfied"]
        st.write(f"**制約条件充足:** {'✅' if satisfied else '⚠️'}")


def display_workload_analysis(workload):
    """個人負荷分析の表示"""
    st.subheader("👥 個人負荷分析")
    
    if not workload:
        st.info("分析対象のスタッフデータがありません")
        return
    
    # データフレーム化
    workload_df = pd.DataFrame([{
        'スタッフ': w.staff_name,
        '総勤務時間': w.total_hours,
        '平均シフト長': w.average_shift_length,
        '疲労スコア': w.fatigue_score,
        'リスクレベル': w.risk_level.value,
        '推奨アクション': ', '.join(w.recommended_actions[:2]) if w.recommended_actions else 'なし'
    } for w in workload])
    
    # ハイリスクスタッフ
    high_risk = workload_df[workload_df['リスクレベル'].isin(['危険', '高'])]
    if not high_risk.empty:
        st.warning(f"⚠️ {len(high_risk)}名のスタッフが高リスク状態です")
    
    # データ表示
    st.dataframe(workload_df, use_container_width=True)


def display_statistical_insights(insights):
    """統計分析の表示"""
    st.subheader("📈 高度統計分析")
    
    # 相関分析
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**相関分析:**")
        st.write(f"需要-不足相関: {insights.correlation_analysis.demand_shortage:.2f}")
        st.write(f"スタッフ-不足相関: {insights.correlation_analysis.staff_shortage:.2f}")
    
    with col2:
        st.write("**回帰分析:**")
        st.write(f"R²スコア: {insights.regression_analysis.r2_score:.3f}")
        st.write(f"予測精度: {(1 - insights.regression_analysis.mse / 100):.1%}")
    
    # クラスタリング
    if insights.clustering_results.cluster_sizes:
        st.write("**クラスタ分析:**")
        cluster_df = pd.DataFrame({
            'クラスタ': list(range(len(insights.clustering_results.cluster_sizes))),
            'サイズ': insights.clustering_results.cluster_sizes
        })
        st.bar_chart(cluster_df.set_index('クラスタ'))
    
    # 時系列分析
    st.write("**時系列分析:**")
    st.write(f"トレンド: {insights.time_series_analysis.trend}")
    st.write(f"予測値: {insights.time_series_analysis.forecast_values[:3]}")


def display_section_details(section_name: str, section_data: Any):
    """汎用セクション表示"""
    title_map = {
        "root_causes": "根本原因",
        "cost_impact": "コスト影響",
        "future_prediction": "将来予測",
        "optimal_allocation": "最適配置",
        "workload_analysis": "負荷分析",
        "statistical_insights": "統計洞察"
    }
    
    with st.expander(f"📌 {title_map.get(section_name, section_name)}"):
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                if isinstance(value, (int, float)):
                    st.write(f"{key}: {value:.2f}")
                elif isinstance(value, list):
                    st.write(f"{key}: {', '.join(map(str, value[:5]))}")
                else:
                    st.write(f"{key}: {value}")
        else:
            st.write(section_data)


# Dash用のインターフェース（必要に応じて実装）
def get_advanced_analysis_for_dash(data_dir: Path, analysis_type: str = "comprehensive") -> Dict:
    """
    Dash用の高度分析データを取得
    
    Args:
        data_dir: データディレクトリ
        analysis_type: 分析タイプ
        
    Returns:
        分析結果の辞書
    """
    try:
        analyzer = ComprehensiveShortageAnalyzer(data_dir)
        
        if not analyzer.load_all_data():
            return {"error": "データ読み込み失敗"}
        
        if analysis_type == "comprehensive":
            return analyzer.generate_comprehensive_report()
        elif analysis_type == "root_causes":
            return analyzer.analyze_root_causes()
        elif analysis_type == "cost_impact":
            impact = analyzer.analyze_cost_impact()
            return impact.__dict__
        elif analysis_type == "prediction":
            return analyzer.predict_future_shortage(use_ml=True)
        elif analysis_type == "optimization":
            return analyzer.simulate_optimal_allocation()
        elif analysis_type == "workload":
            workload = analyzer.analyze_individual_workload()
            return {"workload": [w.__dict__ for w in workload]}
        elif analysis_type == "statistical":
            insights = analyzer.perform_advanced_statistical_analysis()
            return {
                "correlation": insights.correlation_analysis.__dict__,
                "regression": insights.regression_analysis.__dict__,
                "clustering": insights.clustering_results.__dict__,
                "time_series": insights.time_series_analysis.__dict__
            }
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
            
    except Exception as e:
        logger.error(f"Dash analysis error: {e}", exc_info=True)
        return {"error": str(e)}