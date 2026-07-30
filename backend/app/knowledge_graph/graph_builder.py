from typing import Optional
from neo4j import GraphDatabase
from app.config import settings
from app.knowledge_graph.models import ExtractedEntities


class GraphBuilder:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        self._ensure_constraints()

    def close(self):
        self.driver.close()

    def _ensure_constraints(self):
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Equipment) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Regulation) REQUIRE r.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Personnel) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (pt:Permit) REQUIRE pt.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (wo:WorkOrder) REQUIRE wo.id IS UNIQUE",
            ]
            for c in constraints:
                try:
                    session.run(c)
                except Exception as e:
                    print(f"Constraint warning: {e}")

    def insert_entities(self, entities: ExtractedEntities):
        with self.driver.session() as session:
            for doc in entities.documents:
                session.run(
                    """MERGE (d:Document {id: $id})
                       SET d.title = $title, d.doc_type = $doc_type,
                           d.filename = $filename, d.file_type = $file_type,
                           d.upload_date = $upload_date, d.page_count = $page_count""",
                    id=doc.id, title=doc.title, doc_type=doc.doc_type,
                    filename=doc.filename, file_type=doc.file_type,
                    upload_date=doc.upload_date, page_count=doc.page_count
                )

            for eq in entities.equipment:
                session.run(
                    """MERGE (e:Equipment {id: $id})
                       SET e.name = $name, e.type = $equipment_type,
                           e.location = $location, e.criticality = $criticality""",
                    id=eq.id, name=eq.name, equipment_type=eq.equipment_type,
                    location=eq.location, criticality=eq.criticality
                )

            for reg in entities.regulations:
                session.run(
                    """MERGE (r:Regulation {id: $id})
                       SET r.title = $title, r.authority = $authority,
                           r.section = $section""",
                    id=reg.id, title=reg.title, authority=reg.authority,
                    section=reg.section
                )

            for per in entities.personnel:
                session.run(
                    """MERGE (p:Personnel {id: $id})
                       SET p.name = $name, p.role = $role""",
                    id=per.id, name=per.name, role=per.role
                )

            for inc in entities.incidents:
                session.run(
                    """MERGE (i:Incident {id: $id})
                       SET i.description = $description, i.date = $date,
                           i.severity = $severity""",
                    id=inc.id, description=inc.description,
                    date=inc.date, severity=inc.severity
                )

            for pt in entities.permits:
                session.run(
                    """MERGE (p:Permit {id: $id})
                       SET p.permit_type = $permit_type, p.status = $status""",
                    id=pt.id, permit_type=pt.permit_type, status=pt.status
                )

            for wo in entities.work_orders:
                session.run(
                    """MERGE (w:WorkOrder {id: $id})
                       SET w.wo_type = $wo_type, w.priority = $priority,
                           w.status = $status""",
                    id=wo.id, wo_type=wo.wo_type, priority=wo.priority,
                    status=wo.status
                )

            for rel in entities.relations:
                cypher = (
                    f"MATCH (a {{id: $source_id}}) "
                    f"MATCH (b {{id: $target_id}}) "
                    f"MERGE (a)-[r:{rel.relation_type}]->(b)"
                )
                try:
                    session.run(cypher, source_id=rel.source_id, target_id=rel.target_id)
                except Exception as e:
                    print(f"Relation error {rel.source_id} -> {rel.target_id}: {e}")

    def get_graph_summary(self) -> dict:
        with self.driver.session() as session:
            result = session.run(
                """MATCH (n)
                   RETURN labels(n)[0] AS label, count(*) AS count
                   ORDER BY count DESC"""
            )
            node_counts = {r["label"]: r["count"] for r in result}

            result2 = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            rel_count = result2.single()["count"]

            result3 = session.run(
                """MATCH (d:Document)
                   RETURN d.filename AS name, d.doc_type AS type
                   ORDER BY d.upload_date DESC LIMIT 20"""
            )
            docs = [{"name": r["name"], "type": r["type"]} for r in result3]

        return {
            "node_counts": node_counts,
            "relationship_count": rel_count,
            "recent_documents": docs,
        }

    def search_nodes(self, q: str, limit: int = 20) -> list[dict]:
        with self.driver.session() as session:
            result = session.run(
                """MATCH (n)
                   WHERE n.name CONTAINS $q
                      OR n.id CONTAINS $q
                      OR n.title CONTAINS $q
                      OR n.description CONTAINS $q
                   RETURN n.id AS id, labels(n)[0] AS label,
                          coalesce(n.name, n.title, n.description) AS display_name
                   LIMIT $limit""",
                q=q, limit=limit
            )
            return [
                {"id": r["id"], "label": r["label"], "name": r["display_name"]}
                for r in result
            ]

    def get_subgraph(self, node_id: str, depth: int = 2) -> dict:
        with self.driver.session() as session:
            result = session.run(
                f"""MATCH path = (n {{id: $node_id}})-[*1..{depth}]-(m)
                   UNWIND nodes(path) AS node
                   RETURN DISTINCT node.id AS id, labels(node)[0] AS label,
                          node {{.name, .title, .description, .type, .status}} AS props""",
                node_id=node_id
            )
            nodes_map = {}
            for r in result:
                nodes_map[r["id"]] = {
                    "id": r["id"],
                    "label": r["label"],
                    "properties": r["props"] or {},
                }

            result2 = session.run(
                f"""MATCH path = (n {{id: $node_id}})-[*1..{depth}]-(m)
                   UNWIND relationships(path) AS rel
                   RETURN DISTINCT type(rel) AS type,
                          startNode(rel).id AS source,
                          endNode(rel).id AS target""",
                node_id=node_id
            )
            rels = [
                {
                    "type": r["type"],
                    "source": r["source"],
                    "target": r["target"],
                    "properties": {},
                }
                for r in result2
            ]

        return {"nodes": list(nodes_map.values()), "relationships": rels}
