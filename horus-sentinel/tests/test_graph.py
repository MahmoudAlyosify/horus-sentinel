"""Tests for the Intelligence Knowledge Graph and graph scoring."""

from graph.knowledge_graph import KnowledgeGraph
from schemas.findings import EntityKind, Finding
from scoring.graph_scoring import apply_scores


def _f(kind: EntityKind, value: str, *, related_to=None, rel=None, attrs=None) -> Finding:
    return Finding(
        entity_kind=kind,
        entity_value=value,
        attributes=attrs or {},
        related_to=related_to,
        relationship=rel,
        produced_by="test",
    )


def _exposure_chain() -> list[Finding]:
    """domain -> IP -> Service -> Technology -> CVE, the Part 5.3 signature chain."""
    return [
        _f(EntityKind.DOMAIN, "example.com"),
        _f(EntityKind.IP, "93.184.216.34", related_to="example.com", rel="RESOLVES_TO"),
        _f(
            EntityKind.SERVICE,
            "example.com:443",
            related_to="93.184.216.34",
            rel="EXPOSES",
            attrs={"internet_facing": True},
        ),
        _f(EntityKind.TECHNOLOGY, "nginx", related_to="example.com:443", rel="RUNS"),
        _f(
            EntityKind.CVE,
            "CVE-2021-23017",
            related_to="nginx",
            rel="HAS_VULNERABILITY",
            attrs={"cvss": 9.8},
        ),
    ]


def test_graph_builds_nodes_and_edges():
    graph = KnowledgeGraph.from_findings(_exposure_chain())
    assert graph.node_count() == 5
    assert graph.edge_count() == 4
    assert graph.nodes_by_kind(EntityKind.IP) == ["IP:93.184.216.34"]


def test_parent_resolution_uses_correct_kind():
    """The Service's parent must resolve to the IP node, not a mis-kinded stub."""
    graph = KnowledgeGraph.from_findings(_exposure_chain())
    # IP -> Service edge exists with the right endpoints.
    assert graph.g.has_edge("IP:93.184.216.34", "Service:example.com:443")


def test_signature_cve_query_returns_the_chain():
    graph = KnowledgeGraph.from_findings(_exposure_chain())
    hits = graph.public_services_with_critical_cve(min_cvss=9.0)
    assert len(hits) == 1
    hit = hits[0]
    assert hit["ip"] == "93.184.216.34"
    assert hit["technology"] == "nginx"
    assert hit["cve"] == "CVE-2021-23017"
    assert hit["cvss"] == 9.8


def test_low_cvss_is_excluded_from_signature_query():
    findings = _exposure_chain()
    findings[-1] = _f(
        EntityKind.CVE,
        "CVE-low",
        related_to="nginx",
        rel="HAS_VULNERABILITY",
        attrs={"cvss": 4.0},
    )
    graph = KnowledgeGraph.from_findings(findings)
    assert graph.public_services_with_critical_cve(min_cvss=9.0) == []


def test_apply_scores_colors_every_node():
    graph = KnowledgeGraph.from_findings(_exposure_chain())
    results = apply_scores(graph)
    assert len(results) == graph.node_count()
    for _, data in graph.g.nodes(data=True):
        assert "risk_score" in data
        assert "risk_band" in data


def test_critical_cve_node_scores_high():
    graph = KnowledgeGraph.from_findings(_exposure_chain())
    apply_scores(graph)
    cve = graph.g.nodes["CVE:cve-2021-23017"]
    # cvss 9.8 -> reputation and criticality both ~0.98 -> a meaningful score.
    assert cve["risk_score"] > 20


def test_subgraph_context_extracts_neighborhood():
    graph = KnowledgeGraph.from_findings(_exposure_chain())
    ctx = graph.subgraph_context("Service:example.com:443", hops=1)
    keys = {n["key"] for n in ctx["nodes"]}
    assert "Service:example.com:443" in keys
    assert "IP:93.184.216.34" in keys  # 1 hop up
    assert "Technology:nginx" in keys  # 1 hop down


def test_cytoscape_export_shape():
    graph = KnowledgeGraph.from_findings(_exposure_chain())
    apply_scores(graph)
    elements = graph.to_cytoscape()
    assert len(elements["nodes"]) == 5
    assert len(elements["edges"]) == 4
    assert all("color" in n["data"] for n in elements["nodes"])
