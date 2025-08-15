#!/usr/bin/env python3
"""
Need積算の根本的問題調査
現場の方の指摘「その数字はあり得ない」「基準値つまりNeedの積算が問題」を検証
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

class NeedCalculationFundamentalInvestigator:
    """Need積算の根本的問題調査システム"""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        
    def investigate_need_fundamental_issues(self) -> Dict[str, any]:
        """Need積算の根本的問題調査"""
        
        print('=' * 80)
        print('Need積算の根本的問題調査')
        print('現場指摘: 「その数字はあり得ない」「Needの積算が問題」')
        print('=' * 80)
        
        issues = []
        
        # 1. Needファイルの生データ構造詳細調査
        need_issues = self._investigate_need_file_raw_structure()
        issues.extend(need_issues)
        
        # 2. Need積算ロジックの問題特定
        logic_issues = self._investigate_need_calculation_logic()
        issues.extend(logic_issues)
        
        # 3. 現実的なNeed値との乖離分析
        reality_issues = self._investigate_reality_divergence()
        issues.extend(reality_issues)
        
        # 4. Needの意味・解釈の問題
        interpretation_issues = self._investigate_need_interpretation()
        issues.extend(interpretation_issues)
        
        return self._generate_fundamental_issue_report(issues)
    
    def _investigate_need_file_raw_structure(self) -> List[Dict]:
        """Needファイルの生データ構造詳細調査"""
        print('\n【Needファイル生データ構造調査】')
        
        issues = []
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        for need_file in need_files:
            try:
                df = pd.read_parquet(need_file)
                
                print(f'\n{need_file.name}:')
                print(f'  形状: {df.shape}')
                print(f'  データ型: {df.dtypes.iloc[0]}')
                
                # セルの実際の値分析
                print(f'  値の範囲: {df.min().min()} ～ {df.max().max()}')
                print(f'  平均値: {df.mean().mean():.3f}')
                print(f'  中央値: {df.median().median():.3f}')
                print(f'  合計値: {df.sum().sum()}')
                
                # ゼロでない値の分布
                non_zero_values = df[df > 0].stack().values
                if len(non_zero_values) > 0:
                    print(f'  非ゼロ値: {len(non_zero_values)}個')
                    print(f'  非ゼロ値の分布: min={non_zero_values.min()}, max={non_zero_values.max()}, avg={non_zero_values.mean():.3f}')
                    
                    # 具体的な値の例
                    unique_values = np.unique(non_zero_values)
                    print(f'  ユニーク値例: {unique_values[:10]}')
                else:
                    print(f'  警告: 全てゼロ値')
                    issues.append({
                        'type': 'CRITICAL',
                        'file': need_file.name,
                        'issue': '全てゼロ値のNeedファイル',
                        'impact': '需要計算が無効'
                    })
                
                # 時間パターン分析
                print(f'  時間パターン（行方向）:')
                row_sums = df.sum(axis=1)
                high_demand_hours = row_sums[row_sums > row_sums.quantile(0.8)].index
                print(f'    高需要時間帯: {list(high_demand_hours[:10])}')
                
                # 日付パターン分析
                print(f'  日付パターン（列方向）:')
                col_sums = df.sum(axis=0)
                high_demand_days = col_sums[col_sums > col_sums.quantile(0.8)].index
                print(f'    高需要日: {list(high_demand_days[:5])}')
                
                # 現実性検証
                max_single_slot = df.max().max()
                if max_single_slot > 20:  # 1スロットで20人超は異常
                    issues.append({
                        'type': 'ERROR',
                        'file': need_file.name,
                        'issue': f'単一スロットで{max_single_slot}人の需要は非現実的',
                        'impact': '需要過大評価'
                    })
                
                # 日次合計の現実性
                daily_totals = df.sum(axis=0)
                max_daily = daily_totals.max()
                avg_daily = daily_totals.mean()
                
                print(f'  1日最大需要: {max_daily}人')
                print(f'  1日平均需要: {avg_daily:.1f}人')
                
                if max_daily > 200:  # 1日200人超の需要は介護施設として非現実的
                    issues.append({
                        'type': 'ERROR', 
                        'file': need_file.name,
                        'issue': f'1日需要{max_daily}人は介護施設として非現実的',
                        'impact': '需要過大積算'
                    })
                
            except Exception as e:
                issues.append({
                    'type': 'CRITICAL',
                    'file': need_file.name,
                    'issue': f'ファイル読み込みエラー: {e}',
                    'impact': '分析不可'
                })
        
        return issues
    
    def _investigate_need_calculation_logic(self) -> List[Dict]:
        """Need積算ロジックの問題特定"""
        print('\n【Need積算ロジック問題特定】')
        
        issues = []
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        # 全Needファイルの合計計算
        total_need_all_files = 0
        total_need_by_role = {}
        
        for need_file in need_files:
            try:
                df = pd.read_parquet(need_file)
                file_total = df.sum().sum()
                total_need_all_files += file_total
                
                # ファイル名から職種抽出
                role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
                total_need_by_role[role_name] = file_total
                
            except Exception as e:
                continue
        
        print(f'全Needファイル合計: {total_need_all_files}人・時間帯')
        print(f'職種別Need: {total_need_by_role}')
        
        # 現実的な介護施設の需要と比較
        print(f'\n現実的な介護施設との比較:')
        
        # 一般的な介護施設（定員50名程度）の想定需要
        typical_facility_capacity = 50  # 定員50名
        typical_care_hours_per_resident_per_day = 4  # 1人1日4時間のケア
        typical_daily_need_hours = typical_facility_capacity * typical_care_hours_per_resident_per_day
        typical_30day_need_hours = typical_daily_need_hours * 30
        
        # スロット換算（1.143時間/スロット）
        slot_hours = 1.143
        typical_30day_need_slots = typical_30day_need_hours / slot_hours
        
        print(f'現実的な30日需要（定員50名施設）:')
        print(f'  1日需要: {typical_daily_need_hours}時間')
        print(f'  30日需要: {typical_30day_need_hours}時間')
        print(f'  30日需要（スロット換算）: {typical_30day_need_slots:.1f}人・時間帯')
        
        # 乖離率計算
        divergence_ratio = (total_need_all_files - typical_30day_need_slots) / typical_30day_need_slots * 100
        
        print(f'\n乖離分析:')
        print(f'  計算需要: {total_need_all_files}人・時間帯')
        print(f'  現実的需要: {typical_30day_need_slots:.1f}人・時間帯')
        print(f'  乖離率: {divergence_ratio:+.1f}%')
        
        if abs(divergence_ratio) > 100:  # 100%以上の乖離は問題
            issues.append({
                'type': 'CRITICAL',
                'file': 'ALL_NEED_FILES',
                'issue': f'現実的需要との乖離率{divergence_ratio:+.1f}%は異常',
                'impact': 'Need積算ロジック根本的問題'
            })
        
        # 職種別の現実性チェック
        for role, need_value in total_need_by_role.items():
            # 介護系職種の現実性チェック
            if '介護' in role:
                # 介護職種は全体需要の60-80%程度が現実的
                expected_care_need = typical_30day_need_slots * 0.7  # 70%と仮定
                care_divergence = (need_value - expected_care_need) / expected_care_need * 100
                
                if abs(care_divergence) > 200:  # 200%以上の乖離
                    issues.append({
                        'type': 'ERROR',
                        'file': f'need_per_date_slot_role_{role}.parquet',
                        'issue': f'介護職種需要の乖離率{care_divergence:+.1f}%は非現実的',
                        'impact': '介護職種需要過大/過小積算'
                    })
        
        return issues
    
    def _investigate_reality_divergence(self) -> List[Dict]:
        """現実的なNeed値との乖離分析"""
        print('\n【現実的Need値との乖離分析】')
        
        issues = []
        
        # 実際の配置データとの比較
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        print(f'実配置データ: {len(intermediate_data)}レコード')
        
        # 職種別実配置
        actual_allocation_by_role = intermediate_data['role'].value_counts()
        print(f'実配置職種別: {dict(actual_allocation_by_role)}')
        
        # Need vs 実配置の比較
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        for need_file in need_files:
            try:
                df = pd.read_parquet(need_file)
                need_total = df.sum().sum()
                
                # ファイル名から職種
                role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
                
                # 対応する実配置を検索
                matching_roles = [role for role in actual_allocation_by_role.index if role_name in str(role) or str(role) in role_name]
                
                if matching_roles:
                    actual_records = sum(actual_allocation_by_role[role] for role in matching_roles)
                    
                    # Need vs 実配置の比率
                    if actual_records > 0:
                        need_vs_actual_ratio = need_total / actual_records
                        
                        print(f'{role_name}:')
                        print(f'  Need: {need_total}人・時間帯')
                        print(f'  実配置: {actual_records}レコード')
                        print(f'  比率: {need_vs_actual_ratio:.1f}倍')
                        
                        # 異常な比率のチェック
                        if need_vs_actual_ratio > 10:  # 10倍以上は異常
                            issues.append({
                                'type': 'ERROR',
                                'file': need_file.name,
                                'issue': f'Need/実配置比率{need_vs_actual_ratio:.1f}倍は過大',
                                'impact': 'Need過大積算による不正確な不足計算'
                            })
                        elif need_vs_actual_ratio < 0.1:  # 0.1倍以下も異常
                            issues.append({
                                'type': 'WARNING',
                                'file': need_file.name,
                                'issue': f'Need/実配置比率{need_vs_actual_ratio:.1f}倍は過小',
                                'impact': 'Need過小積算の可能性'
                            })
                
            except Exception as e:
                continue
        
        return issues
    
    def _investigate_need_interpretation(self) -> List[Dict]:
        """Needの意味・解釈の問題調査"""
        print('\n【Needの意味・解釈問題調査】')
        
        issues = []
        
        # Needファイルのサンプルデータ詳細解析
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*介護*.parquet'))
        
        if need_files:
            sample_file = need_files[0]
            df = pd.read_parquet(sample_file)
            
            print(f'サンプルファイル: {sample_file.name}')
            print(f'データ詳細分析:')
            
            # 各時間帯の需要パターン
            hourly_pattern = df.sum(axis=1)
            
            print(f'  時間帯別需要パターン（上位10時間帯）:')
            top_hours = hourly_pattern.nlargest(10)
            for idx, value in top_hours.items():
                print(f'    時間帯{idx}: {value}人')
            
            # 各日の需要パターン
            daily_pattern = df.sum(axis=0)
            
            print(f'  日別需要パターン（上位5日）:')
            top_days = daily_pattern.nlargest(5)
            for idx, value in top_days.items():
                print(f'    {idx}: {value}人')
            
            # Needの解釈問題の特定
            
            # 問題1: 時間帯需要の現実性
            max_hourly_need = hourly_pattern.max()
            if max_hourly_need > 50:  # 1時間帯50人超は介護施設として非現実的
                issues.append({
                    'type': 'ERROR',
                    'file': sample_file.name,
                    'issue': f'1時間帯{max_hourly_need}人の需要は介護施設として非現実的',
                    'impact': 'Need解釈・計算方法の根本的誤り'
                })
            
            # 問題2: 需要の時間分布
            zero_hour_count = (hourly_pattern == 0).sum()
            if zero_hour_count > 24:  # 24時間帯以上でゼロ需要は不自然
                issues.append({
                    'type': 'WARNING',
                    'file': sample_file.name,
                    'issue': f'{zero_hour_count}時間帯でゼロ需要は不自然',
                    'impact': 'Need分布パターンの問題'
                })
            
            # 問題3: 需要の日間変動
            daily_cv = daily_pattern.std() / daily_pattern.mean()  # 変動係数
            if daily_cv > 1.0:  # 変動係数1.0超は過大な変動
                issues.append({
                    'type': 'WARNING',
                    'file': sample_file.name,
                    'issue': f'日間需要変動係数{daily_cv:.2f}は過大',
                    'impact': 'Need変動パターンの非現実性'
                })
            
            print(f'  日間変動係数: {daily_cv:.3f}')
            
        return issues
    
    def _generate_fundamental_issue_report(self, issues: List[Dict]) -> Dict[str, any]:
        """根本的問題レポート生成"""
        print('\n' + '=' * 80)
        print('Need積算 根本的問題レポート')
        print('=' * 80)
        
        # 問題の重要度別集計
        critical_issues = [i for i in issues if i['type'] == 'CRITICAL']
        error_issues = [i for i in issues if i['type'] == 'ERROR'] 
        warning_issues = [i for i in issues if i['type'] == 'WARNING']
        
        print(f'\n【問題サマリー】')
        print(f'CRITICAL: {len(critical_issues)}件')
        print(f'ERROR: {len(error_issues)}件')
        print(f'WARNING: {len(warning_issues)}件')
        print(f'総問題数: {len(issues)}件')
        
        print(f'\n【CRITICAL問題】')
        for issue in critical_issues:
            print(f'  {issue["file"]}: {issue["issue"]}')
            print(f'    影響: {issue["impact"]}')
        
        print(f'\n【ERROR問題】')
        for issue in error_issues:
            print(f'  {issue["file"]}: {issue["issue"]}')
            print(f'    影響: {issue["impact"]}')
        
        print(f'\n【根本原因分析】')
        
        # 根本原因の推定
        root_causes = []
        
        if any('非現実的' in i['issue'] for i in issues):
            root_causes.append('Needファイルの値が現実的な介護施設の需要規模を大幅に超過')
        
        if any('乖離率' in i['issue'] for i in issues):
            root_causes.append('Need積算ロジックが実際の運営実態と乖離')
        
        if any('ゼロ値' in i['issue'] for i in issues):
            root_causes.append('Needデータの生成・取得プロセスに問題')
        
        if any('比率' in i['issue'] for i in issues):
            root_causes.append('Need計算の単位系・スケール設定が不適切')
        
        for i, cause in enumerate(root_causes, 1):
            print(f'  {i}. {cause}')
        
        print(f'\n【推奨対策】')
        print('1. 現場の実際の業務量・人員配置を基準としたNeed再定義')
        print('2. Needファイル生成ロジックの全面見直し')  
        print('3. 介護施設の標準的な人員配置基準との整合性確認')
        print('4. 段階的なNeed値の妥当性検証プロセス導入')
        
        return {
            'total_issues': len(issues),
            'critical_count': len(critical_issues),
            'error_count': len(error_issues),
            'warning_count': len(warning_issues),
            'root_causes': root_causes,
            'all_issues': issues,
            'requires_need_recalculation': len(critical_issues) > 0 or len(error_issues) > 2
        }

def run_need_fundamental_investigation():
    """Need積算根本問題調査の実行"""
    scenario_dir = Path('extracted_results/out_p25_based')
    
    if not scenario_dir.exists():
        print(f'エラー: シナリオディレクトリが見つかりません: {scenario_dir}')
        return None
    
    investigator = NeedCalculationFundamentalInvestigator(scenario_dir)
    return investigator.investigate_need_fundamental_issues()

if __name__ == "__main__":
    result = run_need_fundamental_investigation()
    
    if result:
        print('\n' + '=' * 80)
        if result['requires_need_recalculation']:
            print('結論: Need積算の根本的見直しが必要')
            print('現場の指摘通り、基準値（Need）の積算に重大な問題があります')
        else:
            print('結論: Need積算は概ね妥当')
        print('=' * 80)