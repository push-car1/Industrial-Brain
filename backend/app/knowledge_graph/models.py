from pydantic import BaseModel, Field
from typing import Optional


class EquipmentEntity(BaseModel):
    id: str
    name: str
    equipment_type: str = "GENERAL"
    location: str = ""
    criticality: str = "MEDIUM"
    install_date: str = ""


class RegulationEntity(BaseModel):
    id: str
    title: str
    authority: str
    section: str = "General"
    requirement_text: str = ""


class PersonnelEntity(BaseModel):
    id: str
    name: str
    role: str = "Staff"
    certification: str = ""


class DocumentEntity(BaseModel):
    id: str
    title: str
    doc_type: str = "GENERAL"
    filename: str = ""
    file_type: str = ""
    upload_date: str = ""
    page_count: int = 0


class IncidentEntity(BaseModel):
    id: str
    description: str
    date: str = ""
    severity: str = "MEDIUM"
    root_cause: str = ""


class PermitEntity(BaseModel):
    id: str
    permit_type: str = "GENERAL"
    status: str = "ACTIVE"
    issued_date: str = ""
    expiry_date: str = ""


class WorkOrderEntity(BaseModel):
    id: str
    wo_type: str = "CORRECTIVE"
    priority: str = "MEDIUM"
    status: str = "OPEN"
    created_date: str = ""
    description: str = ""


class ParameterEntity(BaseModel):
    id: str
    name: str
    value: str = ""
    unit: str = ""
    range_min: str = ""
    range_max: str = ""
    alarm_threshold: str = ""


class EntityRelation(BaseModel):
    source_id: str
    target_id: str
    relation_type: str


class ExtractedEntities(BaseModel):
    doc_id: str
    equipment: list[EquipmentEntity] = []
    regulations: list[RegulationEntity] = []
    personnel: list[PersonnelEntity] = []
    documents: list[DocumentEntity] = []
    incidents: list[IncidentEntity] = []
    permits: list[PermitEntity] = []
    work_orders: list[WorkOrderEntity] = []
    parameters: list[ParameterEntity] = []
    relations: list[EntityRelation] = []
