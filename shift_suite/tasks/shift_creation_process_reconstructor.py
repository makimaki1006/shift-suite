"""
シフト作成プロセスを時系列で再現し、各ステップでの意思決定を分析するエンジン
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import datetime as dt

import pandas as pd
import numpy as np
import lightgbm as lgb

log = logging.getLogger(__name__)


@dataclass
class CreationState:
    """シフト作成の特定時点での状態"""

    timestamp: pd.Timestamp
    assigned_slots: Dict[str, List[pd.Timestamp]] = field(default_factory=dict)
    staff_hours: Dict[str, float] = field(default_factory=dict)
    consecutive_days: Dict[str, int] = field(default_factory=dict)
    last_work_date: Dict[str, Optional[dt.date]] = field(default_factory=dict)
    role_coverage: Dict[Tuple[pd.Timestamp, str], int] = field(default_factory=dict)
    # --- ▼▼▼ 改善点①: 状態の充実 ▼▼▼ ---
    co_occurrence_matrix: Dict[Tuple[str, str], int] = field(
        default_factory=lambda: defaultdict(int)
    )
    staff_skills: Dict[str, Set[str]] = field(default_factory=dict)
    leave_requests: Dict[dt.date, Set[str]] = field(default_factory=dict)
    # --- ▲▲▲ 改善点①ここまで ▲▲▲ ---

    def copy(self) -> "CreationState":
        """状態の深いコピーを作成"""

        return CreationState(
            timestamp=self.timestamp,
            assigned_slots={k: list(v) for k, v in self.assigned_slots.items()},
            staff_hours=dict(self.staff_hours),
            consecutive_days=dict(self.consecutive_days),
            last_work_date=dict(self.last_work_date),
            role_coverage=dict(self.role_coverage),
            co_occurrence_matrix=self.co_occurrence_matrix.copy(),
            staff_skills={k: set(v) for k, v in self.staff_skills.items()},
            leave_requests={k: set(v) for k, v in self.leave_requests.items()},
        )


@dataclass
class DecisionPoint:
    """シフト作成における一つの意思決定ポイント"""

    slot_time: pd.Timestamp
    role: str
    available_staff: List[str]
    chosen_staff: str
    state_before: CreationState
    decision_factors: Dict[str, float]
    confidence: float


class ShiftCreationProcessReconstructor:
    """シフト作成プロセスを段階的に再現し、各決定の理由を推定"""

    def __init__(self) -> None:
        self.decision_history: List[DecisionPoint] = []
        self.preference_model = None

    def reconstruct_creation_process(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """シフト作成プロセスを時系列で再現"""

        log.info("シフト作成プロセスの再現を開始...")

        df = long_df[long_df.get("parsed_slots_count", 0) > 0].copy()
        df = df.sort_values(["ds", "role", "staff"])

        all_staff = sorted(df["staff"].unique())

        initial_state = CreationState(
            timestamp=df["ds"].min(),
            # --- ▼▼▼ 改善点④: 初期化処理の追加 ▼▼▼ ---
            staff_skills=self._initialize_staff_skills(long_df),
            leave_requests=self._initialize_leave_requests(long_df),
            # --- ▲▲▲ 改善点④ここまで ▲▲▲ ---
        )

        grouped = df.groupby(["ds", "role"])
        current_state = initial_state.copy()

        for (slot_time, role), group in grouped:
            assigned_staff_in_group = group["staff"].tolist()

            # --- ▼▼▼ 改善点②: 利用可能スタッフ推定ロジックの強化 ▼▼▼ ---
            available_staff = self._estimate_available_staff(
                slot_time, role, all_staff, current_state
            )
            # --- ▲▲▲ 改善点②ここまで ▲▲▲ ---

            for staff in assigned_staff_in_group:
                if staff not in available_staff:
                    log.warning(
                        f"配置されたスタッフ'{staff}'が利用可能リストに含まれていませんでした。@ {slot_time}, {role}"
                    )
                    available_staff.append(staff)

            for staff in assigned_staff_in_group:
                # --- ▼▼▼ 改善点③: 意思決定要因の高度化 ▼▼▼ ---
                decision_factors = self._analyze_decision_factors(
                    staff, slot_time, role, current_state, available_staff
                )
                # --- ▲▲▲ 改善点③ここまで ▲▲▲ ---

                confidence = self._calculate_decision_confidence(
                    staff, available_staff, decision_factors
                )

                decision = DecisionPoint(
                    slot_time=slot_time,
                    role=role,
                    available_staff=available_staff,
                    chosen_staff=staff,
                    state_before=current_state.copy(),
                    decision_factors=decision_factors,
                    confidence=confidence,
                )

                self.decision_history.append(decision)

                current_state = self._update_state(current_state, staff, slot_time, role)

        patterns = self._learn_decision_patterns()

        process_insights = self._extract_process_insights()

        return {
            "decision_count": len(self.decision_history),
            "decision_patterns": patterns,
            "process_insights": process_insights,
            "timeline": self._create_timeline_summary(),
        }

    def _initialize_staff_skills(self, long_df: pd.DataFrame) -> Dict[str, Set[str]]:
        """スタッフのスキル（担当役割）を初期化"""

        skills: Dict[str, Set[str]] = defaultdict(set)
        for _, row in long_df.iterrows():
            skills[row["staff"].strip()].add(row["role"].strip())
        return skills

    def _initialize_leave_requests(self, long_df: pd.DataFrame) -> Dict[dt.date, Set[str]]:
        """休暇申請情報を初期化"""

        requests: Dict[dt.date, Set[str]] = defaultdict(set)
        leave_df = long_df[long_df["holiday_type"].isin(["希望休", "有給"])]
        for _, row in leave_df.iterrows():
            requests[row["ds"].date()].add(row["staff"].strip())
        return requests

    def _estimate_available_staff(
        self,
        slot_time: pd.Timestamp,
        role: str,
        all_staff: List[str],
        state: CreationState,
    ) -> List[str]:
        """特定のスロットで利用可能だったスタッフを推定"""

        available: List[str] = []

        for staff in all_staff:
            if staff in state.assigned_slots and slot_time in state.assigned_slots.get(staff, []):
                continue

            # --- ▼▼▼ 改善点②: 利用可能スタッフ推定ロジックの強化 ▼▼▼ ---
            if staff in state.leave_requests.get(slot_time.date(), set()):
                continue

            if role not in state.staff_skills.get(staff, set()):
                continue
            # --- ▲▲▲ 改善点②ここまで ▲▲▲ ---

            if state.consecutive_days.get(staff, 0) >= 5:
                if state.last_work_date.get(staff) == slot_time.date() - pd.Timedelta(days=1):
                    continue

            daily_hours = self._get_daily_hours(staff, slot_time.date(), state)
            if daily_hours >= 8:
                continue

            available.append(staff)

        return available

    def _analyze_decision_factors(
        self,
        staff: str,
        slot_time: pd.Timestamp,
        role: str,
        state: CreationState,
        available_staff: List[str],
    ) -> Dict[str, float]:
        """意思決定に影響した要因を分析"""

        factors: Dict[str, float] = {}

        avg_hours = (
            np.mean([state.staff_hours.get(s, 0) for s in available_staff]) if available_staff else 0
        )
        staff_hours = state.staff_hours.get(staff, 0)
        factors["fairness_score"] = 1.0 - abs(staff_hours - avg_hours) / (avg_hours + 1)

        prev_slot = slot_time - pd.Timedelta(minutes=30)
        if prev_slot in state.assigned_slots.get(staff, []):
            factors["continuity_score"] = 0.8
        else:
            factors["continuity_score"] = 0.2

        factors["skill_match_score"] = self._calculate_skill_match(staff, role, state)

        # --- ▼▼▼ 改善点③: 意思決定要因の高度化 ▼▼▼ ---
        factors["synergy_score"] = self._calculate_team_synergy(staff, slot_time, state)
        # --- ▲▲▲ 改善点③ここまで ▲▲▲ ---

        factors["fatigue_score"] = self._calculate_fatigue_score(staff, state)

        return factors

    def _calculate_team_synergy(self, staff: str, slot_time: pd.Timestamp, state: CreationState) -> float:
        """チームシナジーを評価"""

        concurrent_staff = [
            other_staff
            for other_staff, slots in state.assigned_slots.items()
            if slot_time in slots and other_staff != staff
        ]

        if not concurrent_staff:
            return 0.5

        synergy_scores: List[int] = []
        for other in concurrent_staff:
            pair = tuple(sorted((staff, other)))
            synergy_scores.append(state.co_occurrence_matrix.get(pair, 0))

        max_co_occurrence = max(state.co_occurrence_matrix.values()) if state.co_occurrence_matrix else 1
        return np.mean(synergy_scores) / max_co_occurrence if max_co_occurrence > 0 else 0.5

    def _update_state(
        self, state: CreationState, staff: str, slot_time: pd.Timestamp, role: str
    ) -> CreationState:
        """配置決定後の状態を更新"""

        new_state = state.copy()

        if staff not in new_state.assigned_slots:
            new_state.assigned_slots[staff] = []
        new_state.assigned_slots[staff].append(slot_time)

        new_state.staff_hours[staff] = new_state.staff_hours.get(staff, 0) + 0.5

        current_date = slot_time.date()
        last_date = new_state.last_work_date.get(staff)

        if last_date is None:
            new_state.consecutive_days[staff] = 1
        elif (current_date - last_date).days == 1:
            new_state.consecutive_days[staff] = new_state.consecutive_days.get(staff, 0) + 1
        elif (current_date - last_date).days > 1:
            new_state.consecutive_days[staff] = 1
        new_state.last_work_date[staff] = current_date

        # --- ▼▼▼ 改善点①: 状態の充実 ▼▼▼ ---
        concurrent_staff = [
            other for other, slots in new_state.assigned_slots.items() if slot_time in slots and other != staff
        ]
        for other in concurrent_staff:
            pair = tuple(sorted((staff, other)))
            new_state.co_occurrence_matrix[pair] += 1
        # --- ▲▲▲ 改善点①ここまで ▲▲▲ ---

        new_state.timestamp = slot_time
        return new_state

    def _calculate_skill_match(self, staff: str, role: str, state: CreationState) -> float:
        """スタッフと役割のマッチ度を計算"""

        return 1.0 if role in state.staff_skills.get(staff, set()) else 0.1

    def _calculate_fatigue_score(self, staff: str, state: CreationState) -> float:
        """疲労度を計算（低いほど良い）"""

        consecutive = state.consecutive_days.get(staff, 0)
        fatigue = (consecutive / 7.0) * 0.7
        return 1.0 - min(fatigue, 1.0)

    def _calculate_decision_confidence(
        self, chosen_staff: str, available_staff: List[str], decision_factors: Dict[str, float]
    ) -> float:
        """決定の確信度を計算"""

        if len(available_staff) <= 1:
            return 1.0

        avg_score = np.mean(list(decision_factors.values()))
        choice_penalty = 1.0 - (len(available_staff) - 1) / 20
        return avg_score * max(choice_penalty, 0.5)

    def _get_daily_hours(self, staff: str, date: dt.date, state: CreationState) -> float:
        if staff not in state.assigned_slots:
            return 0.0
        daily_slots = [s for s in state.assigned_slots[staff] if s.date() == date]
        return len(daily_slots) * 0.5

    def _learn_decision_patterns(self) -> Dict[str, Any]:
        """決定履歴から作成者の選好パターンを学習"""

        if not self.decision_history:
            return {}

        X: List[List[float]] = []
        y: List[int] = []
        groups: List[int] = []

        feature_names = [
            "total_hours",
            "consecutive_days",
            "hour",
            "dayofweek",
            "fairness_score",
            "continuity_score",
            "skill_match_score",
            "synergy_score",
            "fatigue_score",
        ]

        for decision in self.decision_history:
            group_size = 0
            for staff in decision.available_staff:
                state_before = decision.state_before
                features = {
                    "total_hours": state_before.staff_hours.get(staff, 0),
                    "consecutive_days": state_before.consecutive_days.get(staff, 0),
                    "hour": decision.slot_time.hour,
                    "dayofweek": decision.slot_time.dayofweek,
                }

                estimated_factors = self._analyze_decision_factors(
                    staff,
                    decision.slot_time,
                    decision.role,
                    state_before,
                    decision.available_staff,
                )
                features.update(estimated_factors)

                X.append([features.get(fn, 0) for fn in feature_names])
                y.append(1 if staff == decision.chosen_staff else 0)
                group_size += 1
            groups.append(group_size)

        if X and y:
            try:
                self.preference_model = lgb.LGBMRanker(
                    objective="lambdarank",
                    metric="ndcg",
                    n_estimators=100,
                    num_leaves=31,
                    verbose=-1,
                )
                self.preference_model.fit(X, y, group=groups)

                importance = (
                    pd.DataFrame(
                        {"feature": feature_names, "importance": self.preference_model.feature_importances_}
                    )
                    .sort_values("importance", ascending=False)
                )

                return {
                    "model_trained": True,
                    "feature_importance": importance.to_dict("records"),
                    "top_factors": importance.head(3)["feature"].tolist(),
                }
            except Exception as e:  # pragma: no cover - rarely triggered
                log.error(f"選好モデルの学習に失敗: {e}")
                return {"model_trained": False, "error": str(e)}

        return {"model_trained": False, "error": "No training data"}

    def _extract_process_insights(self) -> Dict[str, Any]:
        """作成プロセスから洞察を抽出"""

        if not self.decision_history:
            return {}

        insights = {
            "total_decisions": len(self.decision_history),
            "average_confidence": np.mean([d.confidence for d in self.decision_history]),
            "decision_factors_stats": {},
            "critical_decisions": [],
        }

        factor_values: Dict[str, List[float]] = defaultdict(list)
        for d in self.decision_history:
            for factor, value in d.decision_factors.items():
                factor_values[factor].append(value)

        for factor, values in factor_values.items():
            insights["decision_factors_stats"][factor] = {
                "mean": np.mean(values),
                "std": np.std(values),
            }

        sorted_decisions = sorted(self.decision_history, key=lambda d: d.confidence)
        for d in sorted_decisions[:5]:
            insights["critical_decisions"].append(
                {
                    "time": d.slot_time.strftime("%Y-%m-%d %H:%M"),
                    "role": d.role,
                    "chosen": d.chosen_staff,
                    "alternatives": len(d.available_staff),
                    "confidence": f"{d.confidence:.2f}",
                    "main_factor": max(d.decision_factors, key=d.decision_factors.get),
                }
            )

        return insights

    def _create_timeline_summary(self) -> List[Dict[str, Any]]:
        """作成プロセスのタイムライン要約を作成"""

        timeline: List[Dict[str, Any]] = []
        hourly_groups: Dict[pd.Timestamp, List[DecisionPoint]] = defaultdict(list)
        for d in self.decision_history:
            hourly_groups[d.slot_time.floor("H")].append(d)

        for hour, decisions in sorted(hourly_groups.items()):
            timeline.append(
                {
                    "timestamp": hour.strftime("%Y-%m-%d %H:%M"),
                    "decision_count": len(decisions),
                    "avg_confidence": np.mean([d.confidence for d in decisions]),
                    "staff_involved": len(set(d.chosen_staff for d in decisions)),
                }
            )

        return timeline

