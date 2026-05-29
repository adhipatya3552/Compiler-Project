from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ─── Stage 1: Intent ────────────────────────────────────────────────────────

class IntentOutput(BaseModel):
    app_name: str
    app_type: str                          # e.g. "CRM", "E-commerce", "Dashboard"
    core_features: List[str]
    user_roles: List[str]
    auth_required: bool
    payment_required: bool
    assumptions: List[str] = []            # when user was vague


# ─── Stage 2: System Design ──────────────────────────────────────────────────

class Entity(BaseModel):
    name: str
    fields: Dict[str, str]                 # field_name: data_type
    relations: List[str] = []             # e.g. ["User has many Orders"]

class Flow(BaseModel):
    name: str
    steps: List[str]

class SystemDesignOutput(BaseModel):
    entities: List[Entity]
    flows: List[Flow]
    roles: List[str]
    permissions: Dict[str, List[str]]      # role: [allowed actions]


# ─── Stage 3: Schema Generation ──────────────────────────────────────────────

class UIComponent(BaseModel):
    component_type: str                    # "form", "table", "card", "chart"
    fields: List[str] = []
    actions: List[str] = []

class UIPage(BaseModel):
    page_name: str
    route: str
    accessible_by: List[str]              # which roles
    components: List[UIComponent]

class APIEndpoint(BaseModel):
    method: str                           # GET, POST, PUT, DELETE
    path: str
    description: str
    request_body: Optional[Dict[str, str]] = None
    response: Any
    auth_required: bool
    roles_allowed: List[str]

class DBTable(BaseModel):
    table_name: str
    columns: Dict[str, str]               # col_name: type+constraints
    primary_key: str
    foreign_keys: List[str] = []

class AuthConfig(BaseModel):
    strategy: str                         # "JWT", "session", "OAuth"
    roles: List[str]
    role_hierarchy: Dict[str, int]        # role: level (higher = more access)
    protected_routes: List[str]

class SchemaOutput(BaseModel):
    ui: List[UIPage]
    api: List[APIEndpoint]
    database: List[DBTable]
    auth: AuthConfig


# ─── Stage 4: Refined Final Output ───────────────────────────────────────────

class ValidationIssue(BaseModel):
    layer: str                            # "ui", "api", "db", "auth"
    issue: str
    fixed: bool
    fix_description: Optional[str] = None

class FinalOutput(BaseModel):
    intent: IntentOutput
    system_design: SystemDesignOutput
    schema: SchemaOutput
    validation_issues: List[ValidationIssue] = []
    generation_metadata: Dict[str, Any] = {}


# ─── API Request/Response ─────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, description="User's app description")
    mode: str = Field("fast", description="Compilation mode: 'fast' or 'deep'")

class GenerateResponse(BaseModel):
    success: bool
    output: Optional[FinalOutput] = None
    error: Optional[str] = None
    retries: int = 0
    latency_ms: float = 0