#!/usr/bin/env python3
"""
実行結果全テキスト出力システム
app.py、dash_app.py両方で使用可能
"""

import logging
import sys
import io
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

class ExecutionLogger:
    """実行結果を詳細にテキストファイルに記録するクラス"""
    
    def __init__(self, app_name: str = "unknown", log_dir: str = "execution_logs"):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # タイムスタンプ
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ログファイルパス
        self.execution_log_path = self.log_dir / f"execution_log_{app_name}_{self.timestamp}.txt"
        self.analysis_results_path = self.log_dir / f"analysis_results_{app_name}_{self.timestamp}.txt"
        self.error_report_path = self.log_dir / f"error_report_{app_name}_{self.timestamp}.txt"
        self.performance_path = self.log_dir / f"performance_report_{app_name}_{self.timestamp}.txt"
        
        # 実行データ格納
        self.execution_data = {
            "start_time": datetime.now(),
            "app_name": app_name,
            "steps": [],
            "errors": [],
            "warnings": [],
            "performance": {},
            "results": {}
        }
        
        # stdout/stderrキャプチャ設定
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.captured_output = io.StringIO()
        
        self._initialize_logging()
    
    def _initialize_logging(self):
        """ログ設定の初期化"""
        # 基本情報をファイルに記録
        with open(self.execution_log_path, 'w', encoding='utf-8') as f:
            f.write(f"実行ログ - {self.app_name}\n")
            f.write(f"開始時刻: {self.execution_data['start_time']}\n")
            f.write("="*80 + "\n\n")
    
    def start_capture(self):
        """stdout/stderrのキャプチャを開始"""
        sys.stdout = TeeOutput(self.original_stdout, self.captured_output)
        sys.stderr = TeeOutput(self.original_stderr, self.captured_output)
    
    def stop_capture(self):
        """stdout/stderrのキャプチャを停止"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def log_step(self, step_name: str, description: str = "", data: Dict[str, Any] = None):
        """実行ステップを記録"""
        timestamp = datetime.now()
        step_data = {
            "timestamp": timestamp,
            "step_name": step_name,
            "description": description,
            "data": data or {}
        }
        self.execution_data["steps"].append(step_data)
        
        # ファイルに即座に記録
        with open(self.execution_log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp.strftime('%H:%M:%S')}] ステップ: {step_name}\n")
            if description:
                f.write(f"  説明: {description}\n")
            if data:
                f.write(f"  データ: {json.dumps(data, ensure_ascii=False, indent=2)}\n")
            f.write("\n")
    
    def log_error(self, error: Exception, context: str = ""):
        """エラーを記録"""
        error_data = {
            "timestamp": datetime.now(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        self.execution_data["errors"].append(error_data)
        
        # エラーファイルに記録
        with open(self.error_report_path, 'a', encoding='utf-8') as f:
            f.write(f"エラー発生時刻: {error_data['timestamp']}\n")
            f.write(f"エラータイプ: {error_data['error_type']}\n")
            f.write(f"エラーメッセージ: {error_data['error_message']}\n")
            if context:
                f.write(f"コンテキスト: {context}\n")
            f.write(f"トレースバック:\n{error_data['traceback']}\n")
            f.write("="*80 + "\n\n")
    
    def log_warning(self, message: str, context: str = ""):
        """警告を記録"""
        warning_data = {
            "timestamp": datetime.now(),
            "message": message,
            "context": context
        }
        self.execution_data["warnings"].append(warning_data)
        
        with open(self.execution_log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{warning_data['timestamp'].strftime('%H:%M:%S')}] 警告: {message}\n")
            if context:
                f.write(f"  コンテキスト: {context}\n")
            f.write("\n")
    
    def log_performance(self, metric_name: str, value: float, unit: str = ""):
        """パフォーマンス情報を記録"""
        self.execution_data["performance"][metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now()
        }
        
        with open(self.performance_path, 'a', encoding='utf-8') as f:
            f.write(f"{metric_name}: {value} {unit}\n")
    
    def log_result(self, result_name: str, result_data: Any):
        """分析結果を記録"""
        self.execution_data["results"][result_name] = {
            "data": result_data,
            "timestamp": datetime.now()
        }
        
        with open(self.analysis_results_path, 'a', encoding='utf-8') as f:
            f.write(f"結果: {result_name}\n")
            f.write(f"時刻: {datetime.now()}\n")
            f.write(f"データ: {json.dumps(result_data, ensure_ascii=False, indent=2, default=str)}\n")
            f.write("="*80 + "\n\n")
    
    def finalize(self):
        """ログ記録を終了し、サマリーを生成"""
        self.stop_capture()
        
        end_time = datetime.now()
        duration = end_time - self.execution_data["start_time"]
        
        # 実行サマリーを生成
        summary_path = self.log_dir / f"execution_summary_{self.app_name}_{self.timestamp}.txt"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"実行サマリー - {self.app_name}\n")
            f.write("="*80 + "\n")
            f.write(f"開始時刻: {self.execution_data['start_time']}\n")
            f.write(f"終了時刻: {end_time}\n")
            f.write(f"実行時間: {duration}\n\n")
            
            f.write(f"実行ステップ数: {len(self.execution_data['steps'])}\n")
            f.write(f"エラー数: {len(self.execution_data['errors'])}\n")
            f.write(f"警告数: {len(self.execution_data['warnings'])}\n")
            f.write(f"結果数: {len(self.execution_data['results'])}\n\n")
            
            if self.execution_data['errors']:
                f.write("🚨 エラー一覧:\n")
                for i, error in enumerate(self.execution_data['errors'], 1):
                    f.write(f"  {i}. {error['error_type']}: {error['error_message']}\n")
                f.write("\n")
            
            if self.execution_data['warnings']:
                f.write("⚠️  警告一覧:\n")
                for i, warning in enumerate(self.execution_data['warnings'], 1):
                    f.write(f"  {i}. {warning['message']}\n")
                f.write("\n")
            
            f.write("📄 生成されたファイル:\n")
            f.write(f"  - 実行ログ: {self.execution_log_path.name}\n")
            f.write(f"  - 分析結果: {self.analysis_results_path.name}\n")
            f.write(f"  - エラーレポート: {self.error_report_path.name}\n")
            f.write(f"  - パフォーマンス: {self.performance_path.name}\n")
            f.write(f"  - サマリー: {summary_path.name}\n")
        
        # キャプチャした出力を保存
        captured_content = self.captured_output.getvalue()
        if captured_content:
            output_path = self.log_dir / f"captured_output_{self.app_name}_{self.timestamp}.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("キャプチャされた標準出力/エラー出力\n")
                f.write("="*80 + "\n")
                f.write(captured_content)
        
        return summary_path


class TeeOutput:
    """標準出力を分岐させるクラス"""
    
    def __init__(self, *outputs):
        self.outputs = outputs
    
    def write(self, text):
        for output in self.outputs:
            output.write(text)
    
    def flush(self):
        for output in self.outputs:
            if hasattr(output, 'flush'):
                output.flush()


# 使用例とヘルパー関数
def create_app_logger(app_name: str) -> ExecutionLogger:
    """アプリケーション用のExecutionLoggerを作成"""
    return ExecutionLogger(app_name)


def with_execution_logging(app_name: str):
    """デコレータ: 関数実行を自動でログ記録"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = create_app_logger(app_name)
            logger.start_capture()
            
            try:
                logger.log_step("function_start", f"関数 {func.__name__} の実行開始")
                result = func(*args, **kwargs)
                logger.log_step("function_end", f"関数 {func.__name__} の実行完了")
                logger.log_result("function_result", result)
                return result
            except Exception as e:
                logger.log_error(e, f"関数 {func.__name__} の実行中")
                raise
            finally:
                summary_path = logger.finalize()
                print(f"実行ログが保存されました: {summary_path}")
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # テスト用の実行例
    logger = create_app_logger("test")
    logger.start_capture()
    
    try:
        logger.log_step("test_start", "テスト開始")
        print("これはテスト出力です")
        logger.log_result("test_data", {"message": "テスト成功", "value": 123})
        logger.log_step("test_end", "テスト終了")
    except Exception as e:
        logger.log_error(e, "テスト実行中")
    finally:
        summary_path = logger.finalize()
        print(f"テストログ保存: {summary_path}")