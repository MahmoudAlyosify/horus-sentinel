"""Analysis Agent — the HORUS brain reading the graph (master plan Part 4.2/4.3).

This is the heart of the ARGUS→HORUS merge. It:
  1. rebuilds the intelligence graph from the job's findings and risk-scores every node,
  2. maps significant entities to framework techniques via RAG (ATT&CK TA0043/TA0042),
  3. builds deterministic, evidence-linked prioritized findings (graph is ground truth),
  4. asks the self-hosted model for the *narrative* sections, grounded by a subgraph + RAG,
  5. applies a bounded (±1 band), logged risk adjustment,
and returns a typed Report Card. Nothing here invents entities or scores.
"""

from __future__ import annotations

import structlog

from core.findings_store import load_findings
from graph.knowledge_graph import KnowledgeGraph
from horus_brain.horus_provider import ReasoningInput, horus_provider
from horus_brain.report_card import BandAdjustment, FrameworkMapping, PrioritizedFinding, ReportCard
from rag.loader import get_grounding_store, get_technique_index
from schemas.findings import EntityKind, Finding
from scoring.engine import RiskBand, adjust_band, band_for
from scoring.graph_scoring import apply_scores

log = structlog.get_logger("horus.agent.analysis")

# Per-node-kind RAG query seeds — what an adversary could learn from this kind of entity.
_KIND_QUERY = {
    EntityKind.SUBDOMAIN.value: "DNS certificate transparency subdomains network information",
    EntityKind.DOMAIN.value: "DNS WHOIS domain registration network information",
    EntityKind.CERTIFICATE.value: "certificate transparency subdomains network information",
    EntityKind.IP.value: "resolved IP infrastructure reputation malicious",
    EntityKind.PORT.value: "open port network service discovery active scanning exposed",
    EntityKind.SERVICE.value: "public service host software version headers fingerprint",
    EntityKind.TECHNOLOGY.value: "host software version headers fingerprint vulnerability",
    EntityKind.ENDPOINT.value: "web application public-facing endpoint content discovery exploit",
    EntityKind.CVE.value: "host software version known vulnerability exposure",
    EntityKind.EMAIL.value: "identity email addresses phishing",
    EntityKind.INDICATOR.value: "compromise infrastructure reputation malicious IP",
    EntityKind.EVENT.value: "regional instability attack modality target category",
    EntityKind.REGION.value: "regional instability attack modality target category",
    EntityKind.THREAT_ACTOR.value: "threat actor regional instability",
}

# Kinds worth surfacing as prioritized findings (skip low-signal scaffolding nodes).
_PRIORITY_KINDS = {
    EntityKind.CVE.value,
    EntityKind.PORT.value,
    EntityKind.SERVICE.value,
    EntityKind.SUBDOMAIN.value,
    EntityKind.TECHNOLOGY.value,
    EntityKind.ENDPOINT.value,
    EntityKind.INDICATOR.value,
    EntityKind.EVENT.value,
    EntityKind.IP.value,
}


class AnalysisAgent:
    """Turns the correlated graph into a grounded, prioritized intelligence Report Card."""

    name = "analysis"

    async def analyze(self, job_id: str, subject_value: str) -> tuple[ReportCard, dict]:
        findings = load_findings(job_id)
        graph = KnowledgeGraph.from_findings(findings)
        apply_scores(graph)  # writes risk_score/risk_band onto every node in place
        store = get_grounding_store()
        index = get_technique_index()

        signature_hits = graph.public_services_with_critical_cve(min_cvss=9.0)
        prioritized = self._build_prioritized(graph, findings, store, index)
        top_band = self._top_band(prioritized)

        adjustments = self._bounded_adjustment(prioritized, signature_hits)
        if adjustments:
            top_band = adjustments[0].to_band

        # Offensive mode when active reconnaissance produced live attack surface.
        active_ran = bool(
            graph.nodes_by_kind(EntityKind.PORT) or graph.nodes_by_kind(EntityKind.ENDPOINT)
        )
        rag_context = store.context_block(
            f"{subject_value} {'attack surface open ports services endpoints ' if active_ran else 'exposure '}"
            + " ".join(p.entity_key for p in prioritized[:3])
        )
        data = ReasoningInput(
            subject=subject_value,
            subgraph=graph.subgraph_context(self._root_key(graph, subject_value), hops=2),
            rag_context=rag_context,
            entity_count=graph.node_count(),
            top_band=str(top_band),
            critical_cve_hits=len(signature_hits),
            facts=self._facts(graph, prioritized),
            mode="offensive" if active_ran else "defensive",
        )
        card = await horus_provider.reason(data)
        card.prioritized_findings = prioritized
        card.band_adjustments = adjustments
        card.top_band = str(top_band)

        log.info(
            "analysis_complete",
            job_id=job_id,
            entities=graph.node_count(),
            prioritized=len(prioritized),
            critical_cves=len(signature_hits),
            generated_by=card.generated_by,
        )
        return card, graph.to_cytoscape()

    # ---- prioritized findings ----------------------------------------------
    def _build_prioritized(
        self,
        graph: KnowledgeGraph,
        findings: list[Finding],
        store,  # noqa: ANN001
        index: dict[str, dict[str, str]],
    ) -> list[PrioritizedFinding]:
        evidence_by_node = _evidence_by_node(findings)
        items: list[PrioritizedFinding] = []
        for key, data in graph.g.nodes(data=True):
            if data["kind"] not in _PRIORITY_KINDS:
                continue
            score = data.get("risk_score", 0.0)
            band = data.get("risk_band", "Info")
            mapping, recommendation = self._map_framework(data, store, index)
            items.append(
                PrioritizedFinding(
                    title=f"{data['kind']} {data['value']}",
                    entity_key=key,
                    why_it_matters=self._why(data),
                    framework=mapping,
                    recommendation=recommendation,
                    risk_band=band,
                    risk_score=score,
                    evidence_ids=evidence_by_node.get(key, []),
                )
            )
        items.sort(key=lambda p: p.risk_score, reverse=True)
        return items[:12]

    def _map_framework(
        self,
        node_data: dict,
        store,
        index: dict[str, dict[str, str]],  # noqa: ANN001
    ) -> tuple[FrameworkMapping | None, str]:
        query = _KIND_QUERY.get(node_data["kind"], "search open technical databases")
        hits = store.query(query, k=1)
        if not hits:
            return None, "Review and reduce public exposure of this entity."
        meta = hits[0].document.metadata
        tid = meta.get("id", hits[0].document.id)
        tinfo = index.get(tid, {})
        mapping = FrameworkMapping(
            framework="MITRE ATT&CK" if tid.startswith("T") else "Geo-Threat Taxonomy",
            technique_id=tid,
            technique_name=meta.get("name", tinfo.get("name", "")),
            tactic=meta.get("tactic_name", tinfo.get("tactic_name", "")),
        )
        recommendation = tinfo.get("defensive_note") or "Reduce public exposure of this entity."
        return mapping, recommendation

    @staticmethod
    def _why(node_data: dict) -> str:
        kind = node_data["kind"]
        attrs = node_data.get("attributes", {})
        if kind == EntityKind.CVE.value:
            return f"Known vulnerability (CVSS {attrs.get('cvss', 'n/a')}) on public-facing technology."
        if kind == EntityKind.PORT.value:
            banner = attrs.get("banner") or ""
            svc = attrs.get("service", "service")
            return (
                f"Open port {attrs.get('port')} ({svc}) is live attack surface discovered by "
                f"active scanning — a potential entry point"
                + (f"; banner: {banner[:60]}" if banner else ".")
            )
        if kind == EntityKind.SERVICE.value:
            return "Internet-facing service enlarges the attack surface."
        if kind == EntityKind.ENDPOINT.value:
            forms = attrs.get("forms", 0)
            return (
                "Discovered web endpoint (active crawl)"
                + (f" with {forms} input form(s) — an input/attack surface." if forms
                   else " — expands the mapped surface.")
            )
        if kind == EntityKind.SUBDOMAIN.value:
            disc = attrs.get("discovery")
            extra = " (active brute-force)" if disc == "active_bruteforce" else " (certificate transparency)"
            return f"Discoverable subdomain{extra} — potential entry point."
        if kind == EntityKind.INDICATOR.value:
            return "Reputation signal indicates adjacency to known-malicious infrastructure."
        if kind == EntityKind.EVENT.value:
            return "Regional instability shapes the geopolitical threat picture."
        return "Publicly observable entity contributing to the exposure profile."

    # ---- bounded adjustment (invariant Part 2.2 #4) ------------------------
    def _bounded_adjustment(
        self, prioritized: list[PrioritizedFinding], signature_hits: list[dict]
    ) -> list[BandAdjustment]:
        """One logged ±1 nudge: a critical-CVE exposure escalates the headline by one band."""
        if not signature_hits or not prioritized:
            return []
        top = prioritized[0]
        current = RiskBand(top.risk_band)
        if current == RiskBand.CRITICAL:
            return []
        raised = adjust_band(current, +1)
        if raised == current:
            return []
        adj = BandAdjustment(
            entity_key=top.entity_key,
            from_band=str(current),
            to_band=str(raised),
            delta=1,
            reason=(
                f"{len(signature_hits)} public service(s) run technology with a known critical "
                "CVE — headline risk raised one band."
            ),
        )
        log.info("band_adjustment", **adj.model_dump())
        return [adj]

    # ---- helpers ------------------------------------------------------------
    @staticmethod
    def _top_band(prioritized: list[PrioritizedFinding]) -> RiskBand:
        if not prioritized:
            return RiskBand.INFO
        return band_for(max(p.risk_score for p in prioritized))

    @staticmethod
    def _root_key(graph: KnowledgeGraph, subject_value: str) -> str:
        target = subject_value.lower()
        for key, data in graph.g.nodes(data=True):
            if data.get("value", "").lower() == target:
                return key
        return next(iter(graph.g.nodes), "")

    @staticmethod
    def _facts(graph: KnowledgeGraph, prioritized: list[PrioritizedFinding]) -> list[str]:
        facts: list[str] = []
        hist = graph.kind_histogram()
        facts.append("Entity mix: " + ", ".join(f"{v} {k}" for k, v in sorted(hist.items())))

        # Active attack-surface facts (present only when active recon ran).
        open_ports = [
            (d["value"], d.get("attributes", {}))
            for _, d in graph.g.nodes(data=True)
            if d["kind"] == EntityKind.PORT.value
        ]
        if open_ports:
            summary = ", ".join(
                f"{v} ({a.get('service', '?')})" for v, a in open_ports[:12]
            )
            facts.append(
                f"Active recon found {len(open_ports)} open port(s) — live attack surface: {summary}"
            )
        endpoints = graph.nodes_by_kind(EntityKind.ENDPOINT)
        if endpoints:
            facts.append(f"Active web crawl mapped {len(endpoints)} endpoint(s) on the target.")

        for _, data in graph.g.nodes(data=True):
            attrs = data.get("attributes", {})
            if data["kind"] == EntityKind.EVENT.value and attrs.get("threat_context_summary"):
                facts.append(f"Geo-event: {attrs['threat_context_summary']}")
            if data["kind"] == EntityKind.EVENT.value and attrs.get("dominant_modalities"):
                facts.append(
                    f"Dominant modalities in {data['value']}: "
                    + ", ".join(attrs["dominant_modalities"])
                    + f" (instability {attrs.get('instability_index')})"
                )
        for p in prioritized[:5]:
            facts.append(f"{p.title} — {p.risk_band} ({p.risk_score}); {p.why_it_matters}")
        return facts


def _evidence_by_node(findings: list[Finding]) -> dict[str, list[str]]:
    """Map each graph node key to the ids of the findings that assert it (traceability)."""
    out: dict[str, list[str]] = {}
    for f in findings:
        out.setdefault(f.node_key(), []).append(f.id)
    return out


analysis_agent = AnalysisAgent()
