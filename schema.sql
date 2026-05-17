-- ============================================================================
-- LiveProfile — PostgreSQL Schema
-- Персональная страница-профиль с живыми данными
-- ============================================================================

-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";       -- регистронезависимые строки для email/slug

-- ============================================================================
-- ENUM-типы
-- ============================================================================

CREATE TYPE auth_provider AS ENUM (
    'local',        -- email + пароль
    'google',
    'github',
    'discord',
    'telegram'
);

CREATE TYPE profile_status AS ENUM (
    'draft',        -- черновик, не виден никому кроме владельца
    'private',      -- виден только по прямой ссылке / авторизованным
    'published'     -- публичный
);

CREATE TYPE profile_role AS ENUM (
    'owner',
    'editor',
    'viewer'
);

CREATE TYPE block_type AS ENUM (
    'links',            -- ссылки с группировкой
    'widget_faceit',
    'widget_steam',
    'widget_github',
    'widget_telegram',
    'widget_lastfm',
    'widget_spotify',
    'widget_custom',    -- произвольный внешний API
    'pc_config',
    'text',
    'image_gallery'
);

CREATE TYPE org_role AS ENUM (
    'owner',
    'admin',
    'member'
);

-- ============================================================================
-- 1. ПОЛЬЗОВАТЕЛИ И АУТЕНТИФИКАЦИЯ
-- ============================================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           CITEXT UNIQUE NOT NULL,
    password_hash   TEXT,                        -- NULL если зарегистрирован только через OAuth
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    avatar_url      TEXT,
    default_locale  VARCHAR(10) NOT NULL DEFAULT 'ru',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ                  -- soft delete
);

CREATE INDEX idx_users_email ON users (email) WHERE deleted_at IS NULL;

-- Привязки OAuth-провайдеров (у одного пользователя может быть несколько)
CREATE TABLE user_oauth_accounts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider        auth_provider NOT NULL,
    provider_uid    TEXT NOT NULL,                -- ID пользователя у провайдера
    provider_email  TEXT,
    access_token    TEXT,                         -- зашифрован на уровне приложения
    refresh_token   TEXT,
    token_expires_at TIMESTAMPTZ,
    raw_profile     JSONB,                       -- сырой профиль от провайдера
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (provider, provider_uid)
);

CREATE INDEX idx_oauth_user ON user_oauth_accounts (user_id);

-- Сессии / refresh-токены
CREATE TABLE user_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   TEXT UNIQUE NOT NULL,
    user_agent      TEXT,
    ip_address      INET,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_user ON user_sessions (user_id);
CREATE INDEX idx_sessions_expires ON user_sessions (expires_at);

CREATE TABLE app_settings (
    key              VARCHAR(100) PRIMARY KEY,
    value            JSONB NOT NULL DEFAULT '{}',
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 2. ОРГАНИЗАЦИИ / КОМАНДЫ
-- ============================================================================

CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug            CITEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    avatar_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE organization_members (
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            org_role NOT NULL DEFAULT 'member',
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (organization_id, user_id)
);

-- ============================================================================
-- 3. ПРОФИЛИ
-- ============================================================================

-- Один пользователь / организация может иметь несколько профилей (личный, рабочий и т.п.)
CREATE TABLE profiles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- владелец: либо user, либо organization (один из двух NOT NULL)
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    slug            CITEXT UNIQUE NOT NULL,      -- username / URL-путь
    status          profile_status NOT NULL DEFAULT 'draft',

    -- дизайн / тема
    theme_preset    VARCHAR(50) NOT NULL DEFAULT 'material3',  -- material3, apple, fluent, ...
    custom_css      TEXT,                        -- пользовательский CSS
    theme_tokens    JSONB,                       -- переопределение CSS-токенов {"--md-primary": "#6750A4", ...}
    accent_color    VARCHAR(9),                  -- HEX (#RRGGBBAA)

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- ровно один владелец
    CONSTRAINT chk_profile_owner CHECK (
        (user_id IS NOT NULL AND organization_id IS NULL) OR
        (user_id IS NULL AND organization_id IS NOT NULL)
    )
);

CREATE INDEX idx_profiles_user ON profiles (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_profiles_org ON profiles (organization_id) WHERE organization_id IS NOT NULL;
CREATE INDEX idx_profiles_slug ON profiles (slug);

-- Коллабораторы профиля (для командных профилей или делегированного доступа)
CREATE TABLE profile_collaborators (
    profile_id      UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            profile_role NOT NULL DEFAULT 'viewer',
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (profile_id, user_id)
);

-- ============================================================================
-- 4. МУЛЬТИЯЗЫЧНАЯ ШАПКА ПРОФИЛЯ
-- ============================================================================

-- Переводы шапки: имя, bio, теги — по локали
CREATE TABLE profile_translations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id      UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    locale          VARCHAR(10) NOT NULL,        -- 'ru', 'en', 'fi', ...
    display_name    TEXT NOT NULL,
    bio             TEXT,                         -- короткое описание
    tags            TEXT[] DEFAULT '{}',          -- теги / хэштеги

    UNIQUE (profile_id, locale)
);

CREATE INDEX idx_profile_trans_profile ON profile_translations (profile_id);

-- ============================================================================
-- 5. БЛОКИ КОНТЕНТА (ядро — JSONB)
-- ============================================================================

CREATE TABLE profile_blocks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id      UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    block_type      block_type NOT NULL,
    sort_order      SMALLINT NOT NULL DEFAULT 0, -- порядок drag-and-drop
    is_visible      BOOLEAN NOT NULL DEFAULT TRUE,
    locale          VARCHAR(10),                 -- NULL = одинаково для всех локалей

    -- Всё содержимое блока — в JSONB, структура зависит от block_type
    -- Примеры ниже в комментариях
    config          JSONB NOT NULL DEFAULT '{}',

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_blocks_profile_order ON profile_blocks (profile_id, sort_order);
CREATE INDEX idx_blocks_type ON profile_blocks (block_type);
-- GIN для поиска внутри config при необходимости
CREATE INDEX idx_blocks_config ON profile_blocks USING GIN (config jsonb_path_ops);

-- ============================================================================
-- 5a. ПРИМЕРЫ config ДЛЯ РАЗНЫХ block_type (справочный комментарий)
-- ============================================================================

/*
block_type = 'links':
{
    "groups": [
        {
            "title": "Социальные сети",
            "links": [
                {"label": "Telegram", "url": "https://t.me/...", "icon": "telegram"},
                {"label": "GitHub", "url": "https://github.com/...", "icon": "github"}
            ]
        }
    ]
}

block_type = 'widget_steam':
{
    "steam_id": "76561198...",
    "use_connected_account": true,
    "show_recent_games": true,
    "show_profile_stats": true,
    "show_inventory_highlight": true
}

block_type = 'widget_github':
{
    "username": "alexander",
    "show_contributions": true,
    "show_pinned_repos": true,
    "repos_limit": 6
}

block_type = 'widget_spotify' / 'widget_lastfm':
{
    "connected_account_id": "uuid-ref-to-connected_accounts",
    "show_now_playing": true,
    "show_top_tracks": true,
    "top_period": "1month"
}

block_type = 'pc_config':
{
    "title": "Main Rig",
    "components": [
        {"category": "CPU",       "name": "AMD Ryzen 5 7500F"},
        {"category": "GPU",       "name": "NVIDIA RTX 2070 Super"},
        {"category": "RAM",       "name": "32 GB DDR5-5200"},
        {"category": "Storage",   "name": "1 TB NVMe SSD"},
        {"category": "Case",      "name": "..."}
    ]
}

block_type = 'text':
{
    "content": "Markdown или plain text",
    "format": "markdown"
}
*/

-- ============================================================================
-- 6. ПОДКЛЮЧЁННЫЕ АККАУНТЫ (ВНЕШНИЕ СЕРВИСЫ ДЛЯ ЖИВЫХ ДАННЫХ)
-- ============================================================================

CREATE TABLE connected_accounts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL,               -- 'steam', 'faceit', 'github', 'lastfm', 'spotify', 'telegram', ...
    provider_uid    TEXT NOT NULL,                -- ID/username у провайдера
    display_name    TEXT,                         -- отображаемое имя
    access_token    TEXT,                         -- зашифрован, для OAuth-провайдеров
    refresh_token   TEXT,
    token_expires_at TIMESTAMPTZ,
    scopes          TEXT[],                       -- выданные скоупы
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at  TIMESTAMPTZ,
    sync_error      TEXT,                         -- последняя ошибка синхронизации
    metadata        JSONB DEFAULT '{}',          -- доп. данные (steam_id, faceit_elo, etc.)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (user_id, provider, provider_uid)
);

CREATE INDEX idx_connected_user ON connected_accounts (user_id);
CREATE INDEX idx_connected_provider ON connected_accounts (provider);

-- ============================================================================
-- 7. КЭШ ДАННЫХ ОТ ВНЕШНИХ API
-- ============================================================================

-- Персистентный кэш-слой (дополняет Redis — для восстановления после рестарта
-- и для данных, которые не нужно хранить в Redis вечно)
CREATE TABLE widget_data_cache (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connected_account_id UUID NOT NULL REFERENCES connected_accounts(id) ON DELETE CASCADE,
    data_type           TEXT NOT NULL,            -- 'now_playing', 'recent_games', 'contributions', 'elo', ...
    payload             JSONB NOT NULL,
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    ttl_seconds         INT NOT NULL DEFAULT 300, -- 5 мин по умолчанию
    expires_at          TIMESTAMPTZ NOT NULL DEFAULT now() + interval '300 seconds'
);

CREATE INDEX idx_cache_account ON widget_data_cache (connected_account_id);
CREATE INDEX idx_cache_expires ON widget_data_cache (expires_at);
-- Уникальность: один тип данных на аккаунт
CREATE UNIQUE INDEX idx_cache_account_type ON widget_data_cache (connected_account_id, data_type);

-- ============================================================================
-- 8. АНАЛИТИКА (ЗАГОТОВКА — ВТОРАЯ ФАЗА)
-- ============================================================================

-- Таблица спроектирована под append-only, потом можно перенести в TimescaleDB/ClickHouse
CREATE TABLE profile_views (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id      UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    viewer_ip       INET,
    viewer_ua       TEXT,
    referer         TEXT,
    country_code    VARCHAR(2),
    viewed_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_views_profile_time ON profile_views (profile_id, viewed_at DESC);

CREATE TABLE block_clicks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    block_id        UUID NOT NULL REFERENCES profile_blocks(id) ON DELETE CASCADE,
    profile_id      UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    target_url      TEXT,
    viewer_ip       INET,
    clicked_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_clicks_block ON block_clicks (block_id, clicked_at DESC);
CREATE INDEX idx_clicks_profile ON block_clicks (profile_id, clicked_at DESC);

-- ============================================================================
-- 9. ФАЙЛЫ / МЕДИА
-- ============================================================================

CREATE TABLE media_files (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_name   TEXT NOT NULL,
    storage_path    TEXT NOT NULL,                -- путь в S3 / MinIO
    mime_type       TEXT NOT NULL,
    size_bytes      BIGINT NOT NULL,
    width           INT,
    height          INT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_media_user ON media_files (user_id);

-- ============================================================================
-- 10. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
-- ============================================================================

-- Автообновление updated_at
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Применяем ко всем таблицам с updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'updated_at'
          AND table_schema = 'public'
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at()',
            t, t
        );
    END LOOP;
END;
$$;

-- Очистка протухшего кэша (запускать по cron или pg_cron)
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM widget_data_cache WHERE expires_at < now();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ГОТОВО. Итого таблиц: 13
-- users, user_oauth_accounts, user_sessions,
-- organizations, organization_members,
-- profiles, profile_collaborators, profile_translations,
-- profile_blocks, connected_accounts, widget_data_cache,
-- profile_views, block_clicks, media_files
-- ============================================================================
