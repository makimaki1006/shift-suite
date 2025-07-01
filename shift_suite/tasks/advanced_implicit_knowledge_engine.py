"""Discover deeper implicit knowledge from schedule data."""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List

import networkx as nx
import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class ImplicitKnowledge:
    """Representation of discovered implicit knowledge."""

    category: str
    description: str
    strength: float
    evidence: Dict[str, Any]
    actionable_advice: str
    complexity: int


class AdvancedImplicitKnowledgeEngine:
    """Engine combining several analyses."""

    def __init__(self) -> None:
        self.discovered_knowledge: List[ImplicitKnowledge] = []

    def discover_all_implicit_knowledge(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        if long_df.empty:
            return {"discovered_knowledge": [], "knowledge_count": 0}

        knowledge = []
        knowledge.extend(self._discover_temporal_patterns(long_df))
        knowledge.extend(self._discover_social_dynamics(long_df))

        knowledge.sort(key=lambda k: k.strength * k.complexity, reverse=True)
        self.discovered_knowledge = knowledge
        return {
            "discovered_knowledge": [self._to_dict(k) for k in knowledge],
            "knowledge_count": len(knowledge),
            "summary": self._generate_summary(knowledge),
        }

    # --- internal -------------------------------------------------------
    def _discover_temporal_patterns(self, long_df: pd.DataFrame) -> List[ImplicitKnowledge]:
        df = long_df.copy()
        df["hour"] = df["ds"].dt.hour
        counts = df.groupby("hour")["staff"].nunique()
        if counts.empty:
            return []
        low_hours = counts[counts < counts.mean()].index.tolist()
        if not low_hours:
            return []
        return [
            ImplicitKnowledge(
                category="temporal",
                description=f"hours {low_hours} have fewer staff",
                strength=0.7,
                evidence={"hours": low_hours},
                actionable_advice="Use these hours for training",
                complexity=2,
            )
        ]

    def _discover_social_dynamics(self, long_df: pd.DataFrame) -> List[ImplicitKnowledge]:
        G = nx.Graph()
        for _, group in long_df.groupby("ds"):
            staff = group["staff"].unique()
            for i in range(len(staff)):
                for j in range(i + 1, len(staff)):
                    s1, s2 = staff[i], staff[j]
                    if G.has_edge(s1, s2):
                        G[s1][s2]["weight"] += 1
                    else:
                        G.add_edge(s1, s2, weight=1)
        if len(G) < 3:
            return []
        centrality = nx.betweenness_centrality(G)
        top = max(centrality, key=centrality.get)
        return [
            ImplicitKnowledge(
                category="social",
                description=f"{top} plays key role",
                strength=min(centrality[top] * 5, 1.0),
                evidence={"centrality": centrality[top]},
                actionable_advice="Consider backup for key staff",
                complexity=3,
            )
        ]

    def _generate_summary(self, knowledge: List[ImplicitKnowledge]) -> str:
        if not knowledge:
            return "No implicit knowledge discovered."
        counts = Counter(k.category for k in knowledge)
        lines = [f"- {k}: {v}" for k, v in counts.items()]
        return "\n".join(lines)

    def _to_dict(self, k: ImplicitKnowledge) -> Dict[str, Any]:
        return {
            "category": k.category,
            "description": k.description,
            "strength": k.strength,
            "evidence": k.evidence,
            "actionable_advice": k.actionable_advice,
            "complexity": k.complexity,
        }
