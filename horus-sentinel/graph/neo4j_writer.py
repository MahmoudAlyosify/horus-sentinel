"""Optional Neo4j mirror of the Intelligence Knowledge Graph.

The MVP graph lives in ``networkx`` so the platform runs with zero infrastructure. When a
Neo4j server is configured (the full stack), this writer mirrors the same nodes and edges
into it, giving you the Neo4j Browser view and Cypher for the demo. The ``neo4j`` driver
is imported lazily so nothing here is required for the MVP path.
"""

from __future__ import annotations

import structlog

from core.config import settings
from graph.knowledge_graph import KnowledgeGraph

log = structlog.get_logger("horus.graph.neo4j")


def neo4j_available() -> bool:
    """True if the neo4j driver is importable (does not test connectivity)."""
    try:
        import neo4j  # noqa: F401
    except ImportError:
        return False
    return True


def mirror_to_neo4j(graph: KnowledgeGraph, job_id: str) -> bool:
    """Write the graph into Neo4j. Returns False (non-fatally) if unavailable.

    Idempotent per job: nodes are MERGEd on (job_id, key). Safe to call repeatedly.
    """
    if not neo4j_available():
        log.info("neo4j_driver_missing_skip_mirror")
        return False

    import neo4j

    try:
        driver = neo4j.GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    except Exception as exc:  # bad config / server down — non-fatal for the MVP
        log.warning("neo4j_connect_failed", error=str(exc))
        return False

    try:
        with driver.session() as session:
            for key, data in graph.g.nodes(data=True):
                session.run(
                    "MERGE (n:Entity {job_id: $job_id, key: $key}) "
                    "SET n.kind = $kind, n.value = $value, "
                    "n.risk_score = $risk_score, n.risk_band = $risk_band",
                    job_id=job_id,
                    key=key,
                    kind=data.get("kind"),
                    value=data.get("value"),
                    risk_score=data.get("risk_score"),
                    risk_band=data.get("risk_band"),
                )
            for u, v, d in graph.g.edges(data=True):
                session.run(
                    "MATCH (a:Entity {job_id: $job_id, key: $u}), "
                    "(b:Entity {job_id: $job_id, key: $v}) "
                    "MERGE (a)-[r:REL {label: $label}]->(b)",
                    job_id=job_id,
                    u=u,
                    v=v,
                    label=d.get("label", "RELATED"),
                )
        log.info("neo4j_mirror_complete", job_id=job_id, nodes=graph.node_count())
        return True
    except Exception as exc:
        log.warning("neo4j_mirror_failed", error=str(exc))
        return False
    finally:
        driver.close()
