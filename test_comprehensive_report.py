#!/usr/bin/env python3
"""
包括レポート生成器のテストスクリプト
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from shift_suite.tasks.comprehensive_report_generator import generate_comprehensive_report

def create_test_data():
    """テスト用のシフトデータと分析結果を生成"""
    
    # テスト用の長期シフトデータを作成
    start_date = datetime.now() - timedelta(days=90)  # 3ヶ月前
    dates = pd.date_range(start_date, periods=90, freq='30min')
    
    staff_names = ['田中', '佐藤', '鈴木', '高橋', '伊藤', '渡辺', '山本', '中村', '小林', '加藤']
    roles = ['介護職員', '看護師', '生活相談員']
    
    # 長期データフレーム
    long_df = pd.DataFrame({
        'ds': np.tile(dates, len(staff_names) // 3),
        'staff': np.repeat(staff_names[:len(dates) * len(staff_names) // len(dates) // 3], len(dates)),
        'role': np.random.choice(roles, size=len(dates) * len(staff_names) // 3),
        'code': np.random.choice(['早番', '日勤', '遅番', '夜勤', '休み'], size=len(dates) * len(staff_names) // 3)
    })
    
    # 分析結果データを作成
    analysis_results = {}
    
    # 不足分析結果
    analysis_results['shortage_summary'] = pd.DataFrame({
        'time_slot': ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'],
        'lack': [2.5, 1.8, 0.5, 1.2, 3.1, 2.0, 1.5],
        'excess': [0.2, 0.5, 1.8, 0.8, 0.1, 0.3, 0.7]
    })
    
    # 疲労度分析結果
    analysis_results['fatigue_score'] = pd.DataFrame({
        'staff': staff_names,
        'fatigue_score': np.random.uniform(30, 90, len(staff_names))
    })
    
    # 公平性分析結果
    analysis_results['fairness_after'] = pd.DataFrame({
        'staff': staff_names,
        'night_ratio': np.random.uniform(0.15, 0.35, len(staff_names)),
        'unfairness_score': np.random.uniform(0.01, 0.15, len(staff_names))
    })
    
    return long_df, analysis_results

def test_comprehensive_report():
    """包括レポート生成のテスト"""
    print("包括レポート生成器のテストを開始します...")
    
    # テスト用の一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        try:
            # テストデータを作成
            long_df, analysis_results = create_test_data()
            print(f"テストデータ作成完了: {len(long_df)}行のシフトデータ")
            
            # 包括レポートを生成
            report_path = generate_comprehensive_report(
                long_df=long_df,
                analysis_results=analysis_results,
                output_dir=output_dir
            )
            
            # 結果を確認
            if report_path and report_path.exists():
                print(f"✅ 包括レポート生成成功: {report_path}")
                print(f"ファイルサイズ: {report_path.stat().st_size} bytes")
                
                # レポートの内容をプレビュー
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print("\n--- レポート内容プレビュー（最初の1000文字）---")
                    print(content[:1000])
                    print("..." if len(content) > 1000 else "")
                    print("--- プレビュー終了 ---\n")
                
                return True
            else:
                print("❌ 包括レポート生成失敗: ファイルが作成されませんでした")
                return False
                
        except Exception as e:
            print(f"❌ テスト中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_comprehensive_report()
    if success:
        print("🎉 テスト成功！包括レポート生成器は正常に動作します。")
    else:
        print("💥 テスト失敗！問題を確認してください。")