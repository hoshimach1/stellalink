<template>
  <div class="home-page">
    <header class="app-topbar">
      <a href="#hero" class="brand" @click.prevent="scrollTo('hero')">
        <img src="/images/logos/logo.png" alt="Stellalink" class="brand-logo">
        <span class="brand-copy">
          <span class="brand-wordmark">Stellalink</span>
        </span>
      </a>

      <button
        class="menu-trigger"
        :class="{ open: menuOpen }"
        aria-label="Открыть меню"
        :aria-expanded="menuOpen"
        @click="menuOpen = !menuOpen"
      >
        <span />
        <span />
        <span />
      </button>

      <nav class="app-nav" :class="{ open: menuOpen }">
        <a href="#live" @click.prevent="scrollTo('live')"><i class="ri-pulse-line" /> Live</a>
        <a href="#modules" @click.prevent="scrollTo('modules')"><i class="ri-layout-grid-fill" /> Блоки</a>
        <a href="#flow" @click.prevent="scrollTo('flow')"><i class="ri-route-fill" /> Запуск</a>
        <a href="#compare" @click.prevent="scrollTo('compare')"><i class="ri-scales-3-fill" /> Сравнение</a>

        <div v-if="auth.isAuthenticated" class="nav-account-actions">
          <NuxtLink class="user-pill" to="/dashboard" @click="closeMenu">
            <span class="user-avatar">
              <img v-if="userAvatarSrc" :src="userAvatarSrc" alt="">
              <span v-else>{{ emailInitial }}</span>
            </span>
            <span class="user-copy">
              <span class="user-name">{{ userDisplayName }}</span>
              <span v-if="auth.user?.email" class="user-mail">{{ auth.user.email }}</span>
            </span>
          </NuxtLink>
          <button class="logout-pill" aria-label="Выйти" @click="logout">
            <i class="ri-logout-box-r-line" />
          </button>
        </div>

        <template v-else>
          <md-outlined-button class="btn btn-nav-secondary" @click="openAuth('', 'login')">
            Войти
          </md-outlined-button>
          <md-filled-button class="btn btn-nav-primary" @click="openAuth(previewSlug, 'register')">
            Создать профиль
          </md-filled-button>
        </template>
      </nav>
    </header>

    <main>
      <section id="hero" class="hero-section">
        <div class="hero-media" aria-hidden="true">
          <img src="/images/landing/preview.png" alt="">
        </div>

        <div class="hero-overlay" />

        <div class="hero-content">
          <div class="hero-copy reveal">
            <p class="eyebrow">Профиль, который обновляется сам</p>
            <h1>Stellalink собирает тебя в один живой URL</h1>
            <p class="hero-sub">
              Игры, музыка, ссылки, контакты, сетап и портфолио остаются в одном месте.
              Ты меняешь блоки, а посетитель всегда видит актуальный срез.
            </p>

            <div class="hero-actions">
              <md-filled-button class="btn btn-hero-primary" @click="openAuth(previewSlug, 'register')">
                Забрать адрес
              </md-filled-button>
              <md-outlined-button class="btn btn-hero-secondary" @click="scrollTo('live')">
                Смотреть пример
              </md-outlined-button>
            </div>

            <div class="hero-address" aria-label="Пример короткой ссылки">
              <span>stellalink.app/</span>
              <strong>{{ previewSlug }}</strong>
            </div>
          </div>

          <div class="hero-visual reveal" style="--reveal-delay: 120ms">
            <img src="/images/landing/preview.png" alt="Пример мобильного профиля Stellalink">

            <div class="hero-signal-dock">
              <article v-for="signal in heroSignals" :key="signal.label" class="signal-pill">
                <FaceitLogo v-if="signal.icon === 'faceit'" class="signal-faceit-logo" />
                <i v-else :class="signal.icon" />
                <span>{{ signal.label }}</span>
                <strong>{{ signal.value }}</strong>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section id="live" class="section live-section">
        <div class="section-kicker live-kicker">
          <span>Live-профиль</span>
          <h2>Живой профиль с играми, музыкой и ссылками</h2>
          <p>
            Сохранил идею оригинала: один публичный URL, где Steam, Spotify,
            Faceit, ссылки и сетап выглядят как части одной актуальной визитки.
          </p>
        </div>

        <div class="live-layout">
          <md-elevated-card class="profile-console">
            <div class="console-top">
              <div class="profile-person">
                <div class="profile-avatar">A</div>
                <div>
                  <h3>Alexander K.</h3>
                  <p>Геймер, меломан, fullstack creator</p>
                  <div class="profile-mini-tags">
                    <span v-for="tag in profileTags" :key="tag">{{ tag }}</span>
                  </div>
                </div>
              </div>
              <span class="live-badge">live</span>
            </div>

            <div class="console-grid">
              <article class="console-tile steam-tile">
                <div class="tile-head">
                  <i class="ri-steam-fill" />
                  <span>Steam</span>
                </div>
                <strong>Counter-Strike 2</strong>
                <p>2 847 ч · онлайн сейчас</p>
                <div class="steam-meta">
                  <span>Dust II</span>
                  <span>Prime</span>
                  <span>5 друзей онлайн</span>
                </div>
              </article>

              <article class="console-tile faceit-tile">
                <div class="tile-head">
                  <FaceitLogo class="tile-faceit-logo" />
                  <span>Faceit</span>
                </div>
                <FaceitSkillLevel class="faceit-ring" :level="8" />
                <div class="faceit-mini-grid">
                  <span><b>1847</b><small>ELO</small></span>
                  <span><b>1.24</b><small>K/D</small></span>
                  <span><b>54%</b><small>WR</small></span>
                </div>
              </article>

              <article class="console-tile spotify-tile">
                <div class="tile-head">
                  <i class="ri-spotify-fill" />
                  <span>Spotify</span>
                </div>
                <div class="spotify-player">
                  <div class="album-art" />
                  <div class="track-copy">
                    <strong>Fluorescent Adolescent</strong>
                    <p>Arctic Monkeys</p>
                  </div>
                  <div class="eq-bars" aria-hidden="true">
                    <span v-for="n in 5" :key="n" />
                  </div>
                </div>
                <div class="track-progress" aria-hidden="true">
                  <span />
                </div>
              </article>

              <article class="console-tile links-tile">
                <div class="tile-head">
                  <i class="ri-links-fill" />
                  <span>Ссылки</span>
                </div>
                <a
                  v-for="link in liveLinks"
                  :key="link.label"
                  :href="link.href"
                  target="_blank"
                  rel="noopener"
                >
                  <span>
                    <i :class="link.icon" />
                    <b>{{ link.label }}</b>
                    <small>{{ link.caption }}</small>
                  </span>
                  <i class="ri-arrow-right-up-line" />
                </a>
              </article>

              <article class="console-tile pc-tile">
                <div class="tile-head">
                  <i class="ri-computer-fill" />
                  <span>Main PC</span>
                </div>
                <div class="spec-grid">
                  <span v-for="part in pcParts" :key="part.key">
                    <small>{{ part.key }}</small>
                    <b>{{ part.value }}</b>
                  </span>
                </div>
              </article>
            </div>
          </md-elevated-card>

          <div class="live-notes">
            <md-filled-card
              v-for="(note, noteIndex) in liveNotes"
              :key="note.title"
              class="note-card reveal"
              :style="{ '--reveal-delay': `${noteIndex * 80}ms` }"
            >
              <i :class="note.icon" />
              <h3>{{ note.title }}</h3>
              <p>{{ note.text }}</p>
            </md-filled-card>
          </div>
        </div>
      </section>

      <section id="modules" class="section modules-section">
        <div class="section-kicker reveal">
          <span>Блоки</span>
          <h2>Страница собирается как панель: включай только то, что важно</h2>
          <p>
            Каждая категория работает как самостоятельный смысловой слой: игры для тиммейтов,
            музыка для вайба, ссылки для связи, портфолио для дела.
          </p>
        </div>

        <div class="module-grid">
          <md-outlined-card
            v-for="(module, moduleIndex) in modules"
            :key="module.title"
            class="module-card reveal"
            :style="{ '--reveal-delay': `${moduleIndex * 60}ms` }"
          >
            <div class="module-icon">
              <i :class="module.icon" />
            </div>
            <h3>{{ module.title }}</h3>
            <p>{{ module.text }}</p>
            <div class="module-tags">
              <span v-for="tag in module.tags" :key="tag">{{ tag }}</span>
            </div>
          </md-outlined-card>
        </div>
      </section>

      <section class="section scenario-section">
        <div class="scenario-band reveal">
          <div>
            <span class="band-label">Сценарии</span>
            <h2>Один адрес под разные аудитории</h2>
          </div>

          <div class="scenario-list">
            <article v-for="scenario in scenarios" :key="scenario.title">
              <i :class="scenario.icon" />
              <div>
                <h3>{{ scenario.title }}</h3>
                <p>{{ scenario.text }}</p>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section id="flow" class="section flow-section">
        <div class="section-kicker reveal">
          <span>Запуск</span>
          <h2>От пустого имени до готовой страницы за три коротких шага</h2>
        </div>

        <div class="flow-track">
          <article
            v-for="(step, stepIndex) in steps"
            :key="step.title"
            class="flow-step reveal"
            :style="{ '--reveal-delay': `${stepIndex * 90}ms` }"
          >
            <span>{{ step.index }}</span>
            <h3>{{ step.title }}</h3>
            <p>{{ step.description }}</p>
          </article>
        </div>
      </section>

      <section id="compare" class="section compare-section">
        <div class="section-kicker reveal">
          <span>Сравнение</span>
          <h2>Stellalink ближе к личному дашборду, чем к дереву ссылок</h2>
        </div>

        <div class="compare-wrap reveal">
          <table class="compare-table">
            <thead>
              <tr>
                <th>Функция</th>
                <th>Stellalink</th>
                <th>Linktree</th>
                <th>about.me</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in compareRows" :key="row.feature">
                <td>{{ row.feature }}</td>
                <td :class="statusClass(row.stellalink)">{{ statusLabel(row.stellalink) }}</td>
                <td :class="statusClass(row.linktree)">{{ statusLabel(row.linktree) }}</td>
                <td :class="statusClass(row.aboutme)">{{ statusLabel(row.aboutme) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section id="start" class="section cta-section">
        <md-filled-card class="cta-card reveal">
          <div>
            <span class="band-label">Старт</span>
            <h2>Займи короткий адрес и собери свой первый профиль</h2>
            <p>Ник, аватар, несколько блоков и ссылка уже готова к публикации.</p>
          </div>

          <div class="cta-panel">
            <div class="cta-preview">
              <div class="cta-preview-head">
                <span class="profile-avatar small">A</span>
                <div>
                  <strong>stellalink.app/{{ previewSlug }}</strong>
                  <small>готов к публикации</small>
                </div>
              </div>
              <div class="cta-preview-grid">
                <span><i class="ri-steam-fill" /> Steam</span>
                <span><i class="ri-spotify-fill" /> Spotify</span>
                <span><i class="ri-github-fill" /> GitHub</span>
                <span><i class="ri-telegram-fill" /> Telegram</span>
              </div>
            </div>

            <div class="cta-form">
              <label class="slug-field">
                <span>stellalink.app/</span>
                <input
                  type="text"
                  :value="slug"
                  placeholder="username"
                  aria-label="username"
                  @input="onSlugInput"
                  @keydown.enter.prevent="openAuth(previewSlug, 'register')"
                >
              </label>
              <md-filled-button class="btn btn-hero-primary" @click="openAuth(previewSlug, 'register')">
                Создать профиль
              </md-filled-button>
            </div>
          </div>
        </md-filled-card>
      </section>
    </main>

    <footer class="footer">
      <div class="footer-brand-block">
        <div class="footer-brand">
          <img src="/images/logos/logo.png" alt="Stellalink" class="footer-logo">
          <p>Stellalink · 2026</p>
        </div>
        <p class="footer-claim">Один живой URL для игр, музыки, ссылок и портфолио.</p>
      </div>

      <div class="footer-status">
        <span><i class="ri-pulse-line" /> Live blocks</span>
        <span><i class="ri-shield-check-line" /> Privacy first</span>
      </div>

      <div class="footer-links">
        <a
          v-for="link in footerLinks"
          :key="link.label"
          :href="link.href"
          :target="link.href.startsWith('http') ? '_blank' : undefined"
          :rel="link.href.startsWith('http') ? 'noopener noreferrer' : undefined"
        >
          <i :class="link.icon" />
          <span>{{ link.label }}</span>
        </a>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
import { useProfileStore } from '~/stores/profile'
import { resolveAvatarUrl } from '~/composables/useAvatarUrl'

definePageMeta({ layout: 'landing' })

useHead({
  title: 'Stellalink - живой профиль в одном URL',
  meta: [
    {
      name: 'description',
      content: 'Живой профиль в одном коротком URL: игровые виджеты, музыка, ссылки, контакты, сетап и портфолио.',
    },
  ],
})

type CompareState = 'check' | 'partial' | 'none'

const auth = useAuthStore()
const profile = useProfileStore()
const config = useRuntimeConfig()
const menuOpen = ref(false)
const slug = ref('')

const emailInitial = computed(() => auth.user?.email?.[0]?.toUpperCase() ?? '?')
const userDisplayName = computed(() =>
  profile.profile?.display_name?.trim()
  || profile.profile?.slug?.trim()
  || auth.user?.email
  || 'Аккаунт',
)
const userAvatarSrc = computed(() =>
  resolveAvatarUrl(auth.user?.avatar_url ?? null, config.public.apiBase as string),
)
const previewSlug = computed(() => slug.value.trim().replace(/\s+/g, '-').toLowerCase() || 'username')

const heroSignals = [
  { icon: 'ri-steam-fill', label: 'Steam', value: 'CS2 онлайн' },
  { icon: 'ri-lastfm-fill', label: 'Музыка', value: 'Arctic Monkeys' },
  { icon: 'faceit', label: 'Faceit', value: 'Lvl 8' },
]

const profileTags = ['CS2', 'Music', 'Anime', 'Dev']

const liveLinks = [
  {
    icon: 'ri-github-fill',
    label: 'GitHub',
    caption: 'alexkirilin',
    href: 'https://github.com',
  },
  {
    icon: 'ri-telegram-fill',
    label: 'Telegram',
    caption: 'личный канал',
    href: 'https://t.me',
  },
]

const pcParts = [
  { key: 'CPU', value: 'Ryzen 5 7500F' },
  { key: 'GPU', value: 'RTX 2070 Super' },
  { key: 'RAM', value: '32GB DDR5' },
  { key: 'SSD', value: '2TB NVMe' },
]

const liveNotes = [
  {
    icon: 'ri-flashlight-fill',
    title: 'Быстро читается',
    text: 'Главное видно за первые секунды: кто ты, чем занят, где тебя найти.',
  },
  {
    icon: 'ri-drag-move-2-fill',
    title: 'Гибко собирается',
    text: 'Блоки можно включать, скрывать и переставлять под конкретную аудиторию.',
  },
  {
    icon: 'ri-palette-fill',
    title: 'Выглядит по-своему',
    text: 'Темы и кастомные карточки дают профилю характер без ручной верстки.',
  },
]

const modules = [
  {
    icon: 'ri-gamepad-fill',
    title: 'Игровые данные',
    text: 'Steam, Faceit, активность и статистика в одном заметном слое.',
    tags: ['Steam', 'Faceit', 'ELO'],
  },
  {
    icon: 'ri-music-2-fill',
    title: 'Музыкальный вайб',
    text: 'Now Playing, Last.fm и плейлисты помогают показать настроение страницы.',
    tags: ['Now Playing', 'Last.fm', 'Spotify'],
  },
  {
    icon: 'ri-links-fill',
    title: 'Контакты и соцсети',
    text: 'Telegram, Discord, GitHub и другие каналы без лишней навигации.',
    tags: ['Telegram', 'Discord', 'GitHub'],
  },
  {
    icon: 'ri-code-s-slash-fill',
    title: 'Портфолио',
    text: 'Проекты, репозитории, витрины и ссылки для рабочих знакомств.',
    tags: ['Projects', 'GitHub', 'Behance'],
  },
  {
    icon: 'ri-computer-fill',
    title: 'Сетап',
    text: 'Железо, инструменты и кастомные карточки для личного контекста.',
    tags: ['PC', 'Tools', 'Bio'],
  },
  {
    icon: 'ri-shield-star-fill',
    title: 'Единая витрина',
    text: 'Один URL остается прежним, даже когда контент внутри меняется.',
    tags: ['Bio', 'Resume', 'Chat'],
  },
]

const scenarios = [
  {
    icon: 'ri-gamepad-fill',
    title: 'Для игроков',
    text: 'Покажи Steam, Faceit, текущую игру и контакты для команды.',
  },
  {
    icon: 'ri-code-s-slash-fill',
    title: 'Для разработчиков',
    text: 'Собери проекты, GitHub, стек и быстрый способ написать тебе.',
  },
  {
    icon: 'ri-music-2-fill',
    title: 'Для креаторов',
    text: 'Смешай музыку, медиа, соцсети и визуальную тему под свой стиль.',
  },
]

const steps = [
  {
    index: '01',
    title: 'Создай основу',
    description: 'Ник, аватар, короткое bio и базовые теги задают первый слой профиля.',
  },
  {
    index: '02',
    title: 'Подключи блоки',
    description: 'Выбери сервисы, расставь модули и оставь только важные сигналы.',
  },
  {
    index: '03',
    title: 'Опубликуй ссылку',
    description: 'Один URL можно добавить в bio, резюме, чат, Discord или Telegram.',
  },
]

const compareRows: Array<{
  feature: string
  stellalink: CompareState
  linktree: CompareState
  aboutme: CompareState
}> = [
  { feature: 'Базовые ссылки', stellalink: 'check', linktree: 'check', aboutme: 'check' },
  { feature: 'Живые данные из сервисов', stellalink: 'check', linktree: 'none', aboutme: 'none' },
  { feature: 'Игровые блоки Steam и Faceit', stellalink: 'check', linktree: 'none', aboutme: 'none' },
  { feature: 'Музыкальная активность', stellalink: 'check', linktree: 'none', aboutme: 'none' },
  { feature: 'Свободная композиция блоков', stellalink: 'check', linktree: 'partial', aboutme: 'none' },
  { feature: 'Темы и кастомизация', stellalink: 'check', linktree: 'partial', aboutme: 'partial' },
]

const footerLinks = [
  { label: 'Документация', href: '/docs', icon: 'ri-book-open-line' },
  { label: 'Политика', href: '/privacy', icon: 'ri-shield-check-line' },
  { label: 'Условия', href: '/terms', icon: 'ri-file-list-3-line' },
  { label: 'GitHub', href: 'https://github.com/', icon: 'ri-github-fill' },
]

function closeMenu() {
  menuOpen.value = false
}

function scrollTo(id: string) {
  closeMenu()
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function normalizeSlugForAuth(input: string): string {
  return input
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9_-]/g, '')
    .slice(0, 50)
}

async function openAuth(slugValue: string, tab: 'login' | 'register' = 'register') {
  closeMenu()

  if (tab === 'login') {
    await navigateTo('/auth/login')
    return
  }

  const normalizedSlug = normalizeSlugForAuth(slugValue)
  if (normalizedSlug) {
    await navigateTo({ path: '/auth/register', query: { slug: normalizedSlug } })
    return
  }

  await navigateTo('/auth/register')
}

function onSlugInput(event: Event) {
  slug.value = (event.target as HTMLInputElement | null)?.value ?? ''
}

function statusLabel(state: CompareState): string {
  if (state === 'check') {
    return 'Есть'
  }

  if (state === 'partial') {
    return 'Частично'
  }

  return 'Нет'
}

function statusClass(state: CompareState): string {
  return `status-${state}`
}

async function logout() {
  await auth.logout()
  closeMenu()
  await navigateTo('/')
}

let revealObserver: IntersectionObserver | null = null

onMounted(() => {
  if (auth.isAuthenticated && !profile.loading) {
    profile.fetch().catch(() => {})
  }

  const revealItems = Array.from(document.querySelectorAll<HTMLElement>('.reveal'))

  if (!revealItems.length) {
    return
  }

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    revealItems.forEach(item => item.classList.add('is-visible'))
    return
  }

  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          revealObserver?.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.18, rootMargin: '0px 0px -8% 0px' },
  )

  revealItems.forEach(item => revealObserver?.observe(item))
})

watch(
  () => auth.user?.id,
  (userId) => {
    if (userId && !profile.loading) {
      profile.fetch().catch(() => {})
      return
    }

    profile.profile = null
  },
)

onBeforeUnmount(() => {
  revealObserver?.disconnect()
  revealObserver = null
})
</script>

<style src="~/assets/css/landing.css" />
