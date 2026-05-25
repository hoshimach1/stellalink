from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9_-]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    bio: Optional[str] = None
    tags: List[str] = []


class ProfileUpdate(BaseModel):
    slug: Optional[str] = Field(
        None, min_length=2, max_length=50, pattern=r"^[a-z0-9_-]+$"
    )
    status: Optional[Literal["draft", "private", "published"]] = None
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = None
    tags: Optional[List[str]] = None
    theme_preset: Optional[str] = Field(None, max_length=50)
    theme_tokens: Optional[Dict[str, Any]] = None
    accent_color: Optional[str] = Field(None, max_length=9)


class BlockCreate(BaseModel):
    block_type: str
    config: Dict[str, Any] = {}


class BlockUpdate(BaseModel):
    config: Optional[Dict[str, Any]] = None
    is_visible: Optional[bool] = None


class BlockReorder(BaseModel):
    ids: List[UUID]


class BlockResponse(BaseModel):
    id: UUID
    block_type: str
    sort_order: int
    is_visible: bool
    config: Dict[str, Any]

    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    id: UUID
    slug: str
    status: str
    display_name: str
    bio: Optional[str]
    tags: List[str]
    blocks: List[BlockResponse]
    theme_preset: str
    theme_tokens: Optional[Dict[str, Any]]
    accent_color: Optional[str]
    avatar_url: Optional[str]

    model_config = {"from_attributes": True}
