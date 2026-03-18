# Stellalink

**Твой живой профиль** — персональная страница, которая отражает тебя прямо сейчас, а не вчера.

Открыл — за 10-15 секунд понял кто человек, где его найти, чем живёт. Не статика, не набор ссылок — живые данные из подключённых аккаунтов.

---

## Концепция

Stellalink ближе к Linktree, чем к полноценному сайту, но с ключевым отличием: **живые данные**.

- Linktree и about.me — статика. Ты сам обновляешь что там написано.
- Stellalink — динамика. Профиль сам подтягивает актуальное состояние твоих аккаунтов.

Играешь в CS2? Виджет Faceit покажет твой текущий рейтинг. Слушаешь музыку? Last.fm / Spotify — что именно. Пишешь код? GitHub — активность за последние недели.

---

## Структура профиля

### Шапка (фиксированная)
Аватар, имя, короткое bio, теги. Всегда видна, не скроллится.

### Блоки (свободные)
Пользователь сам выбирает какие блоки включить и расставляет их через drag-and-drop.

| Тип блока | Описание |
|---|---|
| `links` | Ссылки с группировкой по категориям (соцсети, проекты, контакты) |
| `widget_steam` | Steam — библиотека игр, часы, статус онлайн |
| `widget_faceit` | Faceit — уровень, матчи, K/D, ELO |
| `widget_github` | GitHub — вклад, пиннед репозитории, активность |
| `widget_spotify` | Spotify — сейчас играет, топ треки |
| `widget_lastfm` | Last.fm — сейчас слушаю, недавние треки |
| `widget_telegram` | Telegram — ссылка на канал/бот с превью |
| `pc_config` | PC конфиг — ручной ввод, красивая карточка с железом |
| `text` | Текстовый блок — Markdown, если хочется пару слов о себе |
| `image_gallery` | Галерея изображений |

---

## Дизайн

**Material 3** — единая основа. Остальные стили (Apple-like, Fluent) — пресеты через CSS токены.
Плюс возможность полного кастома через свой CSS.

Одна кодовая база — разные «скины».

---

## Стек

### Frontend
- **Nuxt 3** + **Vue 3** — SSR для SEO публичных профилей
- **Vuetify 3** — Material 3 из коробки
- **Pinia** — управление состоянием
- **vue-draggable-plus** — drag-and-drop блоков
- **@mdi/font** — Material Design Icons

### Backend
- **FastAPI** — async Python
- **PostgreSQL 16** — основная база, блоки хранятся как `jsonb`
- **Redis** — кэш внешних API (TTL per widget)
- **SQLAlchemy 2** (async) + **asyncpg**
- **JWT** — access + refresh токены с ротацией

### Инфраструктура
- **Docker** + **docker-compose**
- **Gitea Actions** — CI (lint + tests) и CD (deploy)

---

## Локальный запуск

### Требования
- Docker и docker-compose
- Node.js 20+
- Python 3.12+

### Backend

```bash
cd backend
cp .env.example .env        # настрой переменные
docker-compose up -d        # поднимает PostgreSQL + Redis
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

API будет доступно на `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Приложение запустится на `http://localhost:3000`.

---

## Схема базы данных

Основные сущности:

```
users
  └── profiles (slug → /username)
        └── profile_blocks (jsonb config, sort_order)
              └── connected_accounts → widget_data_cache
```

- `profiles.theme_preset` — выбор скина (material3, apple, fluent, ...)
- `profile_blocks.config` — JSONB, структура зависит от типа блока
- `connected_accounts` — токены внешних сервисов (Steam, Spotify, GitHub, ...)
- `widget_data_cache` — персистентный кэш виджетов (+ Redis для горячих данных)

---

## Статус

Проект на ранней стадии разработки.

| Область | Статус |
|---|---|
| Аутентификация (register / login / refresh) | Готово |
| Лендинг | Готово |
| Схема БД | Готово |
| Dashboard (скелет) | Готово |
| Профили + блоки | В разработке |
| Виджеты (Steam, GitHub, Spotify...) | В планах |
| Темы и кастом CSS | В планах |
| Аналитика (просмотры, клики) | В планах |
| Организации / командные профили | В планах |

---

## Лицензия

Проект закрытый. Все права защищены.
