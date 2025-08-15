#!/usr/bin/env python3
"""
app.py - Streamlitアプリケーション（セーフモード）
scikit-learn依存関係問題を回避したバージョン
"""

import streamlit as st
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# 安全なインポート（scikit-learn依存なし）
try:
    from shift_suite.tasks.utils import safe_read_excel, log
    from shift_suite.tasks.io_excel import ingest_excel
    from shift_suite.tasks.heatmap import build_heatmap
    from shift_suite.tasks.shortage import shortage_and_brief
    from shift_suite.tasks.fairness import run_fairness
    from shift_suite.tasks.forecast import build_demand_series, forecast_need
    _HAS_BASIC_SUITE = True
except ImportError as e:
    log.error(f"Basic shift_suite imports failed: {e}")
    _HAS_BASIC_SUITE = False

# 複合制約発見システム（軽量版）
try:
    from shift_suite.tasks.shift_mind_reader_lite import ShiftMindReaderLite
    _HAS_CONSTRAINT_ANALYSIS = True
except ImportError:
    _HAS_CONSTRAINT_ANALYSIS = False

def main():
    """メインアプリケーション（セーフモード）"""
    st.set_page_config(
        page_title="シフト分析システム（セーフモード）",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 シフト分析システム（セーフモード）")
    
    # システム状態表示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if _HAS_BASIC_SUITE:
            st.success("✅ 基本機能利用可能")
        else:
            st.error("❌ 基本機能利用不可")
    
    with col2:
        if _HAS_CONSTRAINT_ANALYSIS:
            st.success("✅ 制約分析利用可能")
        else:
            st.warning("⚠️ 制約分析は軽量版のみ")
    
    with col3:
        st.info("🔧 セーフモード動作中")
    
    # 依存関係問題の説明
    with st.expander("ℹ️ セーフモードについて"):
        st.markdown("""
        **セーフモード**は、scikit-learn DLL依存関係問題を回避するために設計されています。
        
        **利用可能な機能:**
        - ✅ 基本的なシフト分析
        - ✅ ヒートマップ生成
        - ✅ 不足分析
        - ✅ 公平性分析
        - ✅ 需要予測（基本版）
        - ✅ 軽量版制約発見
        
        **制限されている機能:**
        - ❌ 高度な機械学習分析
        - ❌ クラスタリング分析
        - ❌ 異常検知分析
        - ❌ スキルマトリックス構築
        """)
    
    # データアップロード
    st.header("📁 データアップロード")
    
    uploaded_file = st.file_uploader(
        "Excelファイルをアップロードしてください",
        type=['xlsx', 'xls'],
        help="シフトデータが含まれるExcelファイルを選択してください"
    )
    
    if uploaded_file is not None:
        # ファイル情報表示
        st.info(f"📄 アップロードファイル: {uploaded_file.name}")
        
        try:
            # データ読み込み
            if _HAS_BASIC_SUITE:
                # safe_read_excelを使用して読み込み
                df = safe_read_excel(uploaded_file)
                st.success("✅ データ読み込み成功")
                
                # データ概要表示
                st.subheader("📊 データ概要")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("総レコード数", len(df))
                with col2:
                    st.metric("列数", len(df.columns))
                with col3:
                    if 'staff' in df.columns:
                        st.metric("スタッフ数", df['staff'].nunique())
                    else:
                        st.metric("スタッフ数", "不明")
                with col4:
                    if 'ds' in df.columns:
                        date_range = f"{df['ds'].min().date()} - {df['ds'].max().date()}"
                        st.metric("期間", "確認")
                        st.caption(date_range)
                    else:
                        st.metric("期間", "不明")
                
                # データプレビュー
                st.subheader("🔍 データプレビュー")
                st.dataframe(df.head(10), use_container_width=True)
                
                # 制約分析実行
                if _HAS_CONSTRAINT_ANALYSIS and st.button("🔍 軽量版制約分析を実行"):
                    with st.spinner("制約分析を実行中..."):
                        try:
                            mind_reader = ShiftMindReaderLite()
                            insights = mind_reader.get_simplified_insights(df)
                            
                            st.success("✅ 制約分析完了")
                            
                            # 結果表示
                            st.subheader("📋 発見された制約パターン")
                            
                            if insights.get('key_findings'):
                                st.write("**主要な発見:**")
                                for finding in insights['key_findings']:
                                    st.write(f"• {finding}")
                            
                            if insights.get('recommendations'):
                                st.write("**推奨事項:**")
                                for recommendation in insights['recommendations']:
                                    st.write(f"• {recommendation}")
                            
                            # 結果をJSONで表示（詳細）
                            with st.expander("詳細な分析結果"):
                                st.json(insights)
                        
                        except Exception as e:
                            st.error(f"制約分析エラー: {e}")
                            
            else:
                # 基本機能が使えない場合のフォールバック
                df = pd.read_excel(uploaded_file)
                st.warning("⚠️ 基本機能制限モードで読み込み")
                
                st.subheader("📊 基本データ情報")
                st.write(f"レコード数: {len(df)}")
                st.write(f"列数: {len(df.columns)}")
                st.write("列名:", list(df.columns))
                
                st.dataframe(df.head(), use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ データ読み込みエラー: {e}")
            log.error(f"Data loading error: {e}")
    
    # システム診断
    st.header("🔧 システム診断")
    
    if st.button("システム診断実行"):
        with st.spinner("診断中..."):
            diagnosis = {
                "timestamp": datetime.now().isoformat(),
                "basic_suite": _HAS_BASIC_SUITE,
                "constraint_analysis": _HAS_CONSTRAINT_ANALYSIS,
                "python_version": f"{__import__('sys').version}",
                "pandas_version": pd.__version__,
                "numpy_version": np.__version__
            }
            
            st.success("✅ 診断完了")
            st.json(diagnosis)
    
    # フッター
    st.markdown("---")
    st.markdown("""
    **シフト分析システム セーフモード**  
    - 依存関係問題を回避した軽量版
    - 基本的な分析機能を提供  
    - 制約発見システムの実証版
    """)

if __name__ == "__main__":
    main()