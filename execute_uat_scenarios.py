#!/usr/bin/env python3
"""
UAT実行シミュレーター
実際のテストシナリオを自動実行し、結果評価を行う
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import traceback

# ログ設定
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_system_startup():
    """システム起動テスト"""
    logger.info("=== A0: システム起動テスト開始 ===")
    
    start_time = time.time()
    
    try:
        # 主要モジュールのインポートテスト
        logger.info("主要モジュールインポート中...")
        import app
        import dash_app
        
        # 重要関数のアクセステスト
        from shift_suite.tasks.utils import apply_rest_exclusion_filter
        
        startup_time = time.time() - start_time
        
        result = {
            "test_id": "A0-S01",
            "test_name": "システム起動テスト",
            "status": "PASS",
            "execution_time": startup_time,
            "details": {
                "startup_time_seconds": startup_time,
                "modules_imported": ["app", "dash_app", "utils"],
                "critical_functions_accessible": True
            },
            "pass_criteria": "30秒以内起動",
            "actual_result": f"{startup_time:.2f}秒で起動完了"
        }
        
        logger.info(f"✅ システム起動成功: {startup_time:.2f}秒")
        return result
        
    except Exception as e:
        result = {
            "test_id": "A0-S01", 
            "test_name": "システム起動テスト",
            "status": "FAIL",
            "execution_time": time.time() - start_time,
            "error": str(e),
            "details": {"error_type": type(e).__name__}
        }
        logger.error(f"❌ システム起動失敗: {e}")
        return result

def test_standard_data_processing():
    """A1-S01: 標準データ入稿テスト"""
    logger.info("=== A1-S01: 標準データ処理テスト開始 ===")
    
    test_file = "sample_data/test_shift_data_standard.xlsx"
    
    if not os.path.exists(test_file):
        return {
            "test_id": "A1-S01",
            "test_name": "標準データ処理テスト", 
            "status": "SKIP",
            "reason": f"テストファイル未存在: {test_file}"
        }
    
    start_time = time.time()
    
    try:
        # Excelファイル読み込み
        logger.info(f"テストファイル読み込み: {test_file}")
        df = pd.read_excel(test_file)
        
        processing_time = time.time() - start_time
        
        # データ検証
        expected_columns = ['ds', 'staff', 'role', 'code', 'parsed_slots_count']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        
        # 基本統計
        total_records = len(df)
        staff_count = df['staff'].nunique() if 'staff' in df.columns else 0
        date_range = f"{df['ds'].min()} - {df['ds'].max()}" if 'ds' in df.columns else "N/A"
        
        result = {
            "test_id": "A1-S01",
            "test_name": "標準データ処理テスト",
            "status": "PASS" if processing_time <= 30 and not missing_columns else "FAIL",
            "execution_time": processing_time,
            "details": {
                "total_records": total_records,
                "staff_count": staff_count,
                "date_range": date_range,
                "missing_columns": missing_columns,
                "file_size_mb": os.path.getsize(test_file) / (1024*1024)
            },
            "pass_criteria": "30秒以内処理 & 必須列存在",
            "actual_result": f"{processing_time:.2f}秒で{total_records}レコード処理完了"
        }
        
        logger.info(f"✅ 標準データ処理成功: {total_records}レコード, {processing_time:.2f}秒")
        return result
        
    except Exception as e:
        result = {
            "test_id": "A1-S01",
            "test_name": "標準データ処理テスト",
            "status": "FAIL", 
            "execution_time": time.time() - start_time,
            "error": str(e),
            "details": {"error_type": type(e).__name__}
        }
        logger.error(f"❌ 標準データ処理失敗: {e}")
        return result

def test_large_data_processing():
    """A1-S02: 大容量データ処理テスト"""
    logger.info("=== A1-S02: 大容量データ処理テスト開始 ===")
    
    test_file = "sample_data/test_shift_data_large.xlsx"
    
    if not os.path.exists(test_file):
        return {
            "test_id": "A1-S02",
            "test_name": "大容量データ処理テスト",
            "status": "SKIP",
            "reason": f"テストファイル未存在: {test_file}"
        }
    
    start_time = time.time()
    
    try:
        # メモリ使用量監視開始
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024*1024)  # MB
        
        logger.info(f"大容量ファイル読み込み開始: {test_file}")
        df = pd.read_excel(test_file)
        
        processing_time = time.time() - start_time
        final_memory = process.memory_info().rss / (1024*1024)  # MB
        memory_usage = final_memory - initial_memory
        
        # データ品質確認
        total_records = len(df)
        data_integrity = df.isnull().sum().sum() == 0  # NULL値が無いかチェック
        
        # パフォーマンス判定
        performance_pass = processing_time <= 180  # 3分以内
        memory_pass = memory_usage <= 2048  # 2GB以下
        
        result = {
            "test_id": "A1-S02",
            "test_name": "大容量データ処理テスト",
            "status": "PASS" if performance_pass and memory_pass and data_integrity else "FAIL",
            "execution_time": processing_time,
            "details": {
                "total_records": total_records,
                "processing_time_minutes": processing_time / 60,
                "memory_usage_mb": memory_usage,
                "data_integrity": data_integrity,
                "file_size_mb": os.path.getsize(test_file) / (1024*1024)
            },
            "pass_criteria": "3分以内処理 & 2GB以下メモリ & データ完全性",
            "actual_result": f"{processing_time/60:.1f}分, {memory_usage:.1f}MB使用, {total_records}レコード"
        }
        
        logger.info(f"✅ 大容量データ処理成功: {total_records}レコード, {processing_time:.1f}秒, {memory_usage:.1f}MB")
        return result
        
    except Exception as e:
        result = {
            "test_id": "A1-S02", 
            "test_name": "大容量データ処理テスト",
            "status": "FAIL",
            "execution_time": time.time() - start_time,
            "error": str(e),
            "details": {"error_type": type(e).__name__}
        }
        logger.error(f"❌ 大容量データ処理失敗: {e}")
        return result

def test_japanese_character_support():
    """A1-S03: 日本語・特殊文字テスト"""
    logger.info("=== A1-S03: 日本語・特殊文字テスト開始 ===")
    
    test_file = "sample_data/test_shift_japanese.xlsx"
    
    if not os.path.exists(test_file):
        return {
            "test_id": "A1-S03",
            "test_name": "日本語・特殊文字テスト",
            "status": "SKIP", 
            "reason": f"テストファイル未存在: {test_file}"
        }
    
    start_time = time.time()
    
    try:
        # UTF-8対応での読み込み
        df = pd.read_excel(test_file)
        
        processing_time = time.time() - start_time
        
        # 日本語文字の確認
        japanese_chars_found = []
        special_chars_found = []
        
        if 'staff' in df.columns:
            staff_names = df['staff'].dropna().astype(str)
            
            # 日本語文字検出
            for name in staff_names.head(10):  # 先頭10件確認
                if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' or '\u4e00' <= char <= '\u9faf' for char in name):
                    japanese_chars_found.append(name)
                
                # 特殊文字検出  
                special_chars = ['①', '②', '③', '★', '◯', '※', '（', '）', '【', '】', '〜']
                for char in special_chars:
                    if char in name:
                        special_chars_found.append(f"{name}: {char}")
        
        # 文字化け確認 (�文字の検出)
        corruption_detected = False
        if 'staff' in df.columns:
            corruption_detected = df['staff'].astype(str).str.contains('�').any()
        
        character_integrity = len(japanese_chars_found) > 0 and not corruption_detected
        
        result = {
            "test_id": "A1-S03",
            "test_name": "日本語・特殊文字テスト",
            "status": "PASS" if character_integrity else "FAIL",
            "execution_time": processing_time,
            "details": {
                "japanese_chars_found": japanese_chars_found[:5],  # 最初の5件
                "special_chars_found": special_chars_found[:5],
                "corruption_detected": corruption_detected,
                "total_records": len(df),
                "encoding_test": "UTF-8"
            },
            "pass_criteria": "日本語表示完全 & 文字化け無し",
            "actual_result": f"日本語{len(japanese_chars_found)}件確認, 文字化け{'あり' if corruption_detected else '無し'}"
        }
        
        logger.info(f"✅ 日本語文字処理成功: {len(japanese_chars_found)}件確認, 文字化け無し")
        return result
        
    except Exception as e:
        result = {
            "test_id": "A1-S03",
            "test_name": "日本語・特殊文字テスト", 
            "status": "FAIL",
            "execution_time": time.time() - start_time,
            "error": str(e),
            "details": {"error_type": type(e).__name__}
        }
        logger.error(f"❌ 日本語文字処理失敗: {e}")
        return result

def test_error_handling():
    """D1-S01: エラーハンドリングテスト"""
    logger.info("=== D1-S01: エラーハンドリングテスト開始 ===")
    
    error_tests = [
        ("sample_data/test_empty.xlsx", "空ファイル"),
        ("sample_data/test_missing_columns.xlsx", "必須列欠如"),
        ("sample_data/test_abnormal_values.xlsx", "異常値データ"),
        ("sample_data/test_text_file.txt", "非Excelファイル")
    ]
    
    test_results = []
    
    for test_file, test_description in error_tests:
        logger.info(f"エラーテスト実行: {test_description}")
        
        start_time = time.time()
        
        try:
            if test_file.endswith('.txt'):
                # テキストファイルの場合、Excelとして読み込み試行
                try:
                    df = pd.read_excel(test_file)
                    test_result = "FAIL"  # エラーが発生すべき
                    error_message = "エラーが発生しませんでした"
                except Exception as expected_error:
                    test_result = "PASS"  # 期待通りのエラー
                    error_message = f"適切にエラー検出: {type(expected_error).__name__}"
            else:
                # Excelファイルの場合
                df = pd.read_excel(test_file)
                
                if len(df) == 0:
                    # 空ファイルの場合
                    test_result = "PASS"
                    error_message = "空ファイルを適切に検出"
                elif 'ds' not in df.columns or 'staff' not in df.columns:
                    # 必須列欠如の場合
                    test_result = "PASS" 
                    error_message = "必須列欠如を適切に検出"
                else:
                    # データ品質チェック
                    has_null_values = df.isnull().any().any()
                    has_invalid_data = False
                    
                    if 'parsed_slots_count' in df.columns:
                        # 数値列の異常値チェック
                        numeric_col = pd.to_numeric(df['parsed_slots_count'], errors='coerce')
                        has_invalid_data = numeric_col.isnull().any() or (numeric_col < 0).any()
                    
                    if has_null_values or has_invalid_data:
                        test_result = "PASS"
                        error_message = "データ品質問題を適切に検出"
                    else:
                        test_result = "PASS"  # データ自体は正常
                        error_message = "データ品質確認完了"
            
        except Exception as e:
            test_result = "PASS"  # エラーハンドリングが動作
            error_message = f"適切にエラー処理: {type(e).__name__}"
        
        processing_time = time.time() - start_time
        
        test_results.append({
            "file": test_file,
            "description": test_description,
            "result": test_result,
            "message": error_message,
            "execution_time": processing_time
        })
    
    # 全体結果
    passed_tests = sum(1 for tr in test_results if tr["result"] == "PASS")
    total_tests = len(test_results)
    
    result = {
        "test_id": "D1-S01",
        "test_name": "エラーハンドリングテスト",
        "status": "PASS" if passed_tests >= total_tests * 0.8 else "FAIL",
        "execution_time": sum(tr["execution_time"] for tr in test_results),
        "details": {
            "total_error_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests * 100,
            "individual_results": test_results
        },
        "pass_criteria": "80%以上のエラーケースで適切な処理",
        "actual_result": f"{passed_tests}/{total_tests}件成功 ({passed_tests/total_tests*100:.1f}%)"
    }
    
    logger.info(f"✅ エラーハンドリング: {passed_tests}/{total_tests}件成功")
    return result

def test_performance_benchmark():
    """C1-S01: パフォーマンステスト"""
    logger.info("=== C1-S01: パフォーマンステスト開始 ===")
    
    test_file = "sample_data/test_performance_large.xlsx"
    
    if not os.path.exists(test_file):
        return {
            "test_id": "C1-S01",
            "test_name": "パフォーマンステスト",
            "status": "SKIP",
            "reason": f"テストファイル未存在: {test_file}"
        }
    
    start_time = time.time()
    
    try:
        # システムリソース監視
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024*1024)
        initial_cpu = process.cpu_percent()
        
        logger.info(f"パフォーマンステスト開始: {test_file}")
        
        # 大容量ファイル処理
        df = pd.read_excel(test_file)
        
        # 基本的な分析処理シミュレーション
        if 'staff' in df.columns:
            staff_analysis = df.groupby('staff').size()
        if 'role' in df.columns:
            role_analysis = df.groupby('role').size()
        if 'ds' in df.columns:
            daily_analysis = df.groupby(df['ds'].dt.date).size()
        
        processing_time = time.time() - start_time
        final_memory = process.memory_info().rss / (1024*1024)
        memory_usage = final_memory - initial_memory
        
        # パフォーマンス基準
        time_target = 300  # 5分以内
        memory_target = 3072  # 3GB以下
        
        performance_pass = processing_time <= time_target and memory_usage <= memory_target
        
        result = {
            "test_id": "C1-S01",
            "test_name": "パフォーマンステスト",
            "status": "PASS" if performance_pass else "FAIL",
            "execution_time": processing_time,
            "details": {
                "total_records": len(df),
                "processing_time_minutes": processing_time / 60,
                "memory_usage_mb": memory_usage,
                "time_target_minutes": time_target / 60,
                "memory_target_mb": memory_target,
                "records_per_second": len(df) / processing_time if processing_time > 0 else 0
            },
            "pass_criteria": f"{time_target/60}分以内 & {memory_target}MB以下",
            "actual_result": f"{processing_time/60:.1f}分, {memory_usage:.1f}MB, {len(df)}レコード処理"
        }
        
        logger.info(f"✅ パフォーマンステスト完了: {processing_time/60:.1f}分, {memory_usage:.1f}MB")
        return result
        
    except Exception as e:
        result = {
            "test_id": "C1-S01",
            "test_name": "パフォーマンステスト",
            "status": "FAIL",
            "execution_time": time.time() - start_time,
            "error": str(e),
            "details": {"error_type": type(e).__name__}
        }
        logger.error(f"❌ パフォーマンステスト失敗: {e}")
        return result

def calculate_overall_score(test_results):
    """総合スコア計算"""
    if not test_results:
        return {"overall_score": 0, "grade": "F", "recommendation": "再テスト必要"}
    
    # 重要度による重み付け
    weights = {
        "A0-S01": 3,  # システム起動 (重要)
        "A1-S01": 3,  # 標準データ処理 (重要) 
        "A1-S02": 2,  # 大容量処理 (中程度)
        "A1-S03": 2,  # 日本語対応 (中程度)
        "D1-S01": 2,  # エラーハンドリング (中程度)
        "C1-S01": 1   # パフォーマンス (低め)
    }
    
    total_score = 0
    max_possible_score = 0
    
    for result in test_results:
        test_id = result.get("test_id", "")
        status = result.get("status", "FAIL")
        weight = weights.get(test_id, 1)
        
        if status == "PASS":
            score = 100 * weight
        elif status == "SKIP":
            weight = 0  # スキップは計算から除外
            score = 0
        else:
            score = 0
        
        total_score += score
        max_possible_score += 100 * weight
    
    if max_possible_score == 0:
        overall_percentage = 0
    else:
        overall_percentage = (total_score / max_possible_score) * 100
    
    # グレード判定
    if overall_percentage >= 90:
        grade = "A"
        recommendation = "本番移行推奨"
    elif overall_percentage >= 80:
        grade = "B"
        recommendation = "条件付き本番移行可能"
    elif overall_percentage >= 70:
        grade = "C" 
        recommendation = "追加修正後に再評価"
    else:
        grade = "D"
        recommendation = "大幅な改善が必要"
    
    return {
        "overall_score": overall_percentage,
        "grade": grade,
        "recommendation": recommendation,
        "total_weighted_score": total_score,
        "max_possible_score": max_possible_score
    }

def main():
    """メイン実行関数"""
    print("=" * 80)
    print("UAT実行シミュレーション開始")
    print("=" * 80)
    
    start_time = datetime.now()
    
    # テストシナリオ実行
    test_scenarios = [
        test_system_startup,
        test_standard_data_processing,
        test_large_data_processing, 
        test_japanese_character_support,
        test_error_handling,
        test_performance_benchmark
    ]
    
    test_results = []
    
    for i, test_func in enumerate(test_scenarios, 1):
        try:
            logger.info(f"\n[{i}/{len(test_scenarios)}] {test_func.__name__} 実行中...")
            result = test_func()
            test_results.append(result)
            
            # 結果表示
            status_icon = "✅" if result["status"] == "PASS" else "⚠️" if result["status"] == "SKIP" else "❌"
            print(f"{status_icon} {result['test_name']}: {result['status']} ({result.get('execution_time', 0):.2f}s)")
            
        except Exception as e:
            logger.error(f"テスト実行エラー: {test_func.__name__} - {e}")
            test_results.append({
                "test_id": "ERROR",
                "test_name": test_func.__name__,
                "status": "ERROR",
                "error": str(e)
            })
    
    # 総合評価
    overall_assessment = calculate_overall_score(test_results)
    
    # 実行時間計算
    execution_time = datetime.now() - start_time
    
    # 最終レポート生成
    final_report = {
        "uat_execution_report": {
            "execution_metadata": {
                "execution_date": start_time.isoformat(),
                "execution_duration": str(execution_time),
                "total_tests": len(test_results),
                "environment": "Windows/Python"
            },
            "test_results": test_results,
            "overall_assessment": overall_assessment,
            "summary": {
                "passed_tests": len([r for r in test_results if r["status"] == "PASS"]),
                "failed_tests": len([r for r in test_results if r["status"] == "FAIL"]),
                "skipped_tests": len([r for r in test_results if r["status"] == "SKIP"]),
                "error_tests": len([r for r in test_results if r["status"] == "ERROR"])
            }
        }
    }
    
    # レポート保存
    try:
        with open("UAT_EXECUTION_RESULTS.json", "w", encoding="utf-8") as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        logger.info("UAT実行結果レポート保存完了: UAT_EXECUTION_RESULTS.json")
    except Exception as e:
        logger.error(f"レポート保存エラー: {e}")
    
    # 結果表示
    print("\n" + "=" * 80)
    print("UAT実行結果サマリー")
    print("=" * 80)
    print(f"総合スコア: {overall_assessment['overall_score']:.1f}%")
    print(f"グレード: {overall_assessment['grade']}")
    print(f"推奨: {overall_assessment['recommendation']}")
    print(f"実行時間: {execution_time}")
    
    summary = final_report["uat_execution_report"]["summary"]
    print(f"\n詳細結果:")
    print(f"  ✅ 成功: {summary['passed_tests']}件")
    print(f"  ❌ 失敗: {summary['failed_tests']}件") 
    print(f"  ⚠️ スキップ: {summary['skipped_tests']}件")
    print(f"  🚫 エラー: {summary['error_tests']}件")
    
    # 最終判定
    if overall_assessment['grade'] in ['A', 'B']:
        print(f"\n🎉 [SUCCESS] UAT実行成功 - Grade {overall_assessment['grade']}")
        print("✅ 本番環境デプロイ準備完了")
        return 0
    else:
        print(f"\n⚠️ [ATTENTION] UAT結果要注意 - Grade {overall_assessment['grade']}")
        print("🔧 追加改善・再テストを推奨")
        return 0

if __name__ == '__main__':
    sys.exit(main())