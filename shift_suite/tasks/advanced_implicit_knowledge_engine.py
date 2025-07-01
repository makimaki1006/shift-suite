"""高度な機械学習とパターンマイニングを使用した暗黙知発見エンジン."""
from __future__ import annotations

import itertools
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable

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
    """Engine discovering implicit knowledge from long format DataFrame."""

    def __init__(self) -> None:
        self.discovered_knowledge: List[ImplicitKnowledge] = []

    # ------------------------------------------------------------------
    def discover_all_implicit_knowledge(
        self,
        long_df: pd.DataFrame,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Run all discovery steps and return aggregated result."""
        if long_df.empty:
            return {
                "discovered_knowledge": [],
                "knowledge_count": 0,
                "knowledge_network": {"nodes": [], "edges": []},
                "actionable_blueprint": {},
                "summary": "No implicit knowledge discovered.",
            }

        if progress_callback:
            progress_callback((55, "時間的パターンを分析中..."))
        temporal_knowledge = self._discover_temporal_patterns(long_df)

        if progress_callback:
            progress_callback((65, "社会的ダイナミクスを分析中..."))
        social_knowledge = self._discover_social_dynamics(long_df)

        if progress_callback:
            progress_callback((75, "最適化戦略を分析中..."))
        optimization_knowledge = self._discover_optimization_strategies(long_df)

        if progress_callback:
            progress_callback((85, "例外処理パターンを分析中..."))
        exception_knowledge = self._discover_exception_handling(long_df)

        if progress_callback:
            progress_callback((95, "継続的改善パターンを分析中..."))
        learning_knowledge = self._discover_learning_patterns(long_df)

        all_knowledge = (
            temporal_knowledge
            + social_knowledge
            + optimization_knowledge
            + exception_knowledge
            + learning_knowledge
        )

        all_knowledge.sort(key=lambda k: k.strength * k.complexity, reverse=True)
        knowledge_network = self._build_knowledge_network(all_knowledge)
        summary = self._generate_executive_summary(all_knowledge, knowledge_network)
        blueprint = self._generate_actionable_blueprint(all_knowledge, knowledge_network)
        self.discovered_knowledge = all_knowledge
        return {
            "discovered_knowledge": [self._knowledge_to_dict(k) for k in all_knowledge],
            "knowledge_count": len(all_knowledge),
            "knowledge_network": knowledge_network,
            "actionable_blueprint": blueprint,
            "summary": summary,
        }

    # ------------------------------------------------------------------
    def _discover_temporal_patterns(self, long_df: pd.DataFrame) -> List[ImplicitKnowledge]:
        if "ds" not in long_df.columns:
            return []
        df = long_df.copy()
        df["hour"] = pd.to_datetime(df["ds"]).dt.hour
        counts = df.groupby("hour")["staff"].nunique()
        if counts.empty:
            return []
        expected = counts.mean()
        low_hours = counts[counts < expected].index.tolist()
        if not low_hours:
            return []
        strength = min(len(low_hours) / 24, 1.0)
        return [
            ImplicitKnowledge(
                category="temporal",
                description=f"Hours {low_hours} show lower staffing than average",
                strength=strength,
                evidence={
                    "type": "low_staff_hours",
                    "actual_counts": counts.loc[low_hours].to_dict(),
                    "expected_count": expected,
                },
                actionable_advice="Use these hours for training or maintenance",
                complexity=2,
            )
        ]

    # ------------------------------------------------------------------
    def _discover_social_dynamics(self, long_df: pd.DataFrame) -> List[ImplicitKnowledge]:
        knowledge: List[ImplicitKnowledge] = []
        G = nx.Graph()
        time_groups = long_df.groupby("ds")
        for _, group in time_groups:
            staff_list = group["staff"].unique()
            for s1, s2 in itertools.combinations(staff_list, 2):
                if G.has_edge(s1, s2):
                    G[s1][s2]["weight"] += 1
                else:
                    G.add_edge(s1, s2, weight=1)

        if len(G) == 0:
            return knowledge

        communities = list(nx.community.greedy_modularity_communities(G))
        for i, community in enumerate(communities):
            if len(community) < 3:
                continue
            subgraph = G.subgraph(community)
            cohesion = nx.density(subgraph)
            external_links = sum(G.degree(n) for n in community) - 2 * subgraph.number_of_edges()
            if cohesion > 0.5:
                knowledge.append(
                    ImplicitKnowledge(
                        category="team",
                        description=f"Core team {i + 1}: {', '.join(list(community)[:3])}...",
                        strength=cohesion,
                        evidence={
                            "type": "community_detection",
                            "members": list(community),
                            "cohesion_score": round(cohesion, 3),
                            "external_connection_count": external_links,
                            "team_size": len(community),
                        },
                        actionable_advice="Utilise this well connected team for project work",
                        complexity=4,
                    )
                )

        # key person detection
        if len(G) > 2:
            centrality = nx.betweenness_centrality(G)
            if centrality:
                top = max(centrality, key=centrality.get)
                connected = sum(1 for comm in communities if top in comm)
                knowledge.append(
                    ImplicitKnowledge(
                        category="key_person",
                        description=f"{top} acts as hub staff",
                        strength=min(centrality[top] * 2, 1.0),
                        evidence={
                            "type": "key_person",
                            "staff": [top],
                            "connected_communities": connected,
                            "centrality_score": round(centrality[top], 3),
                        },
                        actionable_advice="Prepare backup personnel for this key staff",
                        complexity=3,
                    )
                )

        return knowledge

    # ------------------------------------------------------------------
    def _discover_optimization_strategies(self, long_df: pd.DataFrame) -> List[ImplicitKnowledge]:
        if "role" not in long_df.columns:
            return []
        df = long_df.sort_values("ds")
        transitions: defaultdict[tuple[str, str], int] = defaultdict(int)
        for _, group in df.groupby("staff"):
            roles = group["role"].tolist()
            for r1, r2 in zip(roles, roles[1:]):
                transitions[(r1, r2)] += 1
        if not transitions:
            return []
        total = sum(transitions.values())
        knowledge: List[ImplicitKnowledge] = []
        for (r1, r2), forward in transitions.items():
            backward = transitions.get((r2, r1), 0)
            ratio_f = forward / total
            ratio_b = backward / total if total else 0
            if forward < 3 or ratio_f <= ratio_b:
                continue
            strength = min((ratio_f - ratio_b) * 5, 1.0)
            knowledge.append(
                ImplicitKnowledge(
                    category="skill_progression",
                    description=f"{r1}→{r2} transition frequent",
                    strength=strength,
                    evidence={
                        "type": "transition_rate",
                        "from_role": r1,
                        "to_role": r2,
                        "actual_forward": forward,
                        "actual_backward": backward,
                        "forward_ratio": ratio_f,
                        "backward_ratio": ratio_b,
                    },
                    actionable_advice=f"Train {r1} staff toward {r2}",
                    complexity=3,
                )
            )
        return knowledge

    # ------------------------------------------------------------------
    def _discover_exception_handling(self, long_df: pd.DataFrame) -> List[ImplicitKnowledge]:
        for col in ["exception", "note", "remarks"]:
            if col in long_df.columns:
                ratio = float(long_df[col].notna().mean())
                threshold = 0.05
                if ratio > threshold:
                    return [
                        ImplicitKnowledge(
                            category="exception",
                            description=f"Frequent exceptions noted in {col}",
                            strength=min(ratio / threshold, 1.0),
                            evidence={
                                "type": "exception_rate",
                                "column": col,
                                "actual_ratio": ratio,
                                "threshold": threshold,
                            },
                            actionable_advice="Review rules causing many exceptions",
                            complexity=2,
                        )
                    ]
        return []

    # ------------------------------------------------------------------
    def _discover_learning_patterns(self, long_df: pd.DataFrame) -> List[ImplicitKnowledge]:
        return []

    # ------------------------------------------------------------------
    def _build_knowledge_network(self, knowledge_list: List[ImplicitKnowledge]) -> Dict[str, Any]:
        G = nx.DiGraph()
        for i, k in enumerate(knowledge_list):
            G.add_node(i, category=k.category, description=k.description, strength=k.strength)

        for i, j in itertools.combinations(range(len(knowledge_list)), 2):
            k1, k2 = knowledge_list[i], knowledge_list[j]
            relation = None
            if (
                ("負荷分散" in k1.category and "コスト" in k2.category)
                or ("コスト" in k1.category and "負荷分散" in k2.category)
            ):
                relation = "conflicts"
            if "キーパーソン" in k1.description and "チーム" in k2.description:
                if any(staff in k2.evidence.get("members", []) for staff in k1.evidence.get("staff", [])):
                    relation = "strengthens"
            if relation:
                weight = 0.8 if relation == "conflicts" else 0.9
                G.add_edge(i, j, type=relation, weight=weight)

        return {
            "nodes": [
                {"id": i, "label": f"K{i}: {k.category}", "title": k.description}
                for i, k in enumerate(knowledge_list)
            ],
            "edges": [
                {"from": u, "to": v, "label": d["type"]}
                for u, v, d in G.edges(data=True)
            ],
        }

    # ------------------------------------------------------------------
    def _generate_actionable_blueprint(
        self, knowledge_list: List[ImplicitKnowledge], network: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        return {}

    # ------------------------------------------------------------------
    def _generate_executive_summary(
        self, knowledge_list: List[ImplicitKnowledge], network: Dict[str, Any]
    ) -> str:
        if not knowledge_list:
            return "No implicit knowledge discovered."
        strongest = sorted(knowledge_list, key=lambda k: k.strength, reverse=True)[:3]
        lines = ["### Top Rules"]
        for k in strongest:
            lines.append(f"- {k.description} (strength {k.strength:.2f})")
        most_complex = max(knowledge_list, key=lambda k: k.complexity, default=None)
        if most_complex:
            lines.append(f"- Highest complexity rule: {most_complex.description}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _knowledge_to_dict(self, knowledge: ImplicitKnowledge) -> Dict[str, Any]:
        return knowledge.__dict__.copy()
