from dataclasses import dataclass, field
from typing import Any, Literal

ElementType = Literal["heading", "paragraph", "table"]

@dataclass
class Element:
    # Represents a single extracted element from a document, such as a heading, paragraph, or table.
    text: str
    element_type: ElementType
    level: int = 0
    section_path: list[str] = field(default_factory=list)
    location: dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentBlock:
    # Final RAG-ready chunk.
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)