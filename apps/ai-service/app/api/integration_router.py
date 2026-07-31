"""
REST API Router for Enterprise Integrations Platform (/api/integrations/*).
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.integrations.gateway import IntegrationGateway
from app.integrations.interfaces import WebhookEventType
from app.integrations.models import IntegrationProvider, IntegrationResponse, WebhookEvent

router = APIRouter(prefix="/api/integrations", tags=["Enterprise Integrations Platform"])

# Singleton gateway instance for dependency injection
_gateway_instance: Optional[IntegrationGateway] = None


def get_gateway() -> IntegrationGateway:
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = IntegrationGateway()
    return _gateway_instance


class TestIntegrationBody(BaseModel):
    provider_id: str
    action: str = "DEFAULT"
    payload: Dict[str, Any] = Field(default_factory=dict)


class IncomingWebhookBody(BaseModel):
    provider_id: str
    event_type: WebhookEventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    signature: Optional[str] = None


@router.get("/providers", response_model=List[IntegrationProvider])
def list_providers(gateway: IntegrationGateway = Depends(get_gateway)) -> List[IntegrationProvider]:
    """Lists all registered enterprise integration providers."""
    return gateway.registry.list_all_providers()


@router.get("/providers/{provider_id}", response_model=IntegrationProvider)
def get_provider_details(provider_id: str, gateway: IntegrationGateway = Depends(get_gateway)) -> IntegrationProvider:
    """Retrieves provider metadata and health metrics by ID."""
    provider = gateway.registry.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found.")
    return provider


@router.get("/health", response_model=Dict[str, Any])
def get_integrations_health(gateway: IntegrationGateway = Depends(get_gateway)) -> Dict[str, Any]:
    """Returns aggregated system health across all integration adapters."""
    return gateway.get_system_health()


@router.post("/test", response_model=IntegrationResponse)
def execute_test_request(body: TestIntegrationBody, gateway: IntegrationGateway = Depends(get_gateway)) -> IntegrationResponse:
    """Executes a test request through the Integration Gateway orchestrator."""
    return gateway.execute_integration(
        provider_id=body.provider_id,
        action=body.action,
        payload=body.payload,
    )


@router.post("/webhooks", response_model=WebhookEvent)
def ingest_incoming_webhook(body: IncomingWebhookBody, gateway: IntegrationGateway = Depends(get_gateway)) -> WebhookEvent:
    """Ingests and validates incoming third-party webhooks."""
    return gateway.process_incoming_webhook(
        provider_id=body.provider_id,
        event_type=body.event_type,
        payload=body.payload,
        signature=body.signature,
    )


@router.get("/metrics", response_model=Dict[str, Any])
def get_telemetry_metrics(gateway: IntegrationGateway = Depends(get_gateway)) -> Dict[str, Any]:
    """Returns latency counters, request statistics, and circuit state metrics."""
    return gateway.orchestrator.metrics.get_all_metrics()
