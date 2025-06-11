"""
shift_suite 初期化
  * shift_suite.tasks 内の *.py を全部 lazy import
  * 旧来の `shift_suite.heatmap` などの名前もそのまま生かす
"""

import pkgutil
import sys
from importlib import import_module
from pathlib import Path

# Configure package-wide logging
from .logger_config import configure_logging

configure_logging()

# ────────────────────────────────────────────── lazy task import setup
_tasks_dir = Path(__file__).with_name("tasks")
_task_names = {m.name for m in pkgutil.iter_modules([str(_tasks_dir)])}


def __getattr__(name: str):
    """Lazily import modules from ``shift_suite.tasks``."""
    if name in _task_names:
        module = import_module(f"shift_suite.tasks.{name}")
        sys.modules[f"shift_suite.{name}"] = module
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__} has no attribute {name}")


# ────────────────────────────────────────────── util & 主要関数 re-export
utils = import_module("shift_suite.tasks.utils")

excel_date = utils.excel_date
to_hhmm = utils.to_hhmm
save_df_xlsx = utils.save_df_xlsx


def _lazy_func(module: str, func: str):
    def wrapper(*args, **kwargs):
        mod = import_module(module)
        return getattr(mod, func)(*args, **kwargs)

    return wrapper


ingest_excel = _lazy_func("shift_suite.tasks.io_excel", "ingest_excel")
build_heatmap = _lazy_func("shift_suite.tasks.heatmap", "build_heatmap")
shortage_and_brief = _lazy_func("shift_suite.tasks.shortage", "shortage_and_brief")
merge_shortage_leave = _lazy_func("shift_suite.tasks.shortage", "merge_shortage_leave")
build_stats = _lazy_func("shift_suite.tasks.build_stats", "build_stats")
detect_anomaly = _lazy_func("shift_suite.tasks.anomaly", "detect_anomaly")
train_fatigue = _lazy_func("shift_suite.tasks.fatigue", "train_fatigue")
cluster_staff = _lazy_func("shift_suite.tasks.cluster", "cluster_staff")
build_skill_matrix = _lazy_func("shift_suite.tasks.skill_nmf", "build_skill_matrix")
run_fairness = _lazy_func("shift_suite.tasks.fairness", "run_fairness")
build_demand_series = _lazy_func("shift_suite.tasks.forecast", "build_demand_series")
forecast_need = _lazy_func("shift_suite.tasks.forecast", "forecast_need")
learn_roster = _lazy_func("shift_suite.tasks.rl", "learn_roster")
build_staff_stats = _lazy_func("shift_suite.tasks.summary", "build_staff_stats")
weekday_timeslot_summary = _lazy_func(
    "shift_suite.tasks.shortage", "weekday_timeslot_summary"
)
monthperiod_timeslot_summary = _lazy_func(
    "shift_suite.tasks.shortage", "monthperiod_timeslot_summary"
)
calculate_daily_cost = _lazy_func(
    "shift_suite.tasks.daily_cost",
    "calculate_daily_cost",
)
create_optimal_hire_plan = _lazy_func(
    "shift_suite.tasks.optimal_hire_plan",
    "create_optimal_hire_plan",
)

sys.modules["shift_suite.build_stats"] = import_module("shift_suite.tasks.build_stats")

__all__ = [
    "excel_date",
    "to_hhmm",
    "save_df_xlsx",
    "ingest_excel",
    "build_heatmap",
    "shortage_and_brief",
    "merge_shortage_leave",
    "build_stats",
    "detect_anomaly",
    "train_fatigue",
    "cluster_staff",
    "build_skill_matrix",
    "run_fairness",
    "build_demand_series",
    "forecast_need",
    "learn_roster",
    "build_staff_stats",
    "weekday_timeslot_summary",
    "monthperiod_timeslot_summary",
    "calculate_daily_cost",
    "create_optimal_hire_plan",
]
