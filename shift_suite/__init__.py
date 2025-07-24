"""
shift_suite 初期化
  * shift_suite.tasks 内の *.py を全部 lazy import
  * 旧来の `shift_suite.heatmap` などの名前もそのまま生かす
"""
from importlib import import_module
from pathlib import Path
import pkgutil, sys, importlib

# ────────────────────────────────────────────── tasks 全読み込み
_tasks_dir = Path(__file__).with_name("tasks")
# Skip problematic modules that require TensorFlow/Gymnasium/OR-Tools
skip_modules = {"rl", "fatigue_prediction", "assignment"}
for modinfo in pkgutil.iter_modules([str(_tasks_dir)]):
    if modinfo.name in skip_modules:
        continue
    dotted = f"shift_suite.tasks.{modinfo.name}"   # ex) shift_suite.tasks.heatmap
    try:
        mod    = import_module(dotted)                 # 実体 import
        # 旧: shift_suite.<name> でも参照可
        sys.modules[f"shift_suite.{modinfo.name}"] = mod
        globals()[modinfo.name] = mod                  # from shift_suite import heatmap
    except ImportError as e:
        print(f"Warning: Could not import {dotted}: {e}")
        continue

# ────────────────────────────────────────────── util & 主要関数 re-export
utils = import_module("shift_suite.tasks.utils")

excel_date          = utils.excel_date
to_hhmm             = utils.to_hhmm
ingest_excel        = sys.modules["shift_suite.io_excel"].ingest_excel
build_heatmap       = sys.modules["shift_suite.heatmap"].build_heatmap
shortage_and_brief  = sys.modules["shift_suite.shortage"].shortage_and_brief
# ▼▼ 修正ポイント ▼▼
build_stats         = sys.modules["shift_suite.tasks.build_stats"].build_stats
# ▲▲ ここだけ変更 ▲▲
# 安全なモジュール参照（存在チェック付き）
try:
    detect_anomaly = sys.modules["shift_suite.anomaly"].detect_anomaly
except KeyError:
    detect_anomaly = None

try:
    train_fatigue = sys.modules["shift_suite.fatigue"].train_fatigue
except KeyError:
    train_fatigue = None

try:
    cluster_staff = sys.modules["shift_suite.cluster"].cluster_staff
except KeyError:
    cluster_staff = None

try:
    build_skill_matrix = sys.modules["shift_suite.skill_nmf"].build_skill_matrix
except KeyError:
    build_skill_matrix = None

try:
    run_fairness = sys.modules["shift_suite.fairness"].run_fairness
except KeyError:
    run_fairness = None

try:
    build_demand_series = sys.modules["shift_suite.forecast"].build_demand_series
    forecast_need = sys.modules["shift_suite.forecast"].forecast_need
except KeyError:
    build_demand_series = None
    forecast_need = None
# learn_roster function temporarily disabled due to import issues
# learn_roster        = sys.modules["shift_suite.rl"].learn_roster

# 旧 import 経路への互換 (任意)
sys.modules["shift_suite.build_stats"] = importlib.import_module("shift_suite.tasks.build_stats")
