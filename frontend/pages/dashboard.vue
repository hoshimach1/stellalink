<template>
  <div class="dash">
    <!-- Header -->
    <header class="dash-header">
      <NuxtLink to="/" class="dash-brand">
        <img src="/images/logos/logo.png" alt="" class="dash-logo">
        <span>Stellalink</span>
      </NuxtLink>

      <!-- Tabs (only when profile exists) -->
      <div v-if="profile.hasProfile" class="dash-tabs">
        <button :class="{ active: tab === 'profile' }" @click="tab = 'profile'">
          <i class="ri-layout-line" /> Профиль
        </button>
        <button :class="{ active: tab === 'account' }" @click="tab = 'account'">
          <i class="ri-user-settings-line" /> Аккаунт
        </button>
      </div>

      <div class="dash-header-right">
        <span class="dash-email">{{ auth.user?.email }}</span>
        <button class="dash-logout" @click="logout"><i class="ri-logout-box-r-line" /></button>
      </div>
    </header>

    <div v-if="auth.user && !auth.user.email_verified" class="dash-verify">
      <div class="dash-verify-text">
        <strong>Email не подтверждён.</strong>
        <span>Подтвердите адрес, чтобы повысить безопасность аккаунта.</span>
      </div>
      <button class="dash-verify-btn" :disabled="verifyLoading" @click="sendVerification">
        <span v-if="verifyLoading" class="dash-spinner" />
        <span v-else>Отправить письмо</span>
      </button>
      <div v-if="verifyNotice" class="dash-verify-note">{{ verifyNotice }}</div>
    </div>

    <!-- Setup: no profile -->
    <div v-if="!profile.hasProfile" class="setup-wrap">
      <div class="setup-card">
        <img src="/images/logos/logo.png" class="setup-logo" alt="">
        <h2>Создай свой профиль</h2>
        <p>Выбери имя и адрес страницы</p>
        <form class="setup-form" @submit.prevent="createProfile">
          <input
            v-model="setupName"
            type="text"
            class="setup-input"
            placeholder="Твоё имя или никнейм"
            minlength="1"
            maxlength="100"
            required
            autocomplete="off"
          >
          <div class="setup-url">
            <span class="setup-prefix">stellalink.app/</span>
            <input
              v-model="setupSlug"
              type="text"
              placeholder="username"
              pattern="[a-z0-9_-]+"
              minlength="2"
              maxlength="50"
              required
              autocomplete="off"
            >
          </div>
          <div v-if="setupError" class="dash-error">{{ setupError }}</div>
          <button type="submit" class="dash-btn-primary" :disabled="setupLoading">
            <span v-if="setupLoading" class="dash-spinner" />
            <span v-else>Создать профиль →</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Profile tab -->
    <DashboardProfileTab v-else-if="tab === 'profile'" />

    <!-- Account tab -->
    <div v-else class="dash-body">
      <DashboardAccountTab />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
import { useProfileStore } from '~/stores/profile'

definePageMeta({ layout: 'default', middleware: 'auth' })
useHead({ title: 'Dashboard — Stellalink' })

const auth = useAuthStore()
const profile = useProfileStore()
const router = useRouter()
const route = useRoute()

await profile.fetch()

const tab = ref<'profile' | 'account'>('profile')
const verifyLoading = ref(false)
const verifyNotice = ref('')

// Setup
const setupName = ref('')
const setupSlug = ref('')
const setupError = ref('')
const setupLoading = ref(false)

function normalizeSlug(input: string): string {
  return input
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9_-]/g, '')
    .slice(0, 50)
}

if (!profile.hasProfile && typeof route.query.slug === 'string') {
  setupSlug.value = normalizeSlug(route.query.slug)
}

function extractError(err: unknown, fallback: string): string {
  if (!err || typeof err !== 'object') return fallback
  const e = err as { data?: { detail?: unknown }; message?: string }
  const detail = e.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string }
    if (first?.msg) return first.msg
  }
  return e.message ?? fallback
}

async function sendVerification() {
  verifyLoading.value = true
  verifyNotice.value = ''
  try {
    const response = await auth.requestEmailVerification()
    verifyNotice.value = response.detail
  } catch (err) {
    verifyNotice.value = extractError(err, 'Не удалось отправить письмо')
  } finally {
    verifyLoading.value = false
  }
}

async function createProfile() {
  setupError.value = ''
  setupSlug.value = normalizeSlug(setupSlug.value)
  if (setupSlug.value.length < 2) {
    setupError.value = 'Slug must be at least 2 characters'
    return
  }
  setupLoading.value = true
  try {
    await profile.create({ slug: setupSlug.value, display_name: setupName.value || setupSlug.value })
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string } }
    setupError.value = err.data?.detail ?? 'Ошибка создания профиля'
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
.dash { min-height: 100vh; background: #09090b; color: #ececef; font-family: 'Onest', sans-serif; display: flex; flex-direction: column; }

.dash-header {
  display: flex; align-items: center; gap: 20px;
  padding: 0 20px; height: 58px; flex-shrink: 0;
  background: rgba(15,15,18,0.95);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  position: sticky; top: 0; z-index: 50;
}
.dash-brand {
  display: flex; align-items: center; gap: 8px;
  text-decoration: none; color: #ececef; font-weight: 800; font-size: 15px;
}
.dash-logo { width: 24px; height: 24px; object-fit: contain; mix-blend-mode: screen; }

.dash-tabs { display: flex; gap: 2px; margin: 0 auto; }
.dash-tabs button {
  display: flex; align-items: center; gap: 6px;
  background: transparent; border: none;
  padding: 6px 16px; border-radius: 8px;
  font-size: 13px; font-weight: 600; color: #71717a;
  cursor: pointer; font-family: 'Onest', sans-serif; transition: all 0.15s;
}
.dash-tabs button:hover { color: #a1a1aa; background: rgba(255,255,255,0.04); }
.dash-tabs button.active { color: #ececef; background: rgba(255,255,255,0.08); }

.dash-header-right { display: flex; align-items: center; gap: 10px; margin-left: auto; }
.dash-email { font-size: 12px; color: #71717a; }
.dash-logout {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px; width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  color: #71717a; cursor: pointer; font-size: 15px; transition: all 0.2s;
}
.dash-logout:hover { background: rgba(255,80,80,0.10); color: #ff7070; }

.dash-verify {
  margin: 14px 20px 0;
  border-radius: 14px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(92, 129, 222, 0.16), rgba(90, 100, 160, 0.08));
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px 14px;
  align-items: center;
}

.dash-verify-text {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.dash-verify-text strong {
  font-size: 14px;
  line-height: 1.3;
}

.dash-verify-text span {
  color: #b5b7c5;
  font-size: 13px;
  line-height: 1.4;
}

.dash-verify-btn {
  background: rgba(255,255,255,0.14);
  color: #ececef;
  border: none;
  border-radius: 10px;
  min-height: 36px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 600;
  font-family: 'Onest', sans-serif;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dash-verify-btn:hover { background: rgba(255,255,255,0.2); }
.dash-verify-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.dash-verify-note {
  grid-column: 1 / -1;
  color: #c8cada;
  font-size: 12px;
  line-height: 1.45;
}

/* Account tab wrapper */
.dash-body { padding: 32px 28px; flex: 1; }

/* Setup */
.setup-wrap { flex: 1; display: flex; justify-content: center; align-items: center; padding: 40px 16px; }
.setup-card {
  background: #0f0f12; border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px; padding: 40px 36px; width: 100%; max-width: 420px; text-align: center;
}
.setup-logo { width: 50px; height: 50px; object-fit: contain; mix-blend-mode: screen; margin: 0 auto 16px; display: block; }
.setup-card h2 { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 6px; }
.setup-card p { color: #71717a; font-size: 14px; margin-bottom: 28px; }
.setup-form { text-align: left; display: flex; flex-direction: column; gap: 14px; }
.setup-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; padding: 11px 14px; color: #ececef;
  font-size: 14px; font-family: 'Onest', sans-serif; outline: none; width: 100%;
  transition: border-color 0.2s;
}
.setup-input:focus { border-color: rgba(255,255,255,0.20); }
.setup-url {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; overflow: hidden;
}
.setup-prefix { padding: 11px 0 11px 14px; font-size: 14px; color: #71717a; white-space: nowrap; }
.setup-url input {
  flex: 1; background: none; border: none; outline: none;
  padding: 11px 14px 11px 0; color: #ececef; font-size: 14px; font-family: 'Onest', sans-serif;
}

.dash-error {
  background: rgba(255,80,80,0.10); border: 1px solid rgba(255,80,80,0.22);
  border-radius: 8px; padding: 9px 12px; color: #ff7070; font-size: 13px;
}
.dash-btn-primary {
  background: #fafafa; color: #09090b; border: none;
  border-radius: 10px; padding: 12px; font-size: 15px; font-weight: 700;
  font-family: 'Onest', sans-serif; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.dash-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.dash-spinner {
  width: 16px; height: 16px; border-radius: 50%;
  border: 2px solid rgba(0,0,0,0.2); border-top-color: #09090b;
  animation: spin 0.7s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 760px) {
  .dash-verify {
    margin: 10px 12px 0;
    grid-template-columns: 1fr;
  }

  .dash-verify-btn {
    width: 100%;
  }
}
</style>
