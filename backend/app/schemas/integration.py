from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
    github_oauth_ready: bool = False
    gitlab_oauth_ready: bool = False
    gitea_oauth_ready: bool = False
    code_provider_token_auth_enabled: bool = True


class IntegrationsResponse(BaseModel):
    accounts: List[ConnectedAccountResponse]
    capabilities: IntegrationCapabilities


class SteamOpenIdStartResponse(BaseModel):
    auth_url: str


CodeProvider = Literal["github", "gitlab", "gitea"]


class CodeProviderTokenConnectRequest(BaseModel):
    provider: CodeProvider
    access_token: str = Field(min_length=1, max_length=5000)
    base_url: Optional[str] = Field(default=None, max_length=500)


class CodeProviderOAuthStartRequest(BaseModel):
    provider: CodeProvider
    base_url: Optional[str] = Field(default=None, max_length=500)


class OAuthStartResponse(BaseModel):
    auth_url: str
