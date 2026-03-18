from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.profile import (
    BlockCreate,
    BlockReorder,
    BlockResponse,
    BlockUpdate,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from app.services import profile as svc

router = APIRouter(tags=["profiles"])


def _to_response(profile) -> ProfileResponse:
    trans = next((t for t in profile.translations if t.locale == "ru"), None)
    return ProfileResponse(
        id=profile.id,
        slug=profile.slug,
        status=profile.status,
        display_name=trans.display_name if trans else "",
        bio=trans.bio if trans else None,
        tags=trans.tags if trans else [],
        blocks=[BlockResponse.model_validate(b) for b in profile.blocks],
    )


# ── My profile ────────────────────────────────────────────────────────────────

@router.get("/profiles/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _to_response(profile)


@router.post("/profiles", response_model=ProfileResponse, status_code=201)
async def create_profile(
    body: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if await svc.get_profile_by_user(db, current_user.id):
        raise HTTPException(status_code=409, detail="Profile already exists")
    if await svc.slug_taken(db, body.slug):
        raise HTTPException(status_code=409, detail="Slug already taken")

    profile = await svc.create_profile(
        db,
        user_id=current_user.id,
        slug=body.slug,
        display_name=body.display_name,
        bio=body.bio,
        tags=body.tags,
    )
    return _to_response(profile)


@router.patch("/profiles/me", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if body.slug and body.slug != profile.slug:
        if await svc.slug_taken(db, body.slug, exclude_id=profile.id):
            raise HTTPException(status_code=409, detail="Slug already taken")

    profile = await svc.update_profile(
        db, profile,
        slug=body.slug,
        status=body.status,
        display_name=body.display_name,
        bio=body.bio,
        tags=body.tags,
    )
    return _to_response(profile)


# ── Blocks ────────────────────────────────────────────────────────────────────

@router.post("/profiles/me/blocks", response_model=BlockResponse, status_code=201)
async def create_block(
    body: BlockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return await svc.create_block(db, profile.id, body.block_type, body.config)


@router.patch("/profiles/me/blocks/{block_id}", response_model=BlockResponse)
async def update_block(
    block_id: UUID,
    body: BlockUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    block = next((b for b in profile.blocks if b.id == block_id), None)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    return await svc.update_block(db, block, config=body.config, is_visible=body.is_visible)


@router.delete("/profiles/me/blocks/{block_id}", status_code=204)
async def delete_block(
    block_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    block = next((b for b in profile.blocks if b.id == block_id), None)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    await svc.delete_block(db, block)


@router.put("/profiles/me/blocks/reorder", status_code=204)
async def reorder_blocks(
    body: BlockReorder,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    await svc.reorder_blocks(db, profile.id, body.ids)


# ── Public ────────────────────────────────────────────────────────────────────

@router.get("/u/{slug}", response_model=ProfileResponse)
async def public_profile(slug: str, db: AsyncSession = Depends(get_db)):
    profile = await svc.get_profile_by_slug(db, slug)
    if not profile or profile.status == "draft":
        raise HTTPException(status_code=404, detail="Profile not found")
    return _to_response(profile)
