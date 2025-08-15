#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
シフト分析システム - Streamlit版メインアプリ
分析実行とダッシュボード表示の統合インターフェース
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import subprocess
import sys
import os
import json
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="シフト分析システム",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'analysis_status' not in st.session_state:
    st.session_state.analysis_status = 'idle'
if 'analysis_results_path' not in st.session_state:
    st.session_state.analysis_results_path = None

def run_analysis(excel_file_path):
    """分析を実行"""
    try:
        # shift_suiteコマンドを実行
        cmd = [
            sys.executable, "-m", "shift_suite",
            "run", excel_file_path,
            "--config", "shift_config.json"
        ]
        
        # プロセスを実行
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        # リアルタイムで出力を表示
        progress_container = st.empty()
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                progress_container.text(output.strip())
        
        rc = process.poll()
        
        if rc == 0:
            st.success("✅ 分析が正常に完了しました")
            # 最新の分析結果を取得
            results_dir = Path("analysis_results")
            if results_dir.exists():
                latest_result = max(results_dir.glob("*"), key=os.path.getctime)
                st.session_state.analysis_results_path = latest_result
                return True
        else:
            stderr = process.stderr.read()
            st.error(f"❌ 分析エラー: {stderr}")
            return False
            
    except Exception as e:
        st.error(f"❌ 実行エラー: {str(e)}")
        return False

def main():
    """メインアプリケーション"""
    
    # タイトル
    st.title("📊 シフト分析システム")
    st.markdown("### 修正版 - 不足時間計算とヒートマップ表示を改善")
    
    # サイドバー
    with st.sidebar:
        st.header("🔧 設定")
        
        # 分析モード選択
        mode = st.radio(
            "モード選択",
            ["新規分析実行", "既存結果表示", "ダッシュボード"]
        )
        
        st.divider()
        
        # 修正内容の説明
        st.info("""
        **🎯 修正済み項目:**
        - ✅ 不足時間の重複計算を解消
        - ✅ 職種別ヒートマップの正確な表示
        - ✅ エラーハンドリングの改善
        """)
    
    # メインコンテンツ
    if mode == "新規分析実行":
        st.header("📤 新規分析実行")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader(
            "Excelファイルを選択",
            type=['xlsx', 'xls'],
            help="シフトデータのExcelファイルをアップロードしてください"
        )
        
        # テストファイルの使用オプション
        use_test_file = st.checkbox("テストファイルを使用（デイ_テスト用データ_休日精緻.xlsx）")
        
        if use_test_file:
            test_file_path = Path("デイ_テスト用データ_休日精緻.xlsx")
            if test_file_path.exists():
                st.success(f"✅ テストファイル検出: {test_file_path}")
                if st.button("🚀 分析開始", type="primary"):
                    with st.spinner("分析実行中..."):
                        if run_analysis(str(test_file_path)):
                            st.balloons()
                            st.success("分析が完了しました！")
                            if st.button("📊 ダッシュボードを開く"):
                                st.switch_page("pages/dashboard.py")
            else:
                st.error("テストファイルが見つかりません")
        
        elif uploaded_file is not None:
            # アップロードファイルを保存
            temp_path = Path(f"temp_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ ファイルアップロード完了: {uploaded_file.name}")
            
            if st.button("🚀 分析開始", type="primary"):
                with st.spinner("分析実行中..."):
                    if run_analysis(str(temp_path)):
                        st.balloons()
                        st.success("分析が完了しました！")
                        temp_path.unlink()  # 一時ファイル削除
                        if st.button("📊 ダッシュボードを開く"):
                            st.switch_page("pages/dashboard.py")
    
    elif mode == "既存結果表示":
        st.header("📂 既存分析結果の表示")
        
        # 分析結果ディレクトリをスキャン
        results_dir = Path("analysis_results")
        if results_dir.exists():
            result_dirs = sorted(
                [d for d in results_dir.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if result_dirs:
                # 結果選択
                selected_result = st.selectbox(
                    "分析結果を選択",
                    result_dirs,
                    format_func=lambda x: f"{x.name} ({datetime.fromtimestamp(x.stat().st_mtime).strftime('%Y-%m-%d %H:%M')})"
                )
                
                if selected_result:
                    st.session_state.analysis_results_path = selected_result
                    
                    # 結果サマリー表示
                    col1, col2, col3 = st.columns(3)
                    
                    # 不足時間を確認
                    shortage_file = selected_result / "shortage_role_summary.parquet"
                    if shortage_file.exists():
                        try:
                            df = pd.read_parquet(shortage_file)
                            # 修正済みロジックで計算
                            total_shortage = df[~df['role'].str.startswith('emp_', na=False)]['lack_h'].sum()
                            
                            with col1:
                                st.metric(
                                    "総不足時間",
                                    f"{total_shortage:.1f}時間",
                                    delta="正常値" if total_shortage < 1000 else "要確認"
                                )
                        except Exception as e:
                            st.error(f"データ読み込みエラー: {e}")
                    
                    if st.button("📊 ダッシュボードで詳細表示", type="primary"):
                        st.switch_page("pages/dashboard.py")
            else:
                st.info("分析結果が見つかりません")
        else:
            st.info("分析結果ディレクトリが存在しません")
    
    else:  # ダッシュボード
        st.header("📊 分析ダッシュボード")
        
        # Dashアプリ起動ボタン
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Dashダッシュボード起動", type="primary"):
                st.info("Dashアプリケーションを起動中...")
                # 新しいプロセスでDashを起動
                subprocess.Popen([sys.executable, "run_dash_only.py"])
                st.success("✅ Dashダッシュボードが起動しました")
                st.markdown("[http://localhost:8050](http://localhost:8050) でアクセスしてください")
        
        with col2:
            if st.button("📈 分析結果サマリー表示"):
                st.switch_page("pages/summary.py")

if __name__ == "__main__":
    main()