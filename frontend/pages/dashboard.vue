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

definePageMeta({ layout: 'default' })
useHead({ title: 'Dashboard — Stellalink' })

const auth = useAuthStore()
const profile = useProfileStore()
const router = useRouter()

if (!auth.isAuthenticated) await navigateTo('/')

await profile.fetch()

const tab = ref<'profile' | 'account'>('profile')

// Setup
const setupName = ref('')
const setupSlug = ref('')
const setupError = ref('')
const setupLoading = ref(false)

async function createProfile() {
  setupError.value = ''
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
  auth.logout()
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
</style>
