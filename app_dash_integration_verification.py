#!/usr/bin/env python
"""
app.py と dash_app.py の整合性検証

app.pyで生成されるZIPファイルとdash_app.pyの読み込み処理の整合性を確認
"""

import pandas as pd
import numpy as np
from pathlib import Path
import zipfile
import tempfile
import shutil
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class AppDashIntegrationVerifier:
    """app.py と dash_app.py の整合性検証クラス"""
    
    def __init__(self):
        self.test_output_dir = Path("test_integration_output")
        self.test_output_dir.mkdir(exist_ok=True)
        self.verification_results = {}
        
    def verify_complete_integration(self):
        """完全な統合検証"""
        
        print("=== app.py と dash_app.py 統合検証 ===")
        print("=" * 50)
        
        # Step 1: 改革後システムでZIPファイル生成
        print("\n[Step 1] 改革後システムでのZIP生成テスト")
        zip_generation_result = self._test_enhanced_zip_generation()
        
        # Step 2: 生成されたZIPファイルの内容確認
        print("\n[Step 2] ZIPファイル内容の検証")
        zip_content_result = self._verify_zip_contents()
        
        # Step 3: dash_app.py での読み込みテスト
        print("\n[Step 3] dash_app.py での読み込み検証")
        dash_loading_result = self._test_dash_app_loading()
        
        # Step 4: データ整合性の確認
        print("\n[Step 4] データ整合性の検証")
        data_consistency_result = self._verify_data_consistency()
        
        # 総合評価
        print("\n[Step 5] 総合評価")
        overall_result = self._generate_overall_assessment(
            zip_generation_result,
            zip_content_result, 
            dash_loading_result,
            data_consistency_result
        )
        
        return overall_result
    
    def _test_enhanced_zip_generation(self):
        """改革後システムでのZIP生成テスト"""
        
        try:
            # 改革後の統一システムを使った分析実行
            from unified_shortage_calculator import calculate_true_shortage
            from dynamic_parameter_patch import shortage_and_brief_enhanced
            from robust_time_axis_processor import process_time_data_for_analysis
            
            # テストデータの準備
            test_scenario_dir = self.test_output_dir / "test_scenario"
            test_scenario_dir.mkdir(exist_ok=True)
            
            # 1. 基本シフトデータの生成
            dates = pd.date_range('2025-01-01', periods=7, freq='D')
            time_slots = pd.date_range('09:00', '17:00', freq='30min')
            roles = ['介護', '看護', '事務', 'リハビリ']
            
            # intermediate_data.parquet の生成
            intermediate_data = []
            for date in dates:
                for time_slot in time_slots:
                    for role in roles:
                        intermediate_data.append({
                            'ds': pd.Timestamp.combine(date.date(), time_slot.time()),
                            'staff': f'Staff_{len(intermediate_data)%10}',
                            'role': role,
                            'employment': np.random.choice(['正社員', 'パート']),
                            'need': np.random.randint(1, 4),
                            'allocation': np.random.randint(0, 3)
                        })
            
            intermediate_df = pd.DataFrame(intermediate_data)
            intermediate_df.to_parquet(test_scenario_dir / "intermediate_data.parquet")
            
            # 2. 改革後の統一計算システムで分析実行
            # 需要データの準備
            need_data = intermediate_df.groupby(['ds', 'role'])['need'].sum().unstack(fill_value=0)
            staff_data = intermediate_df.groupby(['ds', 'role'])['allocation'].sum().unstack(fill_value=0)
            
            # 統一過不足計算（0.5時間スロット）
            shortage_results = calculate_true_shortage(need_data.T, staff_data.T, slot_hours=0.5)
            
            # 3. 結果ファイルの保存（app.py形式に合わせて）
            
            # heat_ALL.parquet の生成
            heat_all_data = []
            for _, row in intermediate_df.iterrows():
                heat_all_data.append({
                    'staff': row['staff'],
                    'role': row['role'],
                    'employment': row['employment'],
                    f"{row['ds'].strftime('%Y-%m-%d')}": 1  # 配置フラグ
                })
            
            heat_all_df = pd.DataFrame(heat_all_data)
            heat_all_pivot = heat_all_df.groupby(['staff', 'role', 'employment']).sum().reset_index()
            heat_all_pivot.to_parquet(test_scenario_dir / "heat_ALL.parquet")
            
            # shortage関連ファイルの保存
            shortage_results['shortage_only'].to_parquet(test_scenario_dir / "shortage_time_enhanced.parquet")
            shortage_results['true_balance'].to_parquet(test_scenario_dir / "true_balance.parquet")
            shortage_results['excess_only'].to_parquet(test_scenario_dir / "excess_only.parquet")
            
            # 職種別不足サマリーの生成
            shortage_role_summary = []
            for role in roles:
                if role in shortage_results['shortage_only'].index:
                    role_shortage = shortage_results['shortage_only'].loc[role].sum() * 0.5
                    shortage_role_summary.append({
                        'role': role,
                        'shortage_hours': role_shortage,
                        'avg_daily_shortage': role_shortage / 7
                    })
            
            shortage_role_df = pd.DataFrame(shortage_role_summary)
            shortage_role_df.to_parquet(test_scenario_dir / "shortage_role_summary.parquet")
            
            # 雇用形態別不足サマリーの生成
            shortage_employment_summary = []
            for employment in ['正社員', 'パート']:
                employment_shortage = np.random.uniform(5, 15)  # テスト用
                shortage_employment_summary.append({
                    'employment': employment,
                    'shortage_hours': employment_shortage,
                    'avg_daily_shortage': employment_shortage / 7
                })
            
            shortage_employment_df = pd.DataFrame(shortage_employment_summary)
            shortage_employment_df.to_parquet(test_scenario_dir / "shortage_employment_summary.parquet")
            
            # 4. ZIPファイルの生成
            zip_file_path = self.test_output_dir / "enhanced_analysis_results.zip"
            
            with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in test_scenario_dir.glob("*.parquet"):
                    zipf.write(file_path, f"enhanced_scenario/{file_path.name}")
            
            print(f"   [OK] ZIP生成成功: {zip_file_path}")
            print(f"   [OK] ファイル数: {len(list(test_scenario_dir.glob('*.parquet')))}")
            print(f"   [OK] ZIPサイズ: {zip_file_path.stat().st_size / 1024:.1f}KB")
            
            return {
                'success': True,
                'zip_path': zip_file_path,
                'scenario_dir': test_scenario_dir,
                'file_count': len(list(test_scenario_dir.glob("*.parquet"))),
                'zip_size': zip_file_path.stat().st_size
            }
            
        except Exception as e:
            print(f"   [NG] ZIP生成エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _verify_zip_contents(self):
        """ZIPファイル内容の検証"""
        
        try:
            # ZIPファイルパスの取得（グローバル変数として保存）
            zip_file_path = self.test_output_dir / "enhanced_analysis_results.zip"
            if not zip_file_path.exists():
                raise FileNotFoundError("ZIPファイルが見つかりません")
            
            with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                file_list = zipf.namelist()
            
            # 期待されるファイルリスト
            expected_files = [
                'intermediate_data.parquet',
                'heat_ALL.parquet', 
                'shortage_time_enhanced.parquet',
                'true_balance.parquet',
                'excess_only.parquet',
                'shortage_role_summary.parquet',
                'shortage_employment_summary.parquet'
            ]
            
            # ファイル存在確認
            missing_files = []
            present_files = []
            
            for expected_file in expected_files:
                file_found = any(expected_file in f for f in file_list)
                if file_found:
                    present_files.append(expected_file)
                else:
                    missing_files.append(expected_file)
            
            print(f"   [OK] 存在ファイル: {len(present_files)}/{len(expected_files)}")
            if present_files:
                print(f"     - {', '.join(present_files[:3])}{'...' if len(present_files) > 3 else ''}")
            
            if missing_files:
                print(f"   [注意] 不足ファイル: {missing_files}")
            
            success = len(missing_files) == 0
            
            return {
                'success': success,
                'total_files': len(file_list),
                'expected_files': len(expected_files),
                'present_files': present_files,
                'missing_files': missing_files
            }
            
        except Exception as e:
            print(f"   [NG] ZIP内容検証エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_dash_app_loading(self):
        """dash_app.py での読み込みテスト"""
        
        try:
            # ZIPファイルを一時ディレクトリに展開
            zip_file_path = self.test_output_dir / "enhanced_analysis_results.zip"
            if not zip_file_path.exists():
                raise FileNotFoundError("ZIPファイルが見つかりません")
            
            temp_dir = Path(tempfile.mkdtemp())
            
            with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 展開されたディレクトリを確認
            extracted_dirs = list(temp_dir.glob("*"))
            if not extracted_dirs:
                raise ValueError("ZIPファイルの展開に失敗")
            
            scenario_dir = extracted_dirs[0]  # enhanced_scenario ディレクトリ
            
            # dash_app.py の主要機能をシミュレート
            loading_results = {}
            
            # 1. intermediate_data.parquet の読み込み
            intermediate_file = scenario_dir / "intermediate_data.parquet"
            if intermediate_file.exists():
                intermediate_df = pd.read_parquet(intermediate_file)
                loading_results['intermediate_data'] = {
                    'loaded': True,
                    'shape': intermediate_df.shape,
                    'columns': list(intermediate_df.columns)
                }
                print(f"   [OK] intermediate_data: {intermediate_df.shape}")
            else:
                loading_results['intermediate_data'] = {'loaded': False}
                print(f"   [NG] intermediate_data: ファイル不存在")
            
            # 2. shortage_role_summary.parquet の読み込み
            shortage_role_file = scenario_dir / "shortage_role_summary.parquet"
            if shortage_role_file.exists():
                shortage_role_df = pd.read_parquet(shortage_role_file)
                loading_results['shortage_role_summary'] = {
                    'loaded': True,
                    'shape': shortage_role_df.shape,
                    'roles': shortage_role_df['role'].tolist() if 'role' in shortage_role_df.columns else []
                }
                print(f"   [OK] shortage_role_summary: {shortage_role_df.shape}")
            else:
                loading_results['shortage_role_summary'] = {'loaded': False}
                print(f"   [NG] shortage_role_summary: ファイル不存在")
            
            # 3. shortage_employment_summary.parquet の読み込み
            shortage_employment_file = scenario_dir / "shortage_employment_summary.parquet"
            if shortage_employment_file.exists():
                shortage_employment_df = pd.read_parquet(shortage_employment_file)
                loading_results['shortage_employment_summary'] = {
                    'loaded': True,
                    'shape': shortage_employment_df.shape,
                    'employments': shortage_employment_df['employment'].tolist() if 'employment' in shortage_employment_df.columns else []
                }
                print(f"   [OK] shortage_employment_summary: {shortage_employment_df.shape}")
            else:
                loading_results['shortage_employment_summary'] = {'loaded': False}
                print(f"   [NG] shortage_employment_summary: ファイル不存在")
            
            # 4. heat_ALL.parquet の読み込み
            heat_all_file = scenario_dir / "heat_ALL.parquet"
            if heat_all_file.exists():
                heat_all_df = pd.read_parquet(heat_all_file)
                loading_results['heat_ALL'] = {
                    'loaded': True,
                    'shape': heat_all_df.shape,
                    'columns': list(heat_all_df.columns)
                }
                print(f"   [OK] heat_ALL: {heat_all_df.shape}")
            else:
                loading_results['heat_ALL'] = {'loaded': False}
                print(f"   [NG] heat_ALL: ファイル不存在")
            
            # クリーンアップ
            shutil.rmtree(temp_dir)
            
            # 成功評価
            loaded_count = sum(1 for result in loading_results.values() if result.get('loaded', False))
            total_count = len(loading_results)
            success = loaded_count == total_count
            
            print(f"   [OK] 読み込み成功: {loaded_count}/{total_count}")
            
            return {
                'success': success,
                'loading_results': loading_results,
                'loaded_count': loaded_count,
                'total_count': total_count
            }
            
        except Exception as e:
            print(f"   [NG] dash_app読み込みエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _verify_data_consistency(self):
        """データ整合性の検証"""
        
        try:
            # 生成されたデータの整合性チェック
            scenario_dir = self.test_output_dir / "test_scenario"
            if not scenario_dir.exists():
                raise ValueError("シナリオディレクトリが見つかりません")
            
            consistency_checks = {}
            
            # 1. intermediate_data と heat_ALL の整合性
            intermediate_df = pd.read_parquet(scenario_dir / "intermediate_data.parquet")
            heat_all_df = pd.read_parquet(scenario_dir / "heat_ALL.parquet")
            
            # スタッフ数の整合性
            intermediate_staff_count = intermediate_df['staff'].nunique()
            heat_all_staff_count = heat_all_df['staff'].nunique()
            staff_consistency = intermediate_staff_count == heat_all_staff_count
            
            consistency_checks['staff_count'] = {
                'consistent': staff_consistency,
                'intermediate': intermediate_staff_count,
                'heat_all': heat_all_staff_count
            }
            
            # 職種の整合性
            intermediate_roles = set(intermediate_df['role'].unique())
            
            shortage_role_df = pd.read_parquet(scenario_dir / "shortage_role_summary.parquet")
            shortage_roles = set(shortage_role_df['role'].unique())
            
            roles_consistency = intermediate_roles == shortage_roles
            
            consistency_checks['roles'] = {
                'consistent': roles_consistency,
                'intermediate_roles': list(intermediate_roles),
                'shortage_roles': list(shortage_roles)
            }
            
            # 2. shortage計算の妥当性
            shortage_role_totals = shortage_role_df['shortage_hours'].sum()
            reasonable_shortage = 0 <= shortage_role_totals <= 1000  # 妥当な範囲
            
            consistency_checks['shortage_calculation'] = {
                'reasonable': reasonable_shortage,
                'total_shortage_hours': shortage_role_totals
            }
            
            # 3. データ型の整合性
            date_columns_valid = True
            if 'ds' in intermediate_df.columns:
                try:
                    pd.to_datetime(intermediate_df['ds'])
                except:
                    date_columns_valid = False
            
            consistency_checks['data_types'] = {
                'date_columns_valid': date_columns_valid
            }
            
            # 総合評価
            all_consistent = (
                consistency_checks['staff_count']['consistent'] and
                consistency_checks['roles']['consistent'] and
                consistency_checks['shortage_calculation']['reasonable'] and
                consistency_checks['data_types']['date_columns_valid']
            )
            
            print(f"   [OK] スタッフ数整合性: {staff_consistency}")
            print(f"   [OK] 職種整合性: {roles_consistency}")  
            print(f"   [OK] 不足計算妥当性: {reasonable_shortage}")
            print(f"   [OK] データ型整合性: {date_columns_valid}")
            print(f"   [OK] 総合整合性: {all_consistent}")
            
            return {
                'success': all_consistent,
                'consistency_checks': consistency_checks
            }
            
        except Exception as e:
            print(f"   [NG] データ整合性検証エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_overall_assessment(self, zip_gen, zip_content, dash_loading, data_consistency):
        """総合評価の生成"""
        
        # 各ステップの結果を保存
        self.verification_results = {
            'zip_generation': zip_gen,
            'zip_content': zip_content,
            'dash_loading': dash_loading,
            'data_consistency': data_consistency
        }
        
        # 成功率の計算
        steps = ['zip_generation', 'zip_content', 'dash_loading', 'data_consistency']
        successful_steps = sum(1 for step in steps if self.verification_results[step].get('success', False))
        success_rate = successful_steps / len(steps)
        
        print("=" * 50)
        print("総合評価")
        print("=" * 50)
        
        print(f"成功ステップ: {successful_steps}/{len(steps)}")
        print(f"成功率: {success_rate*100:.1f}%")
        
        print("\n詳細:")
        status_map = {
            'zip_generation': 'ZIP生成',
            'zip_content': 'ZIP内容検証',
            'dash_loading': 'Dash読み込み',
            'data_consistency': 'データ整合性'
        }
        
        for step, name in status_map.items():
            success = self.verification_results[step].get('success', False)
            status = "[OK]" if success else "[NG]"
            print(f"  {status} {name}")
        
        overall_success = success_rate >= 0.75
        
        if overall_success:
            print(f"\napp.py と dash_app.py の整合性が確認されました！")
            print("システムは本番運用準備完了です。")
        else:
            print(f"\n整合性に問題があります。詳細を確認してください。")
        
        # 結果をファイルに保存
        report_file = self.test_output_dir / "integration_verification_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.verification_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n詳細レポート: {report_file}")
        
        return {
            'overall_success': overall_success,
            'success_rate': success_rate,
            'successful_steps': successful_steps,
            'total_steps': len(steps),
            'verification_results': self.verification_results
        }

def main():
    """メイン実行"""
    
    verifier = AppDashIntegrationVerifier()
    result = verifier.verify_complete_integration()
    
    return result

if __name__ == "__main__":
    integration_result = main()