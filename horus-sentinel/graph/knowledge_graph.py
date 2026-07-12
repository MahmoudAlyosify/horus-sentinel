"""The Intelligence Knowledge Graph (master plan Part 5).

Findings become nodes + edges; analysis becomes traversal instead of manual cross-
referencing. This MVP is backed by ``networkx`` so it runs with zero infrastructure; a
Neo4j writer (``graph.neo4j_writer``) mirrors the same graph into Neo4j when configured.

The graph is the single source of truth the HORUS brain reasons over: the Analysis Agent
pulls a *subgraph* (Part 4.2) as grounded context, and the risk engine colors every node.
"""

from __future__ import annotations

import ipaddress
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import networkx as nx

from schemas.findings import EntityKind, Finding

# Edge labels that indicate public/infra exposure, used by the exposure sub-score.
# Includes the active-recon edges (open ports, discovered endpoints, service identification).
_INFRA_EDGES = {
    "HAS_SUBDOMAIN", "RESOLVES_TO", "EXPOSES", "RUNS", "USES_NAMESERVER",
    "HAS_OPEN_PORT", "HAS_ENDPOINT", "IDENTIFIED_AS",
}

_DOMAINISH = re.compile(r"^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")


def _infer_kind(value: str) -> str:
    """Best-effort node kind for a parent that was never asserted as its own finding."""
    try:
        ipaddress.ip_address(value)
        return EntityKind.IP.value
    except ValueError:
        pass
    if ":" in value and value.rsplit(":", 1)[-1].isdigit():
        return EntityKind.SERVICE.value
    if _DOMAINISH.match(value):
        return EntityKind.DOMAIN.value
    return EntityKind.ORGANIZATION.value


@dataclass
class NodeView:
    """A read model of a graph node for the UI / report."""

    key: str
    kind: str
    value: str
    attributes: dict[str, Any]
    risk_score: float | None = None
    risk_band: str | None = None


class KnowledgeGraph:
    """A directed multigraph of intelligence entities and their relationships."""

    def __init__(self) -> None:
        self.g: nx.MultiDiGraph = nx.MultiDiGraph()

    # ---- construction -------------------------------------------------------
    def add_node_from_finding(self, finding: Finding) -> None:
        """Upsert the finding's own entity node (no edges)."""
        self._upsert_node(
            finding.node_key(), finding.entity_kind, finding.entity_value, finding.attributes
        )

    def add_edge_from_finding(self, finding: Finding) -> None:
        """Add the finding's relationship edge, resolving the parent to a real node."""
        if not (finding.related_to and finding.relationship):
            return
        parent_key = self._resolve_parent_key(finding.related_to)
        if parent_key not in self.g:
            kind, value = parent_key.split(":", 1)
            self._upsert_node(parent_key, kind, value, {})
        self.g.add_edge(parent_key, finding.node_key(), label=finding.relationship)

    def add_finding(self, finding: Finding) -> None:
        """Incremental add: upsert the node, then its edge (parent stubbed if absent)."""
        self.add_node_from_finding(finding)
        self.add_edge_from_finding(finding)

    def _upsert_node(
        self, key: str, kind: EntityKind | str, value: str, attributes: dict[str, Any]
    ) -> None:
        kind_str = str(kind)
        if key in self.g:
            self.g.nodes[key]["attributes"].update(attributes)
        else:
            self.g.add_node(key, kind=kind_str, value=value, attributes=dict(attributes))

    def _resolve_parent_key(self, related_to: str) -> str:
        """A finding's ``related_to`` is a raw value; find the node whose value matches."""
        target = related_to.lower()
        for key, data in self.g.nodes(data=True):
            if data.get("value", "").lower() == target:
                return key
        # No asserted parent node — infer the most likely kind for a clean stub.
        return f"{_infer_kind(related_to)}:{target}"

    @classmethod
    def from_findings(cls, findings: list[Finding]) -> KnowledgeGraph:
        """Two-pass build: all nodes first, then all edges, so parents always resolve."""
        graph = cls()
        for f in findings:
            graph.add_node_from_finding(f)
        for f in findings:
            graph.add_edge_from_finding(f)
        return graph

    # ---- inspection ---------------------------------------------------------
    def node_count(self) -> int:
        return self.g.number_of_nodes()

    def edge_count(self) -> int:
        return self.g.number_of_edges()

    def nodes_by_kind(self, kind: EntityKind | str) -> list[str]:
        kind_str = str(kind)
        return [k for k, d in self.g.nodes(data=True) if d.get("kind") == kind_str]

    def neighbors(self, key: str) -> list[str]:
        """Undirected 1-hop neighborhood."""
        out = set(self.g.successors(key)) if key in self.g else set()
        out |= set(self.g.predecessors(key)) if key in self.g else set()
        return sorted(out)

    def subgraph_context(self, key: str, hops: int = 2) -> dict[str, Any]:
        """Extract an entity + its 1–2 hop neighborhood as grounded LLM context (Part 4.2)."""
        if key not in self.g:
            return {"root": key, "nodes": [], "edges": []}
        undirected = self.g.to_undirected(as_view=True)
        within = nx.ego_graph(undirected, key, radius=hops)
        nodes = [
            {
                "key": n,
                "kind": self.g.nodes[n]["kind"],
                "value": self.g.nodes[n]["value"],
                "attributes": self.g.nodes[n]["attributes"],
                "risk_band": self.g.nodes[n].get("risk_band"),
            }
            for n in within.nodes
        ]
        edges = [
            {"source": u, "target": v, "label": d.get("label")}
            for u, v, d in self.g.edges(data=True)
            if u in within.nodes and v in within.nodes
        ]
        return {"root": key, "nodes": nodes, "edges": edges}

    # ---- the signature query (master plan Part 5.3) -------------------------
    def public_services_with_critical_cve(self, min_cvss: float = 9.0) -> list[dict[str, Any]]:
        """Public services running technology with a known critical CVE.

        The graph equivalent of the Cypher in Part 5.3: traverse
        IP -[EXPOSES]-> Service -[RUNS]-> Technology -[HAS_VULNERABILITY]-> CVE.
        """
        results: list[dict[str, Any]] = []
        for cve_key in self.nodes_by_kind(EntityKind.CVE):
            cvss = self.g.nodes[cve_key]["attributes"].get("cvss")
            if cvss is None or float(cvss) < min_cvss:
                continue
            for tech in self.g.predecessors(cve_key):
                if self.g.nodes[tech]["kind"] != EntityKind.TECHNOLOGY.value:
                    continue
                for svc in self.g.predecessors(tech):
                    if self.g.nodes[svc]["kind"] != EntityKind.SERVICE.value:
                        continue
                    for ip in self.g.predecessors(svc):
                        if self.g.nodes[ip]["kind"] != EntityKind.IP.value:
                            continue
                        results.append(
                            {
                                "ip": self.g.nodes[ip]["value"],
                                "service": self.g.nodes[svc]["value"],
                                "technology": self.g.nodes[tech]["value"],
                                "cve": self.g.nodes[cve_key]["value"],
                                "cvss": float(cvss),
                            }
                        )
        return sorted(results, key=lambda r: r["cvss"], reverse=True)

    # ---- export -------------------------------------------------------------
    def to_cytoscape(self) -> dict[str, list[dict[str, Any]]]:
        """Cytoscape.js elements for the Command Center graph viewer."""
        band_colors = {
            "Critical": "#d7263d",
            "High": "#f46036",
            "Medium": "#f0c808",
            "Low": "#2e8b57",
            "Info": "#6c757d",
        }
        nodes = [
            {
                "data": {
                    "id": key,
                    "label": data["value"],
                    "kind": data["kind"],
                    "risk_band": data.get("risk_band", "Info"),
                    "risk_score": data.get("risk_score"),
                    "color": band_colors.get(data.get("risk_band", "Info"), "#6c757d"),
                }
            }
            for key, data in self.g.nodes(data=True)
        ]
        edges = [
            {"data": {"source": u, "target": v, "label": d.get("label", "")}}
            for u, v, d in self.g.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}

    def node_views(self) -> list[NodeView]:
        return [
            NodeView(
                key=k,
                kind=d["kind"],
                value=d["value"],
                attributes=d["attributes"],
                risk_score=d.get("risk_score"),
                risk_band=d.get("risk_band"),
            )
            for k, d in self.g.nodes(data=True)
        ]

    def kind_histogram(self) -> dict[str, int]:
        hist: dict[str, int] = defaultdict(int)
        for _, d in self.g.nodes(data=True):
            hist[d["kind"]] += 1
        return dict(hist)
