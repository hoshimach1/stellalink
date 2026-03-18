<template>
  <div class="dash-wrap">
    <div class="dash-header">
      <img src="/images/logos/logo.png" alt="Stellalink" class="dash-logo">
      <span class="dash-brand">Stellalink</span>
      <div class="dash-spacer" />
      <span class="dash-email">{{ auth.user?.email }}</span>
      <button class="dash-logout" @click="logout">
        <i class="ri-logout-box-r-line" /> Выйти
      </button>
    </div>

    <div class="dash-body">
      <div class="dash-welcome">
        <div class="dash-avatar">{{ initial }}</div>
        <div>
          <h1>Добро пожаловать!</h1>
          <p>Твой профиль скоро появится здесь. Дашборд в разработке.</p>
        </div>
      </div>

      <div class="dash-cards">
        <div class="dash-card">
          <i class="ri-link-m" />
          <span>Ссылки</span>
          <small>скоро</small>
        </div>
        <div class="dash-card">
          <i class="ri-gamepad-line" />
          <span>Steam</span>
          <small>скоро</small>
        </div>
        <div class="dash-card">
          <i class="ri-music-2-line" />
          <span>Last.fm</span>
          <small>скоро</small>
        </div>
        <div class="dash-card">
          <i class="ri-github-line" />
          <span>GitHub</span>
          <small>скоро</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'default' })

useHead({ title: 'Dashboard — Stellalink' })

const auth = useAuthStore()
const router = useRouter()

if (!auth.isAuthenticated) {
  await navigateTo('/')
}

const initial = computed(() => auth.user?.email?.[0]?.toUpperCase() ?? '?')

async function logout() {
  auth.logout()
  await router.push('/')
}
</script>

<style scoped>
.dash-wrap {
  min-height: 100vh;
  background: #090910;
  color: #eeeef8;
  font-family: 'Onest', sans-serif;
}

.dash-header {
  display: flex; align-items: center; gap: 12px;
  padding: 0 32px; height: 60px;
  background: rgba(13,13,28,0.9);
  border-bottom: 1px solid rgba(61,142,255,0.10);
}
.dash-logo { width: 28px; height: 28px; object-fit: contain; mix-blend-mode: screen; }
.dash-brand { font-weight: 800; font-size: 16px; letter-spacing: -0.4px; }
.dash-spacer { flex: 1; }
.dash-email { font-size: 13px; color: #6a6a90; }
.dash-logout {
  display: flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(61,142,255,0.12);
  border-radius: 8px; padding: 6px 14px;
  color: #6a6a90; font-size: 13px; font-family: 'Onest', sans-serif; cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.dash-logout:hover { background: rgba(255,80,80,0.10); color: #ff7070; }

.dash-body {
  max-width: 880px; margin: 0 auto;
  padding: 60px 24px;
}

.dash-welcome {
  display: flex; align-items: center; gap: 20px; margin-bottom: 48px;
}
.dash-avatar {
  width: 64px; height: 64px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; font-weight: 800; color: #fff;
}
.dash-welcome h1 { font-size: 28px; font-weight: 800; letter-spacing: -0.8px; margin-bottom: 4px; }
.dash-welcome p { color: #6a6a90; font-size: 15px; }

.dash-cards {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 14px;
}
.dash-card {
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.10);
  border-radius: 14px; padding: 24px 20px;
  display: flex; flex-direction: column; gap: 8px;
  color: #3a3a58;
}
.dash-card i { font-size: 24px; color: rgba(61,142,255,0.3); }
.dash-card span { font-size: 15px; font-weight: 600; color: #eeeef8; }
.dash-card small { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
</style>
