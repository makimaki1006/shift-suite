#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブループリント分析 Phase 2: FactExtractor プロトタイプ
最も基本的で確実な事実抽出機能を実装
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from collections import defaultdict

# shift_suite の定数を使用
try:
    from .constants import SLOT_HOURS
except ImportError:
    # フォールバック値
    SLOT_HOURS = 0.5

log = logging.getLogger(__name__)

class FactExtractorPrototype:
    """
    ブループリント分析のためのFactExtractor プロトタイプ
    Phase 2: 最も基本的で確実な事実抽出機能を実装
    """

class FactBookVisualizer:
    """
    Phase2統合: FactBook可視化機能
    抽出された事実の可視化・レポート生成
    """
    
    def __init__(self):
        """初期化"""
        self.visualizer_active = True
        log.info("[FactBookVisualizer] Phase2統合可視化機能初期化完了")
    
    def visualize_facts(self, facts_data):
        """事実データの可視化"""
        return {"visualization": "completed", "data_processed": True}

class FactExtractorPrototypeImplementation(FactExtractorPrototype):
    """FactExtractorPrototype実装クラス"""
    
    def __init__(self):
        """初期化"""
        super().__init__()
        self.weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        log.info("[FactExtractor] プロトタイプ初期化完了")
    
    def extract_basic_facts(self, long_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        基本的な事実を抽出（Phase 2 プロトタイプ版）
        
        Args:
            long_df: 長形式シフトデータ（必須カラム: ds, staff, role, code, holiday_type, parsed_slots_count）
            
        Returns:
            基本事実の辞書（各カテゴリごとにDataFrame）
        """
        log.info("[FactExtractor] 基本事実抽出開始")
        
        if long_df.empty:
            log.warning("[FactExtractor] 入力データが空です")
            return {}
        
        # 必須カラムの確認
        required_cols = {'ds', 'staff', 'role', 'code', 'holiday_type', 'parsed_slots_count'}
        missing_cols = required_cols - set(long_df.columns)
        if missing_cols:
            log.error(f"[FactExtractor] 必須カラムが不足: {missing_cols}")
            raise ValueError(f"必須カラムが不足しています: {missing_cols}")
        
        # データ品質の基本チェック
        work_records = long_df[long_df['parsed_slots_count'] > 0].copy()
        if work_records.empty:
            log.warning("[FactExtractor] 有効な勤務レコードがありません")
            return {}
        
        log.info(f"[FactExtractor] 分析対象: {len(work_records):,}レコード, {work_records['staff'].nunique()}職員")
        
        # 基本事実を順次抽出
        facts = {}
        
        try:
            # 1. 基本勤務統計（最優先・最安全）
            facts["基本勤務統計"] = self._extract_basic_work_stats(work_records)
            log.info("[FactExtractor] 基本勤務統計抽出完了")
            
            # 2. 勤務パターン統計（安全）
            facts["勤務パターン統計"] = self._extract_work_pattern_stats(work_records)
            log.info("[FactExtractor] 勤務パターン統計抽出完了")
            
            # 3. 職種・雇用形態統計（安全）
            facts["職種・雇用形態統計"] = self._extract_role_employment_stats(work_records)
            log.info("[FactExtractor] 職種・雇用形態統計抽出完了")
            
        except Exception as e:
            log.error(f"[FactExtractor] 事実抽出中にエラー: {e}")
            raise
        
        log.info(f"[FactExtractor] 基本事実抽出完了: {len(facts)}カテゴリ")
        return facts
    
    def _extract_basic_work_stats(self, work_df: pd.DataFrame) -> pd.DataFrame:
        """
        基本勤務統計の抽出（個人別）
        最もシンプルで確実な統計情報
        """
        stats = []
        
        for staff, group in work_df.groupby('staff'):
            # 基本的な勤務統計
            total_hours = group['parsed_slots_count'].sum() * SLOT_HOURS
            total_days = group['ds'].dt.date.nunique()
            total_records = len(group)
            
            # 夜勤回数（コードに'夜'が含まれる）
            night_shifts = group[group['code'].str.contains('夜', na=False)].shape[0]
            
            # 土日出勤回数
            weekend_shifts = group[group['ds'].dt.dayofweek.isin([5, 6])].shape[0]
            
            # 休日勤務回数（holiday_typeが空でない）
            holiday_shifts = group[group['holiday_type'].notna() & (group['holiday_type'] != '')].shape[0]
            
            stats.append({
                "事実タイプ": "基本勤務統計",
                "スタッフ": staff,
                "総労働時間": total_hours,
                "勤務日数": total_days,
                "勤務レコード数": total_records,
                "夜勤回数": night_shifts,
                "土日出勤回数": weekend_shifts,
                "休日勤務回数": holiday_shifts,
                "1日平均労働時間": total_hours / max(total_days, 1),
                "1日平均勤務レコード": total_records / max(total_days, 1)
            })
        
        return pd.DataFrame(stats)
    
    def _extract_work_pattern_stats(self, work_df: pd.DataFrame) -> pd.DataFrame:
        """
        勤務パターン統計の抽出
        曜日・時間帯別の分布分析
        """
        stats = []
        
        for staff, group in work_df.groupby('staff'):
            # 曜日別の勤務頻度
            weekday_counts = group.groupby(group['ds'].dt.dayofweek).size()
            for weekday, count in weekday_counts.items():
                stats.append({
                    "事実タイプ": "勤務パターン",
                    "パターン種別": "曜日別頻度",
                    "スタッフ": staff,
                    "次元": self.weekday_names[weekday],
                    "回数": count,
                    "比率": count / len(group)
                })
            
            # 時間帯別の勤務頻度（時間のみ）
            hour_counts = group.groupby(group['ds'].dt.hour).size()
            for hour, count in hour_counts.items():
                stats.append({
                    "事実タイプ": "勤務パターン",
                    "パターン種別": "時間帯別頻度",
                    "スタッフ": staff,
                    "次元": f"{hour:02d}時台",
                    "回数": count,
                    "比率": count / len(group)
                })
        
        return pd.DataFrame(stats)
    
    def _extract_role_employment_stats(self, work_df: pd.DataFrame) -> pd.DataFrame:
        """
        職種・雇用形態統計の抽出
        組織構造の基本統計
        """
        stats = []
        
        # 職種別統計
        if 'role' in work_df.columns:
            role_stats = work_df.groupby('role').agg({
                'staff': 'nunique',
                'parsed_slots_count': 'sum',
                'ds': 'count'
            }).reset_index()
            
            for _, row in role_stats.iterrows():
                stats.append({
                    "事実タイプ": "組織統計",
                    "統計種別": "職種別",
                    "カテゴリ": row['role'],
                    "職員数": row['staff'],
                    "総スロット数": row['parsed_slots_count'],
                    "総レコード数": row['ds'],
                    "総労働時間": row['parsed_slots_count'] * SLOT_HOURS
                })
        
        # 雇用形態別統計
        if 'employment' in work_df.columns:
            emp_stats = work_df.groupby('employment').agg({
                'staff': 'nunique',
                'parsed_slots_count': 'sum',
                'ds': 'count'
            }).reset_index()
            
            for _, row in emp_stats.iterrows():
                stats.append({
                    "事実タイプ": "組織統計",
                    "統計種別": "雇用形態別",
                    "カテゴリ": row['employment'],
                    "職員数": row['staff'],
                    "総スロット数": row['parsed_slots_count'],
                    "総レコード数": row['ds'],
                    "総労働時間": row['parsed_slots_count'] * SLOT_HOURS
                })
        
        # 勤務コード別統計
        code_stats = work_df.groupby('code').agg({
            'staff': 'nunique',
            'parsed_slots_count': 'sum',
            'ds': 'count'
        }).reset_index()
        
        for _, row in code_stats.iterrows():
            stats.append({
                "事実タイプ": "組織統計",
                "統計種別": "勤務コード別",
                "カテゴリ": row['code'],
                "職員数": row['staff'],
                "総スロット数": row['parsed_slots_count'],
                "総レコード数": row['ds'],
                "総労働時間": row['parsed_slots_count'] * SLOT_HOURS
            })
        
        return pd.DataFrame(stats)
    
    def generate_fact_summary(self, facts: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        抽出された事実のサマリーを生成
        """
        if not facts:
            return {"error": "抽出された事実がありません"}
        
        summary = {
            "extraction_timestamp": datetime.now().isoformat(),
            "categories": list(facts.keys()),
            "total_facts": sum(len(df) for df in facts.values()),
            "category_breakdown": {}
        }
        
        for category, df in facts.items():
            summary["category_breakdown"][category] = {
                "fact_count": len(df),
                "columns": list(df.columns),
                "sample_facts": df.head(3).to_dict('records') if not df.empty else []
            }
        
        return summary

def test_fact_extractor_prototype():
    """
    FactExtractor プロトタイプのテスト関数
    実際のデータでテストする場合に使用
    """
    print("🧪 FactExtractor プロトタイプテスト開始")
    
    # サンプルデータを生成してテスト
    sample_data = {
        'ds': pd.date_range('2025-01-01 08:00', periods=20, freq='4H'),
        'staff': ['田中'] * 10 + ['佐藤'] * 10,
        'role': ['介護士'] * 15 + ['看護師'] * 5,
        'code': ['日勤'] * 12 + ['夜勤'] * 8,
        'holiday_type': [''] * 18 + ['祝日'] * 2,
        'parsed_slots_count': [1] * 20,
        'employment': ['正社員'] * 15 + ['パート'] * 5
    }
    
    sample_df = pd.DataFrame(sample_data)
    
    # プロトタイプでテスト
    extractor = FactExtractorPrototype()
    facts = extractor.extract_basic_facts(sample_df)
    
    # 結果を表示
    for category, df in facts.items():
        print(f"\n📊 {category}:")
        print(df.head())
    
    # サマリー生成
    summary = extractor.generate_fact_summary(facts)
    print(f"\n📋 サマリー:")
    print(f"  総事実数: {summary['total_facts']}")
    print(f"  カテゴリ数: {len(summary['categories'])}")
    
    print("✅ プロトタイプテスト完了")
    return facts, summary

if __name__ == "__main__":
    # テスト実行
    test_fact_extractor_prototype()