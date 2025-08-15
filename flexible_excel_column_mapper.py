#!/usr/bin/env python
"""
柔軟なExcel列名マッピングシステム

多様なExcelファイル形式と列名規則に対応
自動検出と智的マッピングによる堅牢なデータ取り込み
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import Dict, List, Tuple, Optional, Union, Set
from pathlib import Path
import difflib
from collections import defaultdict
import unicodedata

log = logging.getLogger(__name__)

class FlexibleExcelColumnMapper:
    """柔軟なExcel列名マッピングクラス"""
    
    def __init__(self):
        """初期化 - 標準的な列名マッピング辞書を設定"""
        
        # 基本的な列名マッピング辞書
        self.CORE_COLUMN_MAPPING = {
            # スタッフ関連
            'staff': ['氏名', '名前', 'staff', 'name', '従業員', 'member', '職員', 'スタッフ', '従業員名'],
            
            # 職種関連
            'role': ['職種', '部署', '役職', 'role', 'position', 'department', '職位', '担当', '業務'],
            
            # 雇用形態
            'employment': ['雇用形態', '雇用区分', 'employment', 'type', '契約', '勤務形態', '雇用タイプ'],
            
            # 日時関連
            'datetime': ['日時', '時刻', 'datetime', 'timestamp', '時間', 'time', 'ds', 'date_time'],
            'date': ['日付', 'date', '年月日', '勤務日'],
            'time': ['時間', 'time', '時刻', '開始時刻', 'start_time'],
            
            # シフト関連
            'shift_start': ['開始', 'start', '開始時刻', 'start_time', '勤務開始'],
            'shift_end': ['終了', 'end', '終了時刻', 'end_time', '勤務終了'],
            'shift_hours': ['時間数', 'hours', '勤務時間', 'work_hours', 'duration'],
            
            # その他
            'remarks': ['備考', 'remarks', 'note', 'comment', 'メモ', '注記'],
            'status': ['状態', 'status', 'ステータス', '勤務状況']
        }
        
        # 日付パターンの拡張辞書
        self.DATE_PATTERNS = [
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD, YYYY-MM-DD
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # MM/DD/YYYY, DD/MM/YYYY
            r'\d{1,2}[/-]\d{1,2}',           # MM/DD, DD/MM
            r'\d{8}',                        # YYYYMMDD
            r'\d{4}年\d{1,2}月\d{1,2}日',      # YYYY年MM月DD日
            r'\d{1,2}月\d{1,2}日'              # MM月DD日
        ]
        
        # 時間パターン
        self.TIME_PATTERNS = [
            r'\d{1,2}:\d{2}',               # HH:MM
            r'\d{1,2}時\d{2}分',             # HH時MM分
            r'\d{1,2}:\d{2}:\d{2}'          # HH:MM:SS
        ]
        
        self.mapping_log = []
        self.confidence_scores = {}
        
    def map_excel_columns(
        self, 
        df: pd.DataFrame, 
        file_path: Optional[Path] = None,
        header_row: Optional[int] = None,
        auto_detect_header: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, any]]:
        """
        Excel列名の柔軟マッピング
        
        Args:
            df: 元DataFrame
            file_path: Excelファイルパス（分析用）
            header_row: ヘッダー行番号（Noneの場合は自動検出）
            auto_detect_header: ヘッダー行の自動検出を行うか
            
        Returns:
            tuple: (マッピング済みDataFrame, マッピング情報)
        """
        log.info(f"[EXCEL_MAPPING] 列名マッピング開始: {df.shape}")
        
        mapping_info = {
            'original_columns': list(df.columns),
            'mapped_columns': {},
            'unmapped_columns': [],
            'confidence_scores': {},
            'header_detection': {},
            'data_quality': {}
        }
        
        try:
            # 1. ヘッダー行の自動検出
            if auto_detect_header:
                detected_header_row = self._detect_header_row(df)
                if detected_header_row != 0:
                    df = self._adjust_header_row(df, detected_header_row)
                    mapping_info['header_detection'] = {
                        'auto_detected': True,
                        'header_row': detected_header_row,
                        'adjustment_applied': True
                    }
            
            # 2. 列名の正規化
            normalized_columns = self._normalize_column_names(df.columns)
            
            # 3. 智的列マッピング
            column_mapping = self._perform_intelligent_mapping(df.columns, normalized_columns)
            mapping_info['mapped_columns'] = column_mapping
            mapping_info['confidence_scores'] = self.confidence_scores
            
            # 4. DataFrame列名の更新
            mapped_df = self._apply_column_mapping(df, column_mapping)
            
            # 5. マッピングされなかった列の識別
            unmapped = self._identify_unmapped_columns(df.columns, column_mapping)
            mapping_info['unmapped_columns'] = unmapped
            
            # 6. データ品質評価
            quality_assessment = self._assess_data_quality(mapped_df, mapping_info)
            mapping_info['data_quality'] = quality_assessment
            
            log.info(f"[EXCEL_MAPPING] マッピング完了: {len(column_mapping)}列マッピング済み")
            
            return mapped_df, mapping_info
            
        except Exception as e:
            log.error(f"[EXCEL_MAPPING] マッピングエラー: {e}")
            raise ValueError(f"Excel列名マッピング失敗: {e}")
    
    def _detect_header_row(self, df: pd.DataFrame) -> int:
        """ヘッダー行の自動検出"""
        
        # 最初の5行を分析してヘッダー行を特定
        header_candidates = []
        
        for row_idx in range(min(5, len(df))):
            row_data = df.iloc[row_idx]
            
            # ヘッダー行の特徴を評価
            score = 0
            
            # 1. 非数値データの割合（ヘッダーは通常テキスト）
            non_numeric_count = sum(1 for val in row_data if not self._is_numeric_value(val))
            non_numeric_ratio = non_numeric_count / len(row_data) if len(row_data) > 0 else 0
            score += non_numeric_ratio * 40
            
            # 2. 既知の列名パターンとの一致
            known_patterns_match = 0
            for val in row_data:
                if self._matches_known_column_pattern(str(val)):
                    known_patterns_match += 1
            
            if len(row_data) > 0:
                pattern_match_ratio = known_patterns_match / len(row_data)
                score += pattern_match_ratio * 50
            
            # 3. 重複値の少なさ（ヘッダーは通常ユニーク）
            unique_ratio = len(set(row_data.dropna())) / len(row_data.dropna()) if len(row_data.dropna()) > 0 else 0
            score += unique_ratio * 10
            
            header_candidates.append({'row': row_idx, 'score': score})
        
        # 最高スコアの行をヘッダーとして選択
        best_candidate = max(header_candidates, key=lambda x: x['score'])
        detected_row = best_candidate['row']
        
        log.info(f"[HEADER_DETECT] ヘッダー行検出: 行{detected_row} (スコア: {best_candidate['score']:.1f})")
        
        return detected_row
    
    def _is_numeric_value(self, value) -> bool:
        """値が数値かどうかの判定"""
        if pd.isna(value):
            return False
        
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _matches_known_column_pattern(self, value: str) -> bool:
        """既知の列名パターンとの一致判定"""
        value_normalized = self._normalize_text(value)
        
        # すべての既知パターンをチェック
        for standard_name, variations in self.CORE_COLUMN_MAPPING.items():
            for variation in variations:
                if self._normalize_text(variation) in value_normalized:
                    return True
        
        # 日付パターンのチェック
        for pattern in self.DATE_PATTERNS:
            if re.search(pattern, value):
                return True
        
        return False
    
    def _adjust_header_row(self, df: pd.DataFrame, header_row: int) -> pd.DataFrame:
        """ヘッダー行の調整"""
        if header_row == 0:
            return df  # 既に正しい位置
        
        # 指定行を新しい列名として設定
        new_columns = df.iloc[header_row].values
        adjusted_df = df.iloc[header_row + 1:].copy()
        adjusted_df.columns = new_columns
        
        # インデックスをリセット
        adjusted_df = adjusted_df.reset_index(drop=True)
        
        return adjusted_df
    
    def _normalize_column_names(self, columns: pd.Index) -> List[str]:
        """列名の正規化"""
        normalized = []
        
        for col in columns:
            normalized_col = self._normalize_text(str(col))
            normalized.append(normalized_col)
        
        return normalized
    
    def _normalize_text(self, text: str) -> str:
        """テキストの正規化"""
        if not isinstance(text, str):
            text = str(text)
        
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 全角・半角変換
        text = text.replace('　', ' ')  # 全角スペースを半角に
        
        # 大文字小文字統一
        text = text.lower()
        
        # 不要な文字除去
        text = re.sub(r'[^\w\s]', '', text)
        
        # 連続スペースを単一スペースに
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _perform_intelligent_mapping(self, original_columns: pd.Index, normalized_columns: List[str]) -> Dict[str, str]:
        """智的列マッピングの実行"""
        
        column_mapping = {}
        self.confidence_scores = {}
        
        for i, (original_col, normalized_col) in enumerate(zip(original_columns, normalized_columns)):
            
            best_match = None
            best_score = 0
            
            # 各標準列名との類似度を計算
            for standard_name, variations in self.CORE_COLUMN_MAPPING.items():
                
                for variation in variations:
                    normalized_variation = self._normalize_text(variation)
                    
                    # 複数の類似度計算手法を使用
                    similarity_score = self._calculate_similarity(normalized_col, normalized_variation)
                    
                    if similarity_score > best_score and similarity_score > 0.6:  # 閾値設定
                        best_match = standard_name
                        best_score = similarity_score
            
            # 日付列の特別処理
            if not best_match:
                date_score = self._detect_date_column(str(original_col))
                if date_score > 0.7:
                    best_match = 'date'
                    best_score = date_score
            
            # マッピング結果の記録
            if best_match:
                column_mapping[original_col] = best_match
                self.confidence_scores[original_col] = best_score
                
                log.info(f"[MAPPING] {original_col} → {best_match} (信頼度: {best_score:.2f})")
        
        return column_mapping
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度の計算"""
        
        # 完全一致
        if text1 == text2:
            return 1.0
        
        # 部分一致
        if text1 in text2 or text2 in text1:
            shorter = min(len(text1), len(text2))
            longer = max(len(text1), len(text2))
            return shorter / longer
        
        # レーベンシュタイン距離ベース類似度
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        # 共通部分文字列の追加評価
        common_substrings = self._find_common_substrings(text1, text2)
        if common_substrings:
            substring_bonus = len(max(common_substrings, key=len)) / max(len(text1), len(text2))
            similarity += substring_bonus * 0.3
        
        return min(1.0, similarity)
    
    def _find_common_substrings(self, text1: str, text2: str) -> List[str]:
        """共通部分文字列の検出"""
        common = []
        
        for i in range(len(text1)):
            for j in range(i + 2, len(text1) + 1):  # 最低2文字以上
                substring = text1[i:j]
                if substring in text2:
                    common.append(substring)
        
        return common
    
    def _detect_date_column(self, column_name: str) -> float:
        """日付列の検出"""
        
        # 日付関連キーワードの存在確認
        date_keywords = ['日付', 'date', '年月日', '時', '月', '日', '年']
        
        normalized_col = self._normalize_text(column_name)
        keyword_matches = sum(1 for keyword in date_keywords if keyword in normalized_col)
        
        # 日付パターンの存在確認
        pattern_matches = sum(1 for pattern in self.DATE_PATTERNS if re.search(pattern, column_name))
        
        # スコア計算
        keyword_score = min(1.0, keyword_matches / len(date_keywords))
        pattern_score = min(1.0, pattern_matches / len(self.DATE_PATTERNS))
        
        return (keyword_score + pattern_score) / 2
    
    def _apply_column_mapping(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """列マッピングの適用"""
        
        mapped_df = df.copy()
        
        # マッピング辞書に基づいて列名を変更
        rename_dict = {}
        for original_col, mapped_col in column_mapping.items():
            rename_dict[original_col] = mapped_col
        
        mapped_df = mapped_df.rename(columns=rename_dict)
        
        return mapped_df
    
    def _identify_unmapped_columns(self, original_columns: pd.Index, column_mapping: Dict[str, str]) -> List[str]:
        """マッピングされなかった列の識別"""
        
        mapped_columns = set(column_mapping.keys())
        unmapped = [col for col in original_columns if col not in mapped_columns]
        
        return unmapped
    
    def _assess_data_quality(self, mapped_df: pd.DataFrame, mapping_info: Dict) -> Dict[str, any]:
        """データ品質の評価"""
        
        quality = {
            'mapping_coverage': 0.0,
            'critical_columns_present': [],
            'critical_columns_missing': [],
            'data_type_consistency': {},
            'sample_data_validation': {}
        }
        
        # マッピングカバレッジ
        total_columns = len(mapping_info['original_columns'])
        mapped_columns = len(mapping_info['mapped_columns'])
        quality['mapping_coverage'] = mapped_columns / total_columns if total_columns > 0 else 0
        
        # 重要列の存在確認
        critical_columns = ['staff', 'role', 'date', 'datetime']
        for col in critical_columns:
            if col in mapped_df.columns:
                quality['critical_columns_present'].append(col)
            else:
                quality['critical_columns_missing'].append(col)
        
        # データ型一貫性チェック
        for col in mapped_df.columns:
            if col in critical_columns:
                sample_data = mapped_df[col].dropna().head(10)
                consistency_score = self._check_data_type_consistency(sample_data, col)
                quality['data_type_consistency'][col] = consistency_score
        
        return quality
    
    def _check_data_type_consistency(self, sample_data: pd.Series, expected_type: str) -> float:
        """データ型一貫性のチェック"""
        
        if len(sample_data) == 0:
            return 0.0
        
        consistent_count = 0
        
        for value in sample_data:
            if expected_type == 'date':
                if self._is_date_like(value):
                    consistent_count += 1
            elif expected_type in ['staff', 'role']:
                if isinstance(value, str) and len(str(value).strip()) > 0:
                    consistent_count += 1
            else:
                consistent_count += 1  # その他の型は暫定的にOK
        
        return consistent_count / len(sample_data)
    
    def _is_date_like(self, value) -> bool:
        """日付らしい値かどうかの判定"""
        
        if pd.isna(value):
            return False
        
        try:
            pd.to_datetime(value)
            return True
        except (ValueError, TypeError):
            return False

def map_excel_file_columns(
    file_path: Union[str, Path], 
    sheet_name: Optional[str] = None,
    header_row: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, any]]:
    """
    Excelファイルの列マッピング（便利関数）
    
    Args:
        file_path: Excelファイルパス
        sheet_name: シート名（Noneの場合は最初のシート）
        header_row: ヘッダー行（Noneの場合は自動検出）
        
    Returns:
        tuple: (マッピング済みDataFrame, マッピング情報)
    """
    
    # Excelファイルの読み込み
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
    except Exception as e:
        log.error(f"Excelファイル読み込みエラー: {e}")
        raise
    
    # 列マッピングの実行
    mapper = FlexibleExcelColumnMapper()
    return mapper.map_excel_columns(df, file_path=Path(file_path), header_row=header_row)

def generate_column_mapping_report(mapping_info: Dict[str, any], output_file: Optional[Path] = None) -> str:
    """
    列マッピングレポートの生成
    
    Args:
        mapping_info: マッピング情報
        output_file: 出力ファイルパス
        
    Returns:
        str: レポート内容
    """
    
    report_lines = [
        "=== Excel列名マッピングレポート ===",
        "",
        f"元の列数: {len(mapping_info['original_columns'])}",
        f"マッピング済み列数: {len(mapping_info['mapped_columns'])}",
        f"カバレッジ: {mapping_info['data_quality']['mapping_coverage']*100:.1f}%",
        ""
    ]
    
    # マッピング結果
    if mapping_info['mapped_columns']:
        report_lines.append("【マッピング結果】")
        for original, mapped in mapping_info['mapped_columns'].items():
            confidence = mapping_info['confidence_scores'].get(original, 0)
            report_lines.append(f"  {original} → {mapped} (信頼度: {confidence:.2f})")
        report_lines.append("")
    
    # マッピングされなかった列
    if mapping_info['unmapped_columns']:
        report_lines.append("【未マッピング列】")
        for col in mapping_info['unmapped_columns']:
            report_lines.append(f"  {col}")
        report_lines.append("")
    
    # データ品質
    quality = mapping_info['data_quality']
    report_lines.extend([
        "【データ品質評価】",
        f"重要列存在: {', '.join(quality['critical_columns_present'])}",
        f"重要列欠損: {', '.join(quality['critical_columns_missing'])}",
        ""
    ])
    
    report_content = "\n".join(report_lines)
    
    # ファイル出力
    if output_file:
        output_file.write_text(report_content, encoding='utf-8')
        log.info(f"列マッピングレポート出力: {output_file}")
    
    return report_content

# 使用例とテスト
def test_flexible_excel_column_mapping():
    """柔軟なExcel列マッピングのテスト"""
    
    # テストデータ作成（様々な列名形式）
    test_data = {
        '氏名': ['田中太郎', '佐藤花子', '山田次郎'],
        '職種': ['介護', '看護', '事務'],
        '雇用形態': ['正社員', 'パート', '正社員'],
        '2025/01/01': [2, 1, 0],
        '2025/01/02': [3, 2, 1],
        '備考': ['', '夜勤', '']
    }
    
    test_df = pd.DataFrame(test_data)
    
    print("=== 柔軟なExcel列マッピングテスト ===")
    print(f"元データ:")
    print(test_df)
    print(f"\n元の列名: {list(test_df.columns)}")
    
    # マッピング実行
    mapper = FlexibleExcelColumnMapper()
    mapped_df, mapping_info = mapper.map_excel_columns(test_df)
    
    print(f"\nマッピング後データ:")
    print(mapped_df)
    print(f"\nマッピング済み列名: {list(mapped_df.columns)}")
    
    # レポート生成
    report_content = generate_column_mapping_report(mapping_info)
    print(f"\n{report_content}")
    
    return mapped_df, mapping_info

if __name__ == "__main__":
    # テスト実行
    test_mapped_df, test_mapping_info = test_flexible_excel_column_mapping()
    print("\n柔軟なExcel列マッピングのテストが完了しました！")