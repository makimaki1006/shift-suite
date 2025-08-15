"""Shift assignment using OR-Tools CP-SAT."""

from __future__ import annotations

import os
from typing import Dict

import pandas as pd

try:
    from ortools.sat.python import cp_model
    _HAS_ORTOOLS = True
except ImportError:  # pragma: no cover - optional dependency
    cp_model = None  # type: ignore
    _HAS_ORTOOLS = False

from .utils import log


def _validate_schedule_inputs(
    roster_df: pd.DataFrame,
    staff_df: pd.DataFrame,
    leave_df: pd.DataFrame,
) -> bool:
    """Return ``True`` if all required columns exist and data is non-empty."""

    missing_roster = {"date", "required_personnel"} - set(roster_df.columns)
    missing_staff = {"name", "wage"} - set(staff_df.columns)
    missing_leave = {"staff_id", "date"} - set(leave_df.columns)

    if missing_roster or missing_staff or missing_leave:
        log.error(
            "Invalid input columns - roster: %s staff: %s leave: %s",
            missing_roster,
            missing_staff,
            missing_leave,
        )
        return False

    if roster_df.empty or staff_df.empty:
        log.error("roster_df and staff_df cannot be empty")
        return False

    return True


if _HAS_ORTOOLS and cp_model is not None:
    class ShiftSolutionPrinter(cp_model.CpSolverSolutionCallback):  # type: ignore
        """Print intermediate solutions during search."""

        def __init__(self, variables, staff_ids, dates, limit: int) -> None:
            super().__init__()
            self._variables = variables
            self._staff_ids = staff_ids
            self._dates = dates
            self._solution_count = 0
            self._limit = limit

        def on_solution_callback(self) -> None:
            self._solution_count += 1
            log.info(
                "Solution %d found with objective %.2f",
                self._solution_count,
                self.ObjectiveValue(),
            )
            if self._solution_count >= self._limit:
                log.info("Stopping search after %d solutions", self._limit)
                self.StopSearch()

        def solution_count(self) -> int:
            return self._solution_count
else:
    # cp_model が利用できない場合のダミークラス
    class ShiftSolutionPrinter:
        def __init__(self, *args, **kwargs):
            pass
        def solution_count(self):
            return 0


def generate_optimal_schedule(
    roster_df: pd.DataFrame,
    staff_df: pd.DataFrame,
    leave_df: pd.DataFrame,
    config: Dict,
) -> pd.DataFrame:
    """Generate an optimal shift schedule.

    Parameters
    ----------
    roster_df:
        DataFrame with columns ``date`` and ``required_personnel``.
    staff_df:
        DataFrame indexed by ``staff_id`` with at least columns ``name`` and ``wage``.
    leave_df:
        DataFrame with columns ``staff_id`` and ``date`` listing leave days.
    config:
        Dictionary of solver options. Keys include ``time_limit_phase1``,
        ``time_limit_phase2``, ``max_consecutive_work_days`` and ``window_for_off_days``.

    Returns
    -------
    pd.DataFrame
        Schedule with columns ``date``, ``staff_id`` and ``name``. Empty when no
        solution is found or OR-Tools is unavailable.
    """
    if not _HAS_ORTOOLS or cp_model is None:
        log.warning("ortools is not installed; assignment cannot run")
        return pd.DataFrame()

    if not _validate_schedule_inputs(roster_df, staff_df, leave_df):
        return pd.DataFrame()

    staff_ids = staff_df.index.tolist()
    dates = pd.to_datetime(roster_df["date"]).dt.date.tolist()
    num_days = len(dates)

    required_personnel = dict(zip(dates, roster_df["required_personnel"], strict=True))
    wages = dict(zip(staff_ids, staff_df["wage"], strict=True))

    leave_set = set(
        (row["staff_id"], pd.to_datetime(row["date"]).date())
        for _, row in leave_df.iterrows()
    )

    model = cp_model.CpModel()
    x = {
        (s_id, d): model.NewBoolVar(f"x_{s_id}_{d}")
        for s_id in staff_ids
        for d in dates
    }

    for d in dates:
        model.Add(sum(x[(s_id, d)] for s_id in staff_ids) == required_personnel[d])

    for s_id, d in leave_set:
        if d in dates:
            model.Add(x[(s_id, d)] == 0)

    max_consecutive_days = config.get("max_consecutive_work_days", 5)
    for s_id in staff_ids:
        for i in range(num_days - max_consecutive_days):
            window = [dates[i + j] for j in range(max_consecutive_days + 1)]
            model.Add(sum(x[(s_id, d)] for d in window) <= max_consecutive_days)

    window_size = config.get("window_for_off_days", 7)
    for s_id in staff_ids:
        for i in range(num_days - window_size + 1):
            window = [dates[i + j] for j in range(window_size)]
            model.Add(sum(x[(s_id, d)] for d in window) < window_size)

    total_cost_var = model.NewIntVar(0, sum(wages.values()) * num_days, "total_cost")
    model.Add(
        total_cost_var
        == sum(x[(s_id, d)] * wages[s_id] for s_id in staff_ids for d in dates)
    )
    model.Minimize(total_cost_var)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.get("time_limit_phase1", 60)
    solver.parameters.num_search_workers = os.cpu_count() or 1

    status1 = solver.Solve(model)
    if status1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        log.error("Phase 1 failed to find a solution")
        return pd.DataFrame()

    optimal_cost = solver.Value(total_cost_var)
    log.info("Phase 1 optimal cost: %s", optimal_cost)

    model.Add(total_cost_var == optimal_cost)

    workload_vars = {
        s_id: model.NewIntVar(0, num_days, f"workload_{s_id}") for s_id in staff_ids
    }
    for s_id in staff_ids:
        model.Add(workload_vars[s_id] == sum(x[(s_id, d)] for d in dates))

    max_workload = model.NewIntVar(0, num_days, "max_workload")
    min_workload = model.NewIntVar(0, num_days, "min_workload")
    model.AddMaxEquality(max_workload, list(workload_vars.values()))
    model.AddMinEquality(min_workload, list(workload_vars.values()))
    fairness_diff = model.NewIntVar(0, num_days, "fairness_diff")
    model.Add(fairness_diff == max_workload - min_workload)
    model.Minimize(fairness_diff)

    solver.parameters.max_time_in_seconds = config.get("time_limit_phase2", 60)

    status2 = solver.Solve(model)
    if status2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        log.error("Phase 2 failed to find a fair solution")
        return pd.DataFrame()

    schedule_data = []
    for d in dates:
        for s_id in staff_ids:
            if solver.Value(x[(s_id, d)]):
                schedule_data.append(
                    {"date": d, "staff_id": s_id, "name": staff_df.loc[s_id, "name"]}
                )

    return pd.DataFrame(schedule_data)
