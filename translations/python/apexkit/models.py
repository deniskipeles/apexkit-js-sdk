from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union

@dataclass
class Scope:
    type: str  # 'root' | 'tenant' | 'sandbox'
    id: str

@dataclass
class User:
    id: str
    email: str
    role: str
    scope: str
    metadata: Optional[Dict[str, Any]] = None
    last_active: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuthResponse:
    token: str
    user: User

@dataclass
class BaseRecord:
    id: str
    created: str
    updated: str
    data: Dict[str, Any]
    expand: Dict[str, Any]
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ListResult:
    items: List[Any]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None

@dataclass
class SchemaField:
    name: str
    type: str
    required: bool
    unique: Optional[bool] = None
    options: Optional[List[str]] = None
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Collection:
    id: str
    name: str
    type: str
    schema: Dict[str, Any]
    created: str
    updated: str

@dataclass
class StoredFile:
    id: str
    filename: str
    original_name: str
    mime_type: str
    size: int
    url: str
    created_at: str

@dataclass
class InstantResult:
    id: int
    score: float
    snippet: Dict[str, Any]

@dataclass
class Script:
    id: str
    name: str
    trigger_type: str
    code: str
    active: bool
    target_collection: Optional[str] = None

@dataclass
class Template:
    id: str
    slug: str
    content: str
    script_id: Optional[str] = None

@dataclass
class AiAction:
    id: str
    slug: str
    name: str
    model: str
    system_prompt: Optional[str] = None
    template: str
    config: Optional[Any] = None

@dataclass
class AiSession:
    id: str
    name: str
    messages: List[Dict[str, str]]
    current_manifest: Optional[Any] = None
    diff_summary: Optional[str] = None
    last_error: Optional[str] = None
    created_at: str

@dataclass
class Plugin:
    id: str
    name: str
    version: str
    description: Optional[str] = None
    manifest: Any
    created_at: str

@dataclass
class ApiKey:
    id: str
    name: str
    prefix: str
    role: str
    scope: str
    bypass_cors: bool
    created_at: str

@dataclass
class SystemLog:
    id: str
    level: str  # 'info' | 'warning' | 'error' | 'success'
    message: str
    source: str
    timestamp: str
    meta: Optional[Any] = None

@dataclass
class SiteFile:
    path: str
    size: int
