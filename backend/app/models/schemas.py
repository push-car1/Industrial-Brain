from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    page_count: int
    chunk_count: int
    entity_count: int
    status: str
    message: str


class DocumentListItem(BaseModel):
    id: str
    filename: str
    file_type: str
    upload_date: str
    status: str
    entity_count: int


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    agent_trace: list[dict] = []
    conversation_id: str


class GraphNode(BaseModel):
    id: str
    labels: list[str]
    properties: dict


class GraphRelationship(BaseModel):
    id: str
    type: str
    source: str
    target: str
    properties: dict


class GraphExploreResponse(BaseModel):
    nodes: list[GraphNode]
    relationships: list[GraphRelationship]


class ComplianceCheckRequest(BaseModel):
    equipment_id: Optional[str] = None
    regulation_id: Optional[str] = None


class ComplianceGap(BaseModel):
    regulation: str
    requirement: str
    status: str
    details: str
    severity: str


class ComplianceReport(BaseModel):
    equipment_id: str
    gaps: list[ComplianceGap]
    overall_status: str
    coverage_percentage: float


class MaintenancePredictionRequest(BaseModel):
    equipment_id: str
    days_ahead: int = 30


class MaintenanceRecommendation(BaseModel):
    equipment_id: str
    equipment_name: str
    risk_level: str
    predicted_failure: str
    recommended_action: str
    probability: float
    estimated_remaining_life_days: Optional[int] = None


class RCARequest(BaseModel):
    incident_id: Optional[str] = None
    equipment_id: Optional[str] = None
    description: str


class RCAResponse(BaseModel):
    root_causes: list[str]
    contributing_factors: list[str]
    recommendations: list[str]
    similar_incidents: list[dict]


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict
