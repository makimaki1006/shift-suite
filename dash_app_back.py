# dash_app.py - Shift-Suite高速分析ビューア (app.py機能完全再現版)
import base64
import io
import json
import logging
import tempfile
import zipfile
import threading
import time
import weakref
import psutil
import os
from functools import lru_cache, wraps
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import OrderedDict
import unicodedata

import dash
import dash_cytoscape as cyto
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from flask import jsonify
import traceback
import gc
from shift_suite.tasks.utils import safe_read_excel, gen_labels
from shift_suite.tasks.shortage_factor_analyzer import ShortageFactorAnalyzer
from shift_suite.tasks import over_shortage_log
from shift_suite.tasks.daily_cost import calculate_daily_cost
from shift_suite.tasks import leave_analyzer
try:
    from shift_suite.tasks.analyzers.synergy_enhanced import (
        analyze_synergy, analyze_team_synergy, analyze_synergy_by_role, 
        analyze_all_roles_synergy, create_synergy_correlation_matrix, 
        create_synergy_correlation_matrix_optimized
    )
except ImportError:
    from shift_suite.tasks.analyzers.synergy import analyze_synergy
    analyze_team_synergy = None
    analyze_synergy_by_role = None
    analyze_all_roles_synergy = None
    create_synergy_correlation_matrix = None
    create_synergy_correlation_matrix_optimized = None
from shift_suite.tasks.analyzers.team_dynamics import analyze_team_dynamics
from shift_suite.tasks.blueprint_analyzer import create_blueprint_list
from shift_suite.tasks.integrated_creation_logic_viewer import (
    create_creation_logic_analysis_tab,
)
from shift_suite.tasks.quick_logic_analysis import (
    get_basic_shift_stats,
    get_quick_patterns,
    run_optimized_analysis,
    create_stats_cards,
    create_pattern_list,
    create_deep_analysis_display,
)
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt

def create_shortage_from_heat_all(heat_all_df: pd.DataFrame) -> pd.DataFrame:
    """
    heat_ALLデータから不足データを生成する
    """
    if heat_all_df.empty:
        return pd.DataFrame()
    
    # 日付列を特定（数値でない列は除外）
    date_columns = [col for col in heat_all_df.columns if col not in ['staff', 'role', 'code', 'sum', 'max', 'min', 'avg', 'need']]
    
    if not date_columns:
        return pd.DataFrame()
    
    # 時間インデックスを取得
    time_index = heat_all_df.index
    
    # 各日付・時間帯の不足を計算（簡易版）
    shortage_data = {}
    for date_col in date_columns:
        if date_col in heat_all_df.columns:
            # 実際の人数から必要人数を引いて不足を計算
            # 正の値は不足、負の値は過剰
            actual_staff = heat_all_df[date_col].fillna(0)
            if 'need' in heat_all_df.columns:
                need = heat_all_df['need'].fillna(0)
                shortage = need - actual_staff
            else:
                # needがない場合は、平均値を基準とする
                avg_staff = actual_staff.mean()
                shortage = avg_staff - actual_staff
            
            # 不足のみを対象とする（正の値のみ）
            shortage = shortage.clip(lower=0)
            shortage_data[date_col] = shortage
    
    if not shortage_data:
        return pd.DataFrame()
    
    shortage_df = pd.DataFrame(shortage_data, index=time_index)
    return shortage_df

def simple_synergy_analysis(long_df: pd.DataFrame, target_staff: str) -> pd.DataFrame:
    """
    シンプルなシナジー分析（shortage_dfを使わない版）
    共働頻度とパフォーマンスの相関に基づく分析
    """
    if long_df.empty or not target_staff:
        return pd.DataFrame()
    
    # 対象職員の勤務記録
    target_work = long_df[long_df['staff'] == target_staff]
    if target_work.empty:
        return pd.DataFrame()
    
    # 他の職員との共働分析
    synergy_scores = []
    other_staff = long_df[long_df['staff'] != target_staff]['staff'].unique()
    
    for coworker in other_staff:
        coworker_work = long_df[long_df['staff'] == coworker]
        if coworker_work.empty:
            continue
        
        # 共働した日時を特定
        target_slots = set(target_work['ds'])
        coworker_slots = set(coworker_work['ds'])
        together_slots = target_slots & coworker_slots
        
        if len(together_slots) < 2:  # 最低限の共働回数
            continue
        
        # 共働頻度の計算
        total_target_slots = len(target_slots)
        together_ratio = len(together_slots) / total_target_slots if total_target_slots > 0 else 0
        
        # シナジースコアの計算（共働頻度ベース）
        # より多く一緒に働く = より良い相性と仮定
        synergy_score = together_ratio * 100  # パーセンテージ
        
        synergy_scores.append({
            "相手の職員": coworker,
            "シナジースコア": synergy_score,
            "共働スロット数": len(together_slots)
        })
    
    if not synergy_scores:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(synergy_scores).sort_values("シナジースコア", ascending=False).reset_index(drop=True)
    return result_df

# ロガー設定
LOG_LEVEL = logging.DEBUG
log_stream = io.StringIO()

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.StreamHandler(stream=log_stream)
    ],
    force=True
)
log = logging.getLogger(__name__)

# Analysis logger configuration
analysis_logger = logging.getLogger('analysis')
analysis_logger.setLevel(logging.INFO)
analysis_logger.propagate = False
try:
    file_handler = logging.FileHandler('analysis_log.log', mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s] - %(message)s')
    file_handler.setFormatter(formatter)
    if not analysis_logger.handlers:
        analysis_logger.addHandler(file_handler)
except Exception as e:
    logging.error(f"\u5206\u6790\u30ed\u30b0\u30d5\u30a1\u30a4\u30eb\u306e\u8a2d\u5b9a\u306b\u5931\u6557\u3057\u307e\u3057\u305f: {e}")

# Dashアプリケーション初期化
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Shift-Suite 高速分析ビューア"

# Flask error handlers
@server.errorhandler(Exception)
def handle_exception(e):
    """Catch all unhandled exceptions."""
    log.exception("Unhandled exception in request:")
    error_info = {
        "error": str(e),
        "type": type(e).__name__,
        "traceback": traceback.format_exc(),
    }
    return jsonify(error_info), 200


@server.errorhandler(500)
def handle_500(e):
    log.error("500 error occurred")
    return jsonify({"error": "Internal server error", "message": str(e)}), 200

# === グローバル状態管理（安定性向上版） ===
# メモリ効率的なLRUキャッシュの実装
class ThreadSafeLRUCache:
    """スレッドセーフなLRUキャッシュ実装"""
    def __init__(self, maxsize: int = 50):
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0
        
    def get(self, key: str, default=None):
        with self._lock:
            if key in self._cache:
                # LRU: 最近使用したものを末尾に移動
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return default
            
    def set(self, key: str, value: Any):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            self._cache[key] = value
            # サイズ制限を超えたら最も古いものを削除
            if len(self._cache) > self._maxsize:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                log.debug(f"Cache evicted: {oldest_key}")
                
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            
    def get_stats(self):
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate
            }
            
    def __contains__(self, key):
        with self._lock:
            return key in self._cache
            
    def keys(self):
        with self._lock:
            return list(self._cache.keys())

# グローバルキャッシュとロック
DATA_CACHE = ThreadSafeLRUCache(maxsize=50)

# シナジー分析結果のキャッシュ
SYNERGY_CACHE = ThreadSafeLRUCache(maxsize=10)

def get_synergy_cache_key(long_df: pd.DataFrame, shortage_df: pd.DataFrame) -> str:
    """シナジー分析結果のキャッシュキーを生成"""
    try:
        # データのハッシュ値を計算してキャッシュキーとする
        import hashlib
        long_hash = hashlib.md5(str(long_df.shape).encode() + str(long_df.columns.tolist()).encode()).hexdigest()[:8]
        shortage_hash = hashlib.md5(str(shortage_df.shape).encode() + str(shortage_df.columns.tolist()).encode()).hexdigest()[:8]
        return f"synergy_{long_hash}_{shortage_hash}"
    except:
        return "synergy_default"

def clear_synergy_cache():
    """シナジーキャッシュをクリア"""
    global SYNERGY_CACHE
    SYNERGY_CACHE.clear()
    log.info("シナジーキャッシュをクリアしました")
LOADING_STATUS = {}  # 読み込み中のキーを追跡
LOADING_LOCK = threading.Lock()
# Path to the currently selected scenario directory.
CURRENT_SCENARIO_DIR: Path | None = None
# Temporary directory object for uploaded scenarios
TEMP_DIR_OBJ: tempfile.TemporaryDirectory | None = None

# ``LOGIC_ANALYSIS_CACHE`` stores results keyed by dataframe hash
LOGIC_ANALYSIS_CACHE: dict[int, dict[str, object]] = {}

def get_cached_analysis(df_hash: int):
    """Return cached analysis results for the given hash."""
    return LOGIC_ANALYSIS_CACHE.get(df_hash)


def cache_analysis(df_hash: int, results: dict) -> None:
    """Cache analysis results keeping at most 3 entries."""
    if len(LOGIC_ANALYSIS_CACHE) >= 3:
        oldest_key = next(iter(LOGIC_ANALYSIS_CACHE))
        del LOGIC_ANALYSIS_CACHE[oldest_key]
    LOGIC_ANALYSIS_CACHE[df_hash] = results

# --- ユーティリティ関数 ---
def safe_filename(name: str) -> str:
    """Normalize and sanitize strings for file keys"""
    name = unicodedata.normalize("NFKC", name)
    for ch in ["/", "\\", ":", "*", "?", "\"", "<", ">", "|", "・", "／", "＼"]:
        name = name.replace(ch, "_")
    return name


def calculate_role_dynamic_need(df_heat: pd.DataFrame, date_cols: List[str], heat_key: str) -> pd.DataFrame:
    """
    職種別・雇用形態別の動的need値を正確に計算する共通関数
    
    Args:
        df_heat: 職種別ヒートマップデータ
        date_cols: 日付列のリスト
        heat_key: ヒートマップキー（ログ用）
    
    Returns:
        計算された動的need値のDataFrame
    """
    log.info(f"[ROLE_DYNAMIC_NEED] Calculating for {heat_key}")
    
    # ★★★ 修正：詳細Need値ファイルを直接使用 ★★★
    # 職種別または雇用形態別の詳細Need値ファイルを探す
    detailed_need_key = None
    if heat_key.startswith('heat_emp_'):
        # 雇用形態別
        emp_name = heat_key.replace('heat_emp_', '').replace('heat_', '')
        detailed_need_key = f"need_per_date_slot_emp_{emp_name}"
    elif heat_key.startswith('heat_') and heat_key not in ['heat_all', 'heat_ALL']:
        # 職種別
        role_name = heat_key.replace('heat_', '')
        detailed_need_key = f"need_per_date_slot_role_{role_name}"
    
    # 詳細Need値ファイルが存在する場合は直接使用
    if detailed_need_key:
        detailed_need_df = data_get(detailed_need_key, pd.DataFrame())
        if not detailed_need_df.empty:
            log.info(f"[ROLE_DYNAMIC_NEED] {heat_key}: Using detailed need file {detailed_need_key}")
            
            # 日付列フィルタリング
            available_date_cols = [col for col in date_cols if col in detailed_need_df.columns]
            if available_date_cols:
                filtered_need_df = detailed_need_df[available_date_cols].copy()
                filtered_need_df = filtered_need_df.reindex(index=df_heat.index, fill_value=0)
                log.info(f"[ROLE_DYNAMIC_NEED] {heat_key}: Successfully using detailed need values")
                return filtered_need_df
    
    # フォールバック：従来のロジック
    log.warning(f"[ROLE_DYNAMIC_NEED] {heat_key}: Detailed need file not found, using fallback logic")
    
    # Step 1: need_per_date_slotから全体の動的need値を取得
    need_per_date_df = data_get('need_per_date_slot', pd.DataFrame())
    
    if need_per_date_df.empty or len(date_cols) == 0:
        log.warning(f"[ROLE_DYNAMIC_NEED] {heat_key}: Fallback to baseline need (no global data)")
        return pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(date_cols), axis=1),
                           index=df_heat.index, columns=date_cols)
    
    # Step 2: 全職種の基準need値の合計を計算
    # heat_ALL（全体）と雇用形態別（heat_emp_）を除外して個別職種のみを対象とする
    all_role_keys = [k for k in DATA_CACHE.keys() 
                    if k.startswith('heat_') 
                    and k not in ['heat_all', 'heat_ALL']
                    and not k.startswith('heat_emp_')]
    total_baseline_need = 0.0
    
    # デバッグ情報の出力
    all_heat_keys = [k for k in DATA_CACHE.keys() if k.startswith('heat_')]
    log.info(f"[ROLE_DYNAMIC_NEED] All heat keys: {all_heat_keys}")
    log.info(f"[ROLE_DYNAMIC_NEED] Filtered role keys: {all_role_keys}")
    
    for role_key in all_role_keys:
        role_heat = data_get(role_key, pd.DataFrame())
        if not role_heat.empty and 'need' in role_heat.columns:
            role_baseline = role_heat['need'].sum()
            total_baseline_need += role_baseline
            log.debug(f"[ROLE_DYNAMIC_NEED] {role_key}: baseline_need={role_baseline:.2f}")
    
    if total_baseline_need <= 0:
        log.warning(f"[ROLE_DYNAMIC_NEED] {heat_key}: Fallback to baseline need (no total baseline)")
        return pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(date_cols), axis=1),
                           index=df_heat.index, columns=date_cols)
    
    # Step 3: 当前職種の比率を計算
    current_role_total_baseline = df_heat['need'].sum() if 'need' in df_heat.columns else len(df_heat)
    role_ratio = current_role_total_baseline / total_baseline_need
    
    log.info(f"[ROLE_DYNAMIC_NEED] {heat_key}: role_ratio={role_ratio:.4f}, baseline_need={current_role_total_baseline}, total_baseline={total_baseline_need}")
    
    # Step 4: 全体の動的need値に職種比率を適用
    need_df = pd.DataFrame(index=df_heat.index, columns=date_cols)
    need_per_date_df.columns = [str(col) for col in need_per_date_df.columns]
    
    for date_col in date_cols:
        date_str = str(date_col)
        if date_str in need_per_date_df.columns:
            overall_need_series = need_per_date_df[date_str]
            
            # 時間帯インデックスを合わせる
            if len(overall_need_series) == len(df_heat):
                role_need_series = overall_need_series * role_ratio
                need_df[date_col] = role_need_series.values
            else:
                # インデックス不一致の場合は平均値を使用
                avg_need = overall_need_series.mean() * role_ratio
                need_df[date_col] = avg_need
        else:
            # 該当日付がない場合は基準値を使用
            need_df[date_col] = df_heat['need'].values
    
    need_df = need_df.fillna(0)
    total_calculated_need = need_df.sum().sum()
    log.info(f"[ROLE_DYNAMIC_NEED] {heat_key}: Successfully calculated, total_need={total_calculated_need:.2f}")
    
    return need_df

def date_with_weekday(date_str: str) -> str:
    """日付文字列に曜日を追加"""
    try:  # noqa: E722
        date = pd.to_datetime(date_str)
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        return f"{date.strftime('%m/%d')}({weekdays[date.weekday()]})"
    except Exception:
        return str(date_str)


@lru_cache(maxsize=8)
def safe_read_parquet(filepath: Path) -> pd.DataFrame:
    """Parquetファイルを安全に読み込み結果をキャッシュ"""
    try:
        if not filepath.exists():
            log.debug(f"File does not exist: {filepath}")
            return pd.DataFrame()
        
        if filepath.stat().st_size == 0:
            log.warning(f"Empty file detected: {filepath}")
            return pd.DataFrame()
            
        df = pd.read_parquet(filepath)
        log.debug(f"Successfully loaded {filepath}: shape={df.shape}")
        return df
    except FileNotFoundError:
        log.debug(f"File not found: {filepath}")
        return pd.DataFrame()
    except pd.errors.EmptyDataError:
        log.warning(f"Empty data in file: {filepath}")
        return pd.DataFrame()
    except Exception as e:
        log.warning(f"Failed to read {filepath}: {type(e).__name__}: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=8)
def safe_read_csv(filepath: Path) -> pd.DataFrame:
    """CSVファイルを安全に読み込み結果をキャッシュ"""
    try:
        return pd.read_csv(filepath)  # type: ignore
    except Exception as e:
        log.warning(f"Failed to read {filepath}: {e}")
        return pd.DataFrame()


def clear_data_cache() -> None:
    """Clear cached data when the scenario changes with resource monitoring."""
    memory_before = get_memory_usage()
    log.info(f"Data cache clear started. Memory before: {memory_before['rss_mb']:.1f}MB")
    
    DATA_CACHE.clear()
    safe_read_parquet.cache_clear()
    safe_read_csv.cache_clear()
    
    # 積極的なガベージコレクション
    gc.collect()
    
    memory_after = get_memory_usage()
    memory_freed = memory_before['rss_mb'] - memory_after['rss_mb']
    log.info(f"Data cache cleared. Memory after: {memory_after['rss_mb']:.1f}MB (freed: {memory_freed:.1f}MB)")


# === リソース監視機能（安定性向上のため追加） ===
def get_memory_usage() -> Dict[str, float]:
    """現在のメモリ使用量を取得"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # 実際のメモリ使用量
            "vms_mb": memory_info.vms / 1024 / 1024,  # 仮想メモリ使用量
            "percent": process.memory_percent(),       # システム全体に対する割合
        }
    except Exception as e:
        log.warning(f"Memory usage monitoring failed: {e}")
        return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

def check_memory_pressure() -> bool:
    """メモリプレッシャーをチェック"""
    memory_info = get_memory_usage()
    # メモリ使用率80%以上で警告
    return memory_info["percent"] > 80

def emergency_cleanup():
    """緊急メモリクリーンアップ"""
    log.warning("緊急メモリクリーンアップを実行します")
    
    # キャッシュをクリア
    DATA_CACHE.clear()
    safe_read_parquet.cache_clear()
    safe_read_csv.cache_clear()
    
    # 強制ガベージコレクション
    gc.collect()
    
    memory_after = get_memory_usage()
    log.info(f"クリーンアップ後メモリ使用量: {memory_after['rss_mb']:.1f}MB ({memory_after['percent']:.1f}%)")

# 新しい安定性向上版コールバックラッパー
def safe_callback_enhanced(func):
    """Enhanced safe callback with resource monitoring and better error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        memory_start = get_memory_usage()
        
        try:
            # メモリプレッシャーチェック
            if check_memory_pressure():
                log.warning(f"High memory usage before {func.__name__}: {memory_start['percent']:.1f}%")
                emergency_cleanup()
            
            # ガベージコレクションのプロアクティブな実行
            if gc.get_count()[0] > 700:
                gc.collect()
                
            # 実際のコールバック実行
            result = func(*args, **kwargs)
            
            # パフォーマンスログ
            execution_time = time.time() - start_time
            memory_end = get_memory_usage()
            memory_delta = memory_end['rss_mb'] - memory_start['rss_mb']
            
            if execution_time > 5:  # 5秒以上の処理を警告
                log.warning(f"Slow callback {func.__name__}: {execution_time:.2f}s, memory delta: {memory_delta:+.1f}MB")
            elif execution_time > 1:  # 1秒以上を情報ログ
                log.info(f"Callback {func.__name__}: {execution_time:.2f}s, memory delta: {memory_delta:+.1f}MB")
                
            return result
            
        except PreventUpdate:
            # PreventUpdateは正常なフローなので再発生
            raise
        except FileNotFoundError as e:
            log.error(f"File not found: {e}")
            return html.Div([
                html.H4("Error: File not found", style={'color': 'red'}),
                html.P(str(e)),
                html.P("Please check if the file was uploaded correctly.")
            ])
        except pd.errors.EmptyDataError:
            log.error("Empty dataframe")
            return html.Div([
                html.H4("Error: Data is empty", style={'color': 'orange'}),
                html.P("The data file may be empty or corrupted.")
            ])
        except MemoryError as e:
            log.error(f"Memory error: {e}")
            emergency_cleanup()
            return html.Div([
                html.H4("Memory Error", style={'color': 'red'}),
                html.P("Memory shortage occurred. Cache has been cleared."),
                html.P("Please refresh the browser or try with smaller dataset.")
            ])
        except TimeoutError as e:
            log.error(f"Timeout: {e}")
            return html.Div([
                html.H4("Processing Timeout", style={'color': 'orange'}),
                html.P("Processing is taking too long. Please reduce data size or wait.")
            ])
        except Exception as e:
            log.exception(f"Unexpected error in {func.__name__}")
            
            # エラー時のメモリクリーンアップ
            if check_memory_pressure():
                emergency_cleanup()
                
            return html.Div([
                html.H4(f"Error occurred ({func.__name__})", style={'color': 'red'}),
                html.Details([
                    html.Summary("Show error details"),
                    html.Pre(str(e), style={'background': '#f0f0f0', 'padding': '10px', 'overflow': 'auto'})
                ]),
                html.P("Please refresh the browser if the problem persists.")
            ])
    return wrapper

# 統一されたsafe_callback関数（Enhanced版を使用）
safe_callback = safe_callback_enhanced


def data_get(key: str, default=None):
    """Load a data asset lazily from the current scenario directory with enhanced stability."""
    log.debug(f"data_get('{key}'): キャッシュを検索中...")
    
    # キャッシュチェック（ThreadSafeLRUCacheを使用）
    cached_value = DATA_CACHE.get(key)
    if cached_value is not None:
        log.debug(f"data_get('{key}'): キャッシュヒット")
        return cached_value

    log.debug(f"data_get('{key}'): キャッシュミス。ファイル検索を開始...")

    if CURRENT_SCENARIO_DIR is None:
        log.warning(f"CURRENT_SCENARIO_DIRが未設定のため、データ取得をスキップします。key={key}")
        default_value = default if default is not None else pd.DataFrame()
        DATA_CACHE.set(key, default_value)
        return default_value

    search_dirs = [CURRENT_SCENARIO_DIR, CURRENT_SCENARIO_DIR.parent]
    log.debug(f"Searching {search_dirs} for key {key}")

    # Special file names
    special = {
        "long_df": ["intermediate_data.parquet"],
        "daily_cost": ["daily_cost.parquet", "daily_cost.xlsx"],
        "shortage_time": ["shortage_time_CORRECTED.parquet"],
        "need_per_date_slot": ["need_per_date_slot.parquet"],
    }
    
    # ★★★ 職種別・雇用形態別詳細Need値ファイルの検索対応 ★★★
    if key.startswith("need_per_date_slot_role_") or key.startswith("need_per_date_slot_emp_"):
        filenames = [f"{key}.parquet"]
    else:
        filenames = special.get(key, [f"{key}.parquet", f"{key}.csv", f"{key}.xlsx"])

    # Special handling for need_per_date_slot
    if key == "need_per_date_slot":
        for directory in search_dirs:
            fp = directory / "need_per_date_slot.parquet"
            if fp.exists():
                try:
                    log.debug(f"Loading need_per_date_slot from {fp}")
                    
                    # 複数の方法でdatetime問題を回避
                    df = None
                    
                    # 方法1: PyArrowテーブルとして読み込み、カラム名を手動処理
                    try:
                        table = pq.read_table(fp)
                        # カラム名を文字列に変換
                        new_columns = [str(col) for col in table.column_names]
                        
                        # データフレームに変換（index処理）
                        df = table.to_pandas()
                        df.columns = new_columns
                        
                        log.debug(f"Method 1 success: PyArrow table conversion")
                        
                    except Exception as e1:
                        log.debug(f"Method 1 failed: {e1}")
                        
                        # 方法2: pandas直接読み込み（types_mapperなし）
                        try:
                            df = pd.read_parquet(fp, engine='pyarrow', 
                                               use_nullable_dtypes=False)
                            df.columns = [str(col) for col in df.columns]
                            log.debug(f"Method 2 success: Direct pandas read")
                            
                        except Exception as e2:
                            log.debug(f"Method 2 failed: {e2}")
                            
                            # 方法3: 最後の手段 - ファイル再作成
                            try:
                                # 元データを別の方法で読み込み
                                temp_table = pq.read_table(fp)
                                temp_df = temp_table.to_pandas(types_mapper=pd.ArrowDtype)
                                temp_df.columns = [str(col) for col in temp_df.columns]
                                
                                # 一時的にCSV経由で変換
                                temp_csv = fp.with_suffix('.temp.csv')
                                temp_df.to_csv(temp_csv)
                                df = pd.read_csv(temp_csv, index_col=0)
                                temp_csv.unlink()  # 一時ファイル削除
                                
                                log.debug(f"Method 3 success: CSV conversion")
                                
                            except Exception as e3:
                                log.error(f"All methods failed: {e1}, {e2}, {e3}")
                                raise e3
                    
                    if df is not None:
                        DATA_CACHE.set(key, df)
                        log.info(f"Successfully loaded need_per_date_slot: {df.shape}")
                        return df
                    else:
                        raise ValueError("Failed to load parquet file with any method")
                except Exception as e:
                    log.warning(f"Failed to load {fp}: {e}")
                    continue
        log.warning("need_per_date_slot.parquet not found")
        empty_df = pd.DataFrame()
        DATA_CACHE.set(key, empty_df)
        return empty_df

    for name in filenames:
        for directory in search_dirs:
            fp = directory / name
            log.debug(f"Checking {fp}")
            if fp.suffix == ".parquet" and fp.exists():
                df = safe_read_parquet(fp)
                if not df.empty:
                    DATA_CACHE.set(key, df)
                    log.debug(f"Loaded {fp} into cache for {key}")
                    return df
                break
            if fp.suffix == ".csv" and fp.exists():
                df = safe_read_csv(fp)
                if not df.empty:
                    DATA_CACHE.set(key, df)
                    log.debug(f"Loaded {fp} into cache for {key}")
                    return df
                break
            if fp.suffix == ".xlsx" and fp.exists():
                df = safe_read_excel(fp)
                if not df.empty:
                    DATA_CACHE.set(key, df)
                    log.debug(f"Loaded {fp} into cache for {key}")
                    return df
                break

    if key == "summary_report":
        files = sorted(CURRENT_SCENARIO_DIR.glob("OverShortage_SummaryReport_*.md"))
        if files:
            text = files[-1].read_text(encoding="utf-8")
            DATA_CACHE.set(key, text)
            log.debug(f"Loaded summary report {files[-1]}")
            return text
    if key in {"roles", "employments"}:
        roles, employments = load_shortage_meta(CURRENT_SCENARIO_DIR)
        DATA_CACHE.set("roles", roles)
        DATA_CACHE.set("employments", employments)
        return DATA_CACHE.get(key, default)

    if key == "shortage_events":
        df_events = over_shortage_log.list_events(CURRENT_SCENARIO_DIR)
        DATA_CACHE.set(key, df_events)
        DATA_CACHE.set("shortage_log_path", str(Path(CURRENT_SCENARIO_DIR) / "over_shortage_log.csv"))
        return DATA_CACHE.get(key, default)

    log.debug(f"データキー '{key}' に対応するファイルが見つかりませんでした。")
    DATA_CACHE.set(key, default)
    return default


def _valid_df(df: pd.DataFrame) -> bool:
    """Return True if ``df`` is a non-empty :class:`~pandas.DataFrame`."""
    return isinstance(df, pd.DataFrame) and not df.empty


def calc_ratio_from_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """ヒートマップデータから不足率を計算（統合システム対応）"""
    if df.empty:
        return pd.DataFrame()

    date_cols = [c for c in df.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    if not date_cols:
        return pd.DataFrame()

    # 統合システム: need_per_date_slotを優先使用
    need_per_date_df = data_get('need_per_date_slot')
    
    if not need_per_date_df.empty:
        # need_per_date_slotからneed_dfを作成
        log.info(f"Using need_per_date_slot for accurate need calculation: {need_per_date_df.shape}")
        
        # 日付列の交集合を取得
        available_dates = [col for col in date_cols if str(col) in need_per_date_df.columns]
        
        if available_dates:
            need_df = need_per_date_df[[str(col) for col in available_dates]].copy()
            need_df.columns = available_dates  # 元の列名に戻す
            # インデックスを一致させる
            common_index = df.index.intersection(need_df.index)
            need_df = need_df.loc[common_index]
        else:
            log.warning("No matching dates in need_per_date_slot, falling back to average need")
            need_df = pd.DataFrame(0.0, index=df.index, columns=date_cols)
    else:
        # フォールバック: 従来のaverage need使用
        if "need" in df.columns:
            log.warning("need_per_date_slot not available, using average need values")
            need_series = df["need"].fillna(0)
            need_df = pd.DataFrame(
                np.repeat(need_series.values[:, np.newaxis], len(date_cols), axis=1),
                index=need_series.index,
                columns=date_cols
            )
        else:
            need_df = pd.DataFrame(0.0, index=df.index, columns=date_cols)
    staff_df = df[date_cols].fillna(0)
    
    # 修正: 日曜日の過剰表示を防ぐため、計算を強化
    # need_dfが0の場合の適切な処理
    valid_need_mask = need_df > 0
    ratio_df = pd.DataFrame(0.0, index=need_df.index, columns=need_df.columns)
    
    # 需要がある場合のみ不足率を計算
    ratio_df = ratio_df.where(~valid_need_mask, 
                             ((need_df - staff_df) / need_df).clip(lower=0))
    
    # 最終的にNaN値を0で埋める（日曜日対策）
    ratio_df = ratio_df.fillna(0)
    
    return ratio_df


def load_shortage_meta(data_dir: Path) -> Tuple[List[str], List[str]]:
    """職種と雇用形態のリストを読み込む"""
    roles = []
    employments = []
    meta_fp = data_dir / "shortage.meta.json"
    if meta_fp.exists():
        try:
            with open(meta_fp, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            roles = meta.get("roles", [])
            employments = meta.get("employments", [])
        except Exception as e:
            log.debug(f"Failed to load shortage meta: {e}")
    return roles, employments



def load_and_sum_heatmaps(data_dir: Path, keys: List[str]) -> pd.DataFrame:
    """Load multiple heatmap files and aggregate them."""
    dfs = []
    for key in keys:
        df = data_get(key)
        if df is None and data_dir:
            fp = Path(data_dir) / f"{key}.parquet"
            if fp.exists():
                df = safe_read_parquet(fp)
                if not df.empty:
                    DATA_CACHE.set(key, df)
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    total = dfs[0].copy()
    for df in dfs[1:]:
        total = total.add(df, fill_value=0)

    if {"need", "staff"}.issubset(total.columns):
        total["lack"] = (total["need"] - total["staff"]).clip(lower=0)
    if {"staff", "upper"}.issubset(total.columns):
        total["excess"] = (total["staff"] - total["upper"]).clip(lower=0)

    return total


def generate_heatmap_figure(df_heat: pd.DataFrame, title: str) -> go.Figure:
    """指定されたデータフレームからヒートマップグラフを生成する"""
    if df_heat is None or df_heat.empty:
        return go.Figure().update_layout(title_text=f"{title}: データなし", height=300)

    date_cols = [c for c in df_heat.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    if not date_cols:
        return go.Figure().update_layout(title_text=f"{title}: 表示可能な日付データなし", height=300)

    display_df = df_heat[date_cols]
    time_labels = gen_labels(30)
    display_df = display_df.reindex(time_labels, fill_value=0)
    
    # 修正点1: NaN値を明示的に0で埋める
    display_df = display_df.fillna(0)
    
    display_df_renamed = display_df.copy()
    display_df_renamed.columns = [date_with_weekday(c) for c in display_df.columns]

    # 修正点2: text_autoを追加して、0値も表示されるようにする
    fig = px.imshow(
        display_df_renamed,
        aspect='auto',
        color_continuous_scale=px.colors.sequential.Viridis,
        title=title,
        labels={'x': '日付', 'y': '時間', 'color': '人数'},
        text_auto=True  # セルに値を表示
    )
    
    # 修正点3: 0値の表示スタイルを調整
    fig.update_traces(
        texttemplate='%{text}',
        textfont={"size": 10}
    )
    fig.update_xaxes(tickvals=list(range(len(display_df.columns))))
    return fig


def create_knowledge_network_graph(network_data: Dict) -> cyto.Cytoscape:
    """Return an interactive network graph of implicit knowledge."""
    nodes = [
        {"data": {"id": n["id"], "label": n["label"]}}
        for n in network_data.get("nodes", [])
    ]
    edges = [
        {
            "data": {
                "source": e.get("from"),
                "target": e.get("to"),
                "label": e.get("label", ""),
            }
        }
        for e in network_data.get("edges", [])
    ]

    return cyto.Cytoscape(
        id="knowledge-network-graph",
        elements=nodes + edges,
        style={"width": "100%", "height": "500px"},
        layout={"name": "cose"},
        stylesheet=[
            {"selector": "node", "style": {"content": "data(label)", "font-size": "10px"}},
            {
                "selector": "edge",
                "style": {
                    "label": "data(label)",
                    "font-size": "8px",
                    "curve-style": "bezier",
                },
            },
        ],
    )

# --- UIコンポーネント生成関数 ---
def create_metric_card(label: str, value: str, color: str = "#1f77b4") -> html.Div:
    """メトリクスカードを作成"""
    return html.Div([
        html.Div(label, style={  # type: ignore
            'fontSize': '14px',
            'color': '#666',
            'marginBottom': '5px'
        }),
        html.Div(value, style={  # type: ignore
            'fontSize': '24px',
            'fontWeight': 'bold',
            'color': color
        })
    ], style={
        'padding': '15px',
        'backgroundColor': 'white',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'textAlign': 'center',
        'minHeight': '80px'
    })


def create_overview_tab() -> html.Div:
    """概要タブを作成"""
    df_shortage_role = data_get('shortage_role_summary', pd.DataFrame())
    df_fairness = data_get('fairness_before', pd.DataFrame())
    df_staff = data_get('staff_stats', pd.DataFrame())
    df_alerts = data_get('stats_alerts', pd.DataFrame())

    # メトリクス計算（重複カウントを回避）
    # 総不足時間の正しい計算
    lack_h = 0
    if not df_shortage_role.empty and 'lack_h' in df_shortage_role.columns:
        # 「全体」「合計」「総計」の行がある場合はそれを使用
        total_rows = df_shortage_role[df_shortage_role['role'].isin(['全体', '合計', '総計'])]
        if not total_rows.empty:
            lack_h = total_rows['lack_h'].iloc[0]
        else:
            # shortage_timeから直接計算する方が正確
            shortage_time_df = data_get('shortage_time', pd.DataFrame())
            if not shortage_time_df.empty:
                # 各セルの値を合計（30分単位なので0.5時間）
                try:
                    shortage_values = shortage_time_df.select_dtypes(include=[np.number]).values
                    if shortage_values.size > 0:
                        total_slots = np.nansum(shortage_values)
                        if np.isfinite(total_slots):
                            lack_h = float(total_slots * 0.5)
                        else:
                            log.warning("shortage_time計算で無限値またはNaNが検出されました")
                            lack_h = df_shortage_role['lack_h'].sum()
                    else:
                        log.debug("shortage_time_dfに数値データがありません")
                        lack_h = df_shortage_role['lack_h'].sum()
                except Exception as e:
                    log.debug(f"shortage_time計算でエラー: {e}")
                    # フォールバック：職種別の合計（重複の可能性あり）
                    lack_h = df_shortage_role['lack_h'].sum()
            else:
                # 最終的なフォールバック
                lack_h = df_shortage_role['lack_h'].sum()
    
    # コスト計算も同様に修正
    excess_cost = 0
    lack_temp_cost = 0
    lack_penalty_cost = 0
    
    if not df_shortage_role.empty:
        # 合計行があるかチェック
        total_rows = df_shortage_role[df_shortage_role['role'].isin(['全体', '合計', '総計'])]
        if not total_rows.empty:
            excess_cost = total_rows['estimated_excess_cost'].iloc[0] if 'estimated_excess_cost' in total_rows.columns else 0
            lack_temp_cost = total_rows['estimated_lack_cost_if_temporary_staff'].iloc[0] if 'estimated_lack_cost_if_temporary_staff' in total_rows.columns else 0
            lack_penalty_cost = total_rows['estimated_lack_penalty_cost'].iloc[0] if 'estimated_lack_penalty_cost' in total_rows.columns else 0
        else:
            # 合計行がない場合は、重複を考慮せずに合計
            excess_cost = df_shortage_role['estimated_excess_cost'].sum() if 'estimated_excess_cost' in df_shortage_role.columns else 0
            lack_temp_cost = df_shortage_role['estimated_lack_cost_if_temporary_staff'].sum() if 'estimated_lack_cost_if_temporary_staff' in df_shortage_role.columns else 0
            lack_penalty_cost = df_shortage_role['estimated_lack_penalty_cost'].sum() if 'estimated_lack_penalty_cost' in df_shortage_role.columns else 0

    # Jain指数の安全な取得
    jain_index = "N/A"
    try:
        if not df_fairness.empty and 'metric' in df_fairness.columns:
            jain_row = df_fairness[df_fairness['metric'] == 'jain_index']
            if not jain_row.empty and 'value' in jain_row.columns:
                value = jain_row['value'].iloc[0]
                if pd.notna(value):
                    jain_index = f"{float(value):.3f}"
    except (ValueError, TypeError, IndexError) as e:
        log.debug(f"Jain指数の計算でエラー: {e}")
        jain_index = "エラー"

    # 基本統計の安全な計算
    staff_count = len(df_staff) if not df_staff.empty else 0
    avg_night_ratio = 0
    try:
        if not df_staff.empty and 'night_ratio' in df_staff.columns:
            night_ratios = df_staff['night_ratio'].dropna()
            avg_night_ratio = float(night_ratios.mean()) if len(night_ratios) > 0 else 0
    except (ValueError, TypeError) as e:
        log.debug(f"夜勤比率の計算でエラー: {e}")
        avg_night_ratio = 0
    
    alerts_count = len(df_alerts) if not df_alerts.empty else 0

    return html.Div([
        html.Div(id='overview-insights', style={  # type: ignore
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("分析概要", style={'marginBottom': '20px'}),  # type: ignore
        # 📊 重要指標を大きく表示（最優先）
        html.Div([  # type: ignore
            html.Div([
                html.Div([
                    html.H2(f"{lack_h:.1f}", style={
                        'margin': '0', 'color': '#d32f2f' if lack_h > 100 else '#2e7d32', 
                        'fontSize': '3rem', 'fontWeight': 'bold'
                    }),
                    html.P("総不足時間(h)", style={'margin': '5px 0', 'fontSize': '1.1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white',
                    'borderRadius': '12px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.12)',
                    'border': f"3px solid {'#d32f2f' if lack_h > 100 else '#2e7d32'}"
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(f"{excess_cost:,.0f}", style={
                        'margin': '0', 'color': '#ff9800', 'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("総過剰コスト(¥)", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': '2px solid #ff9800'
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(f"{lack_temp_cost:,.0f}", style={
                        'margin': '0', 'color': '#f44336', 'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("不足コスト(派遣)(¥)", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': '2px solid #f44336'
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(str(alerts_count), style={
                        'margin': '0', 'color': '#ff7f0e' if alerts_count > 0 else '#1f77b4', 
                        'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("アラート数", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': f"2px solid {'#ff7f0e' if alerts_count > 0 else '#1f77b4'}"
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
        ], style={'marginBottom': '20px'}),
        
        # 📈 詳細指標を小さく表示（補助情報）
        html.Div([  # type: ignore
            html.Div([
                create_metric_card("夜勤 Jain指数", jain_index),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("総スタッフ数", str(staff_count)),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("平均夜勤比率", f"{avg_night_ratio:.3f}"),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("不足ペナルティ(¥)", f"{lack_penalty_cost:,.0f}"),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                html.Div([
                    html.P(f"総不足率: {(lack_h / (lack_h + 100)) * 100:.1f}%" if lack_h > 0 else "総不足率: 0%", 
                           style={'margin': '0', 'fontSize': '0.9rem', 'textAlign': 'center'})
                ], style={
                    'padding': '10px', 'backgroundColor': 'white', 'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'minHeight': '60px', 'display': 'flex',
                    'alignItems': 'center', 'justifyContent': 'center'
                }),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
        ], style={'marginBottom': '30px'}),
    ])


def create_heatmap_tab() -> html.Div:
    """ヒートマップタブのレイアウトを生成します。上下2つの比較エリアを持ちます。"""
    roles = data_get('roles', [])
    employments = data_get('employments', [])

    # 比較エリアを1つ生成するヘルパー関数
    def create_comparison_area(area_id: int):
        return html.Div([  # type: ignore
            html.H4(f"比較エリア {area_id}", style={'marginTop': '20px', 'borderTop': '2px solid #ddd', 'paddingTop': '20px'}),  # type: ignore

            # --- 各エリアに職種と雇用形態の両方のフィルターを設置 ---
            html.Div([  # type: ignore
                html.Div([  # type: ignore
                    html.Label("職種フィルター"),  # type: ignore
                    dcc.Dropdown(
                        id={'type': 'heatmap-filter-role', 'index': area_id},
                        options=[{'label': 'すべて', 'value': 'all'}] + [{'label': r, 'value': r} for r in roles],
                        value='all',
                        clearable=False
                    )
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),

                html.Div([  # type: ignore
                    html.Label("雇用形態フィルター"),  # type: ignore
                    dcc.Dropdown(
                        id={'type': 'heatmap-filter-employment', 'index': area_id},
                        options=[{'label': 'すべて', 'value': 'all'}] + [{'label': e, 'value': e} for e in employments],
                        value='all',
                        clearable=False
                    )
                ], style={'width': '48%', 'display': 'inline-block'}),
            ], style={'marginBottom': '10px'}),

            # --- グラフ描画領域 ---
            dcc.Loading(
                id={'type': 'loading-heatmap', 'index': area_id},
                children=html.Div(id={'type': 'graph-output-heatmap', 'index': area_id})
            )
        ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '10px'})

    return html.Div([
        html.H3("ヒートマップ比較分析", style={'marginBottom': '20px'}),  # type: ignore
        html.P("上下のエリアでそれぞれ「職種」と「雇用形態」の組み合わせを選択し、ヒートマップを比較してください。"),  # type: ignore
        create_comparison_area(1),
        create_comparison_area(2)
    ])


def create_shortage_tab() -> html.Div:
    """不足分析タブを作成"""
    df_shortage_role = data_get('shortage_role_summary', pd.DataFrame())
    df_shortage_emp = data_get('shortage_employment_summary', pd.DataFrame())

    content = [html.Div(id='shortage-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("不足分析", style={'marginBottom': '20px'}),  # type: ignore
        html.Div(  # type: ignore
            dcc.Markdown(
                "\n".join(
                    [
                        "### 計算に使用したパラメータ",
                        f"- Need算出方法: {data_get('need_method', 'N/A')}",
                        f"- Upper算出方法: {data_get('upper_method', 'N/A')}",
                        f"- 直接雇用単価: ¥{data_get('wage_direct', 0):,.0f}/h",
                        f"- 派遣単価: ¥{data_get('wage_temp', 0):,.0f}/h",
                        f"- 採用コスト: ¥{data_get('hiring_cost', 0):,}/人",
                        f"- 不足ペナルティ: ¥{data_get('penalty_cost', 0):,.0f}/h",
                    ]
                )
            ),
            style={
                'backgroundColor': '#e9f2fa',
                'padding': '10px',
                'borderRadius': '8px',
                'border': '1px solid #cce5ff',
                'marginBottom': '20px'
            },
        )]

    # 職種別不足分析
    if not df_shortage_role.empty:
        content.append(html.H4("職種別不足時間"))  # type: ignore

        # サマリーメトリクス（重複カウントを回避）
        total_lack = 0
        if 'lack_h' in df_shortage_role.columns:
            # 「全体」「合計」「総計」の行がある場合はそれを使用
            total_rows = df_shortage_role[df_shortage_role['role'].isin(['全体', '合計', '総計'])]
            if not total_rows.empty:
                total_lack = total_rows['lack_h'].iloc[0]
            else:
                # 🔧 修正: 雇用形態データを除外してから合計計算
                role_only_df = df_shortage_role[~df_shortage_role['role'].str.startswith('emp_', na=False)]
                if not role_only_df.empty:
                    total_lack = role_only_df['lack_h'].sum()
                else:
                    # shortage_timeから直接計算
                    shortage_time_df = data_get('shortage_time', pd.DataFrame())
                    if not shortage_time_df.empty:
                        try:
                            shortage_values = shortage_time_df.select_dtypes(include=[np.number]).values
                            total_lack = float(np.nansum(shortage_values) * 0.5)
                        except:
                            total_lack = df_shortage_role['lack_h'].sum()
                    else:
                        total_lack = df_shortage_role['lack_h'].sum()
        if total_lack > 0:
            top_roles = df_shortage_role.nlargest(3, 'lack_h')[['role', 'lack_h']]
            metrics = [
                html.Div([
                    create_metric_card("総不足時間", f"{total_lack:.1f}h")
                ], style={'width': '25%', 'display': 'inline-block', 'padding': '5px'})
            ]
            for i, row in enumerate(top_roles.itertuples(index=False)):
                metrics.append(
                    html.Div([
                        create_metric_card(f"不足Top{i+1}", f"{row.role}: {row.lack_h:.1f}h")  # type: ignore
                    ], style={'width': '25%', 'display': 'inline-block', 'padding': '5px'})
                )
            content.append(html.Div(metrics, style={'marginBottom': '20px'}))

        # 職種別不足時間グラフ
        fig_role_lack = px.bar(
            df_shortage_role,
            x='role',
            y='lack_h',
            title='職種別不足時間',
            labels={'role': '職種', 'lack_h': '不足時間(h)'},
            color_discrete_sequence=['#FFA500']
        )
        content.append(dcc.Graph(figure=fig_role_lack))

        # 職種別過剰時間グラフ
        if 'excess_h' in df_shortage_role.columns:
            fig_role_excess = px.bar(
                df_shortage_role,
                x='role',
                y='excess_h',
                title='職種別過剰時間',
                labels={'role': '職種', 'excess_h': '過剰時間(h)'},
                color_discrete_sequence=['#00BFFF']
            )
            content.append(dcc.Graph(figure=fig_role_excess))

    # 雇用形態別不足分析
    if not df_shortage_emp.empty:
        content.append(html.H4("雇用形態別不足時間", style={'marginTop': '30px'}))  # type: ignore

        fig_emp_lack = px.bar(
            df_shortage_emp,
            x='employment',
            y='lack_h',
            title='雇用形態別不足時間',
            labels={'employment': '雇用形態', 'lack_h': '不足時間(h)'},
            color_discrete_sequence=['#2ca02c']
        )
        content.append(dcc.Graph(figure=fig_emp_lack))

    # 不足率ヒートマップセクション
    content.append(html.Div([
        html.H4("不足率ヒートマップ", style={'marginTop': '30px'}),  # type: ignore
        html.P("各時間帯で必要人数に対してどれくらいの割合で人員が不足していたかを示します。"),  # type: ignore
        html.Div([  # type: ignore
            html.Label("表示範囲"),  # type: ignore
            dcc.Dropdown(
                id='shortage-heatmap-scope',
                options=[
                    {'label': '全体', 'value': 'overall'},
                    {'label': '職種別', 'value': 'role'},
                    {'label': '雇用形態別', 'value': 'employment'}
                ],
                value='overall',
                style={'width': '200px'}
            ),
        ], style={'marginBottom': '10px'}),
        html.Div(id='shortage-heatmap-detail-container'),
        html.Div(id='shortage-ratio-heatmap')
    ]))

    # Factor Analysis section
    content.append(html.Hr())
    content.append(html.H4('要因分析 (AI)', style={'marginTop': '30px'}))  # type: ignore
    content.append(html.Button('要因分析モデルを学習', id='factor-train-button', n_clicks=0))  # type: ignore
    content.append(html.Div(id='factor-output'))  # type: ignore

    # Over/Short Log section
    events_df = data_get('shortage_events', pd.DataFrame())
    if not events_df.empty:
        content.append(html.Hr())  # type: ignore
        content.append(html.H4('過不足手動ログ', style={'marginTop': '30px'}))  # type: ignore
        content.append(dash_table.DataTable(
            id='over-shortage-table',
            data=events_df.to_dict('records'),
            columns=[{'name': c, 'id': c, 'presentation': 'input'} for c in events_df.columns],
            editable=True,
        ))
        content.append(dcc.RadioItems(
            id='log-save-mode',
            options=[{'label': '追記', 'value': 'append'}, {'label': '上書き', 'value': 'overwrite'}],
            value='追記',
            inline=True,
            style={'marginTop': '10px'}
        ))
        content.append(html.Button('ログを保存', id='save-log-button', n_clicks=0, style={'marginTop': '10px'}))  # type: ignore
        content.append(html.Div(id='save-log-msg'))  # type: ignore

    return html.Div(content)


def create_optimization_tab() -> html.Div:
    """最適化分析タブを作成"""
    return html.Div([  # type: ignore
        html.Div(id='optimization-insights', style={
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("最適化分析", style={'marginBottom': '20px'}),  # type: ignore
        html.Div([  # type: ignore
            html.Label("表示範囲"),  # type: ignore
            dcc.Dropdown(
                id='opt-scope',
                options=[
                    {'label': '全体', 'value': 'overall'},
                    {'label': '職種別', 'value': 'role'},
                    {'label': '雇用形態別', 'value': 'employment'}
                ],
                value='overall',
                clearable=False
            ),
        ], style={'width': '30%', 'marginBottom': '20px'}),
        html.Div(id='opt-detail-container'),  # type: ignore
        html.Div(id='optimization-content')  # type: ignore
    ])


def create_leave_analysis_tab() -> html.Div:
    """休暇分析タブを作成"""
    content = [html.Div(id='leave-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("休暇分析", style={'marginBottom': '20px'})]  # type: ignore

    df_staff_balance = data_get('staff_balance_daily', pd.DataFrame())
    df_daily_summary = data_get('daily_summary', pd.DataFrame())
    df_concentration = data_get('concentration_requested', pd.DataFrame())
    df_ratio_breakdown = data_get('leave_ratio_breakdown', pd.DataFrame())

    if not df_staff_balance.empty:
        fig_balance = px.line(
            df_staff_balance,
            x='date',
            y=['total_staff', 'leave_applicants_count', 'non_leave_staff'],
            title='勤務予定人数と全休暇取得者数の推移',
            labels={'value': '人数', 'variable': '項目', 'date': '日付'},
            markers=True
        )
        fig_balance.update_xaxes(tickformat="%m/%d(%a)")
        content.append(dcc.Graph(figure=fig_balance))
        content.append(dash_table.DataTable(
            data=df_staff_balance.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_staff_balance.columns]
        ))

    if not df_daily_summary.empty:
        fig_breakdown = px.bar(
            df_daily_summary,
            x='date',
            y='total_leave_days',
            color='leave_type',
            barmode='stack',
            title='日別 休暇取得者数（内訳）',
            labels={'date': '日付', 'total_leave_days': '休暇取得者数', 'leave_type': '休暇タイプ'}
        )
        fig_breakdown.update_xaxes(tickformat="%m/%d(%a)")
        content.append(dcc.Graph(figure=fig_breakdown))

    if not df_ratio_breakdown.empty:
        fig_ratio_break = px.bar(
            df_ratio_breakdown,
            x='dayofweek',
            y='leave_ratio',
            color='leave_type',
            facet_col='month_period',
            category_orders={
                'dayofweek': ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日'],
                'month_period': ['月初(1-10日)', '月中(11-20日)', '月末(21-末日)'],
            },
            labels={'dayofweek': '曜日', 'leave_ratio': '割合', 'leave_type': '休暇タイプ', 'month_period': '月期間'},
            title='曜日・月期間別休暇取得率'
        )
        content.append(dcc.Graph(figure=fig_ratio_break))

    if not df_concentration.empty:
        fig_conc = go.Figure()
        fig_conc.add_trace(go.Scatter(
            x=df_concentration['date'],
            y=df_concentration['leave_applicants_count'],
            mode='lines+markers',
            name='休暇申請者数',
            line=dict(shape='spline', smoothing=0.5),
            marker=dict(size=6)
        ))
        if 'is_concentrated' in df_concentration.columns:
            concentrated = df_concentration[df_concentration['is_concentrated']]
            if not concentrated.empty:
                fig_conc.add_trace(go.Scatter(
                    x=concentrated['date'],
                    y=concentrated['leave_applicants_count'],
                    mode='markers',
                    marker=dict(color='red', size=12, symbol='diamond'),
                    name='閾値超過日',
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>申請者数: %{y}人<extra></extra>'
                ))

        fig_conc.update_layout(
            title='希望休 申請者数の推移と集中日',
            xaxis_title='日付',
            yaxis_title='申請者数'
        )
        fig_conc.update_xaxes(tickformat="%m/%d(%a)")
        content.append(dcc.Graph(figure=fig_conc))

    return html.Div(content)


def create_cost_analysis_tab() -> html.Div:
    """コスト分析タブを作成"""
    return html.Div([
        html.Div(id='cost-insights', style={
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("人件費分析", style={'marginBottom': '20px'}),

        html.H4("動的コストシミュレーション", style={'marginTop': '30px'}),
        dcc.RadioItems(
            id='cost-by-radio',
            options=[
                {'label': '職種別', 'value': 'role'},
                {'label': '雇用形態別', 'value': 'employment'},
                {'label': 'スタッフ別', 'value': 'staff'},
            ],
            value='role',
            inline=True,
            style={'marginBottom': '10px'},
        ),
        html.Div(id='wage-input-container'),

        dcc.Loading(
            id="loading-cost-analysis",
            type="circle",
            children=html.Div(id='cost-analysis-content')
        )
    ])


def create_hire_plan_tab() -> html.Div:
    """採用計画タブを作成"""
    content = [html.Div(id='hire-plan-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("採用計画", style={'marginBottom': '20px'})]  # type: ignore

    df_hire = data_get('hire_plan', pd.DataFrame())
    df_shortage_role = data_get('shortage_role_summary', pd.DataFrame())
    
    if not df_hire.empty:
        content.append(html.H4("必要FTE（職種別）"))  # type: ignore

        # カラム名を日本語に翻訳
        df_hire_display = df_hire.copy()
        column_translations = {
            'role': '職種',
            'hire_fte': '必要FTE',
            'shortage_hours': '不足時間',
            'current_fte': '現在FTE',
            'target_fte': '目標FTE',
            'priority': '優先度',
            'cost_per_fte': 'FTE単価',
            'total_cost': '総コスト'
        }
        df_hire_display.rename(columns=column_translations, inplace=True)

        # テーブル表示
        content.append(dash_table.DataTable(
            data=df_hire_display.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df_hire_display.columns],
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
        ))

        # グラフ表示（元の列名を使用）
        if 'role' in df_hire.columns and 'hire_fte' in df_hire.columns:
            fig_hire = px.bar(
                df_hire,
                x='role',
                y='hire_fte',
                title='職種別必要FTE',
                labels={'role': '職種', 'hire_fte': '必要FTE'},
                color_discrete_sequence=['#1f77b4']
            )
            content.append(dcc.Graph(figure=fig_hire))

        # 採用戦略提案セクション
        content.append(html.Div([
            html.H4("採用戦略の提案", style={'marginTop': '30px'}),
            html.P("分析結果に基づく採用優先度と戦略的アプローチ："),
            html.Ul([
                html.Li("最も不足の深刻な職種から優先的に採用を検討"),
                html.Li("季節性を考慮した採用タイミングの最適化"),
                html.Li("既存職員の負荷軽減効果の予測"),
                html.Li("コスト効率の高い採用チャネルの活用")
            ])
        ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'marginTop': '20px'}))

    # 最適採用計画
    df_optimal = data_get('optimal_hire_plan', pd.DataFrame())
    if not df_optimal.empty:
        content.append(html.H4("最適採用計画", style={'marginTop': '30px'}))  # type: ignore
        content.append(html.P("分析の結果、以下の具体的な採用計画を推奨します。"))
        
        # カラム名を日本語に翻訳
        df_optimal_display = df_optimal.copy()
        df_optimal_display.rename(columns=column_translations, inplace=True)
        
        content.append(dash_table.DataTable(
            data=df_optimal_display.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df_optimal_display.columns],
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
        ))

    return html.Div(content)


def create_fatigue_tab() -> html.Div:
    """疲労分析タブを作成"""
    explanation = """
    #### 疲労分析の評価方法
    スタッフの疲労スコアは、以下の要素を総合的に評価して算出されます。各要素は、全スタッフ内での相対的な位置（偏差）に基づいてスコア化され、重み付けされて合計されます。
    - **勤務開始時刻のばらつき:** 出勤時刻が不規則であるほどスコアが高くなります。
    - **業務の多様性:** 担当する業務（勤務コード）の種類が多いほどスコアが高くなります。
    - **労働時間のばらつき:** 日々の労働時間が不規則であるほどスコアが高くなります。
    - **短い休息期間:** 勤務間のインターバルが短い頻度が高いほどスコアが高くなります。
    - **連勤:** 3連勤以上の連続勤務が多いほどスコアが高くなります。
    - **夜勤比率:** 全勤務に占める夜勤の割合が高いほどスコアが高くなります。

    *デフォルトでは、これらの要素は均等な重み（各1.0）で評価されます。*
    """
    content = [
        html.Div(  # type: ignore
            dcc.Markdown(explanation),
            style={
                'padding': '15px',
                'backgroundColor': '#e9f2fa',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #cce5ff',
            },
        ),
        html.H3("疲労分析", style={'marginBottom': '20px'}),  # type: ignore
    ]
    df_fatigue = data_get('fatigue_score', pd.DataFrame())

    if not df_fatigue.empty:
        # カラム名を日本語に翻訳
        df_fatigue_display = df_fatigue.reset_index().rename(columns={'index': 'staff'})
        column_translations = {
            'staff': '職員名',
            'fatigue_score': '疲労スコア',
            'work_start_variance': '勤務開始時刻のばらつき',
            'work_diversity': '業務の多様性',
            'work_duration_variance': '労働時間のばらつき',
            'short_rest_frequency': '短い休息期間の頻度',
            'consecutive_work_days': '連勤回数',
            'night_shift_ratio': '夜勤比率'
        }
        df_fatigue_display.rename(columns=column_translations, inplace=True)

        # 1. 従来の棒グラフ
        fig_bar = px.bar(
            df_fatigue_display,
            x='職員名',
            y='疲労スコア',
            title='スタッフ別疲労スコア',
            labels={'職員名': '職員名', '疲労スコア': '疲労スコア'},
            color='疲労スコア',
            color_continuous_scale='Reds'
        )
        content.append(dcc.Graph(figure=fig_bar))

        # 2. ヒートマップ（疲労要因の詳細分析）
        fatigue_factors = ['勤務開始時刻のばらつき', '業務の多様性', '労働時間のばらつき', 
                         '短い休息期間の頻度', '連勤回数', '夜勤比率']
        available_factors = [col for col in fatigue_factors if col in df_fatigue_display.columns]
        
        if len(df_fatigue_display) > 1 and available_factors:
            # データを正規化（0-1スケール）
            factor_data = df_fatigue_display[available_factors].copy()
            for col in available_factors:
                if factor_data[col].max() != factor_data[col].min():
                    factor_data[col] = (factor_data[col] - factor_data[col].min()) / (factor_data[col].max() - factor_data[col].min())
            
            fig_heatmap = px.imshow(
                factor_data.T,
                x=df_fatigue_display['職員名'],
                y=available_factors,
                title='疲労要因ヒートマップ（職員別詳細分析）',
                color_continuous_scale='Reds',
                aspect='auto'
            )
            fig_heatmap.update_layout(xaxis_title="職員名", yaxis_title="疲労要因")
            content.append(dcc.Graph(figure=fig_heatmap))

        # 3. 散布図マトリックス（疲労要因間の相関）
        if len(available_factors) >= 2:
            # 2つの主要要因の散布図
            fig_scatter = px.scatter(
                df_fatigue_display,
                x=available_factors[0],
                y=available_factors[1] if len(available_factors) > 1 else available_factors[0],
                size='疲労スコア',
                hover_name='職員名',
                title=f'{available_factors[0]} vs {available_factors[1] if len(available_factors) > 1 else available_factors[0]}',
                color='疲労スコア',
                color_continuous_scale='Reds'
            )
            content.append(dcc.Graph(figure=fig_scatter))

        # 4. 疲労要因の相関マトリックス
        if len(available_factors) >= 2:
            corr_matrix = df_fatigue_display[available_factors].corr()
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                title="疲労要因間の相関マトリックス",
                color_continuous_scale='RdBu_r'
            )
            fig_corr.update_layout(
                xaxis_title="疲労要因",
                yaxis_title="疲労要因"
            )
            content.append(dcc.Graph(figure=fig_corr))

        # 5. 疲労スコア分布とボックスプロット
        fig_box = px.box(
            df_fatigue_display,
            y='疲労スコア',
            title='疲労スコアの分布（ボックスプロット）',
            points="all"  # 全データ点を表示
        )
        content.append(dcc.Graph(figure=fig_box))

        # 6. レーダーチャート（上位3名の詳細比較）
        if len(df_fatigue_display) >= 3 and available_factors:
            top3 = df_fatigue_display.nlargest(3, '疲労スコア')
            fig_radar = go.Figure()
            
            for _, row in top3.iterrows():
                factor_values = [row[factor] for factor in available_factors]
                # 正規化（0-1スケール）
                max_val = max(factor_values) if max(factor_values) > 0 else 1
                min_val = min(factor_values)
                normalized_values = [(val - min_val) / (max_val - min_val) if max_val != min_val else 0.5 for val in factor_values]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=normalized_values,
                    theta=available_factors,
                    fill='toself',
                    name=row['職員名'],
                    opacity=0.7
                ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1])
                ),
                title="疲労度上位3名の要因比較（レーダーチャート）",
                showlegend=True
            )
            content.append(dcc.Graph(figure=fig_radar))

        # 7. 疲労度ランキング
        if '疲労スコア' in df_fatigue_display.columns:
            ranking = df_fatigue_display.sort_values('疲労スコア', ascending=False)[['職員名', '疲労スコア']]
            ranking.index = range(1, len(ranking) + 1)
            ranking.index.name = '順位'
            ranking = ranking.reset_index()
            content.append(html.H4('疲労度ランキング'))
            content.append(dash_table.DataTable(
                data=ranking.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in ranking.columns],
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 0},
                        'backgroundColor': '#ffebee',
                        'color': 'black',
                    },
                    {
                        'if': {'row_index': 1},
                        'backgroundColor': '#fff3e0',
                        'color': 'black',
                    },
                    {
                        'if': {'row_index': 2},
                        'backgroundColor': '#fff8e1',
                        'color': 'black',
                    }
                ]
            ))

        # データテーブル
        content.append(html.H4("詳細データ", style={'marginTop': '30px'}))
        content.append(dash_table.DataTable(
            data=df_fatigue_display.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_fatigue_display.columns],
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            sort_action="native"
        ))
    else:
        content.append(html.P("疲労分析データが見つかりません。"))  # type: ignore

    return html.Div(content)


def create_forecast_tab() -> html.Div:
    """需要予測タブを作成"""
    content = [html.Div(id='forecast-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("需要予測", style={'marginBottom': '20px'})]  # type: ignore
    df_fc = data_get('forecast', pd.DataFrame())
    df_actual = data_get('demand_series', pd.DataFrame())

    if not df_fc.empty:
        fig = go.Figure()
        if {'ds', 'yhat'}.issubset(df_fc.columns):
            fig.add_trace(go.Scatter(x=df_fc['ds'], y=df_fc['yhat'], mode='lines+markers', name='予測'))
        if not df_actual.empty and {'ds', 'y'}.issubset(df_actual.columns):
            fig.add_trace(go.Scatter(x=df_actual['ds'], y=df_actual['y'], mode='lines', name='実績', line=dict(dash='dash')))
        fig.update_layout(title='需要予測と実績', xaxis_title='日付', yaxis_title='需要')
        content.append(dcc.Graph(figure=fig))
        content.append(dash_table.DataTable(
            data=df_fc.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_fc.columns]
        ))
    else:
        content.append(html.P("需要予測データが見つかりません。"))  # type: ignore

    return html.Div(content)


def create_fairness_tab() -> html.Div:
    """公平性タブを作成"""
    explanation = """
    #### 公平性分析の評価方法
    スタッフ間の「不公平感」は、各個人の働き方が全体の平均からどれだけ乖離しているかに基づいてスコア化されます。以下の要素の乖離度を均等に評価し、その平均値を「不公平感スコア」としています。
    - **夜勤比率の乖離:** 他のスタッフと比較して、夜勤の割合が極端に多い、または少ない。
    - **総労働時間（スロット数）の乖離:** 他のスタッフと比較して、総労働時間が極端に多い、または少ない。
    - **連休取得頻度の乖離:** 他のスタッフと比較して、連休の取得しやすさに差がある。

    *スコアが高いほど、これらの要素において平均からの乖離が大きい（＝不公平感を感じやすい可能性がある）ことを示します。*
    """
    content = [
        html.Div(  # type: ignore
            dcc.Markdown(explanation),
            style={
                'padding': '15px',
                'backgroundColor': '#f0f0f0',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #ddd',
            },
        ),
        html.H3("公平性 (不公平感スコア)", style={'marginBottom': '20px'}),  # type: ignore
    ]
    df_fair = data_get('fairness_after', pd.DataFrame())

    if not df_fair.empty:
        # カラム名を日本語に翻訳
        df_fair_display = df_fair.copy()
        column_translations = {
            'staff': '職員名',
            'unfairness_score': '不公平感スコア',
            'fairness_score': '公平性スコア',
            'night_ratio': '夜勤比率',
            'dev_night_ratio': '夜勤比率の乖離',
            'dev_work_slots': '総労働時間の乖離',
            'dev_consecutive': '連休取得頻度の乖離',
            'work_slots': '総労働時間',
            'consecutive_holidays': '連休取得回数'
        }
        df_fair_display.rename(columns=column_translations, inplace=True)

        metric_col = (
            '不公平感スコア'
            if '不公平感スコア' in df_fair_display.columns
            else ('公平性スコア' if '公平性スコア' in df_fair_display.columns else '夜勤比率')
        )

        # 1. 従来の棒グラフ（改良版）
        fig_bar = px.bar(
            df_fair_display,
            x='職員名',
            y=metric_col,
            labels={'職員名': '職員名', metric_col: 'スコア'},
            color=metric_col,
            color_continuous_scale='RdYlBu_r',
            title='職員別不公平感スコア'
        )
        avg_val = df_fair_display[metric_col].mean()
        fig_bar.add_hline(y=avg_val, line_dash='dash', line_color='red', annotation_text="平均値")
        content.append(dcc.Graph(figure=fig_bar))

        # 2. 公平性要因の散布図マトリックス
        fairness_factors = ['夜勤比率の乖離', '総労働時間の乖離', '連休取得頻度の乖離']
        available_factors = [col for col in fairness_factors if col in df_fair_display.columns]
        
        if len(available_factors) >= 2:
            # 散布図: 2つの主要要因の関係
            fig_scatter = px.scatter(
                df_fair_display,
                x=available_factors[0],
                y=available_factors[1],
                size=metric_col,
                hover_name='職員名',
                title=f'{available_factors[0]} vs {available_factors[1]}',
                color=metric_col,
                color_continuous_scale='RdYlBu_r'
            )
            content.append(dcc.Graph(figure=fig_scatter))

        # 3. 公平性要因のヒートマップ
        if available_factors:
            factor_data = df_fair_display[available_factors].copy()
            # データを正規化
            for col in available_factors:
                if factor_data[col].max() != factor_data[col].min():
                    factor_data[col] = (factor_data[col] - factor_data[col].min()) / (factor_data[col].max() - factor_data[col].min())
            
            fig_heatmap = px.imshow(
                factor_data.T,
                x=df_fair_display['職員名'],
                y=available_factors,
                title='公平性要因ヒートマップ（職員別詳細分析）',
                color_continuous_scale='RdYlBu_r',
                aspect='auto'
            )
            fig_heatmap.update_layout(xaxis_title="職員名", yaxis_title="公平性要因")
            content.append(dcc.Graph(figure=fig_heatmap))

        # 4. 分布図とボックスプロット
        fig_hist = px.histogram(
            df_fair_display,
            x=metric_col,
            nbins=20,
            title="公平性スコア分布",
            labels={metric_col: 'スコア'}
        )
        fig_hist.update_layout(yaxis_title="人数")
        fig_hist.add_vline(x=avg_val, line_dash='dash', line_color='red', annotation_text="平均値")
        content.append(dcc.Graph(figure=fig_hist))

        # 5. レーダーチャート（不公平感上位3名）
        if len(df_fair_display) >= 3 and available_factors:
            top3 = df_fair_display.nlargest(3, metric_col)
            fig_radar = go.Figure()
            
            for _, row in top3.iterrows():
                factor_values = [abs(row[factor]) for factor in available_factors]  # 絶対値で比較
                # 正規化
                max_val = max(factor_values) if max(factor_values) > 0 else 1
                normalized_values = [val/max_val for val in factor_values]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=normalized_values,
                    theta=available_factors,
                    fill='toself',
                    name=row['職員名']
                ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1])
                ),
                title="不公平感上位3名の要因比較（レーダーチャート）"
            )
            content.append(dcc.Graph(figure=fig_radar))

        # 6. ランキングテーブル
        if '不公平感スコア' in df_fair_display.columns:
            ranking = df_fair_display.sort_values('不公平感スコア', ascending=False)[['職員名', '不公平感スコア']]
            ranking.index = range(1, len(ranking) + 1)
            ranking.index.name = '順位'
            ranking = ranking.reset_index()
            content.append(html.H4('不公平感ランキング'))  # type: ignore
            content.append(dash_table.DataTable(
                data=ranking.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in ranking.columns],
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
            ))

        # 詳細データテーブル
        content.append(html.H4("詳細データ", style={'marginTop': '30px'}))
        content.append(dash_table.DataTable(
            data=df_fair_display.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_fair_display.columns],
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            sort_action="native"
        ))
    else:
        content.append(html.P("公平性データが見つかりません。"))

    return html.Div(content)


def create_gap_analysis_tab() -> html.Div:
    """基準乖離分析タブを作成"""
    content = [html.Div(id='gap-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("基準乖離分析", style={'marginBottom': '20px'})]  # type: ignore
    df_summary = data_get('gap_summary', pd.DataFrame())
    df_heat = data_get('gap_heatmap', pd.DataFrame())

    if not df_summary.empty:
        content.append(dash_table.DataTable(
            data=df_summary.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in df_summary.columns]
        ))
    if not df_heat.empty:
        fig = px.imshow(
            df_heat,
            aspect='auto',
            color_continuous_scale='RdBu_r',
            labels={'x': '時間帯', 'y': '職種', 'color': '乖離'}
        )
        content.append(dcc.Graph(figure=fig))
    if df_summary.empty and df_heat.empty:
        content.append(html.P("基準乖離データが見つかりません。"))  # type: ignore

    return html.Div(content)


def create_summary_report_tab() -> html.Div:
    """サマリーレポートタブを作成"""
    content = [html.Div(id='summary-report-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("サマリーレポート", style={'marginBottom': '20px'})]  # type: ignore
    report_text = data_get('summary_report')
    if report_text:
        content.append(dcc.Markdown(report_text))
    else:
        content.append(html.P("レポートが見つかりません。"))
    return html.Div(content)


def create_ppt_report_tab() -> html.Div:
    """PowerPointレポートタブを作成"""
    return html.Div([  # type: ignore
        html.Div(id='ppt-report-insights', style={
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("PowerPointレポート", style={'marginBottom': '20px'}),  # type: ignore
        html.P("ボタンを押してPowerPointレポートを生成してください。"),  # type: ignore
        html.Button('PPTレポートを生成', id='ppt-generate', n_clicks=0)  # type: ignore
    ])


def create_individual_analysis_tab() -> html.Div:
    """職員個別分析タブを作成"""
    long_df = data_get('long_df', pd.DataFrame())

    if long_df.empty:
        return html.Div("分析の元となる勤務データ (long_df) が見つかりません。")

    staff_list = sorted(long_df['staff'].unique())

    return html.Div([
        html.H3("職員個別分析", style={'marginBottom': '20px'}),
        html.P("分析したい職員を以下から選択してください。"),
        dcc.Dropdown(
            id='individual-staff-dropdown',
            options=[{'label': staff, 'value': staff} for staff in staff_list],
            value=staff_list[0] if staff_list else None,
            clearable=False,
            style={'width': '50%', 'marginBottom': '20px'}
        ),
        
        # シナジー分析タイプ選択
        html.Div([
            html.Label("シナジー分析タイプ:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            dcc.RadioItems(
                id='synergy-analysis-type',
                options=[
                    {'label': '基本分析（全職員対象）', 'value': 'basic'},
                    {'label': '同職種限定分析', 'value': 'same_role'},
                    {'label': '全職種詳細分析', 'value': 'all_roles'},
                    {'label': '相関マトリックス（全体）', 'value': 'correlation_matrix'}
                ],
                value='basic',
                inline=True,
                style={'marginBottom': '20px'}
            ),
            html.Div([
                html.Button("キャッシュクリア", id='clear-synergy-cache-btn', className='btn btn-warning btn-sm', style={'marginRight': '10px'}),
                html.Small("※相関マトリックスは計算に時間がかかりますがキャッシュにより高速化されます", style={'color': '#666'})
            ])
        ], style={'marginBottom': '20px', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
        html.Div(id='individual-analysis-content')
    ])


def create_team_analysis_tab() -> html.Div:
    """チーム分析タブを作成"""
    long_df = data_get('long_df', pd.DataFrame())
    if long_df.empty:
        return html.Div("分析データが見つかりません。")

    filterable_cols = ['role', 'code', 'employment']

    return html.Div([
        html.H3("ダイナミック・チーム分析"),
        html.Div([
            html.P("チーム分析では、特定の条件に該当するスタッフグループの特性を分析します。"),
            html.Ul([
                html.Li("チーム構成: 選択した条件に該当するメンバーの一覧と詳細"),
                html.Li("チームダイナミクス: メンバー間の相性や協働パターン分析"),
                html.Li("パフォーマンス指標: チーム全体の効率性指標と改善提案"),
                html.Li("時間帯カバー率: チームがカバーしている時間帯の分布")
            ])
        ], style={
            'backgroundColor': '#f0f8ff',
            'padding': '15px',
            'borderRadius': '5px',
            'marginBottom': '20px'
        }),
        html.P("分析したいチームの条件を指定してください："),
        html.Div([
            dcc.Dropdown(
                id='team-criteria-key-dropdown',
                options=[{'label': col, 'value': col} for col in filterable_cols],
                value='code',
                style={'width': '200px', 'display': 'inline-block'}
            ),
            dcc.Dropdown(
                id='team-criteria-value-dropdown',
                style={
                    'width': '300px',
                    'display': 'inline-block',
                    'marginLeft': '10px'
                }
            )
        ]),
        dcc.Loading(
            id="loading-team-analysis",
            children=html.Div([
                html.Div(id='team-analysis-content'),
                html.Div(id='team-analysis-explanation', style={'marginTop': '20px'})
            ])
        )
    ])


def create_blueprint_analysis_tab() -> html.Div:
    """Return layout for blueprint analysis with facts and implicit knowledge."""
    return html.Div([
        html.H3("シフト作成プロセスの\u300c暗黙知\u300d分析", style={'marginBottom': '20px'}),
        html.P(
            "過去のシフトデータから、客観的事実と暗黙のルールを分析します。",
            style={'marginBottom': '10px'}
        ),

        # 分析タイプの選択
        html.Div([
            dcc.RadioItems(
                id='blueprint-analysis-type',
                options=[
                    {'label': '暗黙知のみ', 'value': 'implicit'},
                    {'label': '客観的事実のみ', 'value': 'facts'},
                    {'label': '統合分析（暗黙知＋事実）', 'value': 'integrated'}
                ],
                value='integrated',
                inline=True,
                style={'marginBottom': '10px'}
            )
        ]),

        html.Details([
            html.Summary('📊 分析の観点（クリックで詳細）', style={'cursor': 'pointer', 'fontWeight': 'bold'}),
            html.Div([
                html.H5("暗黙知の6つの観点"),
                html.Ul([
                    html.Li("🤝 スキル相性: 誰と誰を組ませると上手くいくか、逆に避けているか"),
                    html.Li("⚖️ 負荷分散戦略: 繁忙時間帯にどんな戦略で人を配置しているか"),
                    html.Li("👤 個人配慮: 特定職員の個人事情への配慮パターン"),
                    html.Li("🔄 ローテーション: 公平性を保つための複雑なローテーションルール"),
                    html.Li("🚨 リスク回避: トラブル防止のための暗黙の配置ルール"),
                    html.Li("📅 時系列戦略: 月初・月末、曜日による配置戦略の変化"),
                ]),
                html.H5("客観的事実の観点", style={'marginTop': '10px'}),
                html.Ul([
                    html.Li("📅 曜日パターン: 特定の曜日のみ勤務、曜日の偏り"),
                    html.Li("🏷️ コードパターン: 特定の勤務コードのみ使用、回避"),
                    html.Li("⏰ 時間帯パターン: 早朝・深夜勤務、固定時間帯"),
                    html.Li("👥 ペア関係: 頻繁に一緒に働く/働かないペア"),
                    html.Li("📊 統計的事実: 勤務頻度、平均勤務時間"),
                ])
            ], style={'padding': '10px', 'backgroundColor': '#f0f0f0', 'borderRadius': '5px', 'marginTop': '10px'})
        ], style={'marginBottom': '20px'}),

        html.Button(
            "ブループリントを生成",
            id="generate-blueprint-button",
            n_clicks=0,
            style={
                "marginTop": "10px",
                "marginBottom": "20px",
                "padding": "10px 30px",
                "fontSize": "16px",
                "backgroundColor": "#1f77b4",
                "color": "white",
                "border": "none",
                "borderRadius": "5px",
                "cursor": "pointer"
            },
        ),
        dcc.Loading(
            id="loading-blueprint",
            type="default",
            children=html.Div([
                dcc.Tabs(id='blueprint-result-tabs', children=[
                    dcc.Tab(label='暗黙知分析', value='implicit_analysis', children=[
                        html.Div([
                            html.Div([
                                html.H4("全体分析ビュー：シフト全体の傾向と暗黙知"),
                                dcc.Graph(id='tradeoff-scatter-plot'),
                                html.H5("発見された暗黙知ルール一覧"),
                                html.P("ルールをクリックすると、関連するスタッフの個別分析を表示します。"),
                                dash_table.DataTable(id='rules-data-table', row_selectable='single'),
                            ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                            html.Div([
                                html.H4("スタッフ個別ビュー：個人の働き方と価値観"),
                                dcc.Dropdown(id='staff-selector-dropdown'),
                                dcc.Graph(id='staff-radar-chart'),
                                html.H5("このスタッフに関連する暗黙知"),
                                html.Div(id='staff-related-rules-list'),
                            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingLeft': '1%'}),
                        ])
                    ]),
                    dcc.Tab(label='客観的事実', value='facts_analysis', children=[
                        html.Div([
                            html.H4("発見された客観的事実"),
                            html.Div([
                                html.Label("事実のカテゴリーでフィルター:"),
                                dcc.Dropdown(
                                    id='fact-category-filter',
                                    options=[
                                        {'label': '全て表示', 'value': 'all'},
                                        {'label': '勤務パターン事実', 'value': '勤務パターン事実'},
                                        {'label': '曜日事実', 'value': '曜日事実'},
                                        {'label': 'コード事実', 'value': 'コード事実'},
                                        {'label': '時間帯事実', 'value': '時間帯事実'},
                                        {'label': 'ペア事実', 'value': 'ペア事実'},
                                        {'label': '統計的事実', 'value': '統計的事実'}
                                    ],
                                    value='all',
                                    clearable=False
                                )
                            ], style={'width': '300px', 'marginBottom': '20px'}),
                            dash_table.DataTable(
                                id='facts-data-table',
                                columns=[
                                    {'name': 'スタッフ', 'id': 'スタッフ'},
                                    {'name': 'カテゴリー', 'id': 'カテゴリー'},
                                    {'name': '事実タイプ', 'id': '事実タイプ'},
                                    {'name': '詳細', 'id': '詳細'},
                                    {'name': '確信度', 'id': '確信度', 'type': 'numeric', 'format': {'specifier': '.2f'}}
                                ],
                                style_data_conditional=[
                                    {
                                        'if': {
                                            'column_id': '確信度',
                                            'filter_query': '{確信度} >= 0.8'
                                        },
                                        'backgroundColor': '#3D9970',
                                        'color': 'white',
                                    },
                                    {
                                        'if': {
                                            'column_id': '確信度',
                                            'filter_query': '{確信度} < 0.5'
                                        },
                                        'backgroundColor': '#FFDC00',
                                    }
                                ],
                                sort_action='native',
                                filter_action='native',
                                page_size=20
                            ),
                            html.Div(id='facts-summary', style={'marginTop': '20px'})
                        ])
                    ]),
                    dcc.Tab(label='統合分析', value='integrated_analysis', children=[
                        html.Div([
                            html.H4("事実と暗黙知の関連"),
                            html.P("客観的事実がどのような暗黙知につながっているかを分析します。"),
                            html.Div(id='integrated-analysis-content')
                        ])
                    ])
                ], value='implicit_analysis'),
            ], id='blueprint-analysis-content')
        ),
    ])

# --- メインレイアウト ---
app.layout = html.Div([
    dcc.Store(id='kpi-data-store', storage_type='memory'),
    dcc.Store(id='data-loaded', storage_type='memory'),
    dcc.Store(id='full-analysis-store', storage_type='memory'),
    dcc.Store(id='creation-logic-results-store', storage_type='memory'),
    dcc.Store(id='logic-analysis-progress', storage_type='memory'),
    dcc.Store(id='blueprint-results-store', storage_type='memory'),
    dcc.Interval(id='logic-analysis-interval', interval=500, disabled=True),

    # ヘッダー
    html.Div([  # type: ignore
        html.H1("🗂️ Shift-Suite 高速分析ビューア", style={
            'textAlign': 'center',
            'color': 'white',
            'margin': '0',
            'padding': '20px'
        })
    ], style={
        'backgroundColor': '#2c3e50',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),

    # アップロードエリア
    html.Div([  # type: ignore
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                '分析結果のZIPファイルをドラッグ＆ドロップ または ',
                html.A('クリックして選択', style={'textDecoration': 'underline'})
            ]),
            style={
                'width': '100%',
                'height': '100px',
                'lineHeight': '100px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '10px',
                'textAlign': 'center',
                'margin': '20px 0',
                'backgroundColor': '#f8f9fa',
                'cursor': 'pointer'
            },
            multiple=False
        ),
    ], style={'padding': '0 20px'}),

    html.Div([  # type: ignore
        html.H3("分析シナリオ選択", style={'textAlign': 'center'}),
        dcc.Dropdown(
            id='scenario-dropdown',
            placeholder="まず分析結果のZIPファイルをアップロードしてください",
            style={'width': '60%', 'margin': 'auto'}
        )
    ], id='scenario-selector-div', style={'display': 'none'}),

    # メインコンテンツ
    html.Div(id='main-content', style={'padding': '20px'}),  # type: ignore

    # リアルタイムログビューア
    html.Details([
        html.Summary('リアルタイムログを表示/非表示'),
        dcc.Textarea(id='log-viewer', style={'width': '100%', 'height': 300}, readOnly=True)
    ], style={'padding': '0 20px'}),
    dcc.Interval(id='log-interval', interval=1000),

], style={'backgroundColor': '#f5f5f5', 'minHeight': '100vh'})

# --- コールバック関数 ---
@app.callback(
    Output('data-loaded', 'data'),
    Output('scenario-dropdown', 'options'),
    Output('scenario-dropdown', 'value'),
    Output('scenario-selector-div', 'style'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
@safe_callback
def process_upload(contents, filename):
    """ZIPファイルをアップロードしてシナリオを検出"""
    if contents is None:
        raise PreventUpdate

    global TEMP_DIR_OBJ

    log.info(f"Received upload: {filename}")

    # 一時ディレクトリ作成
    if TEMP_DIR_OBJ:
        TEMP_DIR_OBJ.cleanup()

    TEMP_DIR_OBJ = tempfile.TemporaryDirectory(prefix="shift_suite_dash_")
    temp_dir_path = Path(TEMP_DIR_OBJ.name)
    log.debug(f"Created temp dir {temp_dir_path}")

    # ZIPファイルを展開
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
            zf.extractall(temp_dir_path)
        log.info(f"Extracted ZIP to {temp_dir_path}")

        scenarios = [d.name for d in temp_dir_path.iterdir() if d.is_dir() and d.name.startswith('out_')]
        if not scenarios:
            return {'error': '分析シナリオのフォルダが見つかりません'}, [], None, {'display': 'none'}

        log.debug(f"Found scenarios: {scenarios}")

        # 日本語ラベル用のマッピング
        scenario_name_map = {
            'out_median_based': '中央値ベース',
            'out_mean_based': '平均値ベース',
            'out_p25_based': '25パーセンタイルベース',
        }

        scenario_options = [
            {'label': scenario_name_map.get(s, s.replace('out_', '')), 'value': s}
            for s in scenarios
        ]
        first_scenario = scenarios[0]
        scenario_paths = {d.name: str(d) for d in temp_dir_path.iterdir() if d.is_dir()}
        return {
            'success': True,
            'scenarios': scenario_paths,
        }, scenario_options, first_scenario, {'display': 'block'}

    except Exception as e:
        log.error(f"Error processing ZIP: {e}", exc_info=True)
        return {'error': str(e)}, [], None, {'display': 'none'}


@app.callback(
    Output('kpi-data-store', 'data'),
    Output('main-content', 'children'),
    Input('scenario-dropdown', 'value'),
    State('data-loaded', 'data')
)
@safe_callback
def update_main_content(selected_scenario, data_status):
    """シナリオ選択に応じてデータを読み込み、メインUIを更新"""
    if (
        not selected_scenario
        or not data_status
        or 'success' not in data_status
        or 'scenarios' not in data_status
    ):
        raise PreventUpdate

    data_dir = Path(data_status['scenarios'].get(selected_scenario, ''))
    if not data_dir.exists():
        raise PreventUpdate

    log.info(f"Switching to scenario {selected_scenario} at {data_dir}")

    # Scenario has changed; reset caches and store new directory
    global CURRENT_SCENARIO_DIR
    CURRENT_SCENARIO_DIR = data_dir
    clear_data_cache()

    pre_aggr = data_get('pre_aggregated_data')
    if pre_aggr is None or (isinstance(pre_aggr, pd.DataFrame) and pre_aggr.empty):
        return {}, html.Div(f"エラー: {(data_dir / 'pre_aggregated_data.parquet').name} が見つかりません。")  # type: ignore

    kpi_data = {}

    tabs = dcc.Tabs(id='main-tabs', value='overview', children=[
        dcc.Tab(label='概要', value='overview'),
        dcc.Tab(label='ヒートマップ', value='heatmap'),
        dcc.Tab(label='不足分析', value='shortage'),
        dcc.Tab(label='最適化分析', value='optimization'),
        dcc.Tab(label='休暇分析', value='leave'),
        dcc.Tab(label='コスト分析', value='cost'),
        dcc.Tab(label='採用計画', value='hire_plan'),
        dcc.Tab(label='疲労分析', value='fatigue'),
        dcc.Tab(label='需要予測', value='forecast'),
        dcc.Tab(label='公平性', value='fairness'),
        dcc.Tab(label='基準乖離分析', value='gap'),
        dcc.Tab(label='職員個別分析', value='individual_analysis'),
        dcc.Tab(label='チーム分析', value='team_analysis'),
        dcc.Tab(label='作成ブループリント', value='blueprint_analysis'),
        dcc.Tab(label='ロジック解明', value='logic_analysis'),
    ])

    # 全タブコンテナを静的に作成（CSS表示制御方式）
    main_layout = html.Div([
        tabs,
        html.Div(style={'marginTop': '20px'}, children=[
            # 各タブコンテナ（初期状態では概要タブのみ表示）
            html.Div(id='overview-tab-container', 
                    style={'display': 'block'},
                    children=[
                        dcc.Loading(
                            id="loading-overview",
                            type="circle",
                            children=html.Div(id='overview-content')
                        )
                    ]),
            html.Div(id='heatmap-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-heatmap",
                            type="circle",
                            children=html.Div(id='heatmap-content')
                        )
                    ]),
            html.Div(id='shortage-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-shortage",
                            type="circle",
                            children=html.Div(id='shortage-content')
                        )
                    ]),
            html.Div(id='optimization-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-optimization",
                            type="circle",
                            children=html.Div(id='optimization-content')
                        )
                    ]),
            html.Div(id='leave-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-leave",
                            type="circle",
                            children=html.Div(id='leave-content')
                        )
                    ]),
            html.Div(id='cost-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-cost",
                            type="circle",
                            children=html.Div(id='cost-content')
                        )
                    ]),
            html.Div(id='hire-plan-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-hire-plan",
                            type="circle",
                            children=html.Div(id='hire-plan-content')
                        )
                    ]),
            html.Div(id='fatigue-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-fatigue",
                            type="circle",
                            children=html.Div(id='fatigue-content')
                        )
                    ]),
            html.Div(id='forecast-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-forecast",
                            type="circle",
                            children=html.Div(id='forecast-content')
                        )
                    ]),
            html.Div(id='fairness-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-fairness",
                            type="circle",
                            children=html.Div(id='fairness-content')
                        )
                    ]),
            html.Div(id='gap-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-gap",
                            type="circle",
                            children=html.Div(id='gap-content')
                        )
                    ]),
            html.Div(id='individual-analysis-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-individual-analysis",
                            type="circle",
                            children=html.Div(id='individual-analysis-content')
                        )
                    ]),
            html.Div(id='team-analysis-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-team-analysis",
                            type="circle",
                            children=html.Div(id='team-analysis-content')
                        )
                    ]),
            html.Div(id='blueprint-analysis-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-blueprint-analysis",
                            type="circle",
                            children=html.Div(id='blueprint-analysis-content')
                        )
                    ]),
            html.Div(id='logic-analysis-tab-container',
                    style={'display': 'none'},
                    children=[
                        dcc.Loading(
                            id="loading-logic-analysis",
                            type="circle",
                            children=html.Div(id='logic-analysis-content')
                        )
                    ])
        ])
    ])

    return kpi_data, main_layout


@app.callback(
    [Output('overview-tab-container', 'style'),
     Output('heatmap-tab-container', 'style'),
     Output('shortage-tab-container', 'style'),
     Output('optimization-tab-container', 'style'),
     Output('leave-tab-container', 'style'),
     Output('cost-tab-container', 'style'),
     Output('hire-plan-tab-container', 'style'),
     Output('fatigue-tab-container', 'style'),
     Output('forecast-tab-container', 'style'),
     Output('fairness-tab-container', 'style'),
     Output('gap-tab-container', 'style'),
     Output('individual-analysis-tab-container', 'style'),
     Output('team-analysis-tab-container', 'style'),
     Output('blueprint-analysis-tab-container', 'style'),
     Output('logic-analysis-tab-container', 'style')],
    Input('main-tabs', 'value'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def update_tab_visibility(active_tab, selected_scenario, data_status):
    """タブの表示制御（CSS visibility方式）"""
    if not selected_scenario or not data_status:
        raise PreventUpdate
    
    # 全タブのスタイル定義
    all_tabs = [
        'overview', 'heatmap', 'shortage', 'optimization', 'leave',
        'cost', 'hire_plan', 'fatigue', 'forecast', 'fairness',
        'gap', 'individual_analysis', 'team_analysis', 'blueprint_analysis', 'logic_analysis'
    ]
    
    # 各タブのスタイルを設定（アクティブなタブのみ表示）
    styles = []
    for tab in all_tabs:
        if tab == active_tab:
            styles.append({'display': 'block'})
        else:
            styles.append({'display': 'none'})
    
    return styles


# 各タブコンテンツの初期化コールバック
@app.callback(
    Output('overview-content', 'children'),
    Input('overview-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_overview_content(style, selected_scenario, data_status):
    """概要タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_overview_tab()
    except Exception as e:
        log.error(f"概要タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('heatmap-content', 'children'),
    Input('heatmap-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_heatmap_content(style, selected_scenario, data_status):
    """ヒートマップタブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_heatmap_tab()
    except Exception as e:
        log.error(f"ヒートマップタブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('shortage-content', 'children'),
    Input('shortage-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_shortage_content(style, selected_scenario, data_status):
    """不足分析タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_shortage_tab()
    except Exception as e:
        log.error(f"不足分析タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('optimization-content', 'children'),
    Input('optimization-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_optimization_content(style, selected_scenario, data_status):
    """最適化分析タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_optimization_tab()
    except Exception as e:
        log.error(f"最適化分析タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('leave-content', 'children'),
    Input('leave-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_leave_content(style, selected_scenario, data_status):
    """休暇分析タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_leave_analysis_tab()
    except Exception as e:
        log.error(f"休暇分析タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('cost-content', 'children'),
    Input('cost-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_cost_content(style, selected_scenario, data_status):
    """コスト分析タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_cost_analysis_tab()
    except Exception as e:
        log.error(f"コスト分析タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('hire-plan-content', 'children'),
    Input('hire-plan-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_hire_plan_content(style, selected_scenario, data_status):
    """採用計画タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_hire_plan_tab()
    except Exception as e:
        log.error(f"採用計画タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('fatigue-content', 'children'),
    Input('fatigue-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_fatigue_content(style, selected_scenario, data_status):
    """疲労分析タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_fatigue_tab()
    except Exception as e:
        log.error(f"疲労分析タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('forecast-content', 'children'),
    Input('forecast-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_forecast_content(style, selected_scenario, data_status):
    """需要予測タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_forecast_tab()
    except Exception as e:
        log.error(f"需要予測タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('fairness-content', 'children'),
    Input('fairness-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_fairness_content(style, selected_scenario, data_status):
    """公平性タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_fairness_tab()
    except Exception as e:
        log.error(f"公平性タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('gap-content', 'children'),
    Input('gap-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_gap_content(style, selected_scenario, data_status):
    """基準乖離分析タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_gap_analysis_tab()
    except Exception as e:
        log.error(f"基準乖離分析タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('team-analysis-content', 'children'),
    Input('team-analysis-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_team_analysis_content(style, selected_scenario, data_status):
    """チーム分析タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_team_analysis_tab()
    except Exception as e:
        log.error(f"チーム分析タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('blueprint-analysis-content', 'children'),
    Input('blueprint-analysis-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_blueprint_analysis_content(style, selected_scenario, data_status):
    """作成ブループリントタブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_blueprint_analysis_tab()
    except Exception as e:
        log.error(f"作成ブループリントタブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('logic-analysis-content', 'children'),
    Input('logic-analysis-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_logic_analysis_content(style, selected_scenario, data_status):
    """ロジック解明タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_creation_logic_analysis_tab()
    except Exception as e:
        log.error(f"ロジック解明タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('individual-analysis-content', 'children'),
    Input('individual-analysis-tab-container', 'style'),
    State('scenario-dropdown', 'value'),
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_individual_analysis_content(style, selected_scenario, data_status):
    """職員個別分析タブの内容を初期化"""
    if not selected_scenario or not data_status or style.get('display') == 'none':
        raise PreventUpdate
    try:
        return create_individual_analysis_tab()
    except Exception as e:
        log.error(f"職員個別分析タブの初期化エラー: {str(e)}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})


@app.callback(
    Output({'type': 'heatmap-filter-employment', 'index': ALL}, 'options'),
    Output({'type': 'heatmap-filter-employment', 'index': ALL}, 'value'),
    Input({'type': 'heatmap-filter-role', 'index': ALL}, 'value'),
)
@safe_callback
def update_employment_options(selected_roles):
    """職種選択に応じて雇用形態フィルターを更新"""
    aggregated_df = data_get('pre_aggregated_data')
    if aggregated_df is None or aggregated_df.empty:
        default_options = [{'label': 'すべて', 'value': 'all'}]
        return [default_options, default_options], ['all', 'all']

    output_options = []
    for role in selected_roles:
        if role and role != 'all':
            employments = aggregated_df[aggregated_df['role'] == role][
                'employment'
            ].unique()
            new_options = (
                [{'label': 'すべて', 'value': 'all'}]
                + [{'label': emp, 'value': emp} for emp in sorted(employments)]
            )
        else:
            all_employments = aggregated_df['employment'].unique()
            new_options = (
                [{'label': 'すべて', 'value': 'all'}]
                + [{'label': emp, 'value': emp} for emp in sorted(all_employments)]
            )
        output_options.append(new_options)

    return output_options, ['all', 'all']


@app.callback(
    Output({'type': 'graph-output-heatmap', 'index': 1}, 'children'),
    Output({'type': 'graph-output-heatmap', 'index': 2}, 'children'),
    Input({'type': 'heatmap-filter-role', 'index': 1}, 'value'),
    Input({'type': 'heatmap-filter-employment', 'index': 1}, 'value'),
    Input({'type': 'heatmap-filter-role', 'index': 2}, 'value'),
    Input({'type': 'heatmap-filter-employment', 'index': 2}, 'value'),
)
@safe_callback
def update_comparison_heatmaps(role1, emp1, role2, emp2):
    """事前集計データから動的にヒートマップを生成し、2エリアを更新"""

    aggregated_df = data_get('pre_aggregated_data')
    if aggregated_df is None or aggregated_df.empty:
        error_message = html.Div("ヒートマップの元データが見つかりません。")  # type: ignore
        return error_message, error_message

    def generate_dynamic_heatmap(selected_role, selected_emp):
        """選択された条件で事前集計データをフィルタしピボット化"""

        filtered_df = aggregated_df.copy()
        title_parts = []

        # 選択された条件に合わせてデータを絞り込む
        if selected_role and selected_role != 'all':
            filtered_df = filtered_df[filtered_df['role'] == selected_role]
            title_parts.append(f"職種: {selected_role}")

        if selected_emp and selected_emp != 'all':
            filtered_df = filtered_df[filtered_df['employment'] == selected_emp]
            title_parts.append(f"雇用形態: {selected_emp}")

        title = " AND ".join(title_parts) if title_parts else "全体"

        if filtered_df.empty:
            time_labels = gen_labels(30)
            all_dates = sorted(aggregated_df['date_lbl'].unique())
            empty_heatmap = pd.DataFrame(index=time_labels, columns=all_dates).fillna(0)
            fig_empty = generate_heatmap_figure(empty_heatmap, f"{title} (勤務データなし)")
            return dcc.Graph(figure=fig_empty)

        # 日付順に並び替えてからピボット
        dynamic_heatmap_df = filtered_df.sort_values('date_lbl').pivot_table(
            index='time',
            columns='date_lbl',
            values='staff_count',
            aggfunc='sum',
            fill_value=0,
        )

        # aggregated_df['date_lbl'].unique() は常に30日全ての日付を保持しています
        all_dates_from_aggregated_data = sorted(aggregated_df['date_lbl'].unique())

        # まず列（日付）を全て網羅するようにreindexし、不足している列は0で埋める
        dynamic_heatmap_df = dynamic_heatmap_df.reindex(columns=all_dates_from_aggregated_data, fill_value=0)

        time_labels = gen_labels(30)
        # 次にインデックス（時間）を全て網羅するようにreindexし、不足している行は0で埋める
        dynamic_heatmap_df = dynamic_heatmap_df.reindex(index=time_labels, fill_value=0)

        present_dates = dynamic_heatmap_df.columns.tolist()
        analysis_logger.info(
            f"ヒートマップ '{title}' の生成: 描画対象の日付 ({len(present_dates)}件): {present_dates}"
        )

        long_df = data_get('long_df', pd.DataFrame())
        if not long_df.empty:
            all_dates_in_period = sorted(pd.to_datetime(long_df['ds']).dt.strftime('%Y-%m-%d').unique())
            missing_dates = sorted(list(set(all_dates_in_period) - set(present_dates)))
            if missing_dates:
                analysis_logger.warning(
                    f"ヒートマップ '{title}' で日付が欠落している可能性があります。"
                    f"分析期間中の全日付: {len(all_dates_in_period)}件, "
                    f"描画対象の日付: {len(present_dates)}件, "
                    f"欠落日付 ({len(missing_dates)}件): {missing_dates}"
                )

        fig = generate_heatmap_figure(dynamic_heatmap_df, title)
        return dcc.Graph(figure=fig)

    output1 = generate_dynamic_heatmap(role1, emp1)
    output2 = generate_dynamic_heatmap(role2, emp2)

    return output1, output2


@app.callback(
    Output('shortage-heatmap-detail-container', 'children'),
    Input('shortage-heatmap-scope', 'value')
)
@safe_callback
def update_shortage_heatmap_detail(scope):
    """不足率ヒートマップの詳細選択を更新"""
    if scope == 'overall':
        return None
    elif scope == 'role':
        roles = data_get('roles', [])
        return html.Div([  # type: ignore
            html.Label("職種選択"),  # type: ignore
            dcc.Dropdown(
                id={'type': 'shortage-detail', 'index': 'role'},
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in roles],
                value='ALL',
                style={'width': '200px'}
            )
        ], style={'marginBottom': '10px'})
    elif scope == 'employment':
        employments = data_get('employments', [])
        return html.Div([  # type: ignore
            html.Label("雇用形態選択"),  # type: ignore
            dcc.Dropdown(
                id={'type': 'shortage-detail', 'index': 'employment'},
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': e, 'value': e} for e in employments],
                value='ALL',
                style={'width': '200px'}
            )
        ], style={'marginBottom': '10px'})
    return None


@app.callback(
    Output('shortage-ratio-heatmap', 'children'),
    Input('shortage-heatmap-scope', 'value'),
    Input({'type': 'shortage-detail', 'index': ALL}, 'value')
)
@safe_callback
def update_shortage_ratio_heatmap(scope, detail_values):
    """不足率ヒートマップを更新"""
    # 選択内容からキーを組み立ててデータを取得
    key_suffix = ''
    if scope == 'role' and detail_values and detail_values[0] != 'ALL':
        # 職種別: 直接職種名を使用（role_プレフィックス除去）
        key_suffix = safe_filename(detail_values[0])
    elif scope == 'employment' and detail_values and detail_values[0] != 'ALL':
        # 雇用形態別: emp_プレフィックス付きで使用
        key_suffix = f"emp_{safe_filename(detail_values[0])}"

    heat_key = f"heat_{key_suffix}" if key_suffix else "heat_all"
    df_heat = data_get(heat_key, pd.DataFrame())
    
    # キーが見つからない場合、元の職種名（safe_filename変換前）で再試行
    if df_heat.empty and scope == 'role' and detail_values and detail_values[0] != 'ALL':
        original_heat_key = f"heat_{detail_values[0]}"
        log.info(f"Trying original key: {original_heat_key}")
        df_heat = data_get(original_heat_key, pd.DataFrame())

    if df_heat.empty:
        # より詳細なエラーメッセージと診断情報を提供
        available_keys = [k for k in DATA_CACHE.keys() if k.startswith('heat_')]
        debug_info = []
        debug_info.append(f"探索キー: {heat_key}")
        debug_info.append(f"利用可能なヒートマップキー: {available_keys}")
        debug_info.append(f"選択されたスコープ: {scope}")
        debug_info.append(f"詳細値: {detail_values}")
        
        # 類似キーの提案
        similar_keys = [k for k in available_keys if key_suffix in k] if key_suffix else []
        if similar_keys:
            debug_info.append(f"類似キー: {similar_keys}")
        
        return html.Div([  # type: ignore
            html.P("選択された条件のヒートマップデータが見つかりません。", style={'color': 'red', 'fontWeight': 'bold'}),
            html.P("診断情報:", style={'fontWeight': 'bold'}),
            html.Ul([html.Li(info) for info in debug_info]),
            html.P("解決方法:", style={'fontWeight': 'bold'}),
            html.Ul([
                html.Li("データが正しく分析されているか確認してください"),
                html.Li("職種名に特殊文字が含まれていないか確認してください"), 
                html.Li("別の職種/雇用形態を選択してみてください")
            ])
        ])

    date_cols = [c for c in df_heat.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    staff_df = df_heat[date_cols]
    
    # ★★★ 重要な修正: 職種別・雇用形態別の場合は該当のneed値のみを使用 ★★★
    if scope == 'overall':
        # 全体の場合のみneed_per_date_slot.parquetを使用
        need_per_date_slot_df = data_get('need_per_date_slot', pd.DataFrame())
        
        if not need_per_date_slot_df.empty:
            # need_per_date_slot.parquetが存在する場合、実際の日付別need値を使用
            log.info(f"Using need_per_date_slot.parquet for accurate daily need values: {need_per_date_slot_df.shape}")
            
            # 列名を文字列として統一
            need_per_date_slot_df.columns = [str(col) for col in need_per_date_slot_df.columns]
            date_cols_str = [str(col) for col in date_cols]
            
            # 共通する日付列のみを使用
            common_dates = [col for col in date_cols_str if col in need_per_date_slot_df.columns]
            
            if common_dates:
                # 実際の日付別need値を使用
                need_df = need_per_date_slot_df[common_dates].copy()
                need_df.columns = [c for c in date_cols if str(c) in common_dates]
                
                # 不足している日付があれば平均値で補完
                missing_dates = [c for c in date_cols if str(c) not in common_dates]
                if missing_dates:
                    log.warning(f"Some dates missing in need_per_date_slot.parquet, using fallback for: {missing_dates}")
                    fallback_need = pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(missing_dates), axis=1),
                                               index=df_heat.index, columns=missing_dates)
                    need_df = pd.concat([need_df, fallback_need], axis=1)
                    need_df = need_df.reindex(columns=date_cols)  # 元の順序を保持
            else:
                log.warning("No matching dates found in need_per_date_slot.parquet, falling back to average need")
                need_df = pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(date_cols), axis=1),
                                       index=df_heat.index, columns=date_cols)
        else:
            # need_per_date_slot.parquetが存在しない場合は従来の平均値を使用
            log.info("need_per_date_slot.parquet not available, using average need values")
            need_df = pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(date_cols), axis=1),
                                   index=df_heat.index, columns=date_cols)
    else:
        # 職種別・雇用形態別の場合は、共通関数を使用して動的need値を計算
        need_df = calculate_role_dynamic_need(df_heat, date_cols, heat_key)
    upper_df = pd.DataFrame(np.repeat(df_heat['upper'].values[:, np.newaxis], len(date_cols), axis=1),
                            index=df_heat.index, columns=date_cols)

    # 正確な不足計算の実装
    # need値が正確に計算されているので、シンプルで正確な不足計算を行う
    lack_count_df = (need_df - staff_df).clip(lower=0).fillna(0)
    
    # 実際のneed値が非常に小さい場合（0.01未満）のみ0とする（計算誤差対策）
    mask_tiny_need = need_df < 0.01
    lack_count_df[mask_tiny_need] = 0.0
    
    log.info(f"[LACK_CALCULATION] {heat_key}: Total lack={lack_count_df.sum().sum():.2f}, Max need={need_df.max().max():.2f}, Max staff={staff_df.max().max():.2f}")
    
    excess_count_df = (staff_df - upper_df).clip(lower=0).fillna(0)
    ratio_df = calc_ratio_from_heatmap(df_heat)
    
    # 不足数ヒートマップの修正
    lack_count_df_renamed = lack_count_df.copy()
    lack_count_df_renamed.columns = [date_with_weekday(c) for c in lack_count_df_renamed.columns]
    # 追加の安全対策: NaN値を再度0で埋める（日曜日の欠落対策）
    lack_count_df_renamed = lack_count_df_renamed.fillna(0)
    
    fig_lack = px.imshow(
        lack_count_df_renamed,
        aspect='auto',
        color_continuous_scale='Oranges',
        title='不足人数ヒートマップ',
        labels={'x': '日付', 'y': '時間', 'color': '人数'},
        text_auto=True  # 0値も表示
    )
    
    # 不足数の表示スタイルを調整
    fig_lack.update_traces(
        texttemplate='%{text}',
        textfont={"size": 10}
    )
    fig_lack.update_xaxes(tickvals=list(range(len(lack_count_df.columns))))

    fig_excess = go.Figure()
    if not excess_count_df.empty:
        excess_count_df_renamed = excess_count_df.copy()
        excess_count_df_renamed.columns = [date_with_weekday(c) for c in excess_count_df_renamed.columns]
        fig_excess = px.imshow(
            excess_count_df_renamed,
            aspect='auto',
            color_continuous_scale='Blues',
            title='過剰人数ヒートマップ',
            labels={'x': '日付', 'y': '時間', 'color': '人数'},
        )
        fig_excess.update_xaxes(tickvals=list(range(len(excess_count_df.columns))))

    fig_ratio = go.Figure()
    if not ratio_df.empty:
        ratio_df_renamed = ratio_df.copy()
        ratio_df_renamed.columns = [date_with_weekday(c) for c in ratio_df_renamed.columns]
        fig_ratio = px.imshow(
            ratio_df_renamed,
            aspect='auto',
            color_continuous_scale='RdBu_r',
            title='不足率ヒートマップ',
            labels={'x': '日付', 'y': '時間', 'color': '不足率'},
        )
        fig_ratio.update_xaxes(tickvals=list(range(len(ratio_df.columns))))

    return html.Div([  # type: ignore
        html.H4('不足人数ヒートマップ'),
        dcc.Graph(figure=fig_lack),
        html.H4('過剰人数ヒートマップ', style={'marginTop': '30px'}),
        dcc.Graph(figure=fig_excess),
        html.H4('不足率ヒートマップ', style={'marginTop': '30px'}),
        dcc.Graph(figure=fig_ratio),
    ])


@app.callback(
    Output('opt-detail-container', 'children'),
    Input('opt-scope', 'value')
)
@safe_callback
def update_opt_detail(scope):
    """最適化分析の詳細選択を更新"""
    if scope == 'overall':
        return None
    elif scope == 'role':
        roles = data_get('roles', [])
        return html.Div([  # type: ignore
            html.Label("職種選択"),  # type: ignore
            dcc.Dropdown(
                id={'type': 'opt-detail', 'index': 'role'},
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in roles],
                value='ALL',
                style={'width': '300px', 'marginBottom': '20px'}
            )
        ])
    elif scope == 'employment':
        employments = data_get('employments', [])
        return html.Div([  # type: ignore
            html.Label("雇用形態選択"),  # type: ignore
            dcc.Dropdown(
                id={'type': 'opt-detail', 'index': 'employment'},
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': e, 'value': e} for e in employments],
                value='ALL',
                style={'width': '300px', 'marginBottom': '20px'}
            )
        ])
    return None

@app.callback(
    Output('optimization-content', 'children'),
    Input('opt-scope', 'value'),
    Input({'type': 'opt-detail', 'index': ALL}, 'value')
)
@safe_callback
def update_optimization_content(scope, detail_values):
    """最適化分析コンテンツを更新"""
    # 選択内容からキーを組み立ててヒートマップを取得
    key_suffix = ''
    if scope == 'role' and detail_values and detail_values[0] != 'ALL':
        # 職種別: 直接職種名を使用（role_プレフィックス除去）
        key_suffix = safe_filename(detail_values[0])
    elif scope == 'employment' and detail_values and detail_values[0] != 'ALL':
        # 雇用形態別: emp_プレフィックス付きで使用
        key_suffix = f"emp_{safe_filename(detail_values[0])}"

    heat_key = f"heat_{key_suffix}" if key_suffix else "heat_all"
    df_heat = data_get(heat_key, pd.DataFrame())
    
    # キーが見つからない場合、元の職種名（safe_filename変換前）で再試行
    if df_heat.empty and scope == 'role' and detail_values and detail_values[0] != 'ALL':
        original_heat_key = f"heat_{detail_values[0]}"
        log.info(f"Trying original key for optimization: {original_heat_key}")
        df_heat = data_get(original_heat_key, pd.DataFrame())

    if df_heat.empty:
        return html.Div("選択された条件の最適化分析データが見つかりません。")

    date_cols = [c for c in df_heat.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    staff_df = df_heat[date_cols]
    
    # ★★★ 重要な修正: 職種別・雇用形態別の場合は該当のneed値のみを使用 ★★★
    if scope == 'overall':
        # 全体の場合のみneed_per_date_slot.parquetを使用
        need_per_date_slot_df = data_get('need_per_date_slot', pd.DataFrame())
        
        if not need_per_date_slot_df.empty:
            # need_per_date_slot.parquetが存在する場合、実際の日付別need値を使用
            log.info(f"Using need_per_date_slot.parquet for optimization analysis: {need_per_date_slot_df.shape}")
            
            # 列名を文字列として統一
            need_per_date_slot_df.columns = [str(col) for col in need_per_date_slot_df.columns]
            date_cols_str = [str(col) for col in date_cols]
            
            # 共通する日付列のみを使用
            common_dates = [col for col in date_cols_str if col in need_per_date_slot_df.columns]
            
            if common_dates:
                # 実際の日付別need値を使用
                need_df = need_per_date_slot_df[common_dates].copy()
                need_df.columns = [c for c in date_cols if str(c) in common_dates]
                
                # 不足している日付があれば平均値で補完
                missing_dates = [c for c in date_cols if str(c) not in common_dates]
                if missing_dates:
                    log.warning(f"Some dates missing in need_per_date_slot.parquet for optimization, using fallback for: {missing_dates}")
                    fallback_need = pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(missing_dates), axis=1),
                                               index=df_heat.index, columns=missing_dates)
                    need_df = pd.concat([need_df, fallback_need], axis=1)
                    need_df = need_df.reindex(columns=date_cols)
            else:
                log.warning("No matching dates found in need_per_date_slot.parquet for optimization, falling back to average need")
                need_df = pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(date_cols), axis=1),
                                       index=df_heat.index, columns=date_cols)
        else:
            # need_per_date_slot.parquetが存在しない場合は従来の平均値を使用
            log.info("need_per_date_slot.parquet not available for optimization, using average need values")
            need_df = pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(date_cols), axis=1),
                                   index=df_heat.index, columns=date_cols)
    else:
        # 職種別・雇用形態別の場合は、共通関数を使用して動的need値を計算
        need_df = calculate_role_dynamic_need(df_heat, date_cols, heat_key)
    upper_df = pd.DataFrame(np.repeat(df_heat['upper'].values[:, np.newaxis], len(date_cols), axis=1),
                            index=df_heat.index, columns=date_cols)

    # 不足率・過剰率からスコアを計算
    lack_ratio = ((need_df - staff_df) / need_df.replace(0, np.nan)).clip(lower=0).fillna(0)
    excess_ratio = ((staff_df - upper_df) / upper_df.replace(0, np.nan)).clip(lower=0).fillna(0)

    df_surplus = (staff_df - need_df).clip(lower=0).fillna(0)
    df_margin = (upper_df - staff_df).clip(lower=0).fillna(0)
    df_score = 1 - (0.6 * lack_ratio + 0.4 * excess_ratio).clip(0, 1)

    if not (_valid_df(df_surplus) and _valid_df(df_margin) and _valid_df(df_score)):
        return html.Div("最適化分析データの計算に失敗しました。")
    surplus_df_renamed = df_surplus.copy()
    surplus_df_renamed.columns = [date_with_weekday(c) for c in surplus_df_renamed.columns]

    margin_df_renamed = df_margin.copy()
    margin_df_renamed.columns = [date_with_weekday(c) for c in margin_df_renamed.columns]

    score_df_renamed = df_score.copy()
    score_df_renamed.columns = [date_with_weekday(c) for c in score_df_renamed.columns]

    content = [
        html.Div([
            html.H4("1. 必要人数に対する余剰 (Surplus vs Need)"),
            html.P("各時間帯で必要人数（need）に対して何人多くスタッフがいたかを示します。"),
            dcc.Graph(
                figure=px.imshow(
                    surplus_df_renamed,
                    aspect='auto',
                    color_continuous_scale='Blues',
                    title='必要人数に対する余剰人員ヒートマップ',
                    labels={'x': '日付', 'y': '時間', 'color': '余剰人数'},
                ).update_xaxes(tickvals=list(range(len(df_surplus.columns))))
            ),
        ]),
        html.Div([
            html.H4("2. 上限に対する余白 (Margin to Upper)", style={'marginTop': '30px'}),
            html.P("各時間帯で配置人数の上限（upper）まであと何人の余裕があったかを示します。"),
            dcc.Graph(
                figure=px.imshow(
                    margin_df_renamed,
                    aspect='auto',
                    color_continuous_scale='Greens',
                    title='上限人数までの余白ヒートマップ',
                    labels={'x': '日付', 'y': '時間', 'color': '余白人数'},
                ).update_xaxes(tickvals=list(range(len(df_margin.columns))))
            ),
        ]),
        html.Div([
            html.H4("3. 人員配置 最適化スコア", style={'marginTop': '30px'}),
            html.P("人員配置の効率性を0から1のスコアで示します（1が最も良い）。"),
            dcc.Graph(
                figure=px.imshow(
                    score_df_renamed,
                    aspect='auto',
                    color_continuous_scale='RdYlGn',
                    zmin=0,
                    zmax=1,
                    title='最適化スコア ヒートマップ',
                    labels={'x': '日付', 'y': '時間', 'color': 'スコア'},
                ).update_xaxes(tickvals=list(range(len(df_score.columns))))
            ),
        ]),
    ]

    return html.Div(content)


@app.callback(
    Output('overview-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
@safe_callback
def update_overview_insights(kpi_data):
    if not kpi_data:
        return ""

    total_lack_h = kpi_data.get('total_lack_h', 0)

    if total_lack_h > 0:
        most_lacking_role = kpi_data.get('most_lacking_role_name', 'N/A')
        most_lacking_hours = kpi_data.get('most_lacking_role_hours', 0)
        insight_text = f"""
        #### 📈 分析ハイライト
        - **総不足時間:** {total_lack_h:.1f} 時間
        - **最重要課題:** **{most_lacking_role}** の不足が **{most_lacking_hours:.1f}時間** と最も深刻です。この職種の採用または配置転換が急務と考えられます。
        """
        return dcc.Markdown(insight_text)
    return html.P(
        "👍 人員不足は発生していません。素晴らしい勤務体制です！",
        style={'fontWeight': 'bold'},  # type: ignore
    )


@app.callback(
    Output('shortage-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
@safe_callback
def update_shortage_insights(kpi_data):
    explanation = """
    #### 不足分析の評価方法
    - **不足 (Shortage):** `不足人数 = 必要人数 (Need) - 実績人数` で計算されます。値がプラスの場合、その時間帯は人員が不足していたことを示します。
    - **過剰 (Excess):** `過剰人数 = 実績人数 - 上限人数 (Upper)` で計算されます。値がプラスの場合、過剰な人員が配置されていたことを示します。

    *「必要人数」と「上限人数」は、サイドバーの「分析基準設定」で指定した方法（過去実績の統計、または人員配置基準）に基づいて算出されます。*
    """
    return dcc.Markdown(explanation)


@app.callback(
    Output('hire-plan-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
@safe_callback
def update_hire_plan_insights(kpi_data):
    if not kpi_data:
        return ""
    total_lack_h = kpi_data.get('total_lack_h', 0)
    if total_lack_h == 0:
        return html.P("追加採用の必要はありません。")
    role = kpi_data.get('most_lacking_role_name', 'N/A')
    return dcc.Markdown(
        f"最も不足している **{role}** の補充を優先的に検討してください。"
    )


@app.callback(
    Output('optimization-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
@safe_callback
def update_optimization_insights(kpi_data):
    explanation = """
    #### 最適化分析の評価方法
    人員配置の効率性は、以下の2つの観点からペナルティを計算し、最終的なスコアを算出します。
    - **不足ペナルティ (重み: 60%):** `(必要人数 - 実績人数) / 必要人数`
    - **過剰ペナルティ (重み: 40%):** `(実績人数 - 上限人数) / 上限人数`

    **最適化スコア = 1 - (不足ペナルティ × 0.6 + 過剰ペナルティ × 0.4)**

    *スコアが1に近いほど、不足も過剰もなく、効率的な人員配置ができている状態を示します。*
    """
    return dcc.Markdown(explanation)


@app.callback(
    Output('leave-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
@safe_callback
def update_leave_insights(kpi_data):
    explanation = """
    #### 休暇分析の評価方法
    - **休暇取得者数:** `holiday_type`が休暇関連（希望休、有給など）に設定され、かつ勤務時間がない（`parsed_slots_count = 0`）場合に「1日」としてカウントされます。
    - **集中日:** 「希望休」の取得者数が、サイドバーで設定した閾値（デフォルト: 3人）以上になった日を「集中日」としてハイライトします。
    """
    return dcc.Markdown(explanation)


@app.callback(
    Output('cost-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
@safe_callback
def update_cost_insights(kpi_data):
    explanation = """
    #### コスト分析の評価方法
    日々の人件費は、各スタッフの勤務時間（スロット数 × スロット長）に、サイドバーで設定した単価基準（職種別、雇用形態別など）の時給を乗じて算出されます。
    """
    return dcc.Markdown(explanation)


@app.callback(
    Output('wage-input-container', 'children'),
    Input('cost-by-radio', 'value')
)
@safe_callback
def update_wage_inputs(by_key):
    """単価入力欄を生成"""
    long_df = data_get('long_df')
    if long_df is None or long_df.empty or by_key not in long_df.columns:
        return html.P("単価設定のためのデータがありません。")

    unique_keys: list[str] = sorted(long_df[by_key].dropna().unique())
    inputs = []
    for key in unique_keys:
        inputs.append(html.Div([
            html.Label(f'時給: {key}'),
            dcc.Input(
                id={'type': 'wage-input', 'index': key},
                value=1500,
                type='number',
                debounce=True,
            )
        ], style={'padding': '5px', 'display': 'inline-block'}))
    return inputs


@app.callback(
    Output('cost-analysis-content', 'children'),
    Input('cost-by-radio', 'value'),
    Input({'type': 'wage-input', 'index': ALL}, 'value'),
    State({'type': 'wage-input', 'index': ALL}, 'id'),
)
@safe_callback
def update_cost_analysis_content(by_key, all_wages, all_wage_ids):
    """単価変更に応じてコスト分析タブの全コンテンツを動的に更新する"""
    long_df = data_get('long_df')
    if long_df is None or long_df.empty or not all_wages:
        raise PreventUpdate

    wages = {
        wage_id['index']: (wage_val or 0) for wage_id, wage_val in zip(all_wage_ids, all_wages)
    }

    df_cost = calculate_daily_cost(long_df, wages, by=by_key)
    if df_cost.empty:
        return html.P("コスト計算結果がありません。")

    df_cost['date'] = pd.to_datetime(df_cost['date'])

    if not {'day_of_week', 'total_staff', 'role_breakdown'}.issubset(df_cost.columns):
        details = (
            long_df[long_df.get('parsed_slots_count', 1) > 0]
            .assign(date=lambda x: pd.to_datetime(x['ds']).dt.normalize())
            .groupby('date')
            .agg(
                day_of_week=('ds', lambda x: ['月', '火', '水', '木', '金', '土', '日'][x.iloc[0].weekday()]),
                total_staff=('staff', 'nunique'),
                role_breakdown=('role', lambda s: ', '.join(f"{r}:{c}" for r, c in s.value_counts().items())),
            )
            .reset_index()
        )
        df_cost = pd.merge(df_cost, details, on='date', how='left')

    df_cost = df_cost.sort_values('date')

    content = []

    total_cost = df_cost['cost'].sum()
    avg_daily_cost = df_cost['cost'].mean()
    max_cost_day = df_cost.loc[df_cost['cost'].idxmax()]
    summary_cards = html.Div([
        create_metric_card("総コスト", f"¥{total_cost:,.0f}"),
        create_metric_card("日平均コスト", f"¥{avg_daily_cost:,.0f}"),
        create_metric_card("最高コスト日", f"{max_cost_day['date'].strftime('%m/%d')}<br>¥{max_cost_day['cost']:,.0f}"),
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'})
    content.append(summary_cards)

    df_cost['cumulative_cost'] = df_cost['cost'].cumsum()
    fig_cumulative = px.area(df_cost, x='date', y='cumulative_cost', title='累計人件費の推移')
    fig_cumulative.update_xaxes(tickformat="%m/%d(%a)")
    content.append(dcc.Graph(figure=fig_cumulative))

    fig_daily = px.bar(df_cost, x='date', y='cost', title='日別発生人件費（総額）')
    fig_daily.update_xaxes(tickformat="%m/%d(%a)")
    content.append(dcc.Graph(figure=fig_daily))

    if 'role_breakdown' in df_cost.columns and by_key == 'role':
        role_data = []
        for _, row in df_cost.iterrows():
            if pd.notna(row.get('role_breakdown')):
                date_total_cost = row['cost']
                role_counts = {r.split(':')[0]: int(r.split(':')[1]) for r in row['role_breakdown'].split(', ') if ':' in r}
                total_count = sum(role_counts.values())

                for role, count in role_counts.items():
                    role_cost = (count / total_count) * date_total_cost if total_count > 0 else 0
                    role_data.append({'date': row['date'], 'role': role, 'count': count, 'cost': role_cost})

        if role_data:
            role_df = pd.DataFrame(role_data)

            fig_stacked = px.bar(role_df, x='date', y='cost', color='role', title='日別人件費（職種別内訳）')
            fig_stacked.update_xaxes(tickformat="%m/%d(%a)")
            content.append(dcc.Graph(figure=fig_stacked))

            role_df['month'] = pd.to_datetime(role_df['date']).dt.to_period('M').astype(str)
            monthly_role = role_df.groupby(['month', 'role'])['cost'].sum().reset_index()
            fig_monthly = px.bar(monthly_role, x='month', y='cost', color='role', title='月次人件費（職種別内訳）')
            content.append(dcc.Graph(figure=fig_monthly))

            total_by_role = role_df.groupby('role')['cost'].sum().reset_index()
            fig_pie = px.pie(total_by_role, values='cost', names='role', title='職種別コスト構成比（全期間）')
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            content.append(dcc.Graph(figure=fig_pie))

    return html.Div(content)


@app.callback(
    Output('clear-synergy-cache-btn', 'children'),
    Input('clear-synergy-cache-btn', 'n_clicks'),
    prevent_initial_call=True
)
@safe_callback
def clear_synergy_cache_callback(n_clicks):
    """シナジーキャッシュクリアボタンのコールバック"""
    if n_clicks:
        clear_synergy_cache()
        return "キャッシュクリア済み"
    return "キャッシュクリア"


@app.callback(
    Output('individual-analysis-content', 'children'),
    Input('individual-staff-dropdown', 'value'),
    Input('synergy-analysis-type', 'value')
)
@safe_callback
def update_individual_analysis_content(selected_staff, synergy_type):
    """職員選択に応じて分析コンテンツを更新する"""
    if not selected_staff:
        raise PreventUpdate
    
    # グローバル変数として初期化
    global synergy_matrix_data, synergy_additional_info
    synergy_matrix_data = None
    synergy_additional_info = html.Div()

    # 必要なデータを一括で読み込む
    long_df = data_get('long_df', pd.DataFrame())
    fatigue_df = data_get('fatigue_score', pd.DataFrame())
    fairness_df = data_get('fairness_after', pd.DataFrame())
    shortage_df = data_get('shortage_time', pd.DataFrame())
    excess_df = data_get('excess_time', pd.DataFrame())

    if long_df.empty:
        return html.P("勤務データが見つかりません。")

    staff_df = long_df[long_df['staff'] == selected_staff].copy()

    # --- 1. 勤務区分ごとの占有割合 ---
    work_dist_fig = go.Figure(layout={'title': {'text': f'{selected_staff}さんの勤務割合'}})
    if not staff_df.empty and 'code' in staff_df.columns:
        work_records = staff_df[staff_df.get('parsed_slots_count', 1) > 0]
        if not work_records.empty:
            code_counts = work_records['code'].value_counts()
            work_dist_fig = px.pie(
                values=code_counts.values, names=code_counts.index,
                title=f'{selected_staff}さんの勤務割合', hole=.3
            )
            work_dist_fig.update_traces(textposition='inside', textinfo='percent+label')

    # --- 2. 不公平・疲労度の詳細スコア ---
    fatigue_score, unfairness_score = "データなし", "データなし"
    score_details_df = pd.DataFrame()
    if not fatigue_df.empty:
        fatigue_df_indexed = fatigue_df.set_index('staff') if 'staff' in fatigue_df.columns else fatigue_df
        if selected_staff in fatigue_df_indexed.index:
            fatigue_score = f"{fatigue_df_indexed.loc[selected_staff, 'fatigue_score']:.1f}"
    if not fairness_df.empty and 'staff' in fairness_df.columns:
        staff_fairness = fairness_df[fairness_df['staff'] == selected_staff]
        if not staff_fairness.empty:
            row = staff_fairness.iloc[0]
            unfairness_score = f"{row.get('unfairness_score', 0):.2f}"
            details_data = {
                "指標": ["夜勤比率の乖離", "総労働時間の乖離", "連休取得頻度の乖離"],
                "スコア": [f"{row.get(col, 0):.2f}" for col in ['dev_night_ratio', 'dev_work_slots', 'dev_consecutive']]
            }
            score_details_df = pd.DataFrame(details_data)

    # --- 3. 共働した職員ランキング ---
    coworker_ranking_df = pd.DataFrame()
    my_slots = staff_df[['ds']].drop_duplicates()
    coworkers = long_df[long_df['ds'].isin(my_slots['ds']) & (long_df['staff'] != selected_staff)]
    if not coworkers.empty:
        coworker_counts = coworkers['staff'].value_counts().reset_index()
        coworker_counts.columns = ['職員', '共働回数']
        coworker_ranking_df = coworker_counts.head(5)

    # --- 4. 人員不足/過剰への貢献度分析 ---
    slot_hours = 0.5
    shortage_contribution_h, excess_contribution_h = 0, 0
    staff_work_slots = staff_df[staff_df.get('parsed_slots_count', 0) > 0][['ds']].copy()
    staff_work_slots['date_str'] = staff_work_slots['ds'].dt.strftime('%Y-%m-%d')
    staff_work_slots['time'] = staff_work_slots['ds'].dt.strftime('%H:%M')
    if not shortage_df.empty:
        shortage_long = shortage_df.melt(var_name='date_str', value_name='shortage_count', ignore_index=False).reset_index().rename(columns={'index':'time'})
        merged_shortage = pd.merge(staff_work_slots, shortage_long, on=['date_str', 'time'])
        shortage_contribution_h = merged_shortage[merged_shortage['shortage_count'] > 0].shape[0] * slot_hours
    if not excess_df.empty:
        excess_long = excess_df.melt(var_name='date_str', value_name='excess_count', ignore_index=False).reset_index().rename(columns={'index':'time'})
        merged_excess = pd.merge(staff_work_slots, excess_long, on=['date_str', 'time'])
        excess_contribution_h = merged_excess[merged_excess['excess_count'] > 0].shape[0] * slot_hours

    # --- 5. 個人の休暇取得傾向 ---
    leave_by_dow_fig = go.Figure(layout={'title': {'text': '曜日別の休暇取得日数'}})
    staff_leave_df = staff_df[staff_df.get('holiday_type', '通常勤務') != '通常勤務']
    if not staff_leave_df.empty:
        daily_leave = leave_analyzer.get_daily_leave_counts(staff_leave_df)
        if not daily_leave.empty:
            dow_summary = leave_analyzer.summarize_leave_by_day_count(daily_leave, period='dayofweek')
            if not dow_summary.empty:
                leave_by_dow_fig = px.bar(dow_summary, x='period_unit', y='total_leave_days', color='leave_type', title=f'{selected_staff}さんの曜日別休暇取得日数')
                leave_by_dow_fig.update_xaxes(title_text="曜日").update_yaxes(title_text="日数")

    # --- 6. 職員間の「化学反応」分析 ---
    synergy_fig = go.Figure(layout={'title': {'text': f'{selected_staff}さんとのシナジー分析'}})
    
    # デバッグ情報を追加
    log.info(f"[SYNERGY] 分析開始: {selected_staff}")
    log.info(f"[SYNERGY] long_df shape: {long_df.shape}")
    log.info(f"[SYNERGY] shortage_df shape: {shortage_df.shape}")
    log.info(f"[SYNERGY] shortage_df columns: {shortage_df.columns.tolist() if not shortage_df.empty else 'Empty'}")
    
    # 利用可能なデータの確認
    available_data = {}
    for key in ['shortage_time', 'shortage_role_summary', 'heat_ALL', 'long_df']:
        try:
            data = data_get(key, pd.DataFrame())
            available_data[key] = f"shape: {data.shape}, empty: {data.empty}"
            if not data.empty:
                available_data[key] += f", columns: {data.columns.tolist()[:5]}"  # 最初の5列のみ表示
        except:
            available_data[key] = "取得失敗"
    
    log.info(f"[SYNERGY] 利用可能データ: {available_data}")
    
    # shortage_timeが空の場合、他のデータを試す
    if shortage_df.empty:
        log.info("[SYNERGY] shortage_timeが空のため、他のデータを試します")
        
        # 1. analysis_resultsディレクトリから直接読み取りを試す
        try:
            import os
            current_dir = os.getcwd()
            analysis_results_path = os.path.join(current_dir, "analysis_results")
            shortage_time_path = os.path.join(analysis_results_path, "shortage_time.parquet")
            
            if os.path.exists(shortage_time_path):
                log.info(f"[SYNERGY] 直接ファイルから読み取り: {shortage_time_path}")
                shortage_df = pd.read_parquet(shortage_time_path)
                log.info(f"[SYNERGY] 直接読み取り成功: {shortage_df.shape}")
            else:
                log.info(f"[SYNERGY] ファイルが見つかりません: {shortage_time_path}")
        except Exception as e:
            log.error(f"[SYNERGY] 直接読み取りエラー: {e}")
        
        # 2. まだ空の場合、heat_ALLデータを試す
        if shortage_df.empty:
            heat_all_df = data_get('heat_ALL', pd.DataFrame())
            if not heat_all_df.empty:
                log.info(f"[SYNERGY] heat_ALLを使用: {heat_all_df.shape}")
                # heat_ALLから不足データを生成
                shortage_df = create_shortage_from_heat_all(heat_all_df)
                log.info(f"[SYNERGY] 生成されたshortage_df: {shortage_df.shape}")
        
        # 3. まだ空の場合、excess_timeを試す（符号を反転）
        if shortage_df.empty:
            excess_df = data_get('excess_time', pd.DataFrame())
            if not excess_df.empty:
                log.info(f"[SYNERGY] excess_timeを使用（符号反転): {excess_df.shape}")
                # excess_timeの符号を反転してshortageとして使用
                shortage_df = -excess_df
                shortage_df = shortage_df.clip(lower=0)  # 負の値は0にクリップ
                log.info(f"[SYNERGY] excess_timeから生成: {shortage_df.shape}")
    
    # シナジー分析を実行（分析タイプに応じて）
    synergy_df = pd.DataFrame()
    synergy_additional_data = None
    # synergy_matrix_data と synergy_additional_info は上でグローバル変数として初期化済み
    
    log.info(f"[SYNERGY] 分析タイプ: {synergy_type}")
    
    if not long_df.empty:
        try:
            if synergy_type == 'correlation_matrix':
                try:
                    if create_synergy_correlation_matrix_optimized is not None:
                        log.info("[SYNERGY] 相関マトリックス分析を実行")
                        
                        # キャッシュをチェック
                        cache_key = get_synergy_cache_key(long_df, shortage_df)
                        synergy_matrix_data = SYNERGY_CACHE.get(cache_key)
                        
                        if synergy_matrix_data is not None:
                            log.info(f"[SYNERGY] キャッシュから相関マトリックス取得: {cache_key}")
                        else:
                            log.info("[SYNERGY] 相関マトリックス新規計算開始")
                            n_staff = len(long_df['staff'].unique())
                            total_calculations = n_staff * (n_staff - 1) // 2
                            log.info(f"[SYNERGY] 計算予定ペア数: {total_calculations}")
                            
                            synergy_matrix_data = create_synergy_correlation_matrix_optimized(long_df, shortage_df)
                            if synergy_matrix_data is not None and 'error' not in synergy_matrix_data:
                                SYNERGY_CACHE.set(cache_key, synergy_matrix_data)
                                log.info(f"[SYNERGY] 相関マトリックス計算完了、キャッシュに保存: {cache_key}")
                            else:
                                log.error(f"[SYNERGY] 相関マトリックス計算失敗: {synergy_matrix_data.get('error', 'Unknown error') if synergy_matrix_data else 'None result'}")
                                if synergy_matrix_data is None:
                                    synergy_matrix_data = {"error": "相関マトリックス計算でNone結果"}
                        
                        # メモリ使用量を監視
                        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                        log.info(f"[SYNERGY] 相関マトリックス分析完了, メモリ使用量: {memory_usage:.1f}MB")
                    else:
                        log.error("[SYNERGY] 相関マトリックス関数が利用できません")
                        synergy_matrix_data = {"error": "相関マトリックス関数が利用できません"}
                except Exception as correlation_error:
                    log.error(f"[SYNERGY] 相関マトリックス処理でエラー: {correlation_error}")
                    synergy_matrix_data = {"error": f"相関マトリックス処理エラー: {str(correlation_error)}"}
            elif synergy_type == 'same_role' and analyze_synergy_by_role is not None:
                log.info("[SYNERGY] 同職種限定シナジー分析を実行")
                synergy_df = analyze_synergy_by_role(long_df, shortage_df, selected_staff, same_role_only=True)
                log.info(f"[SYNERGY] 同職種分析結果: {synergy_df.shape}")
            elif synergy_type == 'all_roles' and analyze_all_roles_synergy is not None:
                log.info("[SYNERGY] 全職種詳細シナジー分析を実行")
                synergy_additional_data = analyze_all_roles_synergy(long_df, shortage_df, selected_staff)
                if 'error' not in synergy_additional_data and 'raw_data' in synergy_additional_data:
                    synergy_df = pd.DataFrame(synergy_additional_data['raw_data'])
                log.info(f"[SYNERGY] 全職種分析結果: {synergy_df.shape}")
            else:
                # 基本分析
                if not shortage_df.empty:
                    log.info("[SYNERGY] 基本シナジー分析を実行")
                    synergy_df = analyze_synergy(long_df, shortage_df, selected_staff)
                    log.info(f"[SYNERGY] 基本分析結果: {synergy_df.shape}")
                else:
                    log.info("[SYNERGY] シンプルなシナジー分析を実行")
                    synergy_df = simple_synergy_analysis(long_df, selected_staff)
                    log.info(f"[SYNERGY] シンプル分析結果: {synergy_df.shape}")
        except Exception as e:
            log.error(f"[SYNERGY] 分析エラー: {e}")
            # メモリクリア
            gc.collect()
            # 相関マトリックスでエラーが発生した場合は、エラーデータを設定
            if synergy_type == 'correlation_matrix':
                if synergy_matrix_data is None:  # まだ設定されていない場合のみ
                    synergy_matrix_data = {"error": f"相関マトリックス計算エラー: {str(e)}"}
            else:
                # エラーが発生した場合は基本分析にフォールバック
                if not shortage_df.empty:
                    try:
                        synergy_df = analyze_synergy(long_df, shortage_df, selected_staff)
                    except Exception as fallback_error:
                        log.error(f"[SYNERGY] フォールバック分析エラー: {fallback_error}")
                        synergy_df = simple_synergy_analysis(long_df, selected_staff)
                else:
                    synergy_df = simple_synergy_analysis(long_df, selected_staff)
    else:
        # long_dfが空の場合
        log.warning("[SYNERGY] long_dfが空のため、シナジー分析をスキップ")
        if synergy_type == 'correlation_matrix':
            if synergy_matrix_data is None:  # まだ設定されていない場合のみ
                synergy_matrix_data = {"error": "勤務データ (long_df) が空のため、シナジー分析ができません"}
        else:
            synergy_df = pd.DataFrame()
    
    # 結果を表示
    if synergy_type == 'correlation_matrix':
        if synergy_matrix_data is not None and 'error' not in synergy_matrix_data:
            # 相関マトリックスの表示
            log.info("[SYNERGY] 相関マトリックス表示")
            
            # ヒートマップ用データ準備
            matrix_df = pd.DataFrame(synergy_matrix_data['matrix'])
            
            # ヒートマップ作成
            synergy_fig = go.Figure(data=go.Heatmap(
                z=matrix_df.values,
                x=matrix_df.columns,
                y=matrix_df.index,
                colorscale='RdBu',
                zmid=0,
                text=np.round(matrix_df.values, 2),
                texttemplate='%{text}',
                textfont={"size": 10},
                hoverongaps=False,
                hovertemplate='%{x} & %{y}<br>シナジースコア: %{z:.3f}<extra></extra>'
            ))
            
            # メモリ効率化：不要なデータを早期解放
            del matrix_df
            gc.collect()
            
            synergy_fig.update_layout(
                title="全職員間のシナジー相関マトリックス",
                xaxis_title="職員",
                yaxis_title="職員",
                width=1200,
                height=1000,
                xaxis={'side': 'bottom', 'tickangle': -45},
                yaxis={'autorange': 'reversed'},
                margin=dict(l=150, r=50, t=100, b=150)
            )
            
            # ランキング表示用のデータフレーム作成
            ranking_df = pd.DataFrame(synergy_matrix_data['ranking'])
            if not ranking_df.empty:
                # 上位5名と下位5名を抽出
                top5 = ranking_df.head(5)
                bottom5 = ranking_df.tail(5)
                
                # 追加情報の表示
                synergy_additional_info = html.Div([
                    html.H5("シナジー平均ランキング"),
                    html.Div([
                        html.Div([
                            html.H6("相性の良い職員 TOP 5", style={'color': 'green'}),
                            dash_table.DataTable(
                                data=top5.to_dict('records'),
                                columns=[
                                    {'name': '職員', 'id': '職員'},
                                    {'name': '平均シナジー', 'id': '平均シナジー', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                                    {'name': '職種', 'id': 'role'} if 'role' in top5.columns else {},
                                ],
                                style_cell={'textAlign': 'left'},
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': '平均シナジー'},
                                        'color': 'green',
                                        'fontWeight': 'bold'
                                    }
                                ]
                            )
                        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
                        html.Div([
                            html.H6("相性の悪い職員 BOTTOM 5", style={'color': 'red'}),
                            dash_table.DataTable(
                                data=bottom5.to_dict('records'),
                                columns=[
                                    {'name': '職員', 'id': '職員'},
                                    {'name': '平均シナジー', 'id': '平均シナジー', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                                    {'name': '職種', 'id': 'role'} if 'role' in bottom5.columns else {},
                                ],
                                style_cell={'textAlign': 'left'},
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': '平均シナジー'},
                                        'color': 'red',
                                        'fontWeight': 'bold'
                                    }
                                ]
                            )
                        ], style={'width': '48%', 'display': 'inline-block'})
                    ], style={'marginTop': '20px'})
                ])
            else:
                synergy_additional_info = html.Div()
            
            # メモリ効率化：処理完了後のデータクリア
            if 'synergy_matrix_data' in locals() and synergy_matrix_data is not None:
                del synergy_matrix_data
            gc.collect()
        
        else:
            # 相関マトリックスでエラーが発生した場合
            log.error(f"[SYNERGY] 相関マトリックスエラー: {synergy_matrix_data.get('error', 'Unknown error') if synergy_matrix_data else 'データなし'}")
            synergy_fig = go.Figure()
            synergy_fig.add_annotation(
                text=f"相関マトリックス分析エラー: {synergy_matrix_data.get('error', 'Unknown error') if synergy_matrix_data else 'データが取得できませんでした'}",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=16, color="red")
            )
            synergy_fig.update_layout(
                title="相関マトリックス分析エラー",
                width=800, height=400
            )
            synergy_additional_info = html.Div()
            
    elif not synergy_df.empty:
        log.info(f"[SYNERGY] 最終結果: {synergy_df.shape}")
        log.info(f"[SYNERGY] サンプルデータ: {synergy_df.head()}")
        
        # 分析タイプに応じた表示
        if synergy_type == 'all_roles' and synergy_additional_data is not None:
            # 全職種詳細分析の場合
            if 'role' in synergy_df.columns:
                # 職種別にグループ化して表示
                synergy_fig = px.bar(
                    synergy_df.head(15), x="相手の職員", y="シナジースコア", 
                    color="role", title=f"{selected_staff}さんとのシナジースコア（全職種詳細）"
                )
                synergy_fig.update_layout(xaxis_title="相手の職員", yaxis_title="シナジースコア（高いほど良い）")
            else:
                synergy_fig = px.bar(
                    synergy_df.head(10), x="相手の職員", y="シナジースコア", color="シナジースコア",
                    color_continuous_scale='RdYlGn', title=f"{selected_staff}さんとのシナジースコア（全職種詳細）"
                )
        elif synergy_type == 'same_role':
            # 同職種限定分析の場合
            color_col = "role" if "role" in synergy_df.columns else "シナジースコア"
            synergy_fig = px.bar(
                synergy_df.head(10), x="相手の職員", y="シナジースコア", color=color_col,
                title=f"{selected_staff}さんとのシナジースコア（同職種限定）"
            )
            synergy_fig.update_layout(xaxis_title="相手の職員", yaxis_title="シナジースコア（高いほど良い）")
        else:
            # 基本分析の場合
            synergy_df_top5 = synergy_df.head(5)
            if len(synergy_df) > 5:
                synergy_df_worst5 = synergy_df.tail(5).sort_values("シナジースコア", ascending=True)
                synergy_display_df = pd.concat([synergy_df_top5, synergy_df_worst5])
            else:
                synergy_display_df = synergy_df_top5
            
            synergy_fig = px.bar(
                synergy_display_df, x="相手の職員", y="シナジースコア", color="シナジースコア",
                color_continuous_scale='RdYlGn', title=f"{selected_staff}さんとのシナジースコア（基本分析）"
            )
            synergy_fig.update_layout(xaxis_title="相手の職員", yaxis_title="シナジースコア（高いほど良い）")
    else:
        log.warning("[SYNERGY] 全ての分析が失敗またはデータ不足")
        synergy_fig.add_annotation(
            text="シナジー分析のデータが不十分です",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=16)
        )
    
    # 相関マトリックスの追加情報を初期化（存在しない場合）
    # 既に上部で初期化済みのため、ここでは不要

    # --- 7 & 8. 働き方のクセ分析 ---
    mannelido_score, rhythm_score = "計算不可", "計算不可"
    work_records_for_role = staff_df[staff_df.get('parsed_slots_count', 0) > 0]
    if not work_records_for_role.empty:
        role_per_day = work_records_for_role[['ds', 'role']].copy()
        role_per_day['date'] = role_per_day['ds'].dt.date
        role_counts = role_per_day.drop_duplicates(subset=['date', 'role'])['role'].value_counts(normalize=True)
        if not role_counts.empty:
            mannelido_score = f"{role_counts.max():.2f}"

        daily_starts = work_records_for_role.groupby(work_records_for_role['ds'].dt.date)['ds'].min()
        if len(daily_starts) > 1:
            start_hours = daily_starts.dt.hour + daily_starts.dt.minute / 60.0
            rhythm_score = f"{start_hours.std():.2f}"
        else:
            rhythm_score = "0.00"

    # --- レイアウトの組み立て ---
    layout = html.Div([
        html.Div([
            html.Div([
                html.H4("疲労度・不公平感・働き方のクセ"),
                create_metric_card("疲労スコア", fatigue_score, color="#ff7f0e"),
                create_metric_card("不公平感スコア", unfairness_score, color="#d62728"),
                create_metric_card("業務マンネリ度", mannelido_score, color="#9467bd"),
                create_metric_card("生活リズム破壊度", rhythm_score, color="#8c564b"),
            ], style={'width': '24%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '1%'}),
            html.Div([
                html.H5("不公平感スコアの内訳"),
                dash_table.DataTable(
                    data=score_details_df.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in score_details_df.columns],
                ) if not score_details_df.empty else html.P("詳細データなし")
            ], style={'width': '24%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '1%'}),
            html.Div([
                html.H5("共働ランキング Top 5"),
                dash_table.DataTable(
                    data=coworker_ranking_df.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in coworker_ranking_df.columns],
                ) if not coworker_ranking_df.empty else html.P("共働データなし"),
            ], style={'width': '24%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '1%'}),
            html.Div([
                html.H5("不足/過剰への貢献度"),
                create_metric_card("不足時間帯での勤務 (h)", f"{shortage_contribution_h:.1f}", color="#c53d40"),
                create_metric_card("過剰時間帯での勤務 (h)", f"{excess_contribution_h:.1f}", color="#1f77b4"),
            ], style={'width': '24%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ], style={'marginBottom': '20px'}),
        html.Div([
            html.Div([dcc.Graph(figure=work_dist_fig)], style={'width': '49%', 'display': 'inline-block'}),
            html.Div([dcc.Graph(figure=leave_by_dow_fig)], style={'width': '49%', 'display': 'inline-block'}),
        ]),
        html.Div([
            html.H4("職員間の\u300c化学反応\u300d分析", style={'marginTop': '20px'}),
            html.P("シナジースコアは、そのペアが一緒に勤務した際の\u300c人員不足の起こりにくさ\u300dを示します。スコアが高いほど、不足が少なくなる良い組み合わせです。"),
            
            # 分析タイプ別の追加情報
            html.Div([
                html.H5("分析情報"),
                html.Div([
                    html.P(f"分析タイプ: {['基本分析（全職員対象）' if synergy_type == 'basic' else '同職種限定分析' if synergy_type == 'same_role' else '全職種詳細分析' if synergy_type == 'all_roles' else '相関マトリックス（全体）'][0]}", style={'fontWeight': 'bold'})
                ] + ([
                    html.P(f"全体平均シナジー: {synergy_additional_data['overall_stats']['全体平均シナジー']:.3f}"),
                    html.P(f"分析対象職員数: {synergy_additional_data['overall_stats']['分析対象職員数']}人"),
                    html.P(f"対象職種数: {synergy_additional_data['overall_stats']['対象職種数']}職種"),
                ] if synergy_type == 'all_roles' and synergy_additional_data is not None and 'overall_stats' in synergy_additional_data else []) + ([
                    html.P(f"分析対象職員数: {synergy_matrix_data['summary']['職員数']}人"),
                    html.P(f"全体平均シナジー: {synergy_matrix_data['summary']['全体平均シナジー']:.3f}"),
                ] if synergy_type == 'correlation_matrix' and 'synergy_matrix_data' in locals() and synergy_matrix_data is not None and 'summary' in synergy_matrix_data else []))
            ], style={'marginBottom': '10px', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}) if synergy_type != 'basic' else html.Div(),
            
            dcc.Graph(figure=synergy_fig),
            
            # 相関マトリックスの場合、追加情報を表示
            synergy_additional_info if synergy_type == 'correlation_matrix' and 'synergy_additional_info' in locals() and synergy_additional_info is not None else html.Div()
        ])
    ])

    return layout


@app.callback(
    Output('team-criteria-value-dropdown', 'options'),
    Input('team-criteria-key-dropdown', 'value')
)
@safe_callback
def update_team_value_options(selected_key):
    long_df = data_get('long_df', pd.DataFrame())
    if long_df.empty or not selected_key:
        return []
    options = sorted(long_df[selected_key].unique())
    return [{'label': opt, 'value': opt} for opt in options]


@app.callback(
    Output('team-analysis-content', 'children'),
    Input('team-criteria-value-dropdown', 'value'),
    State('team-criteria-key-dropdown', 'value')
)
@safe_callback
def update_team_analysis_graphs(selected_value, selected_key):
    if not selected_value or not selected_key:
        raise PreventUpdate

    long_df = data_get('long_df', pd.DataFrame())
    fatigue_df = data_get('fatigue_score', pd.DataFrame())
    fairness_df = data_get('fairness_after', pd.DataFrame())

    team_criteria = {selected_key: selected_value}
    team_df = analyze_team_dynamics(long_df, fatigue_df, fairness_df, team_criteria)

    if team_df.empty:
        return html.P("この条件に合致するチームデータはありません。")

    fig_fatigue = px.line(
        team_df,
        y=['avg_fatigue', 'std_fatigue'],
        title=f"チーム「{selected_value}」の疲労度スコア推移"
    )
    fig_fairness = px.line(
        team_df,
        y=['avg_unfairness', 'std_unfairness'],
        title=f"チーム「{selected_value}」の不公平感スコア推移"
    )

    return html.Div([
        html.H4(f"チーム「{selected_value}」の分析結果"),
        
        # グラフの読み解き方説明を追加
        html.Div([
            html.H5("📊 グラフの読み解き方"),
            html.Div([
                html.P("🔍 疲労度スコア推移グラフの見方:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                html.Ul([
                    html.Li("平均疲労度（avg_fatigue）: チーム全体の疲労レベル。数値が高いほど疲労が蓄積している"),
                    html.Li("疲労度のばらつき（std_fatigue）: チーム内の疲労格差。数値が高いほど個人差が大きい"),
                    html.Li("⚠️ 両方が高い場合: チーム全体が疲弊し、かつ個人差も大きく不安定な状態"),
                    html.Li("✅ 理想的な状態: 平均疲労度が低く、ばらつきも小さい状態")
                ]),
                
                html.P("🔍 不公平感スコア推移グラフの見方:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                html.Ul([
                    html.Li("平均不公平感（avg_unfairness）: チーム全体の不公平感。数値が高いほど不満が蓄積している"),
                    html.Li("不公平感のばらつき（std_unfairness）: チーム内の不公平感格差。数値が高いほど個人差が大きい"),
                    html.Li("⚠️ 平均が高い場合: 業務配分や待遇に全体的な不公平感がある可能性"),
                    html.Li("⚠️ ばらつきが大きい場合: 一部のメンバーが特に不公平感を感じている可能性"),
                    html.Li("✅ 理想的な状態: 平均不公平感が低く、ばらつきも小さい状態")
                ])
            ], style={
                'backgroundColor': '#f8f9fa',
                'padding': '15px',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #dee2e6'
            })
        ]),
        
        dcc.Graph(figure=fig_fatigue),
        dcc.Graph(figure=fig_fairness),
        
        # 改善提案セクション
        html.Div([
            html.H5("💡 改善提案"),
            html.P("分析結果に基づく具体的な改善アクション:"),
            html.Ul([
                html.Li("疲労度が高い場合: 勤務間隔の調整、休暇取得の促進、業務量の見直し"),
                html.Li("疲労度のばらつきが大きい場合: 業務分担の均等化、特定メンバーの負荷軽減"),
                html.Li("不公平感が高い場合: 勤務条件の透明化、希望休承認の公平化"),
                html.Li("不公平感のばらつきが大きい場合: 個別面談の実施、不満の聞き取り調査")
            ])
        ], style={
            'backgroundColor': '#e7f3ff',
            'padding': '15px',
            'borderRadius': '8px',
            'marginTop': '20px',
            'border': '1px solid #b3d9ff'
        })
    ])


@app.callback(
    Output('blueprint-results-store', 'data'),
    Output('tradeoff-scatter-plot', 'figure'),
    Output('rules-data-table', 'data'),
    Output('staff-selector-dropdown', 'options'),
    Output('facts-data-table', 'data', allow_duplicate=True),
    Output('facts-summary', 'children'),
    Output('integrated-analysis-content', 'children'),
    Input('generate-blueprint-button', 'n_clicks'),
    State('blueprint-analysis-type', 'value'),
    prevent_initial_call=True
)
@safe_callback
def update_blueprint_analysis_content(n_clicks, analysis_type):
    if not n_clicks:
        raise PreventUpdate

    try:
        long_df = data_get('long_df', pd.DataFrame())
        if long_df.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="データが見つかりません",
                annotations=[
                    dict(
                        text="シフトデータを読み込んでから分析を実行してください。<br><br>" +
                             "📋 手順:<br>" +
                             "1. Excelファイルをアップロード<br>" +
                             "2. データ処理の完了を確認<br>" +
                             "3. 再度分析ボタンをクリック",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5, xanchor='center', yanchor='middle',
                        showarrow=False,
                        font=dict(size=14, color="#666"),
                        bgcolor="rgba(240, 240, 240, 0.8)",
                        bordercolor="#ccc",
                        borderwidth=1
                    )
                ]
            )
            helpful_message = html.Div([
                html.H4("🔍 ブループリント分析について", style={'color': '#1976d2'}),
                html.P("ブループリント分析は、シフト作成者の暗黙知や判断パターンを発見する高度な分析機能です。"),
                html.H5("💡 分析で発見できること:"),
                html.Ul([
                    html.Li("スタッフ個別の勤務パターンや制約"),
                    html.Li("シフト作成者の暗黙的なルール"),
                    html.Li("職種・チーム間の相互関係"),
                    html.Li("効率的なシフト組み合わせ"),
                ]),
                html.P("分析を実行するには、まずシフトデータを読み込んでください。", 
                       style={'fontWeight': 'bold', 'color': '#d32f2f'})
            ], style={
                'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px',
                'border': '1px solid #dee2e6', 'marginTop': '20px'
            })
            return {}, empty_fig, [], [], [], helpful_message, helpful_message

        blueprint_data = create_blueprint_list(long_df)

        scatter_df = pd.DataFrame(blueprint_data.get('tradeoffs', {}).get('scatter_data', []))
        fig_scatter = px.scatter(scatter_df, x='fairness_score', y='cost_score', hover_data=['date']) if not scatter_df.empty else go.Figure()

        rules_df = blueprint_data.get('rules_df', pd.DataFrame())
        rules_table_data = []

        if not rules_df.empty:
            if '詳細データ' in rules_df.columns:
                def safe_json_serialize(x):
                    if isinstance(x, dict):
                        try:
                            # NumPy型を標準Python型に変換
                            clean_dict = {}
                            for k, v in x.items():
                                if hasattr(v, 'item'):  # NumPy scalar
                                    clean_dict[k] = v.item()
                                elif isinstance(v, (list, tuple)):
                                    clean_dict[k] = [item.item() if hasattr(item, 'item') else item for item in v]
                                else:
                                    clean_dict[k] = v
                            return json.dumps(clean_dict, ensure_ascii=False, indent=2)
                        except (TypeError, ValueError):
                            return str(x)
                    else:
                        return str(x)
                
                rules_df['詳細データ'] = rules_df['詳細データ'].apply(safe_json_serialize)
            rules_table_data = rules_df.to_dict('records')

        staff_scores_df = blueprint_data.get('staff_level_scores', pd.DataFrame())
        dropdown_options = [{'label': s, 'value': s} for s in staff_scores_df.index] if not staff_scores_df.empty else []

        facts_df = blueprint_data.get('facts_df', pd.DataFrame())
        facts_table_data = []
        facts_summary = "事実データがありません"
        
        # 🔍 拡張ルール分析の結果表示
        rule_stats = blueprint_data.get('rule_statistics', {})
        total_rules = rule_stats.get('total_rules', 0)
        high_conf_rules = rule_stats.get('high_confidence_rules', 0)
        
        enhanced_summary = html.Div([
            html.Div([
                html.H4("🎯 シフト作成者の暗黙知分析結果", style={'margin': '0 0 15px 0', 'color': '#1976d2'}),
                html.Div([
                    html.Div([
                        html.H3(str(total_rules), style={'margin': '0', 'color': '#2e7d32', 'fontSize': '2rem'}),
                        html.P("発見されたルール", style={'margin': '0', 'fontSize': '0.9rem', 'color': '#666'})
                    ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#e8f5e8', 
                             'borderRadius': '8px', 'border': '2px solid #2e7d32', 'flex': '1'}),
                    html.Div([
                        html.H3(str(high_conf_rules), style={'margin': '0', 'color': '#ff9800', 'fontSize': '2rem'}),
                        html.P("高信頼度ルール", style={'margin': '0', 'fontSize': '0.9rem', 'color': '#666'})
                    ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#fff3e0', 
                             'borderRadius': '8px', 'border': '2px solid #ff9800', 'flex': '1'}),
                    html.Div([
                        html.H3(f"{(high_conf_rules/total_rules*100):.1f}%" if total_rules > 0 else "0%", 
                               style={'margin': '0', 'color': '#1976d2', 'fontSize': '2rem'}),
                        html.P("信頼度率", style={'margin': '0', 'fontSize': '0.9rem', 'color': '#666'})
                    ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#e3f2fd', 
                             'borderRadius': '8px', 'border': '2px solid #1976d2', 'flex': '1'}),
                ], style={'display': 'flex', 'gap': '15px'}),
            ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '12px', 
                     'boxShadow': '0 4px 8px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),
        ]) if blueprint_data.get('enhanced_rules') else html.Div([
            html.Div([
                html.H4("⚠️ 拡張分析データ", style={'color': '#ff9800'}),
                html.P("拡張分析データが生成されていません。データ量が不足している可能性があります。", 
                       style={'color': '#666', 'marginBottom': '10px'}),
                html.P("💡 改善方法:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                html.Ul([
                    html.Li("より多くのシフトデータを使用する"),
                    html.Li("異なる期間のデータを追加する"),
                    html.Li("スタッフ数を増やす"),
                ])
            ], style={'padding': '15px', 'backgroundColor': '#fff3e0', 'borderRadius': '8px',
                     'border': '1px solid #ff9800'})
        ])
        
        # 🔍 拡張ルールの表形式データ作成
        enhanced_table_data = []
        if blueprint_data.get('enhanced_rules'):
            for rule in blueprint_data.get('enhanced_rules', []):
                enhanced_table_data.append({
                    'スタッフ': rule.staff_name,
                    'ルールタイプ': rule.rule_type,
                    'ルール内容': rule.rule_description,
                    '信頼度': f"{rule.confidence_score:.2f}",
                    'セグメント': rule.segment,
                    '統計的証拠': str(rule.statistical_evidence.get('sample_size', 'N/A'))
                })

        if not facts_df.empty:
            facts_df = facts_df.sort_values('確信度', ascending=False)
            facts_table_data = facts_df.to_dict('records')

            total_facts = len(facts_df)
            high_confidence_facts = len(facts_df[facts_df['確信度'] >= 0.8])
            unique_staff = facts_df['スタッフ'].nunique()

            facts_summary = html.Div([
                html.Div([
                    html.H4("📊 事実分析サマリー", style={'margin': '0 0 15px 0', 'color': '#1976d2'}),
                    html.Div([
                        html.Div([
                            html.H3(str(total_facts), style={'margin': '0', 'color': '#2e7d32', 'fontSize': '2rem'}),
                            html.P("発見された事実", style={'margin': '0', 'fontSize': '0.9rem', 'color': '#666'})
                        ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#e8f5e8', 
                                 'borderRadius': '8px', 'border': '2px solid #2e7d32'}),
                        html.Div([
                            html.H3(str(high_confidence_facts), style={'margin': '0', 'color': '#ff9800', 'fontSize': '2rem'}),
                            html.P("高確信度(80%+)", style={'margin': '0', 'fontSize': '0.9rem', 'color': '#666'})
                        ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#fff3e0', 
                                 'borderRadius': '8px', 'border': '2px solid #ff9800'}),
                        html.Div([
                            html.H3(str(unique_staff), style={'margin': '0', 'color': '#1976d2', 'fontSize': '2rem'}),
                            html.P("分析対象スタッフ", style={'margin': '0', 'fontSize': '0.9rem', 'color': '#666'})
                        ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#e3f2fd', 
                                 'borderRadius': '8px', 'border': '2px solid #1976d2'}),
                    ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '20px'}),
                ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '12px', 
                         'boxShadow': '0 4px 8px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),
                
                html.Div([
                    html.H5("📈 カテゴリー別内訳", style={'marginBottom': '15px', 'color': '#1976d2'}),
                    html.Div([
                        html.Div([
                            html.Strong(f"{cat}: "),
                            html.Span(f"{len(df)}件", style={'color': '#2e7d32', 'fontWeight': 'bold'})
                        ], style={'padding': '8px 12px', 'backgroundColor': '#f5f5f5', 'borderRadius': '6px',
                                 'margin': '5px', 'display': 'inline-block', 'border': '1px solid #ddd'})
                        for cat, df in blueprint_data.get('facts_by_category', {}).items()
                        if not df.empty
                    ])
                ], style={'padding': '15px', 'backgroundColor': '#fafafa', 'borderRadius': '8px',
                         'border': '1px solid #e0e0e0'})
            ])

        # 🔍 拡張分析とセグメント分析の統合表示
        segment_analysis = blueprint_data.get('segment_analysis', {})
        constraint_nature = blueprint_data.get('constraint_nature', {})
        advanced_constraints = blueprint_data.get('advanced_constraints', {})
        team_dynamics = blueprint_data.get('team_dynamics', {})
        
        integrated_content = html.Div([
            html.H5("🎯 シフト作成者の暗黙知分析結果"),
            enhanced_summary
        ])

        # Store data for other callbacks
        store_data = {
            'rules_df': rules_df.to_json(orient='split') if not rules_df.empty else None,
            'scored_df': blueprint_data.get('scored_df', pd.DataFrame()).to_json(orient='split') if blueprint_data.get('scored_df') is not None and not blueprint_data.get('scored_df').empty else None,
            'tradeoffs': blueprint_data.get('tradeoffs', {}),
            'staff_level_scores': blueprint_data.get('staff_level_scores', pd.DataFrame()).to_json(orient='split') if blueprint_data.get('staff_level_scores') is not None and not blueprint_data.get('staff_level_scores').empty else None,
            'facts_df': facts_df.to_json(orient='split') if not facts_df.empty else None,
            'facts_by_category': {k: v.to_json(orient='split') for k, v in blueprint_data.get('facts_by_category', {}).items()}
        }

        return store_data, fig_scatter, rules_table_data, dropdown_options, facts_table_data, facts_summary, integrated_content
    
    except Exception as e:
        log.error(f"ブループリント分析でエラーが発生: {str(e)}", exc_info=True)
        empty_fig = go.Figure()
        error_msg = f"エラーが発生しました: {str(e)}"
        return {}, empty_fig, [], [], [], error_msg, error_msg
@app.callback(
    Output('facts-data-table', 'data', allow_duplicate=True),
    Input('fact-category-filter', 'value'),
    State('blueprint-results-store', 'data'),
    prevent_initial_call=True
)
@safe_callback
def filter_facts_by_category(selected_category, stored_data):
    """カテゴリーで事実をフィルタリング"""
    if not stored_data or not stored_data.get('facts_df'):
        return []

    facts_df = pd.read_json(stored_data['facts_df'], orient='split')

    if selected_category == 'all':
        filtered_df = facts_df
    else:
        filtered_df = facts_df[facts_df['カテゴリー'] == selected_category]

    filtered_df = filtered_df.sort_values('確信度', ascending=False)

    return filtered_df.to_dict('records')


def _extract_staff_from_rule(rule_text: str, staff_names: list[str]) -> str | None:
    """Return first staff name found in rule text."""
    for name in staff_names:
        if name in rule_text:
            return name
    return None


@app.callback(
    Output('staff-radar-chart', 'figure'),
    Output('staff-related-rules-list', 'children'),
    Input('staff-selector-dropdown', 'value'),
    Input('rules-data-table', 'selected_rows'),
    State('blueprint-results-store', 'data'),
    State('rules-data-table', 'data'),
    prevent_initial_call=True,
)
@safe_callback
def update_staff_view(selected_staff, selected_row_indices, stored_data, table_data):
    if not stored_data:
        raise PreventUpdate

    rules_json = stored_data.get('rules_df')
    staff_json = stored_data.get('staff_level_scores')
    if not rules_json or not staff_json:
        return go.Figure(), "データがありません。"

    rules_df = pd.read_json(rules_json, orient='split')
    staff_scores_df = pd.read_json(staff_json, orient='split')

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    target_staff = selected_staff
    if trigger_id == 'rules-data-table' and selected_row_indices:
        clicked_rule = table_data[selected_row_indices[0]]
        target_staff = _extract_staff_from_rule(clicked_rule.get('発見された法則', ''), list(staff_scores_df.index))

    if not target_staff or target_staff not in staff_scores_df.index:
        return go.Figure(), "スタッフを選択してください。"

    row = staff_scores_df.loc[target_staff]
    score_cols = ['fairness_score', 'cost_score', 'risk_score', 'satisfaction_score']
    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=row[score_cols].tolist(),
            theta=['公平性', 'コスト', 'リスク', '満足度'],
            fill='toself',
            name=target_staff,
        )
    )
    fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), showlegend=False)

    related_rules = rules_df[rules_df['発見された法則'].str.contains(target_staff)]
    rule_list_items = [html.P(r) for r in related_rules['発見された法則'].tolist()] if not related_rules.empty else [html.P('関連ルールなし')]

    return fig_radar, rule_list_items


@app.callback(
    Output('sim-shortage-graph', 'figure'),
    Output('sim-cost-text', 'children'),
    Input('sim-work-pattern-dropdown', 'value'),
    Input('sim-hire-fte-slider', 'value'),
    State('kpi-data-store', 'data'),
)
@safe_callback
def update_hire_simulation(selected_pattern, added_fte, kpi_data):
    if not kpi_data or not selected_pattern:
        raise PreventUpdate

    from shift_suite.tasks.h2hire import (
        AVG_HOURLY_WAGE,
        RECRUIT_COST_PER_HIRE,
    )

    df_work_patterns = data_get('work_patterns', pd.DataFrame())
    df_shortage_role = data_get('shortage_role_summary', pd.DataFrame()).copy()

    pattern_info = df_work_patterns[df_work_patterns['code'] == selected_pattern]
    if pattern_info.empty:
        raise PreventUpdate
    slots_per_day = pattern_info['parsed_slots_count'].iloc[0]
    hours_per_day = slots_per_day * 0.5
    reduction_hours = added_fte * hours_per_day * 20

    if not df_shortage_role.empty:
        most_lacking_role_index = df_shortage_role['lack_h'].idxmax()
        original_hours = df_shortage_role.loc[most_lacking_role_index, 'lack_h']
        df_shortage_role.loc[most_lacking_role_index, 'lack_h'] = max(0, original_hours - reduction_hours)

    fig = px.bar(
        df_shortage_role,
        x='role',
        y='lack_h',
        title=f'シミュレーション後: {selected_pattern}勤務者を{added_fte}人追加採用した場合の残存不足時間',
        labels={'lack_h': '残存不足時間(h)'},
    )

    # 正しい総不足時間の計算
    new_total_lack_h = 0
    if 'lack_h' in df_shortage_role.columns:
        total_rows = df_shortage_role[df_shortage_role['role'].isin(['全体', '合計', '総計'])]
        if not total_rows.empty:
            new_total_lack_h = total_rows['lack_h'].iloc[0]
        else:
            shortage_time_df = data_get('shortage_time', pd.DataFrame())
            if not shortage_time_df.empty:
                try:
                    shortage_values = shortage_time_df.select_dtypes(include=[np.number]).values
                    new_total_lack_h = float(np.nansum(shortage_values) * 0.5)
                except:
                    new_total_lack_h = df_shortage_role['lack_h'].sum()
            else:
                new_total_lack_h = df_shortage_role['lack_h'].sum()
    
    original_total_lack_h = kpi_data.get('total_lack_h', 0)

    cost_before = original_total_lack_h * 2200
    cost_after_temp = new_total_lack_h * 2200

    added_labor_cost = reduction_hours * AVG_HOURLY_WAGE
    added_recruit_cost = added_fte * RECRUIT_COST_PER_HIRE
    cost_after_hire = cost_after_temp + added_labor_cost + added_recruit_cost

    cost_text = f"""
    #### シミュレーション結果
    - **採用コスト:** {added_recruit_cost:,.0f} 円 (一時)
    - **追加人件費:** {added_labor_cost:,.0f} 円 (期間中)
    - **総コスト (採用シナリオ):** {cost_after_hire:,.0f} 円
    - **比較 (全て派遣で補填した場合):** {cost_before:,.0f} 円
    """

    return fig, dcc.Markdown(cost_text)


@app.callback(
    Output('factor-output', 'children'),
    Input('factor-train-button', 'n_clicks')
)
@safe_callback
def run_factor_analysis(n_clicks):
    if not n_clicks:
        raise PreventUpdate

    heat_df = data_get('heat_ALL')
    short_df = data_get('shortage_time')
    leave_df = data_get('leave_analysis')

    if heat_df is None or heat_df.empty or short_df is None or short_df.empty:
        return html.Div('必要なデータがありません')

    analyzer = ShortageFactorAnalyzer()
    feat_df = analyzer.generate_features(pd.DataFrame(), heat_df, short_df, leave_df, set())
    model, fi_df = analyzer.train_and_get_feature_importance(feat_df)
    DATA_CACHE.set('factor_features', feat_df)
    DATA_CACHE.set('factor_importance', fi_df)

    table = dash_table.DataTable(
        data=fi_df.head(5).to_dict('records'),
        columns=[{'name': c, 'id': c} for c in fi_df.columns]
    )
    return html.Div([html.H5('影響度の高い要因 トップ5'), table])  # type: ignore


def generate_lightweight_tree_visualization(tree_model):
    """Generate a small decision tree visualisation."""
    if not tree_model or not hasattr(tree_model, 'tree_'):
        return html.P('決定木モデルを生成できませんでした。')

    try:
        buf = io.BytesIO()
        fig, ax = plt.subplots(figsize=(12, 6))
        plot_tree(
            tree_model,
            filled=True,
            feature_names=tree_model.feature_names_in_[:20],
            max_depth=2,
            fontsize=8,
            ax=ax,
            impurity=False,
            proportion=True,
        )
        fig.savefig(buf, format='png', dpi=72, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        encoded = base64.b64encode(buf.getvalue()).decode()
        return html.Img(
            src=f"data:image/png;base64,{encoded}",
            style={'width': '100%', 'maxWidth': '1000px'},
        )
    except Exception as exc:  # noqa: BLE001
        log.error(f'決定木可視化エラー: {exc}')
        return html.P(f'決定木の可視化に失敗しました: {exc}')


def generate_results_display(full_results):
    """Create the final display for logic analysis results."""
    mind_results = full_results.get('mind_reading', {})

    if 'error' in mind_results:
        return html.Div(f"分析エラー: {mind_results['error']}", style={'color': 'red'})

    importance_df = pd.DataFrame(mind_results.get('feature_importance', []))
    fig_bar = px.bar(
        importance_df.sort_values('importance', ascending=False).head(15),
        x='importance',
        y='feature',
        orientation='h',
        title='判断基準の重要度（TOP15）',
    )

    tree_content = generate_lightweight_tree_visualization(
        mind_results.get('thinking_process_tree')
    )

    return html.Div([
        html.H4('分析完了！'),
        html.Hr(),
        html.H4('判断基準の重要度'),
        html.P('作成者がどの要素を重視しているかを数値化したものです。'),
        dcc.Graph(figure=fig_bar),
        html.H4('思考フローチャート', style={'marginTop': '30px'}),
        html.P('配置を決定する際の思考の分岐を模倣したものです。'),
        tree_content,
    ])


@app.callback(
    Output('save-log-msg', 'children'),
    Input('save-log-button', 'n_clicks'),
    State('over-shortage-table', 'data'),
    State('log-save-mode', 'value')
)
@safe_callback
def save_over_shortage_log(n_clicks, table_data, mode):
    if not n_clicks:
        raise PreventUpdate

    log_path = data_get('shortage_log_path')
    if not log_path:
        return 'ログファイルパスが見つかりません'  # type: ignore

    df = pd.DataFrame(table_data)
    over_shortage_log.save_log(df, log_path, mode=mode)
    return 'ログを保存しました'


@app.callback(Output('log-viewer', 'value'), Input('log-interval', 'n_intervals'))
@safe_callback
def update_log_viewer(n):
    """ログバッファの内容を定期的に更新"""
    log_stream.seek(0)
    return log_stream.read()


@app.callback(
    Output('creation-logic-results', 'children'),
    Output('full-analysis-store', 'data'),
    Input('analyze-creation-logic-button', 'n_clicks'),
    State('analysis-detail-level', 'value'),
    prevent_initial_call=True,
)
@safe_callback
def update_logic_analysis_immediate(n_clicks, detail_level):
    """Show basic results immediately and start deep analysis."""

    if not n_clicks:
        raise PreventUpdate

    long_df = data_get('long_df', pd.DataFrame())
    if long_df.empty:
        return html.Div('分析データが見つかりません。', style={'color': 'red'}), None

    basic_stats = get_basic_shift_stats(long_df)
    quick_patterns = get_quick_patterns(long_df.head(500))

    immediate_results = html.Div([
        html.H4('✅ 基本分析完了（詳細分析実行中...）', style={'color': 'green'}),
        html.Hr(),
        html.Div([
            html.H5('📊 シフトの基本統計'),
            create_stats_cards(basic_stats),
        ]),
        html.Div([
            html.H5('🔍 発見された主要パターン（簡易版）'),
            create_pattern_list(quick_patterns),
        ], style={'marginTop': '20px'}),
        html.Div([
            html.H5('🧠 AIによる深層分析'),
            dcc.Loading(id='deep-analysis-loading', children=html.Div(id='deep-analysis-results'), type='circle'),
        ], style={'marginTop': '30px'}),
        dcc.Interval(id='background-trigger', interval=100, n_intervals=0, max_intervals=1),
    ])

    return immediate_results, {'status': 'pending', 'level': detail_level}


@app.callback(
    Output('deep-analysis-results', 'children'),
    Input('background-trigger', 'n_intervals'),
    State('analysis-detail-level', 'value'),
    prevent_initial_call=True,
)
@safe_callback
def run_deep_analysis_background(n_intervals, detail_level):
    """Run deeper analysis in the background."""

    if n_intervals == 0:
        raise PreventUpdate

    long_df = data_get('long_df', pd.DataFrame())
    results = run_optimized_analysis(long_df, detail_level)

    return create_deep_analysis_display(results)


@app.callback(
    Output('progress-bar', 'figure'),
    Output('progress-message', 'children'),
    Input('logic-analysis-interval', 'n_intervals'),
    State('logic-analysis-progress', 'data'),
    prevent_initial_call=True,
)
@safe_callback
def update_progress_bar(n_intervals, progress_data):
    """Update the progress bar display."""
    if not progress_data:
        raise PreventUpdate

    progress = progress_data.get('progress', 0)
    stage = progress_data.get('stage', 'loading')

    messages = {
        'loading': 'データを読み込んでいます...',
        'analyzing': 'シフトパターンを分析しています...',
        'visualizing': '結果を可視化しています...',
    }

    figure = {
        'data': [{
            'x': [progress],
            'y': ['Progress'],
            'type': 'bar',
            'orientation': 'h',
            'marker': {'color': '#1f77b4'},
        }],
        'layout': {
            'xaxis': {'range': [0, 100], 'title': '進捗率 (%)'},
            'yaxis': {'visible': False},
            'height': 100,
            'margin': {'l': 0, 'r': 0, 't': 30, 'b': 30},
        },
    }

    return figure, messages.get(stage, '処理中...')



# --- アプリケーション起動 ---
if __name__ == '__main__':
    app.run_server(debug=True, port=8050, host='127.0.0.1')
