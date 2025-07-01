"""Reconstruct shift creation process and infer implicit rules."""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class CreationState:
    """State of schedule at a given time."""

    timestamp: pd.Timestamp
    assigned_slots: Dict[str, List[pd.Timestamp]] = field(default_factory=dict)
    staff_hours: Dict[str, float] = field(default_factory=dict)
    consecutive_days: Dict[str, int] = field(default_factory=dict)
    last_work_date: Dict[str, dt.date] = field(default_factory=dict)
    role_coverage: Dict[Tuple[pd.Timestamp, str], int] = field(default_factory=dict)

    def copy(self) -> "CreationState":
        return CreationState(
            timestamp=self.timestamp,
            assigned_slots={k: list(v) for k, v in self.assigned_slots.items()},
            staff_hours=dict(self.staff_hours),
            consecutive_days=dict(self.consecutive_days),
            last_work_date=dict(self.last_work_date),
            role_coverage=dict(self.role_coverage),
        )


@dataclass
class DecisionPoint:
    """One decision during creation."""

    slot_time: pd.Timestamp
    role: str
    available_staff: List[str]
    chosen_staff: str
    state_before: CreationState
    decision_factors: Dict[str, float]
    confidence: float


class ShiftCreationProcessReconstructor:
    """Reconstruct creation process from schedule data."""

    def __init__(self) -> None:
        self.decision_history: List[DecisionPoint] = []

    # public API -----------------------------------------------------------
    def reconstruct_creation_process(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """Reconstruct process from a long dataframe."""
        if long_df.empty:
            return {}

        df = long_df[long_df.get("parsed_slots_count", 0) > 0].sort_values(["ds", "role", "staff"])

        current_state = CreationState(timestamp=df["ds"].min())
        all_staff = sorted(df["staff"].unique())

        grouped = df.groupby(["ds", "role"])
        for (slot_time, role), group in grouped:
            assigned = group["staff"].tolist()
            available = self._estimate_available_staff(slot_time, all_staff, current_state)
            for staff in assigned:
                factors = self._analyze_decision_factors(staff, slot_time, current_state, available)
                conf = self._calculate_decision_confidence(available, factors)
                decision = DecisionPoint(
                    slot_time=slot_time,
                    role=role,
                    available_staff=available,
                    chosen_staff=staff,
                    state_before=current_state.copy(),
                    decision_factors=factors,
                    confidence=conf,
                )
                self.decision_history.append(decision)
                current_state = self._update_state(current_state, staff, slot_time, role)

        return {
            "decision_count": len(self.decision_history),
            "timeline": self._create_timeline_summary(),
        }

    # internal helpers -----------------------------------------------------
    def _estimate_available_staff(
        self, slot_time: pd.Timestamp, all_staff: List[str], state: CreationState
    ) -> List[str]:
        available = []
        for staff in all_staff:
            if slot_time in state.assigned_slots.get(staff, []):
                continue
            daily_hours = self._get_daily_hours(staff, slot_time.date(), state)
            if daily_hours >= 8:
                continue
            consecutive = state.consecutive_days.get(staff, 0)
            if consecutive >= 5 and state.last_work_date.get(staff) == slot_time.date() - pd.Timedelta(days=1):
                continue
            available.append(staff)
        return available

    def _analyze_decision_factors(
        self,
        staff: str,
        slot_time: pd.Timestamp,
        state: CreationState,
        available_staff: List[str],
    ) -> Dict[str, float]:
        avg_hours = np.mean([state.staff_hours.get(s, 0) for s in available_staff]) if available_staff else 0
        fairness = 1.0 - abs(state.staff_hours.get(staff, 0) - avg_hours) / (avg_hours + 1)
        prev_slot = slot_time - pd.Timedelta(minutes=30)
        cont = 0.8 if prev_slot in state.assigned_slots.get(staff, []) else 0.2
        return {
            "fairness_score": fairness,
            "continuity_score": cont,
        }

    def _calculate_decision_confidence(self, available_staff: List[str], factors: Dict[str, float]) -> float:
        if len(available_staff) <= 1:
            return 1.0
        return float(np.mean(list(factors.values())))

    def _update_state(
        self, state: CreationState, staff: str, slot_time: pd.Timestamp, role: str
    ) -> CreationState:
        new_state = state.copy()
        new_state.assigned_slots.setdefault(staff, []).append(slot_time)
        new_state.staff_hours[staff] = new_state.staff_hours.get(staff, 0) + 0.5
        date = slot_time.date()
        last_date = new_state.last_work_date.get(staff)
        if last_date and (date - last_date).days == 1:
            new_state.consecutive_days[staff] = new_state.consecutive_days.get(staff, 0) + 1
        else:
            new_state.consecutive_days[staff] = 1
        new_state.last_work_date[staff] = date
        new_state.role_coverage[(slot_time, role)] = new_state.role_coverage.get((slot_time, role), 0) + 1
        new_state.timestamp = slot_time
        return new_state

    def _get_daily_hours(self, staff: str, date: dt.date, state: CreationState) -> float:
        slots = [s for s in state.assigned_slots.get(staff, []) if s.date() == date]
        return len(slots) * 0.5

    def _create_timeline_summary(self) -> List[Dict[str, Any]]:
        timeline: Dict[pd.Timestamp, List[DecisionPoint]] = {}
        for d in self.decision_history:
            hour = d.slot_time.floor("H")
            timeline.setdefault(hour, []).append(d)
        summary = []
        for hour, items in sorted(timeline.items()):
            summary.append(
                {
                    "timestamp": hour.strftime("%Y-%m-%d %H:%M"),
                    "decision_count": len(items),
                    "staff_involved": len({i.chosen_staff for i in items}),
                }
            )
        return summary


class ImplicitRuleDiscoverer:
    """Simple discovery of implicit rules from history."""

    def discover_implicit_rules(
        self, long_df: pd.DataFrame, decisions: List[DecisionPoint]
    ) -> Dict[str, Any]:
        if long_df.empty or not decisions:
            return {}
        weekday_pref: Dict[int, Dict[str, int]] = {}
        for d in decisions:
            wd = d.slot_time.dayofweek
            weekday_pref.setdefault(wd, {})[d.chosen_staff] = weekday_pref.get(wd, {}).get(d.chosen_staff, 0) + 1
        rules = []
        for wd, counts in weekday_pref.items():
            total = sum(counts.values())
            for staff, cnt in counts.items():
                if total > 0 and cnt / total > 0.5:
                    rules.append({"weekday": wd, "staff": staff, "ratio": cnt / total})
        return {"weekday_preferences": rules}
