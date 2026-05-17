<template>
  <div class="dash-page">
    <header class="dash-topbar">
      <NuxtLink to="/" class="dash-brand" aria-label="Stellalink">
        <img src="/images/logos/logo.png" alt="" class="dash-brand-logo">
        <span>Stellalink</span>
      </NuxtLink>

      <nav class="dash-tabs" aria-label="Разделы dashboard">
        <button class="dash-tab" :class="{ active: tab === 'profile' }" type="button" @click="switchTab('profile')">
          <i class="ri-layout-masonry-line" />
          <span>Профиль</span>
        </button>
        <button class="dash-tab" :class="{ active: tab === 'account' }" type="button" @click="switchTab('account')">
          <i class="ri-shield-user-line" />
          <span>Аккаунт</span>
        </button>
        <button class="dash-tab" :class="{ active: tab === 'integrations' }" type="button" @click="switchTab('integrations')">
          <i class="ri-plug-line" />
          <span>Сервисы</span>
        </button>
        <button v-if="auth.user?.is_admin" class="dash-tab" :class="{ active: tab === 'admin' }" type="button" @click="switchTab('admin')">
          <i class="ri-settings-4-line" />
          <span>Админка</span>
        </button>
      </nav>

      <div class="dash-actions">
        <a
          v-if="profile.hasProfile"
          :href="publicProfileUrl"
          class="dash-action dash-action-text"
          target="_blank"
          rel="noopener noreferrer"
          title="Открыть публичную страницу"
        >
          <i class="ri-external-link-line" />
          <span>Открыть</span>
        </a>
        <button class="dash-user" type="button" @click="switchTab('account')">
          <span class="dash-avatar">
            <img v-if="userAvatarUrl" :src="userAvatarUrl" alt="">
            <span v-else>{{ userInitial }}</span>
          </span>
          <span class="dash-user-copy">
            <strong>{{ headerNickname }}</strong>
            <small>{{ profile.profile?.slug ? `@${profile.profile.slug}` : 'аккаунт' }}</small>
          </span>
        </button>
        <button class="dash-action dash-logout" type="button" aria-label="Выйти" title="Выйти" @click="logout">
          <i class="ri-logout-box-r-line" />
        </button>
      </div>
    </header>

    <main class="dash-main">
      <Transition name="dash-toast">
        <section v-if="auth.user && !auth.user.email_verified && showEmailNotice" class="dash-mail" aria-live="polite">
          <span class="dash-mail-timer" aria-hidden="true" />
          <div class="dash-mail-icon">
            <i class="ri-mail-check-line" />
          </div>
          <div class="dash-mail-copy">
            <strong>Email не подтвержден</strong>
            <span>Письмо поможет восстановить доступ и защитить аккаунт.</span>
          </div>
          <button class="dash-mail-btn" type="button" :disabled="verifyLoading" @click="sendVerification">
            <span v-if="verifyLoading" class="dash-spinner dash-spinner-dark" />
            <span v-else>Отправить</span>
          </button>
          <button class="dash-mail-close" type="button" aria-label="Скрыть" @click="dismissEmailNotice">
            <i class="ri-close-line" />
          </button>
          <p v-if="verifyNotice" class="dash-mail-note" :class="`tone-${verifyNoticeTone}`">{{ verifyNotice }}</p>
        </section>
      </Transition>

      <Transition name="dash-pane" mode="out-in">
        <section v-if="tab === 'profile' && !profile.hasProfile" key="setup" class="dash-setup">
          <div class="setup-preview" aria-hidden="true">
            <div class="setup-phone">
              <div class="setup-phone-top">
                <div class="setup-phone-avatar">{{ setupInitial }}</div>
                <div>
                  <strong>{{ setupName || 'Ваше имя' }}</strong>
                  <span>{{ publicProfileLabel }}</span>
                </div>
              </div>
              <div class="setup-phone-line wide" />
              <div class="setup-phone-chip-row">
                <span>links</span>
                <span>about</span>
                <span>setup</span>
              </div>
              <div class="setup-phone-link" />
              <div class="setup-phone-link short" />
            </div>
          </div>

          <form class="setup-form" @submit.prevent="createProfile">
            <p class="dash-kicker">Первый запуск</p>
            <h1>Соберите публичный профиль за минуту.</h1>
            <p class="setup-lead">Нужны только имя и адрес страницы. Остальное можно настроить в новой студии.</p>

            <label class="dash-field">
              <span>Имя или ник</span>
              <input v-model="setupName" type="text" placeholder="Alex K." maxlength="100" autocomplete="off">
            </label>

            <label class="dash-field">
              <span>Адрес страницы</span>
              <div class="dash-slug-field">
                <span>{{ requestUrl.host }}/</span>
                <input
                  v-model="setupSlug"
                  type="text"
                  placeholder="username"
                  pattern="[a-z0-9_-]+"
                  minlength="2"
                  maxlength="50"
                  autocomplete="off"
                  @input="onSlugInput"
                >
              </div>
            </label>

            <div class="setup-helper" :class="setupSlugState.tone">{{ setupSlugState.text }}</div>
            <div v-if="setupError" class="dash-note error">{{ setupError }}</div>

            <button class="dash-primary" type="submit" :disabled="setupLoading || !canCreateProfile">
              <span v-if="setupLoading" class="dash-spinner" />
              <span v-else>Создать профиль</span>
            </button>
          </form>
        </section>

        <section v-else-if="tab === 'profile' && profile.hasProfile" key="profile" class="dash-panel">
          <DashboardProfileTab />
        </section>

        <section v-else-if="tab === 'account'" key="account" class="dash-panel">
          <DashboardAccountTab />
        </section>

        <section v-else-if="tab === 'integrations'" key="integrations" class="dash-panel">
          <DashboardIntegrationsTab />
        </section>

        <section v-else key="admin" class="dash-panel">
          <DashboardAdminTab />
        </section>
      </Transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { resolveAvatarUrl } from '~/composables/useAvatarUrl'
import { useAuthStore } from '~/stores/auth'
import { useProfileStore } from '~/stores/profile'
import { extractAuthError, translateAuthMessage } from '~/utils/auth-feedback'

definePageMeta({ layout: 'default', middleware: 'auth' })
useHead({ title: 'Dashboard - Stellalink' })

const auth = useAuthStore()
const profile = useProfileStore()
const router = useRouter()
const route = useRoute()
const requestUrl = useRequestURL()
const config = useRuntimeConfig()

await profile.fetch()

type DashboardTab = 'profile' | 'account' | 'integrations' | 'admin'

const tab = ref<DashboardTab>(readTab(route.query.tab))
const verifyLoading = ref(false)
const verifyNotice = ref('')
const verifyNoticeTone = ref<'success' | 'error'>('success')
const showEmailNotice = ref(false)
const setupName = ref('')
const setupSlug = ref('')
const setupSlugTouched = ref(typeof route.query.slug === 'string' && route.query.slug.length > 0)
const setupError = ref('')
const setupLoading = ref(false)
const avatarVersion = ref(Date.now())

const EMAIL_NOTICE_DELAY_MS = 2000
const EMAIL_NOTICE_AUTO_HIDE_MS = 10000
let emailNoticeDelayTimer: ReturnType<typeof setTimeout> | null = null
let emailNoticeAutoHideTimer: ReturnType<typeof setTimeout> | null = null

if (!profile.hasProfile && typeof route.query.slug === 'string') {
  setupSlug.value = normalizeSlug(route.query.slug)
}

watch(() => route.query.tab, (value) => {
  const next = readTab(value)
  if (next !== tab.value) tab.value = next
}, { immediate: true })

watch(() => auth.user?.avatar_url, () => {
  avatarVersion.value = Date.now()
})

const suggestedSlug = computed(() => normalizeSlug(setupName.value))
watch(suggestedSlug, (value) => {
  if (!setupSlugTouched.value) setupSlug.value = value
})

onMounted(() => {
  if (!auth.user || auth.user.email_verified) return
  emailNoticeDelayTimer = setTimeout(() => {
    emailNoticeDelayTimer = null
    showEmailNotice.value = true
    emailNoticeAutoHideTimer = setTimeout(() => {
      showEmailNotice.value = false
      emailNoticeAutoHideTimer = null
    }, EMAIL_NOTICE_AUTO_HIDE_MS)
  }, EMAIL_NOTICE_DELAY_MS)
})

onBeforeUnmount(() => {
  clearEmailNoticeTimers()
})

const headerNickname = computed(() =>
  profile.profile?.display_name?.trim()
  || profile.profile?.slug?.trim()
  || auth.user?.email?.split('@')[0]
  || 'Аккаунт',
)
const userInitial = computed(() => headerNickname.value.trim().charAt(0).toUpperCase() || '?')
const userAvatarUrl = computed(() =>
  resolveAvatarUrl(auth.user?.avatar_url ?? null, config.public.apiBase as string, avatarVersion.value),
)
const publicProfileSlug = computed(() => profile.profile?.slug?.trim() || setupSlug.value.trim() || 'your-name')
const publicProfileUrl = computed(() => new URL(`/${publicProfileSlug.value}`, requestUrl.origin).toString())
const publicProfileLabel = computed(() => `${requestUrl.host}/${publicProfileSlug.value}`)
const setupInitial = computed(() => (setupName.value.trim() || setupSlug.value.trim() || '?').charAt(0).toUpperCase())

const setupSlugState = computed(() => {
  const slug = normalizeSlug(setupSlug.value)
  if (!slug) {
    return { tone: 'neutral' as const, text: 'Латиница, цифры, дефис или подчеркивание.' }
  }
  if (slug.length < 2) {
    return { tone: 'warn' as const, text: 'Нужно минимум 2 символа.' }
  }
  return { tone: 'ready' as const, text: `Адрес: ${requestUrl.host}/${slug}` }
})

const canCreateProfile = computed(() => normalizeSlug(setupSlug.value).length >= 2)

function normalizeSlug(input: string) {
  return input.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9_-]/g, '').slice(0, 50)
}

function readTab(value: unknown): DashboardTab {
  const rawValue = Array.isArray(value) ? value[0] : value
  if (rawValue === 'admin' && auth.user?.is_admin) return 'admin'
  return rawValue === 'account' || rawValue === 'integrations' ? rawValue : 'profile'
}

function switchTab(next: DashboardTab) {
  if (tab.value === next) return
  tab.value = next
  const query = { ...route.query }
  if (next === 'profile') delete query.tab
  else query.tab = next
  router.replace({ query })
}

function clearEmailNoticeTimers() {
  if (emailNoticeDelayTimer) {
    clearTimeout(emailNoticeDelayTimer)
    emailNoticeDelayTimer = null
  }
  if (emailNoticeAutoHideTimer) {
    clearTimeout(emailNoticeAutoHideTimer)
    emailNoticeAutoHideTimer = null
  }
}

function dismissEmailNotice() {
  clearEmailNoticeTimers()
  showEmailNotice.value = false
}

function onSlugInput() {
  setupSlugTouched.value = true
  setupSlug.value = normalizeSlug(setupSlug.value)
}

async function sendVerification() {
  verifyLoading.value = true
  verifyNotice.value = ''
  try {
    const response = await auth.requestEmailVerification()
    verifyNoticeTone.value = 'success'
    verifyNotice.value = translateAuthMessage(response.detail, 'Письмо отправлено.')
  } catch (error) {
    verifyNoticeTone.value = 'error'
    verifyNotice.value = extractAuthError(error, 'Не удалось отправить письмо.')
  } finally {
    verifyLoading.value = false
  }
}

async function createProfile() {
  setupError.value = ''
  setupSlug.value = normalizeSlug(setupSlug.value)
  if (!canCreateProfile.value) {
    setupError.value = 'Выберите адрес длиной минимум 2 символа.'
    return
  }
  setupLoading.value = true
  try {
    await profile.create({
      slug: setupSlug.value,
      display_name: setupName.value.trim() || setupSlug.value,
    })
    const query = { ...route.query }
    delete query.slug
    delete query.tab
    await router.replace({ query })
    tab.value = 'profile'
  } catch (error) {
    setupError.value = extractAuthError(error, 'Не удалось создать профиль.')
  } finally {
    setupLoading.value = false
  }
}

async function logout() {
  await auth.logout()
  await router.push('/')
}
</script>

<style scoped>
.dash-page {
  --font-brand: Onest, "Segoe UI", sans-serif;
  --bg: oklch(98.4% 0.006 255);
  --surface: oklch(100% 0 0);
  --surface-low: oklch(95.3% 0.012 255);
  --surface-mid: oklch(92% 0.018 255);
  --surface-warm: oklch(96.5% 0.032 178);
  --text-1: oklch(19% 0.024 255);
  --text-2: oklch(43% 0.034 255);
  --text-3: oklch(58% 0.032 255);
  --outline: oklch(88% 0.018 255);
  --primary: oklch(48% 0.15 260);
  --on-primary: #FFFFFF;
  --primary-container: oklch(93.5% 0.038 260);
  --on-primary-container: oklch(30% 0.12 260);
  --secondary: oklch(50% 0.11 178);
  --tertiary: oklch(55% 0.16 305);
  --success: oklch(50% 0.13 152);
  --warning: oklch(58% 0.12 78);
  --error: oklch(52% 0.18 25);
  --shadow-soft: 0 18px 48px color-mix(in srgb, var(--text-1) 10%, transparent);
  --shadow-mid: 0 26px 64px color-mix(in srgb, var(--text-1) 15%, transparent);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --m3-motion: var(--ease-spring);
  --m3-fast: 170ms;
  --m3-med: 300ms;
  --dash-bg: var(--bg);
  --dash-surface: var(--surface);
  --dash-surface-soft: var(--surface-low);
  --dash-surface-strong: var(--surface);
  --dash-text-1: var(--text-1);
  --dash-text-2: var(--text-2);
  --dash-text-3: var(--text-3);
  --dash-outline: var(--outline);
  --dash-accent: var(--primary);
  --dash-accent-strong: var(--on-primary-container);
  --dash-accent-soft: var(--primary-container);
  --dash-green: var(--success);
  --dash-green-soft: #E1F6EA;
  --dash-warn: var(--warning);
  --dash-warn-soft: #FFF0CF;
  --dash-red: var(--error);
  --dash-red-soft: #FFE5E7;
  --dash-shadow: var(--shadow-soft);
  min-height: 100vh;
  color: var(--dash-text-1);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--primary-container) 42%, var(--bg)) 0, transparent 380px),
    linear-gradient(135deg, var(--bg) 0%, color-mix(in srgb, var(--secondary) 8%, var(--bg)) 58%, color-mix(in srgb, var(--tertiary) 6%, var(--bg)) 100%);
  font-family: var(--font-brand);
  overflow-x: clip;
}

.dash-page,
.dash-page :deep(*) {
  box-sizing: border-box;
}

.dash-topbar {
  position: fixed;
  top: 12px;
  left: 50%;
  z-index: 40;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  width: min(1180px, calc(100% - 24px));
  min-height: 62px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--outline) 80%, transparent);
  border-radius: 28px;
  background: color-mix(in srgb, var(--surface) 86%, transparent);
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(18px) saturate(145%);
  transform: translateX(-50%);
}

.dash-brand,
.dash-tab,
.dash-action,
.dash-user,
.dash-mail-btn,
.dash-mail-close,
.dash-primary {
  position: relative;
  border: 0;
  font: inherit;
  cursor: pointer;
  overflow: hidden;
  transition:
    transform var(--m3-fast) var(--m3-motion),
    background var(--m3-fast) var(--m3-motion),
    border-color var(--m3-fast) var(--m3-motion),
    color var(--m3-fast) var(--m3-motion),
    box-shadow var(--m3-fast) var(--m3-motion);
}

.dash-brand::after,
.dash-tab::after,
.dash-action::after,
.dash-user::after,
.dash-mail-btn::after,
.dash-mail-close::after,
.dash-primary::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: currentColor;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--m3-fast) var(--m3-motion);
}

@media (hover: hover) {
  .dash-brand:hover::after,
  .dash-tab:hover::after,
  .dash-action:hover::after,
  .dash-user:hover::after,
  .dash-mail-btn:hover::after,
  .dash-mail-close:hover::after,
  .dash-primary:hover::after {
    opacity: 0.08;
  }
}

.dash-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 42px;
  padding: 0 12px;
  border-radius: 999px;
  color: var(--dash-text-1);
  text-decoration: none;
  font-size: 21px;
  font-weight: 800;
}

.dash-brand-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.dash-tabs {
  justify-self: center;
  display: inline-flex;
  gap: 2px;
  min-width: 0;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: transparent;
  box-shadow: none;
}

.dash-tab {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 13px;
  border-radius: 999px;
  background: transparent;
  color: var(--dash-text-2);
  font-size: 14px;
  font-weight: 700;
}

.dash-tab.active {
  background: color-mix(in srgb, var(--primary-container) 86%, white);
  color: var(--dash-accent-strong);
}

.dash-actions {
  display: inline-flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.dash-action,
.dash-user {
  min-height: 46px;
  border: 1px solid var(--dash-outline);
  border-radius: 999px;
  background: color-mix(in srgb, var(--dash-surface-strong) 88%, transparent);
  color: var(--dash-text-1);
}

.dash-action {
  width: 42px;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  text-decoration: none;
  font-size: 18px;
}

.dash-action-text {
  width: auto;
  gap: 8px;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
}

.dash-user {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  max-width: 280px;
  padding: 4px 14px 4px 4px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--primary-container) 82%, white), color-mix(in srgb, var(--surface) 76%, white));
}

.dash-avatar {
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  display: inline-grid;
  place-items: center;
  overflow: hidden;
  border-radius: 50%;
  background:
    linear-gradient(135deg, var(--dash-accent), #F59E0B);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
}

.dash-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.dash-user-copy {
  display: grid;
  gap: 1px;
  min-width: 0;
  text-align: left;
}

.dash-user-copy strong,
.dash-user-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dash-user-copy strong {
  font-size: 13px;
  font-weight: 800;
}

.dash-user-copy small {
  color: var(--dash-text-3);
  font-size: 11px;
}

.dash-logout:hover {
  color: var(--dash-red);
  border-color: color-mix(in srgb, var(--dash-red) 24%, var(--dash-outline));
  background: var(--dash-red-soft);
}

.dash-main {
  width: min(1540px, calc(100% - 32px));
  margin: 0 auto;
  padding: 98px 0 48px;
}

.dash-panel {
  display: grid;
  min-width: 0;
}

.dash-mail {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 60;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  width: min(470px, calc(100vw - 32px));
  margin: 0;
  padding: 16px 14px 14px;
  border: 1px solid var(--dash-outline);
  border-radius: 8px;
  background: color-mix(in srgb, var(--dash-surface-strong) 96%, transparent);
  box-shadow: 0 20px 54px color-mix(in srgb, var(--dash-text-1) 14%, transparent);
  backdrop-filter: blur(18px) saturate(150%);
  overflow: hidden;
}

.dash-mail-timer {
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, var(--dash-warn), var(--dash-accent));
  transform-origin: left center;
  animation: dash-mail-countdown 10s linear forwards;
}

.dash-mail-icon {
  width: 42px;
  height: 42px;
  display: inline-grid;
  place-items: center;
  border-radius: 8px;
  background: var(--dash-warn-soft);
  color: var(--dash-warn);
  font-size: 20px;
}

.dash-mail-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.dash-mail-copy strong {
  font-size: 14px;
}

.dash-mail-copy span,
.dash-mail-note {
  color: var(--dash-text-2);
  font-size: 12px;
  line-height: 1.45;
}

.dash-mail-btn,
.dash-mail-close {
  min-height: 38px;
  border-radius: 999px;
  background: var(--dash-accent-soft);
  color: var(--dash-accent-strong);
  font-size: 13px;
  font-weight: 800;
}

.dash-mail-btn {
  padding: 0 14px;
}

.dash-mail-close {
  width: 38px;
}

.dash-mail-note {
  grid-column: 2 / -1;
  margin: -4px 0 0;
}

.dash-mail-note.tone-success {
  color: var(--dash-green);
}

.dash-mail-note.tone-error {
  color: var(--dash-red);
}

.dash-setup {
  min-height: calc(100vh - 146px);
  display: grid;
  grid-template-columns: minmax(300px, 0.86fr) minmax(340px, 1fr);
  gap: 36px;
  align-items: center;
  padding: 24px 28px;
}

.setup-preview {
  display: grid;
  justify-items: end;
}

.setup-phone {
  width: min(100%, 360px);
  display: grid;
  gap: 14px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 28px;
  background:
    linear-gradient(160deg, rgba(255,255,255,0.14), transparent 38%),
    linear-gradient(145deg, #171A22, #0E1117);
  color: #F8FAFC;
  box-shadow: 0 26px 72px rgba(31, 44, 73, 0.28);
}

.setup-phone-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.setup-phone-avatar {
  width: 72px;
  height: 72px;
  display: grid;
  place-items: center;
  border-radius: 24px;
  background: linear-gradient(135deg, var(--dash-accent), #F59E0B);
  font-size: 28px;
  font-weight: 900;
}

.setup-phone-top strong {
  display: block;
  font-size: 20px;
}

.setup-phone-top span {
  color: rgba(248, 250, 252, 0.66);
  font-size: 12px;
}

.setup-phone-line,
.setup-phone-link {
  height: 52px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: rgba(255,255,255,0.07);
}

.setup-phone-line.wide {
  height: 86px;
}

.setup-phone-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.setup-phone-chip-row span {
  padding: 7px 10px;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  color: rgba(248,250,252,0.76);
  font-size: 12px;
  font-weight: 800;
}

.setup-phone-link.short {
  width: 74%;
}

.setup-form {
  max-width: 620px;
  display: grid;
  gap: 14px;
}

.dash-kicker {
  margin: 0;
  color: var(--dash-accent-strong);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0;
  text-transform: uppercase;
}

.setup-form h1 {
  margin: 0;
  max-width: 760px;
  font-size: 48px;
  line-height: 0.98;
  font-weight: 900;
}

.setup-lead {
  max-width: 560px;
  margin: 0 0 6px;
  color: var(--dash-text-2);
  font-size: 16px;
  line-height: 1.6;
}

.dash-field {
  display: grid;
  gap: 7px;
}

.dash-field > span {
  color: var(--dash-text-2);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0;
}

.dash-field input,
.dash-slug-field {
  width: 100%;
  min-height: 54px;
  border: 1px solid var(--dash-outline);
  border-radius: 8px;
  background: var(--dash-surface-strong);
  color: var(--dash-text-1);
  font: inherit;
  outline: none;
  transition: border-color var(--m3-fast) var(--m3-motion), box-shadow var(--m3-fast) var(--m3-motion);
}

.dash-field input {
  padding: 0 16px;
}

.dash-slug-field {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
}

.dash-slug-field span {
  flex: 0 0 auto;
  color: var(--dash-text-3);
  font-size: 14px;
  font-weight: 800;
}

.dash-slug-field input {
  min-width: 0;
  min-height: auto;
  padding: 0;
  border: 0;
  background: transparent;
}

.dash-field input:focus,
.dash-slug-field:focus-within {
  border-color: var(--dash-accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--dash-accent) 16%, transparent);
}

.setup-helper,
.dash-note {
  padding: 11px 13px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.45;
}

.setup-helper {
  background: var(--dash-surface-soft);
  color: var(--dash-text-2);
}

.setup-helper.ready {
  background: var(--dash-green-soft);
  color: var(--dash-green);
}

.setup-helper.warn {
  background: var(--dash-warn-soft);
  color: var(--dash-warn);
}

.dash-note.error {
  background: var(--dash-red-soft);
  color: var(--dash-red);
}

.dash-primary {
  min-height: 54px;
  justify-content: center;
  border-radius: 999px;
  background: var(--dash-accent);
  color: #fff;
  font-weight: 900;
  box-shadow: 0 16px 30px color-mix(in srgb, var(--dash-accent) 22%, transparent);
}

.dash-primary:disabled,
.dash-mail-btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.dash-spinner {
  width: 18px;
  height: 18px;
  display: inline-block;
  border: 2px solid rgba(255,255,255,0.36);
  border-top-color: #fff;
  border-radius: 50%;
  animation: dash-spin 0.78s linear infinite;
}

.dash-spinner-dark {
  border-color: color-mix(in srgb, var(--dash-accent) 26%, transparent);
  border-top-color: var(--dash-accent);
}

.dash-pane-enter-active,
.dash-pane-leave-active,
.dash-toast-enter-active,
.dash-toast-leave-active {
  transition: opacity var(--m3-med) var(--m3-motion), transform var(--m3-med) var(--m3-motion);
}

.dash-pane-enter-from,
.dash-pane-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.dash-toast-enter-from,
.dash-toast-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.98);
}

@keyframes dash-spin {
  to { transform: rotate(360deg); }
}

@keyframes dash-mail-countdown {
  to { transform: scaleX(0); }
}

@media (max-width: 1040px) {
  .dash-topbar {
    grid-template-columns: auto 1fr;
    width: min(760px, calc(100% - 24px));
  }

  .dash-main {
    padding-top: 146px;
  }

  .dash-tabs {
    order: 3;
    grid-column: 1 / -1;
    justify-self: stretch;
  }

  .dash-tab {
    flex: 1;
    justify-content: center;
  }

  .dash-setup {
    grid-template-columns: 1fr;
  }

  .setup-preview {
    justify-items: center;
    order: 2;
  }
}

@media (max-width: 680px) {
  .dash-main {
    width: calc(100% - 16px);
    max-width: 1480px;
    padding-top: 138px;
  }

  .dash-topbar {
    left: 8px;
    right: 8px;
    width: auto;
    max-width: 760px;
    gap: 8px;
    padding: 8px;
    top: 8px;
    overflow: hidden;
    transform: none;
  }

  .dash-brand {
    min-height: 42px;
    padding: 0 8px;
    font-size: 0;
  }

  .dash-brand-logo {
    width: 26px;
    height: 26px;
  }

  .dash-action-text {
    width: 42px;
    padding: 0;
  }

  .dash-actions {
    display: grid;
    grid-template-columns: 42px;
    justify-self: end;
    gap: 6px;
  }

  .dash-action-text span,
  .dash-user,
  .dash-user-copy {
    display: none;
  }

  .dash-logout {
    display: none;
  }

  .dash-user {
    width: 42px;
    padding: 3px;
    justify-content: center;
  }

  .dash-avatar {
    width: 34px;
    height: 34px;
  }

  .dash-tabs {
    width: 100%;
    display: flex;
    justify-content: center;
    gap: 8px;
    overflow: hidden;
  }

  .dash-tab {
    width: 54px;
    min-width: 0;
    justify-content: center;
    padding: 0;
    font-size: 17px;
    overflow: hidden;
  }

  .dash-tab i {
    display: inline-flex;
  }

  .dash-tab span {
    display: none;
  }

  .dash-mail {
    left: 8px;
    right: 8px;
    bottom: 14px;
    width: auto;
    margin: 0;
    grid-template-columns: auto minmax(0, 1fr);
    gap: 8px;
    padding: 13px 10px 10px;
  }

  .dash-mail-icon {
    width: 36px;
    height: 36px;
    font-size: 18px;
  }

  .dash-mail-copy span {
    display: none;
  }

  .dash-mail-close {
    display: none;
  }

  .dash-mail-btn {
    grid-column: 1 / -1;
    min-height: 36px;
    padding: 0 12px;
    white-space: nowrap;
  }

  .dash-mail-note {
    grid-column: 1 / -1;
  }

  .dash-setup {
    padding: 22px 0 120px;
  }

  .setup-preview {
    display: none;
  }

  .setup-form h1 {
    font-size: 38px;
  }
}

@media (prefers-color-scheme: dark) {
  .dash-page {
    --bg: oklch(16% 0.015 255);
    --surface: oklch(21% 0.018 255);
    --surface-low: oklch(25% 0.022 255);
    --surface-mid: oklch(30% 0.026 255);
    --surface-warm: color-mix(in srgb, var(--secondary) 16%, transparent);
    --text-1: oklch(94% 0.01 255);
    --text-2: oklch(77% 0.02 255);
    --text-3: oklch(64% 0.026 255);
    --outline: rgba(203, 213, 225, 0.17);
    --primary: oklch(77% 0.11 260);
    --primary-container: color-mix(in srgb, var(--primary) 16%, transparent);
    --on-primary-container: oklch(91% 0.035 260);
    --success: oklch(76% 0.13 152);
    --warning: oklch(82% 0.12 78);
    --error: oklch(79% 0.13 25);
    --dash-bg: var(--bg);
    --dash-surface: var(--surface);
    --dash-surface-soft: var(--surface-low);
    --dash-surface-strong: var(--surface);
    --dash-text-1: var(--text-1);
    --dash-text-2: var(--text-2);
    --dash-text-3: var(--text-3);
    --dash-outline: var(--outline);
    --dash-accent: var(--primary);
    --dash-accent-strong: var(--on-primary-container);
    --dash-accent-soft: var(--primary-container);
    --dash-green: var(--success);
    --dash-green-soft: rgba(40, 160, 91, 0.18);
    --dash-warn: var(--warning);
    --dash-warn-soft: rgba(173, 110, 14, 0.2);
    --dash-red: var(--error);
    --dash-red-soft: rgba(190, 56, 68, 0.18);
    --shadow-soft: 0 18px 48px rgba(0, 0, 0, 0.34);
    --shadow-mid: 0 24px 60px rgba(0, 0, 0, 0.42);
    --dash-shadow: var(--shadow-soft);
    background:
      linear-gradient(180deg, color-mix(in srgb, var(--primary-container) 58%, var(--bg)) 0, transparent 360px),
      linear-gradient(135deg, var(--bg) 0%, color-mix(in srgb, var(--secondary) 9%, var(--bg)) 58%, color-mix(in srgb, var(--tertiary) 8%, var(--bg)) 100%);
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
</style>
