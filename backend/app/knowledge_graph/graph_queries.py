from typing import Optional
from app.knowledge_graph.graph_builder import GraphBuilder


class GraphQueries:
    def __init__(self, builder: GraphBuilder):
        self.builder = builder

    def get_equipment_with_documents(self, equipment_id: Optional[str] = None) -> list[dict]:
        with self.builder.driver.session() as session:
            if equipment_id:
                result = session.run(
                    """MATCH (e:Equipment {id: $eid})<-[:REFERENCES]-(d:Document)
                       RETURN e.id AS equipment_id, e.name AS equipment_name,
                              collect(DISTINCT {id: d.id, title: d.title, type: d.doc_type}) AS documents""",
                    eid=equipment_id
                )
            else:
                result = session.run(
                    """MATCH (e:Equipment)<-[:REFERENCES]-(d:Document)
                       RETURN e.id AS equipment_id, e.name AS equipment_name,
                              collect(DISTINCT {id: d.id, title: d.title, type: d.doc_type}) AS documents
                       LIMIT 50"""
                )
            return [r.data() for r in result]

    def get_active_permits_for_equipment(self, equipment_id: str) -> list[dict]:
        with self.builder.driver.session() as session:
            result = session.run(
                """MATCH (e:Equipment {id: $eid})<-[r:AUTHORIZES_WORK_ON]-(p:Permit)
                   WHERE p.status = 'ACTIVE'
                   RETURN p.id AS permit_id, p.permit_type AS permit_type,
                          p.status AS status, e.id AS equipment_id, e.name AS equipment_name""",
                eid=equipment_id
            )
            return [r.data() for r in result]

    def get_incidents_for_equipment(self, equipment_id: str) -> list[dict]:
        with self.builder.driver.session() as session:
            result = session.run(
                """MATCH (i:Incident)-[:INVOLVES]->(e:Equipment {id: $eid})
                   RETURN i.id AS incident_id, i.description AS description,
                          i.date AS date, i.severity AS severity,
                          i.root_cause AS root_cause
                   ORDER BY i.date DESC""",
                eid=equipment_id
            )
            return [r.data() for r in result]

    def get_work_orders_for_equipment(self, equipment_id: str) -> list[dict]:
        with self.builder.driver.session() as session:
            result = session.run(
                """MATCH (w:WorkOrder)-[:MAINTAINS]->(e:Equipment {id: $eid})
                   RETURN w.id AS work_order_id, w.wo_type AS wo_type,
                          w.priority AS priority, w.status AS status,
                          w.description AS description, w.created_date AS created_date
                   ORDER BY w.created_date DESC""",
                eid=equipment_id
            )
            return [r.data() for r in result]

    def get_equipment_by_regulation(self, regulation_id: str) -> list[dict]:
        with self.builder.driver.session() as session:
            result = session.run(
                """MATCH (r:Regulation {id: $rid})<-[:CITES]-(d:Document)
                   OPTIONAL MATCH (d)-[:REFERENCES]->(e:Equipment)
                   RETURN r.title AS regulation, d.id AS doc_id, d.title AS doc_title,
                          collect(DISTINCT {id: e.id, name: e.name}) AS equipment""",
                rid=regulation_id
            )
            return [r.data() for r in result]

    def find_equipment_without_documents(self) -> list[dict]:
        with self.builder.driver.session() as session:
            result = session.run(
                """MATCH (e:Equipment)
                   WHERE NOT EXISTS { (e)<-[:REFERENCES]-() }
                   RETURN e.id AS id, e.name AS name, e.type AS type
                   LIMIT 20"""
            )
            return [r.data() for r in result]

    def find_simultaneous_permit_conflicts(self) -> list[dict]:
        with self.builder.driver.session() as session:
            result = session.run(
                """MATCH (e:Equipment)<-[:AUTHORIZES_WORK_ON]-(p1:Permit),
                          (e)<-[:AUTHORIZES_WORK_ON]-(p2:Permit)
                   WHERE p1.status = 'ACTIVE' AND p2.status = 'ACTIVE'
                         AND p1.id <> p2.id
                         AND p1.permit_type <> p2.permit_type
                   RETURN e.id AS equipment_id, e.name AS equipment_name,
                          collect(DISTINCT p1.permit_type) AS permit_types
                   LIMIT 20"""
            )
            return [r.data() for r in result]

    def get_all_equipment(self) -> list[dict]:
        with self.builder.driver.session() as session:
            result = session.run(
                """MATCH (e:Equipment)
                   RETURN e.id AS id, e.name AS name, e.type AS type,
                          e.location AS location, e.criticality AS criticality
                   ORDER BY e.name"""
            )
            return [r.data() for r in result]

    def get_all_regulations(self) -> list[dict]:
        with self.builder.driver.session() as session:
            result = session.run(
                """MATCH (r:Regulation)
                   RETURN r.id AS id, r.title AS title, r.authority AS authority
                   ORDER BY r.title"""
            )
            return [r.data() for r in result]

    def search(self, query_text: str, limit: int = 20) -> list[dict]:
        with self.builder.driver.session() as session:
            try:
                result = session.run(
                    """CALL db.index.fulltext.queryNodes('entity_text_index', $q)
                       YIELD node, score
                       RETURN node.id AS id, labels(node)[0] AS label,
                              coalesce(node.name, node.title, node.description) AS name,
                              score
                       LIMIT $limit""",
                    q=query_text, limit=limit
                )
                items = [r.data() for r in result]
                if items:
                    return items
            except Exception:
                pass

            result = session.run(
                """MATCH (n)
                   WHERE n.name CONTAINS $q
                      OR n.title CONTAINS $q
                      OR n.description CONTAINS $q
                      OR n.id CONTAINS $q
                   RETURN n.id AS id, labels(n)[0] AS label,
                          coalesce(n.name, n.title, n.description) AS name,
                          1.0 AS score
                   LIMIT $limit""",
                q=query_text, limit=limit
            )
            return [r.data() for r in result]
