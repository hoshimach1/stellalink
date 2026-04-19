<template>
  <div class="home-page">
    <header class="app-topbar">
      <a href="#hero" class="brand" @click.prevent="scrollTo('hero')">
        <img src="/images/logos/logo.png" alt="Stellalink" class="brand-logo">
        <span class="brand-wordmark">Stellalink</span>
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
        <a href="#profile" @click.prevent="scrollTo('profile')">Профиль</a>
        <a href="#features" @click.prevent="scrollTo('features')">Сценарии</a>
        <a href="#compare" @click.prevent="scrollTo('compare')">Сравнение</a>

        <template v-if="auth.isAuthenticated">
          <NuxtLink class="user-pill" to="/dashboard" @click="closeMenu">
            <span class="user-avatar">{{ emailInitial }}</span>
            <span class="user-email">{{ auth.user?.email }}</span>
          </NuxtLink>
          <button class="logout-pill" aria-label="Выйти" @click="logout">
            <i class="ri-logout-box-r-line" />
          </button>
        </template>

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
      <section id="hero" class="section hero">
        <div class="hero-shell reveal">
          <div class="hero-copy">
            <p class="hero-label md-typescale-title-small">Единая ссылка, которая всегда актуальна</p>
            <h1 class="hero-title md-typescale-display-large">
              Твой живой профиль
              <span>в одном коротком URL</span>
            </h1>
            <p class="hero-sub md-typescale-body-large">
              Stellalink собирает в одной странице твои ключевые блоки: активность,
              ссылки, музыку, игровые данные и контакты. Подключил один раз и дальше
              профиль обновляется сам.
            </p>

            <div class="hero-actions">
              <md-filled-button class="btn btn-hero-primary btn-hero-main" @click="openAuth(previewSlug, 'register')">
                Создать профиль
              </md-filled-button>
              <md-outlined-button class="btn btn-hero-secondary btn-hero-main" @click="scrollTo('profile')">
                Смотреть пример
              </md-outlined-button>
            </div>

            <div class="hero-url">
              <span class="url-prefix">stellalink.app/</span>
              <span class="url-value">{{ previewSlug }}</span>
            </div>

            <md-chip-set class="hero-chips">
              <md-suggestion-chip v-for="chip in heroChips" :key="chip" :label="chip" />
            </md-chip-set>
          </div>

          <div class="hero-photo reveal" style="--reveal-delay: 100ms">
            <img
              src="/images/landing/preview.png"
              alt="Stellalink mobile profile screenshot"
              class="hero-photo-image"
              loading="lazy"
            >
          </div>
        </div>
      </section>

      <section id="profile" class="section profile">
        <div class="section-head reveal">
          <p class="section-label md-typescale-label-large">Пример профиля</p>
          <h2 class="section-title md-typescale-headline-large">
            Структура как в реальной странице пользователя
          </h2>
          <p class="section-sub md-typescale-body-large">
            Те же блоки, что ты показывал: шапка профиля, Steam, Faceit, музыка,
            ссылки и конфиг ПК.
          </p>
        </div>

        <div class="profile-layout">
          <md-elevated-card class="profile-card reveal">
            <div class="profile-head">
              <div class="profile-avatar-wrap">
                <div class="profile-avatar">A</div>
                <span class="profile-online" />
              </div>

              <div class="profile-meta">
                <h3 class="md-typescale-title-large">Alexander K.</h3>
                <p class="md-typescale-body-medium">Геймер • Меломан • Fullstack creator</p>
                <md-chip-set class="profile-tags">
                  <md-suggestion-chip v-for="tag in profileTags" :key="tag" :label="tag" />
                </md-chip-set>
              </div>
            </div>

            <div class="profile-grid">
              <md-outlined-card class="widget steam">
                <div class="widget-head">
                  <p class="widget-title">
                    <span class="widget-icon steam"><i class="ri-steam-fill" /></span>
                    Steam
                  </p>
                  <span class="widget-live">live</span>
                </div>
                <div class="widget-body game-row">
                  <div class="game-cover"><i class="ri-focus-3-fill" /></div>
                  <div>
                    <p class="game-name">Counter-Strike 2</p>
                    <p class="game-meta">2 847 ч • онлайн сейчас</p>
                  </div>
                </div>
              </md-outlined-card>

              <md-outlined-card class="widget faceit">
                <div class="widget-head">
                  <p class="widget-title">
                    <span class="widget-icon faceit"><i class="ri-trophy-fill" /></span>
                    Faceit
                  </p>
                </div>
                <div class="widget-body faceit-stats">
                  <div class="faceit-level">
                    <span>8</span>
                    lvl
                  </div>
                  <div class="faceit-grid">
                    <div>
                      <strong>1847</strong>
                      <small>ELO</small>
                    </div>
                    <div>
                      <strong>1.24</strong>
                      <small>K/D</small>
                    </div>
                    <div>
                      <strong>54%</strong>
                      <small>WR</small>
                    </div>
                  </div>
                </div>
              </md-outlined-card>

              <md-outlined-card class="widget music">
                <div class="widget-head">
                  <p class="widget-title">
                    <span class="widget-icon music"><i class="ri-lastfm-fill" /></span>
                    Сейчас слушает
                  </p>
                  <span class="widget-live">live</span>
                </div>
                <div class="widget-body music-row">
                  <div class="album-art" />
                  <div>
                    <p class="track-name">Fluorescent Adolescent</p>
                    <p class="track-artist">Arctic Monkeys</p>
                  </div>
                  <div class="eq-bars">
                    <span v-for="n in 4" :key="n" />
                  </div>
                </div>
              </md-outlined-card>

              <md-outlined-card class="widget links">
                <div class="widget-head">
                  <p class="widget-title">
                    <span class="widget-icon links"><i class="ri-links-fill" /></span>
                    Ссылки
                  </p>
                </div>
                <div class="widget-body links-list">
                  <a href="https://github.com" target="_blank" rel="noopener" class="widget-link">
                    <span><i class="ri-github-fill" /> GitHub / alexkirilin</span>
                    <i class="ri-arrow-right-up-line" />
                  </a>
                  <a href="https://t.me" target="_blank" rel="noopener" class="widget-link">
                    <span><i class="ri-telegram-fill" /> Telegram канал</span>
                    <i class="ri-arrow-right-up-line" />
                  </a>
                </div>
              </md-outlined-card>

              <md-outlined-card class="widget pc">
                <div class="widget-head">
                  <p class="widget-title">
                    <span class="widget-icon pc"><i class="ri-computer-fill" /></span>
                    Main PC
                  </p>
                </div>
                <div class="widget-body pc-grid">
                  <div v-for="part in pcParts" :key="part.key">
                    <small>{{ part.key }}</small>
                    <p>{{ part.value }}</p>
                  </div>
                </div>
              </md-outlined-card>
            </div>
          </md-elevated-card>

          <div class="profile-side-cards">
            <md-filled-card class="insight-card reveal">
              <p class="insight-label md-typescale-label-medium">Что важно для посетителя</p>
              <ul>
                <li v-for="item in liveInsights" :key="item">
                  <i class="ri-checkbox-circle-fill" />
                  <span>{{ item }}</span>
                </li>
              </ul>
            </md-filled-card>

            <md-outlined-card class="insight-card reveal">
              <p class="insight-label md-typescale-label-medium">Темы профиля</p>
              <ul>
                <li v-for="item in profileThemeNotes" :key="item">
                  <i class="ri-palette-line" />
                  <span>{{ item }}</span>
                </li>
              </ul>
            </md-outlined-card>
          </div>
        </div>
      </section>

      <section id="features" class="section capabilities">
        <div class="section-head reveal">
          <p class="section-label md-typescale-label-large">Сценарии</p>
          <h2 class="section-title md-typescale-headline-large">
            Что пользователь получает сразу и какие блоки можно включить
          </h2>
          <p class="section-sub md-typescale-body-large">
            Коротко: ценность, рабочие сценарии и доступные категории блоков без лишнего текста.
          </p>
        </div>

        <div class="proof-strip">
          <md-filled-card
            v-for="(point, pointIndex) in proofPoints"
            :key="point.value"
            class="proof-card reveal"
            :style="{ '--reveal-delay': `${pointIndex * 65}ms` }"
          >
            <p class="proof-value">{{ point.value }}</p>
            <p class="proof-label">{{ point.label }}</p>
          </md-filled-card>
        </div>

        <div class="capability-shell">
          <div class="scenario-grid">
            <md-outlined-card
              v-for="(scenario, scenarioIndex) in scenarios"
              :key="scenario.title"
              class="scenario-card reveal"
              :style="{ '--reveal-delay': `${scenarioIndex * 70}ms` }"
            >
              <div class="scenario-head">
                <span class="scenario-icon"><i :class="scenario.icon" /></span>
                <h3 class="md-typescale-title-medium">{{ scenario.title }}</h3>
              </div>
              <ul>
                <li v-for="point in scenario.points" :key="point">{{ point }}</li>
              </ul>
            </md-outlined-card>
          </div>

          <md-elevated-card class="launch-card reveal">
            <p class="launch-label md-typescale-label-large">Запуск</p>
            <h3 class="launch-title md-typescale-headline-small">Профиль публикуется в 3 шага</h3>
            <div class="launch-list">
              <article
                v-for="(step, stepIndex) in steps"
                :key="step.title"
                class="launch-item"
                :style="{ '--reveal-delay': `${stepIndex * 60}ms` }"
              >
                <p class="launch-step">{{ step.index }}</p>
                <div>
                  <p class="launch-item-title">{{ step.title }}</p>
                  <p class="launch-item-sub">{{ step.description }}</p>
                </div>
              </article>
            </div>
          </md-elevated-card>
        </div>

        <div id="blocks" class="block-grid">
          <md-filled-card class="block-summary reveal">
            <p class="block-summary-title">Доступные категории блоков</p>
            <p class="block-summary-sub">Выбираешь только нужное и собираешь страницу как модульный профиль.</p>
            <div class="block-compact">
              <article
                v-for="group in blockGroups"
                :key="group.title"
                class="block-compact-item"
              >
                <p class="block-compact-title">
                  <i :class="group.icon" />
                  <span>{{ group.title }}</span>
                </p>
                <p class="block-compact-sub">{{ group.items.join(' · ') }}</p>
              </article>
            </div>
          </md-filled-card>
        </div>
      </section>

      <section id="compare" class="section compare">
        <div class="section-head reveal">
          <p class="section-label md-typescale-label-large">Сравнение</p>
          <h2 class="section-title md-typescale-headline-large">Stellalink vs Linktree</h2>
          <p class="section-sub md-typescale-body-large">
            Коротко и по делу: где просто список ссылок, а где живая профильная страница.
          </p>
        </div>

        <div class="compare-shell reveal">
          <table class="compare-table">
            <thead>
              <tr>
                <th>Функция</th>
                <th class="main-col">Stellalink</th>
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

      <section id="cta" class="section cta">
        <md-filled-card class="cta-card reveal">
          <p class="section-label md-typescale-label-large">Старт</p>
          <h2 class="section-title md-typescale-headline-large">Займи свой короткий адрес</h2>
          <p class="section-sub md-typescale-body-large">
            Создай профиль один раз и обновляй блоки в пару кликов.
          </p>

          <div class="cta-row">
            <div class="slug-wrap">
              <span class="slug-prefix">stellalink.app/</span>
              <input
                class="slug-native-input"
                type="text"
                :value="slug"
                placeholder="username"
                aria-label="username"
                @input="onSlugInput"
                @keydown.enter.prevent="openAuth(previewSlug, 'register')"
              >
            </div>

            <md-filled-button class="btn btn-hero-primary cta-button" @click="openAuth(previewSlug, 'register')">
              Создать профиль
            </md-filled-button>
          </div>
        </md-filled-card>
      </section>
    </main>

    <footer class="footer">
      <div class="footer-brand">
        <img src="/images/logos/logo.png" alt="Stellalink" class="footer-logo">
        <p>Stellalink · 2026</p>
      </div>

      <div class="footer-links">
        <a
          v-for="link in footerLinks"
          :key="link.label"
          :href="link.href"
          :target="link.href.startsWith('http') ? '_blank' : undefined"
          :rel="link.href.startsWith('http') ? 'noopener noreferrer' : undefined"
          class="footer-link"
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

definePageMeta({ layout: 'landing' })

useHead({
  title: 'Stellalink — твой живой профиль',
  meta: [
    {
      name: 'description',
      content: 'Живой профиль в одном коротком URL: игровые виджеты, музыка, ссылки, контакты и гибкие темы профиля.',
    },
  ],
})

type CompareState = 'check' | 'partial' | 'none'

const auth = useAuthStore()
const menuOpen = ref(false)
const slug = ref('')

const emailInitial = computed(() => auth.user?.email?.[0]?.toUpperCase() ?? '?')
const previewSlug = computed(() => slug.value.trim().replace(/\s+/g, '-').toLowerCase() || 'username')

const heroChips = ['Steam', 'Faceit', 'Now Playing', 'GitHub', 'Telegram']


const profileTags = ['CS2', 'Музыка', 'Anime', 'Coffee']

const pcParts = [
  { key: 'CPU', value: 'Ryzen 5 7500F' },
  { key: 'GPU', value: 'RTX 2070 Super' },
  { key: 'RAM', value: '32GB DDR5' },
  { key: 'SSD', value: '2TB NVMe' },
]

const liveInsights = [
  'Ключевая информация читается за 10–15 секунд',
  'Блоки можно включать, скрывать и переставлять',
  'Один URL работает для bio, портфолио и чатов',
]

const profileThemeNotes = [
  'Профиль поддерживает разные стили оформления',
  'Можно подобрать тему под контент и аудиторию',
  'Есть пространство для кастомного CSS',
]

const proofPoints = [
  { value: '1 URL', label: 'для bio, портфолио и контактов' },
  { value: '9 блоков', label: 'от Steam до GitHub и музыки' },
  { value: '2 темы', label: 'с авто-подстройкой под систему' },
]

const scenarios = [
  {
    icon: 'ri-gamepad-fill',
    title: 'Для геймеров',
    points: ['Steam и Faceit в одном экране', 'Статистика и активность без ручных апдейтов'],
  },
  {
    icon: 'ri-code-s-slash-fill',
    title: 'Для разработчиков',
    points: ['GitHub и проекты в одном профиле', 'Контактные каналы без лишней навигации'],
  },
  {
    icon: 'ri-music-2-fill',
    title: 'Для креаторов',
    points: ['Now Playing и медийные ссылки', 'Тема страницы под стиль автора'],
  },
]

const blockGroups = [
  {
    icon: 'ri-gamepad-fill',
    title: 'Игровые',
    items: ['Steam', 'Faceit', 'игровая статистика'],
  },
  {
    icon: 'ri-music-2-fill',
    title: 'Музыкальные',
    items: ['Now Playing', 'Last.fm', 'Spotify'],
  },
  {
    icon: 'ri-links-fill',
    title: 'Контакты и соцсети',
    items: ['Telegram', 'Discord', 'X', 'VK'],
  },
  {
    icon: 'ri-github-fill',
    title: 'Портфолио',
    items: ['GitHub', 'Behance', 'Dribbble'],
  },
  {
    icon: 'ri-file-text-line',
    title: 'О себе',
    items: ['bio', 'сетап', 'кастомные карточки'],
  },
]

const steps = [
  {
    index: '01',
    title: 'Создай основу',
    description: 'Ник, аватар, короткое bio и базовые теги.',
  },
  {
    index: '02',
    title: 'Подключи блоки',
    description: 'Выбери сервисы и расставь блоки в нужном порядке.',
  },
  {
    index: '03',
    title: 'Публикуй ссылку',
    description: 'Один URL для соцсетей, резюме и любого внешнего трафика.',
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
  { feature: 'Игровые блоки (Steam/Faceit)', stellalink: 'check', linktree: 'none', aboutme: 'none' },
  { feature: 'Музыкальная активность', stellalink: 'check', linktree: 'none', aboutme: 'none' },
  { feature: 'Свободная компоновка блоков', stellalink: 'check', linktree: 'partial', aboutme: 'none' },
  { feature: 'Темы и кастомизация', stellalink: 'check', linktree: 'partial', aboutme: 'partial' },
]

const footerLinks = [
  { label: 'Документация', href: '/docs', icon: 'ri-book-open-line' },
  { label: 'Политика конфиденциальности', href: '/privacy', icon: 'ri-shield-check-line' },
  { label: 'Условия использования', href: '/terms', icon: 'ri-file-list-3-line' },
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
    return '✓'
  }

  if (state === 'partial') {
    return 'частично'
  }

  return '—'
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
    { threshold: 0.2, rootMargin: '0px 0px -8% 0px' },
  )

  revealItems.forEach(item => revealObserver?.observe(item))
})

onBeforeUnmount(() => {
  revealObserver?.disconnect()
  revealObserver = null
})
</script>

<style src="~/assets/css/landing.css" />



