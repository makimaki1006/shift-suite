#!/usr/bin/env python3
"""
shift_suite における休日除外問題の包括的調査
=====================================

データフロー全体を通じて休日データがヒートマップに表示される全ての可能性を特定し、
根本原因を明らかにします。

調査対象：
1. データ生成段階 (io_excel.py, heatmap.py)
2. 中間データ生成 (app.py: pre_aggregated_data.parquet)
3. dash_app.py での処理
4. データ集計・ピボット処理
5. キャッシュとファイル保存

"""

import pandas as pd
import numpy as np
import datetime as dt
from pathlib import Path
import logging
import json

# shift_suite モジュールをインポート
from shift_suite.tasks.utils import apply_rest_exclusion_filter, _parse_as_date, log
from shift_suite.tasks.heatmap import build_heatmap, _filter_work_records
from shift_suite.tasks.io_excel import ingest_excel

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HolidayExclusionAnalyzer:
    """休日除外問題の包括的分析クラス"""
    
    def __init__(self, excel_path: str):
        self.excel_path = Path(excel_path)
        self.findings = []
        
    def log_finding(self, stage: str, issue: str, data: dict = None):
        """調査結果を記録"""
        finding = {
            "stage": stage,
            "issue": issue,
            "timestamp": dt.datetime.now().isoformat(),
            "data": data or {}
        }
        self.findings.append(finding)
        log.warning(f"[{stage}] {issue}: {data}")

    def analyze_io_excel_stage(self):
        """1. io_excel.py でのデータ取り込み段階を調査"""
        log.info("=" * 60)
        log.info("1. データ取り込み段階の調査 (io_excel.py)")
        log.info("=" * 60)
        
        if not self.excel_path.exists():
            self.log_finding("IO_EXCEL", "テストExcelファイルが見つかりません", 
                           {"path": str(self.excel_path)})
            return None
        
        try:
            # io_excel.ingest_excel を実行
            long_df, work_types_df = ingest_excel(
                self.excel_path,
                shift_sheets=None,  # 全シート
                header_row=3,
                slot_minutes=30,
                year_month_cell_location="B1"
            )
            
            log.info(f"取り込み結果: {len(long_df)} レコード")
            
            # 休暇タイプの分布を調査
            if 'holiday_type' in long_df.columns:
                holiday_dist = long_df['holiday_type'].value_counts()
                log.info(f"休暇タイプ分布:\n{holiday_dist}")
                
                # 休暇レコードの詳細を分析
                non_work_records = long_df[long_df['holiday_type'] != '通常勤務']
                if not non_work_records.empty:
                    self.log_finding("IO_EXCEL", "休暇レコードが検出されました", {
                        "count": len(non_work_records),
                        "types": holiday_dist.to_dict(),
                        "sample_records": non_work_records.head(3).to_dict('records')
                    })
            
            # スタッフ名の分析 (休暇パターンを含む可能性)
            if 'staff' in long_df.columns:
                unique_staff = long_df['staff'].value_counts()
                suspicious_staff = unique_staff[unique_staff.index.str.contains('×|休|OFF|有|特', na=False, regex=True)]
                if not suspicious_staff.empty:
                    self.log_finding("IO_EXCEL", "疑わしいスタッフ名パターンを検出", {
                        "patterns": suspicious_staff.to_dict()
                    })
            
            # parsed_slots_count が0のレコードを調査
            if 'parsed_slots_count' in long_df.columns:
                zero_slots = long_df[long_df['parsed_slots_count'] <= 0]
                if not zero_slots.empty:
                    self.log_finding("IO_EXCEL", "勤務時間が0のレコードを検出", {
                        "count": len(zero_slots),
                        "sample": zero_slots.head(3).to_dict('records')
                    })
            
            return long_df
            
        except Exception as e:
            self.log_finding("IO_EXCEL", f"データ取り込みエラー: {str(e)}")
            return None

    def analyze_filter_work_records(self, long_df: pd.DataFrame):
        """2. _filter_work_records 関数の効果を調査"""
        log.info("=" * 60)
        log.info("2. _filter_work_records 関数の効果調査")
        log.info("=" * 60)
        
        if long_df is None or long_df.empty:
            return None
        
        original_count = len(long_df)
        filtered_df = _filter_work_records(long_df)
        filtered_count = len(filtered_df)
        
        excluded_count = original_count - filtered_count
        exclusion_rate = excluded_count / original_count if original_count > 0 else 0
        
        log.info(f"フィルタリング結果: {original_count} -> {filtered_count} ({excluded_count}件除外, {exclusion_rate:.1%})")
        
        if excluded_count > 0:
            # 除外されたレコードを分析
            excluded_df = long_df[~long_df.index.isin(filtered_df.index)]
            
            # 除外理由の分析
            exclusion_reasons = {}
            
            # holiday_type による除外
            if 'holiday_type' in excluded_df.columns:
                non_work = excluded_df[excluded_df['holiday_type'] != '通常勤務']
                if not non_work.empty:
                    exclusion_reasons['holiday_type'] = len(non_work)
            
            # parsed_slots_count による除外
            if 'parsed_slots_count' in excluded_df.columns:
                zero_slots = excluded_df[excluded_df['parsed_slots_count'] <= 0]
                if not zero_slots.empty:
                    exclusion_reasons['zero_slots'] = len(zero_slots)
            
            self.log_finding("FILTER_WORK_RECORDS", "レコード除外が実行されました", {
                "excluded_count": excluded_count,
                "exclusion_rate": f"{exclusion_rate:.1%}",
                "reasons": exclusion_reasons
            })
        
        return filtered_df

    def analyze_heatmap_building(self, long_df: pd.DataFrame):
        """3. build_heatmap でのピボット処理を調査"""
        log.info("=" * 60)
        log.info("3. build_heatmap でのピボット処理調査")
        log.info("=" * 60)
        
        if long_df is None or long_df.empty:
            return
        
        # テスト用の出力ディレクトリを作成
        test_out_dir = Path("test_heatmap_output")
        test_out_dir.mkdir(exist_ok=True)
        
        try:
            # build_heatmap を実行
            build_heatmap(
                long_df,
                test_out_dir,
                slot_minutes=30,
                ref_start_date_for_need=dt.date(2024, 11, 1),
                ref_end_date_for_need=dt.date(2024, 11, 30),
                need_statistic_method="平均値",
                need_remove_outliers=False,
                include_zero_days=True
            )
            
            # 生成されたファイルを確認
            heat_all_path = test_out_dir / "heat_ALL.parquet"
            if heat_all_path.exists():
                heat_df = pd.read_parquet(heat_all_path)
                log.info(f"heat_ALL.parquet 生成成功: {heat_df.shape}")
                
                # 日付列の分析
                date_columns = [col for col in heat_df.columns if _parse_as_date(col) is not None]
                log.info(f"日付列数: {len(date_columns)}")
                
                # 0以外の値があるかチェック
                non_zero_data = {}
                for col in date_columns:
                    non_zero_count = (heat_df[col] > 0).sum()
                    if non_zero_count > 0:
                        non_zero_data[col] = int(non_zero_count)
                
                if non_zero_data:
                    self.log_finding("BUILD_HEATMAP", "ヒートマップに勤務データが含まれています", {
                        "non_zero_columns": non_zero_data
                    })
                else:
                    self.log_finding("BUILD_HEATMAP", "ヒートマップが全て0になっています")
                    
        except Exception as e:
            self.log_finding("BUILD_HEATMAP", f"ヒートマップ作成エラー: {str(e)}")

    def analyze_pre_aggregated_data_generation(self, long_df: pd.DataFrame):
        """4. pre_aggregated_data.parquet 生成プロセスを調査"""
        log.info("=" * 60)
        log.info("4. pre_aggregated_data.parquet 生成プロセス調査")
        log.info("=" * 60)
        
        if long_df is None or long_df.empty:
            return
        
        # app.pyの処理を模擬的に実行
        try:
            # 日時情報を追加
            long_df['time'] = pd.to_datetime(long_df['ds'], errors='coerce').dt.strftime('%H:%M')
            long_df['date_lbl'] = pd.to_datetime(long_df['ds'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # 有効なデータのみを選択
            valid_df = long_df.dropna(subset=['time', 'date_lbl', 'staff', 'role'])
            
            # 全ての組み合わせを作成
            all_combinations = []
            for date_lbl in sorted(valid_df['date_lbl'].unique()):
                for time_slot in sorted(valid_df['time'].unique()):
                    for role in sorted(valid_df['role'].unique()):
                        for employment in sorted(valid_df['employment'].unique() if 'employment' in valid_df.columns else ['正社員']):
                            all_combinations.append({
                                'date_lbl': date_lbl,
                                'time': time_slot,
                                'role': role,
                                'employment': employment
                            })
            
            all_combinations_df = pd.DataFrame(all_combinations)
            log.info(f"全組み合わせ: {len(all_combinations_df)} レコード")
            
            # 実際のスタッフ数をカウント
            staff_counts = valid_df.drop_duplicates(subset=['date_lbl', 'time', 'staff']).groupby(
                ['date_lbl', 'time', 'role', 'employment'], observed=True
            ).size().reset_index(name='staff_count')
            
            # 組み合わせにスタッフ数をマージ
            pre_aggregated_df = pd.merge(
                all_combinations_df,
                staff_counts,
                on=['date_lbl', 'time', 'role', 'employment'],
                how='left'
            )
            pre_aggregated_df['staff_count'] = pre_aggregated_df['staff_count'].fillna(0).astype(int)
            
            log.info(f"pre_aggregated_data 作成完了: {len(pre_aggregated_df)} レコード")
            
            # 0でないスタッフ数の分析
            non_zero_records = pre_aggregated_df[pre_aggregated_df['staff_count'] > 0]
            log.info(f"勤務データありレコード: {len(non_zero_records)}")
            
            # 日付別の勤務状況
            date_stats = non_zero_records.groupby('date_lbl')['staff_count'].sum().sort_index()
            log.info(f"日付別勤務人数サマリー (上位10日):\n{date_stats.head(10)}")
            
            # 休暇除外フィルタの効果をテスト
            log.info("\n休暇除外フィルタの効果をテスト...")
            filtered_pre_aggregated = apply_rest_exclusion_filter(pre_aggregated_df, "pre_aggregated_test", for_display=False, exclude_leave_records=False)
            
            excluded_in_pre_agg = len(pre_aggregated_df) - len(filtered_pre_aggregated)
            if excluded_in_pre_agg > 0:
                self.log_finding("PRE_AGGREGATED", "pre_aggregated_data で追加除外が発生", {
                    "excluded_count": excluded_in_pre_agg
                })
            
            # テストファイルとして保存
            test_path = Path("test_pre_aggregated_data.parquet")
            pre_aggregated_df.to_parquet(test_path, index=False)
            log.info(f"テスト用 pre_aggregated_data を保存: {test_path}")
            
            return pre_aggregated_df
            
        except Exception as e:
            self.log_finding("PRE_AGGREGATED", f"pre_aggregated_data 生成エラー: {str(e)}")
            return None

    def analyze_dashboard_processing(self, pre_aggregated_df: pd.DataFrame):
        """5. dash_app.py でのヒートマップ生成処理を調査"""
        log.info("=" * 60)
        log.info("5. dash_app.py でのヒートマップ生成処理調査")
        log.info("=" * 60)
        
        if pre_aggregated_df is None or pre_aggregated_df.empty:
            return
        
        # dash_app.py の update_comparison_heatmaps と同様の処理を模擬
        try:
            # 休暇除外フィルタを適用
            filtered_df = apply_rest_exclusion_filter(pre_aggregated_df.copy(), "dashboard_test", for_display=True, exclude_leave_records=False)
            
            # 追加の0スタッフフィルタ
            if 'staff_count' in filtered_df.columns:
                before_count = len(filtered_df)
                filtered_df = filtered_df[filtered_df['staff_count'] > 0]
                after_count = len(filtered_df)
                
                if before_count != after_count:
                    self.log_finding("DASHBOARD", "ダッシュボードで追加フィルタリングが実行されました", {
                        "before": before_count,
                        "after": after_count,
                        "excluded": before_count - after_count
                    })
            
            # ピボットテーブル作成（全体）
            if not filtered_df.empty:
                heatmap_df = filtered_df.sort_values('date_lbl').pivot_table(
                    index='time',
                    columns='date_lbl',
                    values='staff_count',
                    aggfunc='sum',
                    fill_value=0
                )
                
                log.info(f"ダッシュボード用ヒートマップ作成: {heatmap_df.shape}")
                
                # 非ゼロデータの確認
                non_zero_values = (heatmap_df > 0).sum().sum()
                total_values = heatmap_df.size
                
                log.info(f"非ゼロ値: {non_zero_values}/{total_values} ({non_zero_values/total_values:.1%})")
                
                if non_zero_values == 0:
                    self.log_finding("DASHBOARD", "ダッシュボードヒートマップが全て0になりました")
                else:
                    # 日別データサマリー
                    daily_totals = heatmap_df.sum()
                    working_days = daily_totals[daily_totals > 0]
                    
                    self.log_finding("DASHBOARD", "ダッシュボードヒートマップにデータが含まれています", {
                        "working_days": len(working_days),
                        "total_days": len(daily_totals),
                        "sample_working_days": working_days.head(5).to_dict()
                    })
                
                # テスト保存
                heatmap_df.to_parquet("test_dashboard_heatmap.parquet")
                log.info("テスト用ダッシュボードヒートマップを保存")
                
        except Exception as e:
            self.log_finding("DASHBOARD", f"ダッシュボード処理エラー: {str(e)}")

    def generate_report(self):
        """調査結果レポートを生成"""
        log.info("=" * 60)
        log.info("包括的調査結果レポート")
        log.info("=" * 60)
        
        # 問題の重要度別に分類
        critical_issues = []
        warnings = []
        info = []
        
        for finding in self.findings:
            if "エラー" in finding['issue'] or "全て0" in finding['issue']:
                critical_issues.append(finding)
            elif "除外" in finding['issue'] or "検出" in finding['issue']:
                warnings.append(finding)
            else:
                info.append(finding)
        
        report = {
            "summary": {
                "total_findings": len(self.findings),
                "critical_issues": len(critical_issues),
                "warnings": len(warnings),
                "info": len(info)
            },
            "critical_issues": critical_issues,
            "warnings": warnings,
            "information": info,
            "analysis_timestamp": dt.datetime.now().isoformat()
        }
        
        # JSONレポート保存
        report_path = Path("holiday_exclusion_analysis_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        log.info(f"詳細レポートを保存: {report_path}")
        
        # サマリーを表示
        log.info(f"調査完了: {len(self.findings)}件の発見事項")
        log.info(f"  重要な問題: {len(critical_issues)}件")
        log.info(f"  警告: {len(warnings)}件")
        log.info(f"  情報: {len(info)}件")
        
        return report

    def run_comprehensive_analysis(self):
        """包括的な調査を実行"""
        log.info("shift_suite 休日除外問題の包括的調査を開始します...")
        
        # 1. データ取り込み段階
        long_df = self.analyze_io_excel_stage()
        
        if long_df is not None:
            # 2. フィルタリング段階
            filtered_df = self.analyze_filter_work_records(long_df)
            
            # 3. ヒートマップ構築段階
            self.analyze_heatmap_building(long_df)
            
            # 4. 事前集計データ生成段階
            pre_aggregated_df = self.analyze_pre_aggregated_data_generation(long_df)
            
            # 5. ダッシュボード処理段階
            if pre_aggregated_df is not None:
                self.analyze_dashboard_processing(pre_aggregated_df)
        
        # レポート生成
        return self.generate_report()


def main():
    """メイン実行関数"""
    # 利用可能なテストファイルを探す
    test_files = [
        "デイ_テスト用データ_休日精緻.xlsx",
        "ショート_テスト用データ.xlsx", 
        "勤務表　勤務時間_トライアル.xlsx"
    ]
    
    test_file = None
    for file_name in test_files:
        if Path(file_name).exists():
            test_file = file_name
            break
    
    if not test_file:
        print("テスト用Excelファイルが見つかりません。")
        print("以下のファイルのいずれかを配置してください:")
        for file_name in test_files:
            print(f"  - {file_name}")
        return
    
    print(f"テストファイル: {test_file}")
    
    # 包括的調査を実行
    analyzer = HolidayExclusionAnalyzer(test_file)
    report = analyzer.run_comprehensive_analysis()
    
    print("\n" + "="*80)
    print("調査完了! 詳細は以下のファイルをご確認ください:")
    print("- holiday_exclusion_analysis_report.json")
    print("- test_heatmap_output/")
    print("- test_pre_aggregated_data.parquet")
    print("- test_dashboard_heatmap.parquet")
    print("="*80)


if __name__ == "__main__":
    main()