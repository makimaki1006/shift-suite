#!/usr/bin/env python3
"""
データ読み込み・バリデーション改善モジュール
- 統一されたエラーハンドリング
- 詳細なデータ検証
- ユーザーフレンドリーなエラーメッセージ
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import zipfile
import base64
import io
import tempfile
import shutil
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)

# ===== エラー定義 =====

class ValidationErrorType(Enum):
    """データ検証エラーの種類"""
    FILE_NOT_FOUND = "file_not_found"
    FILE_EMPTY = "file_empty" 
    FILE_CORRUPT = "file_corrupt"
    INVALID_FORMAT = "invalid_format"
    MISSING_COLUMNS = "missing_columns"
    INVALID_DATA = "invalid_data"
    ENCODING_ERROR = "encoding_error"
    PERMISSION_ERROR = "permission_error"

@dataclass
class ValidationResult:
    """データ検証結果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    data_info: Dict[str, Any]
    file_info: Dict[str, Any]

# ===== データ検証ユーティリティ =====

class DataValidator:
    """統一データ検証クラス"""
    
    SUPPORTED_EXTENSIONS = {'.zip', '.xlsx', '.csv', '.parquet'}
    
    # 必須列定義
    REQUIRED_COLUMNS = {
        'shift_data': ['date', 'staff_name', 'role'],
        'shortage_data': ['time_slot', 'need', 'actual'],
        'fatigue_data': ['staff_name', 'date', 'score']
    }
    
    # データ型期待値
    COLUMN_TYPES = {
        'date': ['datetime64', 'object'],  # 日付は複数形式を許可
        'staff_name': ['object'],
        'role': ['object'],
        'need': ['int64', 'float64'],
        'actual': ['int64', 'float64'],
        'score': ['int64', 'float64']
    }
    
    @classmethod
    def validate_file_extension(cls, filename: str) -> ValidationResult:
        """ファイル拡張子の検証"""
        ext = Path(filename).suffix.lower()
        
        if ext not in cls.SUPPORTED_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                errors=[f"未サポートのファイル形式: {ext}。サポート形式: {', '.join(cls.SUPPORTED_EXTENSIONS)}"],
                warnings=[],
                data_info={},
                file_info={'extension': ext}
            )
        
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            data_info={},
            file_info={'extension': ext}
        )
    
    @classmethod
    def validate_file_size(cls, file_size: int, max_size_mb: int = 100) -> ValidationResult:
        """ファイルサイズの検証"""
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                errors=["ファイルが空です"],
                warnings=[],
                data_info={},
                file_info={'size_bytes': file_size}
            )
        
        if file_size > max_size_bytes:
            return ValidationResult(
                is_valid=False,
                errors=[f"ファイルサイズが大きすぎます: {file_size/1024/1024:.1f}MB (最大: {max_size_mb}MB)"],
                warnings=[],
                data_info={},
                file_info={'size_bytes': file_size}
            )
        
        warnings = []
        if file_size > max_size_bytes * 0.8:  # 80%を超えたら警告
            warnings.append(f"大きなファイルです: {file_size/1024/1024:.1f}MB。処理に時間がかかる可能性があります")
        
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=warnings,
            data_info={},
            file_info={'size_bytes': file_size, 'size_mb': file_size/1024/1024}
        )
    
    @classmethod
    def validate_dataframe_structure(cls, df: pd.DataFrame, data_type: str) -> ValidationResult:
        """DataFrameの構造検証"""
        errors = []
        warnings = []
        data_info = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict()
        }
        
        # 空のDataFrameチェック
        if df.empty:
            errors.append("データが空です")
            return ValidationResult(False, errors, warnings, data_info, {})
        
        # 必須列チェック
        if data_type in cls.REQUIRED_COLUMNS:
            required_cols = cls.REQUIRED_COLUMNS[data_type]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                errors.append(f"必須列が不足: {', '.join(missing_cols)}")
        
        # データ型チェック
        for col in df.columns:
            if col in cls.COLUMN_TYPES:
                expected_types = cls.COLUMN_TYPES[col] 
                actual_type = str(df[col].dtype)
                if not any(expected in actual_type for expected in expected_types):
                    warnings.append(f"列 '{col}' のデータ型が期待値と異なります: {actual_type}")
        
        # 欠損値チェック
        missing_counts = df.isnull().sum()
        if missing_counts.any():
            missing_info = missing_counts[missing_counts > 0].to_dict()
            warnings.append(f"欠損値を含む列: {missing_info}")
            data_info['missing_values'] = missing_info
        
        # 重複行チェック
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            warnings.append(f"重複行が{duplicate_count}件あります")
            data_info['duplicate_rows'] = duplicate_count
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data_info=data_info,
            file_info={}
        )

# ===== 改善されたデータ読み込み関数 =====

class SafeDataLoader:
    """安全なデータローダー"""
    
    def __init__(self, cache_size: int = 10):
        self.cache_size = cache_size
        
    @lru_cache(maxsize=10)
    def safe_read_csv(self, filepath: Union[str, Path], **kwargs) -> Tuple[pd.DataFrame, ValidationResult]:
        """CSV読み込み（検証付き）"""
        filepath = Path(filepath)
        
        try:
            # ファイル存在チェック
            if not filepath.exists():
                result = ValidationResult(
                    is_valid=False,
                    errors=[f"ファイルが見つかりません: {filepath}"],
                    warnings=[],
                    data_info={},
                    file_info={'path': str(filepath)}
                )
                return pd.DataFrame(), result
            
            # ファイルサイズチェック
            size_result = DataValidator.validate_file_size(filepath.stat().st_size)
            if not size_result.is_valid:
                return pd.DataFrame(), size_result
            
            # 拡張子チェック
            ext_result = DataValidator.validate_file_extension(filepath.name)
            if not ext_result.is_valid:
                return pd.DataFrame(), ext_result
            
            # データ読み込み（複数エンコーディング対応）
            encodings = ['utf-8', 'shift_jis', 'cp932', 'utf-8-sig']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding, **kwargs)
                    log.debug(f"CSV読み込み成功: {filepath} (エンコーディング: {encoding})")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    log.warning(f"CSV読み込みエラー ({encoding}): {e}")
                    continue
            
            if df is None:
                result = ValidationResult(
                    is_valid=False,
                    errors=["ファイルの読み込みに失敗しました。エンコーディングまたはファイル形式を確認してください"],
                    warnings=[],
                    data_info={},
                    file_info={'path': str(filepath), 'encodings_tried': encodings}
                )
                return pd.DataFrame(), result
            
            # データ構造検証
            validation_result = DataValidator.validate_dataframe_structure(df, 'general')
            validation_result.file_info.update(size_result.file_info)
            
            log.info(f"CSV読み込み完了: {filepath} (形状: {df.shape})")
            return df, validation_result
            
        except PermissionError:
            result = ValidationResult(
                is_valid=False,
                errors=[f"ファイルにアクセスできません（権限不足）: {filepath}"],
                warnings=[],
                data_info={},
                file_info={'path': str(filepath)}
            )
            return pd.DataFrame(), result
            
        except Exception as e:
            result = ValidationResult(
                is_valid=False,
                errors=[f"予期しないエラー: {str(e)}"],
                warnings=[],
                data_info={},
                file_info={'path': str(filepath), 'error_type': type(e).__name__}
            )
            return pd.DataFrame(), result
    
    @lru_cache(maxsize=10)
    def safe_read_parquet(self, filepath: Union[str, Path]) -> Tuple[pd.DataFrame, ValidationResult]:
        """Parquet読み込み（検証付き）"""
        filepath = Path(filepath)
        
        try:
            if not filepath.exists():
                result = ValidationResult(
                    is_valid=False,
                    errors=[f"ファイルが見つかりません: {filepath}"],
                    warnings=[],
                    data_info={},
                    file_info={'path': str(filepath)}
                )
                return pd.DataFrame(), result
            
            size_result = DataValidator.validate_file_size(filepath.stat().st_size)
            if not size_result.is_valid:
                return pd.DataFrame(), size_result
            
            df = pd.read_parquet(filepath)
            validation_result = DataValidator.validate_dataframe_structure(df, 'general')
            validation_result.file_info.update(size_result.file_info)
            
            log.info(f"Parquet読み込み完了: {filepath} (形状: {df.shape})")
            return df, validation_result
            
        except Exception as e:
            result = ValidationResult(
                is_valid=False,
                errors=[f"Parquetファイル読み込みエラー: {str(e)}"],
                warnings=[],
                data_info={},
                file_info={'path': str(filepath), 'error_type': type(e).__name__}
            )
            return pd.DataFrame(), result
    
    @lru_cache(maxsize=10)
    def safe_read_excel(self, filepath: Union[str, Path], sheet_name: Optional[str] = None) -> Tuple[pd.DataFrame, ValidationResult]:
        """Excel読み込み（検証付き）"""
        filepath = Path(filepath)
        
        try:
            if not filepath.exists():
                result = ValidationResult(
                    is_valid=False,
                    errors=[f"ファイルが見つかりません: {filepath}"],
                    warnings=[],
                    data_info={},
                    file_info={'path': str(filepath)}
                )
                return pd.DataFrame(), result
            
            size_result = DataValidator.validate_file_size(filepath.stat().st_size)
            if not size_result.is_valid:
                return pd.DataFrame(), size_result
            
            # シート名の処理
            if sheet_name:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
            else:
                # 最初のシートを読み込み
                df = pd.read_excel(filepath)
            
            validation_result = DataValidator.validate_dataframe_structure(df, 'general')
            validation_result.file_info.update(size_result.file_info)
            
            log.info(f"Excel読み込み完了: {filepath} (形状: {df.shape})")
            return df, validation_result
            
        except Exception as e:
            result = ValidationResult(
                is_valid=False,
                errors=[f"Excelファイル読み込みエラー: {str(e)}"],
                warnings=[],
                data_info={},
                file_info={'path': str(filepath), 'error_type': type(e).__name__}
            )
            return pd.DataFrame(), result
    
    def clear_cache(self):
        """キャッシュクリア"""
        self.safe_read_csv.cache_clear()
        self.safe_read_parquet.cache_clear()
        self.safe_read_excel.cache_clear()
        log.info("データローダーキャッシュをクリアしました")

# ===== 改善されたファイルアップロード処理 =====

class ImprovedFileUploader:
    """改善されたファイルアップローダー"""
    
    def __init__(self, temp_dir_prefix: str = "shift_suite_", max_file_size_mb: int = 100):
        self.temp_dir_prefix = temp_dir_prefix
        self.max_file_size_mb = max_file_size_mb
        self.data_loader = SafeDataLoader()
    
    def validate_upload_contents(self, contents: str, filename: str) -> ValidationResult:
        """アップロード内容の事前検証"""
        try:
            # base64デコード前の基本チェック
            if not contents or not filename:
                return ValidationResult(
                    is_valid=False,
                    errors=["ファイル内容または名前が空です"],
                    warnings=[],
                    data_info={},
                    file_info={}
                )
            
            # ファイル拡張子チェック
            ext_result = DataValidator.validate_file_extension(filename)
            if not ext_result.is_valid:
                return ext_result
            
            # base64デコードとサイズチェック
            try:
                content_type, content_string = contents.split(',', 1)
                decoded = base64.b64decode(content_string)
                file_size = len(decoded)
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"ファイル内容の解析に失敗: {str(e)}"],
                    warnings=[],
                    data_info={},
                    file_info={'filename': filename}
                )
            
            # サイズ検証
            size_result = DataValidator.validate_file_size(file_size, self.max_file_size_mb)
            if not size_result.is_valid:
                return size_result
            
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=size_result.warnings,
                data_info={'content_type': content_type},
                file_info={'filename': filename, 'size_bytes': file_size}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"ファイル検証中にエラー: {str(e)}"],
                warnings=[],
                data_info={},
                file_info={'filename': filename}
            )
    
    def process_zip_file(self, decoded_data: bytes, temp_dir: Path) -> Tuple[List[str], ValidationResult]:
        """ZIPファイル処理（改善版）"""
        try:
            with zipfile.ZipFile(io.BytesIO(decoded_data)) as zf:
                # ZIPファイル内容の事前チェック
                file_list = zf.namelist()
                if not file_list:
                    return [], ValidationResult(
                        is_valid=False,
                        errors=["ZIPファイルが空です"],
                        warnings=[],
                        data_info={},
                        file_info={}
                    )
                
                # 危険なパスの検出
                dangerous_paths = [f for f in file_list if '..' in f or f.startswith('/')]
                if dangerous_paths:
                    return [], ValidationResult(
                        is_valid=False,
                        errors=[f"危険なファイルパスが含まれています: {dangerous_paths[:3]}"],
                        warnings=[],
                        data_info={},
                        file_info={'dangerous_paths': dangerous_paths}
                    )
                
                # 展開
                zf.extractall(temp_dir)
                log.info(f"ZIP展開完了: {len(file_list)}ファイル")
                
            # シナリオ検出
            scenarios = [d.name for d in temp_dir.iterdir() if d.is_dir() and d.name.startswith('out_')]
            
            if not scenarios:
                return [], ValidationResult(
                    is_valid=False,
                    errors=['分析シナリオフォルダが見つかりません。\nZIPファイル内に "out_" で始まるフォルダが必要です。'],
                    warnings=[],
                    data_info={'extracted_files': file_list},
                    file_info={}
                )
            
            return scenarios, ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                data_info={'scenarios': scenarios, 'extracted_files': file_list},
                file_info={}
            )
            
        except zipfile.BadZipFile:
            return [], ValidationResult(
                is_valid=False,
                errors=["破損したZIPファイルです"],
                warnings=[],
                data_info={},
                file_info={}
            )
        except Exception as e:
            return [], ValidationResult(
                is_valid=False,
                errors=[f"ZIP処理エラー: {str(e)}"],
                warnings=[],
                data_info={},
                file_info={'error_type': type(e).__name__}
            )
    
    def create_single_file_scenario(self, decoded_data: bytes, filename: str, temp_dir: Path) -> Tuple[List[str], ValidationResult]:
        """単一ファイルからシナリオ作成"""
        try:
            # ファイル保存
            file_path = temp_dir / filename
            with open(file_path, 'wb') as f:
                f.write(decoded_data)
            
            # シナリオディレクトリ作成
            scenario_dir = temp_dir / "out_single_file"
            scenario_dir.mkdir(exist_ok=True)
            
            # ファイルコピー
            shutil.copy2(file_path, scenario_dir / filename)
            
            # データ検証
            file_ext = Path(filename).suffix.lower()
            if file_ext == '.csv':
                df, validation_result = self.data_loader.safe_read_csv(scenario_dir / filename)
            elif file_ext == '.xlsx':
                df, validation_result = self.data_loader.safe_read_excel(scenario_dir / filename)
            else:
                validation_result = ValidationResult(
                    is_valid=True,
                    errors=[],
                    warnings=[f"ファイル形式 {file_ext} の詳細検証はスキップされました"],
                    data_info={},
                    file_info={}
                )
            
            if not validation_result.is_valid:
                return [], validation_result
            
            scenarios = ["out_single_file"]
            log.info(f"単一ファイルシナリオ作成完了: {filename}")
            
            return scenarios, ValidationResult(
                is_valid=True,
                errors=[],
                warnings=validation_result.warnings,
                data_info={'scenarios': scenarios, 'data_shape': validation_result.data_info.get('shape')},
                file_info={'filename': filename}
            )
            
        except Exception as e:
            return [], ValidationResult(
                is_valid=False,
                errors=[f"単一ファイル処理エラー: {str(e)}"],
                warnings=[],
                data_info={},
                file_info={'filename': filename, 'error_type': type(e).__name__}
            )

# ===== グローバルインスタンス =====
safe_data_loader = SafeDataLoader()
improved_file_uploader = ImprovedFileUploader()