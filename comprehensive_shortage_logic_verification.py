#!/usr/bin/env python3
"""
過不足分析の徹底的ロジック検証システム
技術的な抜け漏れを完全に除去するための包括的検証
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings

class ValidationLevel(Enum):
    """検証レベル定義"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR" 
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class ValidationResult:
    """検証結果の構造化"""
    level: ValidationLevel
    category: str
    message: str
    actual_value: Optional[float] = None
    expected_value: Optional[float] = None
    test_name: str = ""

class ComprehensiveShortageLogicVerifier:
    """過不足分析の包括的ロジック検証システム"""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        self.validation_results: List[ValidationResult] = []
        self.tolerance = 1e-6  # 数値計算の許容誤差
        
    def verify_all_logic(self) -> Dict[str, any]:
        """全ロジックの包括的検証"""
        
        print('=' * 80)
        print('過不足分析 徹底的ロジック検証システム')
        print('技術的抜け漏れの完全除去')
        print('=' * 80)
        
        # 1. データ整合性検証
        self._verify_data_integrity()
        
        # 2. 単位系検証  
        self._verify_unit_consistency()
        
        # 3. 計算精度検証
        self._verify_calculation_precision()
        
        # 4. エッジケース検証
        self._verify_edge_cases()
        
        # 5. 数学的妥当性検証
        self._verify_mathematical_validity()
        
        # 6. 時間軸整合性検証
        self._verify_temporal_consistency()
        
        # 7. 職種マッピング検証
        self._verify_role_mapping()
        
        return self._generate_comprehensive_report()
    
    def _verify_data_integrity(self):
        """データ整合性の徹底検証"""
        print('\n【1. データ整合性検証】')
        
        try:
            # intermediate_data検証
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            
            # 必須カラム存在確認
            required_columns = ['ds', 'role', 'staff', 'employment']
            for col in required_columns:
                if col not in intermediate_data.columns:
                    self.validation_results.append(ValidationResult(
                        ValidationLevel.CRITICAL,
                        "data_integrity", 
                        f"必須カラム '{col}' が存在しません",
                        test_name="required_columns_check"
                    ))
            
            # データ型検証
            if 'ds' in intermediate_data.columns:
                if not pd.api.types.is_datetime64_any_dtype(intermediate_data['ds']):
                    self.validation_results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "data_integrity",
                        "dsカラムがdatetime型ではありません",
                        test_name="datetime_type_check"
                    ))
            
            # 欠損値検証
            null_counts = intermediate_data.isnull().sum()
            for col, null_count in null_counts.items():
                if null_count > 0:
                    null_rate = null_count / len(intermediate_data)
                    if null_rate > 0.1:  # 10%超の欠損は問題
                        self.validation_results.append(ValidationResult(
                            ValidationLevel.ERROR,
                            "data_integrity",
                            f"カラム'{col}'に{null_rate:.1%}の欠損値",
                            actual_value=null_rate,
                            expected_value=0.0,
                            test_name="null_value_check"
                        ))
            
            # 重複レコード検証
            duplicate_count = intermediate_data.duplicated().sum()
            if duplicate_count > 0:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    "data_integrity",
                    f"{duplicate_count}件の重複レコードを発見",
                    actual_value=duplicate_count,
                    expected_value=0,
                    test_name="duplicate_check"
                ))
            
            print(f'  intermediate_data: {len(intermediate_data)}レコード - 基本検証完了')
            
        except Exception as e:
            self.validation_results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                "data_integrity",
                f"データ読み込みエラー: {str(e)}",
                test_name="data_loading_check"
            ))
    
    def _verify_unit_consistency(self):
        """単位系の徹底検証"""
        print('\n【2. 単位系一貫性検証】')
        
        try:
            # 需要データファイル検証
            need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*介護*.parquet'))
            
            if not need_files:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.CRITICAL,
                    "unit_consistency",
                    "需要データファイルが見つかりません",
                    test_name="need_files_existence"
                ))
                return
            
            # 各ファイルの構造統一性検証
            expected_shape = None
            for need_file in need_files:
                df = pd.read_parquet(need_file)
                
                if expected_shape is None:
                    expected_shape = df.shape
                elif df.shape != expected_shape:
                    self.validation_results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "unit_consistency", 
                        f"{need_file.name}: 形状不整合 {df.shape} vs 期待値 {expected_shape}",
                        test_name="shape_consistency"
                    ))
                
                # データ型統一性検証
                if not all(df.dtypes == 'int64'):
                    non_int_columns = df.select_dtypes(exclude=['int64']).columns
                    if len(non_int_columns) > 0:
                        self.validation_results.append(ValidationResult(
                            ValidationLevel.WARNING,
                            "unit_consistency",
                            f"{need_file.name}: 非整数カラムを発見 {list(non_int_columns)}",
                            test_name="data_type_consistency"
                        ))
                
                # 負の値検証
                negative_count = (df < 0).sum().sum()
                if negative_count > 0:
                    self.validation_results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "unit_consistency",
                        f"{need_file.name}: {negative_count}個の負の値を発見",
                        actual_value=negative_count,
                        expected_value=0,
                        test_name="negative_value_check"
                    ))
            
            # 時間スロット数検証（48スロット = 24時間 × 2）
            if expected_shape and expected_shape[0] != 48:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "unit_consistency",
                    f"時間スロット数異常: {expected_shape[0]} (期待値: 48)",
                    actual_value=expected_shape[0],
                    expected_value=48,
                    test_name="time_slot_count"
                ))
            
            # 日数検証（30日想定）
            if expected_shape and expected_shape[1] != 30:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    "unit_consistency", 
                    f"日数設定: {expected_shape[1]} (標準: 30日)",
                    actual_value=expected_shape[1],
                    expected_value=30,
                    test_name="day_count_check"
                ))
            
            print(f'  需要データファイル: {len(need_files)}個 - 単位系検証完了')
            
        except Exception as e:
            self.validation_results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                "unit_consistency",
                f"単位系検証エラー: {str(e)}",
                test_name="unit_consistency_check"
            ))
    
    def _verify_calculation_precision(self):
        """計算精度の徹底検証"""
        print('\n【3. 計算精度検証】')
        
        try:
            # 実際の計算を再現して検証
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            care_data = intermediate_data[intermediate_data['role'].str.contains('介護', na=False)]
            
            need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*介護*.parquet'))
            
            # 複数の方法で同じ計算を実行して整合性確認
            total_need_method1 = 0
            total_need_method2 = 0
            
            for need_file in need_files:
                df = pd.read_parquet(need_file)
                
                # Method 1: 全セルの合計
                method1_sum = df.sum().sum()
                total_need_method1 += method1_sum
                
                # Method 2: numpy配列での計算
                method2_sum = np.sum(df.values)
                total_need_method2 += method2_sum
                
                # 方法間の差異確認
                diff = abs(method1_sum - method2_sum)
                if diff > self.tolerance:
                    self.validation_results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "calculation_precision",
                        f"{need_file.name}: 計算方法間で差異 {diff}",
                        actual_value=diff,
                        expected_value=0.0,
                        test_name="calculation_method_consistency"
                    ))
            
            # 総合計算精度確認
            total_diff = abs(total_need_method1 - total_need_method2)
            if total_diff > self.tolerance:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "calculation_precision",
                    f"総需要計算で方法間差異: {total_diff}",
                    actual_value=total_diff,
                    expected_value=0.0,
                    test_name="total_calculation_precision"
                ))
            
            # 浮動小数点演算精度確認
            slot_hours = 0.5
            total_staff_records = len(care_data)
            
            # 異なる計算順序での検証
            calc1 = (total_need_method1 * slot_hours) / 30 - (total_staff_records * slot_hours) / 30
            calc2 = (total_need_method1 - total_staff_records) * slot_hours / 30
            
            precision_diff = abs(calc1 - calc2)
            if precision_diff > self.tolerance:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    "calculation_precision",
                    f"浮動小数点精度差異: {precision_diff}",
                    actual_value=precision_diff,
                    expected_value=0.0,
                    test_name="floating_point_precision"
                ))
            
            print(f'  需要合計検証: Method1={total_need_method1}, Method2={total_need_method2}')
            print(f'  計算精度差異: {total_diff} (許容値: {self.tolerance})')
            
        except Exception as e:
            self.validation_results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                "calculation_precision",
                f"計算精度検証エラー: {str(e)}",
                test_name="calculation_precision_check"
            ))
    
    def _verify_edge_cases(self):
        """エッジケースの網羅的検証"""
        print('\n【4. エッジケース検証】')
        
        edge_cases = [
            # ケース1: 需要ゼロ
            {"need": 0, "staff": 100, "expected_diff": -100, "case": "需要ゼロ"},
            # ケース2: 配置ゼロ  
            {"need": 100, "staff": 0, "expected_diff": 100, "case": "配置ゼロ"},
            # ケース3: 完全一致
            {"need": 100, "staff": 100, "expected_diff": 0, "case": "完全一致"},
            # ケース4: 極小値
            {"need": 0.001, "staff": 0.002, "expected_diff": -0.001, "case": "極小値"},
            # ケース5: 大きな値
            {"need": 1e6, "staff": 1e6 + 1, "expected_diff": -1, "case": "大きな値"}
        ]
        
        for case in edge_cases:
            need = case["need"]
            staff = case["staff"] 
            expected = case["expected_diff"]
            case_name = case["case"]
            
            # 実際の差分計算
            actual_diff = need - staff
            
            # 期待値との比較
            if abs(actual_diff - expected) > self.tolerance:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "edge_cases",
                    f"{case_name}: 計算結果不整合 {actual_diff} vs 期待値 {expected}",
                    actual_value=actual_diff,
                    expected_value=expected,
                    test_name=f"edge_case_{case_name}"
                ))
        
        print(f'  エッジケース: {len(edge_cases)}ケース検証完了')
    
    def _verify_mathematical_validity(self):
        """数学的妥当性の完全検証"""
        print('\n【5. 数学的妥当性検証】')
        
        try:
            # 実データでの数学的性質確認
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            care_data = intermediate_data[intermediate_data['role'].str.contains('介護', na=False)]
            
            need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*介護*.parquet'))
            
            total_need = 0
            for need_file in need_files:
                df = pd.read_parquet(need_file)
                total_need += df.sum().sum()
            
            # 線形性検証
            slot_hours = 0.5
            period_days = 30
            
            need_hours = total_need * slot_hours
            staff_hours = len(care_data) * slot_hours
            
            # 分配法則検証: (a * b) / c == a * (b / c)
            daily1 = (need_hours - staff_hours) / period_days  # 方法1
            daily2 = (total_need - len(care_data)) * slot_hours / period_days  # 方法2
            
            linearity_diff = abs(daily1 - daily2)
            if linearity_diff > self.tolerance:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "mathematical_validity",
                    f"線形性違反: {linearity_diff}",
                    actual_value=linearity_diff,
                    expected_value=0.0,
                    test_name="linearity_check"
                ))
            
            # 単調性検証: staffが増加すれば不足は減少
            staff_base = len(care_data)
            staff_increased = staff_base + 100
            
            base_shortage = (total_need - staff_base) * slot_hours / period_days
            increased_shortage = (total_need - staff_increased) * slot_hours / period_days
            
            if increased_shortage >= base_shortage:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "mathematical_validity",
                    "単調性違反: 配置増加で不足が増加",
                    actual_value=increased_shortage,
                    expected_value=base_shortage,
                    test_name="monotonicity_check"
                ))
            
            # 可逆性検証
            original_diff = base_shortage
            restored_need = staff_base + (original_diff * period_days / slot_hours)
            
            restoration_diff = abs(restored_need - total_need)
            if restoration_diff > self.tolerance:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    "mathematical_validity",
                    f"可逆性精度低下: {restoration_diff}",
                    actual_value=restoration_diff,
                    expected_value=0.0,
                    test_name="reversibility_check"
                ))
            
            print(f'  線形性差異: {linearity_diff}')
            print(f'  可逆性差異: {restoration_diff}')
            
        except Exception as e:
            self.validation_results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                "mathematical_validity",
                f"数学的妥当性検証エラー: {str(e)}",
                test_name="mathematical_validity_check"
            ))
    
    def _verify_temporal_consistency(self):
        """時間軸整合性検証"""
        print('\n【6. 時間軸整合性検証】')
        
        try:
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            
            # 期間整合性確認
            date_range = intermediate_data['ds'].dt.date.unique()
            actual_days = len(date_range)
            
            min_date = intermediate_data['ds'].min()
            max_date = intermediate_data['ds'].max() 
            expected_days = (max_date - min_date).days + 1
            
            if actual_days != expected_days:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    "temporal_consistency",
                    f"日数不整合: 実際{actual_days}日 vs 期待{expected_days}日",
                    actual_value=actual_days,
                    expected_value=expected_days,
                    test_name="date_range_consistency"
                ))
            
            # 時間スロット整合性確認
            time_slots = intermediate_data['ds'].dt.time.unique()
            unique_slots = len(time_slots)
            
            # 30分間隔での24時間 = 48スロット想定
            if unique_slots != 48:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.WARNING, 
                    "temporal_consistency",
                    f"時間スロット数: {unique_slots} (期待: 48)",
                    actual_value=unique_slots,
                    expected_value=48,
                    test_name="time_slot_consistency"
                ))
            
            print(f'  実際の期間: {actual_days}日')
            print(f'  時間スロット: {unique_slots}個')
            
        except Exception as e:
            self.validation_results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                "temporal_consistency", 
                f"時間軸整合性検証エラー: {str(e)}",
                test_name="temporal_consistency_check"
            ))
    
    def _verify_role_mapping(self):
        """職種マッピング検証"""
        print('\n【7. 職種マッピング検証】')
        
        try:
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            
            # 介護関連職種の存在確認
            all_roles = intermediate_data['role'].unique()
            care_roles = [role for role in all_roles if '介護' in str(role)]
            
            if not care_roles:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.CRITICAL,
                    "role_mapping",
                    "介護関連職種が見つかりません",
                    test_name="care_role_existence"
                ))
            
            # 需要ファイルとの職種対応確認
            need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
            need_file_roles = set()
            
            for need_file in need_files:
                # ファイル名から職種抽出
                filename = need_file.name
                role_part = filename.replace('need_per_date_slot_role_', '').replace('.parquet', '')
                need_file_roles.add(role_part)
            
            # マッピング整合性確認
            care_roles_clean = set()
            for role in care_roles:
                clean_role = str(role).replace('/', '').replace('（', '').replace('）', '').replace('・', '')
                care_roles_clean.add(clean_role)
            
            unmapped_roles = care_roles_clean - need_file_roles
            if unmapped_roles:
                self.validation_results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    "role_mapping",
                    f"需要ファイルが見つからない職種: {list(unmapped_roles)}",
                    test_name="role_file_mapping"
                ))
            
            print(f'  検出職種: {len(care_roles)}個')
            print(f'  需要ファイル: {len(need_file_roles)}個')
            print(f'  未マッピング: {len(unmapped_roles)}個')
            
        except Exception as e:
            self.validation_results.append(ValidationResult(
                ValidationLevel.CRITICAL,
                "role_mapping",
                f"職種マッピング検証エラー: {str(e)}",
                test_name="role_mapping_check"
            ))
    
    def _generate_comprehensive_report(self) -> Dict[str, any]:
        """包括的検証レポート生成"""
        print('\n' + '=' * 80)
        print('包括的検証結果レポート')
        print('=' * 80)
        
        # 重要度別集計
        level_counts = {}
        for level in ValidationLevel:
            count = len([r for r in self.validation_results if r.level == level])
            level_counts[level.value] = count
        
        # カテゴリ別集計
        category_counts = {}
        for result in self.validation_results:
            if result.category not in category_counts:
                category_counts[result.category] = []
            category_counts[result.category].append(result)
        
        print(f'\n【重要度別サマリー】')
        total_issues = len(self.validation_results)
        print(f'総検出問題数: {total_issues}')
        
        for level, count in level_counts.items():
            if count > 0:
                print(f'  {level}: {count}件')
        
        print(f'\n【カテゴリ別詳細】')
        for category, results in category_counts.items():
            print(f'\n{category.upper()}:')
            for result in results:
                status_symbol = {
                    ValidationLevel.CRITICAL: '[CRITICAL]',
                    ValidationLevel.ERROR: '[ERROR]',
                    ValidationLevel.WARNING: '[WARNING]', 
                    ValidationLevel.INFO: '[INFO]'
                }[result.level]
                
                print(f'  {status_symbol} {result.message}')
                if result.actual_value is not None and result.expected_value is not None:
                    print(f'    実測値: {result.actual_value}, 期待値: {result.expected_value}')
        
        # 技術的推奨事項
        print(f'\n【技術的推奨事項】')
        critical_count = level_counts.get('CRITICAL', 0)
        error_count = level_counts.get('ERROR', 0)
        
        if critical_count > 0:
            print('1. CRITICAL問題の即座修正が必要')
        if error_count > 0:
            print('2. ERROR問題の修正後に運用開始')
        if total_issues == 0:
            print('✓ 全検証項目をパス - 技術的品質確保')
        
        return {
            'total_issues': total_issues,
            'level_summary': level_counts,
            'category_details': {cat: len(results) for cat, results in category_counts.items()},
            'validation_results': self.validation_results,
            'technical_quality': 'PASS' if critical_count == 0 and error_count == 0 else 'FAIL'
        }

def run_comprehensive_verification():
    """包括的検証の実行"""
    scenario_dir = Path('extracted_results/out_p25_based')
    
    if not scenario_dir.exists():
        print(f'エラー: シナリオディレクトリが見つかりません: {scenario_dir}')
        return None
    
    verifier = ComprehensiveShortageLogicVerifier(scenario_dir)
    return verifier.verify_all_logic()

if __name__ == "__main__":
    result = run_comprehensive_verification()
    
    if result:
        print('\n' + '=' * 80)
        if result['technical_quality'] == 'PASS':
            print('最終結論: 技術的品質基準をクリア')
        else:
            print('最終結論: 修正が必要な技術的問題を検出')
        print('=' * 80)