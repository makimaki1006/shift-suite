"""Utility access to task analyzers with lazy imports."""

from importlib import import_module

__all__ = [
    "LeaveAnalyzer",
    "RestTimeAnalyzer",
    "WorkPatternAnalyzer",
    "AttendanceBehaviorAnalyzer",
    "CombinedScoreCalculator",
    "LowStaffLoadAnalyzer",
    "ShortageFactorAnalyzer",
]

_module_map = {
    "AttendanceBehaviorAnalyzer": "shift_suite.tasks.analyzers.attendance_behavior",
    "CombinedScoreCalculator": "shift_suite.tasks.analyzers.combined_score",
    "LeaveAnalyzer": "shift_suite.tasks.analyzers.leave",
    "LowStaffLoadAnalyzer": "shift_suite.tasks.analyzers.low_staff_load",
    "RestTimeAnalyzer": "shift_suite.tasks.analyzers.rest_time",
    "WorkPatternAnalyzer": "shift_suite.tasks.analyzers.work_pattern",
    "ShortageFactorAnalyzer": "shift_suite.tasks.shortage_factor_analyzer",
}


def __getattr__(name: str):
    if name in _module_map:
        module = import_module(_module_map[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")
