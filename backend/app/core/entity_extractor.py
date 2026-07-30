import re
from typing import Optional
from app.knowledge_graph.models import (
    DocumentEntity, EquipmentEntity, RegulationEntity,
    PersonnelEntity, IncidentEntity, PermitEntity, WorkOrderEntity,
    ExtractedEntities, EntityRelation
)
from app.utils.helpers import (
    EQUIPMENT_TYPE_KEYWORDS, DOCUMENT_TYPE_KEYWORDS,
    REGULATORY_KEYWORDS, generate_id
)


class EntityExtractor:
    def __init__(self, llm=None):
        self.llm = llm

    def extract_all(
        self,
        text: str,
        doc_id: str,
        filename: str,
        file_type: str
    ) -> ExtractedEntities:
        entities = ExtractedEntities(doc_id=doc_id)

        doc_entity = self._extract_document(text, doc_id, filename, file_type)
        entities.documents.append(doc_entity)

        equipment = self._extract_equipment(text, doc_id)
        entities.equipment.extend(equipment)

        regulations = self._extract_regulations(text, doc_id)
        entities.regulations.extend(regulations)

        personnel = self._extract_personnel(text, doc_id)
        entities.personnel.extend(personnel)

        incidents = self._extract_incidents(text, doc_id)
        entities.incidents.extend(incidents)

        permits = self._extract_permits(text, doc_id)
        entities.permits.extend(permits)

        work_orders = self._extract_work_orders(text, doc_id)
        entities.work_orders.extend(work_orders)

        relations = self._build_relations(entities)
        entities.relations.extend(relations)

        if self.llm:
            try:
                llm_entities = self._extract_with_llm(text, doc_id)
                entities = self._merge_entities(entities, llm_entities)
            except Exception as e:
                print(f"LLM extraction error (non-fatal): {e}")

        return entities

    def _extract_document(
        self, text: str, doc_id: str, filename: str, file_type: str
    ) -> DocumentEntity:
        doc_type = "GENERAL"
        text_lower = text.lower()
        for keyword, dtype in DOCUMENT_TYPE_KEYWORDS.items():
            if keyword in text_lower:
                doc_type = dtype
                break

        title = filename
        title_match = re.search(r"^(?:# |Title:?\s*)(.+?)$", text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        return DocumentEntity(
            id=doc_id,
            title=title,
            doc_type=doc_type,
            filename=filename,
            file_type=file_type,
        )

    def _extract_equipment(self, text: str, doc_id: str) -> list[EquipmentEntity]:
        equipment_list = []
        seen_ids = set()
        lines = text.split("\n")
        for line in lines:
            line_lower = line.lower().strip()
            for keyword in EQUIPMENT_TYPE_KEYWORDS:
                if keyword in line_lower:
                    tag_match = re.search(
                        r"([A-Z0-9][A-Z0-9_-]{2,20}(?:[-_]\d{2,4})?)",
                        line
                    )
                    equip_id = tag_match.group(1) if tag_match else generate_id("eq")
                    if equip_id in seen_ids:
                        continue
                    seen_ids.add(equip_id)
                    name = line.strip()[:80]
                    equipment_list.append(
                        EquipmentEntity(
                            id=equip_id,
                            name=name,
                            equipment_type=keyword.title(),
                            location=self._extract_location(line),
                        )
                    )
                    break
        return equipment_list

    def _extract_regulations(self, text: str, doc_id: str) -> list[RegulationEntity]:
        regulations = []
        seen = set()
        text_lower = text.lower()
        for keyword, authority in REGULATORY_KEYWORDS.items():
            if keyword in text_lower:
                if authority in seen:
                    continue
                seen.add(authority)
                section_match = re.search(
                    rf"{re.escape(keyword)}[\s:]*([A-Za-z0-9\s.-]{{2,30}})",
                    text,
                    re.IGNORECASE
                )
                section = section_match.group(1).strip() if section_match else "General"
                regulations.append(
                    RegulationEntity(
                        id=generate_id("reg"),
                        title=f"{authority} - {section}",
                        authority=authority,
                        section=section,
                    )
                )
        return regulations

    def _extract_personnel(self, text: str, doc_id: str) -> list[PersonnelEntity]:
        personnel = []
        seen_names = set()
        patterns = [
            r"(?:issued by|approved by|prepared by|reviewed by|inspected by):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"(?:name|operator|engineer|technician|manager):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"(?:signature|authorized by):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                if name not in seen_names:
                    seen_names.add(name)
                    role_match = re.search(
                        rf"{re.escape(name)}.*?(operator|engineer|technician|manager|supervisor|inspector)",
                        text,
                        re.IGNORECASE
                    )
                    role = role_match.group(1).title() if role_match else "Staff"
                    personnel.append(
                        PersonnelEntity(
                            id=generate_id("per"),
                            name=name,
                            role=role,
                        )
                    )
        return personnel

    def _extract_incidents(self, text: str, doc_id: str) -> list[IncidentEntity]:
        incidents = []
        incident_sections = re.split(
            r"(?=Incident(?:.?Report|.?ID|.?#|\s*\d+)|Near.?Miss(?:.?Report)?)",
            text,
            flags=re.IGNORECASE
        )
        for section in incident_sections[1:]:
            section_short = section[:500]
            desc_match = re.search(
                r"(?:description|incident|event|hazard):\s*(.+?)(?:\n|$)",
                section_short,
                re.IGNORECASE
            )
            description = desc_match.group(1).strip() if desc_match else section_short[:100]

            date_match = re.search(
                r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{2}[-/]\d{2})",
                section_short
            )
            date = date_match.group(1) if date_match else ""

            sev_match = re.search(
                r"(?:severity|impact):\s*(high|medium|low|critical|minor)",
                section_short,
                re.IGNORECASE
            )
            severity = sev_match.group(1).upper() if sev_match else "MEDIUM"

            incidents.append(
                IncidentEntity(
                    id=generate_id("inc"),
                    description=description[:200],
                    date=date,
                    severity=severity,
                )
            )
        return incidents

    def _extract_permits(self, text: str, doc_id: str) -> list[PermitEntity]:
        permits = []
        permit_patterns = re.split(
            r"(?=Permit(?:.?to.?Work|.?ID|.?#|\s*\d+)|Work.?Permit|PTW)",
            text,
            flags=re.IGNORECASE
        )
        for section in permit_patterns[1:]:
            section_short = section[:300]
            ptype = "GENERAL"
            for pt in ["hot work", "confined space", "height work", "electrical", "excavation", "cold work"]:
                if pt in section_short.lower():
                    ptype = pt.upper().replace(" ", "_")
                    break
            id_match = re.search(r"(?:ID|#|No)[.:\s]*([A-Z0-9-]{4,15})", section_short)
            pid = id_match.group(1) if id_match else generate_id("ptw")
            permits.append(
                PermitEntity(
                    id=pid,
                    permit_type=ptype,
                    status="ACTIVE",
                )
            )
        return permits

    def _extract_work_orders(self, text: str, doc_id: str) -> list[WorkOrderEntity]:
        work_orders = []
        wo_patterns = re.split(
            r"(?=Work.?Order|WO[\s:#]|Maintenance.?Order)",
            text,
            flags=re.IGNORECASE
        )
        for section in wo_patterns[1:]:
            section_short = section[:300]
            wo_match = re.search(r"(?:WO|Order|ID|#)[:\s]*([A-Z0-9-]{4,15})", section_short)
            wo_id = wo_match.group(1) if wo_match else generate_id("wo")

            wo_type = "CORRECTIVE"
            if "preventive" in section_short.lower() or "planned" in section_short.lower():
                wo_type = "PREVENTIVE"
            elif "predictive" in section_short.lower():
                wo_type = "PREDICTIVE"

            priority = "MEDIUM"
            if "critical" in section_short.lower() or "emergency" in section_short.lower():
                priority = "CRITICAL"
            elif "low" in section_short.lower():
                priority = "LOW"

            work_orders.append(
                WorkOrderEntity(
                    id=wo_id,
                    wo_type=wo_type,
                    priority=priority,
                    status="OPEN",
                )
            )
        return work_orders

    def _extract_location(self, line: str) -> str:
        area_match = re.search(
            r"(?:area|zone|location|section|unit)\s*[:\s]*([A-Za-z0-9\s-]{2,20})",
            line,
            re.IGNORECASE
        )
        if area_match:
            return area_match.group(1).strip()
        building_match = re.search(
            r"(?:building|floor|bay|block)\s*[:\s]*([A-Za-z0-9\s-]{2,20})",
            line,
            re.IGNORECASE
        )
        if building_match:
            return building_match.group(1).strip()
        return ""

    def _build_relations(self, entities: ExtractedEntities) -> list[EntityRelation]:
        relations = []
        doc_id = entities.doc_id

        for eq in entities.equipment:
            relations.append(
                EntityRelation(
                    source_id=doc_id,
                    target_id=eq.id,
                    relation_type="REFERENCES",
                )
            )

        for reg in entities.regulations:
            relations.append(
                EntityRelation(
                    source_id=doc_id,
                    target_id=reg.id,
                    relation_type="REFERENCES",
                )
            )
            relations.append(
                EntityRelation(
                    source_id=doc_id,
                    target_id=reg.id,
                    relation_type="CITES",
                )
            )

        for inc in entities.incidents:
            relations.append(
                EntityRelation(
                    source_id=inc.id,
                    target_id=doc_id,
                    relation_type="REPORTED_IN",
                )
            )

        for wo in entities.work_orders:
            for eq in entities.equipment:
                relations.append(
                    EntityRelation(
                        source_id=wo.id,
                        target_id=eq.id,
                        relation_type="MAINTAINS",
                    )
                )

        return relations

    def _extract_with_llm(self, text: str, doc_id: str) -> ExtractedEntities:
        if not self.llm:
            return ExtractedEntities(doc_id=doc_id)

        from langchain_core.prompts import ChatPromptTemplate
        from app.knowledge_graph.models import ExtractedEntities

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an industrial knowledge extraction AI. 
Extract the following entities from the given industrial document text:

1. **Equipment**: Any machinery, tools, or assets mentioned (pumps, compressors, tanks, valves, etc.)
2. **Regulations**: Any regulatory standards referenced (OISD, Factory Act, ISO, etc.)
3. **Personnel**: Names of people with roles
4. **Incidents**: Any accidents, near-misses, or safety events
5. **Permits**: Any work permits mentioned
6. **Work Orders**: Any maintenance work orders

Return ONLY a JSON object with the extracted entities. Follow the schema exactly.
For each entity, use the following format:
{{
  "equipment": [{{"id": "EQ-001", "name": "Boiler B-101", "equipment_type": "Boiler", "location": "Unit 2"}}],
  "regulations": [{{"id": "REG-001", "title": "OISD - Fire Protection", "authority": "OISD", "section": "Fire Protection"}}],
  "personnel": [{{"id": "PER-001", "name": "Rajesh Kumar", "role": "Safety Officer"}}],
  "incidents": [{{"id": "INC-001", "description": "Gas leak detected", "date": "2025-01-15", "severity": "HIGH"}}],
  "permits": [{{"id": "PTW-001", "permit_type": "HOT_WORK", "status": "ACTIVE"}}],
  "work_orders": [{{"id": "WO-001", "wo_type": "PREVENTIVE", "priority": "MEDIUM", "status": "OPEN"}}]
}}

Skip entity types that are not present in the text. Use null for unknown fields.
Do NOT include markdown formatting or code blocks in your response - ONLY valid JSON."""),
            ("human", "Document text:\n\n{text}")
        ])

        chain = prompt | self.llm
        try:
            response = chain.invoke({"text": text[:3000]})
            content = response.content if hasattr(response, 'content') else str(response)
            import json
            data = json.loads(content)
            return self._dict_to_entities(data, doc_id)
        except Exception as e:
            print(f"LLM extraction parsing error: {e}")
            return ExtractedEntities(doc_id=doc_id)

    def _dict_to_entities(self, data: dict, doc_id: str) -> ExtractedEntities:
        entities = ExtractedEntities(doc_id=doc_id)
        for eq in data.get("equipment", []):
            entities.equipment.append(EquipmentEntity(**eq))
        for reg in data.get("regulations", []):
            entities.regulations.append(RegulationEntity(**reg))
        for per in data.get("personnel", []):
            entities.personnel.append(PersonnelEntity(**per))
        for inc in data.get("incidents", []):
            entities.incidents.append(IncidentEntity(**inc))
        for pt in data.get("permits", []):
            entities.permits.append(PermitEntity(**pt))
        for wo in data.get("work_orders", []):
            entities.work_orders.append(WorkOrderEntity(**wo))
        return entities

    def _merge_entities(
        self, base: ExtractedEntities, llm: ExtractedEntities
    ) -> ExtractedEntities:
        base_equip_ids = {e.id for e in base.equipment}
        for eq in llm.equipment:
            if eq.id not in base_equip_ids:
                base.equipment.append(eq)
                base_equip_ids.add(eq.id)

        base_reg_ids = {r.id for r in base.regulations}
        for reg in llm.regulations:
            if reg.id not in base_reg_ids:
                base.regulations.append(reg)
                base_reg_ids.add(reg.id)

        base_per_ids = {p.id for p in base.personnel}
        for per in llm.personnel:
            if per.id not in base_per_ids:
                base.personnel.append(per)
                base_per_ids.add(per.id)

        base_inc_ids = {i.id for i in base.incidents}
        for inc in llm.incidents:
            if inc.id not in base_inc_ids:
                base.incidents.append(inc)
                base_inc_ids.add(inc.id)

        return base
