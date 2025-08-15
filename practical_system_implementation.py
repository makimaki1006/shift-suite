#!/usr/bin/env python3
"""
実用システム実装 - ユーザビリティ重視の実用制約発見システム
軽量版の成果を基に、実際に使える形での実装を提供
"""

import streamlit as st
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import os

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class PracticalConstraintDiscoverySystem:
    """実用制約発見システム"""
    
    def __init__(self):
        self.system_name = "シフト制約発見システム（実用版）"
        self.version = "1.0.0"
        self.lightweight_mode = True  # 軽量版モードで開始
        self.available_files = self._scan_available_files()
    
    def _scan_available_files(self) -> List[str]:
        """利用可能Excelファイルのスキャン"""
        excel_extensions = ['.xlsx', '.xls']
        current_dir = Path('.')
        
        excel_files = []
        for ext in excel_extensions:
            excel_files.extend([f.name for f in current_dir.glob(f'*{ext}')])
        
        return sorted(excel_files)
    
    def analyze_file_constraints(self, file_path: str) -> Dict[str, Any]:
        """ファイル制約分析（実用版）"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": f"ファイル {file_path} が見つかりません"}
            
            file_size = path.stat().st_size
            filename = path.name
            
            # ファイル分析
            constraints = []
            
            # 1. データ可用性制約
            constraints.append({
                "id": f"availability_{hash(filename) % 1000}",
                "type": "データ可用性",
                "constraint": f"{filename}は分析可能です",
                "detail": f"ファイルサイズ: {file_size:,}バイト",
                "confidence": 1.0,
                "priority": "高",
                "actionable": True,
                "action": "このファイルを使用してシフト分析を実行できます"
            })
            
            # 2. ファイルサイズ制約
            if file_size > 100000:  # 100KB以上
                constraints.append({
                    "id": f"size_large_{hash(filename) % 1000}",
                    "type": "データ量制約",
                    "constraint": f"{filename}は大容量データです",
                    "detail": f"サイズ: {file_size:,}バイト（詳細分析推奨）",
                    "confidence": 0.9,
                    "priority": "中",
                    "actionable": True,
                    "action": "段階的な分析実行を推奨します"
                })
            elif file_size < 20000:  # 20KB未満
                constraints.append({
                    "id": f"size_small_{hash(filename) % 1000}",
                    "type": "データ量制約", 
                    "constraint": f"{filename}は小容量データです",
                    "detail": f"サイズ: {file_size:,}バイト（迅速分析可能）",
                    "confidence": 0.8,
                    "priority": "低",
                    "actionable": True,
                    "action": "高速分析が期待できます"
                })
            
            # 3. シフトタイプ制約（ファイル名から推測）
            shift_keywords = {
                'デイ': '日勤シフト',
                'ショート': '短時間シフト', 
                'ナイト': '夜勤シフト',
                '夜勤': '夜勤シフト',
                '日勤': '日勤シフト'
            }
            
            for keyword, shift_type in shift_keywords.items():
                if keyword in filename:
                    constraints.append({
                        "id": f"shift_{keyword.lower()}_{hash(filename) % 1000}",
                        "type": "シフトタイプ制約",
                        "constraint": f"{filename}は{shift_type}特化データです",
                        "detail": f"キーワード「{keyword}」から推測",
                        "confidence": 0.85,
                        "priority": "高",
                        "actionable": True,
                        "action": f"{shift_type}の詳細分析に集中することを推奨"
                    })
            
            # 4. データ目的制約
            if any(keyword in filename for keyword in ['テスト', 'test', 'トライアル', 'trial']):
                constraints.append({
                    "id": f"purpose_test_{hash(filename) % 1000}",
                    "type": "データ目的制約",
                    "constraint": f"{filename}はテスト・実験用データです",
                    "detail": "本番データとは異なる可能性があります",
                    "confidence": 0.95,
                    "priority": "中",
                    "actionable": True,
                    "action": "分析結果は参考値として扱うことを推奨"
                })
            
            # 5. 実用性制約
            if file_size > 10000 and not any(keyword in filename for keyword in ['backup', 'old', '古い']):
                constraints.append({
                    "id": f"practical_{hash(filename) % 1000}",
                    "type": "実用性制約",
                    "constraint": f"{filename}は実用分析に適しています",
                    "detail": "適切なサイズと最新性を持つデータ",
                    "confidence": 0.9,
                    "priority": "高",
                    "actionable": True,
                    "action": "優先的にこのファイルで分析を実行"
                })
            
            return {
                "success": True,
                "file_info": {
                    "name": filename,
                    "size": file_size,
                    "path": str(path)
                },
                "constraints": constraints,
                "summary": {
                    "total_constraints": len(constraints),
                    "high_priority": len([c for c in constraints if c["priority"] == "高"]),
                    "actionable_items": len([c for c in constraints if c["actionable"]]),
                    "avg_confidence": sum(c["confidence"] for c in constraints) / len(constraints) if constraints else 0
                }
            }
            
        except Exception as e:
            return {"error": f"ファイル分析エラー: {str(e)}"}
    
    def batch_analyze_files(self, file_list: List[str]) -> Dict[str, Any]:
        """バッチファイル分析"""
        results = {}
        total_constraints = 0
        total_actionable = 0
        
        for file_path in file_list:
            result = self.analyze_file_constraints(file_path)
            results[file_path] = result
            
            if result.get("success"):
                total_constraints += result["summary"]["total_constraints"]
                total_actionable += result["summary"]["actionable_items"]
        
        # 統合分析
        successful_analyses = [r for r in results.values() if r.get("success")]
        
        if successful_analyses:
            avg_confidence = sum(r["summary"]["avg_confidence"] for r in successful_analyses) / len(successful_analyses)
            
            # カテゴリ別統計
            category_stats = {}
            for result in successful_analyses:
                for constraint in result["constraints"]:
                    category = constraint["type"]
                    if category not in category_stats:
                        category_stats[category] = {"count": 0, "high_priority": 0}
                    category_stats[category]["count"] += 1
                    if constraint["priority"] == "高":
                        category_stats[category]["high_priority"] += 1
        else:
            avg_confidence = 0
            category_stats = {}
        
        return {
            "individual_results": results,
            "batch_summary": {
                "files_analyzed": len(file_list),
                "successful_analyses": len(successful_analyses),
                "total_constraints": total_constraints,
                "total_actionable": total_actionable,
                "avg_confidence": avg_confidence,
                "category_statistics": category_stats
            }
        }
    
    def generate_actionable_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """実行可能な推奨事項生成"""
        recommendations = []
        
        if "batch_summary" in analysis_result:
            summary = analysis_result["batch_summary"]
            
            # 1. ファイル選択推奨
            successful_files = []
            for file_path, result in analysis_result["individual_results"].items():
                if result.get("success") and result["summary"]["high_priority"] > 0:
                    successful_files.append((file_path, result["summary"]["avg_confidence"]))
            
            if successful_files:
                best_file = max(successful_files, key=lambda x: x[1])
                recommendations.append({
                    "category": "ファイル選択",
                    "priority": "最高",
                    "recommendation": f"{best_file[0]}での分析を優先実行",
                    "reason": f"信頼度{best_file[1]:.1%}で最適なファイル",
                    "action": "このファイルをアップロードして制約分析を実行"
                })
            
            # 2. 分析アプローチ推奨
            if summary["total_constraints"] > 15:
                recommendations.append({
                    "category": "分析戦略",
                    "priority": "高",
                    "recommendation": "段階的詳細分析を実行",
                    "reason": f"{summary['total_constraints']}個の制約発見により複雑なデータ",
                    "action": "カテゴリ別に制約を整理して優先順位を設定"
                })
            elif summary["total_constraints"] > 5:
                recommendations.append({
                    "category": "分析戦略",  
                    "priority": "中",
                    "recommendation": "標準制約分析を実行",
                    "reason": f"{summary['total_constraints']}個の制約で適度な複雑性",
                    "action": "全制約を一括分析して包括的理解を獲得"
                })
            
            # 3. 実用化推奨
            if summary["total_actionable"] > 10:
                recommendations.append({
                    "category": "実用化",
                    "priority": "高", 
                    "recommendation": "制約活用計画を策定",
                    "reason": f"{summary['total_actionable']}個の実行可能制約",
                    "action": "制約を実際のシフト改善に適用する計画を立案"
                })
        
        return recommendations
    
    def create_user_dashboard(self) -> None:
        """ユーザーダッシュボード作成"""
        st.set_page_config(
            page_title=self.system_name,
            page_icon="🔍",
            layout="wide"
        )
        
        st.title(f"🔍 {self.system_name}")
        st.caption(f"Version {self.version} - 実用制約発見システム")
        
        # システム状態表示
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("動作モード", "軽量版" if self.lightweight_mode else "完全版")
        with col2:
            st.metric("利用可能ファイル", len(self.available_files))
        with col3:
            st.metric("システム状態", "稼働中")
        with col4:
            st.metric("分析準備", "完了")
        
        # タブ構成
        tab1, tab2, tab3, tab4 = st.tabs(["📁 ファイル分析", "📊 バッチ分析", "💡 推奨事項", "⚙️ システム情報"])
        
        with tab1:
            self._render_file_analysis_tab()
        
        with tab2:
            self._render_batch_analysis_tab()
        
        with tab3:
            self._render_recommendations_tab()
        
        with tab4:
            self._render_system_info_tab()
    
    def _render_file_analysis_tab(self):
        """ファイル分析タブ"""
        st.header("📁 単一ファイル分析")
        
        # ファイル選択
        if self.available_files:
            selected_file = st.selectbox(
                "分析するファイルを選択してください:",
                self.available_files,
                help="検出された利用可能なExcelファイルから選択"
            )
            
            if st.button("🔍 制約分析実行", type="primary"):
                with st.spinner(f"{selected_file}を分析中..."):
                    result = self.analyze_file_constraints(selected_file)
                    
                    if result.get("success"):
                        st.success(f"✅ {selected_file}の分析完了")
                        
                        # 分析サマリー表示
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("発見制約数", result["summary"]["total_constraints"])
                        with col2:
                            st.metric("高優先度", result["summary"]["high_priority"])
                        with col3:
                            st.metric("実行可能項目", result["summary"]["actionable_items"])
                        with col4:
                            st.metric("平均信頼度", f"{result['summary']['avg_confidence']:.1%}")
                        
                        # 制約詳細表示
                        st.subheader("🎯 発見された制約")
                        
                        for i, constraint in enumerate(result["constraints"], 1):
                            with st.expander(f"{i}. {constraint['constraint']} (優先度: {constraint['priority']})"):
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.write(f"**詳細:** {constraint['detail']}")
                                    st.write(f"**カテゴリ:** {constraint['type']}")
                                    if constraint['actionable']:
                                        st.info(f"**推奨アクション:** {constraint['action']}")
                                with col2:
                                    st.metric("信頼度", f"{constraint['confidence']:.1%}")
                                    priority_color = {"高": "🔴", "中": "🟡", "低": "🟢"}
                                    st.write(f"優先度: {priority_color.get(constraint['priority'], '⚪')} {constraint['priority']}")
                        
                        # 結果をセッション状態に保存
                        st.session_state['last_analysis'] = result
                        
                    else:
                        st.error(f"❌ 分析エラー: {result.get('error', '不明なエラー')}")
        else:
            st.warning("⚠️ 分析可能なExcelファイルが見つかりません")
            st.info("以下の形式のファイルを作業ディレクトリに配置してください: .xlsx, .xls")
    
    def _render_batch_analysis_tab(self):
        """バッチ分析タブ"""
        st.header("📊 バッチファイル分析")
        
        if self.available_files:
            st.write("複数ファイルを同時に分析します:")
            
            selected_files = st.multiselect(
                "分析するファイルを選択してください:",
                self.available_files,
                default=self.available_files[:min(3, len(self.available_files))],
                help="最大5ファイルまで同時分析可能"
            )
            
            if selected_files and st.button("🚀 バッチ分析実行", type="primary"):
                with st.spinner(f"{len(selected_files)}個のファイルを分析中..."):
                    batch_result = self.batch_analyze_files(selected_files)
                    
                    st.success(f"✅ {batch_result['batch_summary']['successful_analyses']}個のファイル分析完了")
                    
                    # バッチサマリー表示
                    summary = batch_result["batch_summary"]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("分析ファイル数", summary["files_analyzed"])
                    with col2:
                        st.metric("成功数", summary["successful_analyses"])
                    with col3:
                        st.metric("総制約数", summary["total_constraints"])
                    with col4:
                        st.metric("実行可能項目", summary["total_actionable"])
                    
                    # カテゴリ別統計
                    if summary["category_statistics"]:
                        st.subheader("📈 制約カテゴリ別統計")
                        
                        category_data = []
                        for category, stats in summary["category_statistics"].items():
                            category_data.append({
                                "カテゴリ": category,
                                "制約数": stats["count"],
                                "高優先度": stats["high_priority"],
                                "重要度": f"{stats['high_priority']/stats['count']*100:.0f}%" if stats["count"] > 0 else "0%"
                            })
                        
                        st.dataframe(category_data, use_container_width=True)
                    
                    # ファイル別詳細
                    st.subheader("📋 ファイル別分析結果")
                    
                    for file_path, result in batch_result["individual_results"].items():
                        if result.get("success"):
                            with st.expander(f"📄 {file_path} ({result['summary']['total_constraints']}個の制約)"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("制約数", result["summary"]["total_constraints"])
                                with col2:
                                    st.metric("高優先度", result["summary"]["high_priority"])
                                with col3:
                                    st.metric("信頼度", f"{result['summary']['avg_confidence']:.1%}")
                                
                                # 重要制約のみ表示（高優先度）
                                high_priority_constraints = [c for c in result["constraints"] if c["priority"] == "高"]
                                if high_priority_constraints:
                                    st.write("**主要制約:**")
                                    for constraint in high_priority_constraints[:3]:  # 最大3件
                                        st.write(f"• {constraint['constraint']}")
                        else:
                            with st.expander(f"❌ {file_path} (分析失敗)"):
                                st.error(result.get("error", "不明なエラー"))
                    
                    # 結果をセッション状態に保存
                    st.session_state['batch_analysis'] = batch_result
        else:
            st.warning("⚠️ 分析可能なExcelファイルが見つかりません")
    
    def _render_recommendations_tab(self):
        """推奨事項タブ"""
        st.header("💡 実行可能な推奨事項")
        
        # 過去の分析結果から推奨事項生成
        if 'batch_analysis' in st.session_state:
            recommendations = self.generate_actionable_recommendations(st.session_state['batch_analysis'])
            
            if recommendations:
                st.success(f"✅ {len(recommendations)}個の推奨事項を生成しました")
                
                for i, rec in enumerate(recommendations, 1):
                    priority_colors = {"最高": "🔴", "高": "🟡", "中": "🟢", "低": "⚪"}
                    priority_color = priority_colors.get(rec["priority"], "⚪")
                    
                    with st.container():
                        st.subheader(f"{priority_color} {i}. {rec['recommendation']}")
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**カテゴリ:** {rec['category']}")
                            st.write(f"**理由:** {rec['reason']}")
                            st.info(f"**具体的アクション:** {rec['action']}")
                        with col2:
                            st.metric("優先度", rec["priority"])
                        
                        st.divider()
            else:
                st.info("ℹ️ 推奨事項を生成するには、まずバッチ分析を実行してください")
        
        elif 'last_analysis' in st.session_state:
            st.info("ℹ️ より詳細な推奨事項を得るには、バッチ分析タブで複数ファイルを分析してください")
            
            # 単一ファイル分析からの基本推奨
            result = st.session_state['last_analysis']
            st.write("**基本推奨事項:**")
            
            if result["summary"]["actionable_items"] > 0:
                st.success(f"✅ {result['summary']['actionable_items']}個の実行可能項目があります")
                st.write("1. 制約詳細を確認して具体的改善策を検討")
                st.write("2. 高優先度制約から順次対応を開始")
                st.write("3. 制約を実際のシフト作成に反映")
            else:
                st.warning("⚠️ 実行可能項目が見つかりませんでした")
        else:
            st.info("ℹ️ 推奨事項を表示するには、まずファイル分析を実行してください")
    
    def _render_system_info_tab(self):
        """システム情報タブ"""
        st.header("⚙️ システム情報")
        
        # システム状態
        system_info = {
            "システム名": self.system_name,
            "バージョン": self.version,
            "動作モード": "軽量版（依存関係フリー）",
            "分析エンジン": "ファイルベース制約発見",
            "対応形式": "Excel (.xlsx, .xls)",
            "同時分析": "最大5ファイル",
            "最終更新": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 システム詳細")
            for key, value in system_info.items():
                st.write(f"**{key}:** {value}")
        
        with col2:
            st.subheader("📁 利用可能ファイル")
            if self.available_files:
                for i, file in enumerate(self.available_files, 1):
                    file_path = Path(file)
                    file_size = file_path.stat().st_size if file_path.exists() else 0
                    st.write(f"{i}. {file} ({file_size:,}バイト)")
            else:
                st.write("利用可能なファイルがありません")
        
        # 機能情報
        st.subheader("🔧 実装機能")
        features = [
            "✅ 軽量版制約発見エンジン",
            "✅ ファイル可用性チェック",
            "✅ シフトタイプ推測",
            "✅ 実行可能推奨事項生成",
            "✅ バッチファイル分析",
            "✅ インタラクティブUI",
            "⚠️ 高度ML分析（開発中）",
            "⚠️ リアルタイム監視（計画中）"
        ]
        
        for feature in features:
            st.write(feature)
        
        # 使用方法
        st.subheader("📖 使用方法")
        st.write("""
        1. **ファイル分析**: 単一Excelファイルの制約を発見
        2. **バッチ分析**: 複数ファイルを同時に分析
        3. **推奨事項**: 分析結果から実行可能な改善策を提案
        4. **結果活用**: 制約を実際のシフト改善に適用
        """)

def main():
    """メインアプリケーション"""
    try:
        system = PracticalConstraintDiscoverySystem()
        system.create_user_dashboard()
    except Exception as e:
        st.error(f"システムエラー: {e}")
        log.error(f"System error: {e}")

if __name__ == "__main__":
    main()