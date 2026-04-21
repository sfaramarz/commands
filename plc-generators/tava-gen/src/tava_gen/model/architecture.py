"""Architecture model — components, connections, dataflows, and trust boundaries.

This is the intermediate representation that the analyzer produces
and that the generators consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ComponentType(Enum):
    """Classification of an architecture component."""

    SERVICE = "service"
    DATABASE = "database"
    QUEUE = "queue"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    LIBRARY = "library"
    UI = "ui"
    GATEWAY = "gateway"
    STORAGE = "storage"
    UNKNOWN = "unknown"


@dataclass
class Component:
    """A deployable component in the architecture."""

    id: str
    name: str
    component_type: ComponentType = ComponentType.UNKNOWN
    description: str = ""
    language: str = ""
    source_path: str = ""
    security_notes: list[str] = field(default_factory=list)


@dataclass
class Connection:
    """A directed connection between two components."""

    source_id: str
    target_id: str
    protocol: str = ""
    description: str = ""
    data_classification: str = ""
    is_encrypted: bool | None = None
    port: int | None = None


@dataclass
class TrustBoundary:
    """A trust boundary grouping components."""

    id: str
    name: str
    component_ids: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class DataFlow:
    """A named data flow across components."""

    id: str
    name: str
    connection_ids: list[str] = field(default_factory=list)
    data_types: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ArchitectureModel:
    """Complete architecture model for a project."""

    project_name: str = ""
    description: str = ""
    components: list[Component] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    trust_boundaries: list[TrustBoundary] = field(default_factory=list)
    data_flows: list[DataFlow] = field(default_factory=list)

    def get_component(self, component_id: str) -> Component | None:
        for c in self.components:
            if c.id == component_id:
                return c
        return None

    def add_component(self, component: Component) -> None:
        if not self.get_component(component.id):
            self.components.append(component)

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)

    def add_trust_boundary(self, boundary: TrustBoundary) -> None:
        self.trust_boundaries.append(boundary)
