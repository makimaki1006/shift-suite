# processing_monitor.py - データ処理進捗監視モジュール
"""
データ前処理から分析までの進捗をリアルタイム監視
ユーザーに処理状況を分かりやすく表示
"""

import logging
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
from datetime import datetime

# ログ設定
log = logging.getLogger(__name__)

class ProcessingStage(Enum):
    """処理段階の定義"""
    UPLOAD = "upload"
    VALIDATION = "validation"
    EXTRACTION = "extraction"
    PREPROCESSING = "preprocessing"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class ProcessingStep:
    """個別処理ステップの情報"""
    name: str
    description: str
    icon: str
    estimated_duration: float  # 秒
    actual_duration: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: int = 0  # 0-100
    status: str = "pending"  # pending, running, completed, failed
    error_message: Optional[str] = None

class ProcessingMonitor:
    """データ処理進捗の監視・管理クラス"""
    
    def __init__(self):
        self.current_stage = ProcessingStage.UPLOAD
        self.steps: Dict[str, ProcessingStep] = {}
        self.overall_progress = 0
        self.start_time = None
        self.is_running = False
        self.callbacks: List[Callable] = []
        self._lock = threading.Lock()
        
        # 標準的な処理ステップを定義
        self._initialize_standard_steps()
    
    def _initialize_standard_steps(self):
        """標準的な処理ステップを初期化"""
        standard_steps = [
            ProcessingStep("upload", "ファイルアップロード", "📁", 2.0),
            ProcessingStep("validation", "ファイル検証", "✅", 3.0),
            ProcessingStep("extraction", "データ抽出", "📦", 5.0),
            ProcessingStep("preprocessing", "データ前処理", "🔄", 10.0),
            ProcessingStep("analysis", "分析処理", "📊", 15.0),
            ProcessingStep("visualization", "可視化生成", "🎨", 8.0),
        ]
        
        for step in standard_steps:
            self.steps[step.name] = step
    
    def start_processing(self):
        """処理開始"""
        with self._lock:
            self.is_running = True
            self.start_time = datetime.now()
            self.overall_progress = 0
            log.info("[処理監視] データ処理開始")
            self._notify_callbacks()
    
    def start_step(self, step_name: str, custom_description: Optional[str] = None):
        """個別ステップ開始"""
        with self._lock:
            if step_name in self.steps:
                step = self.steps[step_name]
                step.start_time = datetime.now()
                step.status = "running"
                step.progress = 0
                
                if custom_description:
                    step.description = custom_description
                
                log.info(f"[処理監視] ステップ開始: {step.name} - {step.description}")
                self._notify_callbacks()
    
    def update_step_progress(self, step_name: str, progress: int, message: Optional[str] = None):
        """ステップ進捗更新"""
        with self._lock:
            if step_name in self.steps:
                step = self.steps[step_name]
                step.progress = min(100, max(0, progress))
                
                if message:
                    step.description = message
                
                # 全体進捗を再計算
                self._recalculate_overall_progress()
                
                log.debug(f"[処理監視] 進捗更新: {step.name} - {progress}%")
                self._notify_callbacks()
    
    def complete_step(self, step_name: str, message: Optional[str] = None):
        """ステップ完了"""
        with self._lock:
            if step_name in self.steps:
                step = self.steps[step_name]
                step.end_time = datetime.now()
                step.status = "completed"
                step.progress = 100
                
                if step.start_time:
                    step.actual_duration = (step.end_time - step.start_time).total_seconds()
                
                if message:
                    step.description = message
                
                log.info(f"[処理監視] ステップ完了: {step.name} - {step.actual_duration:.1f}秒")
                self._recalculate_overall_progress()
                self._notify_callbacks()
    
    def fail_step(self, step_name: str, error_message: str):
        """ステップ失敗"""
        with self._lock:
            if step_name in self.steps:
                step = self.steps[step_name]
                step.end_time = datetime.now()
                step.status = "failed"
                step.error_message = error_message
                
                if step.start_time:
                    step.actual_duration = (step.end_time - step.start_time).total_seconds()
                
                log.error(f"[処理監視] ステップ失敗: {step.name} - {error_message}")
                self.is_running = False
                self._notify_callbacks()
    
    def _recalculate_overall_progress(self):
        """全体進捗を再計算"""
        total_weight = sum(step.estimated_duration for step in self.steps.values())
        weighted_progress = sum(
            (step.progress / 100) * step.estimated_duration 
            for step in self.steps.values()
        )
        
        self.overall_progress = int((weighted_progress / total_weight) * 100)
    
    def add_callback(self, callback: Callable):
        """進捗更新コールバックを追加"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self):
        """コールバック通知"""
        for callback in self.callbacks:
            try:
                callback(self.get_status())
            except Exception as e:
                log.error(f"[処理監視] コールバックエラー: {e}")
    
    def get_status(self) -> Dict:
        """現在の状況を取得"""
        with self._lock:
            elapsed_time = 0
            if self.start_time:
                elapsed_time = (datetime.now() - self.start_time).total_seconds()
            
            # 推定残り時間を計算
            estimated_remaining = 0
            if self.overall_progress > 0:
                total_estimated = elapsed_time * (100 / self.overall_progress)
                estimated_remaining = max(0, total_estimated - elapsed_time)
            
            return {
                'overall_progress': self.overall_progress,
                'is_running': self.is_running,
                'elapsed_time': elapsed_time,
                'estimated_remaining': estimated_remaining,
                'current_stage': self.current_stage.value,
                'steps': {
                    name: {
                        'name': step.name,
                        'description': step.description,
                        'icon': step.icon,
                        'progress': step.progress,
                        'status': step.status,
                        'error_message': step.error_message,
                        'duration': step.actual_duration
                    }
                    for name, step in self.steps.items()
                }
            }
    
    def create_progress_display(self, status: Dict) -> dict:
        """Dash用の進捗表示データを生成"""
        import plotly.graph_objects as go
        
        # 全体進捗バー
        overall_fig = go.Figure(go.Bar(
            x=[status['overall_progress']],
            y=['全体進捗'],
            orientation='h',
            marker=dict(
                color='#3498db' if status['is_running'] else '#27ae60',
                opacity=0.8
            ),
            text=[f"{status['overall_progress']}%"],
            textposition='inside',
            textfont=dict(color='white', size=14)
        ))
        
        overall_fig.update_layout(
            xaxis=dict(range=[0, 100], showticklabels=False),
            yaxis=dict(showticklabels=False),
            height=60,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        # 個別ステップの進捗
        step_data = []
        for step_name, step_info in status['steps'].items():
            color = {
                'pending': '#bdc3c7',
                'running': '#3498db', 
                'completed': '#27ae60',
                'failed': '#e74c3c'
            }.get(step_info['status'], '#bdc3c7')
            
            step_data.append({
                'step': step_info['name'],
                'description': step_info['description'],
                'icon': step_info['icon'],
                'progress': step_info['progress'],
                'status': step_info['status'],
                'color': color
            })
        
        # 時間情報
        elapsed_min = int(status['elapsed_time'] // 60)
        elapsed_sec = int(status['elapsed_time'] % 60)
        remaining_min = int(status['estimated_remaining'] // 60)
        remaining_sec = int(status['estimated_remaining'] % 60)
        
        time_info = {
            'elapsed': f"{elapsed_min:02d}:{elapsed_sec:02d}",
            'remaining': f"{remaining_min:02d}:{remaining_sec:02d}" if status['is_running'] else "完了"
        }
        
        return {
            'overall_figure': overall_fig,
            'step_data': step_data,
            'time_info': time_info,
            'is_running': status['is_running']
        }

# グローバルインスタンス
processing_monitor = ProcessingMonitor()

# 便利な関数
def start_processing():
    """処理開始（外部から呼び出し用）"""
    processing_monitor.start_processing()

def start_step(step_name: str, description: Optional[str] = None):
    """ステップ開始（外部から呼び出し用）"""
    processing_monitor.start_step(step_name, description)

def update_progress(step_name: str, progress: int, message: Optional[str] = None):
    """進捗更新（外部から呼び出し用）"""
    processing_monitor.update_step_progress(step_name, progress, message)

def complete_step(step_name: str, message: Optional[str] = None):
    """ステップ完了（外部から呼び出し用）"""
    processing_monitor.complete_step(step_name, message)

def fail_step(step_name: str, error_message: str):
    """ステップ失敗（外部から呼び出し用）"""
    processing_monitor.fail_step(step_name, error_message)