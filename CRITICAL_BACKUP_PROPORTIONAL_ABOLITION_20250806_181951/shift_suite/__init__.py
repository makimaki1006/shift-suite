"""
shift_suite 初期化（セーフモード）
  * 問題のあるモジュールをスキップして安全にインポート
"""
from importlib import import_module
from pathlib import Path
import pkgutil, sys, importlib
import logging

log = logging.getLogger(__name__)

# 問題のあるモジュール（scikit-learn/lightgbm依存）
PROBLEMATIC_MODULES = {
    'shift_mind_reader',
    'advanced_blueprint_engine_v2',
    'fatigue_prediction'
}

# ────────────────────────────────────────────── tasks 安全読み込み
_tasks_dir = Path(__file__).with_name("tasks")
for modinfo in pkgutil.iter_modules([str(_tasks_dir)]):
    dotted = f"shift_suite.tasks.{modinfo.name}"   # ex) shift_suite.tasks.heatmap
    
    # 問題のあるモジュールをスキップ
    if modinfo.name in PROBLEMATIC_MODULES:
        log.warning(f"Skipping problematic module: {modinfo.name}")
        continue
    
    try:
        mod = import_module(dotted)                 # 実体 import
        # 旧: shift_suite.<name> でも参照可
        sys.modules[f"shift_suite.{modinfo.name}"] = mod
        globals()[modinfo.name] = mod                  # from shift_suite import heatmap
    except Exception as e:
        log.warning(f"Failed to import {dotted}: {e}")
        continue

# ────────────────────────────────────────────── util & 主要関数 re-export
try:
    utils = import_module("shift_suite.tasks.utils")
    
    excel_date = utils.excel_date
    to_hhmm = utils.to_hhmm
    
    # 安全にインポートできるもののみ
    safe_imports = [
        ("io_excel", "ingest_excel"),
        ("heatmap", "build_heatmap"),
        ("shortage", "shortage_and_brief"),
        ("build_stats", "build_stats"),
        ("anomaly", "detect_anomaly"),
        ("cluster", "cluster_staff"),
        ("fairness", "run_fairness"),
        ("forecast", "build_demand_series"),
        ("forecast", "forecast_need")
    ]
    
    for module_name, func_name in safe_imports:
        try:
            if f"shift_suite.{module_name}" in sys.modules:
                globals()[func_name] = getattr(sys.modules[f"shift_suite.{module_name}"], func_name)
            elif f"shift_suite.tasks.{module_name}" in sys.modules:
                globals()[func_name] = getattr(sys.modules[f"shift_suite.tasks.{module_name}"], func_name)
        except (AttributeError, KeyError) as e:
            log.warning(f"Could not import {func_name} from {module_name}: {e}")
            
except Exception as e:
    log.error(f"Failed to setup basic utilities: {e}")

# 軽量版の代替インポート
try:
    from .tasks.shift_mind_reader_lite import ShiftMindReaderLite
    globals()['ShiftMindReaderLite'] = ShiftMindReaderLite
    log.info("ShiftMindReaderLite available as fallback")
except ImportError as e:
    log.warning(f"ShiftMindReaderLite not available: {e}")