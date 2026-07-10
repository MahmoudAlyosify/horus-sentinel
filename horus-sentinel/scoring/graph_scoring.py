"""Derive risk sub-scores from graph structure and color the graph.

Keeps ``scoring.engine`` pure: this module is the only place that knows about both the
graph and the scorer. The derivations are deterministic heuristics over node attributes
and 1-hop neighborhood, so the same graph always yields the same colors — exactly the
reproducibility the master plan requires (Part 2.2 #4).
"""

from __future__ import annotations

from graph.knowledge_graph import _INFRA_EDGES, KnowledgeGraph
from schemas.findings import EntityKind
from scoring.engine import RiskInputs, ScoreResult, compute_score

_BASE_CRITICALITY = {
    EntityKind.REGION.value: 0.7,
    EntityKind.DOMAIN.value: 0.6,
    EntityKind.ORGANIZATION.value: 0.6,
    EntityKind.SUBDOMAIN.value: 0.5,
    EntityKind.IP.value: 0.5,
    EntityKind.SERVICE.value: 0.5,
    EntityKind.TECHNOLOGY.value: 0.5,
    EntityKind.THREAT_ACTOR.value: 0.7,
}


def _infra_degree(graph: KnowledgeGraph, key: str) -> int:
    """Number of exposure-related edges incident to a node."""
    g = graph.g
    count = 0
    for _, _, d in g.in_edges(key, data=True):
        if d.get("label") in _INFRA_EDGES:
            count += 1
    for _, _, d in g.out_edges(key, data=True):
        if d.get("label") in _INFRA_EDGES:
            count += 1
    return count


def _neighbor_instability(graph: KnowledgeGraph, key: str) -> float:
    """Max instability index found on the node itself or its immediate neighbors."""
    g = graph.g
    best = 0.0
    candidates = [key, *graph.neighbors(key)]
    for n in candidates:
        attrs = g.nodes[n].get("attributes", {})
        val = attrs.get("instability_index")
        if isinstance(val, int | float):
            best = max(best, float(val))
    return best


def _reputation(graph: KnowledgeGraph, key: str) -> float:
    g = graph.g
    kind = g.nodes[key]["kind"]
    attrs = g.nodes[key].get("attributes", {})

    if kind == EntityKind.CVE.value and attrs.get("cvss") is not None:
        return min(1.0, float(attrs["cvss"]) / 10.0)
    if attrs.get("normalized_reputation") is not None:
        return float(attrs["normalized_reputation"])

    best = 0.0
    for n in graph.neighbors(key):
        nd = g.nodes[n]
        na = nd.get("attributes", {})
        if nd["kind"] == EntityKind.CVE.value and na.get("cvss") is not None:
            best = max(best, min(1.0, float(na["cvss"]) / 10.0) * 0.9)
        if na.get("normalized_reputation") is not None:
            best = max(best, float(na["normalized_reputation"]))
    return best


def _criticality(graph: KnowledgeGraph, key: str) -> float:
    g = graph.g
    kind = g.nodes[key]["kind"]
    attrs = g.nodes[key].get("attributes", {})
    if attrs.get("criticality") is not None:
        return min(1.0, float(attrs["criticality"]))
    if kind == EntityKind.CVE.value and attrs.get("cvss") is not None:
        return min(1.0, float(attrs["cvss"]) / 10.0)
    return _BASE_CRITICALITY.get(kind, 0.3)


def risk_inputs_for_node(graph: KnowledgeGraph, key: str) -> RiskInputs:
    """Deterministically derive the four sub-scores for one node."""
    g = graph.g
    attrs = g.nodes[key].get("attributes", {})

    exposure = min(1.0, 0.12 * _infra_degree(graph, key))
    if attrs.get("internet_facing"):
        exposure = min(1.0, exposure + 0.3)

    return RiskInputs(
        exposure=exposure,
        threat_context=_neighbor_instability(graph, key),
        reputation=_reputation(graph, key),
        criticality=_criticality(graph, key),
    )


def apply_scores(graph: KnowledgeGraph) -> dict[str, ScoreResult]:
    """Score every node and write ``risk_score``/``risk_band`` back for coloring."""
    results: dict[str, ScoreResult] = {}
    for key in list(graph.g.nodes):
        inputs = risk_inputs_for_node(graph, key)
        result = compute_score(inputs)
        graph.g.nodes[key]["risk_score"] = result.score
        graph.g.nodes[key]["risk_band"] = str(result.band)
        results[key] = result
    return results
