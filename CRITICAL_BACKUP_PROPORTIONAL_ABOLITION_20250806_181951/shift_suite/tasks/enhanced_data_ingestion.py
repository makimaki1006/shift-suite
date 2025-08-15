#!/usr/bin/env python3
"""
Enhanced Data Ingestion System
統合データ入稿システム - Truth-Driven Analysisの基盤
"""

from __future__ import annotations  # 型ヒント互換性のため保持

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
# from typing import Tuple  # 未使用のためコメントアウト

import numpy as np  # 数値計算で使用される可能性があるため保持
import pandas as pd
from pandas import DataFrame

from .constants import (
    # DEFAULT_SLOT_MINUTES,  # 現在未使用だが将来的に使用される可能性
    QUALITY_PREVIEW_ROWS, QUALITY_SCORE_MAX, 
    QUALITY_PARTIAL_EXCEL_SCORE, QUALITY_LARGE_FILE_SIZE, QUALITY_LARGE_FILE_SCORE,
    QUALITY_SINGLE_SHEET_SCORE, QUALITY_STAFF_MISSING_SCORE, QUALITY_WEIGHTS
)
from .utils import log  # , write_meta  # write_meta は現在未使用

# Analysis logger
analysis_logger = logging.getLogger('analysis')


class QualityAssessmentResult:
    """データ品質評価結果"""
    
    def __init__(self):
        self.overall_score: float = 0.0
        self.file_format_score: float = 0.0
        self.structure_score: float = 0.0
        self.date_range_score: float = 0.0
        self.staff_integrity_score: float = 0.0
        self.shift_code_score: float = 0.0
        self.completeness_score: float = 0.0
        
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        
        self.detected_slot_interval: Optional[int] = None
        self.detected_date_range: Optional[Tuple[datetime, datetime]] = None
        self.staff_count: int = 0
        self.duplicate_staff_names: List[str] = []
        self.missing_dates: List[str] = []
        
        self.recommended_analysis_method: str = "need_based"
        self.confidence_level: str = "high"


class DataLineageTracker:
    """データ系譜追跡システム"""
    
    def __init__(self):
        self.tracking_id: str = ""
        self.source_file: str = ""
        self.ingestion_timestamp: datetime = datetime.now()
        self.processing_steps: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
    
    def track_step(self, step_name: str, details: Dict[str, Any]) -> None:
        """処理ステップを記録"""
        self.processing_steps.append({
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
        analysis_logger.info(f"[LINEAGE] {step_name}: {details}")
    
    def generate_lineage_report(self) -> Dict[str, Any]:
        """系譜レポート生成"""
        return {
            "tracking_id": self.tracking_id,
            "source_file": self.source_file,
            "ingestion_timestamp": self.ingestion_timestamp.isoformat(),
            "processing_steps": self.processing_steps,
            "metadata": self.metadata
        }


class DynamicSchemaInferrer:
    """動的スキーマ推論システム"""
    
    def __init__(self):
        self.inferred_schema: Dict[str, Any] = {}
        self.confidence_scores: Dict[str, float] = {}
    
    def infer_structure(self, excel_path: Path) -> Dict[str, Any]:
        """Excel構造の自動推論"""
        try:
            # 全シートを読み込んで構造分析
            excel_file = pd.ExcelFile(excel_path)
            sheets_info = {}
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=QUALITY_PREVIEW_ROWS)
                    sheets_info[sheet_name] = {
                        "columns": list(df.columns),
                        "shape": df.shape,
                        "detected_type": self._detect_sheet_type(df, sheet_name)
                    }
                except Exception as e:
                    log.warning(f"シート'{sheet_name}'の解析でエラー: {e}")
                    sheets_info[sheet_name] = {"error": str(e)}
            
            # スキーマ推論
            self.inferred_schema = {
                "file_type": "excel",
                "sheets": sheets_info,
                "primary_data_sheet": self._identify_primary_sheet(sheets_info),
                "has_need_file": "Need" in [s.upper() for s in excel_file.sheet_names],
                "has_master_sheet": any("勤務区分" in s or "マスター" in s for s in excel_file.sheet_names)
            }
            
            return self.inferred_schema
            
        except Exception as e:
            log.error(f"スキーマ推論エラー: {e}")
            return {"error": str(e)}
    
    def _detect_sheet_type(self, df: DataFrame, sheet_name: str) -> str:
        """シートタイプの検出"""
        sheet_name_upper = sheet_name.upper()
        
        if "NEED" in sheet_name_upper:
            return "need_file"
        elif "勤務区分" in sheet_name or "マスター" in sheet_name:
            return "master_data"
        elif any(col for col in df.columns if str(col).replace("/", "").replace("-", "").isdigit()):
            return "daily_schedule"
        else:
            return "unknown"
    
    def _identify_primary_sheet(self, sheets_info: Dict) -> Optional[str]:
        """主要データシートの特定"""
        # Need fileが存在する場合は最優先
        for sheet_name, info in sheets_info.items():
            if info.get("detected_type") == "need_file":
                return sheet_name
        
        # 次に勤務表形式のシート
        for sheet_name, info in sheets_info.items():
            if info.get("detected_type") == "daily_schedule":
                return sheet_name
        
        return None


class DataQualityChecker:
    """データ品質検証システム"""
    
    def __init__(self):
        self.slot_detector = SlotIntervalDetector()
        self.date_validator = DateRangeValidator()
        self.staff_validator = StaffIntegrityValidator()
    
    def evaluate(self, excel_path: Path) -> QualityAssessmentResult:
        """総合的な品質評価"""
        result = QualityAssessmentResult()
        
        try:
            # ファイル形式チェック
            result.file_format_score = self._check_file_format(excel_path)
            
            # Excel読み込み
            excel_file = pd.ExcelFile(excel_path)
            
            # 構造分析
            result.structure_score = self._analyze_structure(excel_file)
            
            # 主要シート特定
            primary_sheet = self._find_primary_sheet(excel_file)
            if not primary_sheet:
                result.issues.append("主要データシートが特定できません")
                return result
            
            # 主要データ読み込み
            df = pd.read_excel(excel_path, sheet_name=primary_sheet)
            
            # 各種品質チェック
            result.date_range_score, result.detected_date_range, result.missing_dates = self._check_date_range(df)
            result.staff_integrity_score, result.staff_count, result.duplicate_staff_names = self._check_staff_integrity(df)
            result.shift_code_score, result.detected_slot_interval = self._check_shift_codes(df)
            result.completeness_score = self._check_completeness(df)
            
            # 総合スコア計算
            result.overall_score = self._calculate_overall_score(result)
            
            # 推奨分析手法決定
            result.recommended_analysis_method, result.confidence_level = self._recommend_analysis_method(result)
            
            # 改善提案生成
            result.recommendations = self._generate_recommendations(result)
            
            analysis_logger.info(f"[QUALITY] 品質評価完了: {result.overall_score:.1f}/100点")
            
        except Exception as e:
            log.error(f"品質評価エラー: {e}")
            result.issues.append(f"品質評価エラー: {e}")
        
        return result
    
    def _check_file_format(self, excel_path: Path) -> float:
        """ファイル形式チェック"""
        try:
            if not excel_path.exists():
                return 0.0
            if excel_path.suffix.lower() not in ['.xlsx', '.xls']:
                return QUALITY_PARTIAL_EXCEL_SCORE
            
            # ファイルサイズチェック
            file_size = excel_path.stat().st_size
            if file_size == 0:
                return 0.0
            elif file_size > QUALITY_LARGE_FILE_SIZE:
                return QUALITY_LARGE_FILE_SCORE
            
            return QUALITY_SCORE_MAX
        except Exception:
            return 0.0
    
    def _analyze_structure(self, excel_file: pd.ExcelFile) -> float:
        """構造分析"""
        try:
            sheet_count = len(excel_file.sheet_names)
            if sheet_count == 0:
                return 0.0
            elif sheet_count >= 2:  # 複数シートある場合は良い
                return QUALITY_SCORE_MAX
            else:
                return QUALITY_SINGLE_SHEET_SCORE  # 単一シートでも使用可能
        except Exception:
            return 0.0
    
    def _find_primary_sheet(self, excel_file: pd.ExcelFile) -> Optional[str]:
        """主要シート特定"""
        # Need fileを最優先
        for sheet_name in excel_file.sheet_names:
            if "Need" in sheet_name or "need" in sheet_name:
                return sheet_name
        
        # 最初のシートを使用
        return excel_file.sheet_names[0] if excel_file.sheet_names else None
    
    def _check_date_range(self, df: DataFrame) -> Tuple[float, Optional[Tuple[datetime, datetime]], List[str]]:
        """日付範囲チェック"""
        try:
            date_columns = []
            dates = []
            
            for col in df.columns:
                if self._is_date_column(col):
                    date_columns.append(col)
                    parsed_date = self._parse_date_column(col)
                    if parsed_date:
                        dates.append(parsed_date)
            
            if not dates:
                return 0.0, None, ["日付列が検出されませんでした"]
            
            dates.sort()
            date_range = (dates[0], dates[-1])
            
            # 連続性チェック
            expected_dates = []
            current_date = dates[0]
            while current_date <= dates[-1]:
                expected_dates.append(current_date)
                current_date += timedelta(days=1)
            
            missing_dates = []
            for expected in expected_dates:
                if expected not in dates:
                    missing_dates.append(expected.strftime("%Y-%m-%d"))
            
            # スコア計算
            completeness_ratio = (len(dates) - len(missing_dates)) / len(expected_dates)
            score = completeness_ratio * 100
            
            return score, date_range, missing_dates
            
        except Exception as e:
            log.error(f"日付範囲チェックでエラー: {e}")
            return 0.0, None, [f"日付範囲チェックエラー: {e}"]
    
    def _check_staff_integrity(self, df: DataFrame) -> Tuple[float, int, List[str]]:
        """スタッフデータ整合性チェック"""
        try:
            if 'staff' not in df.columns:
                return QUALITY_STAFF_MISSING_SCORE, 0, ["staff列が見つかりません"]
            
            staff_series = df['staff'].dropna()
            unique_staff = staff_series.unique()
            staff_count = len(unique_staff)
            
            # 重複名検出
            staff_counts = staff_series.value_counts()
            duplicates = staff_counts[staff_counts > 1].index.tolist()
            
            # 無効な名前検出
            invalid_patterns = ['×', 'X', 'x', '休', '欠', 'OFF', '-', '−', '―']
            valid_staff = []
            for staff in unique_staff:
                if pd.notna(staff) and str(staff).strip() not in invalid_patterns:
                    valid_staff.append(staff)
            
            valid_ratio = len(valid_staff) / len(unique_staff) if unique_staff.size > 0 else 0
            score = valid_ratio * 100
            
            return score, len(valid_staff), duplicates
            
        except Exception as e:
            return 0.0, 0, [f"スタッフ整合性チェックエラー: {e}"]
    
    def _check_shift_codes(self, df: DataFrame) -> Tuple[float, Optional[int]]:
        """勤務コードチェック"""
        try:
            # 時間らしい列を探す
            time_columns = []
            for col in df.columns:
                col_str = str(col)
                if ':' in col_str or any(t in col_str for t in ['時', 'H', 'h']):
                    time_columns.append(col)
            
            if not time_columns:
                return 50.0, None
            
            # スロット間隔検出
            detected_interval = self.slot_detector.detect_interval(time_columns)
            
            score = 90.0 if detected_interval else 70.0
            return score, detected_interval
            
        except Exception as e:
            return 0.0, None
    
    def _check_completeness(self, df: DataFrame) -> float:
        """データ完全性チェック"""
        try:
            total_cells = df.size
            non_null_cells = df.count().sum()
            completeness_ratio = non_null_cells / total_cells if total_cells > 0 else 0
            return completeness_ratio * 100
        except Exception:
            return 0.0
    
    def _calculate_overall_score(self, result: QualityAssessmentResult) -> float:
        """総合スコア計算"""
        weighted_score = (
            result.file_format_score * QUALITY_WEIGHTS['file_format'] +
            result.structure_score * QUALITY_WEIGHTS['structure'] +
            result.date_range_score * QUALITY_WEIGHTS['date_range'] +
            result.staff_integrity_score * QUALITY_WEIGHTS['staff_integrity'] +
            result.shift_code_score * QUALITY_WEIGHTS['shift_code'] +
            result.completeness_score * QUALITY_WEIGHTS['completeness']
        )
        
        return round(weighted_score, 1)
    
    def _recommend_analysis_method(self, result: QualityAssessmentResult) -> Tuple[str, str]:
        """推奨分析手法決定"""
        if result.overall_score >= 85:
            return "need_based", "high"
        elif result.overall_score >= 70:
            return "time_axis", "medium"
        else:
            return "proportional", "low"
    
    def _generate_recommendations(self, result: QualityAssessmentResult) -> List[str]:
        """改善提案生成"""
        recommendations = []
        
        if result.overall_score < 70:
            recommendations.append("データ品質が低いため、データクレンジングを実施してください")
        
        if result.duplicate_staff_names:
            recommendations.append(f"重複するスタッフ名があります: {', '.join(result.duplicate_staff_names[:3])}")
        
        if result.missing_dates:
            recommendations.append(f"欠損日付があります: {len(result.missing_dates)}日")
        
        if result.detected_slot_interval:
            recommendations.append(f"検出されたスロット間隔: {result.detected_slot_interval}分")
        
        return recommendations
    
    def _is_date_column(self, col: Any) -> bool:
        """日付列判定"""
        col_str = str(col)
        return bool(re.search(r'\d{1,2}[/-]\d{1,2}', col_str))
    
    def _parse_date_column(self, col: Any) -> Optional[datetime]:
        """日付列パース"""
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


class SlotIntervalDetector:
    """スロット間隔検出システム"""
    
    def detect_interval(self, time_columns: List[str]) -> Optional[int]:
        """時間スロット間隔を自動検出"""
        try:
            times = []
            for col in time_columns:
                time_match = re.search(r'(\d{1,2}):(\d{2})', str(col))
                if time_match:
                    hour, minute = map(int, time_match.groups())
                    times.append(hour * 60 + minute)
            
            if len(times) < 2:
                return None
            
            times.sort()
            intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
            
            # 最も頻出する間隔
            from collections import Counter
            interval_counts = Counter(intervals)
            most_common_interval = interval_counts.most_common(1)[0][0]
            
            # 15, 30, 60分のいずれかに正規化
            if most_common_interval <= 20:
                return 15
            elif most_common_interval <= 45:
                return 30
            else:
                return 60
                
        except Exception as e:
            log.error(f"スロット間隔検出エラー: {e}")
            return None


class DateRangeValidator:
    """日付範囲バリデーター"""
    
    def validate_continuity(self, dates: List[datetime]) -> Tuple[bool, List[datetime]]:
        """日付の連続性を検証"""
        if not dates:
            return False, []
        
        dates.sort()
        missing_dates = []
        
        current_date = dates[0]
        for expected_date in pd.date_range(dates[0], dates[-1], freq='D'):
            if expected_date.to_pydatetime() not in dates:
                missing_dates.append(expected_date.to_pydatetime())
        
        is_continuous = len(missing_dates) == 0
        return is_continuous, missing_dates


class StaffIntegrityValidator:
    """スタッフデータ整合性バリデーター"""
    
    def __init__(self):
        self.rest_patterns = [
            '×', 'X', 'x', '休', '休み', '休暇', '欠', '欠勤',
            'OFF', 'off', 'Off', '-', '−', '―', 'nan', 'NaN', 'null',
            '有', '有休', '特', '特休', '代', '代休', '振', '振休'
        ]
    
    def validate_staff_names(self, staff_series: pd.Series) -> Dict[str, Any]:
        """スタッフ名の妥当性検証"""
        validation_result = {
            "total_entries": len(staff_series),
            "unique_staff": 0,
            "duplicate_names": [],
            "invalid_entries": [],
            "rest_entries": 0,
            "valid_staff_ratio": 0.0
        }
        
        # 非NULL値のみ処理
        staff_clean = staff_series.dropna()
        
        # 重複検出
        staff_counts = staff_clean.value_counts()
        duplicates = staff_counts[staff_counts > 1].index.tolist()
        validation_result["duplicate_names"] = duplicates
        
        # 休暇パターン除外
        valid_staff = []
        rest_count = 0
        
        for staff in staff_clean:
            staff_str = str(staff).strip()
            if staff_str in self.rest_patterns:
                rest_count += 1
            elif staff_str and staff_str not in ['', ' ', '　']:
                valid_staff.append(staff)
        
        validation_result["unique_staff"] = len(set(valid_staff))
        validation_result["rest_entries"] = rest_count
        validation_result["valid_staff_ratio"] = len(valid_staff) / len(staff_clean) if len(staff_clean) > 0 else 0.0
        
        return validation_result


class QualityAssuredDataset:
    """品質保証付きデータセット"""
    
    def __init__(
        self, 
        data: DataFrame, 
        quality_result: QualityAssessmentResult,
        schema: Dict[str, Any],
        lineage: DataLineageTracker
    ):
        self.data = data
        self.quality_result = quality_result
        self.schema = schema
        self.lineage = lineage
        self.metadata = self._generate_metadata()
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """メタデータ生成"""
        return {
            "processing_timestamp": datetime.now().isoformat(),
            "data_shape": self.data.shape,
            "quality_score": self.quality_result.overall_score,
            "recommended_method": self.quality_result.recommended_analysis_method,
            "confidence_level": self.quality_result.confidence_level,
            "detected_slot_interval": self.quality_result.detected_slot_interval,
            "staff_count": self.quality_result.staff_count
        }
    
    def get_quality_report(self) -> str:
        """品質レポート生成"""
        report = f"""
🔍 データ品質レポート
{'='*50}
📊 総合スコア: {self.quality_result.overall_score:.1f}/100点

📋 詳細評価:
├─ ファイル形式: {self.quality_result.file_format_score:.1f}点
├─ データ構造: {self.quality_result.structure_score:.1f}点  
├─ 日付範囲: {self.quality_result.date_range_score:.1f}点
├─ スタッフ整合性: {self.quality_result.staff_integrity_score:.1f}点
├─ 勤務コード: {self.quality_result.shift_code_score:.1f}点
└─ データ完全性: {self.quality_result.completeness_score:.1f}点

🎯 推奨分析手法: {self.quality_result.recommended_analysis_method}
📈 信頼度: {self.quality_result.confidence_level}

⚠️  検出された問題: {len(self.quality_result.issues)}件
💡 改善提案: {len(self.quality_result.recommendations)}件
"""
        return report


class TruthAssuredDataIngestion:
    """Truth-Driven統合データ入稿システム"""
    
    def __init__(self):
        self.quality_checker = DataQualityChecker()
        self.schema_inferrer = DynamicSchemaInferrer()
        self.lineage_tracker = DataLineageTracker()
    
    def ingest_with_quality_assurance(self, excel_path: Path) -> QualityAssuredDataset:
        """品質保証付きデータ入稿"""
        log.info(f"[INGESTION] 統合データ入稿開始: {excel_path.name}")
        
        # 系譜追跡初期化
        self.lineage_tracker.tracking_id = f"INGEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.lineage_tracker.source_file = str(excel_path)
        
        try:
            # Step 1: 品質評価
            self.lineage_tracker.track_step("quality_assessment", {"stage": "start"})
            quality_result = self.quality_checker.evaluate(excel_path)
            self.lineage_tracker.track_step("quality_assessment", {
                "score": quality_result.overall_score,
                "recommended_method": quality_result.recommended_analysis_method
            })
            
            # Step 2: スキーマ推論
            self.lineage_tracker.track_step("schema_inference", {"stage": "start"})
            schema = self.schema_inferrer.infer_structure(excel_path)
            self.lineage_tracker.track_step("schema_inference", {"schema": schema})
            
            # Step 3: データ読み込み
            self.lineage_tracker.track_step("data_loading", {"stage": "start"})
            primary_sheet = schema.get("primary_data_sheet")
            
            if not primary_sheet:
                raise ValueError("主要データシートが特定できませんでした")
            
            data = pd.read_excel(excel_path, sheet_name=primary_sheet)
            self.lineage_tracker.track_step("data_loading", {
                "sheet": primary_sheet,
                "shape": data.shape
            })
            
            # Step 4: 品質保証データセット作成
            dataset = QualityAssuredDataset(data, quality_result, schema, self.lineage_tracker)
            
            # レポート出力
            log.info(f"[INGESTION] 入稿完了: スコア{quality_result.overall_score:.1f}点")
            analysis_logger.info(dataset.get_quality_report())
            
            return dataset
            
        except Exception as e:
            log.error(f"[INGESTION] データ入稿エラー: {e}")
            self.lineage_tracker.track_step("error", {"error": str(e)})
            raise
    
    def save_ingestion_report(self, dataset: QualityAssuredDataset, output_dir: Path) -> Path:
        """入稿レポート保存"""
        report_path = output_dir / f"ingestion_report_{dataset.lineage.tracking_id}.json"
        
        report_data = {
            "ingestion_summary": dataset.metadata,
            "quality_assessment": {
                "overall_score": dataset.quality_result.overall_score,
                "detailed_scores": {
                    "file_format": dataset.quality_result.file_format_score,
                    "structure": dataset.quality_result.structure_score,
                    "date_range": dataset.quality_result.date_range_score,
                    "staff_integrity": dataset.quality_result.staff_integrity_score,
                    "shift_code": dataset.quality_result.shift_code_score,
                    "completeness": dataset.quality_result.completeness_score
                },
                "issues": dataset.quality_result.issues,
                "warnings": dataset.quality_result.warnings,
                "recommendations": dataset.quality_result.recommendations
            },
            "schema_inference": dataset.schema,
            "data_lineage": dataset.lineage.generate_lineage_report()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        log.info(f"[INGESTION] レポート保存: {report_path}")
        return report_path


# 便利関数
def ingest_excel_with_quality_assurance(excel_path: Path) -> QualityAssuredDataset:
    """品質保証付きExcel入稿（便利関数）"""
    ingestion_system = TruthAssuredDataIngestion()
    return ingestion_system.ingest_with_quality_assurance(excel_path)


# Export
__all__ = [
    "QualityAssessmentResult",
    "QualityAssuredDataset", 
    "TruthAssuredDataIngestion",
    "ingest_excel_with_quality_assurance"
]