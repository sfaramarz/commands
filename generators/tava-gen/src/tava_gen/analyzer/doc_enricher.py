"""Document-based enrichment — extracts architecture signals from text sources.

Parses Confluence pages, Slack discussions, and GRT data to enrich
an ArchitectureModel with components, connections, and descriptions
that aren't visible from source code alone.
"""

from __future__ import annotations

import re

from tava_gen.model.architecture import (
    ArchitectureModel,
    Component,
    ComponentType,
    Connection,
    TrustBoundary,
)
from tava_gen.sources import SourceBundle


# ---------------------------------------------------------------------------
# Text-based component detection
# ---------------------------------------------------------------------------

# Common architecture component keywords and their likely types
_COMPONENT_KEYWORDS: list[tuple[str, ComponentType]] = [
    (r"(?i)\b(api\s*gateway|load\s*balancer|reverse\s*proxy|ingress)\b", ComponentType.GATEWAY),
    (r"(?i)\b(postgres(?:ql)?|mysql|mariadb|oracle\s*db|sql\s*server|cockroachdb)\b", ComponentType.DATABASE),
    (r"(?i)\b(mongodb|dynamodb|cassandra|couchdb|firestore)\b", ComponentType.DATABASE),
    (r"(?i)\b(redis|memcached|elasticache)\b", ComponentType.CACHE),
    (r"(?i)\b(rabbitmq|kafka|nats|pulsar|sqs|sns|event\s*hub)\b", ComponentType.QUEUE),
    (r"(?i)\b(s3|blob\s*storage|minio|gcs|azure\s*storage|nfs)\b", ComponentType.STORAGE),
    (r"(?i)\b(react|angular|vue|svelte|next\.?js|nuxt)\s*(app|frontend|ui|client)\b", ComponentType.UI),
    (r"(?i)\b(nginx|traefik|envoy|haproxy|istio)\b", ComponentType.GATEWAY),
    (r"(?i)\b(ldap|active\s*directory|okta|keycloak|auth0)\b", ComponentType.EXTERNAL_API),
]

# Connection/protocol patterns in documentation
_PROTOCOL_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)\b(grpc)\b", "gRPC"),
    (r"(?i)\b(rest\s*api|restful)\b", "REST"),
    (r"(?i)\b(graphql)\b", "GraphQL"),
    (r"(?i)\b(websocket|wss?://)\b", "WebSocket"),
    (r"(?i)\b(mqtt)\b", "MQTT"),
    (r"(?i)\b(amqp)\b", "AMQP"),
    (r"(?i)\b(tcp|udp)\b", "TCP/UDP"),
    (r"(?i)\b(tls|ssl|https)\b", "TLS/HTTPS"),
]

# Security-relevant observations from docs
_SECURITY_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)\b(authentication|authn|oauth|oidc|saml|jwt)\b", "Authentication mechanism referenced"),
    (r"(?i)\b(authorization|authz|rbac|abac|acl|permissions)\b", "Authorization/access control referenced"),
    (r"(?i)\b(encrypt(?:ion|ed)?|aes|rsa|tls|ssl|at[- ]rest)\b", "Encryption referenced"),
    (r"(?i)\b(pii|personally\s*identifiable|gdpr|hipaa|ccpa)\b", "PII/privacy compliance referenced"),
    (r"(?i)\b(secrets?\s*manag|vault|kms|key\s*management)\b", "Secrets management referenced"),
    (r"(?i)\b(audit\s*log|logging|tracing|observability)\b", "Audit/logging referenced"),
    (r"(?i)\b(firewall|network\s*policy|security\s*group|waf)\b", "Network security controls referenced"),
]


def _make_id(text: str) -> str:
    """Create a safe ID from text."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


def enrich_from_sources(
    model: ArchitectureModel,
    bundle: SourceBundle,
) -> None:
    """Enrich an ArchitectureModel with information extracted from text sources.

    Modifies the model in-place.
    """
    all_text = bundle.all_text
    if not all_text:
        return

    _extract_components(model, all_text)
    _extract_connections(model, all_text)
    _extract_security_notes(model, all_text)
    _extract_description(model, bundle)


def _extract_components(model: ArchitectureModel, text: str) -> None:
    """Detect components mentioned in documentation text."""
    for pattern, comp_type in _COMPONENT_KEYWORDS:
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            comp_id = f"doc_{_make_id(name)}"
            if not model.get_component(comp_id):
                model.add_component(
                    Component(
                        id=comp_id,
                        name=name,
                        component_type=comp_type,
                        description=f"Referenced in documentation",
                    )
                )


def _extract_connections(model: ArchitectureModel, text: str) -> None:
    """Detect connection protocols mentioned in documentation."""
    detected_protocols: list[str] = []
    for pattern, proto_name in _PROTOCOL_PATTERNS:
        if re.search(pattern, text):
            detected_protocols.append(proto_name)

    # Attach detected protocols as metadata to existing connections
    # or note them for the document generator
    if detected_protocols and model.components:
        primary = model.components[0]
        primary.security_notes.append(
            f"Protocols mentioned in docs: {', '.join(detected_protocols)}"
        )


def _extract_security_notes(model: ArchitectureModel, text: str) -> None:
    """Extract security-relevant observations from documentation text."""
    observations: list[str] = []
    for pattern, note in _SECURITY_PATTERNS:
        if re.search(pattern, text):
            observations.append(note)

    if observations and model.components:
        primary = model.components[0]
        for obs in observations:
            if obs not in primary.security_notes:
                primary.security_notes.append(obs)


def _extract_description(model: ArchitectureModel, bundle: SourceBundle) -> None:
    """Build a project description from Confluence/doc sources."""
    parts: list[str] = []

    for src in bundle.confluence_sources:
        # Try to extract the first meaningful paragraph
        lines = src.text.split("\n")
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 50 and not stripped.startswith(("#", "|", "-", "*", "```")):
                parts.append(stripped)
                break

    if parts and not model.description.startswith("Architecture"):
        model.description = " ".join(parts[:3])
