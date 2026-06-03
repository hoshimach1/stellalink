<template>
  <div class="dash-page">
    <header class="dash-topbar">
      <NuxtLink to="/" class="dash-brand" aria-label="Stellalink">
        <img src="/images/logos/logo.png" alt="" class="dash-brand-logo">
        <span>Stellalink</span>
      </NuxtLink>

      <nav class="dash-tabs" aria-label="Разделы dashboard">
        <button class="dash-tab" :class="{ active: tab === 'profile' }" type="button" @click="switchTab('profile')">
          <i aria-hidden="true" class="ri-layout-masonry-line" />
          <span>Профиль</span>
        </button>
        <button class="dash-tab" :class="{ active: tab === 'account' }" type="button" @click="switchTab('account')">
          <i aria-hidden="true" class="ri-shield-user-line" />
          <span>Аккаунт</span>
        </button>
        <button class="dash-tab" :class="{ active: tab === 'integrations' }" type="button" @click="switchTab('integrations')">
          <i aria-hidden="true" class="ri-plug-line" />
          <span>Сервисы</span>
        </button>
        <button v-if="auth.user?.is_admin" class="dash-tab" :class="{ active: tab === 'admin' }" type="button" @click="switchTab('admin')">
          <i aria-hidden="true" class="ri-settings-4-line" />
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
          <i aria-hidden="true" class="ri-external-link-line" />
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
          <i aria-hidden="true" class="ri-logout-box-r-line" />
        </button>
      </div>
    </header>

    <main class="dash-main">
      <Transition name="dash-toast">
        <section v-if="auth.user && !auth.user.email_verified && showEmailNotice" class="dash-mail" aria-live="polite">
          <span class="dash-mail-timer" aria-hidden="true" />
          <div class="dash-mail-icon">
            <i aria-hidden="true" class="ri-mail-check-line" />
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
            <i aria-hidden="true" class="ri-close-line" />
          </button>
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
const { pushToast } = useAppToast()

await profile.fetch()

type DashboardTab = 'profile' | 'account' | 'integrations' | 'admin'

const tab = ref<DashboardTab>(readTab(route.query.tab))
const verifyLoading = ref(false)
const showEmailNotice = ref(false)
const setupName = ref('')
const setupSlug = ref('')
const setupSlugTouched = ref(typeof route.query.slug === 'string' && route.query.slug.length > 0)
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
  try {
    const response = await auth.requestEmailVerification()
    pushToast(translateAuthMessage(response.detail, 'Письмо отправлено.'), 'success')
  } catch (error) {
    pushToast(extractAuthError(error, 'Не удалось отправить письмо.'), 'error')
  } finally {
    verifyLoading.value = false
  }
}

async function createProfile() {
  setupSlug.value = normalizeSlug(setupSlug.value)
  if (!canCreateProfile.value) {
    pushToast('Выберите адрес длиной минимум 2 символа.', 'warning')
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
    pushToast(extractAuthError(error, 'Не удалось создать профиль.'), 'error')
  } finally {
    setupLoading.value = false
  }
}

async function logout() {
  await auth.logout()
  await router.push('/')
}
</script>

<style scoped src="~/assets/css/dashboard.css" />
