<template>
  <nav>
    <a href="#" class="logo">
      <img src="/images/logos/logo.png" alt="Stellalink" class="logo-img">
      <span class="logo-name">Stellalink</span>
    </a>
    <ul class="nav-links" :class="{ open: menuOpen }">
      <li><a href="#features" @click="closeMenu">Возможности</a></li>
      <li><a href="#blocks" @click="closeMenu">Блоки</a></li>
      <li><a href="#howto" @click="closeMenu">Как это работает</a></li>
      <li><a href="#compare" @click="closeMenu">VS Linktree</a></li>
      <li v-if="auth.isAuthenticated">
        <div class="nav-user">
          <NuxtLink to="/dashboard" class="nav-user-pill">
            <span class="nav-user-avatar">{{ emailInitial }}</span>
            <span class="nav-user-email">{{ auth.user?.email }}</span>
          </NuxtLink>
          <button class="nav-logout" aria-label="Выйти" @click="logout">
            <i class="ri-logout-box-r-line" />
          </button>
        </div>
      </li>
      <li v-else>
        <button class="btn-nav" @click="$emit('openAuth')">Создать профиль</button>
      </li>
    </ul>
    <button class="burger" :class="{ open: menuOpen }" :aria-expanded="menuOpen" aria-label="Меню" @click="menuOpen = !menuOpen">
      <span /><span /><span />
    </button>
  </nav>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

defineEmits<{ openAuth: [] }>()

const auth = useAuthStore()
const menuOpen = ref(false)
const closeMenu = () => { menuOpen.value = false }
const emailInitial = computed(() => auth.user?.email?.[0]?.toUpperCase() ?? '?')

async function logout() {
  auth.logout()
  await navigateTo('/')
}
</script>

<style scoped>
.nav-user {
  display: flex; align-items: center; gap: 6px;
}
.nav-user-pill {
  display: flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 100px; padding: 4px 14px 4px 4px;
  text-decoration: none; color: #ececef;
  transition: background 0.2s;
}
.nav-user-pill:hover { background: rgba(255,255,255,0.10); }
.nav-user-avatar {
  width: 26px; height: 26px; border-radius: 50%;
  background: linear-gradient(135deg, #27272a, #3f3f46);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #fafafa;
}
.nav-user-email { font-size: 13px; font-weight: 500; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nav-logout {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px; width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  color: #71717a; cursor: pointer; font-size: 16px;
  transition: background 0.2s, color 0.2s;
}
.nav-logout:hover { background: rgba(255,80,80,0.12); color: #ff7070; border-color: rgba(255,80,80,0.2); }
</style>
