from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum

class FileType(str, Enum):
    SOURCE_CODE = "source_code"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    TEST = "test"
    ASSET = "asset"

class CodeFile(BaseModel):
    path: str
    content: str
    language: str
    size: int
    file_type: FileType

class TechnologyStack(BaseModel):
    languages: List[str]
    frameworks: List[str]
    libraries: List[str]
    tools: List[str]
    databases: List[str]

class CodeInsight(BaseModel):
    category: str  # "bug", "improvement", "architecture", "performance"
    severity: str  # "low", "medium", "high", "critical"
    description: str
    file_path: Optional[str]
    line_number: Optional[int]
    suggestion: str

class RepositoryAnalysis(BaseModel):
    repo_url: str
    summary: str
    tech_stack: TechnologyStack
    insights: List[CodeInsight]
    documentation_score: float
    code_quality_score: float
    maintainability_score: float
    trending_comparisons: List[str]
    recommendations: List[str]