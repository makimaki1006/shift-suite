#!/usr/bin/env python3
"""
組織全体・各職種・各雇用形態の真の過不足あぶりだしシステム
ユーザーの真の目的：組織全体、各職種ごと、各雇用形態ごとに真の過不足をあぶりだす
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from datetime import datetime

@dataclass
class ShortageAnalysisResult:
    """過不足分析結果の構造化"""
    category: str
    subcategory: str
    need_hours: float
    allocated_hours: float
    difference_hours: float
    daily_difference: float
    status: str
    impact_level: str
    records_count: int

class ComprehensiveOrganizationalShortageAnalyzer:
    """組織全体の包括的過不足分析システム"""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        self.results: List[ShortageAnalysisResult] = []
        self.dynamic_slot_hours = None
        self.actual_period_days = None
        
    def analyze_organizational_shortage(self) -> Dict[str, any]:
        """組織全体の包括的過不足分析"""
        
        print('=' * 80)
        print('組織全体 包括的過不足分析システム')
        print('目的: 組織全体・各職種・各雇用形態の真の過不足をあぶりだす')
        print('=' * 80)
        
        # 1. 基礎データ読み込みと動的パラメータ設定
        self._setup_dynamic_parameters()
        
        # 2. 組織全体分析
        self._analyze_organization_wide()
        
        # 3. 各職種分析
        self._analyze_by_role()
        
        # 4. 各雇用形態分析
        self._analyze_by_employment()
        
        # 5. クロス分析（職種×雇用形態）
        self._analyze_role_employment_cross()
        
        # 6. 統合レポート生成
        return self._generate_comprehensive_report()
    
    def _setup_dynamic_parameters(self):
        """動的パラメータの設定"""
        print('\n【動的パラメータ設定】')
        
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        # 実期間の動的取得
        self.actual_period_days = intermediate_data['ds'].dt.date.nunique()
        
        # 動的スロット時間計算
        time_slots = intermediate_data['ds'].dt.time.unique()
        total_minutes = 24 * 60
        self.dynamic_slot_hours = (total_minutes / len(time_slots)) / 60
        
        print(f'実期間: {self.actual_period_days}日')
        print(f'時間スロット数: {len(time_slots)}個')
        print(f'動的スロット時間: {self.dynamic_slot_hours:.3f}時間')
    
    def _analyze_organization_wide(self):
        """組織全体の過不足分析"""
        print('\n【組織全体分析】')
        
        try:
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            
            # 全需要データの収集
            need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
            total_organizational_need = 0
            
            for need_file in need_files:
                df = pd.read_parquet(need_file)
                file_need = df.sum().sum()
                total_organizational_need += file_need
                print(f'  {need_file.name}: {file_need}人・時間帯')
            
            # 全配置の計算（修正: 勤務レコードのみ対象とし、実スロット数を集計）
            work_data = intermediate_data[intermediate_data['holiday_type'].isin(['通常勤務', 'NORMAL'])].copy()
            total_records = len(work_data)
            total_working_slots = work_data['parsed_slots_count'].sum()
            total_allocated_hours = total_working_slots * self.dynamic_slot_hours
            
            # 組織全体の過不足
            org_need_hours = total_organizational_need * self.dynamic_slot_hours
            org_difference = org_need_hours - total_allocated_hours
            org_daily_difference = org_difference / self.actual_period_days
            
            # 状況判定
            if org_daily_difference > 0:
                status = f"不足 {org_daily_difference:.1f}時間/日"
                impact = "要緊急対策"
            elif org_daily_difference < 0:
                status = f"配置過多 {abs(org_daily_difference):.1f}時間/日"
                impact = "効率化機会"
            else:
                status = "完全均衡"
                impact = "理想的"
            
            # 結果登録
            self.results.append(ShortageAnalysisResult(
                category="組織全体",
                subcategory="全体",
                need_hours=org_need_hours,
                allocated_hours=total_allocated_hours,
                difference_hours=org_difference,
                daily_difference=org_daily_difference,
                status=status,
                impact_level=impact,
                records_count=total_records
            ))
            
            print(f'組織全体需要: {org_need_hours:.1f}時間')
            print(f'組織全体配置: {total_allocated_hours:.1f}時間')
            print(f'組織全体差分: {org_difference:.1f}時間')
            print(f'1日差分: {org_daily_difference:.1f}時間/日 ({status})')
            
        except Exception as e:
            print(f'組織全体分析エラー: {e}')
    
    def _analyze_by_role(self):
        """各職種別の過不足分析"""
        print('\n【各職種別分析】')
        
        try:
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            
            # 全職種の取得
            all_roles = intermediate_data['role'].unique()
            print(f'検出職種数: {len(all_roles)}職種')
            
            for role in all_roles:
                # 職種別配置データ（修正: 勤務レコードのみ対象とし、実スロット数を集計）
                role_all_data = intermediate_data[intermediate_data['role'] == role]
                work_data = role_all_data[role_all_data['holiday_type'].isin(['通常勤務', 'NORMAL'])].copy()
                role_records = len(work_data)
                total_working_slots = work_data['parsed_slots_count'].sum()
                role_allocated_hours = total_working_slots * self.dynamic_slot_hours
                
                # 職種別需要データの検索
                role_need_hours = 0
                need_files = self._find_need_files_for_role(role)
                
                for need_file in need_files:
                    df = pd.read_parquet(need_file)
                    file_need = df.sum().sum()
                    role_need_hours += file_need * self.dynamic_slot_hours
                
                # 過不足計算
                role_difference = role_need_hours - role_allocated_hours
                role_daily_difference = role_difference / self.actual_period_days
                
                # 状況判定
                if role_daily_difference > 5:
                    status = f"深刻な不足 {role_daily_difference:.1f}時間/日"
                    impact = "緊急対策必要"
                elif role_daily_difference > 0:
                    status = f"軽微な不足 {role_daily_difference:.1f}時間/日"
                    impact = "注意監視"
                elif role_daily_difference < -5:
                    status = f"大幅配置過多 {abs(role_daily_difference):.1f}時間/日"
                    impact = "配置見直し"
                elif role_daily_difference < 0:
                    status = f"軽微配置過多 {abs(role_daily_difference):.1f}時間/日"
                    impact = "効率化検討"
                else:
                    status = "適正配置"
                    impact = "維持"
                
                # 結果登録
                self.results.append(ShortageAnalysisResult(
                    category="職種別",
                    subcategory=role,
                    need_hours=role_need_hours,
                    allocated_hours=role_allocated_hours,
                    difference_hours=role_difference,
                    daily_difference=role_daily_difference,
                    status=status,
                    impact_level=impact,
                    records_count=role_records
                ))
                
                print(f'{role}: {role_daily_difference:+.1f}時間/日 ({status})')
                
        except Exception as e:
            print(f'職種別分析エラー: {e}')
    
    def _analyze_by_employment(self):
        """各雇用形態別の過不足分析"""
        print('\n【各雇用形態別分析】')
        
        try:
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            
            # 全雇用形態の取得
            all_employments = intermediate_data['employment'].unique()
            print(f'検出雇用形態数: {len(all_employments)}形態')
            
            for employment in all_employments:
                # 雇用形態別配置データ（修正: 勤務レコードのみ対象とし、実スロット数を集計）
                emp_all_data = intermediate_data[intermediate_data['employment'] == employment]
                emp_data = emp_all_data[emp_all_data['holiday_type'].isin(['通常勤務', 'NORMAL'])].copy() # Filter for work records
                emp_records = len(emp_data)
                total_working_slots = emp_data['parsed_slots_count'].sum()
                emp_allocated_hours = total_working_slots * self.dynamic_slot_hours
                
                # 雇用形態別の職種構成分析
                emp_roles = emp_data['role'].unique()
                emp_need_hours = 0
                
                # 各職種の需要を合計
                for role in emp_roles:
                    role_count_in_emp = len(emp_data[emp_data['role'] == role])
                    role_ratio = role_count_in_emp / emp_records
                    
                    # 職種の全体需要を取得
                    need_files = self._find_need_files_for_role(role)
                    role_total_need = 0
                    
                    for need_file in need_files:
                        df = pd.read_parquet(need_file)
                        role_total_need += df.sum().sum() * self.dynamic_slot_hours
                    
                    # 雇用形態別の需要配分（比例配分）
                    emp_need_hours += role_total_need * role_ratio
                
                # 過不足計算
                emp_difference = emp_need_hours - emp_allocated_hours
                emp_daily_difference = emp_difference / self.actual_period_days
                
                # 雇用形態特有の評価基準
                if "正社員" in str(employment) or "常勤" in str(employment):
                    threshold_high = 8
                    threshold_low = -8
                elif "パート" in str(employment) or "非常勤" in str(employment):
                    threshold_high = 4
                    threshold_low = -4
                else:
                    threshold_high = 6
                    threshold_low = -6
                
                # 状況判定
                if emp_daily_difference > threshold_high:
                    status = f"深刻な不足 {emp_daily_difference:.1f}時間/日"
                    impact = "採用強化必要"
                elif emp_daily_difference > 0:
                    status = f"軽微な不足 {emp_daily_difference:.1f}時間/日"
                    impact = "募集検討"
                elif emp_daily_difference < threshold_low:
                    status = f"大幅配置過多 {abs(emp_daily_difference):.1f}時間/日"
                    impact = "勤務調整必要"
                elif emp_daily_difference < 0:
                    status = f"軽微配置過多 {abs(emp_daily_difference):.1f}時間/日"
                    impact = "効率活用"
                else:
                    status = "適正配置"
                    impact = "維持"
                
                # 結果登録
                self.results.append(ShortageAnalysisResult(
                    category="雇用形態別",
                    subcategory=employment,
                    need_hours=emp_need_hours,
                    allocated_hours=emp_allocated_hours,
                    difference_hours=emp_difference,
                    daily_difference=emp_daily_difference,
                    status=status,
                    impact_level=impact,
                    records_count=emp_records
                ))
                
                print(f'{employment}: {emp_daily_difference:+.1f}時間/日 ({status})')
                
        except Exception as e:
            print(f'雇用形態別分析エラー: {e}')
    
    def _analyze_role_employment_cross(self):
        """職種×雇用形態クロス分析"""
        print('\n【職種×雇用形態クロス分析】')
        
        try:
            intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            
            # 職種×雇用形態の組み合わせ分析
            cross_combinations = intermediate_data.groupby(['role', 'employment']).size()
            
            print(f'職種×雇用形態組み合わせ: {len(cross_combinations)}パターン')
            
            for (role, employment), count in cross_combinations.items():
                # クロス配置データ（修正: 勤務レコードのみ対象とし、実スロット数を集計）
                cross_all_data = intermediate_data[
                    (intermediate_data['role'] == role) & 
                    (intermediate_data['employment'] == employment)
                ]
                cross_data = cross_all_data[cross_all_data['holiday_type'].isin(['通常勤務', 'NORMAL'])].copy()
                cross_records = len(cross_data)
                total_working_slots = cross_data['parsed_slots_count'].sum()
                cross_allocated_hours = total_working_slots * self.dynamic_slot_hours
                
                # クロス需要の推定（職種需要×雇用形態比率）
                need_files = self._find_need_files_for_role(role)
                role_total_need = 0
                
                for need_file in need_files:
                    df = pd.read_parquet(need_file)
                    role_total_need += df.sum().sum() * self.dynamic_slot_hours
                
                # 雇用形態別の配分比率
                role_data = intermediate_data[intermediate_data['role'] == role]
                emp_ratio = len(cross_data) / len(role_data) if len(role_data) > 0 else 0
                cross_need_hours = role_total_need * emp_ratio
                
                # 過不足計算
                cross_difference = cross_need_hours - cross_allocated_hours
                cross_daily_difference = cross_difference / self.actual_period_days
                
                # 重要性評価（レコード数による重み付け）
                if cross_records >= 100:
                    importance = "高重要"
                elif cross_records >= 50:
                    importance = "中重要"
                elif cross_records >= 10:
                    importance = "低重要"
                else:
                    importance = "参考"
                
                # 状況判定
                if cross_daily_difference > 2:
                    status = f"不足 {cross_daily_difference:.1f}時間/日"
                    impact = "対策検討"
                elif cross_daily_difference < -2:
                    status = f"配置過多 {abs(cross_daily_difference):.1f}時間/日"
                    impact = "配置見直し"
                else:
                    status = "適正"
                    impact = "維持"
                
                # 結果登録（重要なもののみ）
                if cross_records >= 10:  # 10件以上のみ
                    self.results.append(ShortageAnalysisResult(
                        category="職種×雇用形態",
                        subcategory=f"{role}×{employment}",
                        need_hours=cross_need_hours,
                        allocated_hours=cross_allocated_hours,
                        difference_hours=cross_difference,
                        daily_difference=cross_daily_difference,
                        status=f"{status} ({importance})",
                        impact_level=impact,
                        records_count=cross_records
                    ))
                
                if cross_records >= 10:  # 10件以上のみ表示
                    print(f'{role}×{employment}: {cross_daily_difference:+.1f}時間/日 ({importance})')
                    
        except Exception as e:
            print(f'クロス分析エラー: {e}')
    
    def _find_need_files_for_role(self, role: str) -> List[Path]:
        """職種に対応する需要ファイルの検索"""
        need_files = []
        all_need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        for need_file in all_need_files:
            filename = need_file.name
            role_part = filename.replace('need_per_date_slot_role_', '').replace('.parquet', '')
            
            # 完全一致
            if role == role_part:
                need_files.append(need_file)
                continue
            
            # クリーン一致
            clean_role = str(role).replace('/', '').replace('（', '').replace('）', '').replace('・', '')
            if clean_role == role_part:
                need_files.append(need_file)
                continue
            
            # 部分一致
            if role in role_part or role_part in role:
                need_files.append(need_file)
        
        return need_files
    
    def _generate_comprehensive_report(self) -> Dict[str, any]:
        """包括的過不足レポート生成"""
        print('\n' + '=' * 80)
        print('包括的過不足分析レポート')
        print('=' * 80)
        
        # カテゴリ別集計
        category_summary = {}
        for result in self.results:
            if result.category not in category_summary:
                category_summary[result.category] = {
                    'count': 0,
                    'total_shortage': 0,
                    'total_excess': 0,
                    'balanced': 0
                }
            
            category_summary[result.category]['count'] += 1
            
            if result.daily_difference > 0:
                category_summary[result.category]['total_shortage'] += result.daily_difference
            elif result.daily_difference < 0:
                category_summary[result.category]['total_excess'] += abs(result.daily_difference)
            else:
                category_summary[result.category]['balanced'] += 1
        
        # 重要な発見事項の抽出
        critical_shortages = [r for r in self.results if r.daily_difference > 5]
        major_excesses = [r for r in self.results if r.daily_difference < -5]
        
        print('\n【カテゴリ別サマリー】')
        for category, summary in category_summary.items():
            print(f'\n{category}:')
            print(f'  分析対象: {summary["count"]}項目')
            print(f'  不足合計: {summary["total_shortage"]:.1f}時間/日')
            print(f'  過多合計: {summary["total_excess"]:.1f}時間/日')
            print(f'  均衡項目: {summary["balanced"]}項目')
        
        print(f'\n【緊急対策必要項目】')
        print(f'深刻な不足: {len(critical_shortages)}項目')
        for shortage in critical_shortages:
            print(f'  {shortage.subcategory}: {shortage.daily_difference:+.1f}時間/日')
        
        print(f'\n【効率化機会項目】')
        print(f'大幅な配置過多: {len(major_excesses)}項目')
        for excess in major_excesses:
            print(f'  {excess.subcategory}: {excess.daily_difference:+.1f}時間/日')
        
        # JSON形式での詳細結果保存
        detailed_results = []
        for result in self.results:
            detailed_results.append({
                'category': result.category,
                'subcategory': result.subcategory,
                'need_hours': result.need_hours,
                'allocated_hours': result.allocated_hours,
                'difference_hours': result.difference_hours,
                'daily_difference': result.daily_difference,
                'status': result.status,
                'impact_level': result.impact_level,
                'records_count': result.records_count
            })
        
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'period_days': self.actual_period_days,
            'dynamic_slot_hours': self.dynamic_slot_hours,
            'category_summary': category_summary,
            'critical_shortages': len(critical_shortages),
            'major_excesses': len(major_excesses),
            'total_analyzed_items': len(self.results),
            'detailed_results': detailed_results
        }

def run_comprehensive_organizational_analysis():
    """包括的組織過不足分析の実行"""
    scenario_dir = Path('extracted_results/out_p25_based')
    
    if not scenario_dir.exists():
        print(f'エラー: シナリオディレクトリが見つかりません: {scenario_dir}')
        return None
    
    analyzer = ComprehensiveOrganizationalShortageAnalyzer(scenario_dir)
    return analyzer.analyze_organizational_shortage()

if __name__ == "__main__":
    result = run_comprehensive_organizational_analysis()
    
    if result:
        # 結果をJSONファイルに保存
        output_file = Path('comprehensive_organizational_shortage_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f'\n詳細結果を保存: {output_file}')
        print('=' * 80)
        print('ユーザー目的達成: 組織全体・各職種・各雇用形態の真の過不足をあぶりだし完了')
        print('=' * 80)