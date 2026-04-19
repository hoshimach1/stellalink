<template>
  <main class="auth-page">
    <NuxtLink class="auth-top-right-link" to="/auth/register">Регистрация</NuxtLink>

    <section class="auth-card">
      <NuxtLink class="auth-brand" to="/">
        <img src="/images/logos/logo.png" alt="Stellalink">
        <span>Stellalink</span>
      </NuxtLink>

      <h1 class="auth-headline">Войти</h1>
      <p class="auth-subtitle">Восстановим сессию автоматически через refresh token, если access устарел.</p>

      <div v-if="notice" class="auth-alert auth-alert-success">{{ notice }}</div>
      <div v-if="error" class="auth-alert auth-alert-error">{{ error }}</div>

      <form class="auth-form" @submit.prevent="submit">
        <div class="auth-field">
          <label>Email</label>
          <input v-model="email" class="auth-input" type="email" autocomplete="email" required placeholder="you@example.com">
        </div>

        <div class="auth-field">
          <label>Пароль</label>
          <div class="auth-input-wrap">
            <input
              v-model="password"
              class="auth-input auth-password-input"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              required
              placeholder="••••••••"
            >
            <button type="button" class="auth-password-toggle" @click="showPassword = !showPassword">
              <i :class="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'" />
            </button>
          </div>
        </div>

        <div class="auth-row">
          <NuxtLink class="auth-link" to="/auth/forgot-password">Забыли пароль?</NuxtLink>
          <NuxtLink class="auth-link" to="/auth/register">Нет аккаунта?</NuxtLink>
        </div>

        <button class="auth-btn auth-btn-primary" type="submit" :disabled="loading">
          <span v-if="loading" class="auth-spinner" />
          <span v-else>Войти</span>
        </button>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Вход — Stellalink' })

const auth = useAuthStore()
const route = useRoute()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const notice = computed(() => {
  if (route.query.verified === '1') return 'Email успешно подтверждён. Теперь можно войти.'
  if (route.query.reset === '1') return 'Пароль обновлён. Войдите с новым паролем.'
  return ''
})

const redirectPath = computed(() => {
  const raw = route.query.redirect
  if (typeof raw === 'string' && raw.startsWith('/')) {
    return raw
  }
  return '/dashboard'
})

function extractError(err: unknown): string {
  if (!err || typeof err !== 'object') return 'Не удалось выполнить вход'
  const e = err as {
    data?: { detail?: unknown }
    message?: string
  }
  const detail = e.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string }
    if (first?.msg) return first.msg
  }
  return e.message ?? 'Не удалось выполнить вход'
}

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    await navigateTo(redirectPath.value)
  } catch (err) {
    error.value = extractError(err)
  } finally {
    loading.value = false
  }
}
</script>
