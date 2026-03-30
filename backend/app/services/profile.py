from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile, ProfileBlock, ProfileTranslation
from app.models.user import User


async def _load_profile(db: AsyncSession, where) -> Optional[Profile]:
    result = await db.execute(
        select(Profile)
        .options(
            selectinload(Profile.translations),
            selectinload(Profile.blocks),
            selectinload(Profile.user),
        )
        .where(where)
    )
    return result.scalar_one_or_none()


async def get_profile_by_user(db: AsyncSession, user_id: UUID) -> Optional[Profile]:
    return await _load_profile(db, Profile.user_id == user_id)


async def get_profile_by_slug(db: AsyncSession, slug: str) -> Optional[Profile]:
    return await _load_profile(db, Profile.slug == slug)


async def slug_taken(db: AsyncSession, slug: str, exclude_id: Optional[UUID] = None) -> bool:
    q = select(Profile.id).where(Profile.slug == slug)
    if exclude_id:
        q = q.where(Profile.id != exclude_id)
    result = await db.execute(q)
    return result.scalar_one_or_none() is not None


async def create_profile(
    db: AsyncSession,
    user_id: UUID,
    slug: str,
    display_name: str,
    bio: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Profile:
    profile = Profile(user_id=user_id, slug=slug)
    db.add(profile)
    await db.flush()

    translation = ProfileTranslation(
        profile_id=profile.id,
        locale="ru",
        display_name=display_name,
        bio=bio,
        tags=tags or [],
    )
    db.add(translation)
    await db.commit()

    return await get_profile_by_user(db, user_id)


async def update_profile(
    db: AsyncSession,
    profile: Profile,
    slug: Optional[str] = None,
    status: Optional[str] = None,
    display_name: Optional[str] = None,
    bio: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Profile:
    now = datetime.now(timezone.utc)
    if slug is not None:
        profile.slug = slug
    if status is not None:
        profile.status = status
    profile.updated_at = now

    trans = next((t for t in profile.translations if t.locale == "ru"), None)
    if trans is None and any(v is not None for v in (display_name, bio, tags)):
        trans = ProfileTranslation(
            profile_id=profile.id,
            locale="ru",
            display_name=display_name or "",
            bio=bio,
            tags=tags or [],
        )
        db.add(trans)
    elif trans is not None:
        if display_name is not None:
            trans.display_name = display_name
        if bio is not None:
            trans.bio = bio
        if tags is not None:
            trans.tags = tags

    await db.commit()
    return await get_profile_by_user(db, profile.user_id)


async def create_block(
    db: AsyncSession,
    profile_id: UUID,
    block_type: str,
    config: dict,
) -> ProfileBlock:
    result = await db.execute(
        select(ProfileBlock.sort_order)
        .where(ProfileBlock.profile_id == profile_id)
        .order_by(ProfileBlock.sort_order.desc())
        .limit(1)
    )
    max_order = result.scalar_one_or_none() or -1

    block = ProfileBlock(
        profile_id=profile_id,
        block_type=block_type,
        config=config,
        sort_order=max_order + 1,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def update_block(
    db: AsyncSession,
    block: ProfileBlock,
    config: Optional[dict] = None,
    is_visible: Optional[bool] = None,
) -> ProfileBlock:
    if config is not None:
        block.config = config
    if is_visible is not None:
        block.is_visible = is_visible
    block.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(block)
    return block


async def delete_block(db: AsyncSession, block: ProfileBlock) -> None:
    await db.delete(block)
    await db.commit()


async def reorder_blocks(db: AsyncSession, profile_id: UUID, block_ids: List[UUID]) -> None:
    result = await db.execute(
        select(ProfileBlock).where(ProfileBlock.profile_id == profile_id)
    )
    blocks = {b.id: b for b in result.scalars().all()}
    for i, bid in enumerate(block_ids):
        if bid in blocks:
            blocks[bid].sort_order = i
    await db.commit()
