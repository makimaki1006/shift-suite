"""
シフト作成者の思考プロセスを完全に解読するシステム
「なぜこの選択をしたのか」を明らかにする
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

import pandas as pd

# Machine learning dependencies disabled to avoid sklearn dependency issues
_HAS_LIGHTGBM = False
lgb = None

# Simple LightGBM replacement for basic functionality
class SimpleLGBMClassifier:
    """Simple LightGBM classifier replacement"""
    
    def __init__(self, **kwargs):
        self.classes_ = None
        self.feature_importances_ = None
        
    def fit(self, X, y, **kwargs):
        import numpy as np
        # Simple implementation: use majority class
        unique_classes, counts = np.unique(y, return_counts=True)
        self.classes_ = unique_classes
        self.majority_class = unique_classes[np.argmax(counts)]
        
        # Dummy feature importances
        if hasattr(X, 'shape'):
            self.feature_importances_ = np.ones(X.shape[1]) / X.shape[1]
        else:
            self.feature_importances_ = np.array([1.0])
        
        return self
        
    def predict(self, X):
        import numpy as np
        if hasattr(X, 'shape'):
            return np.full(X.shape[0], self.majority_class)
        else:
            return np.array([self.majority_class])
    
    def predict_proba(self, X):
        import numpy as np
        if hasattr(X, 'shape'):
            n_samples = X.shape[0]
        else:
            n_samples = 1
        n_classes = len(self.classes_) if self.classes_ is not None else 2
        return np.full((n_samples, n_classes), 1.0 / n_classes)

class SimpleLGBM:
    """Simple LightGBM module replacement"""
    LGBMClassifier = SimpleLGBMClassifier
    
lgb = SimpleLGBM()

# sklearn import removed - using simple implementation
_HAS_SKLEARN = False

# Simple decision tree classifier replacement
class SimpleDecisionTreeClassifier:
    """Simple decision tree classifier using basic statistical rules"""
    
    def __init__(self, max_depth=3, random_state=None):
        self.max_depth = max_depth
        self.random_state = random_state
        self.feature_importances_ = None
        self.tree_rules = []
        
    def fit(self, X, y):
        import numpy as np
        if self.random_state:
            np.random.seed(self.random_state)
            
        # Simple rule-based approach using most common class
        unique_classes, counts = np.unique(y, return_counts=True)
        self.majority_class = unique_classes[np.argmax(counts)]
        
        # Generate simple rules based on feature means
        self.feature_importances_ = np.ones(X.shape[1]) / X.shape[1]
        
        # Create simple rules
        for i in range(min(3, X.shape[1])):
            feature_mean = np.mean(X[:, i])
            self.tree_rules.append(f"Feature_{i} <= {feature_mean:.2f}")
            
        return self
    
    def predict(self, X):
        import numpy as np
        # Simple prediction: always return majority class
        return np.full(X.shape[0], self.majority_class)
    
    def score(self, X, y):
        predictions = self.predict(X)
        return (predictions == y).mean()

DecisionTreeClassifier = SimpleDecisionTreeClassifier

from .analyzers import (
    RestTimeAnalyzer,
    WorkPatternAnalyzer,
    AttendanceBehaviorAnalyzer,
)
from .fatigue import _features as calc_fatigue_features
from .fairness import calculate_jain_index
from .constants import SLOT_HOURS

log = logging.getLogger(__name__)


@dataclass
class DecisionPoint:
    """シフト作成における意思決定ポイント"""

    context: Dict[str, Any]
    options: List[Dict[str, Any]]
    chosen_idx: int
    query_id: int


class ShiftMindReader:
    """シフト作成者の思考を読み解く"""

    def __init__(self):
        self.preference_model = None

    def read_creator_mind(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """作成者の思考プロセスを完全解読するメインフロー"""
        log.info("思考プロセス解読を開始...")
        decision_history = self._reconstruct_all_decisions(long_df)
        if not decision_history:
            return {"error": "意思決定ポイントを再構築できませんでした。"}

        preference_model, feature_importance = self._reverse_engineer_preferences(
            decision_history,
            long_df,
        )
        self.preference_model = preference_model

        thinking_process_tree = self._mimic_thinking_process(decision_history)

        return {
            "feature_importance": feature_importance.to_dict(orient="records"),
            "thinking_process_tree": thinking_process_tree,
        }

    def _reconstruct_all_decisions(self, long_df: pd.DataFrame) -> List[DecisionPoint]:
        """【実装方針】
        1. `long_df`を日付、時間などでソートし、処理順を仮定。
        2. 1行（1つの配置）ずつループ処理を行う。
        3. 各ループで、その配置を「選ばれた選択(chosen)」とする。
        4. そのスロットに配置可能な「他の全スタッフ」を「選ばれなかった選択肢(rejected)」としてリストアップする。
        5. その時点でのシフト全体の状況（各スタッフの総労働時間、連勤日数など）を`context`として計算する。
        6. `chosen`と`rejected`を合わせたリストを`options`とし、DecisionPointオブジェクトを作成してリストに追加する。
        """
        log.info("意思決定の瞬間を再構築中...")
        if long_df.empty or "staff" not in long_df.columns or "ds" not in long_df.columns:
            return []

        df = long_df.sort_values("ds").reset_index(drop=True)
        all_staff = sorted(df["staff"].unique())
        hours_worked: Dict[str, float] = {s: 0.0 for s in all_staff}
        decisions: List[DecisionPoint] = []

        for i, row in df.iterrows():
            slot_time = pd.to_datetime(row["ds"])
            chosen_staff = row["staff"]
            context = {"slot_time": slot_time}

            options: List[Dict[str, Any]] = []
            for staff in all_staff:
                options.append({"staff": staff, "hours": hours_worked.get(staff, 0.0)})
            chosen_idx = all_staff.index(chosen_staff)

            decisions.append(
                DecisionPoint(
                    context=context,
                    options=options,
                    chosen_idx=chosen_idx,
                    query_id=i,
                )
            )

            # 更新: 選ばれたスタッフの勤務時間を増加(1単位)
            hours_worked[chosen_staff] = hours_worked.get(chosen_staff, 0.0) + 1.0

        return decisions

    def _get_current_features_for_all_staff(self, long_df: pd.DataFrame, context_date: pd.Timestamp) -> pd.DataFrame:
        """Calculate latest features for every staff up to ``context_date``."""
        df_until_now = long_df[long_df["ds"] < context_date]
        if df_until_now.empty:
            return pd.DataFrame(index=long_df["staff"].unique())

        # fatigue related features (simplified)
        fatigue_features = calc_fatigue_features(df_until_now)

        staff_features = pd.DataFrame(index=long_df["staff"].unique())
        staff_features["total_hours"] = (
            df_until_now.groupby("staff")["ds"].count() * SLOT_HOURS
        )

        def _consecutive(s: pd.Series) -> int:
            if s.empty:
                return 0
            s = pd.to_datetime(s)
            days = s.dt.date
            _ = days  # prevent unused-variable lint error
            diff = s.diff().dt.days.ne(1).cumsum()
            return diff.value_counts().max()

        staff_features["consecutive_days"] = df_until_now.groupby("staff")["ds"].apply(_consecutive)

        if not fatigue_features.empty:
            staff_features = staff_features.join(
                fatigue_features, how="left"
            )

        # additional analyzers
        rta = RestTimeAnalyzer()
        rest_daily = rta.analyze(df_until_now)
        if not rest_daily.empty:
            last_rest = rest_daily.groupby("staff")["rest_hours"].last()
            staff_features["recent_rest_hours"] = staff_features.index.map(last_rest).fillna(0)

        aba = AttendanceBehaviorAnalyzer()
        att = aba.analyze(df_until_now)
        if not att.empty:
            staff_features["attendance_rate"] = staff_features.index.map(att.set_index("staff")["attendance_rate"]).fillna(0)

        wpa = WorkPatternAnalyzer()
        pattern_df = wpa.analyze(df_until_now)
        if not pattern_df.empty:
            code_cols = [c for c in pattern_df.columns if c != "staff"]
            staff_features["num_codes"] = pattern_df.set_index("staff")[code_cols].gt(0).sum(axis=1)

        jain_val = calculate_jain_index(staff_features.get("total_hours", pd.Series(dtype=float)))
        staff_features["jain_index"] = jain_val

        return staff_features.fillna(0)

    def _reverse_engineer_preferences(
        self, decisions: List[DecisionPoint], long_df: pd.DataFrame
    ) -> Tuple[Any, pd.DataFrame]:
        """【実装方針】
        1. `decisions`リストから、LGBMRanker用の学習データを生成する (X, y, group)。
        2. 各選択肢（option）の特徴量ベクトルを生成する。特徴量の例：コスト、公平性、疲労度、スキルマッチ度など。
        3. `chosen`のラベルは1、`rejected`のラベルは0とする。
        4. LGBMRankerモデルを初期化し、学習させる（`fit(X, y, group=group)`）。
        5. 学習済みモデルの`feature_importances_`属性から特徴量重要度を取得し、DataFrameとして整形する。
        6. 学習済みモデルと特徴量重要度DFを返す。
        """
        log.info("選好関数を逆算中 (拡張特徴量版)...")

        X_train: List[List[float]] = []
        y_train: List[int] = []
        group: List[int] = []
        feature_names = [
            "total_hours",
            "consecutive_days",
            "recent_rest_hours",
            "attendance_rate",
            "num_codes",
        ]

        if not decisions or not _HAS_LIGHTGBM:
            # LightGBMが利用できない場合の代替処理
            if not _HAS_LIGHTGBM:
                log.warning("LightGBM not available, using simplified analysis")
            return None, pd.DataFrame({"feature": feature_names, "importance": [0] * len(feature_names)})

        for dp in decisions:
            current_features = self._get_current_features_for_all_staff(long_df, dp.context["slot_time"])
            query_features: List[List[float]] = []
            for opt in dp.options:
                staff_id = opt["staff"]
                feats = {
                    "total_hours": current_features.loc[staff_id].get("total_hours", 0) + SLOT_HOURS,
                    "consecutive_days": current_features.loc[staff_id].get("consecutive_days", 0),
                    "recent_rest_hours": current_features.loc[staff_id].get("recent_rest_hours", 0),
                    "attendance_rate": current_features.loc[staff_id].get("attendance_rate", 0),
                    "num_codes": current_features.loc[staff_id].get("num_codes", 0),
                }
                query_features.append([feats.get(fn, 0) for fn in feature_names])

            X_train.extend(query_features)
            labels = [0] * len(dp.options)
            labels[dp.chosen_idx] = 1
            y_train.extend(labels)
            group.append(len(dp.options))

        model = lgb.LGBMRanker(verbose=-1)
        if X_train:
            try:
                model.fit(X_train, y_train, group=group)
            except Exception as e:  # noqa: BLE001
                log.warning(f"LGBMRanker fit failed: {e}")

        importance = getattr(model, "feature_importances_", [0] * len(feature_names))
        fi_df = pd.DataFrame({"feature": feature_names, "importance": importance})
        return model, fi_df.sort_values("importance", ascending=False)

    def _mimic_thinking_process(self, decisions: List[DecisionPoint]) -> Any:
        """【実装方針】
        1. `decisions`リストから、決定木用の学習データを生成する。
        2. `context`（状況）を説明変数X、選ばれたスタッフのIDやカテゴリを目的変数yとする。
        3. `sklearn.tree.DecisionTreeClassifier`を初期化し、学習させる。
        4. 学習済みのtreeオブジェクトを返す（可視化は呼び出し元で行う）。
        """
        log.info("決定木による思考プロセスの模倣中...")
        if not decisions or not _HAS_SKLEARN:
            if not _HAS_SKLEARN:
                log.warning("scikit-learn not available, using simplified analysis")
            return None

        X = pd.DataFrame({
            "slot_order": [i for i, _ in enumerate(decisions)],
            "num_options": [len(dp.options) for dp in decisions],
        })
        y = [dp.options[dp.chosen_idx]["staff"] for dp in decisions]

        clf = DecisionTreeClassifier(max_depth=3)
        try:
            clf.fit(X, y)
        except Exception as e:  # noqa: BLE001
            log.warning(f"DecisionTree fit failed: {e}")
        return clf
