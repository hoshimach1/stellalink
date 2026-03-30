import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.user import User  # noqa: F401 — needed for relationship resolution


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    slug = Column(String, unique=True, nullable=False)
    status = Column(ENUM("draft", "private", "published", name="profile_status", create_type=False), nullable=False, default="draft")
    theme_preset = Column(String(50), nullable=False, default="material3")
    custom_css = Column(Text, nullable=True)
    theme_tokens = Column(JSONB, nullable=True)
    accent_color = Column(String(9), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    translations = relationship(
        "ProfileTranslation", back_populates="profile", cascade="all, delete-orphan"
    )
    blocks = relationship(
        "ProfileBlock", back_populates="profile", cascade="all, delete-orphan",
        order_by="ProfileBlock.sort_order",
    )
    user = relationship("User", foreign_keys=[user_id], lazy="raise")


class ProfileTranslation(Base):
    __tablename__ = "profile_translations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    locale = Column(String(10), nullable=False)
    display_name = Column(Text, nullable=False)
    bio = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=False, default=list)

    profile = relationship("Profile", back_populates="translations")

    __table_args__ = (UniqueConstraint("profile_id", "locale"),)


class ProfileBlock(Base):
    __tablename__ = "profile_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    block_type = Column(ENUM("links", "widget_faceit", "widget_steam", "widget_github", "widget_telegram", "widget_lastfm", "widget_spotify", "widget_custom", "pc_config", "text", "image_gallery", name="block_type", create_type=False), nullable=False)
    sort_order = Column(SmallInteger, nullable=False, default=0)
    is_visible = Column(Boolean, nullable=False, default=True)
    locale = Column(String(10), nullable=True)
    config = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="blocks")
