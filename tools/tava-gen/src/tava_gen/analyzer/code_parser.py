"""Source code analyzer — parses a project into an ArchitectureModel.

Scans a source tree for structural signals (config files, imports,
service definitions, database connections, API endpoints, etc.) and
builds an intermediate ArchitectureModel.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from tava_gen.model.architecture import (
    ArchitectureModel,
    Component,
    ComponentType,
    Connection,
)


# ---------------------------------------------------------------------------
# Heuristic detectors
# ---------------------------------------------------------------------------

_DOCKER_COMPOSE_NAMES = {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}
_DOCKERFILE_NAMES = {"Dockerfile"}


def _detect_components_from_docker_compose(path: Path) -> list[Component]:
    """Extract service components from a Docker Compose file."""
    components: list[Component] = []
    try:
        import yaml  # optional dependency

        with open(path) as f:
            data = yaml.safe_load(f)
        services = data.get("services", {})
        for name, svc in services.items():
            comp_type = _guess_type_from_image(svc.get("image", ""))
            components.append(
                Component(
                    id=f"svc_{name}",
                    name=name,
                    component_type=comp_type,
                    description=f"Docker Compose service: {name}",
                    source_path=str(path),
                )
            )
    except ImportError:
        # yaml not installed — fall back to regex scanning
        text = path.read_text(errors="ignore")
        in_services = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "services:":
                in_services = True
                continue
            if in_services and re.match(r"^[a-zA-Z_][\w-]*:$", stripped):
                name = stripped.rstrip(":")
                components.append(
                    Component(
                        id=f"svc_{name}",
                        name=name,
                        component_type=ComponentType.SERVICE,
                        description=f"Docker Compose service: {name}",
                        source_path=str(path),
                    )
                )
            elif in_services and not line.startswith(" ") and stripped:
                in_services = False
    except Exception:
        pass
    return components


def _detect_components_from_package_json(path: Path) -> list[Component]:
    """Detect a Node.js service from package.json."""
    try:
        data = json.loads(path.read_text(errors="ignore"))
        name = data.get("name", path.parent.name)
        desc = data.get("description", "")
        return [
            Component(
                id=f"node_{name}",
                name=name,
                component_type=ComponentType.SERVICE,
                description=desc or f"Node.js project: {name}",
                language="javascript/typescript",
                source_path=str(path.parent),
            )
        ]
    except Exception:
        return []


def _detect_components_from_pyproject(path: Path) -> list[Component]:
    """Detect a Python service/library from pyproject.toml."""
    text = path.read_text(errors="ignore")
    name_match = re.search(r'name\s*=\s*"([^"]+)"', text)
    name = name_match.group(1) if name_match else path.parent.name
    desc_match = re.search(r'description\s*=\s*"([^"]+)"', text)
    desc = desc_match.group(1) if desc_match else ""
    return [
        Component(
            id=f"py_{name}",
            name=name,
            component_type=ComponentType.SERVICE,
            description=desc or f"Python project: {name}",
            language="python",
            source_path=str(path.parent),
        )
    ]


def _detect_connections_from_source(
    root: Path, components: list[Component]
) -> list[Connection]:
    """Scan source files for connection patterns (DB URIs, HTTP calls, etc.)."""
    connections: list[Connection] = []
    seen: set[tuple[str, str, str]] = set()
    component_id = components[0].id if components else "main"

    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith((".py", ".ts", ".js", ".go", ".java", ".yaml", ".yml", ".toml", ".env")):
                continue
            fpath = Path(dirpath) / fname
            try:
                text = fpath.read_text(errors="ignore")
            except Exception:
                continue

            # Database connections
            for pattern, proto, comp_type in [
                (r"postgres(?:ql)?://", "postgresql", ComponentType.DATABASE),
                (r"mysql://", "mysql", ComponentType.DATABASE),
                (r"mongodb(?:\+srv)?://", "mongodb", ComponentType.DATABASE),
                (r"redis://", "redis", ComponentType.CACHE),
                (r"amqp://", "amqp", ComponentType.QUEUE),
                (r"kafka://|bootstrap[._]servers", "kafka", ComponentType.QUEUE),
            ]:
                if re.search(pattern, text, re.IGNORECASE):
                    key = (component_id, proto, comp_type.value)
                    if key not in seen:
                        seen.add(key)
                        ext_id = f"ext_{proto}"
                        # Add the external component if not present
                        if not any(c.id == ext_id for c in components):
                            components.append(
                                Component(
                                    id=ext_id,
                                    name=proto.title(),
                                    component_type=comp_type,
                                    description=f"External {proto} dependency",
                                )
                            )
                        connections.append(
                            Connection(
                                source_id=component_id,
                                target_id=ext_id,
                                protocol=proto,
                                description=f"{proto} connection detected in {fname}",
                            )
                        )

            # HTTP/API calls
            if re.search(r"https?://[^\s\"']+", text):
                key = (component_id, "https", "external_api")
                if key not in seen:
                    seen.add(key)
                    ext_id = "ext_http_api"
                    if not any(c.id == ext_id for c in components):
                        components.append(
                            Component(
                                id=ext_id,
                                name="External HTTP APIs",
                                component_type=ComponentType.EXTERNAL_API,
                                description="External HTTP/HTTPS API dependencies",
                            )
                        )
                    connections.append(
                        Connection(
                            source_id=component_id,
                            target_id=ext_id,
                            protocol="https",
                            description=f"HTTP API call detected in {fname}",
                        )
                    )

    return connections


def _guess_type_from_image(image: str) -> ComponentType:
    """Guess component type from a Docker image name."""
    image_lower = image.lower()
    if any(db in image_lower for db in ("postgres", "mysql", "mariadb", "mongo", "sqlite")):
        return ComponentType.DATABASE
    if any(q in image_lower for q in ("rabbitmq", "kafka", "nats", "redis")):
        return ComponentType.QUEUE
    if "redis" in image_lower:
        return ComponentType.CACHE
    if any(gw in image_lower for gw in ("nginx", "traefik", "envoy", "haproxy")):
        return ComponentType.GATEWAY
    return ComponentType.SERVICE


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze_project(project_path: str | Path) -> ArchitectureModel:
    """Analyze a source project and return an ArchitectureModel.

    Parameters
    ----------
    project_path:
        Path to the root of the source project to analyze.

    Returns
    -------
    ArchitectureModel
        Populated model with detected components and connections.
    """
    root = Path(project_path).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Project path does not exist: {root}")

    model = ArchitectureModel(
        project_name=root.name,
        description=f"Architecture model for {root.name}",
    )

    # Walk top-level files for config-based detection
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        name = item.name.lower()

        if name in {n.lower() for n in _DOCKER_COMPOSE_NAMES}:
            for comp in _detect_components_from_docker_compose(item):
                model.add_component(comp)

        elif name == "package.json" and "node_modules" not in str(item):
            for comp in _detect_components_from_package_json(item):
                model.add_component(comp)

        elif name == "pyproject.toml":
            for comp in _detect_components_from_pyproject(item):
                model.add_component(comp)

    # If no components found, create a default one from the project root
    if not model.components:
        model.add_component(
            Component(
                id=f"proj_{root.name}",
                name=root.name,
                component_type=ComponentType.SERVICE,
                description=f"Main project: {root.name}",
                source_path=str(root),
            )
        )

    # Detect connections from source code
    conns = _detect_connections_from_source(root, model.components)
    for conn in conns:
        model.add_connection(conn)

    return model
