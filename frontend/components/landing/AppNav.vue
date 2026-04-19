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
        <md-filled-button class="btn-nav" @click="$emit('openAuth')">Создать профиль</md-filled-button>
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
  await auth.logout()
  await navigateTo('/')
}
</script>

<style scoped>
.nav-user {
  display: flex; align-items: center; gap: 6px;
}
.nav-user-pill {
  display: flex; align-items: center; gap: 8px;
  background: rgba(16, 27, 45, 0.82);
  border: 1px solid rgba(149, 188, 255, 0.22);
  border-radius: 100px; padding: 4px 14px 4px 4px;
  text-decoration: none; color: #dbe9ff;
  transition: background 0.2s;
}
.nav-user-pill:hover { background: rgba(22, 35, 58, 0.94); }
.nav-user-avatar {
  width: 26px; height: 26px; border-radius: 50%;
  background: linear-gradient(145deg, #3a66bf, #79a8ff);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #f2f7ff;
}
.nav-user-email { font-size: 13px; font-weight: 500; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nav-logout {
  background: rgba(16, 27, 45, 0.82); border: 1px solid rgba(149, 188, 255, 0.2);
  border-radius: 8px; width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  color: #b9c9e5; cursor: pointer; font-size: 16px;
  transition: background 0.2s, color 0.2s;
}
.nav-logout:hover { background: rgba(58, 26, 28, 0.95); color: #ffb4b4; border-color: rgba(255, 158, 158, 0.3); }
</style>
