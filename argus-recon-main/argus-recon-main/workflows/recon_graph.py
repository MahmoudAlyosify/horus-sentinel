"""
LangGraph orchestration workflow (section 2.3).

A stateful, conditional graph that orchestrates the recon pipeline:

  OSINT (passive)
    → Web Fingerprinting (passive)
    → [conditional] Network (active, if authorized)
    → Threat Intel (passive enrichment)
    → [future] Analysis (LLM reasoning)
    → [future] Report generation

Each node reads from ReconState, calls a tool/agent, and updates state with
findings. Edges can be conditional: the Network node is skipped unless
RoE.active_scanning_authorized is True.
"""

from __future__ import annotations

from agents.network_agent import NetworkAgent
from agents.osint_agent import OsintAgent
from agents.threat_intel_agent import ThreatIntelAgent
from agents.web_agent import WebAgent
from langgraph.graph import END, StateGraph
from schemas.recon_state import ReconState


async def osint_node(state: ReconState) -> ReconState:
    """Run OSINT collection, update state with discovered assets."""
    agent = OsintAgent()
    result = await agent.run(state.apex_domain)

    state.discovered_domains.extend(result.domains)
    state.discovered_subdomains.extend(result.subdomains)
    state.discovered_ips.extend(result.ip_addresses)

    state.kb_refs["osint"] = {
        "domains": result.domains,
        "subdomains": result.subdomains,
        "ips": result.ip_addresses,
        "mx": result.mx_hosts,
        "ns": result.ns_hosts,
        "txt": result.txt_records,
    }
    return state


async def web_node(state: ReconState) -> ReconState:
    """Run web fingerprinting on discovered hosts."""
    hosts_to_probe = [state.apex_domain] + state.discovered_subdomains[:5]

    agent = WebAgent()
    result = await agent.run(hosts_to_probe)

    state.kb_refs["web"] = {"hosts": result.model_dump(mode="json")["hosts"]}
    return state


async def network_node(state: ReconState) -> ReconState:
    """Run active network discovery (port scanning) if authorized."""
    if not state.active_scanning_authorized:
        return state

    agent = NetworkAgent()
    result = await agent.run(state.discovered_ips)

    state.kb_refs["network"] = {"targets": result.model_dump(mode="json")["targets"]}
    return state


async def threat_intel_node(state: ReconState) -> ReconState:
    """Enrich discovered assets with threat intelligence."""
    assets = [
        {"kind": "domain", "value": d} for d in state.discovered_domains
    ] + [{"kind": "ip", "value": ip} for ip in state.discovered_ips]

    agent = ThreatIntelAgent()
    result = await agent.run(assets)

    state.kb_refs["threat_intel"] = {
        "assets": result.model_dump(mode="json")["assets"]
    }
    return state


def should_run_network(state: ReconState) -> bool:
    """Conditional edge: only run network if active scanning is authorized."""
    return state.active_scanning_authorized


def build_recon_graph() -> StateGraph:
    """Construct the LangGraph state graph for reconnaissance orchestration."""
    graph = StateGraph(ReconState)

    # Add nodes
    graph.add_node("osint", osint_node)
    graph.add_node("web", web_node)
    graph.add_node("network", network_node)
    graph.add_node("threat_intel", threat_intel_node)

    # Define flow
    graph.set_entry_point("osint")

    graph.add_edge("osint", "web")

    graph.add_conditional_edges(
        "web",
        should_run_network,
        {True: "network", False: "threat_intel"},
    )

    graph.add_edge("network", "threat_intel")
    graph.add_edge("threat_intel", END)

    return graph.compile()


# Global compiled graph
recon_graph = build_recon_graph()
