#!/usr/bin/env python3
"""
MECE品質の深い検証テスト

12軸シフト分析システムのMECE（相互排他性・網羅性）品質を検証
1. 軸間の重複チェック（相互排他性）
2. 各軸内の網羅性チェック
3. 抽出制約の実用性評価
4. 制約間の関係性分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class MECEQualityVerifier:
    """MECE品質検証クラス"""
    
    def __init__(self):
        self.axis_results = {}
        self.overlap_findings = []
        self.coverage_gaps = []
        self.quality_metrics = {}
        
    def create_comprehensive_test_data(self) -> pd.DataFrame:
        """包括的なテストデータを生成"""
        log.info("包括的テストデータ生成開始...")
        
        # より現実的なシフトパターンを生成
        np.random.seed(42)  # 再現性のため
        
        # 日付範囲（3ヶ月）
        date_range = pd.date_range('2024-01-01', '2024-03-31', freq='H')
        
        # スタッフリスト（経験レベル付き）
        staff_info = {
            '田中': {'role': '看護師', 'level': 'ベテラン', 'employment': '正社員'},
            '佐藤': {'role': '看護師', 'level': '中堅', 'employment': '正社員'},
            '鈴木': {'role': 'ケアマネ', 'level': 'ベテラン', 'employment': '正社員'},
            '山田': {'role': '介護職', 'level': '新人', 'employment': 'パート'},
            '高橋': {'role': '介護職', 'level': '中堅', 'employment': '正社員'},
            '伊藤': {'role': '看護師', 'level': '新人', 'employment': 'パート'},
            '渡辺': {'role': 'ケアマネ', 'level': '中堅', 'employment': '正社員'},
            '中村': {'role': '介護職', 'level': 'ベテラン', 'employment': '正社員'},
        }
        
        # 勤務コード（時間帯別）
        shift_codes = {
            '日勤': {'start': 8, 'end': 17, 'hours': 8},
            '早出': {'start': 7, 'end': 16, 'hours': 8},
            '遅出': {'start': 10, 'end': 19, 'hours': 8},
            '夜勤': {'start': 17, 'end': 9, 'hours': 16},  # 翌日まで
            '半日': {'start': 8, 'end': 13, 'hours': 4},
        }
        
        records = []
        
        # 各スタッフのシフトパターンを生成
        for date in pd.date_range('2024-01-01', '2024-03-31'):
            # 曜日による需要変動
            weekday = date.dayofweek
            is_weekend = weekday >= 5
            is_holiday = date.strftime('%m-%d') in ['01-01', '01-02', '01-03', '02-11', '02-12']
            
            # スタッフごとのシフト生成
            for staff_name, info in staff_info.items():
                # 個人の勤務パターン（経験レベルに応じて）
                if info['level'] == 'ベテラン':
                    work_prob = 0.8 if not is_weekend else 0.6
                    night_prob = 0.3
                elif info['level'] == '新人':
                    work_prob = 0.6 if not is_weekend else 0.3
                    night_prob = 0.1  # 新人は夜勤少ない
                else:
                    work_prob = 0.7 if not is_weekend else 0.5
                    night_prob = 0.2
                
                # 休日は勤務確率低下
                if is_holiday:
                    work_prob *= 0.5
                
                # 勤務するかどうか
                if np.random.random() < work_prob:
                    # 勤務コード選択（役職と経験による）
                    if info['role'] == '看護師' and np.random.random() < night_prob:
                        code = '夜勤'
                    elif info['employment'] == 'パート' and np.random.random() < 0.5:
                        code = '半日'
                    else:
                        code = np.random.choice(['日勤', '早出', '遅出'], p=[0.5, 0.25, 0.25])
                    
                    shift_info = shift_codes[code]
                    
                    # 時間スロットごとのレコード生成
                    if code == '夜勤':
                        # 夜勤は日をまたぐ
                        for hour in range(shift_info['start'], 24):
                            records.append({
                                'ds': pd.Timestamp(date) + pd.Timedelta(hours=hour),
                                'staff': staff_name,
                                'role': info['role'],
                                'employment': info['employment'],
                                'code': code,
                                'parsed_slots_count': 1,
                                'worktype': code,
                                'experience_level': info['level']
                            })
                        # 翌日の朝まで
                        next_date = date + timedelta(days=1)
                        for hour in range(0, shift_info['end']):
                            records.append({
                                'ds': pd.Timestamp(next_date) + pd.Timedelta(hours=hour),
                                'staff': staff_name,
                                'role': info['role'],
                                'employment': info['employment'],
                                'code': code,
                                'parsed_slots_count': 1,
                                'worktype': code,
                                'experience_level': info['level']
                            })
                    else:
                        for hour in range(shift_info['start'], shift_info['end']):
                            records.append({
                                'ds': pd.Timestamp(date) + pd.Timedelta(hours=hour),
                                'staff': staff_name,
                                'role': info['role'],
                                'employment': info['employment'],
                                'code': code,
                                'parsed_slots_count': 1,
                                'worktype': code,
                                'experience_level': info['level']
                            })
        
        df = pd.DataFrame(records)
        log.info(f"テストデータ生成完了: {len(df)}レコード, {df['staff'].nunique()}名, {df['ds'].min()} ～ {df['ds'].max()}")
        return df
    
    def run_all_axes_extraction(self, test_df: pd.DataFrame) -> Dict[int, Dict]:
        """全12軸の抽出を実行"""
        log.info("全12軸のMECE事実抽出を開始...")
        
        # 各軸のインポートと実行
        axes_modules = [
            (1, 'mece_fact_extractor', 'MECEFactExtractor', 'extract_axis1_facility_rules'),
            (2, 'axis2_staff_mece_extractor', 'StaffMECEFactExtractor', 'extract_axis2_staff_rules'),
            (3, 'axis3_time_calendar_mece_extractor', 'TimeCalendarMECEFactExtractor', 'extract_axis3_time_calendar_rules'),
            (4, 'axis4_demand_load_mece_extractor', 'DemandLoadMECEFactExtractor', 'extract_axis4_demand_load_rules'),
            (5, 'axis5_medical_care_quality_mece_extractor', 'MedicalCareQualityMECEFactExtractor', 'extract_axis5_medical_care_quality_rules'),
            (6, 'axis6_cost_efficiency_mece_extractor', 'CostEfficiencyMECEFactExtractor', 'extract_axis6_cost_efficiency_rules'),
            (7, 'axis7_legal_regulatory_mece_extractor', 'LegalRegulatoryMECEFactExtractor', 'extract_axis7_legal_regulatory_rules'),
            (8, 'axis8_staff_satisfaction_mece_extractor', 'StaffSatisfactionMECEFactExtractor', 'extract_axis8_staff_satisfaction_rules'),
            (9, 'axis9_business_process_mece_extractor', 'BusinessProcessMECEFactExtractor', 'extract_axis9_business_process_rules'),
            (10, 'axis10_risk_emergency_mece_extractor', 'RiskEmergencyMECEFactExtractor', 'extract_axis10_risk_emergency_rules'),
            (11, 'axis11_performance_improvement_mece_extractor', 'PerformanceImprovementMECEFactExtractor', 'extract_axis11_performance_improvement_rules'),
            (12, 'axis12_strategy_future_mece_extractor', 'StrategyFutureMECEFactExtractor', 'extract_axis12_strategy_future_rules')
        ]
        
        for axis_num, module_name, class_name, method_name in axes_modules:
            try:
                log.info(f"軸{axis_num}の抽出開始...")
                module = __import__(f'shift_suite.tasks.{module_name}', fromlist=[class_name])
                extractor_class = getattr(module, class_name)
                extractor = extractor_class()
                method = getattr(extractor, method_name)
                
                result = method(test_df)
                self.axis_results[axis_num] = result
                
                # 基本統計
                hr_count = len(result.get('human_readable', {}))
                mr_count = len(result.get('machine_readable', {}))
                log.info(f"軸{axis_num}完了: HR項目数={hr_count}, MR項目数={mr_count}")
                
            except Exception as e:
                log.error(f"軸{axis_num}でエラー: {str(e)}")
                self.axis_results[axis_num] = None
        
        return self.axis_results
    
    def verify_mutual_exclusivity(self) -> List[Dict]:
        """軸間の相互排他性を検証"""
        log.info("=== 相互排他性（軸間の重複）検証開始 ===")
        
        overlaps = []
        
        # 各軸ペアで制約の重複をチェック
        for i in range(1, 13):
            for j in range(i+1, 13):
                if self.axis_results.get(i) and self.axis_results.get(j):
                    overlap = self._check_axis_overlap(i, j)
                    if overlap:
                        overlaps.extend(overlap)
        
        # 重複の分類と分析
        if overlaps:
            log.warning(f"発見された重複: {len(overlaps)}件")
            for overlap in overlaps[:5]:  # 最初の5件を表示
                log.warning(f"  軸{overlap['axis1']}と軸{overlap['axis2']}: {overlap['type']} - {overlap['detail']}")
        else:
            log.info("✅ 軸間の重複は検出されませんでした（良好な相互排他性）")
        
        self.overlap_findings = overlaps
        return overlaps
    
    def verify_collective_exhaustiveness(self) -> List[Dict]:
        """各軸内の網羅性を検証"""
        log.info("=== 網羅性（カバレッジ）検証開始 ===")
        
        gaps = []
        
        # 各軸の期待されるカテゴリーとカバレッジ
        expected_categories = {
            1: ['配置基準', '設備制約', '運用時間', 'エリア制約', '役割定義', '業務範囲', '協力体制', '施設特性'],
            2: ['個人勤務パターン', 'スキル・配置', '時間選好', '休暇・休息', '経験レベル', '協働・相性', 'パフォーマンス', 'ライフスタイル'],
            3: ['祝日・特別日', '季節性・月次', '曜日・週次', '時間帯', '繁忙期・閑散期', '年間カレンダー', '時間枠・間隔', 'カレンダー依存'],
            4: ['需要予測', 'ピーク負荷', '負荷分散', '需要変動', 'リソース配分', 'キャパシティ', '需要パターン', '負荷平準化'],
            5: ['医療安全', 'ケア継続性', '専門性配置', '品質監督', '利用者適応', '医療連携', 'ケア記録', '品質改善'],
            6: ['人件費最適化', '雇用効率', '時間効率', '残業管理', '生産性向上', 'リソース活用', '業務効率', 'コスト削減'],
            7: ['労働基準', '配置基準', '資格要件', '安全衛生', 'コンプライアンス', '記録保持', '監査対応', '法改正対応'],
            8: ['ワークライフバランス', '公平性', '成長・キャリア', 'チームワーク', '労働環境', '評価・フィードバック', '自律性', '報酬・待遇'],
            9: ['業務手順', 'ワークフロー', '情報共有', 'タスク優先度', '処理時間', '引き継ぎ', '標準化', 'プロセス改善'],
            10: ['人員リスク', '業務継続', '緊急対応', '安全管理', 'インシデント', 'バックアップ', 'リスク評価', '訓練・準備'],
            11: ['性能指標', '品質評価', '効率測定', '改善目標', 'ベンチマーク', '監視・測定', 'フィードバック', '継続的改善'],
            12: ['戦略方向性', '将来ビジョン', '持続可能性', '成長・発展', '競争優位', '技術革新', '組織変革', 'レガシー継承']
        }
        
        for axis_num, categories in expected_categories.items():
            if self.axis_results.get(axis_num):
                result = self.axis_results[axis_num]
                hr_data = result.get('human_readable', {})
                
                # カバレッジチェック
                covered = set()
                if 'MECE分解事実' in hr_data:
                    covered = set(hr_data['MECE分解事実'].keys())
                
                missing = set(categories) - covered
                extra = covered - set(categories)
                
                if missing:
                    gaps.append({
                        'axis': axis_num,
                        'type': 'missing_categories',
                        'categories': list(missing),
                        'severity': 'high' if len(missing) > 2 else 'medium'
                    })
                    log.warning(f"軸{axis_num}: カバーされていないカテゴリー: {missing}")
                
                if extra:
                    log.info(f"軸{axis_num}: 追加カテゴリー: {extra}")
                
                # カテゴリー内の事実数チェック
                if 'MECE分解事実' in hr_data:
                    for cat, facts in hr_data['MECE分解事実'].items():
                        if isinstance(facts, list) and len(facts) == 0:
                            gaps.append({
                                'axis': axis_num,
                                'type': 'empty_category',
                                'category': cat,
                                'severity': 'medium'
                            })
        
        if gaps:
            log.warning(f"カバレッジギャップ: {len(gaps)}件")
        else:
            log.info("✅ 全軸で期待されるカテゴリーがカバーされています")
        
        self.coverage_gaps = gaps
        return gaps
    
    def analyze_constraint_quality(self) -> Dict[str, Any]:
        """抽出された制約の品質を分析"""
        log.info("=== 制約品質分析開始 ===")
        
        quality_analysis = {
            'total_constraints': 0,
            'hard_constraints': 0,
            'soft_constraints': 0,
            'preferences': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'actionable_constraints': 0,
            'vague_constraints': 0,
            'quantified_constraints': 0
        }
        
        # 各軸の制約を分析
        for axis_num, result in self.axis_results.items():
            if result and 'machine_readable' in result:
                mr_data = result['machine_readable']
                
                # 制約タイプのカウント
                for constraint_type in ['hard_constraints', 'soft_constraints', 'preferences']:
                    if constraint_type in mr_data:
                        constraints = mr_data[constraint_type]
                        if isinstance(constraints, list):
                            quality_analysis['total_constraints'] += len(constraints)
                            quality_analysis[constraint_type.replace('_constraints', '_constraints' if 'preferences' not in constraint_type else '')] += len(constraints)
                            
                            # 各制約の品質チェック
                            for constraint in constraints:
                                if isinstance(constraint, dict):
                                    # 信頼度チェック
                                    confidence = constraint.get('confidence', 0.5)
                                    if confidence >= 0.8:
                                        quality_analysis['high_confidence'] += 1
                                    elif confidence >= 0.5:
                                        quality_analysis['medium_confidence'] += 1
                                    else:
                                        quality_analysis['low_confidence'] += 1
                                    
                                    # 実行可能性チェック
                                    if self._is_actionable_constraint(constraint):
                                        quality_analysis['actionable_constraints'] += 1
                                    else:
                                        quality_analysis['vague_constraints'] += 1
                                    
                                    # 定量化チェック
                                    if self._is_quantified_constraint(constraint):
                                        quality_analysis['quantified_constraints'] += 1
        
        # 品質スコア計算
        if quality_analysis['total_constraints'] > 0:
            quality_analysis['actionability_ratio'] = quality_analysis['actionable_constraints'] / quality_analysis['total_constraints']
            quality_analysis['quantification_ratio'] = quality_analysis['quantified_constraints'] / quality_analysis['total_constraints']
            quality_analysis['high_confidence_ratio'] = quality_analysis['high_confidence'] / quality_analysis['total_constraints']
        else:
            quality_analysis['actionability_ratio'] = 0
            quality_analysis['quantification_ratio'] = 0
            quality_analysis['high_confidence_ratio'] = 0
        
        log.info(f"総制約数: {quality_analysis['total_constraints']}")
        log.info(f"  - ハード制約: {quality_analysis['hard_constraints']}")
        log.info(f"  - ソフト制約: {quality_analysis['soft_constraints']}")
        log.info(f"  - 選好: {quality_analysis['preferences']}")
        log.info(f"実行可能性: {quality_analysis['actionability_ratio']:.1%}")
        log.info(f"定量化率: {quality_analysis['quantification_ratio']:.1%}")
        log.info(f"高信頼度率: {quality_analysis['high_confidence_ratio']:.1%}")
        
        self.quality_metrics = quality_analysis
        return quality_analysis
    
    def analyze_inter_axis_relationships(self) -> List[Dict]:
        """軸間の関係性を分析"""
        log.info("=== 軸間関係性分析開始 ===")
        
        relationships = []
        
        # 重要な軸間関係のマッピング
        key_relationships = [
            (1, 7, "施設基準と法的要件"),
            (2, 8, "職員ルールと満足度"),
            (3, 4, "時間パターンと需要"),
            (4, 6, "需要とコスト効率"),
            (5, 7, "医療品質と法的基準"),
            (6, 11, "コスト効率とパフォーマンス"),
            (9, 11, "業務プロセスとパフォーマンス"),
            (10, 12, "リスク管理と戦略"),
        ]
        
        for axis1, axis2, relationship_type in key_relationships:
            if self.axis_results.get(axis1) and self.axis_results.get(axis2):
                # 両軸の制約を比較
                constraints1 = self._get_all_constraints(axis1)
                constraints2 = self._get_all_constraints(axis2)
                
                # 関連性スコア計算
                relationship_score = self._calculate_relationship_score(constraints1, constraints2)
                
                relationships.append({
                    'axis1': axis1,
                    'axis2': axis2,
                    'type': relationship_type,
                    'score': relationship_score,
                    'strength': 'strong' if relationship_score > 0.7 else 'medium' if relationship_score > 0.4 else 'weak'
                })
                
                log.info(f"軸{axis1}⇔軸{axis2} ({relationship_type}): スコア={relationship_score:.2f}")
        
        return relationships
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """包括的なMECE品質レポートを生成"""
        log.info("=== MECE品質レポート生成 ===")
        
        report = {
            'summary': {
                'total_axes': 12,
                'successful_axes': sum(1 for r in self.axis_results.values() if r),
                'total_overlaps': len(self.overlap_findings),
                'total_gaps': len(self.coverage_gaps),
                'overall_quality_score': 0
            },
            'mutual_exclusivity': {
                'overlaps': self.overlap_findings,
                'score': 1.0 - (len(self.overlap_findings) / 66) if len(self.overlap_findings) < 66 else 0  # 66 = C(12,2)
            },
            'collective_exhaustiveness': {
                'gaps': self.coverage_gaps,
                'score': 1.0 - (len(self.coverage_gaps) / 96) if len(self.coverage_gaps) < 96 else 0  # 96 = 12軸 × 8カテゴリー
            },
            'constraint_quality': self.quality_metrics,
            'recommendations': []
        }
        
        # 総合スコア計算
        me_score = report['mutual_exclusivity']['score']
        ce_score = report['collective_exhaustiveness']['score']
        quality_score = self.quality_metrics.get('actionability_ratio', 0) * 0.4 + \
                       self.quality_metrics.get('quantification_ratio', 0) * 0.3 + \
                       self.quality_metrics.get('high_confidence_ratio', 0) * 0.3
        
        report['summary']['overall_quality_score'] = (me_score + ce_score + quality_score) / 3
        
        # 推奨事項生成
        if me_score < 0.8:
            report['recommendations'].append("軸間の重複を削減し、相互排他性を向上させる")
        if ce_score < 0.8:
            report['recommendations'].append("カバレッジギャップを埋め、網羅性を向上させる")
        if quality_score < 0.7:
            report['recommendations'].append("制約の実行可能性と定量化を改善する")
        
        log.info(f"\n{'='*60}")
        log.info(f"MECE品質スコア: {report['summary']['overall_quality_score']:.1%}")
        log.info(f"  - 相互排他性: {me_score:.1%}")
        log.info(f"  - 網羅性: {ce_score:.1%}")
        log.info(f"  - 制約品質: {quality_score:.1%}")
        log.info(f"{'='*60}")
        
        return report
    
    # ヘルパーメソッド
    def _check_axis_overlap(self, axis1: int, axis2: int) -> List[Dict]:
        """2つの軸間の重複をチェック"""
        overlaps = []
        
        # 制約の類似性チェック
        constraints1 = self._get_all_constraints(axis1)
        constraints2 = self._get_all_constraints(axis2)
        
        for c1 in constraints1:
            for c2 in constraints2:
                similarity = self._calculate_constraint_similarity(c1, c2)
                if similarity > 0.8:  # 80%以上の類似性
                    overlaps.append({
                        'axis1': axis1,
                        'axis2': axis2,
                        'type': 'constraint_overlap',
                        'detail': f"{c1.get('type', 'unknown')} vs {c2.get('type', 'unknown')}",
                        'similarity': similarity
                    })
        
        return overlaps
    
    def _get_all_constraints(self, axis_num: int) -> List[Dict]:
        """指定軸の全制約を取得"""
        constraints = []
        if self.axis_results.get(axis_num):
            mr_data = self.axis_results[axis_num].get('machine_readable', {})
            for constraint_type in ['hard_constraints', 'soft_constraints', 'preferences']:
                if constraint_type in mr_data and isinstance(mr_data[constraint_type], list):
                    constraints.extend(mr_data[constraint_type])
        return constraints
    
    def _calculate_constraint_similarity(self, c1: Dict, c2: Dict) -> float:
        """2つの制約の類似度を計算"""
        # 簡易的な類似度計算（実際はより高度な手法を使用）
        if c1.get('type') == c2.get('type'):
            return 0.9
        if c1.get('category') == c2.get('category'):
            return 0.7
        return 0.0
    
    def _calculate_relationship_score(self, constraints1: List[Dict], constraints2: List[Dict]) -> float:
        """2つの軸の関係性スコアを計算"""
        if not constraints1 or not constraints2:
            return 0.0
        
        # 相互参照や依存関係の数をカウント
        references = 0
        for c1 in constraints1:
            for c2 in constraints2:
                if self._constraints_are_related(c1, c2):
                    references += 1
        
        max_possible = min(len(constraints1), len(constraints2))
        return min(references / max_possible, 1.0) if max_possible > 0 else 0.0
    
    def _constraints_are_related(self, c1: Dict, c2: Dict) -> bool:
        """2つの制約が関連しているかチェック"""
        # 簡易的な関連性チェック
        return any(keyword in str(c2) for keyword in str(c1).split() if len(keyword) > 3)
    
    def _is_actionable_constraint(self, constraint: Dict) -> bool:
        """制約が実行可能かチェック"""
        # 実行可能性の基準
        return all([
            constraint.get('type'),
            constraint.get('rule') or constraint.get('constraint'),
            constraint.get('confidence', 0) >= 0.5
        ])
    
    def _is_quantified_constraint(self, constraint: Dict) -> bool:
        """制約が定量化されているかチェック"""
        # 数値を含むかチェック
        constraint_str = str(constraint)
        return any(char.isdigit() for char in constraint_str)


def main():
    """メイン実行関数"""
    log.info("MECE品質深層検証テスト開始")
    log.info("="*60)
    
    verifier = MECEQualityVerifier()
    
    # 1. テストデータ生成
    test_df = verifier.create_comprehensive_test_data()
    
    # 2. 全軸の抽出実行
    axis_results = verifier.run_all_axes_extraction(test_df)
    
    # 3. 相互排他性検証
    overlaps = verifier.verify_mutual_exclusivity()
    
    # 4. 網羅性検証
    gaps = verifier.verify_collective_exhaustiveness()
    
    # 5. 制約品質分析
    quality = verifier.analyze_constraint_quality()
    
    # 6. 軸間関係性分析
    relationships = verifier.analyze_inter_axis_relationships()
    
    # 7. 総合レポート生成
    report = verifier.generate_comprehensive_report()
    
    # レポート保存
    with open('mece_quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    log.info("\n検証完了！レポートをmece_quality_report.jsonに保存しました。")
    
    return report


if __name__ == "__main__":
    main()