from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ConnectedAccountResponse(BaseModel):
    id: UUID
    provider: str
    provider_uid: str
    display_name: Optional[str]
    is_active: bool
    last_synced_at: Optional[datetime]
    sync_error: Optional[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntegrationCapabilities(BaseModel):
    steam_api_key_set: bool
    faceit_api_key_set: bool
    steam_inventory_prices_supported: bool = False


class IntegrationsResponse(BaseModel):
    accounts: List[ConnectedAccountResponse]
    capabilities: IntegrationCapabilities


class SteamOpenIdStartResponse(BaseModel):
    auth_url: str


class SteamConnectRequest(BaseModel):
    steam_id: str = Field(..., min_length=1, max_length=160)

    @field_validator("steam_id")
    @classmethod
    def clean_steam_id(cls, value: str) -> str:
        return value.strip()
